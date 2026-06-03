# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.post_incident_review@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookPostIncidentReviewV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.post_incident_review@v1.

    Playbook id: playbook--40a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b9

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __incident_id__
    # Identifier of the closed/contained incident this review is being run against. External input.
    incident_id: str
    # playbook_variable: __timeline_artifact__
    # Reference to the collated timeline artifact (path, document ID, or URI) produced by the timeline-collation step.
    timeline_artifact: str
    # playbook_variable: __evidence_gaps_present__
    # Whether the timeline collation step detected gaps in the evidence record — cleared eventlogs, disabled audit policy, timestomped files, or any of the anti-forensics signals enumerated in external_references. Gaps are recorded in the review without blocking it; the review template explicitly addresses how decisions were made under partial evidence.
    evidence_gaps_present: bool
    # playbook_variable: __review_artifact__
    # Reference to the completed blameless-review document (path, document ID, or URI) produced by the review-template step.
    review_artifact: str
    # playbook_variable: __corrective_action_register__
    # Reference to the corrective-action register entry (path, ticket ID, or URI) produced by the corrective-action-tracking step. Holds owner, due-date, and verification clause for each action item.
    corrective_action_register: str
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
async def timeline_collation(incident_id: str) -> dict[str, object]:
    """Collate a chronological timeline of the incident from the artifacts the responders left behind: ticket comments, chat transcripts, EDR / SIEM exports, network captures, and operator-supplied evidence packages. The step must flag gaps in the evidence record where anti-forensics signals (cleared eventlogs, disabled audit policy, timestomped files) are present — these are recorded in __evidence_gaps_present__ rather than silently smoothed over, so the review template can address decisions made under partial evidence. Produces __timeline_artifact__ and __evidence_gaps_present__.

    CACAO step_id : action--40000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--40000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--40a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b9', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'timeline collation', 'secops_ng.tool.name': 'timeline_collation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--40000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--40a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b9', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'timeline collation', 'secops_ng.tool.name': 'timeline_collation'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--40000000-0000-4000-8000-000000000002'"
        )

@tool
async def blameless_review_template(incident_id: str, timeline_artifact: str, evidence_gaps_present: bool) -> str:
    """Walk the operator's blameless review template against the collated timeline. The template separates contributing factors (process, tooling, staffing, training, environment) from individual error, and explicitly captures decisions that were reasonable given the evidence available at the time. If __evidence_gaps_present__ is true the template's evidence-gaps section is mandatory rather than optional. Produces __review_artifact__.

    CACAO step_id : action--40000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--40000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--40a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b9', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'blameless review template', 'secops_ng.tool.name': 'blameless_review_template'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--40000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--40a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b9', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'blameless review template', 'secops_ng.tool.name': 'blameless_review_template'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--40000000-0000-4000-8000-000000000003'"
        )

@tool
async def corrective_action_tracking(incident_id: str, review_artifact: str) -> str:
    """Extract corrective actions from the review artifact and register each one with owner, due-date, and verification clause. Registration is the deliverable here — execution and verification of each action are out of scope for this playbook (they live on the operator's existing change / ticketing system). Produces __corrective_action_register__.

    CACAO step_id : action--40000000-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--40000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--40a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b9', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'corrective-action tracking', 'secops_ng.tool.name': 'corrective_action_tracking'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--40000000-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--40a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b9', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'corrective-action tracking', 'secops_ng.tool.name': 'corrective_action_tracking'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--40000000-0000-4000-8000-000000000004'"
        )

async def llm_step(state: PlaybookPostIncidentReviewV1State) -> dict:
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

STATE_SCHEMA = PlaybookPostIncidentReviewV1State
TOOLS = (timeline_collation, blameless_review_template, corrective_action_tracking,)
AGENTIC_HOOK = llm_step
