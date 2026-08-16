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
async def inventory_crypto_policy(crypto_scope: str, policy_clauses: dict[str, object], posture_window: str, scoped_assets: dict[str, object]) -> dict[str, object]:
    """Resolve the operator's declared cryptography policy at the start of the posture window: algorithm floor (symmetric and asymmetric), minimum key sizes, declared key-rotation cadence per key class, TLS-version floor, and the set of in-scope endpoints / key-management surfaces / datasets-at-rest enumerated in __crypto_scope__. Reads the operator's governance source-of-truth (policy document or policy catalogue) and emits __policy_inventory_id__ — the snapshot the subsequent steps measure against. The playbook does NOT author the policy; if no policy is declared for __crypto_scope__, this step emits an inventory artifact with the gap explicitly flagged and the downstream steps still run so the attestation records the missing-policy condition.

    CACAO step_id: action--51000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--51000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--51000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'inventory crypto policy', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'inventory_crypto_policy'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--51000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--51000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'inventory crypto policy', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'inventory_crypto_policy'})
        )
        from content.playbooks.crypto_posture_management.primitives.policy import inventory_crypto_policy
        __policy_inventory_id__ = inventory_crypto_policy(posture_window=__posture_window__, crypto_scope=__crypto_scope__, policy_clauses=__policy_clauses__, scoped_assets=__scoped_assets__)

INVENTORY_CRYPTO_POLICY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def probe_cert_posture(accepted_cipher_suites: dict[str, object], certificate_observations: dict[str, object], crypto_scope: str, policy_inventory_id: dict[str, object]) -> dict[str, object]:
    """Probe the certificate posture of the TLS endpoints enumerated in __crypto_scope__ against the floors carried in __policy_inventory_id__: certificate validity and chain, days-to-expiry, negotiated TLS version, negotiated cipher suite, and presence of mandated extensions. Per-endpoint records are aggregated into __cert_posture_id__. The probe is read-only and side-effect-free against operator infrastructure; it does not attempt connection coercion or downgrade. Detection bindings for expired-cert / weak-cipher / floor-violation upstream rule ids are owned by the CORE-layer sibling card once stable ids are selected.

    CACAO step_id: action--51000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--51000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--51000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'probe cert posture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'probe_cert_posture'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--51000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--51000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'probe cert posture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'probe_cert_posture'})
        )
        from content.playbooks.crypto_posture_management.primitives.certificates import probe_cert_posture
        __cert_posture_id__ = probe_cert_posture(crypto_scope=__crypto_scope__, policy_inventory=__policy_inventory_id__, certificate_observations=__certificate_observations__, accepted_cipher_suites=__accepted_cipher_suites__)

PROBE_CERT_POSTURE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def check_key_rotation(crypto_scope: str, key_records: dict[str, object], policy_inventory_id: dict[str, object]) -> dict[str, object]:
    """Walk the key-management surfaces enumerated in __crypto_scope__ and, for each managed key, compare the last-rotation timestamp against the per-key-class cadence carried in __policy_inventory_id__. Emit __rotation_status__ as a per-key record of (key id, key class, last rotation, declared cadence, overdue-by-days). Keys with no declared cadence in the policy snapshot are reported as policy gaps rather than overdue rotations; the distinction is preserved so the attestation surfaces the policy-side and operations-side gaps separately. The check is read-only; it does NOT perform rotations.

    CACAO step_id: action--51000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--51000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--51000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'check key rotation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'check_key_rotation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--51000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--51000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'check key rotation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'check_key_rotation'})
        )
        from content.playbooks.crypto_posture_management.primitives.rotation import check_key_rotation
        __rotation_status__ = check_key_rotation(crypto_scope=__crypto_scope__, policy_inventory=__policy_inventory_id__, key_records=__key_records__)

CHECK_KEY_ROTATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def evidence_capture(captured_at: str, cert_posture_id: dict[str, object], crypto_owner_role: str, execution_id: str, policy_inventory_id: dict[str, object], posture_window: str, rotation_status: dict[str, object], workflow_id: str) -> dict[str, object]:
    """Compose and publish the dated cryptography-posture attestation to the operator's evidence store. The record carries the policy-inventory snapshot, the cert-posture probe artifact, the key-rotation status artifact, the posture window, and a top-level gap summary (missing-policy, expiring-certs, overdue-rotations counts). This is the audit-evident artifact that NIS2 Art.21(2)(h) reviewers read; missing or stale attestations are the failure mode the metrics surface. The attestation is always emitted, including the policy-gap branch (which records the missing-policy condition rather than skipping the attestation).

    CACAO step_id: action--51000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--51000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--51000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'evidence capture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evidence_capture'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--51000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--51000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'evidence capture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evidence_capture'})
        )
        from content.playbooks.crypto_posture_management.primitives.evidence import capture_crypto_evidence
        __attestation_id__ = capture_crypto_evidence(policy_inventory=__policy_inventory_id__, cert_posture=__cert_posture_id__, rotation_status=__rotation_status__, posture_window=__posture_window__, owner_role=__crypto_owner_role__, workflow_id=__workflow_id__, execution_id=__execution_id__, captured_at=__captured_at__)

