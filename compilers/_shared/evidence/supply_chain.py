"""Supply-chain evidence-artifact emitter (F-CP-03 CORE-FANOUT).

A pure helper that turns one execution of any F-WF-* playbook that
calls external providers into one record conforming to
``schemas/evidence/supply-chain.schema.json`` and writes it to disk.

The emitter is deliberately decoupled from any compile target:

* It does not import ``temporalio``, ``langgraph``, or any n8n shim.
* It does no network I/O. The only side effect is the JSON file it
  writes; the caller chooses the output directory.
* Same context in → same record out → same ``artifact_id``. The id is
  the SHA-256 of ``<workflow_id>|<execution_id>|<captured_at>`` (UTF-8,
  no separators around the pipes) per the schema's ``artifact_id``
  contract, so a replay of the same execution at the same captured-at
  instant re-derives the same id and downstream deduplication is
  trivial.

The CORE-FANOUT keeps the contract small on purpose. One execution per
artifact; the per-dependency sovereignty classification follows the
shared ``sovereignty_band`` rollup (a deterministic function of
``residency``, ``ownership``, and the sub-processor-chain bands); the
``aggregates`` block is optional and forwarded only when the caller
already tracks it. Per-target byte-parity goldens land in the
EXTEND-tests sibling; drift / EXTEND-metrics / EXTEND-NIS2-MAPPING and
the ROADMAP flip each have their own sibling card.

The companion target-side wrappers for the CORE-FANOUT are
``compilers.temporal.evidence.supply_chain_activity``,
``compilers.n8n.evidence.supply_chain_node``, and
``compilers.langgraph.evidence.supply_chain_node``.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

__all__ = [
    "SupplyChainContext",
    "Dependency",
    "SovereigntyClassification",
    "Attestation",
    "Aggregates",
    "compute_sovereignty_band",
    "derive_artifact_id",
    "emit_supply_chain_artifact",
    "render_supply_chain_artifact",
]

# Pin matches the ``schema_version`` const in
# ``schemas/evidence/supply-chain.schema.json``. Bumped together with
# the schema when a breaking change ships.
SCHEMA_VERSION = "1.0.0"
STREAM = "supply-chain"

# Canonical vocabularies — kept in lockstep with the supporting schemas
# under ``schemas/{sovereignty_band,sovereignty_residency,
# sovereignty_ownership,supply_chain_dependency_kind,attestation_state}.json``.
# Catching shape errors here gives the caller a Python traceback instead
# of a JSON Schema validation error at write time; the schema is still
# the source of truth at persistence.
_DEPENDENCY_KINDS = frozenset(
    {
        "software_dependency",
        "hosted_api",
        "data_feed",
        "ai_provider",
        "managed_runtime",
    }
)
_RESIDENCIES = frozenset(
    {"eu", "eea", "eu_adequate_third_country", "non_eu", "unknown"}
)
_OWNERSHIPS = frozenset(
    {"eu_owned", "eu_majority_owned", "non_eu_owned", "unknown"}
)
_SOVEREIGNTY_BANDS = frozenset(
    {"sovereign", "eu_hosted_non_sovereign", "eu_adequate", "non_eu", "unknown"}
)
_ATTESTATION_STATES = frozenset(
    {"effective", "partially_effective", "ineffective", "overdue"}
)

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_WORKFLOW_ID_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
_CONTROL_REF_RE = re.compile(
    r"^control\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_REGULATION_REF_RE = re.compile(
    r"^(nis2|dora|cra|gdpr|iso27001|soc2):[a-z0-9][a-z0-9.-]*$"
)
_PROVIDER_ID_RE = re.compile(
    r"^provider\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_ISO8601_DURATION_RE = re.compile(
    r"^P([0-9]+Y)?([0-9]+M)?([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+S)?)?$"
)
_ISO8601_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_KB_REF_RE = re.compile(r"^supplier-kb://[A-Za-z0-9._~:/?#@!$&'()*+,;=%-]+$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$")


class EmitError(ValueError):
    """Raised when the context cannot produce a schema-conforming artifact."""


@dataclass(frozen=True)
class SovereigntyClassification:
    """Per-dependency sovereignty classification.

    The four primary axes mirror the schema's
    ``dependencies[].sovereignty_classification`` block. ``residency``,
    ``ownership``, and ``sovereignty_band`` are required; the
    sub-processor chain and the operator-supplied free-text rationale /
    KB pointer are optional.

    The ``sovereignty_band`` value is the rolled-up verdict. The caller
    may supply it directly (when the operator's KB already pins it) or
    leave it to the emitter to compute via
    :func:`compute_sovereignty_band` — see the helper's docstring for
    the deterministic rules.
    """

    residency: str
    ownership: str
    sovereignty_band: str
    sub_processor_chain: Sequence[str] | None = None
    band_rationale: str | None = None
    kb_ref: str | None = None


@dataclass(frozen=True)
class Attestation:
    """Per-dependency attestation freshness pointer.

    Mirrors the schema's
    ``dependencies[].attestation`` block. ``state``,
    ``last_reattested_at``, and ``next_due_at`` are required; the
    operator-side opaque attestation-record reference is optional.
    """

    state: str
    last_reattested_at: datetime
    next_due_at: datetime
    attestation_ref: str | None = None


@dataclass(frozen=True)
class Dependency:
    """One external dependency this execution resolved against.

    ``call_count == 0`` is valid and means "linked but not called this
    run" — useful for the SBOM-style enumeration without traffic. The
    schema's ``version`` field is intentionally permissive (semver /
    commit SHA / calendar version / ISO date / ``None`` for moving-tag
    hosted services).
    """

    provider_id: str
    kind: str
    call_count: int
    sovereignty_classification: SovereigntyClassification
    attestation: Attestation
    version: str | None = None
    risk_notes: str | None = None


@dataclass(frozen=True)
class Aggregates:
    """Optional pre-computed counts the emitter forwards verbatim.

    Catalog metrics may compute these themselves from ``dependencies[]``;
    the field set reserves the shape for emitters that already track
    them. The schema's ``additionalProperties: false`` constraint means
    every key here lands on disk as-is; the helper neither defaults nor
    re-derives them.
    """

    total_providers: int | None = None
    sovereign_count: int | None = None
    eu_hosted_count: int | None = None
    non_eu_count: int | None = None
    ai_provider_count: int | None = None


@dataclass(frozen=True)
class SupplyChainContext:
    """One execution of an F-WF-* playbook that called external providers.

    A workflow step builds this dataclass from its own state — the
    workflow identifier declared under ``content/playbooks/``, the
    execution id the workflow runtime issued for this run, the
    enumerated dependency surface that execution resolved against, and
    the dated ownership pointer for the supplier-inventory control
    attestation.

    All fields are validated by the emitter before any JSON is written;
    the schema is the source of truth, but catching the obvious shape
    errors here gives the caller a useful Python traceback instead of a
    JSON Schema validation error at write time.
    """

    workflow_id: str
    execution_id: str
    regulation_refs: Sequence[str]
    control_refs: Sequence[str]
    dependencies: Sequence[Dependency]
    owner_role: str
    owner_assigned_at: str
    captured_at: datetime
    source_url: str
    aggregates: Aggregates | None = None
    commit_sha: str | None = None
    retention: str | None = None


def _iso8601_z(dt: datetime) -> str:
    """Render a UTC ``datetime`` as a stable ISO-8601 ``...Z`` string.

    The schema marks timestamps ``format: date-time``; we canonicalise
    here so renders are deterministic and goldens stay byte-stable.
    """
    if dt.tzinfo is None:
        raise EmitError("timestamp must be timezone-aware (UTC).")
    dt_utc = dt.astimezone(timezone.utc).replace(microsecond=0)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def derive_artifact_id(
    workflow_id: str, execution_id: str, captured_at: datetime
) -> str:
    """SHA-256(``<workflow_id>|<execution_id>|<captured_at>``).

    ``captured_at`` is canonicalised through :func:`_iso8601_z` so the
    derivation is stable across timezone-aware inputs that resolve to
    the same UTC second.
    """
    captured_text = _iso8601_z(captured_at)
    payload = f"{workflow_id}|{execution_id}|{captured_text}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def compute_sovereignty_band(
    residency: str,
    ownership: str,
    sub_processor_bands: Sequence[str] | None,
) -> str:
    """Deterministic rollup of (residency, ownership, sub-processor bands).

    Rules (mirror the ``x_band_definitions`` block in
    ``schemas/sovereignty_band.json``):

    * Any of ``residency`` / ``ownership`` is ``unknown`` → ``unknown``.
    * Any sub-processor band is ``unknown`` → ``unknown``.
    * ``residency == 'non_eu'`` → ``non_eu``.
    * ``residency == 'eu_adequate_third_country'`` → ``eu_adequate``.
    * ``residency`` ∈ {``eu``, ``eea``} and ``ownership`` ∈
      {``eu_owned``, ``eu_majority_owned``} and every sub-processor
      band is ``sovereign`` → ``sovereign``.
    * ``residency`` ∈ {``eu``, ``eea``} (every other case) →
      ``eu_hosted_non_sovereign``.

    ``sub_processor_bands`` is the rolled-up band for each declared
    sub-processor. ``None`` means "the operator's KB has not captured
    the chain yet" and is treated as ``unknown`` per the schema's
    ``x_band_definitions``. An empty sequence means "provider declares
    no sub-processors" and contributes no constraint.
    """
    if residency not in _RESIDENCIES:
        raise EmitError(
            f"residency {residency!r} is not in the promoted vocabulary "
            f"{sorted(_RESIDENCIES)}"
        )
    if ownership not in _OWNERSHIPS:
        raise EmitError(
            f"ownership {ownership!r} is not in the promoted vocabulary "
            f"{sorted(_OWNERSHIPS)}"
        )
    if sub_processor_bands is None:
        return "unknown"
    if residency == "unknown" or ownership == "unknown":
        return "unknown"
    for sp_band in sub_processor_bands:
        if sp_band not in _SOVEREIGNTY_BANDS:
            raise EmitError(
                f"sub-processor band {sp_band!r} is not in the promoted "
                f"vocabulary {sorted(_SOVEREIGNTY_BANDS)}"
            )
        if sp_band == "unknown":
            return "unknown"
    if residency == "non_eu":
        return "non_eu"
    if residency == "eu_adequate_third_country":
        return "eu_adequate"
    # residency ∈ {eu, eea} from here on.
    eu_owned = ownership in {"eu_owned", "eu_majority_owned"}
    all_sub_sovereign = all(
        sp == "sovereign" for sp in sub_processor_bands
    )
    if eu_owned and all_sub_sovereign:
        return "sovereign"
    return "eu_hosted_non_sovereign"


def _validate_classification(
    cls: SovereigntyClassification, where: str
) -> None:
    if cls.residency not in _RESIDENCIES:
        raise EmitError(
            f"{where}.residency {cls.residency!r} is not in the promoted "
            f"vocabulary {sorted(_RESIDENCIES)}"
        )
    if cls.ownership not in _OWNERSHIPS:
        raise EmitError(
            f"{where}.ownership {cls.ownership!r} is not in the promoted "
            f"vocabulary {sorted(_OWNERSHIPS)}"
        )
    if cls.sovereignty_band not in _SOVEREIGNTY_BANDS:
        raise EmitError(
            f"{where}.sovereignty_band {cls.sovereignty_band!r} is not in "
            f"the promoted vocabulary {sorted(_SOVEREIGNTY_BANDS)}"
        )
    if cls.sub_processor_chain is not None:
        seen: set[str] = set()
        for sp_id in cls.sub_processor_chain:
            if not _PROVIDER_ID_RE.match(sp_id):
                raise EmitError(
                    f"{where}.sub_processor_chain entry {sp_id!r} does not "
                    "match the provider.<id>@v<n> shape"
                )
            if sp_id in seen:
                raise EmitError(
                    f"{where}.sub_processor_chain has duplicate entry "
                    f"{sp_id!r}; the schema pins uniqueness"
                )
            seen.add(sp_id)
    if cls.band_rationale is not None and not (
        1 <= len(cls.band_rationale) <= 400
    ):
        raise EmitError(
            f"{where}.band_rationale must be 1..400 chars (got "
            f"{len(cls.band_rationale)})"
        )
    if cls.kb_ref is not None and not _KB_REF_RE.match(cls.kb_ref):
        raise EmitError(
            f"{where}.kb_ref {cls.kb_ref!r} must match the "
            "supplier-kb://... shape"
        )


def _validate_attestation(att: Attestation, where: str) -> None:
    if att.state not in _ATTESTATION_STATES:
        raise EmitError(
            f"{where}.state {att.state!r} is not in the promoted "
            f"vocabulary {sorted(_ATTESTATION_STATES)}"
        )
    if att.last_reattested_at.tzinfo is None:
        raise EmitError(
            f"{where}.last_reattested_at must be timezone-aware (UTC)."
        )
    if att.next_due_at.tzinfo is None:
        raise EmitError(
            f"{where}.next_due_at must be timezone-aware (UTC)."
        )
    if att.attestation_ref is not None and not (
        1 <= len(att.attestation_ref) <= 400
    ):
        raise EmitError(
            f"{where}.attestation_ref must be 1..400 chars (got "
            f"{len(att.attestation_ref)})"
        )


def _validate_dependency(dep: Dependency, idx: int) -> None:
    where = f"dependencies[{idx}]"
    if not _PROVIDER_ID_RE.match(dep.provider_id):
        raise EmitError(
            f"{where}.provider_id {dep.provider_id!r} does not match the "
            "provider.<id>@v<n> shape pinned by the schema"
        )
    if dep.kind not in _DEPENDENCY_KINDS:
        raise EmitError(
            f"{where}.kind {dep.kind!r} is not in the promoted vocabulary "
            f"{sorted(_DEPENDENCY_KINDS)}"
        )
    if dep.call_count < 0:
        raise EmitError(
            f"{where}.call_count must be >= 0 (got {dep.call_count!r})"
        )
    if dep.version is not None and not (1 <= len(dep.version) <= 200):
        raise EmitError(
            f"{where}.version must be 1..200 chars when present (got "
            f"{len(dep.version)})"
        )
    if dep.risk_notes is not None and len(dep.risk_notes) > 1000:
        raise EmitError(
            f"{where}.risk_notes must be <= 1000 chars (got "
            f"{len(dep.risk_notes)})"
        )
    _validate_classification(dep.sovereignty_classification, where)
    _validate_attestation(dep.attestation, where)


def _validate_aggregates(agg: Aggregates) -> None:
    for name in (
        "total_providers",
        "sovereign_count",
        "eu_hosted_count",
        "non_eu_count",
        "ai_provider_count",
    ):
        value = getattr(agg, name)
        if value is not None and value < 0:
            raise EmitError(
                f"aggregates.{name} must be >= 0 (got {value!r})"
            )


def _validate_context(ctx: SupplyChainContext) -> None:
    if not _WORKFLOW_ID_RE.match(ctx.workflow_id) or len(ctx.workflow_id) > 200:
        raise EmitError(
            f"workflow_id {ctx.workflow_id!r} does not match the "
            "[a-z][a-z0-9_-]* shape (<= 200 chars) pinned by the schema"
        )
    if not ctx.execution_id or len(ctx.execution_id) > 200:
        raise EmitError(
            "execution_id must be a non-empty string <= 200 chars per the "
            "schema"
        )
    if not ctx.regulation_refs:
        raise EmitError(
            "regulation_refs must carry at least one entry; an artifact "
            "with no regulatory anchor is not evidence in the F-CP-03 sense"
        )
    seen_reg: set[str] = set()
    for ref in ctx.regulation_refs:
        if not _REGULATION_REF_RE.match(ref):
            raise EmitError(
                f"regulation_ref {ref!r} does not match the "
                "<regime>:<id> shape pinned by the schema"
            )
        if ref in seen_reg:
            raise EmitError(
                f"regulation_refs has duplicate entry {ref!r}; the schema "
                "pins uniqueness"
            )
        seen_reg.add(ref)
    if not ctx.control_refs:
        raise EmitError(
            "control_refs must carry at least one entry per the schema"
        )
    seen_ctrl: set[str] = set()
    for cref in ctx.control_refs:
        if not _CONTROL_REF_RE.match(cref):
            raise EmitError(
                f"control_ref {cref!r} does not match the "
                "control.<id>@v<n> shape pinned by the schema"
            )
        if cref in seen_ctrl:
            raise EmitError(
                f"control_refs has duplicate entry {cref!r}; the schema "
                "pins uniqueness"
            )
        seen_ctrl.add(cref)
    if not ctx.dependencies:
        raise EmitError(
            "dependencies must carry at least one entry; an execution "
            "with zero external dependencies should not emit a "
            "supply-chain evidence artifact at all"
        )
    for idx, dep in enumerate(ctx.dependencies):
        _validate_dependency(dep, idx)
    if not ctx.owner_role or len(ctx.owner_role) > 200:
        raise EmitError(
            "owner_role must be a non-empty string <= 200 chars per the "
            "schema"
        )
    if not _ISO8601_DATE_RE.match(ctx.owner_assigned_at):
        raise EmitError(
            f"owner_assigned_at {ctx.owner_assigned_at!r} must be an "
            "ISO-8601 date (YYYY-MM-DD) per the schema"
        )
    if ctx.commit_sha is not None and not _COMMIT_SHA_RE.match(ctx.commit_sha):
        raise EmitError(
            f"commit_sha {ctx.commit_sha!r} must be 7..64 lowercase hex chars"
        )
    if ctx.retention is not None and not _ISO8601_DURATION_RE.match(
        ctx.retention
    ):
        raise EmitError(
            f"retention {ctx.retention!r} is not an ISO-8601 duration"
        )
    if ctx.aggregates is not None:
        _validate_aggregates(ctx.aggregates)


def _render_classification(
    cls: SovereigntyClassification,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "residency": cls.residency,
        "ownership": cls.ownership,
        "sovereignty_band": cls.sovereignty_band,
    }
    if cls.sub_processor_chain is not None:
        out["sub_processor_chain"] = list(cls.sub_processor_chain)
    if cls.band_rationale is not None:
        out["band_rationale"] = cls.band_rationale
    if cls.kb_ref is not None:
        out["kb_ref"] = cls.kb_ref
    return out


def _render_attestation(att: Attestation) -> dict[str, Any]:
    out: dict[str, Any] = {
        "state": att.state,
        "last_reattested_at": _iso8601_z(att.last_reattested_at),
        "next_due_at": _iso8601_z(att.next_due_at),
    }
    if att.attestation_ref is not None:
        out["attestation_ref"] = att.attestation_ref
    return out


def _render_dependency(dep: Dependency) -> dict[str, Any]:
    out: dict[str, Any] = {
        "provider_id": dep.provider_id,
        "kind": dep.kind,
        "call_count": dep.call_count,
        "sovereignty_classification": _render_classification(
            dep.sovereignty_classification
        ),
        "attestation": _render_attestation(dep.attestation),
    }
    if dep.version is not None:
        out["version"] = dep.version
    if dep.risk_notes is not None:
        out["risk_notes"] = dep.risk_notes
    return out


def _render_aggregates(agg: Aggregates) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if agg.total_providers is not None:
        out["total_providers"] = agg.total_providers
    if agg.sovereign_count is not None:
        out["sovereign_count"] = agg.sovereign_count
    if agg.eu_hosted_count is not None:
        out["eu_hosted_count"] = agg.eu_hosted_count
    if agg.non_eu_count is not None:
        out["non_eu_count"] = agg.non_eu_count
    if agg.ai_provider_count is not None:
        out["ai_provider_count"] = agg.ai_provider_count
    return out


def render_supply_chain_artifact(ctx: SupplyChainContext) -> dict[str, Any]:
    """Pure context → record. Does not touch disk.

    Useful for tests, dry-runs, and any compile target that needs the
    record in-memory before persisting it through its own audit channel.
    """
    _validate_context(ctx)

    captured_at_text = _iso8601_z(ctx.captured_at)

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": derive_artifact_id(
            ctx.workflow_id, ctx.execution_id, ctx.captured_at
        ),
        "stream": STREAM,
        "workflow_id": ctx.workflow_id,
        "execution_id": ctx.execution_id,
        "regulation_refs": list(ctx.regulation_refs),
        "control_refs": list(ctx.control_refs),
        "dependencies": [_render_dependency(d) for d in ctx.dependencies],
        "owner": {
            "role": ctx.owner_role,
            "assigned_at": ctx.owner_assigned_at,
        },
        "captured_at": captured_at_text,
        "provenance": {
            "source_url": ctx.source_url,
            "captured_at": captured_at_text,
        },
    }
    if ctx.commit_sha:
        record["provenance"]["commit_sha"] = ctx.commit_sha
    if ctx.aggregates is not None:
        rendered_agg = _render_aggregates(ctx.aggregates)
        if rendered_agg:
            record["aggregates"] = rendered_agg
    if ctx.retention is not None:
        record["retention"] = ctx.retention

    return record


def emit_supply_chain_artifact(
    ctx: SupplyChainContext,
    output_dir: str | os.PathLike[str],
) -> Path:
    """Render the record and persist it as ``<artifact_id>.json``.

    Returns the absolute path of the written file. The directory is
    created if it does not exist. Writes atomically through a sibling
    ``.tmp`` then ``os.replace`` so a partial write cannot be read by a
    concurrent consumer.

    Re-emissions for the same
    ``(workflow_id, execution_id, captured_at)`` derive the same
    ``artifact_id`` and overwrite the same path with byte-stable
    content. Re-runs of the same workflow with a fresh ``execution_id``
    (or a fresh ``captured_at`` instant) land under a distinct
    ``artifact_id`` — the Cooperation-Group overlay reads re-emission
    as evidentiary signal rather than dedup waste.
    """
    record = render_supply_chain_artifact(ctx)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{record['artifact_id']}.json"
    tmp_path = out_dir / f".{record['artifact_id']}.json.tmp"
    serialized = json.dumps(record, indent=2, sort_keys=True) + "\n"
    tmp_path.write_text(serialized, encoding="utf-8")
    os.replace(tmp_path, out_path)
    return out_path.resolve()


# Silence linters that flag the imports kept for re-export.
_ = Mapping
