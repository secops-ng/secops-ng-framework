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
async def inventory_network_segments(reconciliation_window: str) -> str:
    """Enumerate the documented network segments on the operator's own deployed estate by reading the operator's declared network-inventory sources under the operator's documented source-precedence ordering: declarative infrastructure-as- code records for VLAN / VPC / subnet / zone definitions, the cloud-provider network APIs (VPC / subnet describe endpoints keyed off the operator's account inventory), and the on- premise network-controller inventories. Read-only against each source. Composes the operator-authoritative segment record list under a canonical, source-precedence-ordered hash and pins __segment_inventory_id__ against the composed snapshot; the deterministic derivation lets replays of the same reconciliation window recover the same inventory identifier without re-hitting the sources. Each segment record carries the zone identifier, the cloud/on-premise account or controller binding, the CIDR / IP-plan allocation, and the tenancy label the policy-evaluation step reads. OCSF Network Activity (class_uid 4001) shape: an inventory-composed event is emitted at snapshot pinning naming __reconciliation_window__ and __segment_inventory_id__ for the audit-evident chain.

    CACAO step_id: action--7e750001-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--7e750001-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000002', 'secops_ng.step.name': 'inventory_network_segments', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'inventory_network_segments'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--7e750001-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000002', 'secops_ng.step.name': 'inventory_network_segments', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'inventory_network_segments'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--7e750001-0000-4000-8000-000000000002'"
        )

INVENTORY_NETWORK_SEGMENTS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def evaluate_segmentation_policy(reconciliation_window: str, segment_inventory_id: str) -> str:
    """Read the current segmentation-policy snapshot from the operator's documented policy source (declared zone-transit matrix, per-segment allowance set, OSCAL-anchored control binding for SC-7 boundary-protection and SC-3 security- function isolation) and normalise it against the segment inventory pinned upstream. Pins __policy_snapshot_id__ against the resolved revision so the evidence artifact identifies which policy the reconciliation ran against. Records the per-segment-pair allowance state under the documented three-value allowance algebra (allowed / denied / conditional) — the conditional branch names the predicate the detect step must evaluate against observed reachability before deciding whether a per-pair violation stands. Empty allowance set is emitted explicitly so a policy-missing reconciliation window still closes with an audit-evident artifact rather than short-circuiting the chain silently.

    CACAO step_id: action--7e750001-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--7e750001-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000003', 'secops_ng.step.name': 'evaluate_segmentation_policy', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evaluate_segmentation_policy'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--7e750001-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000003', 'secops_ng.step.name': 'evaluate_segmentation_policy', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evaluate_segmentation_policy'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--7e750001-0000-4000-8000-000000000003'"
        )

EVALUATE_SEGMENTATION_POLICY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def detect_policy_violations(segment_inventory_id: str, policy_snapshot_id: str) -> str:
    """Compute the per-segment-pair violation set by comparing the observed reachability posture against the policy-snapshot allowance state. Observed reachability is drawn from the operator's documented telemetry sources under the documented source-precedence: network-traffic observations (OCSF Network Activity 4001 events emitted by the operator's flow-log stream), boundary-control state pulled from the operator's firewall / security-group inventory, and active reachability probes where the operator's documented probe surface is bound. Each per-pair evaluation resolves to allowed-and-observed (no violation), denied- and-not-observed (no violation, evidence recorded), denied-and-observed (violation emitted), or conditional (predicate evaluated against the observed traffic fingerprint before deciding). Violations are classified against the documented taxonomy — undocumented-transit (traffic across a segment-pair not in the allowance set), unauthorised-egress (traffic to a boundary the policy denies), boundary-control-drift (the firewall / security- group state diverged from the declared zone-transit matrix) — and pinned to __violation_set_id__. The set is keyed against __segment_inventory_id__ + __policy_snapshot_id__ so the same inputs re-emit the same violation identifiers under replay. D3FEND anchor: D3-NTA (network traffic analysis) — the detect step is the operator-side network-traffic analysis primitive against the declared policy. Empty set is emitted explicitly so a clean-window reconciliation is distinguishable from a skipped step.

    CACAO step_id: action--7e750001-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--7e750001-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000004', 'secops_ng.step.name': 'detect_policy_violations', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_policy_violations'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--7e750001-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000004', 'secops_ng.step.name': 'detect_policy_violations', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_policy_violations'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--7e750001-0000-4000-8000-000000000004'"
        )

DETECT_POLICY_VIOLATIONS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def enforce_remediation(violation_set_id: str) -> str:
    """Engage the operator's pre-bound remediation surface against each violation in __violation_set_id__ per the operator's documented per-classification remediation binding. Three documented surfaces: (a) per-segment ACL / firewall-rule change dispatched against the operator's change-management posture (undocumented-transit and unauthorised-egress classifications default here), (b) boundary-control posture-change ticket opened against the operator's documented ticketing surface (boundary-control-drift classification defaults here), (c) short-circuit isolation of the offending path where the violation's severity marker names an active-abuse fingerprint and the operator's documented isolation posture allows automated engagement. Empty when __violation_set_id__ resolved empty; the closure record still names the empty set so the audit-evident chain remains complete. Each engaged action returns a persistent identifier (change-ticket id, posture-change- ticket id, or isolation-record id) that the evidence artifact binds under __remediation_action_id__ together with a per-violation dispatch table naming which surface was engaged against which violation. The playbook does not author the remediation architecture — it dispatches against pre-bound surfaces the operator's change- management posture already documents; auditability is preserved by requiring every engaged action to return an operator-side persistent identifier before the step closes.

    CACAO step_id: action--7e750001-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--7e750001-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000005', 'secops_ng.step.name': 'enforce_remediation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enforce_remediation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--7e750001-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000005', 'secops_ng.step.name': 'enforce_remediation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enforce_remediation'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--7e750001-0000-4000-8000-000000000005'"
        )

