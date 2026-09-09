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
async def resolve_policy_inventory(crypto_scope: str, lifecycle_event: str, declared_policy: dict[str, object]) -> dict[str, object]:
    """Resolve the operator's declared cryptography policy at the start of the lifecycle event: policy.resolve_policy_inventory canonicalises the declared clauses for __crypto_scope__ — symmetric and asymmetric algorithm allow-lists, per-algorithm minimum key sizes, per-key-class rotation cadence, TLS-version floor, declared CA / trust anchors, and the certificate expiry buffer — into the snapshot every downstream branch measures its lifecycle action against. The policy is input, not content: an undeclared clause stays undeclared and is named on undocumented_clauses; the framework ships no default cipher baseline, because a shipped baseline would become a de-facto standard it has no authority to set. A misspelled clause key fails loud rather than silently reporting as an operator gap. Where no policy is declared for the scope at all, the inventory is emitted with every clause flagged and the downstream branches still run, recording the missing-policy condition on the attestation rather than proceeding silently. Bound since the CORE-WIRE card: the binding assigns the snapshot to __policy_inventory__ and the compile target's adapter extracts __policy_inventory_id__.

    CACAO step_id: action--52000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'resolve policy inventory', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'resolve_policy_inventory'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'resolve policy inventory', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'resolve_policy_inventory'})
        )
        from content.playbooks.cryptographic_controls.primitives.policy import resolve_policy_inventory
        __policy_inventory__ = resolve_policy_inventory(crypto_scope=__crypto_scope__, declared_policy=__declared_policy__)

RESOLVE_POLICY_INVENTORY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def key_lifecycle(lifecycle_event: str, key_record: dict[str, object], policy_inventory: dict[str, object]) -> dict[str, object]:
    """Discharge the key-lifecycle branch of __lifecycle_event__ — generation of a new key against the declared algorithm and key-size floor (key-generate), rotation of an existing key backreferencing the previous key (key-rotate), or revocation on compromise or scope exit with its reason (key-revoke): keys.record_key_lifecycle judges the executed action's metadata in __key_record__ against the policy snapshot and composes the evidence record. Metadata only — an input carrying key_material, private_key or secret fails loud rather than being quietly dropped, because a dropped secret has already crossed a boundary it must never cross. Each policy check lands on the satisfied / violated / undocumented ladder, with the record outcome reserved for compliant only when every consulted clause is documented and satisfied; a documented floor violation is recorded as a breach on the attestation rather than refused, because the KMS action already happened and hiding it would blind the audit trail. Whether the previous key was overdue for rotation is the read-side crypto_posture_management sibling's check, not this write-side record's. Reached on the key branch of the lifecycle switch; executing the action against the operator's KMS backend is the compile target's adapter. The binding assigns the record to __key_lifecycle_result__; the adapter extracts __key_lifecycle_record__.

    CACAO step_id: action--52000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'key lifecycle', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'key_lifecycle'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'key lifecycle', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'key_lifecycle'})
        )
        from content.playbooks.cryptographic_controls.primitives.keys import record_key_lifecycle
        __key_lifecycle_result__ = record_key_lifecycle(lifecycle_event=__lifecycle_event__, key_record=__key_record__, policy_inventory=__policy_inventory__)

KEY_LIFECYCLE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def enforce_encryption(crypto_scope: str, workload_ref: str, observed_at: str, at_rest_condition: dict[str, object], in_transit_condition: dict[str, object], policy_inventory: dict[str, object]) -> dict[str, object]:
    """Evaluate the encryption-enforcement gate on the pair of conditions the policy names: enforcement.decide_enforcement_gate judges the observed at-rest condition (declared algorithm plus a key-material binding — the binding is a handle, never material) and the observed in-transit condition (negotiated TLS version against the declared floor, compared on the closed 1.0 < 1.1 < 1.2 < 1.3 ladder) for __workload_ref__ against the policy snapshot, and emits the admit / deny decision record. The gate denies only on a documented violation: an undocumented clause admits — the framework has no authority to block a workload on a policy the operator never declared — but the condition is enumerated as undocumented and never reported satisfied. A persistent-storage surface with no key-material binding at all is structurally violated regardless of clause coverage. Read-and-decide only: admitting or blocking the workload is discharged by the operator's provisioning control plane against the emitted decision, so the read-only-by-contract framing that scopes this playbook is preserved. Reached on the enforcement-gate branch of the lifecycle switch. The binding assigns the record to __enforcement_result__; the adapter extracts __enforcement_decision__.

    CACAO step_id: action--52000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'enforce encryption', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enforce_encryption'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'enforce encryption', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enforce_encryption'})
        )
        from content.playbooks.cryptographic_controls.primitives.enforcement import decide_enforcement_gate
        __enforcement_result__ = decide_enforcement_gate(workload_ref=__workload_ref__, observed_at=__observed_at__, at_rest=__at_rest_condition__, in_transit=__in_transit_condition__, policy_inventory=__policy_inventory__)

ENFORCE_ENCRYPTION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def certificate_lifecycle(lifecycle_event: str, certificate_record: dict[str, object], policy_inventory: dict[str, object]) -> dict[str, object]:
    """Discharge the certificate-lifecycle branch of __lifecycle_event__ — issue against the declared CA / trust anchors (cert-issue), renew ahead of the declared expiry buffer backreferencing the previous certificate (cert-renew), or revoke on compromise or scope exit with its reason and the revocation-list reference (cert-revoke): certificates.record_certificate_lifecycle judges the executed action's metadata in __certificate_record__ against the policy snapshot and composes the evidence record. Trust-anchor and expiry-buffer checks land on the same satisfied / violated / undocumented ladder as the key branch; renewal timeliness is judged from the supplied instants against the declared buffer, with no clock read inside the primitive, and a renewal inside the buffer is recorded as a violated check rather than hidden — the renewal already happened. A revocation is not discharged without both its reason and the revocation-list reference. Reached on the certificate branch of the lifecycle switch; executing the action against the operator's CA backend is the compile target's adapter. The binding assigns the record to __cert_lifecycle_result__; the adapter extracts __cert_lifecycle_record__.

    CACAO step_id: action--52000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'certificate lifecycle', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'certificate_lifecycle'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'certificate lifecycle', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'certificate_lifecycle'})
        )
        from content.playbooks.cryptographic_controls.primitives.certificates import record_certificate_lifecycle
        __cert_lifecycle_result__ = record_certificate_lifecycle(lifecycle_event=__lifecycle_event__, certificate_record=__certificate_record__, policy_inventory=__policy_inventory__)