EVIDENCE_CAPTURE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_crypto_owner(attestation_id: dict[str, object], crypto_owner_role: str, crypto_scope: str, notification_channel_ref: str) -> dict[str, object]:
    """Deliver the attestation reference to the cryptography owner along the operator's pre-bound channel (ticketing system, chat thread, email). Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently; an attestation written but never delivered to the owner is itself a posture gap.

    CACAO step_id: action--51000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--51000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--51000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify crypto owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_crypto_owner'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--51000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--51000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify crypto owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_crypto_owner'})
        )
        from content.playbooks.crypto_posture_management.primitives.notify import plan_crypto_owner_notification
        __notification_plan__ = plan_crypto_owner_notification(attestation=__attestation_id__, crypto_scope=__crypto_scope__, owner_role=__crypto_owner_role__, channel_ref=__notification_channel_ref__)

NOTIFY_CRYPTO_OWNER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookCryptoPostureManagementV1Workflow:
    """Operate the cryptography & encryption posture surface required by NIS2 Art.21(2)(h): inventory the operator's declared cryptography policy and the assets in its scope, probe the certificate posture of declared TLS endpoints, check key-rotation cadence against the documented rotation schedule, capture a dated posture-attestation artifact, and notify the cryptography owner. The playbook is the operationalisation of a documented cryptography policy; it does not author the policy itself. SKELETON only — control bindings (control.crypto_policy_inventory@v1, control.cert_posture_scan@v1, control.key_rotation_evidence@v1) are pinned but detection bindings (expired-cert, weak-cipher, missed-rotation upstream rule ids), golden tests, and per-target compiler emissions are owned by CORE / EXTEND siblings. The metric_refs pin the catalogue entries kri.expiring_tls_certs@v1 and kri.overdue_key_rotations@v1 that already ship under content/mappings/nis2/article-21-2-h.yaml; the CORE/EXTEND siblings add cipher-suite-floor and rotation-cadence KPI catalogue entries and re-pin step-level refs against them. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7
    stable_id         : playbook.crypto_posture_management@v1
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--51000000-0000-4000-8000-000000000001
    activities        : inventory_crypto_policy, probe_cert_posture, check_key_rotation, evidence_capture, notify_crypto_owner
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.crypto_posture_management@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.crypto_posture_management@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--6a1b2c3d-4e5f-4a00-9b1c-d2e3f4a5b6c7', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.crypto_posture_management@v1'"
            )

WORKFLOW = PlaybookCryptoPostureManagementV1Workflow
ACTIVITIES = (inventory_crypto_policy, probe_cert_posture, check_key_rotation, evidence_capture, notify_crypto_owner,)
RETRY_POLICIES = (INVENTORY_CRYPTO_POLICY_RETRY_POLICY, PROBE_CERT_POSTURE_RETRY_POLICY, CHECK_KEY_ROTATION_RETRY_POLICY, EVIDENCE_CAPTURE_RETRY_POLICY, NOTIFY_CRYPTO_OWNER_RETRY_POLICY,)
