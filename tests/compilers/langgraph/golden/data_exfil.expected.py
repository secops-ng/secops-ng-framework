# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.data_exfil@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookDataExfilV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.data_exfil@v1.

    Playbook id: playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __signal_id__
    # Identifier of the originating DLP / egress signal supplied by the detection layer.
    signal_id: str
    # playbook_variable: __data_classification__
    # Resolved data classification of the affected payload (e.g. public, internal, confidential, restricted, special-category). Drives both containment and notification routing.
    data_classification: str
    # playbook_variable: __affected_subjects_count__
    # Estimated count of data subjects whose data is in scope after assessment. Feeds the regulator-threshold gate.
    affected_subjects_count: int
    # playbook_variable: __exfil_confirmed__
    # Whether scope assessment confirmed actual exfiltration. False signals trigger close-out, not containment.
    exfil_confirmed: bool
    # playbook_variable: __regulator_required__
    # Whether the affected-subjects count and data classification together cross the regulator-notification threshold (NIS2 Art. 23 / DORA Art. 19 / GDPR Art. 33 routing).
    regulator_required: bool
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
async def triage_signal(signal_id: str) -> None:
    """Receive the DLP / egress signal, hydrate it with originating user / asset / destination context, and decide whether the signal warrants scope assessment or is a known benign egress pattern.

    CACAO step_id : action--20000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--20000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'triage signal', 'secops_ng.tool.name': 'triage_signal'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--20000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'triage signal', 'secops_ng.tool.name': 'triage_signal'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--20000000-0000-4000-8000-000000000002'"
        )

@tool
async def scope_assessment(signal_id: str) -> dict[str, object]:
    """Determine the volume and classification of data observed leaving the boundary, the count of distinct data subjects affected, and whether actual exfiltration occurred or was prevented by an in-line control. Produces __data_classification__, __affected_subjects_count__, and __exfil_confirmed__.

    CACAO step_id : action--20000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--20000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'scope assessment', 'secops_ng.tool.name': 'scope_assessment'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--20000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'scope assessment', 'secops_ng.tool.name': 'scope_assessment'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--20000000-0000-4000-8000-000000000003'"
        )

@tool
async def containment(data_classification: str, affected_subjects_count: int) -> None:
    """Apply containment proportionate to data classification and scope: revoke session tokens, isolate the originating identity / host, force a credential rotation, and tighten the egress policy on the destination(s) named in the signal. Bounded by the operator-supplied authorisation policy.

    CACAO step_id : action--20000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--20000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'containment', 'secops_ng.tool.name': 'containment'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--20000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'containment', 'secops_ng.tool.name': 'containment'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--20000000-0000-4000-8000-000000000005'"
        )

@tool
async def notify_regulator(data_classification: str, affected_subjects_count: int) -> None:
    """Compose and send the regulator notification along the operator's pre-bound channel (national CSIRT for NIS2, competent authority for DORA, supervisory authority for GDPR). The notification payload is a structured incident finding sourced from the scope-assessment outputs.

    CACAO step_id : action--20000000-0000-4000-8000-000000000007
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--20000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify regulator', 'secops_ng.tool.name': 'notify_regulator'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--20000000-0000-4000-8000-000000000007', attributes={'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify regulator', 'secops_ng.tool.name': 'notify_regulator'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--20000000-0000-4000-8000-000000000007'"
        )

@tool
async def notify_customer(data_classification: str, affected_subjects_count: int) -> None:
    """Notify affected customers / data subjects via the operator's pre-bound channel. Tracked separately from regulator notification so the SLA-compliance KPI can report the two timelines independently.

    CACAO step_id : action--20000000-0000-4000-8000-000000000008
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--20000000-0000-4000-8000-000000000008',
        attributes={'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 'notify customer', 'secops_ng.tool.name': 'notify_customer'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--20000000-0000-4000-8000-000000000008', attributes={'secops_ng.playbook.id': 'playbook--20a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.step.id': 'action--20000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 'notify customer', 'secops_ng.tool.name': 'notify_customer'})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--20000000-0000-4000-8000-000000000008'"
        )

async def llm_step(state: PlaybookDataExfilV1State) -> dict:
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

STATE_SCHEMA = PlaybookDataExfilV1State
TOOLS = (triage_signal, scope_assessment, containment, notify_regulator, notify_customer,)
AGENTIC_HOOK = llm_step
