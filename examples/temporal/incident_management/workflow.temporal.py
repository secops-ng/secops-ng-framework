# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.temporal <playbook.cacao.json>`.
#
# This file is a stub. Workflow control flow and activity bodies are
# intentionally NotImplementedError until a human integrator wires them
# to the operator's runtime.
"""Generated Temporal stub. See module-level metadata in the workflow docstring."""
from __future__ import annotations

from datetime import timedelta

from temporalio import activity, workflow
from temporalio.common import RetryPolicy

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

@activity.defn
async def intake_significant_incident_signal(signal_id: str) -> str:
    """Receive the originating incident signal and hydrate it with the typed intake-event payload shape consumed by the F-PT-02 incident-timeline pattern. Produces __incident_id__. CORE body lands in CORE-PRIM (card 5); SKELETON stub raises NotImplementedError against the named contract.

    CACAO step_id: action--50000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--50000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'intake significant-incident signal', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'intake_significant_incident_signal'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--50000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'intake significant-incident signal', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'intake_significant_incident_signal'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--50000000-0000-4000-8000-000000000002'"
        )

INTAKE_SIGNIFICANT_INCIDENT_SIGNAL_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def classify_significance_and_cross_border_scope(incident_id: str) -> dict[str, object]:
    """Apply the deterministic significance + cross-border classification policy per NIS2 Article 23(3) and 23(6). No DSPy reach — regulated decisions are deterministic code. Produces __significant__ and __cross_border__.

    CACAO step_id: action--50000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--50000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify significance and cross-border scope', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_significance_and_cross_border_scope'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--50000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify significance and cross-border scope', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_significance_and_cross_border_scope'})
        )
        from content.playbooks.incident_management.primitives.classification import classify_significance
        __classification_verdict__ = classify_significance(signals=__intake_signals__)

CLASSIFY_SIGNIFICANCE_AND_CROSS_BORDER_SCOPE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def open_incident_timeline(incident_id: str, significant: bool, cross_border: bool) -> str:
    """Signal the F-PT-02 incident-timeline pattern's start: stage clock 0 begins, the timeline-state machine moves into the early-warning window. Produces __timeline_handle__ — the opaque pattern handle every subsequent submission threads through.

    CACAO step_id: action--50000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--50000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'open incident timeline', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'open_incident_timeline'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--50000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'open incident timeline', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'open_incident_timeline'})
        )
        from content.playbooks.incident_management.primitives.timeline_binding import open_timeline
        __timeline_handle__ = open_timeline(incident_id=__incident_id__, opened_at=__timeline_opened_at__)

OPEN_INCIDENT_TIMELINE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def submit_24_hour_early_warning(incident_id: str, timeline_handle: str, significant: bool, cross_border: bool, notification_destinations: dict[str, object]) -> str:
    """Submit the NIS2 Article 23(4)(a) early warning through the operator-configured regulator destination for the 'early_warning' stage. Emits a timeline event consumed by the F-PT-02 pattern. Bounded by the stage-clock primitive that the CORE-PRIM card will land — overrun trips the regulator-notification-overrun KRI.

    CACAO step_id: action--50000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--50000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'submit 24-hour early warning', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'submit_24_hour_early_warning'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--50000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'submit 24-hour early warning', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'submit_24_hour_early_warning'})
        )
        from content.playbooks.incident_management.primitives.regulator_submission import resolve_destination
        __early_warning_destination__ = resolve_destination(destinations=__notification_destinations__, stage='early_warning')

