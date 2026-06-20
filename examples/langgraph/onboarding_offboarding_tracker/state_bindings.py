# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.onboarding_offboarding_tracker@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookOnboardingOffboardingTrackerV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.onboarding_offboarding_tracker@v1.

    Playbook id: playbook--20212021-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __execution_id__
    # Per-execution identifier issued by the compile target's workflow runtime (n8n execution id, Temporal workflow run id, LangGraph thread/checkpoint id). Pinned by the upstream runtime; the workflow reads it for the access-evidence artifact join.
    execution_id: str
    # playbook_variable: __lifecycle_event_ref__
    # Pointer to the operator's lifecycle-event record under processing on this execution. Operator-configured; the workflow reads it as an opaque pointer to a joiner / mover / leaver event held in the operator's identity source (a sovereign EU directory, an on-prem IdP, a Git-managed role-and-capability repository). The framework ships no default hosted IdP / HR-SaaS dependency, no default non-EU endpoint, and no vendor SDK bundling — the operator supplies whatever identity source is in scope.
    lifecycle_event_ref: str
    # playbook_variable: __lifecycle_event_record_ref__
    # Pointer to the ingested lifecycle-event record produced by ingest-lifecycle-event. Closed shape per CORE sibling card; event-kind (joiner | mover | leaver) keyed, principal-handle + declared capability-delta envelope valued. Consumed by resolve-identity.
    lifecycle_event_record_ref: str
    # playbook_variable: __resolved_identity_ref__
    # Pointer to the resolved caller-identity block produced by resolve-identity — role-shaped principal handle (service-account name, workflow-runtime principal id, automation role) per the F-CP-07 public-bar discipline. Personal-user principals are rejected at the primitive boundary.
    resolved_identity_ref: str
    # playbook_variable: __capability_delta_ref__
    # Pointer to the applied capability-delta record produced by apply-capability-delta — the closed `verb.resource` add-set and remove-set the workflow asked the operator's identity source to materialise against the resolved principal. Consumed by confirm-grant-revoke.
    capability_delta_ref: str
    # playbook_variable: __confirmation_ref__
    # Pointer to the grant/revoke confirmation record produced by confirm-grant-revoke — the closed capability list the resolved principal carries after the delta was applied, read back from the same operator-supplied identity source. The confirmation closes the loop between declared intent (capability_delta) and observed effect (closed capability list).
    confirmation_ref: str
    # playbook_variable: __access_artifact_ref__
    # Pointer to the access-evidence artifact emitted by emit-access-evidence, shaped against schemas/evidence/access.schema.json. Reuses the F-CP-07 access stream — the artifact carries the resolved role-shaped caller identity and the closed capability list the principal holds at the end of this lifecycle execution.
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
async def ingest_lifecycle_event(execution_id: str, lifecycle_event_ref: str) -> str:
    """Read the lifecycle-event record referenced by __lifecycle_event_ref__ from the operator-supplied identity source and bind it to a normalised in-workflow event record (event_kind in {joiner, mover, leaver}, principal_handle, declared_capability_delta, effective_at). Read-only by contract; the workflow MUST NOT mutate the source event on this step. Identity-source endpoint is operator-configured — the framework ships no default hosted IdP, no HR-SaaS dependency, and no non-EU default endpoint.

    CACAO step_id : action--20212021-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--20212021-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--20212021-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest-lifecycle-event', 'secops_ng.tool.name': 'ingest_lifecycle_event', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--20212021-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--20212021-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest-lifecycle-event', 'secops_ng.tool.name': 'ingest_lifecycle_event', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--20212021-0000-4000-8000-000000000002'"
        )

@tool
async def resolve_identity(lifecycle_event_record_ref: str) -> str:
    """Resolve the principal_handle carried by the ingested lifecycle event against the operator's identity source and bind it to a role-shaped caller-identity block (principal_type in {service_account, workflow_runtime, automation_role}, principal_id, identity_provider). The principal is role-shaped by contract — never an individual personal name or a credential-shaped string. Personal-user principals are rejected at the primitive boundary; the F-WF-08 IAM auditor enforces the same shape on the read side.

    CACAO step_id : action--20212021-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--20212021-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--20212021-0000-4000-8000-000000000003', 'secops_ng.step.name': 'resolve-identity', 'secops_ng.tool.name': 'resolve_identity', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--20212021-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--20212021-0000-4000-8000-000000000003', 'secops_ng.step.name': 'resolve-identity', 'secops_ng.tool.name': 'resolve_identity', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--20212021-0000-4000-8000-000000000003'"
        )

