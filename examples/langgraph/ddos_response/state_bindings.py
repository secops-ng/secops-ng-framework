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
    # Identifier of the classified attack vector for the anomaly: volumetric (e.g. UDP / ICMP / amplification flood), protocol (e.g. SYN flood, TCP state exhaustion), or application-layer (e.g. HTTP flood, slow-loris). Empty when classification could not be completed within the documented mitigation-engagement deadline; an empty value short-circuits into an evidence-capture failure record while still engaging the most-restrictive pre-bound mitigation. Extracted at the compile target's adapter seam from __classification__.attack_vector.
    attack_vector: str
    # playbook_variable: __mitigation_action_id__
    # Identifier of the engaged mitigation action against the operator's pre-bound response surface (upstream-scrubbing provider activation reference, rate-limit / WAF posture-change ticket id, or failover-to-standby exercise reference). Always populated; the value names the discipline that was engaged even on the short-circuit branch. Extracted at the compile target's adapter seam from __engagement__.mitigation_action_id.
    mitigation_action_id: str
    # playbook_variable: __service_restored__
    # Outcome of the validate-service-restoration step: true when the protected service is observed back inside the documented availability objective (latency, error rate, throughput) for the documented validation window; false when the service has not recovered and the incident remains active. A false value does not block the evidence-capture and notify branches; the record is published with the failure marker so the incident-management owner is paged with full context rather than discovering the gap later. Extracted at the compile target's adapter seam from __restoration_verdict__.service_restored.
    service_restored: bool
    # playbook_variable: __evidence_id__
    # Identifier of the dated availability-incident evidence record published to the operator's evidence store. Always populated, including on the short-circuit branch (unclassified vector) and the unrestored-service branch. Extracted at the compile target's adapter seam from __evidence_record__.evidence_id.
    evidence_id: str
    # playbook_variable: __service_inventory__
    # The operator's documented service inventory handed over by the adapter: services — rows carrying service, availability_objective (latency_ms_p99, error_rate_max, throughput_min_rps) and mitigation_surfaces (upstream_scrubber, rate_limit_waf, standby_failover — all three required, so the full ladder is documented before an incident). Consumed by detect.resolve_availability_trigger.
    service_inventory: dict[str, object]
    # playbook_variable: __trigger_envelope__
    # Trigger envelope composed by detect.resolve_availability_trigger: protected_service, anomaly_window (start, end), availability_objective, mitigation_surfaces. The engage binding reads .mitigation_surfaces and the validate binding reads .availability_objective.
    trigger_envelope: dict[str, object]
    # playbook_variable: __vector_signals__
    # The monitoring adapter's per-vector verdicts for classify.classify_attack_vector: volumetric, protocol, application_layer — real booleans, all three keys required so an absent surface is an explicit false, never an omission. The packet-capture / flow-record reading that produced them is the adapter's.
    vector_signals: dict[str, object]
    # playbook_variable: __deadline_exceeded__
    # Whether the documented mitigation-engagement deadline expired before classification completed. The adapter enforces the clock; classify.classify_attack_vector decides what the flag means (a signal that arrived still classifies; no signal plus the flag records deadline_exceeded).
    deadline_exceeded: bool
    # playbook_variable: __classification__
    # Classification envelope composed by classify.classify_attack_vector: attack_vector (empty on the short-circuit branch), classification_state (classified | deadline_exceeded | no_signal), signals. The adapter extracts __attack_vector__; the engage and evidence bindings read .attack_vector.
    classification: dict[str, object]
    # playbook_variable: __engagement__
    # Engagement order composed by mitigation.select_mitigation_engagement: mitigation_action_id (ddos-mit-<discipline>-…), discipline, surface_ref, short_circuit, engagement_order. Executed by the response-surface adapter; the adapter extracts __mitigation_action_id__ and the evidence binding reads .mitigation_action_id.
    engagement: dict[str, object]
    # playbook_variable: __validation_observations__
    # JSON-native list of the monitoring adapter's samples across the documented validation window for restoration.evaluate_service_restoration: at (Zulu instant), latency_ms_p99, error_rate, throughput_rps. Restoration is verified against these observations, never asserted on the mitigation having been applied.
    validation_observations: str
    # playbook_variable: __restoration_verdict__
    # Restoration verdict composed by restoration.evaluate_service_restoration: service_restored, samples_evaluated, breaches (per-dimension records with observed value and bound). The adapter extracts __service_restored__; the evidence binding consumes the whole verdict and the notify binding reads .service_restored.
    restoration_verdict: dict[str, object]
    # playbook_variable: __evidence_record__
    # Availability-incident evidence record composed by evidence.compose_incident_evidence_record: evidence_id (ddos-evd-…), record_date, protected_service, anomaly_window, attack_vector, mitigation_action_id, service_restored, markers, restoration. Published by the evidence-store adapter; the adapter extracts __evidence_id__ and the notify binding reads .evidence_id.
    evidence_record: dict[str, object]
    # playbook_variable: __owner_channel__
    # Role-shaped reference to the incident-management owner's pre-bound delivery channel (ticketing system, chat thread, page-out roster). Consumed by notify.compose_owner_notification; delivery along it is the messaging surface's.
    owner_channel: str
    # playbook_variable: __owner_notification__
    # Owner notification composed by notify.compose_owner_notification: channel_ref, urgency (page | inform), evidence_id, service_restored, headline, body. Delivered by the messaging surface.
    owner_notification: dict[str, object]
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
async def detect_availability_anomaly(protected_service: str, anomaly_window: str, service_inventory: dict[str, object]) -> dict[str, object]:
    """Resolve the trigger for this run: detect.resolve_availability_trigger confirms __anomaly_window__ is a bounded ISO-8601 interval, resolves __protected_service__ to its row in the operator's documented __service_inventory__ (an undocumented service or a duplicated row fails loud), and surfaces the availability objective (latency, error rate, throughput) together with the full pre-bound mitigation ladder — upstream scrubber, rate-limit / WAF and standby failover are all required at detect time, so a missing surface is discovered before an incident rather than mid-engagement with the service down. The synthetic-probe alert, edge / origin telemetry deviation or operator-initiated trigger that raised the anomaly is the monitoring adapter's ingress. The binding assigns the trigger envelope to __trigger_envelope__; the engage and validate bindings read its mitigation_surfaces and availability_objective.

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
        from content.playbooks.ddos_response.primitives.detect import resolve_availability_trigger
        __trigger_envelope__ = resolve_availability_trigger(protected_service=__protected_service__, anomaly_window=__anomaly_window__, service_inventory=__service_inventory__)

@tool
async def classify_attack_vector(vector_signals: dict[str, object], deadline_exceeded: bool) -> dict[str, object]:
    """Classify the attack vector against the operator's documented taxonomy — volumetric (UDP / ICMP / amplification flood), protocol (SYN flood, TCP state exhaustion) or application-layer (HTTP flood, slow-loris): classify.classify_attack_vector consumes the monitoring adapter's per-vector verdicts in __vector_signals__ (real booleans, all three keys required) and the adapter-enforced __deadline_exceeded__ time-box flag. Multi-signal precedence is volumetric > protocol > application_layer (the pipe-filler first); an aggregate 'under attack' verdict is never produced. A signal that arrived is a completed classification even at the deadline; when no signal arrived the vector is empty and classification_state records deadline_exceeded or no_signal, so the engage step engages the most-restrictive pre-bound mitigation rather than holding the operator to a perfect-classification stall while the service stays down. The binding assigns the envelope to __classification__; the compile target's adapter extracts __attack_vector__ (empty on the short-circuit branch).

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
        from content.playbooks.ddos_response.primitives.classify import classify_attack_vector
        __classification__ = classify_attack_vector(signals=__vector_signals__, deadline_exceeded=__deadline_exceeded__)

