# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.ddos_response@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookDdosResponseV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.ddos_response@v1.

    Playbook id: playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __protected_service__
    # Identifier of the monitored service whose availability is in question (matches a row in the operator's documented service-inventory: which endpoint, which availability objective, which mitigation surface is pre-bound).
    protected_service: str
    # playbook_variable: __anomaly_window__
    # ISO 8601 interval describing the availability anomaly being evaluated. Supplied by the monitoring surface (synthetic-probe alert, edge / origin telemetry, operator-initiated trigger).
    anomaly_window: str
    # playbook_variable: __attack_vector__
    # Identifier of the classified attack vector for the anomaly: volumetric (e.g. UDP / ICMP / amplification flood), protocol (e.g. SYN flood, TCP state exhaustion), or application-layer (e.g. HTTP flood, slow-loris). Empty when classification could not be completed within the documented mitigation-engagement deadline; an empty value short-circuits into an evidence-capture failure record while still engaging the most-restrictive pre-bound mitigation.
    attack_vector: str
    # playbook_variable: __mitigation_action_id__
    # Identifier of the engaged mitigation action against the operator's pre-bound response surface (upstream-scrubbing provider activation reference, rate-limit / WAF posture-change ticket id, or failover-to-standby exercise reference). Always populated; the value names the discipline that was engaged even on the short-circuit branch.
    mitigation_action_id: str
    # playbook_variable: __service_restored__
    # Outcome of the validate-service-restoration step: true when the protected service is observed back inside the documented availability objective (latency, error rate, throughput) for the documented validation window; false when the service has not recovered and the incident remains active. A false value does not block the evidence-capture and notify branches; the record is published with the failure marker so the incident-management owner is paged with full context rather than discovering the gap later.
    service_restored: bool
    # playbook_variable: __evidence_id__
    # Identifier of the dated availability-incident evidence record published to the operator's evidence store. Always populated, including on the short-circuit branch (unclassified vector) and the unrestored-service branch.
    evidence_id: str
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
async def detect_availability_anomaly(protected_service: str, anomaly_window: str) -> None:
    """Resolve the trigger for this run: a synthetic-probe alert against __protected_service__ has tripped an availability threshold, edge / origin telemetry shows a sustained throughput / error-rate / latency deviation outside the documented availability objective, or an operator-initiated trigger landed. Reads __protected_service__ and __anomaly_window__ to confirm the anomaly is current and bounded; reads the operator's documented service-inventory row for the protected service to surface the pre-bound mitigation surface (upstream scrubber, rate-limit / WAF, standby failover) the downstream steps will engage against.

    CACAO step_id : action--60000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--60000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect availability anomaly', 'secops_ng.tool.name': 'detect_availability_anomaly', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--60000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect availability anomaly', 'secops_ng.tool.name': 'detect_availability_anomaly', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--60000000-0000-4000-8000-000000000002'"
        )

@tool
async def classify_attack_vector(protected_service: str, anomaly_window: str) -> str:
    """Classify the attack vector for the anomaly against the operator's documented vector taxonomy: volumetric (UDP / ICMP / amplification flood), protocol (SYN flood, TCP state exhaustion), or application-layer (HTTP flood, slow-loris). Reads the same monitoring surfaces the detect step consulted plus any operator-bound packet-capture / flow-record source documented for __protected_service__. Sets __attack_vector__. The classification is best-effort and time-boxed; if classification cannot be completed within the documented mitigation-engagement deadline (so the operator is not held by a perfect-classification stall while the service stays down), this step leaves __attack_vector__ empty and the downstream engage-mitigation step engages the most-restrictive pre-bound mitigation rather than waiting.

    CACAO step_id : action--60000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--60000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify attack vector', 'secops_ng.tool.name': 'classify_attack_vector', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--60000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify attack vector', 'secops_ng.tool.name': 'classify_attack_vector', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--60000000-0000-4000-8000-000000000003'"
        )

