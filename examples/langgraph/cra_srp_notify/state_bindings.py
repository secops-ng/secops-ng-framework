# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.cra_srp_notify@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookCraSrpNotifyV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.cra_srp_notify@v1.

    Playbook id: playbook--5a509a09-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __case_id__
    # Case identifier handed in by the upstream incident-handling or vulnerability-intake playbook. Used as the correlation key across the three submission clocks so a reviewer can join the early-warning, full-notification, and final-report records into a single reportable-event ledger.
    case_id: str
    # playbook_variable: __clock_kind__
    # Which CRA Article 14 clock applies to this case. One of: actively_exploited_vulnerability (Art. 14(2) — 14-day final report) or severe_incident (Art. 14(3) — 1-month final report). Selected by the upstream classifier; determines the final-report deadline the delay step waits on.
    clock_kind: str
    # playbook_variable: __awareness_ts__
    # ISO 8601 timestamp when the operator became aware of the actively-exploited vulnerability or severe incident. Anchors the 24h / 72h / 14d-or-30d clocks. Stamped by the upstream classifier; the SRP intake step consumes it directly.
    awareness_ts: str
    # playbook_variable: __srp_early_warning_id__
    # Identifier of the 24h early-warning submission published to the SRP intake surface. Empty until the early-warning submission returns a confirmed receipt.
    srp_early_warning_id: str
    # playbook_variable: __srp_full_notification_id__
    # Identifier of the 72h full-notification submission published to the SRP intake surface. Empty until the full-notification submission returns a confirmed receipt.
    srp_full_notification_id: str
    # playbook_variable: __srp_final_report_id__
    # Identifier of the final-report submission published to the SRP intake surface (14 days for an actively-exploited vulnerability under Art. 14(2), or 1 month for a severe incident under Art. 14(3)). Empty until the final-report submission returns a confirmed receipt.
    srp_final_report_id: str
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
async def early_warning(case_id: str, clock_kind: str, awareness_ts: str) -> str:
    """SKELETON — CRA Article 14 24-hour early warning. Compose the early-warning submission body (product / manufacturer / vulnerability or incident metadata) against the SRP intake shape and dispatch it to the manufacturer's main-establishment CSIRT via the SRP, with simultaneous availability to ENISA per Article 14. Records __srp_early_warning_id__ on confirmed receipt. TODO (CORE): SRP intake schema is not yet public (Commission page notes a pre-go-live testing period ahead of 11 September 2026); the submission body shape is a placeholder here and a sibling CORE card lands the schema-conformant payload builder once the SRP schema is published. The 24h clock anchor is __awareness_ts__ + 24 hours.

    CACAO step_id : action--5a509a09-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--5a509a09-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--5a509a09-0000-4000-8000-000000000002', 'secops_ng.step.name': 'early_warning', 'secops_ng.tool.name': 'early_warning', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--5a509a09-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--5a509a09-0000-4000-8000-000000000002', 'secops_ng.step.name': 'early_warning', 'secops_ng.tool.name': 'early_warning', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--5a509a09-0000-4000-8000-000000000002'"
        )

@tool
async def wait_until_72h_deadline(awareness_ts: str) -> None:
    """SKELETON — durable delay to the CRA Article 14 72-hour deadline. Sleeps until __awareness_ts__ + 72 hours as durable state so the wait survives worker restart on each compile target. TODO (CORE): CACAO v2 does not ship a first-class 'delay' step type; the reference emitters (Temporal timer, n8n Wait node, LangGraph interrupt-then-resume-at-timestamp) each carry the wait in their idiomatic way. The compile-target parity test (roadmap goal G-03) verifies the 72h boundary survives restart without drift on all three targets.

    CACAO step_id : action--5a509a09-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--5a509a09-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--5a509a09-0000-4000-8000-000000000004', 'secops_ng.step.name': 'wait until 72h deadline', 'secops_ng.tool.name': 'wait_until_72h_deadline', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--5a509a09-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--5a509a09-0000-4000-8000-000000000004', 'secops_ng.step.name': 'wait until 72h deadline', 'secops_ng.tool.name': 'wait_until_72h_deadline', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--5a509a09-0000-4000-8000-000000000004'"
        )