SUBMIT_24_HOUR_EARLY_WARNING_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def submit_72_hour_notification(incident_id: str, timeline_handle: str, significant: bool, cross_border: bool, notification_destinations: dict[str, object]) -> str:
    """Submit the NIS2 Article 23(4)(b) incident notification through the operator-configured regulator destination for the 'notification' stage. Emits a timeline event consumed by the F-PT-02 pattern. Bounded by the stage-clock primitive — overrun trips the regulator-notification-overrun KRI.

    CACAO step_id: action--50000000-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--50000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'submit 72-hour notification', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'submit_72_hour_notification'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--50000000-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'submit 72-hour notification', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'submit_72_hour_notification'})
        )
        from content.playbooks.incident_management.primitives.stage_clock import verdict_for_submission
        __notification_stage_verdict__ = verdict_for_submission(stage='notification', opened_at=__timeline_opened_at__, submitted_at=__notification_submitted_at__)

SUBMIT_72_HOUR_NOTIFICATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def submit_1_month_final_report(incident_id: str, timeline_handle: str, significant: bool, cross_border: bool, notification_destinations: dict[str, object]) -> str:
    """Submit the NIS2 Article 23(4)(c) final report through the operator-configured regulator destination for the 'final_report' stage. The free-text fields on this submission — incident narrative, root-cause description, applied-mitigations summary — are the single DSPy-signature reach for this workflow; every other field is deterministic. Bounded by the stage-clock primitive — overrun trips the regulator-notification-overrun KRI.

    CACAO step_id: action--50000000-0000-4000-8000-000000000009
    """
    with _TRACER.start_as_current_span(
        name='activity.action--50000000-0000-4000-8000-000000000009',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000009', 'secops_ng.step.name': 'submit 1-month final report', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'submit_1_month_final_report'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--50000000-0000-4000-8000-000000000009', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000009', 'secops_ng.step.name': 'submit 1-month final report', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'submit_1_month_final_report'})
        )
        from content.playbooks.incident_management.primitives.regulator_submission import resolve_destination
        __final_report_destination__ = resolve_destination(destinations=__notification_destinations__, stage='final_report')

SUBMIT_1_MONTH_FINAL_REPORT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def close_incident_timeline(incident_id: str, timeline_handle: str) -> str:
    """Signal the F-PT-02 incident-timeline pattern's close: the canonical regulator-shaped timeline JSON is persisted at content/evidence/incidents/<__incident_id__>/timeline.json for downstream consumption by F-CP-02. Stamps the timeline-completeness KPI.

    CACAO step_id: action--50000000-0000-4000-8000-00000000000a
    """
    with _TRACER.start_as_current_span(
        name='activity.action--50000000-0000-4000-8000-00000000000a',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-00000000000a', 'secops_ng.step.name': 'close incident timeline', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'close_incident_timeline'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--50000000-0000-4000-8000-00000000000a', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-00000000000a', 'secops_ng.step.name': 'close incident timeline', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'close_incident_timeline'})
        )
        from content.playbooks.incident_management.primitives.timeline_binding import close_timeline
        __timeline_artefact_path__ = close_timeline(session=__timeline_handle__, closed_at=__timeline_closed_at__)

CLOSE_INCIDENT_TIMELINE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookIncidentManagementV1Workflow:
    """Manage a significant security incident through the NIS2 Article 23 three-stage regulator timeline: intake the originating signal, classify significance and cross-border scope, open a deterministic incident timeline, submit the 24-hour early warning, submit the 72-hour notification, submit the one-month final report (free-text fields scoped to narrative, root cause, and applied mitigations only), and close the timeline so the regulator-shaped JSON artefact is persisted. CACAO v2 + SecOps-NG content-model extensions. Forward-public artifact: regulator destinations are operator-supplied through playbook variables (sovereign-stack constraint — the framework ships no default endpoint) and the timeline binding consumes the F-PT-02 incident-timeline pattern.

    CACAO playbook id : playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0
    stable_id         : playbook.incident_management@v1
    content_version   : 0.2.0
    maturity          : experimental
    workflow_start    : start--50000000-0000-4000-8000-000000000001
    activities        : intake_significant_incident_signal, classify_significance_and_cross_border_scope, open_incident_timeline, submit_24_hour_early_warning, submit_72_hour_notification, submit_1_month_final_report, close_incident_timeline
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.incident_management@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.playbook.version': '0.2.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.incident_management@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.playbook.version': '0.2.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.incident_management@v1'"
            )

WORKFLOW = PlaybookIncidentManagementV1Workflow
ACTIVITIES = (intake_significant_incident_signal, classify_significance_and_cross_border_scope, open_incident_timeline, submit_24_hour_early_warning, submit_72_hour_notification, submit_1_month_final_report, close_incident_timeline,)
RETRY_POLICIES = (INTAKE_SIGNIFICANT_INCIDENT_SIGNAL_RETRY_POLICY, CLASSIFY_SIGNIFICANCE_AND_CROSS_BORDER_SCOPE_RETRY_POLICY, OPEN_INCIDENT_TIMELINE_RETRY_POLICY, SUBMIT_24_HOUR_EARLY_WARNING_RETRY_POLICY, SUBMIT_72_HOUR_NOTIFICATION_RETRY_POLICY, SUBMIT_1_MONTH_FINAL_REPORT_RETRY_POLICY, CLOSE_INCIDENT_TIMELINE_RETRY_POLICY,)