@tool
async def engage_mitigation(classification: dict[str, object], protected_service: str, anomaly_window: str, trigger_envelope: dict[str, object]) -> dict[str, object]:
    """Engage the mitigation discipline against the operator's pre-bound response surface: mitigation.select_mitigation_engagement maps the vector to the discipline — volumetric ⇒ upstream scrubbing, application-layer ⇒ rate-limit / WAF posture, protocol ⇒ failover to standby — reading the surfaces resolved at detect time from __trigger_envelope__.mitigation_surfaces; an empty vector (the classify short-circuit) engages the most-restrictive pre-bound mitigation, failover, with short_circuit recorded rather than waiting for classification. The composed engagement order carries a deterministic, discipline-naming action id (ddos-mit-<discipline>-… over service, window and surface) so the value names the discipline even on the short-circuit branch and a replayed engagement resolves to the same id. Activating the scrubbing provider, pushing the posture change or exercising the failover is the compile target's adapter — the framework ships the hand-off and no scrubbing-provider binding. The binding assigns the order to __engagement__; the adapter extracts __mitigation_action_id__.

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
        from content.playbooks.ddos_response.primitives.mitigation import select_mitigation_engagement
        __engagement__ = select_mitigation_engagement(attack_vector=__classification__.attack_vector, protected_service=__protected_service__, anomaly_window=__anomaly_window__, mitigation_surfaces=__trigger_envelope__.mitigation_surfaces)

@tool
async def validate_service_restoration(trigger_envelope: dict[str, object], validation_observations: str) -> dict[str, object]:
    """Verify restoration against observed traffic, never against the mitigation having been applied: restoration.evaluate_service_restoration takes the monitoring adapter's samples across the documented validation window in __validation_observations__ and judges each against the availability objective resolved at detect time (__trigger_envelope__.availability_objective) — latency, error rate and throughput, with boundary equality inside the objective. The verdict is true only when every sample sits inside the objective; a false verdict is data, not a failure — every breach is enumerated by dimension with observed value and bound, the evidence record publishes with the failure marker, and the notify step pages the owner for the next mitigation lever (escalate scrubbing tier, expand rate-limit scope, manual failover). Malformed samples fail loud. The binding assigns the verdict to __restoration_verdict__; the adapter extracts __service_restored__.

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
        from content.playbooks.ddos_response.primitives.restoration import evaluate_service_restoration
        __restoration_verdict__ = evaluate_service_restoration(availability_objective=__trigger_envelope__.availability_objective, observations=__validation_observations__)