CERTIFICATE_LIFECYCLE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def record_lifecycle_evidence(lifecycle_event: str, event_ts: str, policy_inventory: dict[str, object], key_lifecycle_result: dict[str, object], cert_lifecycle_result: dict[str, object], enforcement_result: dict[str, object]) -> dict[str, object]:
    """Compose the dated cryptographic-controls lifecycle attestation for the operator's evidence store: attestation.compose_lifecycle_attestation embeds the policy snapshot whole and exactly the evidence record the event class produced — the key record on a key event, the certificate record on a certificate event, the gate decision on an enforcement-gate run — and refuses a mismatched or missing payload, because a lifecycle action attested without its evidence, or attested alongside another branch's, is mislabelled evidence. Whichever branch of the lifecycle switch ran supplies its envelope; the other two arrive null. The record is dated from the supplied event instant, never an emitter clock read, and carries the has_breach and has_policy_gap flags computed once here: a gap is true whenever the inventory left a consulted clause undocumented, so a missing policy rides the attestation instead of being silently absorbed. This is the audit-evident write-side counterpart the sibling crypto_posture_management playbook's read-side attestation then measures against; a lifecycle action executed but not recorded is itself a posture gap that surface will find. Publishing to the evidence store is the compile target's adapter. The binding assigns the attestation to __lifecycle_attestation__; the adapter extracts __lifecycle_attestation_id__.

    CACAO step_id: action--52000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'record lifecycle evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'record_lifecycle_evidence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'record lifecycle evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'record_lifecycle_evidence'})
        )
        from content.playbooks.cryptographic_controls.primitives.attestation import compose_lifecycle_attestation
        __lifecycle_attestation__ = compose_lifecycle_attestation(lifecycle_event=__lifecycle_event__, event_ts=__event_ts__, policy_inventory=__policy_inventory__, key_lifecycle_record=__key_lifecycle_result__, cert_lifecycle_record=__cert_lifecycle_result__, enforcement_decision=__enforcement_result__)

RECORD_LIFECYCLE_EVIDENCE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_crypto_owner(lifecycle_attestation_id: str, crypto_scope: str, lifecycle_event: str, lifecycle_attestation: dict[str, object], owner_channel: str) -> dict[str, object]:
    """Compose the notification that delivers the lifecycle-attestation reference to the cryptography owner along the operator's pre-bound __owner_channel__ (ticketing system, chat thread, email): notify.compose_owner_notification grades the urgency from the attestation's own flags — a documented breach or an undocumented consulted clause raises it to attention, since both are conditions the owner must act on (fix the surface, or declare the policy), and a clean attestation informs. The flags arrive as real booleans; a coerced string is refused, because 'false' is truthy and would either page on a clean run or, worse, demote a breach. Composition only: delivery along the channel is the compile target's messaging surface. Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently — a lifecycle action executed and recorded but never delivered to the owner is itself a posture gap. The binding assigns the payload to __owner_notification__.

    CACAO step_id: action--52000000-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--52000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify crypto owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_crypto_owner'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--52000000-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--52000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify crypto owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_crypto_owner'})
        )
        from content.playbooks.cryptographic_controls.primitives.notify import compose_owner_notification
        __owner_notification__ = compose_owner_notification(lifecycle_attestation_id=__lifecycle_attestation_id__, crypto_scope=__crypto_scope__, lifecycle_event=__lifecycle_event__, has_breach=__lifecycle_attestation__.has_breach, has_policy_gap=__lifecycle_attestation__.has_policy_gap, owner_channel=__owner_channel__)

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
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--52000000-0000-4000-8000-000000000001
    activities        : resolve_policy_inventory, key_lifecycle, enforce_encryption, certificate_lifecycle, record_lifecycle_evidence, notify_crypto_owner
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.cryptographic_controls@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.cryptographic_controls@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7c9d0e1f-2a3b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.cryptographic_controls@v1'"
            )

WORKFLOW = PlaybookCryptographicControlsV1Workflow
ACTIVITIES = (resolve_policy_inventory, key_lifecycle, enforce_encryption, certificate_lifecycle, record_lifecycle_evidence, notify_crypto_owner,)
RETRY_POLICIES = (RESOLVE_POLICY_INVENTORY_RETRY_POLICY, KEY_LIFECYCLE_RETRY_POLICY, ENFORCE_ENCRYPTION_RETRY_POLICY, CERTIFICATE_LIFECYCLE_RETRY_POLICY, RECORD_LIFECYCLE_EVIDENCE_RETRY_POLICY, NOTIFY_CRYPTO_OWNER_RETRY_POLICY,)
