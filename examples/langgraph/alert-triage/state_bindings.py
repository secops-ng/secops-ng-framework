# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.alert_triage@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookAlertTriageV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.alert_triage@v1.

    Playbook id: playbook--a1e47431-0000-4000-8000-000000000000

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __alert_id__
    # Identifier of the inbound alert in the operator's alert store. Carried opaquely; the source shape is asserted in __alert_source_shape__.
    alert_id: str
    # playbook_variable: __alert_source_shape__
    # One of: push_detection_pipeline, pull_alert_store. Used to select the normalization path in the ingest step.
    alert_source_shape: str
    # playbook_variable: __benign_or_seen__
    # Set by the suppression check: true when the alert matches a known- benign rule or an already-seen case fingerprint inside the configured suppression window.
    benign_or_seen: bool
    # playbook_variable: __priority__
    # Deterministic priority assigned by the prioritisation policy. One of: p1_severe, p2_high, p3_routine, p4_informational.
    priority: str
    # bookkeeping
    # Per-step status map keyed by CACAO step_id. Conventional values: 'pending', 'running', 'ok', 'failed', 'awaiting-human'. The graph builder writes here; conditional-edge routers read it.
    step_status: dict[str, str]
    # bookkeeping
    # Accumulated error messages from failed steps. Use a reducer that appends (e.g. operator.add) when wiring into StateGraph.
    errors: list[str]
    # bookkeeping
    # LangGraph/LangChain message channel for the agentic-extension surface. An LLM-driven node reads/writes here; non-LLM playbooks leave it empty.
    messages: Annotated[list[AnyMessage], add_messages]

@tool
async def ingest_typed_alert_payload(alert_id: str, alert_source_shape: str) -> None:
    """SKELETON. Normalise the inbound alert into the SecOps-NG alert envelope. Two source shapes are required by the roadmap acceptance criteria (push from detection pipeline, pull from a shared alert store); the dispatcher branches on __alert_source_shape__. Body of the normalization rules lands in the CORE-INGEST card.

    CACAO step_id : action--a1e47431-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--a1e47431-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest typed alert payload', 'secops_ng.tool.name': 'ingest_typed_alert_payload', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--a1e47431-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest typed alert payload', 'secops_ng.tool.name': 'ingest_typed_alert_payload', 'secops_ng.workflow.run_id': ''})
        )
        from alert_triage.primitives.payloads import validate_alert_payload
        __alert_payload__ = validate_alert_payload(raw=__raw_payload__, source_shape=__alert_source_shape__)

@tool
async def enrich_with_telemetry_context() -> bool:
    """SKELETON. Pull adjacent telemetry for the entities named in the alert (subject identity, source/destination, asset) so the prioritisation policy and suppression check have evidence beyond the alert envelope itself. Stubbed; the enrichment fan-out lands in CORE-ENRICH.

    CACAO step_id : action--a1e47431-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--a1e47431-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000003', 'secops_ng.step.name': 'enrich with telemetry context', 'secops_ng.tool.name': 'enrich_with_telemetry_context', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--a1e47431-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000003', 'secops_ng.step.name': 'enrich with telemetry context', 'secops_ng.tool.name': 'enrich_with_telemetry_context', 'secops_ng.workflow.run_id': ''})
        )
        from alert_triage.primitives.suppression import canonical_seen_key
        __seen_key__ = canonical_seen_key(asset_ref=__asset_ref__, classification=__classification__, detection_rule_id=__detection_rule_id__, subject_ref=__subject_ref__)

@tool
async def suppress_and_close() -> None:
    """SKELETON. Link this alert onto the existing case (or onto the benign-rule record), close it without paging, and account the suppression against the false-positive-rate KPI and (when the suppression covers a re-fire of a previously closed case) the recurring-incident correlator.

    CACAO step_id : action--a1e47431-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--a1e47431-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000005', 'secops_ng.step.name': 'suppress and close', 'secops_ng.tool.name': 'suppress_and_close', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--a1e47431-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000005', 'secops_ng.step.name': 'suppress and close', 'secops_ng.tool.name': 'suppress_and_close', 'secops_ng.workflow.run_id': ''})
        )
        from alert_triage.primitives.suppression import canonical_seen_key
        __close_record_key__ = canonical_seen_key(asset_ref=__asset_ref__, classification=__classification__, detection_rule_id=__detection_rule_id__, subject_ref=__subject_ref__)

@tool
async def classify_and_prioritise_deterministic_policy() -> str:
    """SKELETON. Apply the operator's prioritisation policy. The policy itself is expressed as code (the roadmap pins this: deterministic prioritisation, DSPy used only for free-text fields like the analyst summary). Output is __priority__ ∈ {p1_severe, p2_high, p3_routine, p4_informational}.

    CACAO step_id : action--a1e47431-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--a1e47431-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000006', 'secops_ng.step.name': 'classify and prioritise (deterministic policy)', 'secops_ng.tool.name': 'classify_and_prioritise_deterministic_policy', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--a1e47431-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000006', 'secops_ng.step.name': 'classify and prioritise (deterministic policy)', 'secops_ng.tool.name': 'classify_and_prioritise_deterministic_policy', 'secops_ng.workflow.run_id': ''})
        )
        from alert_triage.primitives.prioritisation import prioritise
        __priority_verdict__ = prioritise(context=__asset_context__, correlates_open_case=__correlates_open_case__, detection_class=__detection_class__, detection_severity=__detection_severity__)

