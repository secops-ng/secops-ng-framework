# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.incident_management@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookIncidentManagementV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.incident_management@v1.

    Playbook id: playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __signal_id__
    # Identifier of the originating incident signal handed in by the upstream triage workflow (alert-triage close-out, ransomware-containment close-out, or an operator-raised ticket).
    signal_id: str
    # playbook_variable: __notification_destinations__
    # Operator-supplied dictionary of regulator-notification destinations. Keys are the three regulator-submission stages ('early_warning', 'notification', 'final_report'); values are opaque destination handles resolved at the compile target's config layer (n8n credential, Temporal worker env, LangGraph runtime config). The framework ships no default endpoint per the sovereign-stack constraint; absent or empty entries fail the corresponding submit action by contract.
    notification_destinations: dict[str, object]
    # playbook_variable: __incident_id__
    # Workflow-assigned incident identifier. Joined into the timeline JSON artefact path at `content/evidence/incidents/<incident-id>/timeline.json` (consumed downstream by F-CP-02).
    incident_id: str
    # playbook_variable: __significant__
    # Whether the intake event meets the NIS2 Article 23(3) significance threshold. Deterministic classification — produced by the classify-significance action.
    significant: bool
    # playbook_variable: __cross_border__
    # Whether the incident has cross-border impact under NIS2 Article 23(6). Deterministic classification — produced by the classify-significance action.
    cross_border: bool
    # playbook_variable: __timeline_handle__
    # Opaque handle returned by the F-PT-02 incident-timeline pattern's open-timeline call. Consumed by every subsequent timeline-event submission and by the close-timeline action.
    timeline_handle: str
    # playbook_variable: __early_warning_event_id__
    # Timeline-event identifier returned by the 24-hour early-warning submission. Persisted into the timeline JSON.
    early_warning_event_id: str
    # playbook_variable: __notification_event_id__
    # Timeline-event identifier returned by the 72-hour notification submission. Persisted into the timeline JSON.
    notification_event_id: str
    # playbook_variable: __final_report_ready__
    # Whether the root-cause analysis and applied-mitigations narrative for the final report are complete before the one-month boundary. Determines whether the workflow submits the final report or closes out with a deferred-final-report marker on the timeline (the deferred case is closed under the same timeline; the late final-report submission ships through a separate operator-driven re-entry that is out of scope for this card).
    final_report_ready: bool
    # playbook_variable: __final_report_event_id__
    # Timeline-event identifier returned by the one-month final-report submission. Persisted into the timeline JSON.
    final_report_event_id: str
    # playbook_variable: __timeline_artefact_path__
    # Repository-relative path where the canonical timeline JSON artefact was persisted by the close-timeline action.
    timeline_artefact_path: str
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
async def intake_significant_incident_signal(signal_id: str) -> str:
    """Receive the originating incident signal and hydrate it with the typed intake-event payload shape consumed by the F-PT-02 incident-timeline pattern. Produces __incident_id__. CORE body lands in CORE-PRIM (card 5); SKELETON stub raises NotImplementedError against the named contract.

    CACAO step_id : action--50000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--50000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'intake significant-incident signal', 'secops_ng.tool.name': 'intake_significant_incident_signal', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--50000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'intake significant-incident signal', 'secops_ng.tool.name': 'intake_significant_incident_signal', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--50000000-0000-4000-8000-000000000002'"
        )

@tool
async def classify_significance_and_cross_border_scope(incident_id: str) -> dict[str, object]:
    """Apply the deterministic significance + cross-border classification policy per NIS2 Article 23(3) and 23(6). No DSPy reach — regulated decisions are deterministic code. Produces __significant__ and __cross_border__.

    CACAO step_id : action--50000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--50000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify significance and cross-border scope', 'secops_ng.tool.name': 'classify_significance_and_cross_border_scope', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--50000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify significance and cross-border scope', 'secops_ng.tool.name': 'classify_significance_and_cross_border_scope', 'secops_ng.workflow.run_id': ''})
        )
        from incident_management.primitives.classification import classify_significance
        __classification_verdict__ = classify_significance(signals=__intake_signals__)

