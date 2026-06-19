"""Regenerate the committed DORA Article 19 report-variant worked example (Temporal).

F-SV-03 CORE — the F-WF-05 incident_management workflow emits one
DORA Article 19 report-variant record per regulator-submission
milestone on the chain. This script materialises all four variants
for one representative incident by driving the Temporal activity
adapter at
``compilers.temporal.evidence.emit_dora_art19_report_activity``
exactly as a Temporal worker would: a typed
:class:`DoraArt19ReportContext` is passed in, the activity delegates
to the shared helper, and one artifact per variant is written to disk
under ``examples/temporal/dora_art19_report/evidence/``.

The example pins one representative incident under DORA Art. 19:

* ``initial_4h``    — 4h initial notification (Art. 19(4)(a)).
* ``intermediate_72h`` — 72h intermediate report (Art. 19(4)(b)).
* ``final_1mo``     — one-month final report (Art. 19(4)(c)).
* ``voluntary_cyber_threat`` — Art. 19(2) voluntary notification on a
  separate (precursor) cyber threat.

Inputs are kept byte-identical to the n8n and LangGraph siblings at
``examples/{n8n,langgraph}/dora_art19_report/`` so the per-target
adapters write byte-identical records per variant — every emission
runs through one shared helper, which is the F-SV-03 CORE invariant.

Run from the repo root after any change to the report-variant shared
emitter or the Temporal adapter::

    PYTHONPATH=. python examples/temporal/dora_art19_report/regenerate.py

The committed ``<variant>.report.json`` files are the resulting
artifacts renamed for human-friendly diffing; the deterministic
``<report_id>.json`` written by the activity is the SHA-256-named
sibling of the same bytes (the script removes the sha-named twin).

Public-bar artifact: no individual personal names, no operator
branding, no internal infrastructure references on any free-text
field. The illustrative narrative belongs to the community / NGO
voice — a worked example a reviewer can re-derive in their own fork.
"""
from __future__ import annotations

import asyncio
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from compilers._shared.evidence import (
    DoraArt19ReportContext,
    DoraClassification,
    ImpactIndicators,
    MitigationStatus,
    TimelineRefs,
)
from compilers.temporal.evidence import emit_dora_art19_report_activity

HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = HERE / "evidence"

# Canonical incident pinned for the worked example. Re-used byte-for-
# byte across the three target siblings so the cross-target byte-parity
# guarantee holds at the artifact-bytes level.
INCIDENT_ID = "11111111-2222-4333-8444-555555555555"
TIMELINE_HANDLE = "incident-timeline/abcd1234ef567890"
OPENED_AT = datetime(2026, 6, 9, 5, 0, 0, tzinfo=timezone.utc)
EARLY_WARNING_EVENT_ID = "0123456789abcdef"
NOTIFICATION_EVENT_ID = "fedcba9876543210"
FINAL_REPORT_EVENT_ID = "abcdef0123456789"
THREAT_AWARENESS_AT = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
THREAT_EVENT_ID = "1122334455667788"

# Submission instants per variant. The 4h / 72h / 1mo offsets are the
# "submitted promptly" exemplar — well inside each Art. 19(4) window.
INITIAL_4H_SUBMITTED_AT = datetime(2026, 6, 9, 8, 30, 0, tzinfo=timezone.utc)
INTERMEDIATE_72H_SUBMITTED_AT = datetime(
    2026, 6, 11, 12, 0, 0, tzinfo=timezone.utc
)
FINAL_1MO_SUBMITTED_AT = datetime(2026, 7, 9, 9, 0, 0, tzinfo=timezone.utc)
VOLUNTARY_THREAT_SUBMITTED_AT = datetime(
    2026, 6, 2, 14, 0, 0, tzinfo=timezone.utc
)

# Timeline-event log carried on every emission so the cross-milestone
# `previous_milestone_event_id` resolver can pin against a real prior
# stage. Mirrors the F-WF-05 TimelineSession.events shape the timeline
# binding accumulates.
CHAIN_TIMELINE_EVENTS: tuple[dict, ...] = (
    {"stage": "timeline_open", "event_id": "deadbeefcafef00d"},
    {"stage": "early_warning", "event_id": EARLY_WARNING_EVENT_ID},
    {"stage": "notification", "event_id": NOTIFICATION_EVENT_ID},
    {"stage": "final_report", "event_id": FINAL_REPORT_EVENT_ID},
)

SOURCE_URL = "https://example.org/runs/dora_art19_report_example_0001"