@tool
async def response_p1_severe_page_and_escalate() -> None:
    """SKELETON. Page the on-call responder, open the incident case, stamp the timeline-start signal, and hand off to the incident management playbook. Records against the MTTR-critical clock and the regulator-notification-overrun KRI window.

    CACAO step_id : action--a1e47431-0000-4000-8000-000000000008
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--a1e47431-0000-4000-8000-000000000008',
        attributes={'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000008', 'secops_ng.step.name': 'response: p1 severe — page and escalate', 'secops_ng.tool.name': 'response_p1_severe_page_and_escalate', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--a1e47431-0000-4000-8000-000000000008', attributes={'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000008', 'secops_ng.step.name': 'response: p1 severe — page and escalate', 'secops_ng.tool.name': 'response_p1_severe_page_and_escalate', 'secops_ng.workflow.run_id': ''})
        )
        from alert_triage.primitives.response import escalation_route
        __escalation_directive__ = escalation_route(asset_criticality=__asset_context__.asset_criticality, internet_exposed=__asset_context__.internet_exposed, priority=__priority__, regulated_data=__asset_context__.regulated_data)

@tool
async def response_p2_high_queue_for_primary_analyst() -> None:
    """SKELETON. Queue the case to the primary analyst queue with the enriched evidence packet, no page. Records against the MTTR clock and the handoff-brief delivery SLA.

    CACAO step_id : action--a1e47431-0000-4000-8000-000000000009
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--a1e47431-0000-4000-8000-000000000009',
        attributes={'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000009', 'secops_ng.step.name': 'response: p2 high — queue for primary analyst', 'secops_ng.tool.name': 'response_p2_high_queue_for_primary_analyst', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--a1e47431-0000-4000-8000-000000000009', attributes={'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-000000000009', 'secops_ng.step.name': 'response: p2 high — queue for primary analyst', 'secops_ng.tool.name': 'response_p2_high_queue_for_primary_analyst', 'secops_ng.workflow.run_id': ''})
        )
        from alert_triage.primitives.response import notify_on_call
        __notification_directive__ = notify_on_call(asset_criticality=__asset_context__.asset_criticality, internet_exposed=__asset_context__.internet_exposed, priority=__priority__, regulated_data=__asset_context__.regulated_data)

@tool
async def response_p3_routine_queue_for_review() -> None:
    """SKELETON. Append to the review queue for batched analyst attention; no SLA clock beyond the routine review-completion SLA.

    CACAO step_id : action--a1e47431-0000-4000-8000-00000000000a
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--a1e47431-0000-4000-8000-00000000000a',
        attributes={'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-00000000000a', 'secops_ng.step.name': 'response: p3 routine — queue for review', 'secops_ng.tool.name': 'response_p3_routine_queue_for_review', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--a1e47431-0000-4000-8000-00000000000a', attributes={'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-00000000000a', 'secops_ng.step.name': 'response: p3 routine — queue for review', 'secops_ng.tool.name': 'response_p3_routine_queue_for_review', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--a1e47431-0000-4000-8000-00000000000a'"
        )

@tool
async def response_p4_informational_log_and_close() -> None:
    """SKELETON. Record the alert for telemetry-coverage accounting and close without further action. Feeds the false-positive-rate denominator and the detection-coverage view.

    CACAO step_id : action--a1e47431-0000-4000-8000-00000000000b
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--a1e47431-0000-4000-8000-00000000000b',
        attributes={'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'response: p4 informational — log and close', 'secops_ng.tool.name': 'response_p4_informational_log_and_close', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--a1e47431-0000-4000-8000-00000000000b', attributes={'secops_ng.playbook.id': 'playbook--a1e47431-0000-4000-8000-000000000000', 'secops_ng.step.id': 'action--a1e47431-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'response: p4 informational — log and close', 'secops_ng.tool.name': 'response_p4_informational_log_and_close', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--a1e47431-0000-4000-8000-00000000000b'"
        )

async def llm_step(state: PlaybookAlertTriageV1State) -> dict:
    """Agentic-extension hook.

    Insert this function (or a variant) as a LangGraph node when a
    CACAO action step should be driven by an LLM with tool-calling
    rather than by a hand-written activity.

    Contract:
      - Read from ``state`` — every CACAO playbook variable is on
        the typed state under its slugified key (see the state
        TypedDict above).
      - Call your LLM, optionally with the tools emitted in this
        module bound via ``llm.bind_tools([...])`` or routed
        through a ``ToolNode``.
      - Return a dict of state updates; LangGraph merges it into
        the typed state via the reducers the integrator chose.
      - Append assistant / tool messages to ``state['messages']``
        (the channel uses ``add_messages``, so returning a list
        under that key concatenates rather than replaces).

    Provider-neutrality: this stub intentionally does not import a
    specific LLM SDK. Pick one at integration time.
    """
    raise NotImplementedError(
        "LLM step not implemented: integrator must wire an LLM here."
    )

STATE_SCHEMA = PlaybookAlertTriageV1State
TOOLS = (ingest_typed_alert_payload, enrich_with_telemetry_context, suppress_and_close, classify_and_prioritise_deterministic_policy, response_p1_severe_page_and_escalate, response_p2_high_queue_for_primary_analyst, response_p3_routine_queue_for_review, response_p4_informational_log_and_close,)
AGENTIC_HOOK = llm_step

