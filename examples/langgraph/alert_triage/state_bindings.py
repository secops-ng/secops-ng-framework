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
    # playbook_variable: __alert_payload__
    # The validated, normalised alert envelope (AlertPayload) written by validate_alert_payload. Every step after ingest reads from this, never from __raw_payload__.
    alert_payload: dict[str, object]
    # playbook_variable: __alert_source_shape__
    # One of: push_detection_pipeline, pull_alert_store. Used to select the normalization path in the ingest step.
    alert_source_shape: str
    # playbook_variable: __asset_context__
    # Business context for the affected asset as read from the operator's inventory at enrichment: asset_criticality, regulated_data, internet_exposed (the AssetContext model in primitives/prioritisation.py). The response-step bindings read its fields dotted (__asset_context__.asset_criticality).
    asset_context: dict[str, object]
    # playbook_variable: __asset_ref__
    # Reference into the operator's asset inventory for the affected asset. Fingerprint component.
    asset_ref: str
    # playbook_variable: __benign_or_seen__
    # Set by the suppression check: true when the alert matches a known- benign rule or an already-seen case fingerprint inside the configured suppression window.
    benign_or_seen: bool
    # playbook_variable: __classification__
    # Detection classification carried on the validated payload (rule taxonomy label, e.g. credential_access). Fingerprint component; suppression must not collapse different classifications that share a rule id.
    classification: str
    # playbook_variable: __close_record_key__
    # The same canonical fingerprint recomputed at suppress-and-close and stamped on the closure record, so a later alert with this fingerprint is attributable to this closure.
    close_record_key: str
    # playbook_variable: __closure_record__
    # Closure record (ClosureRecord) for the p4 branch: the logged informational close, keyed for later suppression attribution.
    closure_record: dict[str, object]
    # playbook_variable: __correlates_open_case__
    # True when enrichment found an open case sharing the suppression fingerprint, which lifts the prioritisation floor. Defaults to false in the policy when unset.
    correlates_open_case: bool
    # playbook_variable: __detection_class__
    # Detection class consumed by the prioritisation policy. Values are the DetectionClass policy enum in primitives/prioritisation.py; the policy, not this declaration, is the authority on the set.
    detection_class: str
    # playbook_variable: __detection_rule_id__
    # Identifier of the detection rule that produced the alert, as carried on the validated payload. One of the four components of the canonical suppression fingerprint.
    detection_rule_id: str
    # playbook_variable: __detection_severity__
    # Upstream detector severity consumed by the prioritisation policy (DetectionSeverity enum in primitives/prioritisation.py). Deliberately distinct from __priority__ — the policy output — so a detector cannot pre-assign its own triage priority.
    detection_severity: str
    # playbook_variable: __escalation_directive__
    # Escalation directive (EscalationDirective) for the p1 branch: who to page, with what context.
    escalation_directive: dict[str, object]
    # playbook_variable: __notification_directive__
    # Notification directive (NotificationDirective) for the p2 branch: primary-analyst queue entry plus on-call notice.
    notification_directive: dict[str, object]
    # playbook_variable: __priority__
    # Deterministic priority assigned by the prioritisation policy. One of: p1_severe, p2_high, p3_routine, p4_informational.
    priority: str
    # playbook_variable: __priority_verdict__
    # Full prioritisation verdict (PriorityVerdict): the priority plus the policy factors that produced it. __priority__ carries the bare priority for branch conditions; this carries the evidence.
    priority_verdict: dict[str, object]
    # playbook_variable: __raw_payload__
    # The inbound alert exactly as received — the push body from the detection pipeline or the pulled alert-store record — before any shape validation. Input to validate_alert_payload, which branches on __alert_source_shape__.
    raw_payload: dict[str, object]
    # playbook_variable: __review_queue_directive__
    # Review-queue directive (ReviewQueueDirective) for the p3 branch.
    review_queue_directive: dict[str, object]
    # playbook_variable: __seen_key__
    # Canonical suppression fingerprint computed at enrichment, checked against the suppression window to set __benign_or_seen__.
    seen_key: str
    # playbook_variable: __subject_ref__
    # Reference to the subject the detection fired on (principal, mailbox, service account). Fingerprint component; distinct from __asset_ref__ so a rule firing for one user across many hosts and one host across many users produce different keys.
    subject_ref: str
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
    """Normalise the inbound alert into the SecOps-NG alert envelope. Two source shapes are required by the roadmap acceptance criteria (push from detection pipeline, pull from a shared alert store); the dispatcher branches on __alert_source_shape__.

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
        from content.playbooks.alert_triage.primitives.payloads import validate_alert_payload
        __alert_payload__ = validate_alert_payload(raw=__raw_payload__, source_shape=__alert_source_shape__)

@tool
async def enrich_with_telemetry_context() -> bool:
    """Pull adjacent telemetry for the entities named in the alert (subject identity, source/destination, asset) so the prioritisation policy and suppression check have evidence beyond the alert envelope itself. The bound body derives the canonical seen-key for the suppression window; wider telemetry fan-out is an operator extension point.

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
        from content.playbooks.alert_triage.primitives.suppression import canonical_seen_key
        __seen_key__ = canonical_seen_key(asset_ref=__asset_ref__, classification=__classification__, detection_rule_id=__detection_rule_id__, subject_ref=__subject_ref__)

