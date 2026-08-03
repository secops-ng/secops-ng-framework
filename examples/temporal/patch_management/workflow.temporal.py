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
    """Detect-patch-availability step. Binds against the deterministic primitive at content.playbooks.patch_management.primitives.detect.detect_patch_availability: normalises the advisory observation that landed on the operator's documented advisory-intake surface (vendor feed, distribution channel, upstream release notification) against the operator-supplied tracked deployment-inventory and emits a canonical update-subject + update-reference record (plus the advisory_kind and the in_scope marker). Reads __update_subject__ and __update_reference__; the operator's deployment-inventory row supplies the ring topology and the patch-criticality taxonomy the downstream steps will classify against. The detect step is read-only against the advisory-intake surface and the deployment-inventory; the framework does not author either.

    CACAO step_id: action--70000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--70000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect patch availability', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_patch_availability'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--70000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect patch availability', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_patch_availability'})
        )
        from content.playbooks.patch_management.primitives.detect import detect_patch_availability
        __detection_record__ = detect_patch_availability(update_subject=__update_subject__, update_reference=__update_reference__, advisory_kind=__advisory_kind__, tracked_inventory=__tracked_inventory__)

DETECT_PATCH_AVAILABILITY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def classify_patch_criticality(update_subject: str, update_reference: str) -> str:
    """Classify-patch-criticality step. Binds against the deterministic primitive at content.playbooks.patch_management.primitives.classify.classify_patch_criticality: resolves the update against the operator's documented patch-criticality taxonomy (security-critical, security-routine, feature-only) over the closed severity-band + exploit-status + feature-only inputs. Reads the same advisory surface the detect step consulted plus any operator-bound severity / exploit-status enrichment documented for __update_subject__. Sets __patch_criticality__. The classification is best-effort and time-boxed; when the documented intake deadline elapses the primitive is invoked with deadline_missed=true and emits the sentinel 'unclassified' so the operator is not held by a perfect-classification stall while the rollout deadline slips; the downstream stage-rollout step treats the unclassified sentinel (and the empty wire shape) as security-critical for scheduling purposes rather than waiting.

    CACAO step_id: action--70000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--70000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify patch criticality', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_patch_criticality'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--70000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify patch criticality', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_patch_criticality'})
        )
        from content.playbooks.patch_management.primitives.classify import classify_patch_criticality
        __patch_criticality__ = classify_patch_criticality(update_subject=__update_subject__, severity_band=__severity_band__, exploit_observed=__exploit_observed__, is_feature_only=__is_feature_only__)

CLASSIFY_PATCH_CRITICALITY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def stage_rollout_to_canary_ring(update_subject: str, update_reference: str, patch_criticality: str) -> str:
    """Stage-rollout-to-canary-ring step. Binds against the deterministic primitive at content.playbooks.patch_management.primitives.stage.stage_rollout_to_canary_ring: derives a SHA-256 staged_ring_id over the canonical (update_subject, update_reference, canary_ring, cadence) tuple, where the canary cohort is the second entry of the operator's documented test/canary/broad ring topology and the cadence is selected by the classified __patch_criticality__ (security-critical -> immediate, security-routine -> next-window, feature-only -> maintenance-window; the unclassified sentinel and the empty wire shape both map to immediate). The compile target's runtime engages the update against the operator's distribution channel upstream; the primitive only emits the durable identifier. Sets __staged_ring_id__. Detection bindings for canary-engagement misconfiguration (update pushed to wrong ring, distribution channel returned partial success, cohort membership stale) are owned by CORE-FANOUT cards once upstream rule ids are selected.

    CACAO step_id: action--70000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--70000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'stage rollout to canary ring', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'stage_rollout_to_canary_ring'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--70000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'stage rollout to canary ring', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'stage_rollout_to_canary_ring'})
        )
        from content.playbooks.patch_management.primitives.stage import stage_rollout_to_canary_ring
        __staged_ring_id__ = stage_rollout_to_canary_ring(update_subject=__update_subject__, update_reference=__update_reference__, patch_criticality=__patch_criticality__, ring_topology=__ring_topology__)

STAGE_ROLLOUT_TO_CANARY_RING_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def validate_canary(update_subject: str, staged_ring_id: str) -> bool:
    """Validate-canary step. Binds against the deterministic primitive at content.playbooks.patch_management.primitives.validate.validate_canary: evaluates the closed health-gate inputs (functional_probe in {green, red, unknown}, error_rate_within_threshold, latency_within_threshold, rollback_ready) and emits __canary_healthy__ true iff the functional probe is green and all three threshold gates are true. The compile target's runtime reads the documented canary-health endpoints upstream; the primitive only evaluates the resulting closed gate combination. A false outcome does not block downstream steps — the evidence-capture record is published with the failure marker, the fan-out step is the deterministic skip path, and the notify step pages the maintenance owner with full context so the next maintenance lever (rollback the canary, escalate the advisory, hold the broad rollout) can be engaged. The mean-time-to-containment KPI (kpi.mttr_containment@v1) reads this step's __canary_healthy__ observation alongside the evidence-capture timestamp to measure validation-window discharge.

    CACAO step_id: action--70000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--70000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'validate canary', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'validate_canary'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--70000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'validate canary', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'validate_canary'})
        )
        from content.playbooks.patch_management.primitives.validate import validate_canary
        __canary_verdict__ = validate_canary(functional_probe=__functional_probe__, error_rate_within_threshold=__error_rate_within_threshold__, latency_within_threshold=__latency_within_threshold__, rollback_ready=__rollback_ready__)