ENFORCE_REMEDIATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def generate_posture_evidence_artifact(reconciliation_window: str, segment_inventory_id: str, policy_snapshot_id: str, violation_set_id: str, remediation_action_id: str) -> str:
    """Publish the dated network-security-posture evidence artifact to the operator's evidence store. The artifact is shaped against an OSCAL Assessment Result stub: the assessed subject is the reconciled segment inventory pinned by __segment_inventory_id__, the assessment activity is the policy-reconciliation run keyed by __reconciliation_window__ against __policy_snapshot_id__, the finding set carries one finding per violation in __violation_set_id__ (or an explicit no-findings marker when the set is empty), and the response record binds each finding to the engaged remediation action from __remediation_action_id__. The artifact closes the audit-evident chain end-to-end for the window: an auditor reading the record can trace from window identifier through inventory, policy, violation set, and remediation dispatch to the operator-side persistent identifier the remediation surface returned. Pins __posture_evidence_id__ against the persisted record. Always emitted, including on the empty-violation-set branch — the closure record is the primary audit-evident output of the reconciliation regardless of whether any violation was surfaced.

    CACAO step_id: action--7e750001-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--7e750001-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000006', 'secops_ng.step.name': 'generate_posture_evidence_artifact', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'generate_posture_evidence_artifact'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--7e750001-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000006', 'secops_ng.step.name': 'generate_posture_evidence_artifact', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'generate_posture_evidence_artifact'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--7e750001-0000-4000-8000-000000000006'"
        )

GENERATE_POSTURE_EVIDENCE_ARTIFACT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookNetworkSecurityV1Workflow:
    """CACAO v2 playbook operationalising the per-window reconciliation of a declared segmentation policy against the observed network-boundary state on the operator's own deployed estate. Anchored to NIS2 Article 21(2)(e) (security in network and information systems) and to DORA Article 9 read against the JC RTS on ICT risk management framework (Commission Delegated Regulation (EU) 2024/1774) network- security articles. The lifecycle enumerates documented network segments from the operator's declarative network-inventory sources, evaluates the segmentation-policy allowances against the observed per-segment reachability posture, detects policy violations (undocumented cross-segment reachability, unauthorised egress paths, boundary-control drift against the declared zone-transit matrix), engages the operator's pre-bound remediation surface against each violation, and generates a dated network-security- posture evidence artifact for the reconciliation window. The playbook does not author the operator's segmentation policy or the segmentation architecture itself; it operationalises a documented reconciliation posture against pre-bound segmentation sources and pre-bound remediation surfaces. Distinct from playbook.infra_posture_management@v1 which is the broader infrastructure-posture (host, workload, IAM) reconciliation engine; this playbook is the network-boundary limb only.

    CACAO playbook id : playbook--7e750001-0000-4000-8000-000000000001
    stable_id         : playbook.network_security@v1
    content_version   : 0.2.0
    maturity          : experimental
    workflow_start    : start--7e750001-0000-4000-8000-000000000001
    activities        : inventory_network_segments, evaluate_segmentation_policy, detect_policy_violations, enforce_remediation, generate_posture_evidence_artifact
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.network_security@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.network_security@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.network_security@v1'"
            )

WORKFLOW = PlaybookNetworkSecurityV1Workflow
ACTIVITIES = (inventory_network_segments, evaluate_segmentation_policy, detect_policy_violations, enforce_remediation, generate_posture_evidence_artifact,)
RETRY_POLICIES = (INVENTORY_NETWORK_SEGMENTS_RETRY_POLICY, EVALUATE_SEGMENTATION_POLICY_RETRY_POLICY, DETECT_POLICY_VIOLATIONS_RETRY_POLICY, ENFORCE_REMEDIATION_RETRY_POLICY, GENERATE_POSTURE_EVIDENCE_ARTIFACT_RETRY_POLICY,)
