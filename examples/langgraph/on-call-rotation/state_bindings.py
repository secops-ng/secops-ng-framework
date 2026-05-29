# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.on_call_rotation@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages


class PlaybookOnCallRotationV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.on_call_rotation@v1.

    Playbook id: playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __shift_window__
    # ISO 8601 interval describing the shift window being evaluated. Supplied by the scheduler that triggers this playbook (cron, Temporal schedule, or n8n trigger).
    shift_window: str
    # playbook_variable: __current_on_call__
    # Identifier of the responder holding the primary on-call slot for the evaluated shift window. Resolved from the roster against the shift window.
    current_on_call: str
    # playbook_variable: __next_on_call__
    # Identifier of the responder receiving the next shift. Used by the handoff branch; empty when the playbook runs mid-shift.
    next_on_call: str
    # playbook_variable: __escalation_chain__
    # Ordered, comma-separated chain of responders the paging system will escalate through (primary, secondary, manager). Bound from the roster + tier policy and read by the operator's paging system at page time.
    escalation_chain: str
    # playbook_variable: __handoff_window__
    # True when the evaluated shift window crosses a rotation boundary and a handoff brief is due. False during steady-state shifts.
    handoff_window: bool
    # playbook_variable: __brief_id__
    # Identifier of the generated handoff brief artifact (open incidents, recent alerts, ack-latency snapshot). Empty when no brief is produced.
    brief_id: str
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
async def load_rotation_roster(shift_window: str) -> dict[str, object]:
    """Read the rotation roster from the operator's source of truth (paging system schedule, calendar feed, or roster file) and resolve who holds the primary slot and who receives the next shift for the evaluated window. The roster source itself is operator-bound; this step normalises its output into __current_on_call__ and __next_on_call__.

    CACAO step_id : action--30000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    raise NotImplementedError(
        f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000002'"
    )

@tool
async def bind_escalation_tiers(current_on_call: str) -> dict[str, object]:
    """Resolve the escalation chain the paging system will fan through when an alert is not acknowledged: primary (current_on_call), secondary (back-up slot from the roster), then manager. The bound chain is published to the paging system's runtime configuration so the next page uses it. Detection coverage for unusual-hours authentication anomalies during off-hours rotation handoff and for suspicious privileged-account modification during rotation gaps is wired by the CORE-layer mapping; upstream SigmaHQ rule ids are referenced from the playbook-level external_references (TODO entries until pinned).

    CACAO step_id : action--30000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    raise NotImplementedError(
        f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000003'"
    )

@tool
async def generate_handoff_brief(current_on_call: str, next_on_call: str) -> str:
    """Compose a structured handoff brief covering open incidents, recent alerts within the configured lookback, outstanding escalations, and ack-latency snapshot for the prior shift. The brief is delivered as a structured artifact (markdown + a JSON payload), not free-form prose, so the next on-call ingests it deterministically.

    CACAO step_id : action--30000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    raise NotImplementedError(
        f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000005'"
    )

@tool
async def notify_incoming_on_call(next_on_call: str, brief_id: str) -> None:
    """Deliver the handoff brief to the incoming on-call along the operator's pre-bound channel (paging system DM, chat thread, email). Tracked separately from brief generation so the delivery-SLA KPI can report compose-time and deliver-time independently.

    CACAO step_id : action--30000000-0000-4000-8000-000000000006
    CACAO type    : action
    """
    raise NotImplementedError(
        f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000006'"
    )

async def llm_step(state: PlaybookOnCallRotationV1State) -> dict:
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

STATE_SCHEMA = PlaybookOnCallRotationV1State
TOOLS = (load_rotation_roster, bind_escalation_tiers, generate_handoff_brief, notify_incoming_on_call,)
AGENTIC_HOOK = llm_step