VALIDATE_CANARY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def fan_out_to_broad_rings(update_subject: str, update_reference: str, staged_ring_id: str, canary_healthy: bool) -> str:
    """Fan-out-to-broad-rings step. Binds against the deterministic primitive at content.playbooks.patch_management.primitives.fanout.fan_out_to_broad_rings: on a healthy canary (__canary_healthy__ true) derives a SHA-256 broad_rollout_id over the canonical (update_subject, update_reference, staged_ring_id, sorted broad_rings) tuple; on an unhealthy canary the step is the deterministic skip path leaving __broad_rollout_id__ empty with the explicit broad_rollout_skip_reason='canary_unhealthy' marker so the evidence-capture step records the skip in the audit-evident chain without forcing the broad rollout against a failing canary. The compile target's runtime engages the update against the operator's distribution channel upstream; the primitive only emits the durable identifier or the skip marker. Reads __update_subject__, __update_reference__, __staged_ring_id__, and __canary_healthy__; emits __broad_rollout_id__. The conditional shape is intentionally explicit at the description level rather than at a CACAO conditional-step level for SKELETON simplicity; CORE-layer cards may refactor into a `playbook-condition` step once the conditional shape is exercised by the worked-example fan-out.

    CACAO step_id: action--70000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--70000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'fan out to broad rings', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'fan_out_to_broad_rings'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--70000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'fan out to broad rings', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'fan_out_to_broad_rings'})
        )
        from content.playbooks.patch_management.primitives.fanout import fan_out_to_broad_rings
        __broad_rollout_id__ = fan_out_to_broad_rings(update_subject=__update_subject__, update_reference=__update_reference__, staged_ring_id=__staged_ring_id__, canary_healthy=__canary_healthy__, broad_rings=__broad_rings__)

FAN_OUT_TO_BROAD_RINGS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def evidence_capture(update_subject: str, update_reference: str, patch_criticality: str, staged_ring_id: str, canary_healthy: bool, broad_rollout_id: str) -> str:
    """Evidence-capture step. Binds against the deterministic primitive at content.playbooks.patch_management.primitives.artifact.build_patch_application_evidence_artifact: composes the JSON-native patch-application evidence record shaped against schemas/evidence/patch.schema.json (stream: patch) and pins the artifact_id as SHA-256(workflow_id|execution_id|captured_at). compile_target is intentionally NOT part of the id so the three reference compilers re-derive byte-identical bytes from the same primitive output (the byte-parity contract the F-WF-PATCH CORE-FANOUT siblings assert against). The record carries the update subject, the advisory reference, the classified criticality (or the unclassified sentinel on the short-circuit branch), the staged ring id, the canary health outcome and the closed health-observations block, the broad rollout id (or the empty wire shape with the canary_unhealthy skip marker on the unhealthy-canary branch), and the dated capture timestamp. The skip-marker invariant and the canary_healthy <-> gate-combination invariant are enforced at the primitive boundary so an inconsistent record fails loud here rather than at the schema-validation boundary downstream. This is the audit-evident artifact NIS2 Art. 21(2)(e) reviewers read against a maintenance / patch-rollout obligation; missing or stale evidence is the failure mode the maintenance metrics surface. The primitive only produces the JSON-native record; the durable emitter wiring (artifact-path, content-addressed filename, atomic write) is owned by the per-target compilers and lands with the CORE-FANOUT sibling cards.

    CACAO step_id: action--70000000-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--70000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'evidence capture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evidence_capture'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--70000000-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'evidence capture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evidence_capture'})
        )
        from content.playbooks.patch_management.primitives.artifact import build_patch_application_evidence_artifact
        __evidence_id__ = build_patch_application_evidence_artifact(workflow_id=__workflow_id__, execution_id=__execution_id__, regulation_refs=__regulation_refs__, control_refs=__control_refs__, update_subject=__update_subject__, update_reference=__update_reference__, patch_criticality=__patch_criticality__, staged_ring_id=__staged_ring_id__, canary_healthy=__canary_healthy__, broad_rollout_id=__broad_rollout_id__, health_observations=__health_observations__, captured_at=__captured_at__, source_url=__source_url__)

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
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 'notify maintenance owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_maintenance_owner'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--70000000-0000-4000-8000-000000000008', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 'notify maintenance owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_maintenance_owner'})
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
    content_version   : 0.2.0
    maturity          : experimental
    workflow_start    : start--70000000-0000-4000-8000-000000000001
    activities        : detect_patch_availability, classify_patch_criticality, stage_rollout_to_canary_ring, validate_canary, fan_out_to_broad_rings, evidence_capture, notify_maintenance_owner
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.patch_management@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.2.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.patch_management@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.playbook.version': '0.2.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.patch_management@v1'"
            )

WORKFLOW = PlaybookPatchManagementV1Workflow
ACTIVITIES = (detect_patch_availability, classify_patch_criticality, stage_rollout_to_canary_ring, validate_canary, fan_out_to_broad_rings, evidence_capture, notify_maintenance_owner,)
RETRY_POLICIES = (DETECT_PATCH_AVAILABILITY_RETRY_POLICY, CLASSIFY_PATCH_CRITICALITY_RETRY_POLICY, STAGE_ROLLOUT_TO_CANARY_RING_RETRY_POLICY, VALIDATE_CANARY_RETRY_POLICY, FAN_OUT_TO_BROAD_RINGS_RETRY_POLICY, EVIDENCE_CAPTURE_RETRY_POLICY, NOTIFY_MAINTENANCE_OWNER_RETRY_POLICY,)
