"""DORA Art. 19(4) milestone submissions for dora_major_incident_reporting.

Backs the three notify-authority steps: the initial notification, the
intermediate report and the final report. Each composes one record
conforming to ``schemas/evidence/dora-art19-technical-incident-report.schema.json``
by calling the existing report builder
(``compilers/_shared/evidence/dora_art19_report.py``) — this module adds
no second implementation of the schema. What it adds is what the builder
leaves to its caller:

* **The JSON-native boundary.** Plain dicts and Zulu strings in and out,
  so the three compile targets marshal identically.
* **The chain.** The builder links each milestone to its predecessor
  through a timeline log and fails closed without one. Here the
  predecessor is the previous primitive's own output, so the intermediate
  report cannot be composed before the initial notification exists, nor
  the final before the intermediate. Stage event ids are derived
  deterministically from the incident and the milestone.
* **The deadline.** Each milestone carries ``due_at`` and
  ``within_deadline``:

  - initial: within 4 hours of classification as major, and no later than
    24 hours after awareness — whichever is earlier;
  - intermediate: within 72 hours of classification, as the step text
    anchors it. Where a reading anchors the 72 hours on the initial
    notification instead, that deadline is later, so this one is never
    missed under either;
  - final: no later than one calendar month after the intermediate report
    was submitted, with the end-of-month clamp.

* **The gate.** A non-major incident is not reported under Art. 19; every
  primitive here refuses a classification whose ``major`` is not ``True``.

Composition only: submission to the competent authority is the adapter's.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from compilers._shared.evidence.dora_art19_report import (
    DoraArt19EmitError,
    DoraArt19ReportContext,
    DoraClassification,
    ImpactIndicators,
    MitigationStatus,
    TimelineRefs,
    render_dora_art19_report,
)

from ._common import add_months, digest, hours, pointer, text, zulu

__all__ = [
    "InvalidReportingError",
    "compose_final_report",
    "compose_initial_notification",
    "compose_intermediate_report",
]

_IMPACT_KEYS = {"affected_functions", "affected_clients_count", "duration_minutes",
                "geographic_scope", "data_loss_indicator", "indicators_of_compromise"}
_MITIGATION_KEYS = {"state", "actions_in_flight", "completed_actions", "root_cause", "residual_risk"}
_STAGE = {"initial_4h": "early_warning", "intermediate_72h": "notification", "final_1mo": "final_report"}


class InvalidReportingError(ValueError):
    """Inputs are malformed, out of order, or the incident is not major."""


def _major(classification: object) -> dict:
    needed = {"classification_id", "incident_id", "classified_at", "major", "reasons", "rule_ids",
              "recurring_incident"}
    if not isinstance(classification, dict) or not needed <= set(classification):
        raise InvalidReportingError("classification must be the classify-step output")
    if classification["major"] is not True:
        raise InvalidReportingError(
            "only an incident classified as major is reported under DORA Art. 19; "
            f"classification.major is {classification['major']!r}"
        )
    return classification


def _stage_event_id(incident_id: str, variant: str) -> str:
    return digest(incident_id, variant)[:16]


def _impact(value: object) -> ImpactIndicators:
    if not isinstance(value, dict) or not set(value) <= _IMPACT_KEYS:
        raise InvalidReportingError(f"impact may carry only {sorted(_IMPACT_KEYS)}")
    v = dict(value)
    for k in ("affected_functions", "geographic_scope", "indicators_of_compromise"):
        v[k] = tuple(v.get(k) or ())
    return ImpactIndicators(**v)


def _mitigation(value: object) -> MitigationStatus:
    if not isinstance(value, dict) or "state" not in value or not set(value) <= _MITIGATION_KEYS:
        raise InvalidReportingError(f"mitigation must carry state, and only {sorted(_MITIGATION_KEYS)}")
    v = dict(value)
    for k in ("actions_in_flight", "completed_actions"):
        v[k] = tuple(v.get(k) or ())
    return MitigationStatus(**v)


def _previous(prev: object, expected_variant: str, incident_id: str) -> dict:
    report = prev.get("report") if isinstance(prev, dict) else None
    if not isinstance(report, dict) or report.get("report_variant") != expected_variant:
        raise InvalidReportingError(
            f"the previous milestone must be the {expected_variant} output of this chain"
        )
    if report.get("incident_id") != incident_id:
        raise InvalidReportingError("the previous milestone belongs to a different incident")
    return report


def _compose(variant: str, classification: dict, reporting_window: str, aware_at: str, submitted_at: str,
             impact: dict, mitigation: dict, source_url: str, submission_ref: str | None,
             previous: dict | None, due: datetime, basis: str) -> dict:
    window = pointer(reporting_window, "reporting_window", InvalidReportingError)
    aware = zulu(aware_at, "aware_at", InvalidReportingError)
    classified = zulu(classification["classified_at"], "classification.classified_at", InvalidReportingError)
    submitted = zulu(submitted_at, "submitted_at", InvalidReportingError)
    if classified < aware:
        raise InvalidReportingError("the incident was classified before the operator became aware of it")
    if submitted < classified:
        raise InvalidReportingError("a milestone cannot be submitted before the incident was classified")
    if not isinstance(source_url, str) or not source_url:
        raise InvalidReportingError("source_url must be a non-empty string")
    events = []
    if previous is not None:
        prev_submitted = zulu(previous["submitted_at"], "previous.submitted_at", InvalidReportingError)
        if submitted < prev_submitted:
            raise InvalidReportingError("a milestone cannot be submitted before the one it follows")
        events.append({"stage": _STAGE[previous["report_variant"]],
                       "event_id": previous["timeline_refs"]["stage_event_id"]})
    incident_id = classification["incident_id"]
    context = DoraArt19ReportContext(
        incident_id=incident_id,
        report_variant=variant,
        classification=DoraClassification(
            major=True, reasons=tuple(classification["reasons"]), rule_ids=tuple(classification["rule_ids"]),
            recurring_incident=classification["recurring_incident"]),
        timeline_refs=TimelineRefs(timeline_handle=window, clock_started_at=aware,
                                   stage_event_id=_stage_event_id(incident_id, variant)),
        impact_indicators=_impact(impact),
        mitigation_status=_mitigation(mitigation),
        submitted_at=submitted,
        source_url=source_url,
        timeline_events=tuple(events),
        submission_ref=None if submission_ref in (None, "") else submission_ref,
    )
    try:
        report = render_dora_art19_report(context)
    except (DoraArt19EmitError, TypeError) as exc:
        raise InvalidReportingError(str(exc)) from exc
    return {"report": report, "due_at": text(due), "within_deadline": submitted <= due, "deadline_basis": basis}


def compose_initial_notification(classification: dict, reporting_window: str, aware_at: str, submitted_at: str,
                                 impact: dict, mitigation: dict, source_url: str,
                                 submission_ref: str | None = None) -> dict:
    """Art. 19(4)(a) initial notification: due 4 h after classification, and at most 24 h after awareness."""
    c = _major(classification)
    classified = zulu(c["classified_at"], "classification.classified_at", InvalidReportingError)
    aware = zulu(aware_at, "aware_at", InvalidReportingError)
    due = min(classified + hours(4), aware + hours(24))
    return _compose("initial_4h", c, reporting_window, aware_at, submitted_at, impact, mitigation, source_url,
                    submission_ref, None, due, "4h after classification, at most 24h after awareness")


def compose_intermediate_report(classification: dict, initial: dict, reporting_window: str, aware_at: str,
                                submitted_at: str, impact: dict, mitigation: dict, source_url: str,
                                submission_ref: str | None = None) -> dict:
    """Art. 19(4)(b) intermediate report: due 72 h after classification."""
    c = _major(classification)
    prev = _previous(initial, "initial_4h", c["incident_id"])
    due = zulu(c["classified_at"], "classification.classified_at", InvalidReportingError) + hours(72)
    return _compose("intermediate_72h", c, reporting_window, aware_at, submitted_at, impact, mitigation,
                    source_url, submission_ref, prev, due, "72h after classification")


def compose_final_report(classification: dict, intermediate: dict, reporting_window: str, aware_at: str,
                         submitted_at: str, impact: dict, mitigation: dict, source_url: str,
                         submission_ref: str | None = None) -> dict:
    """Art. 19(4)(c) final report: due one calendar month after the intermediate report."""
    c = _major(classification)
    prev = _previous(intermediate, "intermediate_72h", c["incident_id"])
    due = add_months(zulu(prev["submitted_at"], "intermediate.submitted_at", InvalidReportingError), 1)
    return _compose("final_1mo", c, reporting_window, aware_at, submitted_at, impact, mitigation, source_url,
                    submission_ref, prev, due, "one calendar month after the intermediate report")
