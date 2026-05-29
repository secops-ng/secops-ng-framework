# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.vuln_intake@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages


class PlaybookVulnIntakeV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.vuln_intake@v1.

    Playbook id: playbook--aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __finding_id__
    # Vendor advisory or scanner finding identifier.
    finding_id: str
    # playbook_variable: __severity__
    # Normalised severity (CVSS-derived) — one of low, medium, high, critical.
    severity: str
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
async def enrich_finding(finding_id: str) -> str:
    """Pull asset, owner, and exposure context for the finding.

    CACAO step_id : action--22222222-2222-4222-8222-222222222222
    CACAO type    : action
    """
    raise NotImplementedError(
        f"CACAO action tool not implemented: step_id='action--22222222-2222-4222-8222-222222222222'"
    )

@tool
async def open_critical_ticket() -> None:
    """Open a P1 ticket with the asset owner and link the advisory.

    CACAO step_id : action--44444444-4444-4444-8444-444444444444
    CACAO type    : action
    """
    raise NotImplementedError(
        f"CACAO action tool not implemented: step_id='action--44444444-4444-4444-8444-444444444444'"
    )

@tool
async def queue_routine_ticket() -> None:
    """Queue a routine remediation ticket on the team's backlog.

    CACAO step_id : action--55555555-5555-4555-8555-555555555555
    CACAO type    : action
    """
    raise NotImplementedError(
        f"CACAO action tool not implemented: step_id='action--55555555-5555-4555-8555-555555555555'"
    )

async def llm_step(state: PlaybookVulnIntakeV1State) -> dict:
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

STATE_SCHEMA = PlaybookVulnIntakeV1State
TOOLS = (enrich_finding, open_critical_ticket, queue_routine_ticket,)
AGENTIC_HOOK = llm_step