@tool
async def evidence_capture(protected_service: str, anomaly_window: str, classification: dict[str, object], engagement: dict[str, object], restoration_verdict: dict[str, object]) -> dict[str, object]:
    """Compose the dated availability-incident evidence record the NIS2 Art. 21(2)(b) reviewer reads: evidence.compose_incident_evidence_record pins __protected_service__, __anomaly_window__, the classified vector (empty on the short-circuit branch, carrying the unclassified_vector marker), the engaged __engagement__.mitigation_action_id, the restoration verdict (service_not_restored marker on the unrestored branch) and the observed measurements — dated from the anomaly window's start instant, never from emitter run time, with a content-derived record identity so re-publication is idempotent. Missing or stale evidence is the failure mode the incident-handling metrics surface; publishing to the evidence store is the compile target's adapter. The binding assigns the record to __evidence_record__; the adapter extracts __evidence_id__.

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
        from content.playbooks.ddos_response.primitives.evidence import compose_incident_evidence_record
        __evidence_record__ = compose_incident_evidence_record(protected_service=__protected_service__, anomaly_window=__anomaly_window__, attack_vector=__classification__.attack_vector, mitigation_action_id=__engagement__.mitigation_action_id, restoration=__restoration_verdict__)

@tool
async def notify_incident_management_owner(evidence_record: dict[str, object], protected_service: str, restoration_verdict: dict[str, object], owner_channel: str) -> dict[str, object]:
    """Compose the owner notification: notify.compose_owner_notification carries __evidence_record__.evidence_id and the restoration outcome to the incident-management owner's pre-bound __owner_channel__ (ticketing system, chat thread, page-out roster) — a false service_restored pages with the next-lever prompt, a true one informs; a coerced string flag is refused. Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently; an evidence record written but never delivered to the owner is itself an incident-handling gap. Delivery along the channel is the messaging surface's; the binding assigns the payload to __owner_notification__.

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
        from content.playbooks.ddos_response.primitives.notify import compose_owner_notification
        __owner_notification__ = compose_owner_notification(evidence_id=__evidence_record__.evidence_id, protected_service=__protected_service__, service_restored=__restoration_verdict__.service_restored, owner_channel=__owner_channel__)

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

