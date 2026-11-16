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
async def inventory_network_segments(reconciliation_window: str, inventory_sources: str, inventory_composed_at: str) -> dict[str, object]:
    """Compose the window's segment inventory from the operator's network-inventory sources in its documented precedence order: infrastructure-as-code records, cloud-provider network APIs and on-premise network controllers, read-only. Where two sources report the same segment the higher one's record is kept and every field a lower one disagrees on is recorded. A segment no declarative source reports is in the estate but not in the documentation, and is listed as undocumented; overlapping ranges inside one binding are listed too. Produces __segment_inventory__, from which __segment_inventory_id__ is extracted.

    CACAO step_id: action--7e750001-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--7e750001-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000002', 'secops_ng.step.name': 'inventory_network_segments', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'inventory_network_segments'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--7e750001-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000002', 'secops_ng.step.name': 'inventory_network_segments', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'inventory_network_segments'})
        )
        from content.playbooks.network_security.primitives.inventory import compose_segment_inventory
        __segment_inventory__ = compose_segment_inventory(window_ref=__reconciliation_window__, sources=__inventory_sources__, composed_at=__inventory_composed_at__)

INVENTORY_NETWORK_SEGMENTS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def evaluate_segmentation_policy(segment_inventory: dict[str, object], segmentation_policy: dict[str, object], policy_evaluated_at: str) -> dict[str, object]:
    """Normalise the operator's zone-transit matrix against the inventory and pin the snapshot the window is reconciled against. Every directed zone pair is allowed, denied, or conditional on services or a time-boxed authorisation; every pair the matrix does not list is denied, within a zone as well as between zones (Commission Implementing Regulation (EU) 2024/2690, Annex points 6.7.2(c) and 6.8.2(e)). The policy's own gaps are recorded. Produces __policy_evaluation__, from which __policy_snapshot_id__ is extracted.

    CACAO step_id: action--7e750001-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--7e750001-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000003', 'secops_ng.step.name': 'evaluate_segmentation_policy', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evaluate_segmentation_policy'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--7e750001-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000003', 'secops_ng.step.name': 'evaluate_segmentation_policy', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evaluate_segmentation_policy'})
        )
        from content.playbooks.network_security.primitives.policy import evaluate_segmentation_policy
        __policy_evaluation__ = evaluate_segmentation_policy(inventory=__segment_inventory__, policy=__segmentation_policy__, evaluated_at=__policy_evaluated_at__)

EVALUATE_SEGMENTATION_POLICY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def detect_policy_violations(segment_inventory: dict[str, object], policy_evaluation: dict[str, object], observed_transits: str, boundary_rules: str, violations_detected_at: str) -> dict[str, object]:
    """Compare the observed transits and the boundary rules in force against the pinned matrix. An observed transit outside it is unauthorised_egress when the destination is an external zone and undocumented_transit otherwise; a conditional allowance holds only for its services and inside its authorisation window. A boundary rule that permits what the matrix denies or does not list, or denies what it plainly allows, is boundary_control_drift, recorded with its direction whether or not traffic was seen. Repeated sightings merge into one violation. The set may be empty. Produces __violation_detection__, from which __violation_set_id__ is extracted.

    CACAO step_id: action--7e750001-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--7e750001-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000004', 'secops_ng.step.name': 'detect_policy_violations', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_policy_violations'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--7e750001-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000004', 'secops_ng.step.name': 'detect_policy_violations', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_policy_violations'})
        )
        from content.playbooks.network_security.primitives.detection import detect_policy_violations
        __violation_detection__ = detect_policy_violations(inventory=__segment_inventory__, policy=__policy_evaluation__, observations=__observed_transits__, boundary_rules=__boundary_rules__, detected_at=__violations_detected_at__)

DETECT_POLICY_VIOLATIONS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def enforce_remediation(violation_detection: dict[str, object], remediation_binding: dict[str, object], automated_isolation_allowed: bool, remediation_dispatches: str, remediation_dispatched_at: str) -> dict[str, object]:
    """Record the dispatch of every violation to the operator's pre-bound remediation surface: a rule change or a posture ticket per the binding. Isolation is the short-circuit, never the default: only a violation carrying an active-abuse fingerprint, and only when the operator's posture allows automated isolation (Delegated Regulation (EU) 2024/1774, Art. 13). The step closes only when every dispatch has returned a persistent identifier. It runs on every window; with an empty violation set it dispatches nothing. Produces __remediation_dispatch__, from which __remediation_action_id__ is extracted, unset when nothing was dispatched.

    CACAO step_id: action--7e750001-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--7e750001-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000005', 'secops_ng.step.name': 'enforce_remediation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enforce_remediation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--7e750001-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000005', 'secops_ng.step.name': 'enforce_remediation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enforce_remediation'})
        )
        from content.playbooks.network_security.primitives.remediation import dispatch_remediation
        __remediation_dispatch__ = dispatch_remediation(detection=__violation_detection__, binding=__remediation_binding__, automated_isolation=__automated_isolation_allowed__, dispatches=__remediation_dispatches__, dispatched_at=__remediation_dispatched_at__)

ENFORCE_REMEDIATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def generate_posture_evidence_artifact(segment_inventory: dict[str, object], policy_evaluation: dict[str, object], violation_detection: dict[str, object], remediation_dispatch: dict[str, object], evidence_produced_at: str) -> dict[str, object]:
    """Compose the dated posture evidence for the window, shaped after an OSCAL assessment result. The chain is checked: the policy evaluation must be of this inventory, the detection of this inventory and snapshot, and the dispatch of this violation set; a record from another window is refused. Every finding names its surface and the identifier the surface returned; an empty window says no_findings. Undocumented segments, source disagreements and the policy's own gaps are carried as open items. Produces __posture_evidence__, from which __posture_evidence_id__ is extracted.

    CACAO step_id: action--7e750001-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--7e750001-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000006', 'secops_ng.step.name': 'generate_posture_evidence_artifact', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'generate_posture_evidence_artifact'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--7e750001-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--7e750001-0000-4000-8000-000000000006', 'secops_ng.step.name': 'generate_posture_evidence_artifact', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'generate_posture_evidence_artifact'})
        )
        from content.playbooks.network_security.primitives.evidence import compose_posture_evidence
        __posture_evidence__ = compose_posture_evidence(inventory=__segment_inventory__, policy=__policy_evaluation__, detection=__violation_detection__, remediation=__remediation_dispatch__, produced_at=__evidence_produced_at__)

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
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--7e750001-0000-4000-8000-000000000001
    activities        : inventory_network_segments, evaluate_segmentation_policy, detect_policy_violations, enforce_remediation, generate_posture_evidence_artifact
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.network_security@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.network_security@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7e750001-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.network_security@v1'"
            )

WORKFLOW = PlaybookNetworkSecurityV1Workflow
ACTIVITIES = (inventory_network_segments, evaluate_segmentation_policy, detect_policy_violations, enforce_remediation, generate_posture_evidence_artifact,)
RETRY_POLICIES = (INVENTORY_NETWORK_SEGMENTS_RETRY_POLICY, EVALUATE_SEGMENTATION_POLICY_RETRY_POLICY, DETECT_POLICY_VIOLATIONS_RETRY_POLICY, ENFORCE_REMEDIATION_RETRY_POLICY, GENERATE_POSTURE_EVIDENCE_ARTIFACT_RETRY_POLICY,)
