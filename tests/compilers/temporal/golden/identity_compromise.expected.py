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


@activity.defn
async def triage_identity_signal(signal_id: str, principal_id: str) -> bool:
    """Hydrate the originating identity-protection signal with principal context (role, group memberships, recent sign-ins, conditional-access posture). Decide whether the signal warrants containment or is a known benign pattern (planned travel, sanctioned automation).

    CACAO step_id: action--30000000-0000-4000-8000-000000000002
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--30000000-0000-4000-8000-000000000002'"
    )

TRIAGE_IDENTITY_SIGNAL_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def reset_mfa_factors(principal_id: str) -> None:
    """Force re-enrollment of MFA factors for the principal: revoke existing TOTP / WebAuthn registrations, invalidate app passwords, and require step-up at next sign-in. Document factor list pre / post reset.

    CACAO step_id: action--30000000-0000-4000-8000-000000000004
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--30000000-0000-4000-8000-000000000004'"
    )

RESET_MFA_FACTORS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def revoke_active_sessions(principal_id: str) -> int:
    """Revoke all live sessions, refresh tokens, and persistent device grants for the principal across the IdP and downstream SaaS tenants. Produces __sessions_revoked_count__ for the containment KPI.

    CACAO step_id: action--30000000-0000-4000-8000-000000000005
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--30000000-0000-4000-8000-000000000005'"
    )

REVOKE_ACTIVE_SESSIONS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def lateral_movement_hunt(principal_id: str) -> int:
    """Hunt for downstream activity attributable to the compromised principal within the configured lookback window: STS / AssumeRole chains, cross-tenant access, API-token reuse, OAuth-grant escalation, host logons. Produces __lateral_findings_count__.

    CACAO step_id: action--30000000-0000-4000-8000-000000000006
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--30000000-0000-4000-8000-000000000006'"
    )

LATERAL_MOVEMENT_HUNT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def iam_audit_and_persistence_removal(principal_id: str) -> None:
    """Audit the principal's IAM surface for residual persistence: rogue OAuth consents, third-party app grants, conditional-access exceptions, inbox rules, new device registrations, and standing-privilege role assignments. Remove anything the principal could not authorise legitimately during the compromise window.

    CACAO step_id: action--30000000-0000-4000-8000-000000000007
    """
    raise NotImplementedError(
        f"CACAO action stub not implemented: step_id='action--30000000-0000-4000-8000-000000000007'"
    )

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
    content_version   : 0.1.0
    maturity          : draft
    workflow_start    : start--30000000-0000-4000-8000-000000000001
    activities        : triage_identity_signal, reset_mfa_factors, revoke_active_sessions, lateral_movement_hunt, iam_audit_and_persistence_removal
    """

    @workflow.run
    async def run(self) -> None:
        raise NotImplementedError(
            f"CACAO workflow lowering not implemented: stable_id='playbook.identity_compromise@v1'"
        )

WORKFLOW = PlaybookIdentityCompromiseV1Workflow
ACTIVITIES = (triage_identity_signal, reset_mfa_factors, revoke_active_sessions, lateral_movement_hunt, iam_audit_and_persistence_removal,)
RETRY_POLICIES = (TRIAGE_IDENTITY_SIGNAL_RETRY_POLICY, RESET_MFA_FACTORS_RETRY_POLICY, REVOKE_ACTIVE_SESSIONS_RETRY_POLICY, LATERAL_MOVEMENT_HUNT_RETRY_POLICY, IAM_AUDIT_AND_PERSISTENCE_REMOVAL_RETRY_POLICY,)
