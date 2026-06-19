# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.infra_posture_management@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookInfraPostureManagementV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.infra_posture_management@v1.

    Playbook id: playbook--06f06f06-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __execution_id__
    # Per-execution identifier issued by the compile target's workflow runtime (n8n execution id, Temporal workflow run id, LangGraph thread/checkpoint id). Pinned by the upstream runtime; the workflow reads it for the posture-evidence artifact join.
    execution_id: str
    # playbook_variable: __scope_ref__
    # Pointer to the operator's in-scope infrastructure manifest (cloud accounts, identity boundaries, network baselines) under review on this execution. Operator-configured; the workflow reads it as the closed list of resources the posture evaluation walks. No default scope is shipped — the framework does not assume the operator's infrastructure shape.
    scope_ref: str
    # playbook_variable: __posture_state_ref__
    # Pointer to the collected posture-state snapshot produced by collect-posture. Closed shape per CORE sibling card; resource-id keyed, configuration-state valued. Consumed by evaluate-controls.
    posture_state_ref: str
    # playbook_variable: __control_evaluation_ref__
    # Pointer to the per-control evaluation result set produced by evaluate-controls — one entry per (control_ref, scoped-resource-id) pair, with the attestation state (effective / partially_effective / ineffective) and the deviation list. Consumed by emit-posture-evidence.
    control_evaluation_ref: str
    # playbook_variable: __posture_artifact_ref__
    # Pointer to the posture-evidence artifact emitted by emit-posture-evidence, shaped against schemas/evidence/posture.schema.json.
    posture_artifact_ref: str
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
async def collect_posture(execution_id: str, scope_ref: str) -> str:
    """Walk the in-scope infrastructure manifest at __scope_ref__ and collect the current posture-state snapshot: per-resource configuration state read from the operator's posture sources (cloud account read APIs, identity-provider read APIs, network-baseline read APIs). Read-only by contract; the workflow MUST NOT mutate any resource on the collect path. Source endpoints are operator-configured — the framework ships no default non-EU endpoint and no hosted-SaaS dependency.

    CACAO step_id : action--06f06f06-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--06f06f06-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--06f06f06-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--06f06f06-0000-4000-8000-000000000002', 'secops_ng.step.name': 'collect-posture', 'secops_ng.tool.name': 'collect_posture', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--06f06f06-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--06f06f06-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--06f06f06-0000-4000-8000-000000000002', 'secops_ng.step.name': 'collect-posture', 'secops_ng.tool.name': 'collect_posture', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--06f06f06-0000-4000-8000-000000000002'"
        )

@tool
async def evaluate_controls(posture_state_ref: str) -> str:
    """Evaluate each control declared in the operator's posture policy against the collected posture state. Per (control_ref, scoped-resource-id) pair, classify the attestation state as effective, partially_effective, or ineffective; capture the deviation list (configuration values that differ from the declared baseline) on partially_effective / ineffective entries. Deterministic on the same posture snapshot and the same policy version — re-evaluation under the same inputs re-derives the same result set so a reviewer can re-derive the evaluation off the committed artifact.

    CACAO step_id : action--06f06f06-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--06f06f06-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--06f06f06-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--06f06f06-0000-4000-8000-000000000003', 'secops_ng.step.name': 'evaluate-controls', 'secops_ng.tool.name': 'evaluate_controls', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--06f06f06-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--06f06f06-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--06f06f06-0000-4000-8000-000000000003', 'secops_ng.step.name': 'evaluate-controls', 'secops_ng.tool.name': 'evaluate_controls', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--06f06f06-0000-4000-8000-000000000003'"
        )

@tool
async def emit_posture_evidence(execution_id: str, posture_state_ref: str, control_evaluation_ref: str) -> str:
    """Combine the posture-state snapshot and the per-control evaluation result set into one posture-evidence artifact shaped against schemas/evidence/posture.schema.json (stream: posture). The artifact carries the workflow id, execution id, compile target, regulation_refs (nis2:art-21-2-a), control_refs, the evaluated_at timestamp, the policy version under which the evaluation ran, and the provenance envelope. Emission is byte-stable: same execution inputs, same compile target, same policy version re-derive the same artifact_id (SHA-256 of workflow_id|execution_id|compile_target|policy_version). Destination is operator-configured — no default non-EU endpoint.

    CACAO step_id : action--06f06f06-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--06f06f06-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--06f06f06-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--06f06f06-0000-4000-8000-000000000004', 'secops_ng.step.name': 'emit-posture-evidence', 'secops_ng.tool.name': 'emit_posture_evidence', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--06f06f06-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--06f06f06-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--06f06f06-0000-4000-8000-000000000004', 'secops_ng.step.name': 'emit-posture-evidence', 'secops_ng.tool.name': 'emit_posture_evidence', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--06f06f06-0000-4000-8000-000000000004'"
        )

async def llm_step(state: PlaybookInfraPostureManagementV1State) -> dict:
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

STATE_SCHEMA = PlaybookInfraPostureManagementV1State
TOOLS = (collect_posture, evaluate_controls, emit_posture_evidence,)
AGENTIC_HOOK = llm_step

