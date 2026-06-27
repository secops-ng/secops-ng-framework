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
async def detect_patch_availability(update_subject: str, update_reference: str) -> None:
    """Resolve the trigger for this run: an advisory landed on the operator's documented advisory-intake surface (vendor feed, distribution channel, upstream release notification) against __update_subject__, an operator-scheduled maintenance window opened, or an operator-initiated trigger landed. Reads __update_subject__ and __update_reference__ to confirm the update applies to a tracked deployment-inventory row; reads the operator's documented deployment-inventory row to surface the ring topology (test / canary / broad) and the patch-criticality taxonomy the downstream steps will classify against.

    CACAO step_id: action--70000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--70000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect patch availability', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_patch_availability'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--70000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect patch availability', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_patch_availability'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--70000000-0000-4000-8000-000000000002'"
        )

DETECT_PATCH_AVAILABILITY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def classify_patch_criticality(update_subject: str, update_reference: str) -> str:
    """Classify the update against the operator's documented patch-criticality taxonomy: security-critical (rollout deadline measured in hours / days, e.g. remotely exploitable RCE with active exploitation, kernel / hypervisor patch), security-routine (rollout deadline measured in days / weeks, e.g. lower-severity advisories without active exploitation), or feature-only (rollout cadenced against the operator's documented maintenance window, no security urgency). Reads the same advisory surface the detect step consulted plus any operator-bound severity / exploit-status enrichment documented for __update_subject__. Sets __patch_criticality__. The classification is best-effort and time-boxed; if classification cannot be completed within the documented intake deadline (so the operator is not held by a perfect-classification stall while the deadline slips), this step leaves __patch_criticality__ empty and the downstream stage-rollout step treats the update as security-critical for scheduling purposes rather than waiting.

    CACAO step_id: action--70000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--70000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify patch criticality', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_patch_criticality'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--70000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify patch criticality', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_patch_criticality'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--70000000-0000-4000-8000-000000000003'"
        )

CLASSIFY_PATCH_CRITICALITY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def stage_rollout_to_canary_ring(update_subject: str, update_reference: str, patch_criticality: str) -> str:
    """Engage the update against the operator's pre-bound canary ring for __update_subject__: push the update through the documented distribution channel (package mirror, image registry, firmware-distribution surface) to the test / canary cohort. Reads __patch_criticality__ to select the rollout cadence (security-critical → immediate, security-routine → next-window, feature-only → maintenance-window); when __patch_criticality__ is empty the step treats the update as security-critical for scheduling rather than waiting for classification. Emits __staged_ring_id__ — the durable identifier of the canary cohort that received the update (cohort reference, change ticket id, distribution-channel push reference). Detection bindings for canary-engagement misconfiguration (update pushed to wrong ring, distribution channel returned partial success, cohort membership stale) are owned by CORE-layer cards once upstream rule ids are selected.

    CACAO step_id: action--70000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--70000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'stage rollout to canary ring', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'stage_rollout_to_canary_ring'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--70000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'stage rollout to canary ring', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'stage_rollout_to_canary_ring'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--70000000-0000-4000-8000-000000000004'"
        )

STAGE_ROLLOUT_TO_CANARY_RING_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def validate_canary(update_subject: str, staged_ring_id: str) -> bool:
    """Observe the canary ring against the operator's documented health gates after the staged rollout: functional probes green, error-rate / latency deviation inside the documented thresholds, rollback path verified for the documented validation window. Reads __update_subject__ and __staged_ring_id__; sets __canary_healthy__. A false outcome does not block downstream steps — the evidence-capture record is published with the failure marker, the fan-out step is skipped, and the notify step pages the maintenance owner with the full context so the next maintenance lever (rollback the canary, escalate the advisory, hold the broad rollout) can be engaged. The mean-time-to-containment KPI (kpi.mttr_containment@v1) reads this step's __canary_healthy__ observation alongside the evidence-capture timestamp to measure validation-window discharge.

    CACAO step_id: action--70000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--70000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'validate canary', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'validate_canary'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--70000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'validate canary', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'validate_canary'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--70000000-0000-4000-8000-000000000005'"
        )

