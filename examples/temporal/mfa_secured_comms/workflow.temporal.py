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
async def probe_mfa_coverage(posture_window: str, auth_scope: str) -> str:
    """Probe the identity providers enumerated in __auth_scope__ for MFA enrolment and enforcement state across every in-scope principal class. Emits __mfa_coverage_id__ as a per-principal record of (principal id, principal class, MFA factor types enrolled, enforcement state, last successful MFA event). The probe is read-only against the identity-provider surface; it does not enrol factors or alter policy. Principals with no declared MFA requirement in the operator's policy are reported as policy gaps rather than enforcement gaps; the distinction is preserved so the attestation surfaces the policy-side and operations-side gaps separately.

    CACAO step_id: action--52000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'probe mfa coverage', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'probe_mfa_coverage'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'probe mfa coverage', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'probe_mfa_coverage'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--52000000-0000-4000-8000-000000000002'"
        )

PROBE_MFA_COVERAGE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def assess_continuous_auth(auth_scope: str, mfa_coverage_id: str) -> str:
    """Walk the session surfaces enumerated in __auth_scope__ and assess whether continuous-authentication signals (re-authentication on privilege escalation, session re-binding on context change, periodic step-up) are observed on long-lived sessions against the declared cadence. Emits __continuous_auth_id__ as a per-session record of (session id, principal id, session age, last re-auth event, declared cadence, overdue-by-minutes). Sessions in scopes with no declared continuous-authentication cadence are reported as policy gaps rather than overdue re-authentications. The assessment is read-only; it does NOT invalidate sessions or force step-up.

    CACAO step_id: action--52000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'assess continuous auth', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assess_continuous_auth'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'assess continuous auth', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assess_continuous_auth'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--52000000-0000-4000-8000-000000000003'"
        )

ASSESS_CONTINUOUS_AUTH_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def verify_oob_channels(auth_scope: str, posture_window: str) -> str:
    """Test the out-of-band emergency communications channels enumerated in __auth_scope__ (voice, secure messaging, paging) for reachability and independence from the primary information-system path. Emits __oob_channel_status__ as a per-channel record of (channel id, channel class, last successful test, independence-path verification, owner). The verification is a documented test transaction against each channel; it does not deliver a real emergency notification. Channels with no declared independence path are reported as policy gaps rather than reachability failures.

    CACAO step_id: action--52000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'verify oob channels', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'verify_oob_channels'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'verify oob channels', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'verify_oob_channels'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--52000000-0000-4000-8000-000000000004'"
        )

VERIFY_OOB_CHANNELS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def evidence_capture(mfa_coverage_id: str, continuous_auth_id: str, oob_channel_status: str, posture_window: str) -> str:
    """Compose and publish the dated authentication and secured-communications posture attestation to the operator's evidence store. The record carries the MFA-coverage snapshot, the continuous-authentication assessment, the OOB-channel verification, the posture window, and a top-level gap summary (missing-MFA, stale-session, unreachable-OOB counts). This is the audit-evident artifact that NIS2 Art.21(2)(j) reviewers read; missing or stale attestations are the failure mode the metrics surface. The attestation is always emitted, including the policy-gap branch (which records missing-policy conditions rather than skipping the attestation).

    CACAO step_id: action--52000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'evidence capture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evidence_capture'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'evidence capture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evidence_capture'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--52000000-0000-4000-8000-000000000005'"
        )

EVIDENCE_CAPTURE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_authentication_owner(attestation_id: str, auth_scope: str) -> None:
    """Deliver the attestation reference to the authentication owner along the operator's pre-bound channel (ticketing system, chat thread, email). Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently; an attestation written but never delivered to the owner is itself a posture gap.

    CACAO step_id: action--52000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify authentication owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_authentication_owner'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify authentication owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_authentication_owner'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--52000000-0000-4000-8000-000000000006'"
        )

NOTIFY_AUTHENTICATION_OWNER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookMfaSecuredCommsV1Workflow:
    """Operate the multi-factor / continuous-authentication and secured-communications posture surface required by NIS2 Art.21(2)(j): probe the identity-provider surface to confirm MFA coverage across in-scope principals, assess whether continuous-authentication signals are observed on long-lived sessions, verify the out-of-band emergency communications channel is reachable independently of the primary information-system path, capture a dated posture-attestation artifact, and notify the authentication owner. The playbook is the operationalisation of declared authentication and secured-communications policy; it does not author the policy itself. SKELETON only — control bindings (control.mfa_state_probe@v1, control.oob_channel_probe@v1) are pinned but detection bindings (missing-MFA, stale-session, unreachable-OOB upstream rule ids), golden tests, and per-target compiler emissions are owned by CORE / EXTEND siblings. The metric_refs pin the catalogue entry kri.mfa_coverage_gaps@v1 that already ships under content/mappings/nis2/article-21-2-j.yaml; the CORE/EXTEND siblings add session-staleness and OOB-reachability KPI catalogue entries and re-pin step-level refs against them. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8
    stable_id         : playbook.mfa_secured_comms@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--52000000-0000-4000-8000-000000000001
    activities        : probe_mfa_coverage, assess_continuous_auth, verify_oob_channels, evidence_capture, notify_authentication_owner
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.mfa_secured_comms@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.mfa_secured_comms@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.mfa_secured_comms@v1'"
            )

WORKFLOW = PlaybookMfaSecuredCommsV1Workflow
ACTIVITIES = (probe_mfa_coverage, assess_continuous_auth, verify_oob_channels, evidence_capture, notify_authentication_owner,)
RETRY_POLICIES = (PROBE_MFA_COVERAGE_RETRY_POLICY, ASSESS_CONTINUOUS_AUTH_RETRY_POLICY, VERIFY_OOB_CHANNELS_RETRY_POLICY, EVIDENCE_CAPTURE_RETRY_POLICY, NOTIFY_AUTHENTICATION_OWNER_RETRY_POLICY,)
