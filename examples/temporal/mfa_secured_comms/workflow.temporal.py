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
async def probe_mfa_coverage(auth_scope: str, posture_window: str, principals: str) -> str:
    """Probe the identity providers enumerated in __auth_scope__ for MFA enrolment and enforcement state across every in-scope principal class. Binds against content.playbooks.mfa_secured_comms.primitives.probe.probe_mfa_coverage: canonicalises and validates the caller-supplied observation set under a closed factor-type vocabulary and a closed enforcement-state enumeration, sorts by principal_id, and emits the deterministic coverage_counts tally. Read-only against the identity-provider surface — no enrolment, no factor reset, no policy mutation. Principals with no declared MFA requirement in the operator's policy are reported as policy gaps rather than enforcement gaps; the distinction is preserved so the attestation surfaces the policy-side and operations-side gaps separately.

    CACAO step_id: action--52000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'probe mfa coverage', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'probe_mfa_coverage'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'probe mfa coverage', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'probe_mfa_coverage'})
        )
        from content.playbooks.mfa_secured_comms.primitives.probe import probe_mfa_coverage
        __mfa_coverage_id__ = probe_mfa_coverage(auth_scope=__auth_scope__, posture_window=__posture_window__, principals=__principals__)

PROBE_MFA_COVERAGE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def assess_continuous_auth(auth_scope: str, sessions: str) -> str:
    """Walk the session surfaces enumerated in __auth_scope__ and assess whether continuous-authentication signals (re-authentication on privilege escalation, session re-binding on context change, periodic step-up) are observed on long-lived sessions against the declared cadence. Binds against content.playbooks.mfa_secured_comms.primitives.assess.assess_continuous_auth: scores per-session staleness (fresh, overdue by minutes, or policy_gap when no cadence is declared) and emits the deterministic verdict_counts tally. Read-only-by-contract — no session is invalidated and no step-up is forced.

    CACAO step_id: action--52000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'assess continuous auth', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assess_continuous_auth'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'assess continuous auth', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assess_continuous_auth'})
        )
        from content.playbooks.mfa_secured_comms.primitives.assess import assess_continuous_auth
        __continuous_auth_id__ = assess_continuous_auth(auth_scope=__auth_scope__, sessions=__sessions__)

ASSESS_CONTINUOUS_AUTH_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def verify_oob_channels(auth_scope: str, posture_window: str, channels: str) -> str:
    """Test the out-of-band emergency communications channels enumerated in __auth_scope__ (voice, secure messaging, paging) for reachability and independence from the primary information-system path. Binds against content.playbooks.mfa_secured_comms.primitives.verify.verify_oob_channel: derives a per-channel status (ready, unreachable, independence_failure, policy_gap) from the reachability + independence-path booleans and emits the deterministic status_counts tally. The verification models a documented test transaction against each channel; no real emergency notification is delivered.

    CACAO step_id: action--52000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'verify oob channels', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'verify_oob_channels'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'verify oob channels', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'verify_oob_channels'})
        )
        from content.playbooks.mfa_secured_comms.primitives.verify import verify_oob_channel
        __oob_channel_status__ = verify_oob_channel(auth_scope=__auth_scope__, posture_window=__posture_window__, channels=__channels__)

VERIFY_OOB_CHANNELS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def evidence_capture(workflow_id: str, execution_id: str, regulation_refs: str, control_refs: str, auth_scope: str, posture_window: str, mfa_coverage_id: str, continuous_auth_id: str, oob_channel_status: str, captured_at: str, source_url: str) -> str:
    """Compose and publish the dated authentication and secured-communications posture attestation to the operator's evidence store. Binds against content.playbooks.mfa_secured_comms.primitives.artifact.build_mfa_posture_attestation_artifact: assembles the MFA-coverage snapshot, the continuous-authentication assessment, the OOB-channel verification, the posture window, and the aggregate gap_summary (missing-MFA, stale-session, unreachable-OOB counts) into the JSON-native attestation record. The deterministic artifact_id derives from SHA-256(workflow_id|execution_id|captured_at) so the three reference compilers re-derive byte-identical bytes (byte-parity contract). This is the audit-evident artifact NIS2 Art.21(2)(j) reviewers read; missing or stale attestations are the failure mode the metrics surface. The attestation is always emitted, including the policy-gap branch.

    CACAO step_id: action--52000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'evidence capture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evidence_capture'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'evidence capture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evidence_capture'})
        )
        from content.playbooks.mfa_secured_comms.primitives.artifact import build_mfa_posture_attestation_artifact
        __attestation_id__ = build_mfa_posture_attestation_artifact(workflow_id=__workflow_id__, execution_id=__execution_id__, regulation_refs=__regulation_refs__, control_refs=__control_refs__, auth_scope=__auth_scope__, posture_window=__posture_window__, mfa_coverage_snapshot=__mfa_coverage_id__, continuous_auth_assessment=__continuous_auth_id__, oob_channel_status=__oob_channel_status__, captured_at=__captured_at__, source_url=__source_url__)

