# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.cyber_hygiene_training@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookCyberHygieneTrainingV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.cyber_hygiene_training@v1.

    Playbook id: playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __training_window__
    # ISO 8601 interval describing the training-evaluation window for this run. Supplied by the scheduler that triggers this playbook (cron, Temporal schedule, or n8n trigger), or by an operator-initiated trigger.
    training_window: str
    # playbook_variable: __training_scope__
    # Identifier of the in-scope training surface for this run (matches a row in the operator's documented scope catalogue: which staff cohorts, which mandatory awareness and role-based training tracks, and which phishing-simulation cohorts are subject to the declared training policy).
    training_scope: str
    # playbook_variable: __roster_id__
    # Identifier of the training-roster snapshot artifact: per-staff record of (staff id, cohort, mandatory training tracks assigned, role-based training tracks assigned, joiner/leaver state) resolved from the operator's HR / identity source against __training_scope__.
    roster_id: str
    # playbook_variable: __cycle_id__
    # Identifier of the scheduled training-cycle artifact: per-cohort record of (cohort id, training track id, assigned at, due at, channel) emitted by the scheduling step against the training-roster snapshot.
    cycle_id: str
    # playbook_variable: __simulation_id__
    # Identifier of the phishing-simulation run artifact: per-recipient record of (recipient id, template id, delivered at, clicked, reported, time-to-report) emitted by the simulation step. The simulation is a documented exercise; it does NOT trigger downstream incident response.
    simulation_id: str
    # playbook_variable: __completion_id__
    # Identifier of the training-completion tracking artifact: per-staff record of (staff id, track id, completion state, completed at, overdue-by-days) and per-cohort aggregate of completion-rate and click/report rate against the declared targets.
    completion_id: str
    # playbook_variable: __attestation_id__
    # Identifier of the dated cyber-hygiene and security-training posture attestation record published to the operator's evidence store. Carries the training-roster snapshot, the cycle assignments, the simulation results, and the completion tracking — the audit-evident discharge of NIS2 Art.21(2)(g).
    attestation_id: str
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
async def inventory_training_roster(training_window: str, training_scope: str) -> str:
    """Resolve the in-scope training roster from the operator's HR / identity source against __training_scope__: which staff cohorts are subject to mandatory awareness training, which staff hold roles that require role-based training, and which cohorts are enrolled in the phishing-simulation programme. Emits __roster_id__ as a per-staff record of (staff id, cohort, mandatory tracks assigned, role-based tracks assigned, joiner/leaver state). The inventory is read-only against the HR and identity surfaces; it does not modify roster assignments. Staff with no declared training requirement in the operator's policy are reported as policy gaps rather than completion gaps; the distinction is preserved so the attestation surfaces the policy-side and operations-side gaps separately.

    CACAO step_id : action--53000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--53000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'inventory training roster', 'secops_ng.tool.name': 'inventory_training_roster', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--53000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'inventory training roster', 'secops_ng.tool.name': 'inventory_training_roster', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--53000000-0000-4000-8000-000000000002'"
        )

@tool
async def schedule_training_cycle(roster_id: str, training_window: str) -> str:
    """Schedule the per-cycle awareness and role-based training assignments for the roster emitted by inventory-training-roster against the declared training tracks and cadence. Emits __cycle_id__ as a per-cohort record of (cohort id, training track id, assigned at, due at, channel). The scheduling step writes assignment intents to the operator's learning-management surface; it does NOT push training content directly to staff. Tracks with no declared cadence in the operator's policy are reported as policy gaps rather than scheduling failures.

    CACAO step_id : action--53000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--53000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'schedule training cycle', 'secops_ng.tool.name': 'schedule_training_cycle', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--53000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'schedule training cycle', 'secops_ng.tool.name': 'schedule_training_cycle', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--53000000-0000-4000-8000-000000000003'"
        )

@tool
async def run_phishing_simulation(cycle_id: str, training_scope: str) -> str:
    """Dispatch the cycle's phishing-simulation exercise to the cohorts enrolled in the simulation programme using a documented simulation template. Emits __simulation_id__ as a per-recipient record of (recipient id, template id, delivered at, clicked, reported, time-to-report). The simulation is a clearly-labelled exercise governed by the operator's awareness programme; it does NOT trigger downstream incident response, does NOT inject content into production mailflow controls, and does NOT exfiltrate credentials. Cohorts with no declared simulation cadence are reported as policy gaps rather than simulation failures.

    CACAO step_id : action--53000000-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--53000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'run phishing simulation', 'secops_ng.tool.name': 'run_phishing_simulation', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--53000000-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'run phishing simulation', 'secops_ng.tool.name': 'run_phishing_simulation', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--53000000-0000-4000-8000-000000000004'"
        )

@tool
async def track_completion(cycle_id: str, simulation_id: str) -> str:
    """Read completion state for the cycle's training assignments from the operator's learning-management surface and aggregate the phishing-simulation results from __simulation_id__. Emits __completion_id__ as a per-staff record of (staff id, track id, completion state, completed at, overdue-by-days) and per-cohort aggregate of completion-rate, click-rate, and report-rate against the declared targets. The tracking step is read-only against the LMS; it does NOT mark training as complete on the operator's behalf. Tracks past their due date are reported as overdue-completion gaps with the overdue-by-days delta preserved so the attestation surfaces the magnitude of the gap rather than a boolean.

    CACAO step_id : action--53000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--53000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'track completion', 'secops_ng.tool.name': 'track_completion', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--53000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'track completion', 'secops_ng.tool.name': 'track_completion', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--53000000-0000-4000-8000-000000000005'"
        )

@tool
async def evidence_capture(roster_id: str, cycle_id: str, simulation_id: str, completion_id: str, training_window: str) -> str:
    """Compose and publish the dated cyber-hygiene and security-training posture attestation to the operator's evidence store. The record carries the training-roster snapshot, the cycle assignments, the simulation results, the completion tracking, the training window, and a top-level gap summary (missed-mandatory-training, overdue-role-based-training, simulation-click counts). This is the audit-evident artifact NIS2 Art.21(2)(g) reviewers read; missing or stale attestations are the failure mode the metrics surface. The attestation is always emitted, including the policy-gap branch (which records missing-policy conditions rather than skipping the attestation).

    CACAO step_id : action--53000000-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--53000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'evidence capture', 'secops_ng.tool.name': 'evidence_capture', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--53000000-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'evidence capture', 'secops_ng.tool.name': 'evidence_capture', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--53000000-0000-4000-8000-000000000006'"
        )

@tool
async def notify_gaps(attestation_id: str, training_scope: str) -> None:
    """Deliver the attestation reference and the gap summary to the training owner along the operator's pre-bound channel (ticketing system, chat thread, email). Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently; an attestation written but never delivered to the owner is itself a posture gap.

    CACAO step_id : action--53000000-0000-4000-8000-000000000007
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--53000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify gaps', 'secops_ng.tool.name': 'notify_gaps', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--53000000-0000-4000-8000-000000000007', attributes={'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify gaps', 'secops_ng.tool.name': 'notify_gaps', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--53000000-0000-4000-8000-000000000007'"
        )

async def llm_step(state: PlaybookCyberHygieneTrainingV1State) -> dict:
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

STATE_SCHEMA = PlaybookCyberHygieneTrainingV1State
TOOLS = (inventory_training_roster, schedule_training_cycle, run_phishing_simulation, track_completion, evidence_capture, notify_gaps,)
AGENTIC_HOOK = llm_step

