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
async def resolve_policy_inventory(crypto_scope: str, lifecycle_event: str) -> str:
    """Resolve the operator's declared cryptography policy at the start of the lifecycle event: algorithm floor (symmetric and asymmetric), minimum key sizes, per-key-class rotation cadence, TLS-version floor, declared CA / trust anchors, and expiry buffer for certificate renewal. Emits __policy_inventory_id__ — the snapshot every downstream branch measures its lifecycle action against. If no policy is declared for __crypto_scope__ the step emits an inventory artifact with the gap explicitly flagged; the downstream lifecycle branches still run and record the missing-policy condition on the attestation rather than proceeding silently.

    CACAO step_id: action--52000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'resolve policy inventory', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'resolve_policy_inventory'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'resolve policy inventory', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'resolve_policy_inventory'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--52000000-0000-4000-8000-000000000002'"
        )

RESOLVE_POLICY_INVENTORY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def key_lifecycle(crypto_scope: str, lifecycle_event: str, policy_inventory_id: str) -> str:
    """Discharge the key-lifecycle branch of __lifecycle_event__: generation of a new key against the algorithm / key-size floor carried in __policy_inventory_id__ (key-generate); rotation of an existing key against the per-key-class cadence, keying a new material and backreferencing the previous key (key-rotate); revocation of a key on compromise or scope exit, emitting the revocation reason (key-revoke). The branching on __lifecycle_event__ across the three sub-branches is a linear scaffold at the CACAO layer; the sibling EXTEND card lands the branch-selection logic and the adapter Protocols against the operator's KMS backend under patterns.cryptographic_controls. Per-branch evidence is aggregated into __key_lifecycle_record__.

    CACAO step_id: action--52000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'key lifecycle', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'key_lifecycle'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'key lifecycle', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'key_lifecycle'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--52000000-0000-4000-8000-000000000003'"
        )

KEY_LIFECYCLE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def enforce_encryption(crypto_scope: str, policy_inventory_id: str) -> str:
    """Evaluate the encryption-enforcement gate on the pair of at-rest and in-transit conditions the policy names: (a) does the target workload's persistent-storage surface satisfy the declared at-rest algorithm and key-material binding, and (b) do the target workload's declared network endpoints negotiate the declared TLS-version and cipher-suite floor. Emit __enforcement_decision__ as a decision record (admit / deny + reason). The gate is a read-and-decide surface — the actual admission or blocking of the workload is discharged by the operator's provisioning control plane against the emitted decision, so the read-only-by-contract framing that scopes this playbook is preserved.

    CACAO step_id: action--52000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'enforce encryption', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enforce_encryption'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'enforce encryption', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enforce_encryption'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--52000000-0000-4000-8000-000000000004'"
        )

ENFORCE_ENCRYPTION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def certificate_lifecycle(crypto_scope: str, lifecycle_event: str, policy_inventory_id: str) -> str:
    """Discharge the certificate-lifecycle branch of __lifecycle_event__: issue a new certificate against the operator's declared CA / trust anchors (cert-issue); renew an existing certificate ahead of the declared expiry buffer, backreferencing the previous certificate (cert-renew); revoke a certificate on compromise or scope exit, emitting the revocation reason and updating the operator's revocation list surface (cert-revoke). The branching on __lifecycle_event__ across the three sub-branches is a linear scaffold at the CACAO layer; the sibling EXTEND card lands the branch-selection logic and the adapter Protocols against the operator's CA backend under patterns.cryptographic_controls. Per-branch evidence is aggregated into __cert_lifecycle_record__.

    CACAO step_id: action--52000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'certificate lifecycle', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'certificate_lifecycle'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'certificate lifecycle', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'certificate_lifecycle'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--52000000-0000-4000-8000-000000000005'"
        )

