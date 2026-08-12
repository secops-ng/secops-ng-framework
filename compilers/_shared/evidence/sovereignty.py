"""Sovereignty posture evidence-artifact emitter (F-SV-04 CORE).

A pure helper that turns one posture-attestation exercise into one
record conforming to ``schemas/evidence/sovereignty.schema.json`` and
writes it to disk.

The emitter is deliberately decoupled from any compile target:

* It does not import ``temporalio``, ``langgraph``, or any n8n shim.
* It does no network I/O and names no sink — the record is composed
  from observations the operator supplies, and the only side effect is
  the JSON file it writes into a caller-chosen directory. The record
  carries no endpoint literal, so it cannot itself become a non-EU
  reference that ``kri.hardcoded_non_eu_endpoint_reference_count@v1``
  would count.
* Same context in → same record out → same ``artifact_id`` (SHA-256 of
  ``<workflow_id>|<execution_id>|<compile_target>``). ``captured_at``
  is deliberately not part of the id — re-emissions inside the same
  execution stay byte-identical at the path level.

Two disciplines the schema pins and this emitter surfaces early:

* **Completeness is mechanical.** Every sovereignty-cluster indicator
  must carry an observation; a missing or unknown indicator raises
  :class:`EmitError` naming it, before any file is written. An
  indicator the operator cannot observe is carried through the
  attestation state — never fabricated, never dropped.
* **No numeric aggregate.** The emitter derives nothing from the
  observations — no score, no ratio, no roll-up. Per-indicator
  evaluation against a declared baseline is the F-SV-05 conformance
  profile's job, downstream of this record.

``REQUIRED_INDICATORS`` mirrors the schema's ``observations.required``
list; ``tests/content_model/test_sovereignty_evidence_emitter.py``
asserts the two never drift (the schema test already pins schema ↔
catalogue, so the three stay in lockstep).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

__all__ = [
    "Observation",
    "SovereigntyContext",
    "REQUIRED_INDICATORS",
    "derive_artifact_id",
    "emit_sovereignty_artifact",
    "render_sovereignty_artifact",
]

# Pins match ``schemas/evidence/sovereignty.schema.json``; bumped
# together with the schema when a breaking change ships.
SCHEMA_VERSION = "1.0.0"
STREAM = "sovereignty"

# Mirrors the schema's ``observations.required`` list — the
# sovereignty-cluster indicators under content/metrics/. The schema and
# its catalogue-sync test own the list; the emitter test pins this
# tuple against the schema so all three surfaces stay in lockstep.
REQUIRED_INDICATORS = (
    "kpi.ai_provider_neutral_binding_ratio@v1",
    "kpi.backup_integrity_pass_rate@v1",
    "kpi.cloud_posture_coverage@v1",
    "kpi.dependency_free_ratio@v1",
    "kpi.eu_data_residency_declaration_coverage@v1",
    "kpi.eu_regulatory_reference_coverage@v1",
    "kpi.forward_public_hygiene_high_severity_escape_rate@v1",
    "kpi.gdpr_lawful_basis_section_coverage@v1",
    "kpi.lm_endpoint_eu_residency_coverage@v1",
    "kpi.non_eu_saas_free_workflow_ratio@v1",
    "kpi.notification_sla_compliance@v1",
    "kpi.reference_deployment_target_coverage@v1",
    "kpi.sovereign_cloud_provider_diversity@v1",
    "kpi.sovereign_object_storage_binding_coverage@v1",
    "kpi.unmanaged_asset_cardinality@v1",
    "kri.cloud_container_unclassifiable_scope_count@v1",
    "kri.cross_border_transfer_exposure_count@v1",
    "kri.declared_target_without_example_count@v1",
    "kri.hardcoded_non_eu_endpoint_reference_count@v1",
    "kri.lawful_basis_undocumented_surface_count@v1",
    "kri.lm_endpoint_unknown_residency_exposure@v1",
    "kri.non_eu_critical_dependency_count@v1",
    "kri.non_eu_lm_endpoint_escape_rate@v1",
    "kri.non_eu_vendor_sdk_exposure@v1",
    "kri.object_storage_unknown_jurisdiction_exposure@v1",
    "kri.unresolvable_regulatory_reference_count@v1",
)

# Shared four-state vocabulary — schemas/attestation_state.json is the
# source of truth (the artifact schema imports it by $ref); the emitter
# test pins this tuple against that file.
ATTESTATION_STATES = ("effective", "partially_effective", "ineffective", "overdue")

THRESHOLD_BANDS = ("on_target", "warn", "high", "breach")

_COMPILE_TARGETS = frozenset({"n8n", "temporal", "langgraph"})

# Canonical regexes — kept in lockstep with the schema. Catching shape
# errors here gives the caller a Python traceback instead of a JSON
# Schema validation error at write time; the schema is still the source
# of truth at persistence.
_WORKFLOW_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$")
_CONTROL_REF_RE = re.compile(
    r"^control\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_REGULATION_REF_RE = re.compile(
    r"^(nis2|dora|cra|gdpr|iso27001|soc2|eu_ai_act):[a-z0-9][a-z0-9.-]*$"
)
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$")


class EmitError(ValueError):
    """Raised when the context cannot produce a schema-conforming artifact."""


@dataclass(frozen=True)
class Observation:
    """One indicator reading inside the assessment window.

    ``observed_value`` is the reading in the indicator's own catalogue
    unit; ``threshold_band`` is the band it fell in against the
    indicator's own catalogue thresholds (``on_target`` when none
    fired); ``observed_at`` is when it was sampled and must fall inside
    the artifact's assessment window — the window, not this instant, is
    the staleness contract.
    """

    observed_value: float
    threshold_band: str
    observed_at: datetime


@dataclass(frozen=True)
class SovereigntyContext:
    """One posture-attestation exercise under a specific compile target.

    ``observations`` maps indicator ``stable_id`` → :class:`Observation`
    and must cover every entry of :data:`REQUIRED_INDICATORS`, exactly.
    ``attestation_state`` describes the attestation exercise itself
    (fresh and complete vs. gapped vs. overdue) using the shared
    vocabulary — it is not a sovereignty verdict and not a score.
    """

    workflow_id: str
    execution_id: str
    compile_target: str
    regulation_refs: Sequence[str]
    control_refs: Sequence[str]
    window_from: datetime
    window_to: datetime
    observations: Mapping[str, Observation]
    attestation_state: str
    captured_at: datetime
    source_url: str
    commit_sha: str | None = None


def _iso8601_z(dt: datetime, field: str) -> str:
    """Render a UTC ``datetime`` as a stable ISO-8601 ``...Z`` string."""
    if dt.tzinfo is None:
        raise EmitError(f"{field} must be timezone-aware (UTC).")
    dt_utc = dt.astimezone(timezone.utc).replace(microsecond=0)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def derive_artifact_id(
    workflow_id: str, execution_id: str, compile_target: str
) -> str:
    """SHA-256(``<workflow_id>|<execution_id>|<compile_target>``)."""
    payload = f"{workflow_id}|{execution_id}|{compile_target}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_refs(ctx: SovereigntyContext) -> None:
    if not _WORKFLOW_ID_RE.match(ctx.workflow_id) or len(ctx.workflow_id) > 200:
        raise EmitError(
            f"workflow_id {ctx.workflow_id!r} does not match the "
            "[a-z][a-z0-9_]* shape (<= 200 chars) pinned by the schema"
        )
    if not ctx.execution_id or len(ctx.execution_id) > 200:
        raise EmitError(
            "execution_id must be a non-empty string <= 200 chars per the schema"
        )
    if ctx.compile_target not in _COMPILE_TARGETS:
        raise EmitError(
            f"compile_target {ctx.compile_target!r} is not in the reference "
            f"enum {sorted(_COMPILE_TARGETS)}"
        )
    if not ctx.regulation_refs:
        raise EmitError(
            "regulation_refs must carry at least one entry; an artifact with "
            "no regulatory anchor is not evidence in the F-SV-04 sense"
        )
    for seq, regex, label in (
        (ctx.regulation_refs, _REGULATION_REF_RE, "regulation_ref"),
        (ctx.control_refs, _CONTROL_REF_RE, "control_ref"),
    ):
        seen: set[str] = set()
        for ref in seq:
            if not regex.match(ref):
                raise EmitError(
                    f"{label} {ref!r} does not match the shape pinned by the schema"
                )
            if ref in seen:
                raise EmitError(
                    f"{label}s has duplicate entry {ref!r}; the schema pins uniqueness"
                )
            seen.add(ref)
    if not ctx.control_refs:
        raise EmitError("control_refs must carry at least one entry per the schema")
    if ctx.commit_sha is not None and not _COMMIT_SHA_RE.match(ctx.commit_sha):
        raise EmitError(
            f"commit_sha {ctx.commit_sha!r} must be 7..64 lowercase hex chars"
        )


def _validate_observations(ctx: SovereigntyContext) -> None:
    supplied = set(ctx.observations)
    required = set(REQUIRED_INDICATORS)

    missing = sorted(required - supplied)
    if missing:
        raise EmitError(
            f"observations missing {len(missing)} sovereignty-cluster "
            f"indicator(s): {missing}. The posture attestation covers every "
            "indicator or it is not the F-SV-04 artifact — an indicator the "
            "operator cannot observe is carried through attestation_state, "
            "never dropped."
        )
    unknown = sorted(supplied - required)
    if unknown:
        raise EmitError(
            f"observations carry unknown indicator(s): {unknown}. The "
            "sovereignty cluster under content/metrics/ (and the schema's "
            "required list) is the authority on the set."
        )

    for stable_id in REQUIRED_INDICATORS:
        obs = ctx.observations[stable_id]
        if not isinstance(obs.observed_value, (int, float)) or isinstance(
            obs.observed_value, bool
        ):
            raise EmitError(
                f"observations[{stable_id!r}].observed_value must be a number"
            )
        if obs.threshold_band not in THRESHOLD_BANDS:
            raise EmitError(
                f"observations[{stable_id!r}].threshold_band "
                f"{obs.threshold_band!r} is not in {list(THRESHOLD_BANDS)}"
            )
        observed_at = obs.observed_at
        if observed_at.tzinfo is None:
            raise EmitError(
                f"observations[{stable_id!r}].observed_at must be "
                "timezone-aware (UTC)."
            )
        if not (ctx.window_from <= observed_at <= ctx.window_to):
            raise EmitError(
                f"observations[{stable_id!r}].observed_at "
                f"{observed_at.isoformat()} falls outside the assessment "
                f"window [{ctx.window_from.isoformat()} .. "
                f"{ctx.window_to.isoformat()}] — the window is the honesty "
                "contract about how stale an observation may be."
            )


def _validate_context(ctx: SovereigntyContext) -> None:
    _validate_refs(ctx)
    if ctx.window_from.tzinfo is None or ctx.window_to.tzinfo is None:
        raise EmitError("assessment window bounds must be timezone-aware (UTC).")
    if ctx.window_from > ctx.window_to:
        raise EmitError("assessment window is inverted (from > to).")
    if ctx.attestation_state not in ATTESTATION_STATES:
        raise EmitError(
            f"attestation_state {ctx.attestation_state!r} is not in the "
            f"shared vocabulary {list(ATTESTATION_STATES)} "
            "(schemas/attestation_state.json is the source of truth)."
        )
    _validate_observations(ctx)


def render_sovereignty_artifact(ctx: SovereigntyContext) -> dict[str, Any]:
    """Pure context → record. Does not touch disk.

    Derives nothing from the observations — no score, no ratio, no
    roll-up; the record carries exactly what was observed.
    """
    _validate_context(ctx)

    captured_at_text = _iso8601_z(ctx.captured_at, "captured_at")

    observations: dict[str, Any] = {}
    for stable_id in REQUIRED_INDICATORS:
        obs = ctx.observations[stable_id]
        observations[stable_id] = {
            "observed_value": obs.observed_value,
            "threshold_band": obs.threshold_band,
            "observed_at": _iso8601_z(
                obs.observed_at, f"observations[{stable_id!r}].observed_at"
            ),
        }

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": derive_artifact_id(
            ctx.workflow_id, ctx.execution_id, ctx.compile_target
        ),
        "stream": STREAM,
        "workflow_id": ctx.workflow_id,
        "execution_id": ctx.execution_id,
        "compile_target": ctx.compile_target,
        "regulation_refs": list(ctx.regulation_refs),
        "control_refs": list(ctx.control_refs),
        "assessment_window": {
            "from": _iso8601_z(ctx.window_from, "assessment_window.from"),
            "to": _iso8601_z(ctx.window_to, "assessment_window.to"),
        },
        "observations": observations,
        "attestation_state": ctx.attestation_state,
        "captured_at": captured_at_text,
        "provenance": {
            "source_url": ctx.source_url,
            "captured_at": captured_at_text,
        },
    }
    if ctx.commit_sha:
        record["provenance"]["commit_sha"] = ctx.commit_sha
    return record


def emit_sovereignty_artifact(
    ctx: SovereigntyContext,
    output_dir: str | os.PathLike[str],
) -> Path:
    """Render the record and persist it as ``<artifact_id>.json``.

    Returns the absolute path of the written file. The directory is
    created if it does not exist. Writes atomically through a sibling
    ``.tmp`` then ``os.replace`` so a partial write cannot be read by a
    concurrent consumer. Re-emissions for the same ``(workflow_id,
    execution_id, compile_target)`` land on the same path with
    byte-stable content.
    """
    record = render_sovereignty_artifact(ctx)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{record['artifact_id']}.json"
    tmp_path = out_dir / f".{record['artifact_id']}.json.tmp"
    serialized = json.dumps(record, indent=2, sort_keys=True) + "\n"
    tmp_path.write_text(serialized, encoding="utf-8")
    os.replace(tmp_path, out_path)
    return out_path.resolve()
