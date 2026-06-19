# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.iam_auditor@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookIamAuditorV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.iam_auditor@v1.

    Playbook id: playbook--08aa0d10-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __execution_id__
    # Per-execution identifier issued by the compile target's workflow runtime (n8n execution id, Temporal workflow run id, LangGraph thread/checkpoint id). Pinned by the upstream runtime; the workflow reads it for the access-evidence artifact join.
    execution_id: str
    # playbook_variable: __caller_identity_ref__
    # Pointer to the caller-identity block produced by enumerate-identities — role-shaped principal id (service-account name, workflow-runtime principal, automation role) per the F-CP-07 public-bar discipline.
    caller_identity_ref: str
    # playbook_variable: __capabilities_ref__
    # Pointer to the closed capability list produced by enumerate-capabilities — verb.resource tokens the caller held at execution time.
    capabilities_ref: str
    # playbook_variable: __access_artifact_ref__
    # Pointer to the access-evidence artifact emitted by emit-access-evidence, shaped against schemas/evidence/access.schema.json.
    access_artifact_ref: str
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
async def enumerate_identities(execution_id: str) -> str:
    """Resolve the caller identity that invoked the compiled workflow on this execution. The identity is role-shaped (service-account name, workflow-runtime principal id, automation role) — never an individual personal name or a credential-shaped string. The compile target's runtime is the source of truth: n8n credential binding, Temporal worker identity, LangGraph runtime principal. Output is the caller-identity block consumed by emit-access-evidence.

    CACAO step_id : action--08aa0d10-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--08aa0d10-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--08aa0d10-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--08aa0d10-0000-4000-8000-000000000002', 'secops_ng.step.name': 'enumerate-identities', 'secops_ng.tool.name': 'enumerate_identities', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--08aa0d10-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--08aa0d10-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--08aa0d10-0000-4000-8000-000000000002', 'secops_ng.step.name': 'enumerate-identities', 'secops_ng.tool.name': 'enumerate_identities', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--08aa0d10-0000-4000-8000-000000000002'"
        )

@tool
async def enumerate_capabilities(caller_identity_ref: str) -> str:
    """Walk the closed capability list the resolved caller identity held at execution time. Each capability is a verb.resource token; the list is closed (no implicit grants). This is the runtime-side assertion; the F-PT-01 platform card carries the orthogonal guarantee that the caller actually held the listed capabilities at boot, which is out of scope for this workflow.

    CACAO step_id : action--08aa0d10-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--08aa0d10-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--08aa0d10-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--08aa0d10-0000-4000-8000-000000000003', 'secops_ng.step.name': 'enumerate-capabilities', 'secops_ng.tool.name': 'enumerate_capabilities', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--08aa0d10-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--08aa0d10-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--08aa0d10-0000-4000-8000-000000000003', 'secops_ng.step.name': 'enumerate-capabilities', 'secops_ng.tool.name': 'enumerate_capabilities', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--08aa0d10-0000-4000-8000-000000000003'"
        )

@tool
async def emit_access_evidence(caller_identity_ref: str, capabilities_ref: str, execution_id: str) -> str:
    """Combine the caller-identity block and the capability list into one access-evidence artifact shaped against schemas/evidence/access.schema.json (stream: access). The artifact carries the workflow id, execution id, compile target, regulation_refs (nis2:art-21-2-i), control_refs, captured_at, and provenance. Emission is byte-stable: same execution inputs and same compile target re-derive the same artifact_id (SHA-256 of workflow_id|execution_id|compile_target). Destination is operator-configured — no default non-EU endpoint.

    CACAO step_id : action--08aa0d10-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--08aa0d10-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--08aa0d10-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--08aa0d10-0000-4000-8000-000000000004', 'secops_ng.step.name': 'emit-access-evidence', 'secops_ng.tool.name': 'emit_access_evidence', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--08aa0d10-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--08aa0d10-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--08aa0d10-0000-4000-8000-000000000004', 'secops_ng.step.name': 'emit-access-evidence', 'secops_ng.tool.name': 'emit_access_evidence', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--08aa0d10-0000-4000-8000-000000000004'"
        )

async def llm_step(state: PlaybookIamAuditorV1State) -> dict:
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

STATE_SCHEMA = PlaybookIamAuditorV1State
TOOLS = (enumerate_identities, enumerate_capabilities, emit_access_evidence,)
AGENTIC_HOOK = llm_step

