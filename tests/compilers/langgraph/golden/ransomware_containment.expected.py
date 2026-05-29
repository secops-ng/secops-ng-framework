# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.ransomware_containment@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages


class PlaybookRansomwareContainmentV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.ransomware_containment@v1.

    Playbook id: playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b8

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __signal_id__
    # Identifier of the originating detection signal (EDR alert, Sigma match, or SOC-raised ticket).
    signal_id: str
    # playbook_variable: __affected_host__
    # Host identifier (hostname or asset id) implicated by the signal; consumed by isolation.
    affected_host: str
    # playbook_variable: __affected_identity__
    # Identity principal (user or service account) implicated by the signal; consumed by identity revocation.
    affected_identity: str
    # playbook_variable: __ransomware_confirmed__
    # Whether triage promoted the signal to a confirmed ransomware event. False routes to close-out without containment.
    ransomware_confirmed: bool
    # playbook_variable: __edr_available__
    # Whether the EDR agent on the affected host is reachable and capable of issuing an isolate action. False triggers the network-ACL fallback.
    edr_available: bool
    # playbook_variable: __latest_known_good_snapshot__
    # Identifier of the most recent backup snapshot that pre-dates the event window. Produced by the backup-verification step.
    latest_known_good_snapshot: str
    # playbook_variable: __snapshot_integrity_ok__
    # Whether the located snapshot's integrity hash matches the value recorded in the backup catalogue.
    snapshot_integrity_ok: bool
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
async def triage_signal(signal_id: str) -> dict[str, object]:
    """Receive the originating detection signal and hydrate it with host, identity, and process context. Decide whether the signal is a confirmed ransomware event or a benign / out-of-scope alert. Produces __affected_host__, __affected_identity__, and __ransomware_confirmed__.

    CACAO step_id : action--30000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    raise NotImplementedError(
        f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000002'"
    )

@tool
async def endpoint_isolation_edr_isolate(affected_host: str) -> None:
    """Issue the EDR-vendor isolate action against __affected_host__ via the operator's pre-bound EDR agent. Bounded by the operator-supplied authorisation policy. Primary path.

    CACAO step_id : action--30000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    raise NotImplementedError(
        f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000005'"
    )

@tool
async def endpoint_isolation_network_acl_deny_fallback(affected_host: str) -> None:
    """EDR fallback: deny all ingress/egress for __affected_host__ at the operator's network chokepoint (firewall rule, switchport disable, or SDN policy). Used when the EDR agent is unreachable or absent.

    CACAO step_id : action--30000000-0000-4000-8000-000000000006
    CACAO type    : action
    """
    raise NotImplementedError(
        f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000006'"
    )

@tool
async def identity_revocation(affected_identity: str) -> None:
    """Disable the implicated user account, revoke active sessions, and invalidate refresh/access tokens at the operator's IdP. Includes Kerberos TGT invalidation where supported. Targets __affected_identity__.

    CACAO step_id : action--30000000-0000-4000-8000-000000000007
    CACAO type    : action
    """
    raise NotImplementedError(
        f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000007'"
    )

@tool
async def backup_verification() -> dict[str, object]:
    """Locate the most recent known-good backup snapshot that pre-dates the event window and verify its integrity hash against the backup-catalogue record. Produces __latest_known_good_snapshot__ and __snapshot_integrity_ok__. Does NOT restore — restore is a separate, out-of-scope recovery playbook.

    CACAO step_id : action--30000000-0000-4000-8000-000000000008
    CACAO type    : action
    """
    raise NotImplementedError(
        f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000008'"
    )

@tool
async def comms_plan(affected_host: str, affected_identity: str, latest_known_good_snapshot: str, snapshot_integrity_ok: bool) -> None:
    """Notify the IR lead and comms officer along the operator's pre-bound channels, and draft the regulator early-warning pre-notification per NIS2 Article 23 within the 24-hour clock from initial detection. The drafted notification is staged for human sign-off, not auto-sent.

    CACAO step_id : action--30000000-0000-4000-8000-000000000009
    CACAO type    : action
    """
    raise NotImplementedError(
        f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000009'"
    )

async def llm_step(state: PlaybookRansomwareContainmentV1State) -> dict:
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

STATE_SCHEMA = PlaybookRansomwareContainmentV1State
TOOLS = (triage_signal, endpoint_isolation_edr_isolate, endpoint_isolation_network_acl_deny_fallback, identity_revocation, backup_verification, comms_plan,)
AGENTIC_HOOK = llm_step