@tool
async def open_incident_timeline(incident_id: str, significant: bool, cross_border: bool) -> str:
    """Signal the F-PT-02 incident-timeline pattern's start: stage clock 0 begins, the timeline-state machine moves into the early-warning window. Produces __timeline_handle__ — the opaque pattern handle every subsequent submission threads through.

    CACAO step_id : action--50000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--50000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'open incident timeline', 'secops_ng.tool.name': 'open_incident_timeline', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--50000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'open incident timeline', 'secops_ng.tool.name': 'open_incident_timeline', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--50000000-0000-4000-8000-000000000005'"
        )

@tool
async def submit_24_hour_early_warning(incident_id: str, timeline_handle: str, significant: bool, cross_border: bool, notification_destinations: dict[str, object]) -> str:
    """Submit the NIS2 Article 23(4)(a) early warning through the operator-configured regulator destination for the 'early_warning' stage. Emits a timeline event consumed by the F-PT-02 pattern. Bounded by the stage-clock primitive that the CORE-PRIM card will land — overrun trips the regulator-notification-overrun KRI.

    CACAO step_id : action--50000000-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--50000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'submit 24-hour early warning', 'secops_ng.tool.name': 'submit_24_hour_early_warning', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--50000000-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'submit 24-hour early warning', 'secops_ng.tool.name': 'submit_24_hour_early_warning', 'secops_ng.workflow.run_id': ''})
        )
        from incident_management.primitives.regulator_submission import resolve_destination
        __early_warning_destination__ = resolve_destination(destinations=__notification_destinations__, stage='early_warning')

@tool
async def submit_72_hour_notification(incident_id: str, timeline_handle: str, significant: bool, cross_border: bool, notification_destinations: dict[str, object]) -> str:
    """Submit the NIS2 Article 23(4)(b) incident notification through the operator-configured regulator destination for the 'notification' stage. Emits a timeline event consumed by the F-PT-02 pattern. Bounded by the stage-clock primitive — overrun trips the regulator-notification-overrun KRI.

    CACAO step_id : action--50000000-0000-4000-8000-000000000007
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--50000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'submit 72-hour notification', 'secops_ng.tool.name': 'submit_72_hour_notification', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--50000000-0000-4000-8000-000000000007', attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'submit 72-hour notification', 'secops_ng.tool.name': 'submit_72_hour_notification', 'secops_ng.workflow.run_id': ''})
        )
        from incident_management.primitives.stage_clock import verdict_for_submission
        __notification_stage_verdict__ = verdict_for_submission(stage='notification', opened_at=__timeline_opened_at__, submitted_at=__notification_submitted_at__)

@tool
async def submit_1_month_final_report(incident_id: str, timeline_handle: str, significant: bool, cross_border: bool, notification_destinations: dict[str, object]) -> str:
    """Submit the NIS2 Article 23(4)(c) final report through the operator-configured regulator destination for the 'final_report' stage. The free-text fields on this submission — incident narrative, root-cause description, applied-mitigations summary — are the single DSPy-signature reach for this workflow; every other field is deterministic. Bounded by the stage-clock primitive — overrun trips the regulator-notification-overrun KRI.

    CACAO step_id : action--50000000-0000-4000-8000-000000000009
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--50000000-0000-4000-8000-000000000009',
        attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000009', 'secops_ng.step.name': 'submit 1-month final report', 'secops_ng.tool.name': 'submit_1_month_final_report', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--50000000-0000-4000-8000-000000000009', attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000009', 'secops_ng.step.name': 'submit 1-month final report', 'secops_ng.tool.name': 'submit_1_month_final_report', 'secops_ng.workflow.run_id': ''})
        )
        from incident_management.primitives.regulator_submission import resolve_destination
        __final_report_destination__ = resolve_destination(destinations=__notification_destinations__, stage='final_report')

@tool
async def close_incident_timeline(incident_id: str, timeline_handle: str) -> str:
    """Signal the F-PT-02 incident-timeline pattern's close: the canonical regulator-shaped timeline JSON is persisted at content/evidence/incidents/<__incident_id__>/timeline.json for downstream consumption by F-CP-02. Stamps the timeline-completeness KPI.

    CACAO step_id : action--50000000-0000-4000-8000-00000000000a
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--50000000-0000-4000-8000-00000000000a',
        attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-00000000000a', 'secops_ng.step.name': 'close incident timeline', 'secops_ng.tool.name': 'close_incident_timeline', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--50000000-0000-4000-8000-00000000000a', attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6c0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-00000000000a', 'secops_ng.step.name': 'close incident timeline', 'secops_ng.tool.name': 'close_incident_timeline', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--50000000-0000-4000-8000-00000000000a'"
        )

async def llm_step(state: PlaybookIncidentManagementV1State) -> dict:
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

STATE_SCHEMA = PlaybookIncidentManagementV1State
TOOLS = (intake_significant_incident_signal, classify_significance_and_cross_border_scope, open_incident_timeline, submit_24_hour_early_warning, submit_72_hour_notification, submit_1_month_final_report, close_incident_timeline,)
AGENTIC_HOOK = llm_step

