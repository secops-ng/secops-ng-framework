# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.temporal <playbook.cacao.json>`.
#
# This file is a stub. Workflow control flow and activity bodies are
# intentionally NotImplementedError until a human integrator wires them
# to the operator's runtime.
"""Generated Temporal stub. See module-level metadata in the workflow docstring."""
from __future__ import annotations

from datetime import timedelta

from temporalio import activity, workflow
from temporalio.common import RetryPolicy

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

@activity.defn
async def triage_identity_signal(signal_id: str, principal_id: str, hydrated_signal: dict[str, object], principal_context: dict[str, object], benign_patterns: str, analyst_verdict: str) -> dict[str, object]:
    """Decide whether the hydrated identity signal confirms a compromise, by an explicit rule: a decisive detection (MFA bypass, MFA disabled, AssumeRole misuse), two corroborating detections, or any detection on a privileged principal. Benign patterns (planned travel, sanctioned automation) clear impossible travel and nothing else. An analyst verdict decides when present, and a disagreement is recorded as an override. Produces __triage_record__, from which __compromise_confirmed__ is extracted.

    CACAO step_id: action--30000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'triage identity signal', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'triage_identity_signal'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'triage identity signal', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'triage_identity_signal'})
        )
        from content.playbooks.identity_compromise.primitives.triage import triage_identity_signal
        __triage_record__ = triage_identity_signal(signal=__hydrated_signal__, principal_context=__principal_context__, benign_patterns=__benign_patterns__, analyst_verdict=__analyst_verdict__)

TRIAGE_IDENTITY_SIGNAL_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def reset_mfa_factors(triage_record: dict[str, object], registered_factors: str, requested_at: str) -> dict[str, object]:
    """Compose the factor reset for the principal: revoke every registered factor, invalidate app passwords, and require re-enrolment with step-up at the next sign-in, recording the factor list before and after. A service principal or workload identity holds no factors, so the reset is recorded as not applicable. Produces __mfa_reset_directive__.

    CACAO step_id: action--30000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'reset MFA factors', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'reset_mfa_factors'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'reset MFA factors', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'reset_mfa_factors'})
        )
        from content.playbooks.identity_compromise.primitives.mfa import compose_mfa_reset
        __mfa_reset_directive__ = compose_mfa_reset(triage=__triage_record__, registered_factors=__registered_factors__, requested_at=__requested_at__)

RESET_MFA_FACTORS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def revoke_active_sessions(triage_record: dict[str, object], live_sessions: str, reachable_tenants: str, enumerated_tenants: str, requested_at: str) -> dict[str, object]:
    """Compose the revocation of every live session, refresh token and persistent device grant the principal holds across the enumerated tenants, and report the reachable tenants that could not be enumerated as a coverage gap. Produces __session_revocation_directive__, from which __sessions_revoked_count__ is extracted for the containment KPI.

    CACAO step_id: action--30000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'revoke active sessions', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'revoke_active_sessions'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'revoke active sessions', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'revoke_active_sessions'})
        )
        from content.playbooks.identity_compromise.primitives.sessions import compose_session_revocation
        __session_revocation_directive__ = compose_session_revocation(triage=__triage_record__, live_sessions=__live_sessions__, reachable_tenants=__reachable_tenants__, enumerated_tenants=__enumerated_tenants__, requested_at=__requested_at__)

REVOKE_ACTIVE_SESSIONS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def lateral_movement_hunt(triage_record: dict[str, object], hunt_findings: str, hunted_surfaces: str, lookback_hours: int) -> dict[str, object]:
    """Summarise the downstream activity attributable to the principal inside the lookback window (STS / AssumeRole chains, cross-tenant access, API-token reuse, OAuth-grant escalation, host logons): the distinct resources touched, findings outside the window, and how much of the hunt surface was actually queried. Produces __hunt_summary__, from which __lateral_findings_count__ is extracted.

    CACAO step_id: action--30000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'lateral-movement hunt', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'lateral_movement_hunt'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'lateral-movement hunt', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'lateral_movement_hunt'})
        )
        from content.playbooks.identity_compromise.primitives.hunt import summarise_lateral_hunt
        __hunt_summary__ = summarise_lateral_hunt(triage=__triage_record__, hunt_findings=__hunt_findings__, hunted_surfaces=__hunted_surfaces__, lookback_hours=__lookback_hours__)

LATERAL_MOVEMENT_HUNT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def iam_audit_and_persistence_removal(triage_record: dict[str, object], iam_items: str, compromise_window_start: str) -> dict[str, object]:
    """Audit the principal's IAM surface (OAuth consents, third-party app grants, conditional-access exceptions, inbox rules, device registrations, role assignments) and plan the removal of every item created inside the compromise window without an authorising change record; items that predate the window or carry a change record are kept, with the reason. Produces __persistence_removal_plan__.

    CACAO step_id: action--30000000-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'IAM audit and persistence removal', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'iam_audit_and_persistence_removal'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'IAM audit and persistence removal', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'iam_audit_and_persistence_removal'})
        )
        from content.playbooks.identity_compromise.primitives.persistence import plan_persistence_removal
        __persistence_removal_plan__ = plan_persistence_removal(triage=__triage_record__, iam_items=__iam_items__, compromise_window_start=__compromise_window_start__)

IAM_AUDIT_AND_PERSISTENCE_REMOVAL_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookIdentityCompromiseV1Workflow:
    """Respond to a detected account compromise (credential theft, MFA bypass, anomalous sign-in, suspicious OAuth grant, or impossible-travel signal). The playbook drives the operator through MFA reset, session revocation across IdP / SaaS, a lateral-movement hunt scoped to the compromised principal's blast radius, and a final IAM audit to remove residual persistence (rogue OAuth grants, app passwords, conditional-access exceptions). CACAO v2 + SecOps-NG content-model extensions; Sigma rule IDs are referenced under external_references — detection authoring stays upstream at SigmaHQ.

    CACAO playbook id : playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701
    stable_id         : playbook.identity_compromise@v1
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--30000000-0000-4000-8000-000000000001
    activities        : triage_identity_signal, reset_mfa_factors, revoke_active_sessions, lateral_movement_hunt, iam_audit_and_persistence_removal
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.identity_compromise@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.identity_compromise@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a701', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.identity_compromise@v1'"
            )

WORKFLOW = PlaybookIdentityCompromiseV1Workflow
ACTIVITIES = (triage_identity_signal, reset_mfa_factors, revoke_active_sessions, lateral_movement_hunt, iam_audit_and_persistence_removal,)
RETRY_POLICIES = (TRIAGE_IDENTITY_SIGNAL_RETRY_POLICY, RESET_MFA_FACTORS_RETRY_POLICY, REVOKE_ACTIVE_SESSIONS_RETRY_POLICY, LATERAL_MOVEMENT_HUNT_RETRY_POLICY, IAM_AUDIT_AND_PERSISTENCE_REMOVAL_RETRY_POLICY,)