# Per-variant contexts. Every field on every variant is operator-
# supplied / deterministic — the F-WF-05 DSPy reach is scoped to the
# free-text root_cause / residual_risk on the final_1mo record.
CONTEXTS: dict[str, DoraArt19ReportContext] = {
    "initial_4h": DoraArt19ReportContext(
        incident_id=INCIDENT_ID,
        report_variant="initial_4h",
        classification=DoraClassification(
            major=True,
            reasons=(
                "significance_rule=major_disruption_two_member_states: "
                "severe service disruption across two or more Member States",
                "cross_border_rule=multi_member_state: incident materially "
                "affected users in two or more Member States",
            ),
            rule_ids=(
                "dora.sig.severe_disruption",
                "dora.cb.multi_member_state",
            ),
            cross_border=True,
            recurring_incident=False,
        ),
        timeline_refs=TimelineRefs(
            timeline_handle=TIMELINE_HANDLE,
            clock_started_at=OPENED_AT,
            stage_event_id=EARLY_WARNING_EVENT_ID,
        ),
        impact_indicators=ImpactIndicators(
            data_loss_indicator="unknown",
            geographic_scope=("NL", "DE"),
        ),
        mitigation_status=MitigationStatus(
            state="in_flight",
            actions_in_flight=(
                "Isolated the affected segment from the public network "
                "and initiated containment per the operator's runbook.",
            ),
        ),
        submitted_at=INITIAL_4H_SUBMITTED_AT,
        source_url=SOURCE_URL,
        timeline_events=CHAIN_TIMELINE_EVENTS,
    ),
    "intermediate_72h": DoraArt19ReportContext(
        incident_id=INCIDENT_ID,
        report_variant="intermediate_72h",
        classification=DoraClassification(
            major=True,
            reasons=(
                "significance_rule=major_disruption_two_member_states: "
                "severe service disruption across two or more Member States",
                "cross_border_rule=multi_member_state: incident materially "
                "affected users in two or more Member States",
            ),
            rule_ids=(
                "dora.sig.severe_disruption",
                "dora.cb.multi_member_state",
            ),
            cross_border=True,
            recurring_incident=False,
        ),
        timeline_refs=TimelineRefs(
            timeline_handle=TIMELINE_HANDLE,
            clock_started_at=OPENED_AT,
            stage_event_id=NOTIFICATION_EVENT_ID,
        ),
        impact_indicators=ImpactIndicators(
            affected_clients_count=1200,
            duration_minutes=None,
            geographic_scope=("NL", "DE", "FR"),
            data_loss_indicator="availability",
            indicators_of_compromise=(
                "ioc:hash:abc123",
                "ioc:domain:example.invalid",
            ),
        ),
        mitigation_status=MitigationStatus(
            state="partially_mitigated",
            actions_in_flight=(
                "Rotated credentials across the affected scope; "
                "monitoring detection coverage for residual exposure.",
            ),
        ),
        submitted_at=INTERMEDIATE_72H_SUBMITTED_AT,
        source_url=SOURCE_URL,
        timeline_events=CHAIN_TIMELINE_EVENTS,
    ),
    "final_1mo": DoraArt19ReportContext(
        incident_id=INCIDENT_ID,
        report_variant="final_1mo",
        classification=DoraClassification(
            major=True,
            reasons=(
                "significance_rule=major_disruption_two_member_states: "
                "severe service disruption across two or more Member States",
                "cross_border_rule=multi_member_state: incident materially "
                "affected users in two or more Member States",
            ),
            rule_ids=(
                "dora.sig.severe_disruption",
                "dora.cb.multi_member_state",
            ),
            cross_border=True,
            recurring_incident=False,
        ),
        timeline_refs=TimelineRefs(
            timeline_handle=TIMELINE_HANDLE,
            clock_started_at=OPENED_AT,
            stage_event_id=FINAL_REPORT_EVENT_ID,
        ),
        impact_indicators=ImpactIndicators(
            affected_functions=("payments_settlement", "client_onboarding"),
            affected_clients_count=1200,
            duration_minutes=360,
            geographic_scope=("NL", "DE", "FR"),
            data_loss_indicator="availability",
            indicators_of_compromise=(
                "ioc:hash:abc123",
                "ioc:domain:example.invalid",
            ),
        ),
        mitigation_status=MitigationStatus(
            state="remediated",
            completed_actions=(
                "Isolated the affected segment and restored the impacted "
                "function from a clean replica.",
                "Rotated every credential in the affected scope and "
                "validated detections against a regression test set.",
            ),
            root_cause=(
                "An upstream provider's certificate-rotation procedure "
                "failed to update the downstream trust store within the "
                "documented window; the resulting trust failure cascaded "
                "into the dependent settlement function."
            ),
            residual_risk=(
                "Trust-store update propagation remains a "
                "single-failure-mode dependency on the upstream provider; "
                "remediation tracked under the next quarterly review."
            ),
        ),
        submitted_at=FINAL_1MO_SUBMITTED_AT,
        source_url=SOURCE_URL,
        timeline_events=CHAIN_TIMELINE_EVENTS,
        submission_ref="csirt-ticket-2026-073",
    ),
    "voluntary_cyber_threat": DoraArt19ReportContext(
        incident_id="22222222-3333-4444-8555-666666666666",
        report_variant="voluntary_cyber_threat",
        classification=DoraClassification(
            major=False,
            reasons=(
                "voluntary cyber-threat notification: precursor activity "
                "observed against a peer financial entity in the same "
                "operating region.",
            ),
            rule_ids=("dora.threat.voluntary_precursor",),
        ),
        timeline_refs=TimelineRefs(
            timeline_handle="threat-timeline/feedface12345678",
            clock_started_at=THREAT_AWARENESS_AT,
            stage_event_id=THREAT_EVENT_ID,
        ),
        impact_indicators=ImpactIndicators(
            indicators_of_compromise=(
                "ioc:domain:phish-bait.invalid",
                "ioc:url:https://phish-bait.invalid/login",
            ),
        ),
        mitigation_status=MitigationStatus(
            state="in_flight",
            actions_in_flight=(
                "Distributed indicators of compromise to peer financial "
                "entities through the regional sharing channel.",
            ),
        ),
        submitted_at=VOLUNTARY_THREAT_SUBMITTED_AT,
        source_url=SOURCE_URL,
    ),
}


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    for variant, ctx in CONTEXTS.items():
        written_str = asyncio.run(
            emit_dora_art19_report_activity(ctx, EVIDENCE_DIR)
        )
        written = Path(written_str)
        snapshot = EVIDENCE_DIR / f"{variant}.report.json"
        shutil.copyfile(written, snapshot)
        written.unlink()
        record = json.loads(snapshot.read_text("utf-8"))
        assert record["schema_version"] == "1.0.0"
        assert record["report_variant"] == variant
        print(
            f"wrote {snapshot} (report_id={record['report_id']})"
        )


if __name__ == "__main__":
    main()