CERTIFICATE_LIFECYCLE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def record_lifecycle_evidence(policy_inventory_id: str, key_lifecycle_record: str, cert_lifecycle_record: str, enforcement_decision: str, lifecycle_event: str) -> str:
    """Compose and publish the dated cryptographic-controls lifecycle attestation to the operator's evidence store. The record carries the policy-inventory snapshot, the key-lifecycle record (when set), the certificate-lifecycle record (when set), the enforcement-gate decision (when set), and the __lifecycle_event__ context. This is the audit-evident write-side counterpart the sibling crypto_posture_management playbook's read-side attestation then measures against; a lifecycle action executed but not recorded is itself a posture gap the sibling surface will surface.

    CACAO step_id: action--52000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'record lifecycle evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'record_lifecycle_evidence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'record lifecycle evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'record_lifecycle_evidence'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--52000000-0000-4000-8000-000000000006'"
        )

RECORD_LIFECYCLE_EVIDENCE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_crypto_owner(lifecycle_attestation_id: str, crypto_scope: str, lifecycle_event: str) -> None:
    """Deliver the lifecycle-attestation reference to the cryptography owner along the operator's pre-bound channel (ticketing system, chat thread, email). Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently; a lifecycle action executed and recorded but never delivered to the owner is itself a posture gap.

    CACAO step_id: action--52000000-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify crypto owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_crypto_owner'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify crypto owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_crypto_owner'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--52000000-0000-4000-8000-000000000007'"
        )

NOTIFY_CRYPTO_OWNER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookCryptographicControlsV1Workflow:
    """Operator-side lifecycle of the cryptographic-controls surface an essential or important entity operates against its documented cryptography policy. Covers the three lifecycle disciplines the policy has to discharge in production: (a) symmetric- and asymmetric-key lifecycle — generation of new keys against the declared algorithm and key-size floor, rotation of keys against the declared per-key-class cadence, and revocation of keys on compromise or scope exit; (b) an encryption-enforcement gate that admits or denies workload provisioning on the pair of at-rest (persistent-storage encryption) and in-transit (declared-endpoint TLS floor) conditions the policy names; and (c) certificate lifecycle — issue against the operator's declared CA / trust anchors, renew ahead of the declared expiry buffer, and revoke on compromise or scope exit. Deliberately paired with the sibling crypto_posture_management playbook which operates the read-only posture-attestation surface (per-cycle inventory, cert probe, rotation-status check, dated attestation); this lifecycle is the write-side lane that produces the material the posture surface then attests. Workflow shape, variable envelope, mapping anchors, and three-target compiled examples with byte-parity goldens ship on the CORE tier; adapter Protocols under patterns.cryptographic_controls (KMS backend, CA backend, storage-encryption backend, TLS-endpoint backend), the enforcement-gate policy evaluator, and the cookbook walkthrough with advanced features (HSM-backed key ceremonies, post-quantum rollover choreography, per-Member-State CA-trust posture) land on the sibling EXTEND card.

    CACAO playbook id : playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f
    stable_id         : playbook.cryptographic_controls@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--52000000-0000-4000-8000-000000000001
    activities        : resolve_policy_inventory, key_lifecycle, enforce_encryption, certificate_lifecycle, record_lifecycle_evidence, notify_crypto_owner
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.cryptographic_controls@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.cryptographic_controls@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.cryptographic_controls@v1'"
            )

WORKFLOW = PlaybookCryptographicControlsV1Workflow
ACTIVITIES = (resolve_policy_inventory, key_lifecycle, enforce_encryption, certificate_lifecycle, record_lifecycle_evidence, notify_crypto_owner,)
RETRY_POLICIES = (RESOLVE_POLICY_INVENTORY_RETRY_POLICY, KEY_LIFECYCLE_RETRY_POLICY, ENFORCE_ENCRYPTION_RETRY_POLICY, CERTIFICATE_LIFECYCLE_RETRY_POLICY, RECORD_LIFECYCLE_EVIDENCE_RETRY_POLICY, NOTIFY_CRYPTO_OWNER_RETRY_POLICY,)