@tool
async def suppress_and_close() -> None:
    """Link this alert onto the existing case (or onto the benign-rule record), close it without paging, and account the suppression against the false-positive-rate KPI and (when the suppression covers a re-fire of a previously closed case) the recurring-incident correlator.

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
        from content.playbooks.alert_triage.primitives.suppression import canonical_seen_key
        __close_record_key__ = canonical_seen_key(asset_ref=__asset_ref__, classification=__classification__, detection_rule_id=__detection_rule_id__, subject_ref=__subject_ref__)

@tool
async def classify_and_prioritise_deterministic_policy() -> str:
    """Apply the operator's prioritisation policy. The policy itself is expressed as code (the roadmap pins this: deterministic prioritisation, DSPy used only for free-text fields like the analyst summary). Output is __priority__ ∈ {p1_severe, p2_high, p3_routine, p4_informational}.

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
        from content.playbooks.alert_triage.primitives.prioritisation import prioritise
        __priority_verdict__ = prioritise(context=__asset_context__, correlates_open_case=__correlates_open_case__, detection_class=__detection_class__, detection_severity=__detection_severity__)

@tool
async def response_p1_severe_page_and_escalate() -> None:
    """Page the on-call responder, open the incident case, stamp the timeline-start signal, and hand off to the incident management playbook. Records against the MTTR-critical clock and the regulator-notification-overrun KRI window.

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
        from content.playbooks.alert_triage.primitives.response import escalation_route
        __escalation_directive__ = escalation_route(asset_criticality=__asset_context__.asset_criticality, internet_exposed=__asset_context__.internet_exposed, priority=__priority__, regulated_data=__asset_context__.regulated_data)

@tool
async def response_p2_high_queue_for_primary_analyst() -> None:
    """Queue the case to the primary analyst queue with the enriched evidence packet, no page. Records against the MTTR clock and the handoff-brief delivery SLA.

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
        from content.playbooks.alert_triage.primitives.response import notify_on_call
        __notification_directive__ = notify_on_call(asset_criticality=__asset_context__.asset_criticality, internet_exposed=__asset_context__.internet_exposed, priority=__priority__, regulated_data=__asset_context__.regulated_data)

@tool
async def response_p3_routine_queue_for_review() -> None:
    """Append to the review queue for batched analyst attention; no SLA clock beyond the routine review-completion SLA.

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
        from content.playbooks.alert_triage.primitives.response import route_to_review_queue
        __review_queue_directive__ = route_to_review_queue(asset_criticality=__asset_context__.asset_criticality, internet_exposed=__asset_context__.internet_exposed, priority=__priority__, regulated_data=__asset_context__.regulated_data)

@tool
async def response_p4_informational_log_and_close() -> None:
    """Record the alert for telemetry-coverage accounting and close without further action. Feeds the false-positive-rate denominator and the detection-coverage view. A crown-jewel asset or regulated data upgrades the close to keep a retention pointer for the recurring-incident correlator — still no page and no queue entry.

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
        from content.playbooks.alert_triage.primitives.response import log_and_close
        __closure_record__ = log_and_close(asset_criticality=__asset_context__.asset_criticality, internet_exposed=__asset_context__.internet_exposed, priority=__priority__, regulated_data=__asset_context__.regulated_data)

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