VALIDATE_CANARY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def fan_out_to_broad_rings(update_subject: str, update_reference: str, staged_ring_id: str, canary_healthy: bool) -> str:
    """On a healthy canary (__canary_healthy__ true), engage the update against the remaining rings of the operator's documented deployment-ring topology along the same documented distribution channel. Reads __update_subject__, __update_reference__, __staged_ring_id__, and __canary_healthy__; emits __broad_rollout_id__ — the durable identifier of the broad-ring engagement (deployment reference, change ticket id, distribution-channel push reference). On an unhealthy canary (__canary_healthy__ false) the step is skipped and __broad_rollout_id__ is left empty; the evidence-capture and notify steps record the skip explicitly so the audit-evident chain is closed without forcing the broad rollout against a failing canary. The conditional shape is intentionally explicit at the description level rather than at a CACAO conditional-step level for SKELETON simplicity; CORE-layer cards may refactor into a `playbook-condition` step once the conditional shape is exercised by the worked-example fan-out.

    CACAO step_id: action--70000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--70000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'fan out to broad rings', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'fan_out_to_broad_rings'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--70000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'fan out to broad rings', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'fan_out_to_broad_rings'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--70000000-0000-4000-8000-000000000006'"
        )

FAN_OUT_TO_BROAD_RINGS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def evidence_capture(update_subject: str, update_reference: str, patch_criticality: str, staged_ring_id: str, canary_healthy: bool, broad_rollout_id: str) -> str:
    """Compose and publish the dated patch-application evidence record to the operator's evidence store. The record carries the update subject, the advisory reference, the classified criticality (or the empty-classification marker on the short-circuit branch), the staged ring id, the canary health outcome (or the failure marker), the broad rollout id (or the empty marker on the canary-failure branch), and the observed health-gate measurements across the validation window. This is the audit-evident artifact NIS2 Art. 21(2)(e) reviewers read against a maintenance / patch-rollout obligation; missing or stale evidence is the failure mode the maintenance metrics surface.

    CACAO step_id: action--70000000-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--70000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'evidence capture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evidence_capture'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--70000000-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'evidence capture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evidence_capture'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--70000000-0000-4000-8000-000000000007'"
        )

EVIDENCE_CAPTURE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_maintenance_owner(evidence_id: str, update_subject: str, canary_healthy: bool) -> None:
    """Deliver the evidence reference to the maintenance owner along the operator's pre-bound channel (ticketing system, chat thread, change-management board). Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently; an evidence record written but never delivered to the owner is itself a maintenance-discipline gap. Notification carries the canary health outcome so a false __canary_healthy__ pages with appropriate urgency for the next maintenance lever (rollback the canary, escalate the advisory, hold the broad rollout).

    CACAO step_id: action--70000000-0000-4000-8000-000000000008
    """
    with _TRACER.start_as_current_span(
        name='activity.action--70000000-0000-4000-8000-000000000008',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 'notify maintenance owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_maintenance_owner'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--70000000-0000-4000-8000-000000000008', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 'notify maintenance owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_maintenance_owner'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--70000000-0000-4000-8000-000000000008'"
        )

NOTIFY_MAINTENANCE_OWNER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookPatchManagementV1Workflow:
    """Operationalise the patch / update maintenance capability against the operator's own deployed estate: detect that a security update is available against a tracked package / image / firmware line, classify the update against the operator's documented patch-criticality taxonomy (security-critical, security-routine, feature-only), stage the rollout against the operator's documented deployment-ring topology (test → canary → broad), validate the canary ring against the documented health gates (functional probes, error-rate / latency deviation, rollback readiness), fan out to the remaining rings on a green canary, capture the dated patch-application evidence record, and notify the maintenance owner. The playbook does not author the operator's patch-distribution architecture itself; it operationalises the documented rollout posture against an already-provisioned update channel and ring topology. SKELETON only — control bindings (control.patch_evidence@v1) are pinned but detection bindings, golden tests, and per-target compiler emissions are owned by CORE / EXTEND siblings. The CORE / EXTEND siblings add the canary-health / rollback-readiness detection bindings and the time-to-patch / patch-coverage metric emitters. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc
    stable_id         : playbook.patch_management@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--70000000-0000-4000-8000-000000000001
    activities        : detect_patch_availability, classify_patch_criticality, stage_rollout_to_canary_ring, validate_canary, fan_out_to_broad_rings, evidence_capture, notify_maintenance_owner
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.patch_management@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.patch_management@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.patch_management@v1'"
            )

WORKFLOW = PlaybookPatchManagementV1Workflow
ACTIVITIES = (detect_patch_availability, classify_patch_criticality, stage_rollout_to_canary_ring, validate_canary, fan_out_to_broad_rings, evidence_capture, notify_maintenance_owner,)
RETRY_POLICIES = (DETECT_PATCH_AVAILABILITY_RETRY_POLICY, CLASSIFY_PATCH_CRITICALITY_RETRY_POLICY, STAGE_ROLLOUT_TO_CANARY_RING_RETRY_POLICY, VALIDATE_CANARY_RETRY_POLICY, FAN_OUT_TO_BROAD_RINGS_RETRY_POLICY, EVIDENCE_CAPTURE_RETRY_POLICY, NOTIFY_MAINTENANCE_OWNER_RETRY_POLICY,)