EVIDENCE_CAPTURE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_authentication_owner(attestation_id: str, auth_scope: str) -> dict[str, object]:
    """Deliver the attestation reference to the authentication owner along the operator's pre-bound channel (ticketing system, chat thread, email). Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently; an attestation written but never delivered to the owner is itself a posture gap. The deterministic half is bound since the #937 wire card: compose_owner_notification builds the closed payload (role-shaped recipient, attestation ref, idempotency key) the messaging surface delivers verbatim — delivery itself remains a discipline of the compile target's messaging surface, mirroring the incident_management destination-resolver split.

    CACAO step_id: action--52000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify authentication owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_authentication_owner'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify authentication owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_authentication_owner'})
        )
        from content.playbooks.mfa_secured_comms.primitives.notify import compose_owner_notification
        __owner_notification__ = compose_owner_notification(attestation_id=__attestation_id__, auth_scope=__auth_scope__)

NOTIFY_AUTHENTICATION_OWNER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookMfaSecuredCommsV1Workflow:
    """Operate the multi-factor / continuous-authentication and secured-communications posture surface required by NIS2 Art.21(2)(j) and DORA Art.9(4)(b): probe the identity-provider surface to confirm MFA coverage across in-scope principals, assess whether continuous-authentication signals are observed on long-lived sessions, verify the out-of-band emergency communications channel is reachable independently of the primary information-system path, capture a dated posture-attestation artifact, and notify the authentication owner. The playbook is the operationalisation of declared authentication and secured-communications policy; it does not author the policy itself. CORE layer: the four action bodies bind against deterministic primitives under content/playbooks/mfa_secured_comms/primitives/ (probe.probe_mfa_coverage, assess.assess_continuous_auth, verify.verify_oob_channel, artifact.build_mfa_posture_attestation_artifact). The artifact_id is derived from SHA-256(workflow_id|execution_id|captured_at) so the three reference compile targets (n8n, Temporal, LangGraph) re-derive byte-identical bytes from the same execution context. The metric_refs pin the catalogue entry kri.mfa_coverage_gaps@v1 that already ships under content/mappings/nis2/article-21-2-j.yaml. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8
    stable_id         : playbook.mfa_secured_comms@v1
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--52000000-0000-4000-8000-000000000001
    activities        : probe_mfa_coverage, assess_continuous_auth, verify_oob_channels, evidence_capture, notify_authentication_owner
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.mfa_secured_comms@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.mfa_secured_comms@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7b2c3d4e-5f60-4a11-9c2d-e3f4a5b6c7d8', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.mfa_secured_comms@v1'"
            )

WORKFLOW = PlaybookMfaSecuredCommsV1Workflow
ACTIVITIES = (probe_mfa_coverage, assess_continuous_auth, verify_oob_channels, evidence_capture, notify_authentication_owner,)
RETRY_POLICIES = (PROBE_MFA_COVERAGE_RETRY_POLICY, ASSESS_CONTINUOUS_AUTH_RETRY_POLICY, VERIFY_OOB_CHANNELS_RETRY_POLICY, EVIDENCE_CAPTURE_RETRY_POLICY, NOTIFY_AUTHENTICATION_OWNER_RETRY_POLICY,)
