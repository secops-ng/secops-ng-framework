# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.security_awareness_training@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookSecurityAwarenessTrainingV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.security_awareness_training@v1.

    Playbook id: playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __training_window__
    # ISO 8601 interval describing the training-programme cycle window for this run. Supplied by the scheduler that triggers this playbook or by an operator-initiated cycle-review request.
    training_window: str
    # playbook_variable: __training_scope__
    # Identifier of the in-scope training-programme surface for this run (matches a row in the operator's documented programme scope catalogue: which staff cohorts, which mandatory awareness tracks, which role-based tracks, and which regulatory training requirements are in scope for the programme).
    training_scope: str
    # playbook_variable: __assessment_id__
    # Identifier of the training-needs assessment artifact emitted by the schedule-assessment step: per-cohort record of (cohort id, required tracks, identified gaps, regulatory drivers, priority).
    assessment_id: str
    # playbook_variable: __curriculum_id__
    # Identifier of the training-content curriculum artifact emitted by the design-content step: per-track record of (track id, module ids, learning objectives, source citation, review date).
    curriculum_id: str
    # playbook_variable: __delivery_id__
    # Identifier of the training-delivery artifact emitted by the deliver-training step: per-cohort record of (cohort id, delivery channel, delivered at, target audience count).
    delivery_id: str
    # playbook_variable: __completion_id__
    # Identifier of the completion-record artifact emitted by the record-completion step: per-staff record of (staff id, track id, completion state, completed at, overdue-by-days) rolled up to per-cohort aggregate.
    completion_id: str
    # playbook_variable: __gap_report_id__
    # Identifier of the residual-gap report artifact emitted by the report-gaps step: structured gap summary the training owner reads at cycle close (missed-mandatory, overdue-role-based, uncovered-regulatory-requirement).
    gap_report_id: str
    # playbook_variable: __cycle_review_id__
    # Identifier of the cycle-review artifact emitted by the review-cycle step: dated end-of-cycle record carrying the assessment, curriculum, delivery, completion, and gap-report references, plus programme-level recommendations for the next cycle.
    cycle_review_id: str
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
async def schedule_assessment(training_window: str, training_scope: str) -> str:
    """Schedule the training-needs assessment against the in-scope programme surface: resolve the required awareness and role-based training tracks per cohort, identify residual gaps against the operator's declared training policy, and pin the per-cohort priority for this cycle. Emits __assessment_id__ as a per-cohort record. Read-only against the operator's HR / identity / policy surfaces; does not mutate roster or policy state.

    CACAO step_id : action--54000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--54000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'schedule assessment', 'secops_ng.tool.name': 'schedule_assessment', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--54000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'schedule assessment', 'secops_ng.tool.name': 'schedule_assessment', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--54000000-0000-4000-8000-000000000002'"
        )

@tool
async def design_content(assessment_id: str, training_scope: str) -> str:
    """Author or update the per-track training curriculum against the assessment artifact: learning objectives, module content references, source citations, and next review dates. Emits __curriculum_id__ as a per-track record. The curriculum is the programme-level content-authoring surface; individual per-cycle delivery lives downstream on this playbook and on the operational cyber_hygiene_training playbook.

    CACAO step_id : action--54000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--54000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'design content', 'secops_ng.tool.name': 'design_content', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--54000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'design content', 'secops_ng.tool.name': 'design_content', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--54000000-0000-4000-8000-000000000003'"
        )

@tool
async def deliver_training(curriculum_id: str, training_scope: str) -> str:
    """Deliver the cycle's curriculum to the in-scope cohorts along the operator's declared training channel(s) (learning-management surface, live session, self-paced module). Emits __delivery_id__ as a per-cohort delivery record. The delivery step writes delivery-intent records to the training surface; the operator's LMS owns final scheduling and per-staff dispatch.

    CACAO step_id : action--54000000-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--54000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'deliver training', 'secops_ng.tool.name': 'deliver_training', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--54000000-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'deliver training', 'secops_ng.tool.name': 'deliver_training', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--54000000-0000-4000-8000-000000000004'"
        )

@tool
async def record_completion(delivery_id: str, training_window: str) -> str:
    """Read per-staff completion state from the operator's learning-management surface against the delivery artifact and roll up to per-cohort aggregate. Emits __completion_id__ as per-staff (staff id, track id, completion state, completed at, overdue-by-days) with per-cohort completion-rate. Read-only against the LMS; does not mark completion on the operator's behalf.

    CACAO step_id : action--54000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--54000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'record completion', 'secops_ng.tool.name': 'record_completion', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--54000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'record completion', 'secops_ng.tool.name': 'record_completion', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--54000000-0000-4000-8000-000000000005'"
        )

@tool
async def report_gaps(completion_id: str, assessment_id: str) -> str:
    """Compose the residual-gap report for the cycle: missed-mandatory tracks, overdue role-based tracks, cohorts below the declared completion-rate target, and any uncovered regulatory training requirement the assessment surfaced but the curriculum did not close. Emits __gap_report_id__. The report is the programme-owner-facing summary of what did NOT close this cycle.

    CACAO step_id : action--54000000-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--54000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'report gaps', 'secops_ng.tool.name': 'report_gaps', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--54000000-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'report gaps', 'secops_ng.tool.name': 'report_gaps', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--54000000-0000-4000-8000-000000000006'"
        )

@tool
async def review_cycle(assessment_id: str, curriculum_id: str, delivery_id: str, completion_id: str, gap_report_id: str, training_window: str) -> str:
    """Close the cycle with a dated cycle-review record referencing the assessment, curriculum, delivery, completion, and gap-report artifacts, plus programme-level recommendations feeding the next cycle's assessment (curriculum updates, cohort-scope changes, regulatory drivers). The cycle-review record is the audit-evident programme-governance artifact NIS2 Art. 21(2)(g) reviewers read against the operator's declared training policy.

    CACAO step_id : action--54000000-0000-4000-8000-000000000007
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--54000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'review cycle', 'secops_ng.tool.name': 'review_cycle', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--54000000-0000-4000-8000-000000000007', attributes={'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'review cycle', 'secops_ng.tool.name': 'review_cycle', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--54000000-0000-4000-8000-000000000007'"
        )

async def llm_step(state: PlaybookSecurityAwarenessTrainingV1State) -> dict:
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

STATE_SCHEMA = PlaybookSecurityAwarenessTrainingV1State
TOOLS = (schedule_assessment, design_content, deliver_training, record_completion, report_gaps, review_cycle,)
AGENTIC_HOOK = llm_step

