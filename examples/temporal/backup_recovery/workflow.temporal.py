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
async def detect_restore_drill_trigger(backup_inventory: dict[str, object], backup_scope: str, drill_window: str) -> str:
    """Resolve the trigger for this run: a scheduled drill window matured (cron / Temporal schedule), an operator-initiated drill request landed, or a continuity event up the chain raised the drill cadence. Reads __drill_window__ and __backup_scope__ and selects __candidate_backup_id__ — the most recent backup artifact for the in-scope data set that is eligible for a non-destructive drill against an isolated target.

    CACAO step_id: action--50000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--50000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect restore-drill trigger', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_restore_drill_trigger'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--50000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect restore-drill trigger', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_restore_drill_trigger'})
        )
        from content.playbooks.backup_recovery.primitives.detect import resolve_drill_trigger
        __candidate_backup_id__ = resolve_drill_trigger(drill_window=__drill_window__, backup_scope=__backup_scope__, backup_inventory=__backup_inventory__)

DETECT_RESTORE_DRILL_TRIGGER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def validate_backup_integrity(candidate_backup_id: str, integrity_observation: dict[str, object]) -> bool:
    """Run the documented integrity checks on the candidate backup: checksum / manifest verification, decryption-key availability against the operator's key-management surface, and a presence check against the documented backup-scope inventory (no silently-dropped objects). Sets __integrity_ok__. A false outcome short-circuits the drill into the evidence-capture step (failure attestation) without executing the restore, so the operator's continuity owner is notified of the integrity gap rather than discovering it under real recovery pressure.

    CACAO step_id: action--50000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--50000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'validate backup integrity', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'validate_backup_integrity'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--50000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'validate backup integrity', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'validate_backup_integrity'})
        )
        from content.playbooks.backup_recovery.primitives.integrity import evaluate_backup_integrity
        __integrity_ok__ = evaluate_backup_integrity(candidate_backup_id=__candidate_backup_id__, integrity_observation=__integrity_observation__)

VALIDATE_BACKUP_INTEGRITY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def execute_restore_drill(backup_scope: str, candidate_backup_id: str, drill_observation: dict[str, object]) -> str:
    """Execute the non-destructive restore drill against the operator's documented isolated drill target (not production). Restore the in-scope objects from __candidate_backup_id__, record the observed RTO / RPO against the documented objectives, capture the restored object inventory, and emit __drill_result__. The drill is non-destructive by construction; production state is untouched. Detection bindings for restore-target misconfiguration (restore landing in production, drill target reachable from production network) are owned by CORE-layer cards once upstream rule ids are selected. The drill's dated attestation feeds kpi.restore_drill_attestation_freshness@v1, pinned on this step and on evidence capture since the EXTEND card landed the catalogue wiring.

    CACAO step_id: action--50000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--50000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'execute restore drill', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'execute_restore_drill'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--50000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'execute restore drill', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'execute_restore_drill'})
        )
        from content.playbooks.backup_recovery.primitives.drill import evaluate_restore_drill
        __drill_result__ = evaluate_restore_drill(candidate_backup_id=__candidate_backup_id__, backup_scope=__backup_scope__, drill_observation=__drill_observation__)

EXECUTE_RESTORE_DRILL_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def evidence_capture(backup_scope: str, candidate_backup_id: str, captured_at: str, drill_result: str, execution_id: str, integrity_observation: dict[str, object], integrity_ok: bool, workflow_id: str) -> dict[str, object]:
    """Compose and publish the dated attestation + drill-evidence record to the operator's evidence store. The record carries the candidate backup id, integrity-check outcome, executed drill result (or the failure marker for the short-circuit branch), observed RTO/RPO, restored inventory, and the drill window. This is the audit-evident artifact that NIS2 Art.21(2)(c) and DORA Art.12 reviewers read; missing or stale attestations are the failure mode the metrics surface.

    CACAO step_id: action--50000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--50000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'evidence capture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evidence_capture'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--50000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'evidence capture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evidence_capture'})
        )
        from content.playbooks.backup_recovery.primitives.attestation import build_drill_attestation
        __attestation_id__ = build_drill_attestation(workflow_id=__workflow_id__, execution_id=__execution_id__, captured_at=__captured_at__, backup_scope=__backup_scope__, candidate_backup_id=__candidate_backup_id__, integrity_ok=__integrity_ok__, drill_result=__drill_result__, integrity_observation=__integrity_observation__)

EVIDENCE_CAPTURE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_continuity_owner(attestation_id: dict[str, object], backup_scope: str, owner_binding: dict[str, object]) -> dict[str, object]:
    """Deliver the attestation reference to the continuity owner along the operator's pre-bound channel (ticketing system, chat thread, email). Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently; an attestation written but never delivered to the owner is itself a continuity gap.

    CACAO step_id: action--50000000-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--50000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify continuity owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_continuity_owner'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--50000000-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify continuity owner', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_continuity_owner'})
        )
        from content.playbooks.backup_recovery.primitives.notify import compose_continuity_notification
        __continuity_notification__ = compose_continuity_notification(attestation=__attestation_id__, backup_scope=__backup_scope__, owner_binding=__owner_binding__)

NOTIFY_CONTINUITY_OWNER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookBackupRecoveryV1Workflow:
    """Exercise the business-continuity surface: on a scheduled or operator-triggered restore-drill window, validate the integrity of the most recent in-scope backup, execute a non-destructive restore drill against an isolated target, capture the dated attestation and drill evidence, and notify the continuity owner. The playbook is the operationalisation of a documented backup policy and recovery procedure; it does not author the policy itself. CORE layer: every action step carries a core_body binding onto the deterministic primitives under primitives/ (drill-trigger resolution, integrity evaluation, restore-drill evaluation, attestation build, notification composition); operator observations arrive as external playbook variables so the primitives stay pure and replayable. Worked examples and byte-parity goldens ship for all three compile targets. The metric_refs pin the catalogue entry kpi.backup_integrity_pass_rate@v1 that already ships under content/metrics/; an EXTEND sibling adds restore-drill-cadence and integrity-failure KRI catalogue entries and re-pins step-level refs against them. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba
    stable_id         : playbook.backup_recovery@v1
    content_version   : 0.2.0
    maturity          : experimental
    workflow_start    : start--50000000-0000-4000-8000-000000000001
    activities        : detect_restore_drill_trigger, validate_backup_integrity, execute_restore_drill, evidence_capture, notify_continuity_owner
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.backup_recovery@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.playbook.version': '0.2.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.backup_recovery@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.playbook.version': '0.2.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.backup_recovery@v1'"
            )

WORKFLOW = PlaybookBackupRecoveryV1Workflow
ACTIVITIES = (detect_restore_drill_trigger, validate_backup_integrity, execute_restore_drill, evidence_capture, notify_continuity_owner,)
RETRY_POLICIES = (DETECT_RESTORE_DRILL_TRIGGER_RETRY_POLICY, VALIDATE_BACKUP_INTEGRITY_RETRY_POLICY, EXECUTE_RESTORE_DRILL_RETRY_POLICY, EVIDENCE_CAPTURE_RETRY_POLICY, NOTIFY_CONTINUITY_OWNER_RETRY_POLICY,)
