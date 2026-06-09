"""Vulnerabilities evidence-artifact emitter (F-CP-04 SKELETON).

A pure helper that turns one execution of the F-WF-01 vulnerability-triage
playbook into one record conforming to
``schemas/evidence/vulns.schema.json`` and writes it to disk.

The emitter is deliberately decoupled from any compile target:

* It does not import ``temporalio``, ``langgraph``, or any n8n shim.
* It does no network I/O. The only side effect is the JSON file it
  writes; the caller chooses the output directory.
* Same context in → same record out → same ``artifact_id``. The id is
  the SHA-256 of ``<case_ref>|<execution_id>`` (UTF-8) per the
  schema's ``artifact_id`` contract, so a replay of the same execution
  re-derives the same id and downstream deduplication is trivial.

The SKELETON keeps the contract small on purpose. One execution per
artifact; the four CRA-timing milestones land as ordered entries on
``disclosure_timeline``; the reporter-acknowledgement event is
optional (omitted for internal scanner findings). CORE-FANOUT carries
the n8n and LangGraph adapters; per-target byte-parity goldens land
in the EXTEND-tests sibling; drift / NIS2 mapping doc / ROADMAP flip
each have their own sibling card.

The companion target-side wrapper for the SKELETON is
``compilers.temporal.evidence.vulns_activity``.
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
    "VulnsContext",
    "TriageDecision",
    "ResponseBranch",
    "DisclosureMilestone",
    "ReporterAcknowledgement",
    "derive_artifact_id",
    "emit_vulns_artifact",
    "render_vulns_artifact",
]

# Pin matches the ``schema_version`` const in
# ``schemas/evidence/vulns.schema.json``. Bumped together with the
# schema when a breaking change ships.
SCHEMA_VERSION = "1.0.0"
STREAM = "vulns"

# Canonical vocabularies — kept in lockstep with the supporting schemas
# under ``schemas/{vuln_response_band,cra_clock_kind,cra_timing_milestone}.json``.
# Catching shape errors here gives the caller a Python traceback instead
# of a JSON Schema validation error at write time; the schema is still
# the source of truth at persistence.
_SEVERITY_BANDS = frozenset({"None", "Low", "Medium", "High", "Critical"})
_RESPONSE_BANDS = frozenset({"critical", "high", "scheduled", "accept"})
_CRA_CLOCKS = frozenset({"none", "article_14_1", "article_14_3"})
_CRA_MILESTONES = frozenset(
    {
        "early_warning_24h",
        "severe_incident_24h",
        "incident_notification_72h",
        "final_report_14d",
    }
)
_DEDUP_OUTCOMES = frozenset({"new", "duplicate"})

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_CONTROL_REF_RE = re.compile(
    r"^control\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_REGULATION_REF_RE = re.compile(
    r"^(nis2|dora|cra|gdpr|iso27001|soc2):[a-z0-9][a-z0-9.-]*$"
)
_ISO8601_DURATION_RE = re.compile(
    r"^P([0-9]+Y)?([0-9]+M)?([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+S)?)?$"
)
_CVSS_VECTOR_RE = re.compile(r"^CVSS:(3\.0|3\.1|4\.0)/.+$")


class EmitError(ValueError):
    """Raised when the context cannot produce a schema-conforming artifact."""


@dataclass(frozen=True)
class TriageDecision:
    """Deterministic outputs of the F-WF-01 triage step.

    ``severity`` and ``cvss_severity`` follow the CVSS qualitative
    alphabet; ``cra_clock`` and ``dedup_outcome`` follow the promoted
    enums under ``schemas/{cra_clock_kind,…}.json``.
    """

    severity: str
    cvss_severity: str
    cra_clock: str
    dedup_outcome: str
    cvss_base_score: float | None = None
    cvss_vector: str | None = None
    epss_probability: float | None = None
    actively_exploited: bool | None = None
    dedup_collided_with: str | None = None
    risk_summary: str | None = None


@dataclass(frozen=True)
class ResponseBranch:
    """Response branch the triaged case was routed onto.

    ``band`` is one of ``critical`` / ``high`` / ``scheduled`` /
    ``accept``. ``accept_rationale`` is required when ``band == 'accept'``;
    everything else is optional and shaped by the schema.
    """

    band: str
    case_opened_at: datetime | None = None
    patch_disseminated_at: datetime | None = None
    advisory_ref: str | None = None
    accept_rationale: str | None = None
    compensating_controls: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class DisclosureMilestone:
    """One entry on the CRA Article 14 regulator-notification chain."""

    milestone: str
    clock_started_at: datetime
    submitted_at: datetime
    submission_ref: str | None = None
    on_time: bool | None = None


@dataclass(frozen=True)
class ReporterAcknowledgement:
    """CVD-intake acknowledgement event. Optional on the context."""

    disclosure_received_at: datetime
    acknowledged_at: datetime
    sla_duration: str | None = None


@dataclass(frozen=True)
class VulnsContext:
    """One execution of the F-WF-01 vulnerability-triage playbook.

    A workflow step builds this dataclass from its own state — the case
    identifier the dedup primitive issued upstream, the execution id the
    workflow runtime issued for this run, the triage outputs, the
    response branch the case was routed onto, the disclosure-timeline
    milestones reached so far, and (for CVD intakes) the reporter
    acknowledgement event.

    All fields are validated by the emitter before any JSON is written;
    the schema is the source of truth, but catching the obvious shape
    errors here gives the caller a useful Python traceback instead of a
    JSON Schema validation error at write time.
    """

    case_ref: str
    execution_id: str
    regulation_refs: Sequence[str]
    control_refs: Sequence[str]
    triage_decision: TriageDecision
    response: ResponseBranch
    owner_role: str
    owner_assigned_at: str
    captured_at: datetime
    source_url: str
    disclosure_timeline: Sequence[DisclosureMilestone] = field(default_factory=tuple)
    reporter_acknowledgement: ReporterAcknowledgement | None = None
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


def derive_artifact_id(case_ref: str, execution_id: str) -> str:
    """SHA-256(``<case_ref>|<execution_id>``) per the schema contract."""
    payload = f"{case_ref}|{execution_id}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_context(ctx: VulnsContext) -> None:
    if not _HEX64_RE.match(ctx.case_ref):
        raise EmitError(
            f"case_ref {ctx.case_ref!r} is not a 64-character lowercase hex "
            "digest as pinned by the schema"
        )
    if not ctx.execution_id or len(ctx.execution_id) > 200:
        raise EmitError(
            "execution_id must be a non-empty string ≤ 200 chars per the schema"
        )
    if not ctx.regulation_refs:
        raise EmitError(
            "regulation_refs must carry at least one entry; an artifact "
            "with no regulatory anchor is not evidence in the F-CP-04 sense"
        )
    for ref in ctx.regulation_refs:
        if not _REGULATION_REF_RE.match(ref):
            raise EmitError(
                f"regulation_ref {ref!r} does not match the "
                "<regime>:<id> shape pinned by the schema"
            )
    if not ctx.control_refs:
        raise EmitError(
            "control_refs must carry at least one entry per the schema"
        )
    for cref in ctx.control_refs:
        if not _CONTROL_REF_RE.match(cref):
            raise EmitError(
                f"control_ref {cref!r} does not match the "
                "control.<id>@v<n> shape pinned by the schema"
            )

    td = ctx.triage_decision
    if td.severity not in _SEVERITY_BANDS:
        raise EmitError(
            f"triage_decision.severity {td.severity!r} is not in the CVSS "
            f"qualitative alphabet {sorted(_SEVERITY_BANDS)}"
        )
    if td.cvss_severity not in _SEVERITY_BANDS:
        raise EmitError(
            f"triage_decision.cvss_severity {td.cvss_severity!r} is not in "
            f"the CVSS qualitative alphabet {sorted(_SEVERITY_BANDS)}"
        )
    if td.cra_clock not in _CRA_CLOCKS:
        raise EmitError(
            f"triage_decision.cra_clock {td.cra_clock!r} is not in the "
            f"promoted vocabulary {sorted(_CRA_CLOCKS)}"
        )
    if td.dedup_outcome not in _DEDUP_OUTCOMES:
        raise EmitError(
            f"triage_decision.dedup_outcome {td.dedup_outcome!r} must be "
            "'new' or 'duplicate'"
        )
    if td.dedup_outcome == "duplicate" and not td.dedup_collided_with:
        raise EmitError(
            "triage_decision.dedup_collided_with is required when "
            "dedup_outcome == 'duplicate'"
        )
    if td.dedup_collided_with is not None and not _HEX64_RE.match(
        td.dedup_collided_with
    ):
        raise EmitError(
            f"triage_decision.dedup_collided_with {td.dedup_collided_with!r} "
            "must be a 64-character lowercase hex digest"
        )
    if td.cvss_base_score is not None and not 0.0 <= td.cvss_base_score <= 10.0:
        raise EmitError(
            f"triage_decision.cvss_base_score {td.cvss_base_score!r} must be "
            "in [0.0, 10.0]"
        )
    if td.cvss_vector is not None and not _CVSS_VECTOR_RE.match(td.cvss_vector):
        raise EmitError(
            f"triage_decision.cvss_vector {td.cvss_vector!r} must begin "
            "with CVSS:3.0/, CVSS:3.1/, or CVSS:4.0/"
        )
    if td.epss_probability is not None and not 0.0 <= td.epss_probability <= 1.0:
        raise EmitError(
            f"triage_decision.epss_probability {td.epss_probability!r} must "
            "be in [0.0, 1.0]"
        )

    rb = ctx.response
    if rb.band not in _RESPONSE_BANDS:
        raise EmitError(
            f"response.band {rb.band!r} is not in the promoted vocabulary "
            f"{sorted(_RESPONSE_BANDS)}"
        )
    if rb.band == "accept" and not rb.accept_rationale:
        raise EmitError(
            "response.accept_rationale is required when response.band == 'accept'"
        )
    if rb.band != "accept" and rb.accept_rationale:
        raise EmitError(
            "response.accept_rationale must be omitted when response.band != 'accept'"
        )
    for cref in rb.compensating_controls:
        if not _CONTROL_REF_RE.match(cref):
            raise EmitError(
                f"response.compensating_controls entry {cref!r} does not "
                "match the control.<id>@v<n> shape"
            )

    for entry in ctx.disclosure_timeline:
        if entry.milestone not in _CRA_MILESTONES:
            raise EmitError(
                f"disclosure_timeline.milestone {entry.milestone!r} is not "
                f"in the promoted vocabulary {sorted(_CRA_MILESTONES)}"
            )

    if ctx.retention is not None and not _ISO8601_DURATION_RE.match(ctx.retention):
        raise EmitError(
            f"retention {ctx.retention!r} is not an ISO-8601 duration"
        )


def _render_triage(td: TriageDecision) -> dict[str, Any]:
    out: dict[str, Any] = {
        "severity": td.severity,
        "cvss_severity": td.cvss_severity,
        "cra_clock": td.cra_clock,
        "dedup_outcome": td.dedup_outcome,
    }
    if td.cvss_base_score is not None:
        out["cvss_base_score"] = td.cvss_base_score
    if td.cvss_vector is not None:
        out["cvss_vector"] = td.cvss_vector
    if td.epss_probability is not None:
        out["epss_probability"] = td.epss_probability
    if td.actively_exploited is not None:
        out["actively_exploited"] = td.actively_exploited
    if td.dedup_collided_with is not None:
        out["dedup_collided_with"] = td.dedup_collided_with
    if td.risk_summary is not None:
        out["risk_summary"] = td.risk_summary
    return out


def _render_response(rb: ResponseBranch) -> dict[str, Any]:
    out: dict[str, Any] = {"band": rb.band}
    if rb.case_opened_at is not None:
        out["case_opened_at"] = _iso8601_z(rb.case_opened_at)
    if rb.patch_disseminated_at is not None:
        out["patch_disseminated_at"] = _iso8601_z(rb.patch_disseminated_at)
    if rb.advisory_ref is not None:
        out["advisory_ref"] = rb.advisory_ref
    if rb.accept_rationale is not None:
        out["accept_rationale"] = rb.accept_rationale
    if rb.compensating_controls:
        out["compensating_controls"] = list(rb.compensating_controls)
    return out


def _render_milestone(m: DisclosureMilestone) -> dict[str, Any]:
    out: dict[str, Any] = {
        "milestone": m.milestone,
        "clock_started_at": _iso8601_z(m.clock_started_at),
        "submitted_at": _iso8601_z(m.submitted_at),
    }
    if m.submission_ref is not None:
        out["submission_ref"] = m.submission_ref
    if m.on_time is not None:
        out["on_time"] = m.on_time
    return out


def _render_ack(ack: ReporterAcknowledgement) -> dict[str, Any]:
    out: dict[str, Any] = {
        "disclosure_received_at": _iso8601_z(ack.disclosure_received_at),
        "acknowledged_at": _iso8601_z(ack.acknowledged_at),
    }
    if ack.sla_duration is not None:
        out["sla_duration"] = ack.sla_duration
    return out


def render_vulns_artifact(ctx: VulnsContext) -> dict[str, Any]:
    """Pure context → record. Does not touch disk.

    Useful for tests, dry-runs, and any compile target that needs the
    record in-memory before persisting it through its own audit channel.
    """
    _validate_context(ctx)

    captured_at_text = _iso8601_z(ctx.captured_at)

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": derive_artifact_id(ctx.case_ref, ctx.execution_id),
        "stream": STREAM,
        "case_ref": ctx.case_ref,
        "execution_id": ctx.execution_id,
        "regulation_refs": list(ctx.regulation_refs),
        "control_refs": list(ctx.control_refs),
        "triage_decision": _render_triage(ctx.triage_decision),
        "response": _render_response(ctx.response),
        "disclosure_timeline": [
            _render_milestone(m) for m in ctx.disclosure_timeline
        ],
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

    if ctx.reporter_acknowledgement is not None:
        record["reporter_acknowledgement"] = _render_ack(
            ctx.reporter_acknowledgement
        )

    if ctx.retention is not None:
        record["retention"] = ctx.retention

    return record


def emit_vulns_artifact(
    ctx: VulnsContext,
    output_dir: str | os.PathLike[str],
) -> Path:
    """Render the record and persist it as ``<artifact_id>.json``.

    Returns the absolute path of the written file. The directory is
    created if it does not exist. Writes atomically through a sibling
    ``.tmp`` then ``os.replace`` so a partial write cannot be read by a
    concurrent consumer.

    Re-emissions for the same ``(case_ref, execution_id)`` derive the
    same ``artifact_id`` and overwrite the same path with byte-stable
    content. Re-runs of the same case with a fresh ``execution_id``
    land under a distinct ``artifact_id`` — the regulator-notification
    chain reads re-emission as evidentiary signal rather than dedup
    waste.
    """
    record = render_vulns_artifact(ctx)
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
