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
    # Identity provider subject of the suspected-compromised principal (user, service principal, or workload identity). The trigger input; the hydration adapter assembles __hydrated_signal__ and __principal_context__ for it.
    principal_id: str
    # playbook_variable: __signal_id__
    # Identifier of the originating identity-protection / sign-in signal (an Azure AD Identity Protection risk event, an Okta ThreatInsight event, or a SOC-raised ticket).
    signal_id: str
    # playbook_variable: __hydrated_signal__
    # The signal the hydration adapter assembled for __signal_id__: exactly signal_id, source, detected_at (Zulu), principal_id and detections (names from the triage vocabulary; an unknown name fails loud).
    hydrated_signal: dict[str, object]
    # playbook_variable: __principal_context__
    # What the IdP says about the principal: exactly principal_type (user, service principal or workload identity) and privileged (a real boolean). A privileged principal is contained on one uncleared detection.
    principal_context: dict[str, object]
    # playbook_variable: __benign_patterns__
    # The operator's benign patterns, each exactly principal_id, kind (planned_travel or sanctioned_automation), valid_from and valid_until (Zulu). They clear impossible travel and nothing else. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    benign_patterns: str
    # playbook_variable: __analyst_verdict__
    # An analyst ruling when one exists: confirmed or benign. It decides over the rule, and a disagreement is recorded as an override. Empty when no analyst has ruled (the n8n trigger supplies an empty string for an unset variable).
    analyst_verdict: str
    # playbook_variable: __registered_factors__
    # The MFA factors the IdP lists for the principal, each exactly factor_id and kind. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    registered_factors: str
    # playbook_variable: __requested_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the containment directives are requested at; the MFA and session steps stamp it.
    requested_at: str
    # playbook_variable: __live_sessions__
    # The live sessions, refresh tokens and device grants the tenant adapters returned, each exactly session_ref, tenant_ref and kind. A session in a tenant that was not enumerated fails loud. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    live_sessions: str
    # playbook_variable: __reachable_tenants__
    # The tenants the principal can reach. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    reachable_tenants: str
    # playbook_variable: __enumerated_tenants__
    # The tenants whose adapters returned a session inventory; the difference from __reachable_tenants__ is reported as the coverage gap. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    enumerated_tenants: str
    # playbook_variable: __hunt_findings__
    # What the hunt queries found, each exactly surface, resource_ref and observed_at (Zulu). A finding on a surface that was not hunted fails loud. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    hunt_findings: str
    # playbook_variable: __hunted_surfaces__
    # The hunt surfaces whose queries actually ran. CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    hunted_surfaces: str
    # playbook_variable: __lookback_hours__
    # The operator's hunt lookback window, in hours before detection, as a positive integer.
    lookback_hours: int
    # playbook_variable: __iam_items__
    # The principal's IAM surface, each exactly item_ref, kind, created_at (Zulu) and change_ref (the authorising change record, or null). CACAO v2 has no list type, so the value rides as a string carrying a JSON-native list; the compile target's adapter seam marshals it.
    iam_items: str
    # playbook_variable: __compromise_window_start__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the compromise window opens; it closes at detection. An adapter input, because triage sees detection names and the detection time but not when the compromise began; the sign-in history or forensic-timeline adapter that has it supplies it. A start after detection fails loud.
    compromise_window_start: str
    # playbook_variable: __compromise_confirmed__
    # Whether triage confirmed the compromise; false closes out as a false positive. Extracted at the compile target's adapter seam from __triage_record__.compromise_confirmed. A real boolean: the gate compares it to true, and the string 'false' is truthy in most runtimes.
    compromise_confirmed: bool
    # playbook_variable: __sessions_revoked_count__
    # Number of distinct live sessions, refresh tokens and device grants revoked across the enumerated tenants. Feeds the containment KPI. Extracted at the compile target's adapter seam from __session_revocation_directive__.sessions_revoked_count.
    sessions_revoked_count: int
    # playbook_variable: __lateral_findings_count__
    # Distinct downstream resources the principal touched inside the hunt window. Extracted at the compile target's adapter seam from __hunt_summary__.lateral_findings_count.
    lateral_findings_count: int
    # playbook_variable: __triage_record__
    # Envelope the triage step emits: the principal type and privilege, the detections and those a benign pattern cleared, compromise_confirmed as a real boolean with its basis, and overridden_by_analyst.
    triage_record: dict[str, object]
    # playbook_variable: __mfa_reset_directive__
    # Envelope the MFA step emits: the factors before and after, one action per factor, and the re-enrolment requirement; not applicable to principals that cannot hold factors.
    mfa_reset_directive: dict[str, object]
    # playbook_variable: __session_revocation_directive__
    # Envelope the session step emits: one revocation per distinct session, the counts by kind, and the tenants that could not be enumerated.
    session_revocation_directive: dict[str, object]
    # playbook_variable: __hunt_summary__
    # Envelope the hunt step emits: the window, the touched resources and their surfaces, findings outside the window, and hunt coverage as hunted and unhunted surfaces.
    hunt_summary: dict[str, object]
    # playbook_variable: __persistence_removal_plan__
    # Envelope the persistence step emits: each IAM item removed or kept, with the reason it was kept.
    persistence_removal_plan: dict[str, object]
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
async def triage_identity_signal(signal_id: str, principal_id: str, hydrated_signal: dict[str, object], principal_context: dict[str, object], benign_patterns: str, analyst_verdict: str) -> dict[str, object]:
    """Decide whether the hydrated identity signal confirms a compromise, by an explicit rule: a decisive detection (MFA bypass, MFA disabled, AssumeRole misuse), two corroborating detections, or any detection on a privileged principal. Benign patterns (planned travel, sanctioned automation) clear impossible travel and nothing else. An analyst verdict decides when present, and a disagreement is recorded as an override. Produces __triage_record__, from which __compromise_confirmed__ is extracted.

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
        from content.playbooks.identity_compromise.primitives.triage import triage_identity_signal
        __triage_record__ = triage_identity_signal(signal=__hydrated_signal__, principal_context=__principal_context__, benign_patterns=__benign_patterns__, analyst_verdict=__analyst_verdict__)

@tool
async def reset_mfa_factors(triage_record: dict[str, object], registered_factors: str, requested_at: str) -> dict[str, object]:
    """Compose the factor reset for the principal: revoke every registered factor, invalidate app passwords, and require re-enrolment with step-up at the next sign-in, recording the factor list before and after. A service principal or workload identity holds no factors, so the reset is recorded as not applicable. Produces __mfa_reset_directive__.

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
        from content.playbooks.identity_compromise.primitives.mfa import compose_mfa_reset
        __mfa_reset_directive__ = compose_mfa_reset(triage=__triage_record__, registered_factors=__registered_factors__, requested_at=__requested_at__)