@tool
async def full_notification(case_id: str, clock_kind: str, awareness_ts: str) -> str:
    """SKELETON — CRA Article 14 72-hour full notification. Compose and dispatch the full notification body (product / manufacturer / vulnerability or incident metadata plus corrective / mitigating measures the manufacturer has taken or recommended) to the SRP, with simultaneous availability to ENISA per Article 14. Records __srp_full_notification_id__ on confirmed receipt. TODO (CORE): SRP intake schema is not yet public; the submission body shape is a placeholder pending the CORE card.

    CACAO step_id : action--5a509a09-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--5a509a09-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--5a509a09-0000-4000-8000-000000000005', 'secops_ng.step.name': 'full_notification', 'secops_ng.tool.name': 'full_notification', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--5a509a09-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--5a509a09-0000-4000-8000-000000000005', 'secops_ng.step.name': 'full_notification', 'secops_ng.tool.name': 'full_notification', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--5a509a09-0000-4000-8000-000000000005'"
        )

@tool
async def wait_until_final_report_deadline(clock_kind: str, awareness_ts: str) -> None:
    """SKELETON — durable delay to the CRA Article 14 final-report deadline. For __clock_kind__ = actively_exploited_vulnerability (Art. 14(2)) the wait resolves at __awareness_ts__ + 14 days after a corrective or mitigating measure becomes available; for __clock_kind__ = severe_incident (Art. 14(3)) the wait resolves at __awareness_ts__ + 1 month. Modelled as durable state so the wait survives worker restart on each compile target. TODO (CORE): the 'after a corrective measure becomes available' anchor is an event, not a fixed offset from awareness — the CORE card wires the corrective-measure-available signal from the upstream vulnerability-intake or incident-handling playbook so this delay can start its 14-day clock at the right instant; a placeholder anchor is used in the SKELETON.

    CACAO step_id : action--5a509a09-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--5a509a09-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--5a509a09-0000-4000-8000-000000000006', 'secops_ng.step.name': 'wait until final-report deadline', 'secops_ng.tool.name': 'wait_until_final_report_deadline', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--5a509a09-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--5a509a09-0000-4000-8000-000000000006', 'secops_ng.step.name': 'wait until final-report deadline', 'secops_ng.tool.name': 'wait_until_final_report_deadline', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--5a509a09-0000-4000-8000-000000000006'"
        )

@tool
async def final_report(case_id: str, clock_kind: str, awareness_ts: str) -> str:
    """SKELETON — CRA Article 14 final report. Compose and dispatch the final report (description of the vulnerability, severity and impact, information on actors that have exploited or could exploit the vulnerability, and details of the corrective measures for Art. 14(2); analogous shape for Art. 14(3) severe incidents at the 1-month deadline) to the SRP with simultaneous availability to ENISA. Records __srp_final_report_id__ on confirmed receipt. TODO (CORE): SRP intake schema is not yet public; the submission body shape is a placeholder pending the CORE card.

    CACAO step_id : action--5a509a09-0000-4000-8000-000000000007
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--5a509a09-0000-4000-8000-000000000007',
        attributes={'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--5a509a09-0000-4000-8000-000000000007', 'secops_ng.step.name': 'final_report', 'secops_ng.tool.name': 'final_report', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--5a509a09-0000-4000-8000-000000000007', attributes={'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--5a509a09-0000-4000-8000-000000000007', 'secops_ng.step.name': 'final_report', 'secops_ng.tool.name': 'final_report', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--5a509a09-0000-4000-8000-000000000007'"
        )

async def llm_step(state: PlaybookCraSrpNotifyV1State) -> dict:
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

STATE_SCHEMA = PlaybookCraSrpNotifyV1State
TOOLS = (early_warning, wait_until_72h_deadline, full_notification, wait_until_final_report_deadline, final_report,)
AGENTIC_HOOK = llm_step

