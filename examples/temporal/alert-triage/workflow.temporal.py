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
async def ingest_typed_alert_payload(alert_id: str, alert_source_shape: str) -> None:
    """SKELETON. Normalise the inbound alert into the SecOps-NG alert envelope. Two source shapes are required by the roadmap acceptance criteria (push from detection pipeline, pull from a shared alert store); the dispatcher branches on __alert_source_shape__. Body of the normalization rules lands in the CORE-INGEST card.

    CACAO step_id: action--a1e47431-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--a1e47431-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest typed alert payload', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_typed_alert_payload'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--a1e47431-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest typed alert payload', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_typed_alert_payload'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--a1e47431-0000-4000-8000-000000000002'"
        )

INGEST_TYPED_ALERT_PAYLOAD_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def enrich_with_telemetry_context() -> bool:
    """SKELETON. Pull adjacent telemetry for the entities named in the alert (subject identity, source/destination, asset) so the prioritisation policy and suppression check have evidence beyond the alert envelope itself. Stubbed; the enrichment fan-out lands in CORE-ENRICH.

    CACAO step_id: action--a1e47431-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--a1e47431-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000003', 'secops_ng.step.name': 'enrich with telemetry context', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enrich_with_telemetry_context'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--a1e47431-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000003', 'secops_ng.step.name': 'enrich with telemetry context', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enrich_with_telemetry_context'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--a1e47431-0000-4000-8000-000000000003'"
        )

ENRICH_WITH_TELEMETRY_CONTEXT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def suppress_and_close() -> None:
    """SKELETON. Link this alert onto the existing case (or onto the benign-rule record), close it without paging, and account the suppression against the false-positive-rate KPI and (when the suppression covers a re-fire of a previously closed case) the recurring-incident correlator.

    CACAO step_id: action--a1e47431-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--a1e47431-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000005', 'secops_ng.step.name': 'suppress and close', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'suppress_and_close'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--a1e47431-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000005', 'secops_ng.step.name': 'suppress and close', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'suppress_and_close'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--a1e47431-0000-4000-8000-000000000005'"
        )

SUPPRESS_AND_CLOSE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def classify_and_prioritise_deterministic_policy() -> str:
    """SKELETON. Apply the operator's prioritisation policy. The policy itself is expressed as code (the roadmap pins this: deterministic prioritisation, DSPy used only for free-text fields like the analyst summary). Output is __priority__ ∈ {p1_severe, p2_high, p3_routine, p4_informational}.

    CACAO step_id: action--a1e47431-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--a1e47431-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000006', 'secops_ng.step.name': 'classify and prioritise (deterministic policy)', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_and_prioritise_deterministic_policy'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--a1e47431-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000006', 'secops_ng.step.name': 'classify and prioritise (deterministic policy)', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_and_prioritise_deterministic_policy'})
        )
        from alert_triage.primitives.prioritisation import prioritise
        __priority_verdict__ = prioritise(context=__asset_context__, correlates_open_case=__correlates_open_case__, detection_class=__detection_class__, detection_severity=__detection_severity__)

CLASSIFY_AND_PRIORITISE_DETERMINISTIC_POLICY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def response_p1_severe_page_and_escalate() -> None:
    """SKELETON. Page the on-call responder, open the incident case, stamp the timeline-start signal, and hand off to the incident management playbook. Records against the MTTR-critical clock and the regulator-notification-overrun KRI window.

    CACAO step_id: action--a1e47431-0000-4000-8000-000000000008
    """
    with _TRACER.start_as_current_span(
        name='activity.action--a1e47431-0000-4000-8000-000000000008',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000008', 'secops_ng.step.name': 'response: p1 severe — page and escalate', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'response_p1_severe_page_and_escalate'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--a1e47431-0000-4000-8000-000000000008', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000008', 'secops_ng.step.name': 'response: p1 severe — page and escalate', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'response_p1_severe_page_and_escalate'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--a1e47431-0000-4000-8000-000000000008'"
        )

RESPONSE_P1_SEVERE_PAGE_AND_ESCALATE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def response_p2_high_queue_for_primary_analyst() -> None:
    """SKELETON. Queue the case to the primary analyst queue with the enriched evidence packet, no page. Records against the MTTR clock and the handoff-brief delivery SLA.

    CACAO step_id: action--a1e47431-0000-4000-8000-000000000009
    """
    with _TRACER.start_as_current_span(
        name='activity.action--a1e47431-0000-4000-8000-000000000009',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000009', 'secops_ng.step.name': 'response: p2 high — queue for primary analyst', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'response_p2_high_queue_for_primary_analyst'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--a1e47431-0000-4000-8000-000000000009', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000009', 'secops_ng.step.name': 'response: p2 high — queue for primary analyst', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'response_p2_high_queue_for_primary_analyst'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--a1e47431-0000-4000-8000-000000000009'"
        )