@tool
async def revoke_active_sessions(triage_record: dict[str, object], live_sessions: str, reachable_tenants: str, enumerated_tenants: str, requested_at: str) -> dict[str, object]:
    """Compose the revocation of every live session, refresh token and persistent device grant the principal holds across the enumerated tenants, and report the reachable tenants that could not be enumerated as a coverage gap. Produces __session_revocation_directive__, from which __sessions_revoked_count__ is extracted for the containment KPI.

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
        from content.playbooks.identity_compromise.primitives.sessions import compose_session_revocation
        __session_revocation_directive__ = compose_session_revocation(triage=__triage_record__, live_sessions=__live_sessions__, reachable_tenants=__reachable_tenants__, enumerated_tenants=__enumerated_tenants__, requested_at=__requested_at__)

@tool
async def lateral_movement_hunt(triage_record: dict[str, object], hunt_findings: str, hunted_surfaces: str, lookback_hours: int) -> dict[str, object]:
    """Summarise the downstream activity attributable to the principal inside the lookback window (STS / AssumeRole chains, cross-tenant access, API-token reuse, OAuth-grant escalation, host logons): the distinct resources touched, findings outside the window, and how much of the hunt surface was actually queried. Produces __hunt_summary__, from which __lateral_findings_count__ is extracted.

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
        from content.playbooks.identity_compromise.primitives.hunt import summarise_lateral_hunt
        __hunt_summary__ = summarise_lateral_hunt(triage=__triage_record__, hunt_findings=__hunt_findings__, hunted_surfaces=__hunted_surfaces__, lookback_hours=__lookback_hours__)

@tool
async def iam_audit_and_persistence_removal(triage_record: dict[str, object], iam_items: str, compromise_window_start: str) -> dict[str, object]:
    """Audit the principal's IAM surface (OAuth consents, third-party app grants, conditional-access exceptions, inbox rules, device registrations, role assignments) and plan the removal of every item created inside the compromise window without an authorising change record; items that predate the window or carry a change record are kept, with the reason. Produces __persistence_removal_plan__.

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
        from content.playbooks.identity_compromise.primitives.persistence import plan_persistence_removal
        __persistence_removal_plan__ = plan_persistence_removal(triage=__triage_record__, iam_items=__iam_items__, compromise_window_start=__compromise_window_start__)

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

