"""DORA Article 19 technical-incident report-variant emitter (F-SV-03 CORE).

A framework-agnostic pure helper that turns one regulator-submission
milestone on the F-WF-05 ``incident_management`` timeline into one
record conforming to
``schemas/evidence/dora-art19-technical-incident-report.schema.json``
and writes it to disk.

The emitter is decoupled from any compile target:

* It does not import ``temporalio``, ``langgraph``, or any n8n shim.
* It does no network I/O. The only side effect is the JSON file it
  writes; the caller chooses the output directory.
* Same context in → same record out → same ``report_id``. The id is
  ``SHA-256(<incident_id>|<report_variant>|<submitted_at>)`` per the
  schema's ``report_id`` contract, so a replay of the same submission
  is byte-identical and downstream deduplication is trivial.

One report record is produced per ``(incident_id, report_variant)``
on the DORA Article 19 chain (Regulation (EU) 2022/2554 Article 19(4)).
The four enum values map onto F-WF-05 timeline events as follows:

* ``initial_4h`` — derived from the ``early_warning`` regulator
  submission.
* ``intermediate_72h`` — derived from the ``notification`` regulator
  submission.
* ``final_1mo`` — derived from the ``final_report`` regulator
  submission.
* ``voluntary_cyber_threat`` — Article 19(2) voluntary notification;
  no mandatory clock and no F-WF-05 stage analogue. The operator
  threads the awareness instant in via the context.

Cross-milestone field derivations (``previous_milestone_event_id``)
are resolved by the emitter from the timeline-event log carried in
the context: intermediate_72h pins the early-warning event id, final_1mo
pins the notification event id. The emitter fails closed when the
required cross-milestone reference is absent.

Public-bar artifact: no individual personal names, no operator
branding, no internal infrastructure references. The schema's
``additionalProperties: false`` envelopes and the explicit closed
alphabets defend against silent shape drift.

The companion target-side wrappers for this emitter live at:

* ``compilers.n8n.evidence.dora_art19_report_node`` — n8n adapter.
* ``compilers.temporal.evidence.dora_art19_report_activity`` —
  Temporal activity.
* ``compilers.langgraph.evidence.dora_art19_report_node`` — LangGraph
  node.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

__all__ = [
    "DoraArt19ReportContext",
    "DoraClassification",
    "TimelineRefs",
    "ImpactIndicators",
    "MitigationStatus",
    "REPORT_VARIANTS",
    "STAGE_TO_REPORT_VARIANT",
    "DEFAULT_REGULATION_REFS",
    "PREVIOUS_MILESTONE_STAGE",
    "DoraArt19EmitError",
    "derive_report_id",
    "emit_dora_art19_report",
    "render_dora_art19_report",
]

# Pin matches the ``schema_version`` const in
# ``schemas/evidence/dora-art19-technical-incident-report.schema.json``.
# SKELETON layer carried "0.1.0"; CORE lifts to "1.0.0" now the
# per-target emitters land. Bumped together with the schema when a
# breaking change ships.
SCHEMA_VERSION = "1.0.0"

# Closed alphabets — kept in lockstep with the supporting schemas.
# Catching shape errors here gives the caller a Python traceback
# instead of a JSON Schema validation error at write time; the schema
# is still the source of truth at persistence.
ReportVariant = Literal[
    "initial_4h",
    "intermediate_72h",
    "final_1mo",
    "voluntary_cyber_threat",
]
REPORT_VARIANTS: tuple[ReportVariant, ...] = (
    "initial_4h",
    "intermediate_72h",
    "final_1mo",
    "voluntary_cyber_threat",
)

DataLossBand = Literal[
    "none",
    "confidentiality",
    "integrity",
    "availability",
    "multiple",
    "unknown",
]
_DATA_LOSS_BANDS = frozenset(
    {"none", "confidentiality", "integrity", "availability", "multiple", "unknown"}
)

MitigationState = Literal[
    "in_flight", "partially_mitigated", "remediated", "unknown"
]
_MITIGATION_STATES = frozenset(
    {"in_flight", "partially_mitigated", "remediated", "unknown"}
)

# Map each F-WF-05 regulator-submission stage to the DORA Art. 19
# report variant it produces. Authoritative pin documented in
# ``content/mappings/dora/article-19-report-variant.md``.
STAGE_TO_REPORT_VARIANT: Mapping[str, ReportVariant] = {
    "early_warning": "initial_4h",
    "notification": "intermediate_72h",
    "final_report": "final_1mo",
}

# Cross-milestone pin: which prior stage's event_id populates
# ``previous_milestone_event_id`` on the current variant. The
# initial_4h and voluntary_cyber_threat variants have no prior
# milestone.
PREVIOUS_MILESTONE_STAGE: Mapping[ReportVariant, str | None] = {
    "initial_4h": None,
    "intermediate_72h": "early_warning",
    "final_1mo": "notification",
    "voluntary_cyber_threat": None,
}

# Default regulation_refs per variant. The mapping back into
# ``content/mappings/dora/article-19-and-28.yaml`` is pinned by the
# drift guard in
# ``tests/content_model/test_dora_art19_report_variant_schema.py``.
DEFAULT_REGULATION_REFS: Mapping[ReportVariant, tuple[str, ...]] = {
    "initial_4h": ("dora:art-19-initial-4h",),
    "intermediate_72h": ("dora:art-19-intermediate-72h",),
    "final_1mo": ("dora:art-19-final-one-month",),
    "voluntary_cyber_threat": ("dora:art-19-cyber-threat-voluntary",),
}


_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
_REGULATION_REF_RE = re.compile(r"^dora:[a-z0-9][a-z0-9.-]*$")
_RULE_ID_RE = re.compile(r"^[a-z][a-z0-9_.]*$")
_EVENT_ID_RE = re.compile(r"^[0-9a-f]{16}$")
_ISO3166_RE = re.compile(r"^[A-Z]{2}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$")


class DoraArt19EmitError(ValueError):
    """Raised when the context cannot produce a schema-conforming report."""


# ---------------------------------------------------------------------------
# Context dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DoraClassification:
    """Deterministic outputs of the DORA Article 18(1) major-incident classifier.

    Mirrors the
    :class:`content.playbooks.incident_management.primitives.classification.ClassificationVerdict`
    shape so a workflow step can pass its own verdict through. The
    ``major`` flag is the DORA-side equivalent of the NIS2 ``significant``
    flag; the operator is responsible for not filing an Art. 19 report
    at all when ``major == False``.

    Per the F-WF-05 gap inventory, the DORA-aware classifier rule pack
    is a separate sibling card (CORE-CLASSIFIER). When that card lands,
    callers populate ``rule_ids`` with the ``dora.<class>.<rule>``
    alphabet directly; until then the emitter accepts any
    snake_case rule id (pattern ``^[a-z][a-z0-9_.]*$``).
    """

    major: bool
    reasons: Sequence[str] = field(default_factory=tuple)
    rule_ids: Sequence[str] = field(default_factory=tuple)
    cross_border: bool | None = None
    recurring_incident: bool | None = None


@dataclass(frozen=True)
class TimelineRefs:
    """F-WF-05 timeline pointers the report variant binds against.

    ``timeline_handle`` is carried verbatim from
    :class:`primitives.timeline_binding.TimelineSession.handle`.
    ``clock_started_at`` is :attr:`TimelineSession.opened_at` for the
    chain variants and the operator-supplied awareness instant for
    ``voluntary_cyber_threat``. ``stage_event_id`` is the
    :class:`primitives.timeline_binding.TimelineEvent.event_id` of the
    regulator-submission event the report corresponds to.

    ``previous_milestone_event_id`` is resolved by the emitter from
    the ``timeline_events`` log on :class:`DoraArt19ReportContext` and
    must not be set on the context directly — the field is computed
    so a forged shape cannot bypass the cross-milestone pin.
    """

    timeline_handle: str
    clock_started_at: datetime
    stage_event_id: str


@dataclass(frozen=True)
class ImpactIndicators:
    """Per-Art. 19(4) impact indicators populated incrementally.

    The shape is intentionally permissive at the CORE layer — most
    fields are operator-supplied per the operator's own CACAO
    variables. The Commission ITS (EU) 2024/2956 field-level
    vocabulary tightening is deferred to the EXTEND-schema sibling
    card; the emitter rejects shapes that would fail the schema's
    additionalProperties:false envelope today.
    """

    affected_functions: Sequence[str] = field(default_factory=tuple)
    affected_clients_count: int | None = None
    duration_minutes: float | None = None
    geographic_scope: Sequence[str] = field(default_factory=tuple)
    data_loss_indicator: DataLossBand | None = None
    indicators_of_compromise: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class MitigationStatus:
    """Per-milestone mitigation status.

    For ``initial_4h`` / ``intermediate_72h`` the state is typically
    ``in_flight`` or ``partially_mitigated`` and ``actions_in_flight``
    carries the in-progress action summaries; ``root_cause`` and
    ``residual_risk`` are ``None`` until the final_1mo milestone, at
    which point the F-WF-05
    :class:`primitives.regulator_submission.FinalReportSubmission`
    populates them.
    """

    state: MitigationState
    actions_in_flight: Sequence[str] = field(default_factory=tuple)
    completed_actions: Sequence[str] = field(default_factory=tuple)
    root_cause: str | None = None
    residual_risk: str | None = None


@dataclass(frozen=True)
class DoraArt19ReportContext:
    """One DORA Article 19 report-variant emission.

    A workflow step builds this dataclass from its own state — the
    incident identifier the F-WF-05 ``open_timeline`` primitive
    issued, the report_variant, the classification verdict, the
    timeline pointers, and the per-milestone impact / mitigation
    bandwidth. ``timeline_events`` is the ordered tuple of
    :class:`TimelineEvent`-shaped records (or mappings carrying
    ``stage`` and ``event_id``) the F-WF-05 timeline has accumulated
    so far; the emitter uses it to resolve cross-milestone
    references.

    The framework ships **no default** ``submission_ref`` — when an
    operator wires a real regulator-portal receipt id, CSIRT ticket
    id, or URN, they thread it through. Public-bar artifact: no
    individual names, no operator branding, no internal infrastructure
    references on any free-text field.
    """

    incident_id: str
    report_variant: ReportVariant
    classification: DoraClassification
    timeline_refs: TimelineRefs
    impact_indicators: ImpactIndicators
    mitigation_status: MitigationStatus
    submitted_at: datetime
    source_url: str
    timeline_events: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    regulation_refs: Sequence[str] | None = None
    submission_ref: str | None = None
    commit_sha: str | None = None


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def _iso8601_z(dt: datetime) -> str:
    """Render a UTC ``datetime`` as a stable ISO-8601 ``...Z`` string.

    The schema marks timestamps ``format: date-time``; we canonicalise
    here so renders are deterministic and goldens stay byte-stable.
    """
    if dt.tzinfo is None:
        raise DoraArt19EmitError("timestamp must be timezone-aware (UTC).")
    dt_utc = dt.astimezone(timezone.utc).replace(microsecond=0)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def derive_report_id(
    incident_id: str, report_variant: str, submitted_at: datetime
) -> str:
    """SHA-256(``<incident_id>|<report_variant>|<submitted_at>``).

    The submitted_at instant is rendered through the same canonical
    ISO-8601 ``...Z`` formatter the report carries so a replay of the
    same submission at the same instant produces a byte-identical id.
    """
    payload = (
        f"{incident_id}|{report_variant}|{_iso8601_z(submitted_at)}"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _resolve_previous_milestone_event_id(
    ctx: DoraArt19ReportContext,
) -> str | None:
    """Resolve ``previous_milestone_event_id`` from the timeline events.

    For ``intermediate_72h`` and ``final_1mo`` the field is required;
    a missing prior event fails the emission closed. For ``initial_4h``
    and ``voluntary_cyber_threat`` the field is unset.
    """
    prior_stage = PREVIOUS_MILESTONE_STAGE.get(ctx.report_variant)
    if prior_stage is None:
        return None
    for event in ctx.timeline_events:
        if event.get("stage") == prior_stage:
            event_id = event.get("event_id")
            if not isinstance(event_id, str):
                raise DoraArt19EmitError(
                    f"timeline event for stage {prior_stage!r} carries a "
                    "non-string event_id; the timeline-event log must "
                    "carry the canonical 16-hex-digit event_id strings."
                )
            return event_id
    raise DoraArt19EmitError(
        f"report_variant {ctx.report_variant!r} requires a timeline event "
        f"for the prior stage {prior_stage!r} to derive "
        "previous_milestone_event_id; none found on the timeline_events log. "
        "An emitter that has not seen the prior milestone must not file "
        "this report — DORA Art. 19(4) chains every report against the "
        "preceding milestone."
    )


def _validate_context(ctx: DoraArt19ReportContext) -> None:
    if ctx.report_variant not in REPORT_VARIANTS:
        raise DoraArt19EmitError(
            f"report_variant {ctx.report_variant!r} is not in the closed "
            f"alphabet {REPORT_VARIANTS!r}"
        )
    if not _UUID_RE.match(ctx.incident_id):
        raise DoraArt19EmitError(
            f"incident_id {ctx.incident_id!r} is not an RFC 4122 UUID as "
            "pinned by the schema"
        )

    refs = (
        ctx.regulation_refs
        if ctx.regulation_refs is not None
        else DEFAULT_REGULATION_REFS[ctx.report_variant]
    )
    if not refs:
        raise DoraArt19EmitError(
            "regulation_refs must carry at least one entry; a DORA Art. 19 "
            "report with no regulatory anchor is not evidence in the F-SV-03 "
            "sense"
        )
    seen_refs: set[str] = set()
    for ref in refs:
        if not _REGULATION_REF_RE.match(ref):
            raise DoraArt19EmitError(
                f"regulation_ref {ref!r} does not match the dora:<id> shape "
                "pinned by the schema"
            )
        if ref in seen_refs:
            raise DoraArt19EmitError(
                f"regulation_refs carries {ref!r} more than once; the schema "
                "marks the array uniqueItems"
            )
        seen_refs.add(ref)

    cls = ctx.classification
    if not isinstance(cls.major, bool):
        raise DoraArt19EmitError(
            "classification.major must be a bool; the operator is "
            "responsible for not filing an Art. 19 report at all when "
            "major == False"
        )
    seen_rule_ids: set[str] = set()
    for rid in cls.rule_ids:
        if not _RULE_ID_RE.match(rid):
            raise DoraArt19EmitError(
                f"classification.rule_ids entry {rid!r} does not match the "
                "policy rule-id shape pinned by the schema"
            )
        if rid in seen_rule_ids:
            raise DoraArt19EmitError(
                f"classification.rule_ids carries {rid!r} more than once"
            )
        seen_rule_ids.add(rid)
    for reason in cls.reasons:
        if not (1 <= len(reason) <= 400):
            raise DoraArt19EmitError(
                "classification.reasons entries must be 1..400 characters "
                "per the schema"
            )

    refs_t = ctx.timeline_refs
    if not (1 <= len(refs_t.timeline_handle) <= 200):
        raise DoraArt19EmitError(
            "timeline_refs.timeline_handle length must be 1..200 chars"
        )
    if refs_t.clock_started_at.tzinfo is None:
        raise DoraArt19EmitError(
            "timeline_refs.clock_started_at must be timezone-aware (UTC)"
        )
    if not _EVENT_ID_RE.match(refs_t.stage_event_id):
        raise DoraArt19EmitError(
            f"timeline_refs.stage_event_id {refs_t.stage_event_id!r} must "
            "be a 16-hex-digit digest per the schema"
        )

    imp = ctx.impact_indicators
    seen_fn: set[str] = set()
    for fn in imp.affected_functions:
        if not (1 <= len(fn) <= 200):
            raise DoraArt19EmitError(
                "impact_indicators.affected_functions entries must be "
                "1..200 chars"
            )
        if fn in seen_fn:
            raise DoraArt19EmitError(
                f"impact_indicators.affected_functions carries {fn!r} more "
                "than once; the schema marks the array uniqueItems"
            )
        seen_fn.add(fn)
    if imp.affected_clients_count is not None and imp.affected_clients_count < 0:
        raise DoraArt19EmitError(
            "impact_indicators.affected_clients_count must be non-negative"
        )
    if imp.duration_minutes is not None and imp.duration_minutes < 0:
        raise DoraArt19EmitError(
            "impact_indicators.duration_minutes must be non-negative"
        )
    seen_geo: set[str] = set()
    for geo in imp.geographic_scope:
        if not _ISO3166_RE.match(geo):
            raise DoraArt19EmitError(
                f"impact_indicators.geographic_scope entry {geo!r} must be "
                "an ISO-3166 alpha-2 code"
            )
        if geo in seen_geo:
            raise DoraArt19EmitError(
                f"impact_indicators.geographic_scope carries {geo!r} more "
                "than once; the schema marks the array uniqueItems"
            )
        seen_geo.add(geo)
    if (
        imp.data_loss_indicator is not None
        and imp.data_loss_indicator not in _DATA_LOSS_BANDS
    ):
        raise DoraArt19EmitError(
            f"impact_indicators.data_loss_indicator "
            f"{imp.data_loss_indicator!r} is not in the closed alphabet "
            f"{sorted(_DATA_LOSS_BANDS)}"
        )
    seen_ioc: set[str] = set()
    for ioc in imp.indicators_of_compromise:
        if not (1 <= len(ioc) <= 200):
            raise DoraArt19EmitError(
                "impact_indicators.indicators_of_compromise entries must be "
                "1..200 chars"
            )
        if ioc in seen_ioc:
            raise DoraArt19EmitError(
                f"impact_indicators.indicators_of_compromise carries "
                f"{ioc!r} more than once"
            )
        seen_ioc.add(ioc)

    mit = ctx.mitigation_status
    if mit.state not in _MITIGATION_STATES:
        raise DoraArt19EmitError(
            f"mitigation_status.state {mit.state!r} is not in the closed "
            f"alphabet {sorted(_MITIGATION_STATES)}"
        )
    for action in mit.actions_in_flight:
        if not (1 <= len(action) <= 2000):
            raise DoraArt19EmitError(
                "mitigation_status.actions_in_flight entries must be "
                "1..2000 chars"
            )
    for action in mit.completed_actions:
        if not (1 <= len(action) <= 2000):
            raise DoraArt19EmitError(
                "mitigation_status.completed_actions entries must be "
                "1..2000 chars"
            )
    if mit.root_cause is not None and not (1 <= len(mit.root_cause) <= 4000):
        raise DoraArt19EmitError(
            "mitigation_status.root_cause length must be 1..4000 chars"
        )
    if mit.residual_risk is not None and not (
        1 <= len(mit.residual_risk) <= 4000
    ):
        raise DoraArt19EmitError(
            "mitigation_status.residual_risk length must be 1..4000 chars"
        )

    # CORE layer: final_1mo must carry the closure free-text fields.
    if ctx.report_variant == "final_1mo":
        if mit.root_cause is None:
            raise DoraArt19EmitError(
                "report_variant 'final_1mo' requires mitigation_status."
                "root_cause; the F-WF-05 FinalReportSubmission carries "
                "this field as the DSPy-mediated closure narrative"
            )
        if not mit.completed_actions:
            raise DoraArt19EmitError(
                "report_variant 'final_1mo' requires mitigation_status."
                "completed_actions to be non-empty; Art. 19(4)(c) names "
                "the remediation actions completed by the milestone instant"
            )

    if ctx.submitted_at.tzinfo is None:
        raise DoraArt19EmitError(
            "submitted_at must be timezone-aware (UTC)"
        )

    if ctx.submission_ref is not None and not (
        1 <= len(ctx.submission_ref) <= 200
    ):
        raise DoraArt19EmitError(
            "submission_ref length must be 1..200 chars per the schema"
        )

    if ctx.commit_sha is not None and not _COMMIT_SHA_RE.match(ctx.commit_sha):
        raise DoraArt19EmitError(
            f"commit_sha {ctx.commit_sha!r} must be 7-64 lowercase hex "
            "characters per the schema"
        )


def _render_classification(cls: DoraClassification) -> dict[str, Any]:
    out: dict[str, Any] = {
        "major": cls.major,
        "reasons": list(cls.reasons),
        "rule_ids": list(cls.rule_ids),
    }
    if cls.cross_border is not None:
        out["cross_border"] = cls.cross_border
    if cls.recurring_incident is not None:
        out["recurring_incident"] = cls.recurring_incident
    return out


def _render_timeline_refs(
    refs: TimelineRefs, previous_milestone_event_id: str | None
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "timeline_handle": refs.timeline_handle,
        "clock_started_at": _iso8601_z(refs.clock_started_at),
        "stage_event_id": refs.stage_event_id,
    }
    if previous_milestone_event_id is not None:
        out["previous_milestone_event_id"] = previous_milestone_event_id
    return out


def _render_impact_indicators(imp: ImpactIndicators) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if imp.affected_functions:
        out["affected_functions"] = list(imp.affected_functions)
    if imp.affected_clients_count is not None:
        out["affected_clients_count"] = imp.affected_clients_count
    if imp.duration_minutes is not None:
        out["duration_minutes"] = imp.duration_minutes
    if imp.geographic_scope:
        out["geographic_scope"] = list(imp.geographic_scope)
    if imp.data_loss_indicator is not None:
        out["data_loss_indicator"] = imp.data_loss_indicator
    if imp.indicators_of_compromise:
        out["indicators_of_compromise"] = list(imp.indicators_of_compromise)
    return out


def _render_mitigation_status(mit: MitigationStatus) -> dict[str, Any]:
    out: dict[str, Any] = {"state": mit.state}
    if mit.actions_in_flight:
        out["actions_in_flight"] = list(mit.actions_in_flight)
    if mit.completed_actions:
        out["completed_actions"] = list(mit.completed_actions)
    if mit.root_cause is not None:
        out["root_cause"] = mit.root_cause
    if mit.residual_risk is not None:
        out["residual_risk"] = mit.residual_risk
    return out


def render_dora_art19_report(ctx: DoraArt19ReportContext) -> dict[str, Any]:
    """Pure context → record. Does not touch disk.

    Useful for tests, dry-runs, and any compile target that needs the
    record in-memory before persisting it through its own audit
    channel.
    """
    _validate_context(ctx)

    submitted_at_text = _iso8601_z(ctx.submitted_at)
    previous_milestone_event_id = _resolve_previous_milestone_event_id(ctx)

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "report_id": derive_report_id(
            ctx.incident_id, ctx.report_variant, ctx.submitted_at
        ),
        "report_variant": ctx.report_variant,
        "incident_id": ctx.incident_id,
        "regulation_refs": list(
            ctx.regulation_refs
            if ctx.regulation_refs is not None
            else DEFAULT_REGULATION_REFS[ctx.report_variant]
        ),
        "classification": _render_classification(ctx.classification),
        "timeline_refs": _render_timeline_refs(
            ctx.timeline_refs, previous_milestone_event_id
        ),
        "impact_indicators": _render_impact_indicators(ctx.impact_indicators),
        "mitigation_status": _render_mitigation_status(ctx.mitigation_status),
        "submitted_at": submitted_at_text,
        "provenance": {
            "source_url": ctx.source_url,
            "captured_at": submitted_at_text,
        },
    }
    if ctx.submission_ref is not None:
        record["submission_ref"] = ctx.submission_ref
    if ctx.commit_sha is not None:
        record["provenance"]["commit_sha"] = ctx.commit_sha

    return record


def emit_dora_art19_report(
    ctx: DoraArt19ReportContext,
    output_dir: str | os.PathLike[str],
) -> Path:
    """Render the record and persist it as ``<report_id>.json``.

    Returns the absolute path of the written file. The directory is
    created if it does not exist. Writes atomically through a sibling
    ``.tmp`` then ``os.replace`` so a partial write cannot be read by
    a concurrent consumer.

    Re-emissions for the same ``(incident_id, report_variant,
    submitted_at)`` derive the same ``report_id`` and overwrite the
    same path with byte-stable content. A re-emission of a milestone
    at a fresh ``submitted_at`` lands under a distinct ``report_id``
    — the chain reads re-submissions as evidentiary signal rather
    than dedup waste.
    """
    record = render_dora_art19_report(ctx)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{record['report_id']}.json"
    tmp_path = out_dir / f".{record['report_id']}.json.tmp"
    serialized = json.dumps(record, indent=2, sort_keys=True) + "\n"
    tmp_path.write_text(serialized, encoding="utf-8")
    os.replace(tmp_path, out_path)
    return out_path.resolve()


# Silence linters that flag the import kept for re-export.
_ = Mapping
