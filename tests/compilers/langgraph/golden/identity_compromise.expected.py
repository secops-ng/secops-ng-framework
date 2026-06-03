# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.identity_compromise@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookIdentityCompromiseV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.identity_compromise@v1.

    Playbook id: playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __principal_id__
    # Identity provider subject of the suspected-compromised principal (user, service principal, or workload identity).
    principal_id: str
    # playbook_variable: __signal_id__
    # Identifier of the originating identity-protection / sign-in signal (e.g. Azure AD Identity Protection risk event, Okta ThreatInsight finding).
    signal_id: str
    # playbook_variable: __compromise_confirmed__
    # Set by initial triage. False signals branch to a false-positive close-out path; true signals proceed to containment.
    compromise_confirmed: bool
    # playbook_variable: __sessions_revoked_count__
    # Number of active sessions revoked across IdP / SaaS tenants for the principal. Feeds the containment KPI.
    sessions_revoked_count: int
    # playbook_variable: __lateral_findings_count__
    # Distinct downstream resources or principals the compromised identity touched within the hunt window.
    lateral_findings_count: int
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
async def triage_identity_signal(signal_id: str, principal_id: str) -> bool:
    """Hydrate the originating identity-protection signal with principal context (role, group memberships, recent sign-ins, conditional-access posture). Decide whether the signal warrants containment or is a known benign pattern (planned travel, sanctioned automation).

    CACAO step_id : action--30000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'triage identity signal', 'secops_ng.tool.name': 'triage_identity_signal', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'triage identity signal', 'secops_ng.tool.name': 'triage_identity_signal', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000002'"
        )

@tool
async def reset_mfa_factors(principal_id: str) -> None:
    """Force re-enrollment of MFA factors for the principal: revoke existing TOTP / WebAuthn registrations, invalidate app passwords, and require step-up at next sign-in. Document factor list pre / post reset.

    CACAO step_id : action--30000000-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'reset MFA factors', 'secops_ng.tool.name': 'reset_mfa_factors', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'reset MFA factors', 'secops_ng.tool.name': 'reset_mfa_factors', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000004'"
        )

@tool
async def revoke_active_sessions(principal_id: str) -> int:
    """Revoke all live sessions, refresh tokens, and persistent device grants for the principal across the IdP and downstream SaaS tenants. Produces __sessions_revoked_count__ for the containment KPI.

    CACAO step_id : action--30000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'revoke active sessions', 'secops_ng.tool.name': 'revoke_active_sessions', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'revoke active sessions', 'secops_ng.tool.name': 'revoke_active_sessions', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000005'"
        )

@tool
async def lateral_movement_hunt(principal_id: str) -> int:
    """Hunt for downstream activity attributable to the compromised principal within the configured lookback window: STS / AssumeRole chains, cross-tenant access, API-token reuse, OAuth-grant escalation, host logons. Produces __lateral_findings_count__.

    CACAO step_id : action--30000000-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'lateral-movement hunt', 'secops_ng.tool.name': 'lateral_movement_hunt', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'lateral-movement hunt', 'secops_ng.tool.name': 'lateral_movement_hunt', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000006'"
        )

@tool
async def iam_audit_and_persistence_removal(principal_id: str) -> None:
    """Audit the principal's IAM surface for residual persistence: rogue OAuth consents, third-party app grants, conditional-access exceptions, inbox rules, new device registrations, and standing-privilege role assignments. Remove anything the principal could not authorise legitimately during the compromise window.

    CACAO step_id : action--30000000-0000-4000-8000-000000000007
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--30000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'IAM audit and persistence removal', 'secops_ng.tool.name': 'iam_audit_and_persistence_removal', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--30000000-0000-4000-8000-000000000007', attributes={'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'IAM audit and persistence removal', 'secops_ng.tool.name': 'iam_audit_and_persistence_removal', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--30000000-0000-4000-8000-000000000007'"
        )

async def llm_step(state: PlaybookIdentityCompromiseV1State) -> dict:
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

STATE_SCHEMA = PlaybookIdentityCompromiseV1State
TOOLS = (triage_identity_signal, reset_mfa_factors, revoke_active_sessions, lateral_movement_hunt, iam_audit_and_persistence_removal,)
AGENTIC_HOOK = llm_step
