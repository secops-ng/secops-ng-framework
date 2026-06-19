"""Incidents evidence-artifact emitter (F-CP-02 SKELETON).

A pure helper that turns one execution of the F-WF-05 incident_management
playbook into one record conforming to
``schemas/evidence/incidents.schema.json`` and writes it to disk.

The emitter is deliberately decoupled from any compile target:

* It does not import ``temporalio``, ``langgraph``, or any n8n shim.
* It does no network I/O. The only side effect is the JSON file it
  writes; the caller chooses the output directory.
* Same context in → same record out → same ``artifact_id``. The id is
  the SHA-256 of ``<incident_id>|<execution_id>`` (UTF-8) per the
  schema's ``artifact_id`` contract, so a replay of the same execution
  re-derives the same id and downstream deduplication is trivial.

The SKELETON keeps the contract small on purpose. One execution per
artifact; the three NIS2 Article 23(4) regulator-notification milestones
land as ordered entries on ``notification_timeline``; ``kpi_windows``
and ``retention`` are optional fields the emitter forwards when the
caller supplies them. CORE-FANOUT carries the n8n and LangGraph
adapters; per-target byte-parity goldens land in the EXTEND-tests
sibling; the NIS2 Art. 21(2)(b) + Art. 23 mapping doc and the ROADMAP
flip each have their own sibling card.

The companion target-side wrapper for the SKELETON is
``compilers.temporal.evidence.incidents_activity``.
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
    "IncidentsContext",
    "ClassificationVerdict",
    "Lifecycle",
    "KpiWindows",
    "NotificationMilestone",
    "derive_artifact_id",
    "emit_incidents_artifact",
    "render_incidents_artifact",
]

# Pin matches the ``schema_version`` const in
# ``schemas/evidence/incidents.schema.json``. Bumped together with the
# schema when a breaking change ships.
SCHEMA_VERSION = "1.0.0"
STREAM = "incidents"

# Canonical vocabularies — kept in lockstep with the supporting schemas.
# Catching shape errors here gives the caller a Python traceback instead
# of a JSON Schema validation error at write time; the schema is still
# the source of truth at persistence.
_SEVERITY_BANDS = frozenset(
    {"Informational", "Low", "Medium", "High", "Critical"}
)
_NOTIFICATION_MILESTONES = frozenset(
    {
        "early_warning_24h",
        "incident_notification_72h",
        "final_report_1mo",
    }
)

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
_CONTROL_REF_RE = re.compile(
    r"^control\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_REGULATION_REF_RE = re.compile(
    r"^(nis2|dora|cra|gdpr|iso27001|soc2):[a-z0-9][a-z0-9.-]*$"
)
_ISO8601_DURATION_RE = re.compile(
    r"^P([0-9]+Y)?([0-9]+M)?([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+S)?)?$"
)
_RULE_ID_RE = re.compile(r"^(sig|cb)\.[a-z][a-z0-9_]*$")
_ISO8601_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$")


class EmitError(ValueError):
    """Raised when the context cannot produce a schema-conforming artifact."""


@dataclass(frozen=True)
class ClassificationVerdict:
    """Deterministic outputs of the F-WF-05 classify-significance primitive.

    Mirrors the ``ClassificationVerdict`` dataclass in
    ``primitives/classification.py`` 1:1 so a workflow step can pass
    its own verdict straight through. ``severity`` and ``summary`` are
    optional — operator-supplied bandwidth that the F-WF-05 final-report
    signature fills in late.
    """

    significant: bool
    cross_border: bool
    reasons: Sequence[str] = field(default_factory=tuple)
    rule_ids: Sequence[str] = field(default_factory=tuple)
    severity: str | None = None
    summary: str | None = None


@dataclass(frozen=True)
class Lifecycle:
    """Lifecycle-marker timestamps the catalog KPIs measure against.

    ``detected_at`` is required (the incident exists from the detection
    instant); every other marker is optional while the incident is open
    and required once the incident is closed. Downstream completeness
    KPI reads against the present set.
    """

    detected_at: datetime
    first_observation_at: datetime | None = None
    triaged_at: datetime | None = None
    contained_at: datetime | None = None
    eradicated_at: datetime | None = None
    recovered_at: datetime | None = None
    closed_at: datetime | None = None


@dataclass(frozen=True)
class KpiWindows:
    """Optional pre-computed KPI windows the emitter may carry.

    All values in minutes; the catalog KPIs may compute these
    themselves from ``lifecycle`` so the fields are entirely optional.
    """

    mttd_minutes: float | None = None
    mttr_minutes: float | None = None
    containment_window_minutes: float | None = None
    eradication_window_minutes: float | None = None


@dataclass(frozen=True)
class NotificationMilestone:
    """One entry on the NIS2 Article 23(4) regulator-notification chain."""

    milestone: str
    clock_started_at: datetime
    submitted_at: datetime
    submission_ref: str | None = None
    on_time: bool | None = None


@dataclass(frozen=True)
class IncidentsContext:
    """One execution of the F-WF-05 incident_management playbook.

    A workflow step builds this dataclass from its own state — the
    incident identifier the F-WF-05 ``timeline_open`` primitive issued,
    the execution id the workflow runtime issued for this run, the
    classification verdict, the lifecycle markers reached so far, the
    regulator-notification milestones submitted, and the ownership
    pointer. ``kpi_windows``, ``reporter_acknowledgement``, ``commit_sha``,
    and ``retention`` are optional bandwidth.

    All fields are validated by the emitter before any JSON is written;
    the schema is the source of truth, but catching the obvious shape
    errors here gives the caller a useful Python traceback instead of a
    JSON Schema validation error at write time.
    """

    incident_id: str
    execution_id: str
    regulation_refs: Sequence[str]
    control_refs: Sequence[str]
    classification: ClassificationVerdict
    lifecycle: Lifecycle
    owner_role: str
    owner_assigned_at: str
    captured_at: datetime
    source_url: str
    notification_timeline: Sequence[NotificationMilestone] = field(
        default_factory=tuple
    )
    kpi_windows: KpiWindows | None = None
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


def derive_artifact_id(incident_id: str, execution_id: str) -> str:
    """SHA-256(``<incident_id>|<execution_id>``) per the schema contract."""
    payload = f"{incident_id}|{execution_id}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_context(ctx: IncidentsContext) -> None:
    if not _UUID_RE.match(ctx.incident_id):
        raise EmitError(
            f"incident_id {ctx.incident_id!r} is not an RFC 4122 UUID as "
            "pinned by the schema"
        )
    if not ctx.execution_id or len(ctx.execution_id) > 200:
        raise EmitError(
            "execution_id must be a non-empty string ≤ 200 chars per the schema"
        )
    if not ctx.regulation_refs:
        raise EmitError(
            "regulation_refs must carry at least one entry; an artifact "
            "with no regulatory anchor is not evidence in the F-CP-02 sense"
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

    cls = ctx.classification
    for rid in cls.rule_ids:
        if not _RULE_ID_RE.match(rid):
            raise EmitError(
                f"classification.rule_ids entry {rid!r} does not match the "
                "(sig|cb).<rule> shape pinned by the schema"
            )
    if cls.severity is not None and cls.severity not in _SEVERITY_BANDS:
        raise EmitError(
            f"classification.severity {cls.severity!r} is not in the "
            f"closed alphabet {sorted(_SEVERITY_BANDS)}"
        )
    if cls.summary is not None and not (1 <= len(cls.summary) <= 4000):
        raise EmitError(
            "classification.summary length must be in [1, 4000] characters "
            "per the schema"
        )

    # Lifecycle: detected_at is required and must be tz-aware; all other
    # markers are optional but must be tz-aware when present. The schema
    # marks them format: date-time.
    if ctx.lifecycle.detected_at.tzinfo is None:
        raise EmitError("lifecycle.detected_at must be timezone-aware (UTC).")
    for name in (
        "first_observation_at",
        "triaged_at",
        "contained_at",
        "eradicated_at",
        "recovered_at",
        "closed_at",
    ):
        value = getattr(ctx.lifecycle, name)
        if value is not None and value.tzinfo is None:
            raise EmitError(
                f"lifecycle.{name} must be timezone-aware (UTC) when set"
            )

    if ctx.kpi_windows is not None:
        for name in (
            "mttd_minutes",
            "mttr_minutes",
            "containment_window_minutes",
            "eradication_window_minutes",
        ):
            value = getattr(ctx.kpi_windows, name)
            if value is not None and value < 0:
                raise EmitError(
                    f"kpi_windows.{name} {value!r} must be non-negative"
                )

    seen_milestones: set[str] = set()
    for entry in ctx.notification_timeline:
        if entry.milestone not in _NOTIFICATION_MILESTONES:
            raise EmitError(
                f"notification_timeline.milestone {entry.milestone!r} is "
                f"not in the promoted vocabulary "
                f"{sorted(_NOTIFICATION_MILESTONES)}"
            )
        # The schema requires uniqueItems on the array. Per (incident_id,
        # execution_id) the workflow submits each stage at most once;
        # surface a duplicate as an emit-time error rather than wait for
        # JSON Schema to flag it on write.
        if entry.milestone in seen_milestones:
            raise EmitError(
                f"notification_timeline carries milestone "
                f"{entry.milestone!r} more than once; the schema marks the "
                "array uniqueItems and the F-WF-05 chain submits each "
                "stage at most once per execution"
            )
        seen_milestones.add(entry.milestone)
        if entry.clock_started_at.tzinfo is None:
            raise EmitError(
                "notification_timeline.clock_started_at must be "
                "timezone-aware (UTC)"
            )
        if entry.submitted_at.tzinfo is None:
            raise EmitError(
                "notification_timeline.submitted_at must be timezone-aware "
                "(UTC)"
            )
        if entry.submission_ref is not None and not (
            1 <= len(entry.submission_ref) <= 200
        ):
            raise EmitError(
                "notification_timeline.submission_ref length must be in "
                "[1, 200] characters per the schema"
            )

    if not ctx.owner_role or not (1 <= len(ctx.owner_role) <= 200):
        raise EmitError(
            "owner_role length must be in [1, 200] characters per the schema"
        )
    if not _ISO8601_DATE_RE.match(ctx.owner_assigned_at):
        raise EmitError(
            f"owner_assigned_at {ctx.owner_assigned_at!r} must be an "
            "ISO-8601 date (YYYY-MM-DD) per the schema"
        )

    if ctx.commit_sha is not None and not _COMMIT_SHA_RE.match(ctx.commit_sha):
        raise EmitError(
            f"commit_sha {ctx.commit_sha!r} must be 7-64 lowercase hex "
            "characters per the schema"
        )

    if ctx.retention is not None and not _ISO8601_DURATION_RE.match(
        ctx.retention
    ):
        raise EmitError(
            f"retention {ctx.retention!r} is not an ISO-8601 duration"
        )


def _render_classification(cls: ClassificationVerdict) -> dict[str, Any]:
    out: dict[str, Any] = {
        "significant": cls.significant,
        "cross_border": cls.cross_border,
        "reasons": list(cls.reasons),
        "rule_ids": list(cls.rule_ids),
    }
    if cls.severity is not None:
        out["severity"] = cls.severity
    if cls.summary is not None:
        out["summary"] = cls.summary
    return out


def _render_lifecycle(lc: Lifecycle) -> dict[str, Any]:
    out: dict[str, Any] = {"detected_at": _iso8601_z(lc.detected_at)}
    if lc.first_observation_at is not None:
        out["first_observation_at"] = _iso8601_z(lc.first_observation_at)
    if lc.triaged_at is not None:
        out["triaged_at"] = _iso8601_z(lc.triaged_at)
    if lc.contained_at is not None:
        out["contained_at"] = _iso8601_z(lc.contained_at)
    if lc.eradicated_at is not None:
        out["eradicated_at"] = _iso8601_z(lc.eradicated_at)
    if lc.recovered_at is not None:
        out["recovered_at"] = _iso8601_z(lc.recovered_at)
    if lc.closed_at is not None:
        out["closed_at"] = _iso8601_z(lc.closed_at)
    return out


def _render_kpi_windows(kw: KpiWindows) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if kw.mttd_minutes is not None:
        out["mttd_minutes"] = kw.mttd_minutes
    if kw.mttr_minutes is not None:
        out["mttr_minutes"] = kw.mttr_minutes
    if kw.containment_window_minutes is not None:
        out["containment_window_minutes"] = kw.containment_window_minutes
    if kw.eradication_window_minutes is not None:
        out["eradication_window_minutes"] = kw.eradication_window_minutes
    return out


def _render_milestone(m: NotificationMilestone) -> dict[str, Any]:
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


def render_incidents_artifact(ctx: IncidentsContext) -> dict[str, Any]:
    """Pure context → record. Does not touch disk.

    Useful for tests, dry-runs, and any compile target that needs the
    record in-memory before persisting it through its own audit channel.
    """
    _validate_context(ctx)

    captured_at_text = _iso8601_z(ctx.captured_at)

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": derive_artifact_id(ctx.incident_id, ctx.execution_id),
        "stream": STREAM,
        "incident_id": ctx.incident_id,
        "execution_id": ctx.execution_id,
        "regulation_refs": list(ctx.regulation_refs),
        "control_refs": list(ctx.control_refs),
        "classification": _render_classification(ctx.classification),
        "lifecycle": _render_lifecycle(ctx.lifecycle),
        "notification_timeline": [
            _render_milestone(m) for m in ctx.notification_timeline
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
    if ctx.kpi_windows is not None:
        windows = _render_kpi_windows(ctx.kpi_windows)
        if windows:
            record["kpi_windows"] = windows
    if ctx.commit_sha:
        record["provenance"]["commit_sha"] = ctx.commit_sha
    if ctx.retention is not None:
        record["retention"] = ctx.retention

    return record


def emit_incidents_artifact(
    ctx: IncidentsContext,
    output_dir: str | os.PathLike[str],
) -> Path:
    """Render the record and persist it as ``<artifact_id>.json``.

    Returns the absolute path of the written file. The directory is
    created if it does not exist. Writes atomically through a sibling
    ``.tmp`` then ``os.replace`` so a partial write cannot be read by a
    concurrent consumer.

    Re-emissions for the same ``(incident_id, execution_id)`` derive the
    same ``artifact_id`` and overwrite the same path with byte-stable
    content. Re-runs of the same incident with a fresh ``execution_id``
    land under a distinct ``artifact_id`` — the regulator-notification
    chain reads re-emission as evidentiary signal rather than dedup
    waste.
    """
    record = render_incidents_artifact(ctx)
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