RESPONSE_P2_HIGH_QUEUE_FOR_PRIMARY_ANALYST_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def response_p3_routine_queue_for_review() -> None:
    """SKELETON. Append to the review queue for batched analyst attention; no SLA clock beyond the routine review-completion SLA.

    CACAO step_id: action--a1e47431-0000-4000-8000-00000000000a
    """
    with _TRACER.start_as_current_span(
        name='activity.action--a1e47431-0000-4000-8000-00000000000a',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-00000000000a', 'secops_ng.step.name': 'response: p3 routine — queue for review', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'response_p3_routine_queue_for_review'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--a1e47431-0000-4000-8000-00000000000a', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-00000000000a', 'secops_ng.step.name': 'response: p3 routine — queue for review', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'response_p3_routine_queue_for_review'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--a1e47431-0000-4000-8000-00000000000a'"
        )

RESPONSE_P3_ROUTINE_QUEUE_FOR_REVIEW_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def response_p4_informational_log_and_close() -> None:
    """SKELETON. Record the alert for telemetry-coverage accounting and close without further action. Feeds the false-positive-rate denominator and the detection-coverage view.

    CACAO step_id: action--a1e47431-0000-4000-8000-00000000000b
    """
    with _TRACER.start_as_current_span(
        name='activity.action--a1e47431-0000-4000-8000-00000000000b',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'response: p4 informational — log and close', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'response_p4_informational_log_and_close'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--a1e47431-0000-4000-8000-00000000000b', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'response: p4 informational — log and close', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'response_p4_informational_log_and_close'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--a1e47431-0000-4000-8000-00000000000b'"
        )

RESPONSE_P4_INFORMATIONAL_LOG_AND_CLOSE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookAlertTriageV1Workflow:
    """SOC alert-triage source playbook. Ingests typed alert payloads from at least two source shapes (push from detection pipeline, pull from a shared alert store), enriches with telemetry context, suppresses already-seen or known-benign hits inside a configurable window, applies a deterministic prioritisation policy (free-text fields may be routed through a DSPy module, the priority decision itself stays in code), and routes the case onto a response branch keyed on the disposition. SKELETON: action bodies are stubs; the workflow graph, join keys, and metric/control references are the contract this source artifact commits to.

    CACAO playbook id : playbook--a1e47431-0000-4000-8000-000000000000
    stable_id         : playbook.alert_triage@v1
    content_version   : 0.1.0
    maturity          : draft
    workflow_start    : start--a1e47431-0000-4000-8000-000000000001
    activities        : ingest_typed_alert_payload, enrich_with_telemetry_context, suppress_and_close, classify_and_prioritise_deterministic_policy, response_p1_severe_page_and_escalate, response_p2_high_queue_for_primary_analyst, response_p3_routine_queue_for_review, response_p4_informational_log_and_close
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.alert_triage@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.alert_triage@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.alert_triage@v1'"
            )

WORKFLOW = PlaybookAlertTriageV1Workflow
ACTIVITIES = (ingest_typed_alert_payload, enrich_with_telemetry_context, suppress_and_close, classify_and_prioritise_deterministic_policy, response_p1_severe_page_and_escalate, response_p2_high_queue_for_primary_analyst, response_p3_routine_queue_for_review, response_p4_informational_log_and_close,)
RETRY_POLICIES = (INGEST_TYPED_ALERT_PAYLOAD_RETRY_POLICY, ENRICH_WITH_TELEMETRY_CONTEXT_RETRY_POLICY, SUPPRESS_AND_CLOSE_RETRY_POLICY, CLASSIFY_AND_PRIORITISE_DETERMINISTIC_POLICY_RETRY_POLICY, RESPONSE_P1_SEVERE_PAGE_AND_ESCALATE_RETRY_POLICY, RESPONSE_P2_HIGH_QUEUE_FOR_PRIMARY_ANALYST_RETRY_POLICY, RESPONSE_P3_ROUTINE_QUEUE_FOR_REVIEW_RETRY_POLICY, RESPONSE_P4_INFORMATIONAL_LOG_AND_CLOSE_RETRY_POLICY,)