@tool
async def apply_capability_delta(lifecycle_event_record_ref: str, resolved_identity_ref: str) -> str:
    """Apply the declared capability delta from the ingested lifecycle event against the resolved principal — grant the add-set on a joiner event, adjust both add-set and remove-set on a mover event, drain the remove-set on a leaver event. Capabilities are verb.resource tokens; the delta is closed (no implicit grants, no implicit revocations beyond what the event declares). Deterministic on the same event record + same resolved principal — re-runs collapse to byte-identical bytes at the delta layer. The actual mutation on the operator's identity source is delegated to the CORE primitive bound in the CORE-FANOUT sibling card; at SKELETON the step pins the contract only.

    CACAO step_id : action--20212021-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--20212021-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--20212021-0000-4000-8000-000000000004', 'secops_ng.step.name': 'apply-capability-delta', 'secops_ng.tool.name': 'apply_capability_delta', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--20212021-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--20212021-0000-4000-8000-000000000004', 'secops_ng.step.name': 'apply-capability-delta', 'secops_ng.tool.name': 'apply_capability_delta', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--20212021-0000-4000-8000-000000000004'"
        )

@tool
async def confirm_grant_revoke(resolved_identity_ref: str, capability_delta_ref: str) -> str:
    """Re-read the resolved principal's closed capability list from the same operator-supplied identity source and confirm that the declared capability delta landed — the add-set is present, the remove-set is gone. The confirmation closes the loop between intent (capability_delta) and observed effect (closed capability list); divergence between declared and observed surfaces as a confirmation-failure on the emitted access-evidence artifact and on the joiner-mover-leaver evidence the F-WF-08 IAM auditor anchors against the F-CP-07 access stream. Read-only on this step.

    CACAO step_id : action--20212021-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--20212021-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--20212021-0000-4000-8000-000000000005', 'secops_ng.step.name': 'confirm-grant-revoke', 'secops_ng.tool.name': 'confirm_grant_revoke', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--20212021-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--20212021-0000-4000-8000-000000000005', 'secops_ng.step.name': 'confirm-grant-revoke', 'secops_ng.tool.name': 'confirm_grant_revoke', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--20212021-0000-4000-8000-000000000005'"
        )

@tool
async def emit_access_evidence(execution_id: str, resolved_identity_ref: str, confirmation_ref: str) -> str:
    """Combine the resolved caller-identity block and the confirmed closed capability list into one access-evidence artifact shaped against schemas/evidence/access.schema.json (stream: access). The artifact carries the workflow id (onboarding_offboarding_tracker), execution id, compile target, regulation_refs (nis2:art-21-2-i), control_refs, captured_at, and provenance. Reuses the F-CP-07 access stream that F-WF-08 IAM auditor already binds onto — joiner-mover-leaver execution evidence is one access artifact per lifecycle event, runtime-side capability inventory is one access artifact per workflow execution, both feed the same NIS2 Article 21(2)(i) clause anchor. Destination is operator-configured — no default non-EU endpoint.

    CACAO step_id : action--20212021-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--20212021-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--20212021-0000-4000-8000-000000000006', 'secops_ng.step.name': 'emit-access-evidence', 'secops_ng.tool.name': 'emit_access_evidence', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--20212021-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--20212021-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--20212021-0000-4000-8000-000000000006', 'secops_ng.step.name': 'emit-access-evidence', 'secops_ng.tool.name': 'emit_access_evidence', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--20212021-0000-4000-8000-000000000006'"
        )

async def llm_step(state: PlaybookOnboardingOffboardingTrackerV1State) -> dict:
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

STATE_SCHEMA = PlaybookOnboardingOffboardingTrackerV1State
TOOLS = (ingest_lifecycle_event, resolve_identity, apply_capability_delta, confirm_grant_revoke, emit_access_evidence,)
AGENTIC_HOOK = llm_step

