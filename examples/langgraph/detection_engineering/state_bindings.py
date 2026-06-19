# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.detection_engineering@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookDetectionEngineeringV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.detection_engineering@v1.

    Playbook id: playbook--f0e4f404-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __effectiveness_snapshot_id__
    # Stable identifier of the per-rule-version effectiveness snapshot emitted by the measure state. SHA-256 hex digest shape per the snapshot schema. Persisted into the operator's configured metric sink.
    effectiveness_snapshot_id: str
    # playbook_variable: __proposal_rationale__
    # Short rationale the proposer attached to the candidate rule (what threat it addresses, which detection gap it closes, which ATT&CK technique(s) it binds). Carried opaquely through the lifecycle.
    proposal_rationale: str
    # playbook_variable: __review_verdict__
    # Verdict produced by the review state. One of: approved, changes_requested, rejected. Transitions are unconditional in this artifact; the gating predicate on ``review -> ship`` reads this variable in a follow-up sibling card.
    review_verdict: str
    # playbook_variable: __rule_id__
    # Stable identifier of the rule being lifecycled. Opaque to the framework; the operator's detection store assigns it.
    rule_id: str
    # playbook_variable: __rule_version__
    # Version label of the candidate rule. The lifecycle operates on a single rule-version at a time so the effectiveness snapshot can pin its measurement to the exact version that produced it.
    rule_version: str
    # playbook_variable: __ship_status__
    # Production status after the ship state. One of: production, staged, withdrawn. Transitions are unconditional in this artifact; the gating predicate on ``ship -> measure`` reads this variable in a follow-up sibling card.
    ship_status: str
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
async def propose_rule_version(rule_id: str, rule_version: str, proposal_rationale: str) -> None:
    """Intake the candidate rule version, its rationale, and the ATT&CK / detection-class bindings the proposer asserts. Operator wires the proposal-envelope handler in n8n; the CACAO I/O contract carries the inputs and the variable the next step reads.

    CACAO step_id : action--f0e4f404-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--f0e4f404-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--f0e4f404-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--f0e4f404-0000-4000-8000-000000000002', 'secops_ng.step.name': 'propose-rule-version', 'secops_ng.tool.name': 'propose_rule_version', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--f0e4f404-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--f0e4f404-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--f0e4f404-0000-4000-8000-000000000002', 'secops_ng.step.name': 'propose-rule-version', 'secops_ng.tool.name': 'propose_rule_version', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--f0e4f404-0000-4000-8000-000000000002'"
        )

@tool
async def review_rule_version(rule_id: str, rule_version: str) -> str:
    """Peer-review the candidate rule against the operator's review checklist. Produces ``__review_verdict__``. Transitions are unconditional in this artifact; the follow-up sibling inserts a switch-condition keyed on the verdict with three branches (approved -> ship, changes_requested -> propose, rejected -> end).

    CACAO step_id : action--f0e4f404-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--f0e4f404-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--f0e4f404-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--f0e4f404-0000-4000-8000-000000000003', 'secops_ng.step.name': 'review-rule-version', 'secops_ng.tool.name': 'review_rule_version', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--f0e4f404-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--f0e4f404-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--f0e4f404-0000-4000-8000-000000000003', 'secops_ng.step.name': 'review-rule-version', 'secops_ng.tool.name': 'review_rule_version', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--f0e4f404-0000-4000-8000-000000000003'"
        )

@tool
async def ship_rule_version(rule_id: str, rule_version: str, review_verdict: str) -> str:
    """Promote the approved rule version to production status in the operator's detection store. Operator-side destination is resolved at the compile target's config layer (sovereign-stack constraint — the framework ships no default detection store). Sets ``__ship_status__``.

    CACAO step_id : action--f0e4f404-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--f0e4f404-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--f0e4f404-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--f0e4f404-0000-4000-8000-000000000004', 'secops_ng.step.name': 'ship-rule-version', 'secops_ng.tool.name': 'ship_rule_version', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--f0e4f404-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--f0e4f404-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--f0e4f404-0000-4000-8000-000000000004', 'secops_ng.step.name': 'ship-rule-version', 'secops_ng.tool.name': 'ship_rule_version', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--f0e4f404-0000-4000-8000-000000000004'"
        )

@tool
async def measure_rule_version(rule_id: str, rule_version: str, ship_status: str) -> str:
    """Emit a per-rule-version effectiveness-metric snapshot shaped per ``schemas/evidence/rule-effectiveness-snapshot.schema.json``. The snapshot pins the indicator value to the exact (``__rule_id__``, ``__rule_version__``) the lifecycle is operating on and carries pointers to the OCSF source-data shape and the reference visualisation hint the F-CP-06 effectiveness stream consumes. Metric storage is operator-configured; the n8n adapter at ``compilers/n8n/evidence/rule_effectiveness_node.py`` writes the snapshot to a directory the operator's chosen sink ingests from.

    CACAO step_id : action--f0e4f404-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--f0e4f404-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--f0e4f404-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--f0e4f404-0000-4000-8000-000000000005', 'secops_ng.step.name': 'measure-rule-version', 'secops_ng.tool.name': 'measure_rule_version', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--f0e4f404-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--f0e4f404-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--f0e4f404-0000-4000-8000-000000000005', 'secops_ng.step.name': 'measure-rule-version', 'secops_ng.tool.name': 'measure_rule_version', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--f0e4f404-0000-4000-8000-000000000005'"
        )

async def llm_step(state: PlaybookDetectionEngineeringV1State) -> dict:
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

STATE_SCHEMA = PlaybookDetectionEngineeringV1State
TOOLS = (propose_rule_version, review_rule_version, ship_rule_version, measure_rule_version,)
AGENTIC_HOOK = llm_step