@tool
async def engage_mitigation(protected_service: str, attack_vector: str) -> str:
    """Engage the appropriate mitigation discipline against the operator's pre-bound response surface for __protected_service__: activate the upstream-scrubbing provider (volumetric); push the documented rate-limit / WAF posture change against the operator's edge surface (application-layer); or initiate the documented failover to the standby (protocol exhaustion or when scrubbing / rate-limit cannot recover the service inside the validation window). Reads __attack_vector__ to select the mitigation discipline; when __attack_vector__ is empty the step engages the most-restrictive pre-bound mitigation (typically failover) rather than waiting for classification. Emits __mitigation_action_id__ — the durable identifier of the engagement against the response surface (provider activation reference, ticket id, or failover-exercise reference). Detection bindings for mitigation-surface misconfiguration (scrubber not actually engaged, rate-limit pushed to wrong zone, standby reachable but not healthy) are owned by CORE-layer cards once upstream rule ids are selected.

    CACAO step_id : action--60000000-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--60000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'engage mitigation', 'secops_ng.tool.name': 'engage_mitigation', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--60000000-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'engage mitigation', 'secops_ng.tool.name': 'engage_mitigation', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--60000000-0000-4000-8000-000000000004'"
        )

@tool
async def validate_service_restoration(protected_service: str, mitigation_action_id: str) -> bool:
    """Observe the protected service against its documented availability objective (latency, error rate, throughput) for the documented validation window after the mitigation engagement. Reads __protected_service__ and __mitigation_action_id__; sets __service_restored__. A false outcome does not block downstream steps — the evidence-capture record is published with the failure marker and the notify step pages the incident-management owner with the full context so the next mitigation lever (escalate scrubbing tier, expand rate-limit scope, manual failover) can be engaged. Time-to-mitigation and availability-restoration metric emitters that read this step are owned by a sibling EXTEND card; this step intentionally does not pin a step-level metric_ref until that catalogue entry lands.

    CACAO step_id : action--60000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--60000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'validate service restoration', 'secops_ng.tool.name': 'validate_service_restoration', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--60000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'validate service restoration', 'secops_ng.tool.name': 'validate_service_restoration', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--60000000-0000-4000-8000-000000000005'"
        )

@tool
async def evidence_capture(protected_service: str, attack_vector: str, mitigation_action_id: str, service_restored: bool) -> str:
    """Compose and publish the dated availability-incident evidence record to the operator's evidence store. The record carries the protected service id, the anomaly window, the classified attack vector (or the empty-classification marker on the short-circuit branch), the engaged mitigation action id, the restoration outcome (or the failure marker), and the observed availability-objective measurements across the validation window. This is the audit-evident artifact NIS2 Art. 21(2)(b) reviewers read against an availability/DoS incident; missing or stale evidence is the failure mode the incident-handling metrics surface.

    CACAO step_id : action--60000000-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--60000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'evidence capture', 'secops_ng.tool.name': 'evidence_capture', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--60000000-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'evidence capture', 'secops_ng.tool.name': 'evidence_capture', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--60000000-0000-4000-8000-000000000006'"
        )

@tool
async def notify_incident_management_owner(evidence_id: str, protected_service: str, service_restored: bool) -> None:
    """Deliver the evidence reference to the incident-management owner along the operator's pre-bound channel (ticketing system, chat thread, page-out roster). Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently; an evidence record written but never delivered to the owner is itself an incident-handling gap. Notification carries the restoration outcome so a false __service_restored__ pages with appropriate urgency for the next mitigation lever.

    CACAO step_id : action--60000000-0000-4000-8000-000000000007
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--60000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify incident-management owner', 'secops_ng.tool.name': 'notify_incident_management_owner', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--60000000-0000-4000-8000-000000000007', attributes={'secops_ng.playbook.id': 'playbook--60a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6bb', 'secops_ng.step.id': 'action--60000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify incident-management owner', 'secops_ng.tool.name': 'notify_incident_management_owner', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--60000000-0000-4000-8000-000000000007'"
        )

async def llm_step(state: PlaybookDdosResponseV1State) -> dict:
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

STATE_SCHEMA = PlaybookDdosResponseV1State
TOOLS = (detect_availability_anomaly, classify_attack_vector, engage_mitigation, validate_service_restoration, evidence_capture, notify_incident_management_owner,)
AGENTIC_HOOK = llm_step

