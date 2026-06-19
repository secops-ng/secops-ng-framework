"""Codebase disclosure-timeline evidence-artifact emitter (F-WF-07 CORE-N8N).

A pure helper that turns one ``assess-disclosure`` / ``track-timeline``
walk over one (SBOM, advisory, component) finding into one record
conforming to
``content/evidence/codebase_vuln_management/disclosure-timeline-record.schema.json``
and writes it to disk.

The emitter is deliberately decoupled from any compile target:

* It does not import ``temporalio``, ``langgraph``, or any n8n shim.
* It does no network I/O. The only side effect is the JSON file it
  writes; the caller chooses the output directory.
* Same context in → same record out → same ``id``. The id is the
  SHA-256 of
  ``<workflow_id>|<sbom_content_hash>|<component.purl>|<advisory_id>``
  (UTF-8, no separators around the pipes) per the schema's ``id``
  contract, so a re-walk of the same SBOM against the same advisory
  re-derives the same id and downstream deduplication is trivial.
  ``captured_at`` is deliberately *not* part of the id — a re-emission
  inside the same workflow case stays byte-identical at the path
  level.

The CORE-N8N keeps the contract small on purpose. One finding per
record; the underlying advisory payload is *not* embedded — the
``source_data`` pointer is the public-bar-safe surface, and any
personal data in the raw payload is out of scope per AGENTS.md §3.

The companion target-side wrapper for this CORE-N8N is
``compilers.n8n.evidence.disclosure_timeline_node``. Temporal and
LangGraph wrappers are separate CORE-TEMPORAL / CORE-LANGGRAPH
siblings. Per-target byte-parity goldens, cookbook walkthrough, and
ROADMAP flip each have their own sibling card.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

__all__ = [
    "DisclosureTimelineContext",
    "ComponentRef",
    "DisclosureWindow",
    "SourceData",
    "derive_artifact_id",
    "emit_disclosure_timeline_artifact",
    "render_disclosure_timeline_artifact",
]

# Pin matches the ``schema_version`` const in
# ``content/evidence/codebase_vuln_management/disclosure-timeline-record.schema.json``.
# Bumped together with the schema when a breaking change ships.
SCHEMA_VERSION = "0.1.0"
STREAM = "codebase_vuln_management"
WORKFLOW_ID = "codebase_vuln_management"

# Canonical regexes — kept in lockstep with the schema. Catching shape
# errors here gives the caller a Python traceback instead of a JSON
# Schema validation error at write time; the schema is still the
# source of truth at persistence.
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_WORKFLOW_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$")
_ADVISORY_ID_RE = re.compile(
    r"^(CVE-[0-9]{4}-[0-9]+"
    r"|GHSA-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}"
    r"|OSV-[0-9]{4}-[0-9]+"
    r"|[A-Z][A-Z0-9._-]{1,60})$"
)
_PURL_RE = re.compile(r"^pkg:[a-z][a-z0-9+.\-]*/")
_POLICY_REF_RE = re.compile(
    r"^policy\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_VIZ_REF_RE = re.compile(
    r"^viz\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_TELEMETRY_REF_RE = re.compile(
    r"^telemetry\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_ISO8601_Z_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)

_SEVERITIES = frozenset({"critical", "high", "medium", "low"})
_SOURCE_KINDS = frozenset({"ocsf", "telemetry", "none"})


class EmitError(ValueError):
    """Raised when the context cannot produce a schema-conforming artifact."""


@dataclass(frozen=True)
class ComponentRef:
    """The affected component+version pair as pinned against the SBOM.

    PURL-shaped so the record joins back into the SBOM artefact at
    ``sbom_content_hash`` without ambiguity. ``version`` is a string so
    non-semver ecosystems (Debian epoch versions, Maven qualifiers)
    round-trip unchanged.
    """

    purl: str
    version: str


@dataclass(frozen=True)
class DisclosureWindow:
    """Disclosure-window deadlines under the operator's CVD policy.

    ``policy_ref`` pins which CVD-policy revision the deadlines were
    computed against; the three ``..._by`` fields are timezone-aware
    UTC ``datetime`` instances that the emitter canonicalises to the
    ISO-8601 ``...Z`` string the schema pattern requires.
    """

    policy_ref: str
    acknowledge_by: datetime
    fix_by: datetime
    disclose_by: datetime


@dataclass(frozen=True)
class SourceData:
    """Source-shape pointer for the finding.

    Mirror of the F-CP-06 effectiveness-snapshot ``source_shape``
    discipline (G-04 metric field shape). The underlying advisory
    payload is deliberately not embedded — this pointer is the
    public-bar-safe surface.
    """

    kind: str
    ocsf_class_uid: int | None = None
    telemetry_ref: str | None = None


@dataclass(frozen=True)
class DisclosureTimelineContext:
    """One finding produced by the codebase_vuln_management workflow.

    A workflow step (``assess-disclosure`` resolving into
    ``track-timeline``) builds this dataclass from its own state — the
    SBOM content hash pinned at ingest, the advisory the finding
    matched against, the affected component+version, the assessed
    severity tier, the disclosure-window deadlines under the
    operator's CVD policy, and the source-shape pointer for the
    underlying payload.

    All fields are validated by the emitter before any JSON is
    written; the schema is the source of truth, but catching the
    obvious shape errors here gives the caller a useful Python
    traceback instead of a JSON Schema validation error at write
    time.
    """

    sbom_content_hash: str
    advisory_id: str
    component: ComponentRef
    severity: str
    disclosure_window: DisclosureWindow
    source_data: SourceData
    ref_viz: str
    captured_at: datetime
    workflow_id: str = WORKFLOW_ID


def _iso8601_z(dt: datetime) -> str:
    """Render a UTC ``datetime`` as a stable ISO-8601 ``...Z`` string.

    Several schema fields use the strict ``YYYY-MM-DDTHH:MM:SSZ``
    shape with second precision — we canonicalise here rather than
    trust the caller's ``isoformat``.
    """
    if dt.tzinfo is None:
        raise EmitError("datetime must be timezone-aware (UTC).")
    dt_utc = dt.astimezone(timezone.utc).replace(microsecond=0)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def derive_artifact_id(
    workflow_id: str,
    sbom_content_hash: str,
    component_purl: str,
    advisory_id: str,
) -> str:
    """SHA-256(``<workflow_id>|<sbom_content_hash>|<purl>|<advisory_id>``).

    Matches the ``id`` contract on the schema verbatim. Deterministic
    on those four inputs so a re-walk of the same SBOM against the
    same advisory re-derives the same id.
    """
    payload = (
        f"{workflow_id}|{sbom_content_hash}|{component_purl}|{advisory_id}"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_context(ctx: DisclosureTimelineContext) -> None:
    if not _WORKFLOW_ID_RE.match(ctx.workflow_id):
        raise EmitError(
            f"workflow_id {ctx.workflow_id!r} does not match the "
            "snake_case dotted shape pinned by the schema"
        )
    if not _HEX64_RE.match(ctx.sbom_content_hash):
        raise EmitError(
            f"sbom_content_hash {ctx.sbom_content_hash!r} must be a "
            "lowercase 64-hex SHA-256 digest"
        )
    if not _ADVISORY_ID_RE.match(ctx.advisory_id):
        raise EmitError(
            f"advisory_id {ctx.advisory_id!r} does not match the "
            "CVE / GHSA / OSV / vendor advisory shape pinned by the schema"
        )
    if not _PURL_RE.match(ctx.component.purl):
        raise EmitError(
            f"component.purl {ctx.component.purl!r} does not match the "
            "pkg:<type>/... shape pinned by the schema"
        )
    if not ctx.component.version:
        raise EmitError("component.version must be a non-empty string")
    if ctx.severity not in _SEVERITIES:
        raise EmitError(
            f"severity {ctx.severity!r} must be one of {sorted(_SEVERITIES)}"
        )
    win = ctx.disclosure_window
    if not _POLICY_REF_RE.match(win.policy_ref):
        raise EmitError(
            f"disclosure_window.policy_ref {win.policy_ref!r} does not match "
            "the policy.<id>@v<n> shape pinned by the schema"
        )
    if not _VIZ_REF_RE.match(ctx.ref_viz):
        raise EmitError(
            f"ref_viz {ctx.ref_viz!r} does not match the viz.<id>@v<n> shape "
            "pinned by the schema"
        )
    src = ctx.source_data
    if src.kind not in _SOURCE_KINDS:
        raise EmitError(
            f"source_data.kind {src.kind!r} must be one of "
            f"{sorted(_SOURCE_KINDS)}"
        )
    if src.kind == "ocsf":
        if src.ocsf_class_uid is None or src.ocsf_class_uid < 0:
            raise EmitError(
                "source_data.kind=ocsf requires a non-negative "
                "ocsf_class_uid"
            )
        if src.telemetry_ref is not None:
            raise EmitError(
                "source_data.telemetry_ref must be absent when kind=ocsf"
            )
    elif src.kind == "telemetry":
        if not src.telemetry_ref or not _TELEMETRY_REF_RE.match(
            src.telemetry_ref
        ):
            raise EmitError(
                "source_data.kind=telemetry requires a telemetry_ref "
                "matching telemetry.<id>@v<n>"
            )
        if src.ocsf_class_uid is not None:
            raise EmitError(
                "source_data.ocsf_class_uid must be absent when kind=telemetry"
            )
    else:  # none
        if src.ocsf_class_uid is not None or src.telemetry_ref is not None:
            raise EmitError(
                "source_data.kind=none must carry neither ocsf_class_uid "
                "nor telemetry_ref"
            )


def render_disclosure_timeline_artifact(
    ctx: DisclosureTimelineContext,
) -> dict[str, Any]:
    """Pure context → record. Does not touch disk.

    Useful for tests, dry-runs, and any compile target that needs the
    record in-memory before persisting it through its own audit
    channel.
    """
    _validate_context(ctx)

    captured_at_text = _iso8601_z(ctx.captured_at)

    window: dict[str, Any] = {
        "policy_ref": ctx.disclosure_window.policy_ref,
        "acknowledge_by": _iso8601_z(ctx.disclosure_window.acknowledge_by),
        "fix_by": _iso8601_z(ctx.disclosure_window.fix_by),
        "disclose_by": _iso8601_z(ctx.disclosure_window.disclose_by),
    }

    source_data: dict[str, Any] = {"kind": ctx.source_data.kind}
    if ctx.source_data.kind == "ocsf":
        source_data["ocsf_class_uid"] = ctx.source_data.ocsf_class_uid
    elif ctx.source_data.kind == "telemetry":
        source_data["telemetry_ref"] = ctx.source_data.telemetry_ref

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "id": derive_artifact_id(
            ctx.workflow_id,
            ctx.sbom_content_hash,
            ctx.component.purl,
            ctx.advisory_id,
        ),
        "stream": STREAM,
        "workflow_id": ctx.workflow_id,
        "sbom_content_hash": ctx.sbom_content_hash,
        "advisory_id": ctx.advisory_id,
        "component": {
            "purl": ctx.component.purl,
            "version": ctx.component.version,
        },
        "severity": ctx.severity,
        "disclosure_window": window,
        "source_data": source_data,
        "ref_viz": ctx.ref_viz,
        "captured_at": captured_at_text,
    }
    return record


def emit_disclosure_timeline_artifact(
    ctx: DisclosureTimelineContext,
    output_dir: str | os.PathLike[str],
) -> Path:
    """Render the record and persist it as ``<id>.json``.

    Returns the absolute path of the written file. The directory is
    created if it does not exist. Writes atomically through a sibling
    ``.tmp`` then ``os.replace`` so a partial write cannot be read by
    a concurrent consumer.
    """
    record = render_disclosure_timeline_artifact(ctx)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{record['id']}.json"
    tmp_path = out_dir / f".{record['id']}.json.tmp"
    serialized = json.dumps(record, indent=2, sort_keys=True) + "\n"
    tmp_path.write_text(serialized, encoding="utf-8")
    os.replace(tmp_path, out_path)
    return out_path.resolve()
