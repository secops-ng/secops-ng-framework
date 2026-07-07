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
async def detect_and_declare_bcm_event() -> dict[str, object]:
    """SKELETON — receive a business-continuity trigger on the operator's declared event-declaration surface (major outage escalation from the incident-management lane, ransomware containment escalation from the containment lane, upstream-dependency failure signal, or facility- loss declaration). Assign __event_id__ and stamp __event_declared_ts__ against the NIS2 Art. 23 clock. TODO (CORE): pin the trigger-surface adapter shape and the initial evidence-capture record.

    CACAO step_id: action--b17c0072-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--b17c0072-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect_and_declare_bcm_event', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_and_declare_bcm_event'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--b17c0072-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect_and_declare_bcm_event', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_and_declare_bcm_event'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--b17c0072-0000-4000-8000-000000000002'"
        )

DETECT_AND_DECLARE_BCM_EVENT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def activate_bcm_plan(event_id: str) -> dict[str, object]:
    """SKELETON — retrieve the documented BCM plan artifact for the affected service from the operator's BCM-plan store and activate it. Reads the documented isolation targets, failover targets, and recovery objectives (RTO / RPO) into workflow state. Evaluates the event against the operator's declared significance-threshold policy and sets __significant_incident__ accordingly. TODO (CORE): pin the BCM-plan store adapter, the plan-artifact schema, and the significance-threshold evaluator.

    CACAO step_id: action--b17c0072-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--b17c0072-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000003', 'secops_ng.step.name': 'activate_bcm_plan', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'activate_bcm_plan'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--b17c0072-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000003', 'secops_ng.step.name': 'activate_bcm_plan', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'activate_bcm_plan'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--b17c0072-0000-4000-8000-000000000003'"
        )

ACTIVATE_BCM_PLAN_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def isolate_affected_systems(event_id: str, bcm_plan_ref: str) -> str:
    """SKELETON — where the event and the activated plan call for it, contain the failure surface by isolating the affected primary systems, network segments, or upstream dependencies against the operator's isolation surface per __bcm_plan_ref__. Records __isolation_scope__ for the downstream recovery-and-verification cutback discipline. Skipped (empty __isolation_scope__) where the plan documents no isolation step for the event class (e.g. a pure availability outage with no compromise indicator). TODO (CORE): pin the isolation-surface adapter and the isolation-scope schema.

    CACAO step_id: action--b17c0072-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--b17c0072-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000004', 'secops_ng.step.name': 'isolate_affected_systems', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'isolate_affected_systems'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--b17c0072-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000004', 'secops_ng.step.name': 'isolate_affected_systems', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'isolate_affected_systems'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--b17c0072-0000-4000-8000-000000000004'"
        )

ISOLATE_AFFECTED_SYSTEMS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def switch_to_backup(event_id: str, bcm_plan_ref: str, isolation_scope: str) -> str:
    """SKELETON — failover the affected service to the documented backup site, data replica, or standby capacity per __bcm_plan_ref__. The failover is the disaster- recovery leg of the Art. 21(2)(c) triplet (backup + disaster recovery + crisis management); backup integrity the failover reads is exercised on the sibling backup_recovery playbook's periodic restore-drill lane. Records __failover_target__ for the downstream restore-and-verify cutback discipline. TODO (CORE): pin the failover-surface adapter, the recovery-objective evaluator (observed vs documented RTO / RPO), and the cutover-evidence record.

    CACAO step_id: action--b17c0072-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--b17c0072-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000005', 'secops_ng.step.name': 'switch_to_backup', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'switch_to_backup'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--b17c0072-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000005', 'secops_ng.step.name': 'switch_to_backup', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'switch_to_backup'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--b17c0072-0000-4000-8000-000000000005'"
        )

SWITCH_TO_BACKUP_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_competent_authority(event_id: str, event_declared_ts: str, significant_incident: bool) -> str:
    """SKELETON — where __significant_incident__ is true, dispatch the NIS2 Art. 23 significant-incident notification to the operator's competent authority (national cybersecurity authority per the entity's establishment Member State) on the Art. 23 timeline: 24h early warning, 72h incident notification, one-month final report. The envelope carries __event_id__, __event_declared_ts__, the preliminary assessment, the impact scope, and the cross- border-effect indicator. Where __significant_incident__ is false, the step records a locally-logged no-notification determination (retained for accountability) and short-circuits to restore-and-verify. Records __notification_ref__ for the post-incident-review record. TODO (CORE): pin the competent-authority adapter (per-Member- State delivery surface), the Art. 23 envelope templates (early-warning, incident-notification, final-report), and the significance-determination evidence discipline.

    CACAO step_id: action--b17c0072-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--b17c0072-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify_competent_authority', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_competent_authority'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--b17c0072-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify_competent_authority', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_competent_authority'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--b17c0072-0000-4000-8000-000000000006'"
        )

NOTIFY_COMPETENT_AUTHORITY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def restore_and_verify(event_id: str, bcm_plan_ref: str, failover_target: str) -> str:
    """SKELETON — return the primary service to a known-good state per __bcm_plan_ref__ (cutback from __failover_target__ where applicable, dependency revalidation, and health-signal check against the documented recovery objectives). Records __recovery_result__ with the observed RTO / RPO delta against the documented objectives and the primary-service health signal. TODO (CORE): pin the health-signal adapter, the cutback procedure, and the recovery-attestation evidence discipline.

    CACAO step_id: action--b17c0072-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--b17c0072-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000007', 'secops_ng.step.name': 'restore_and_verify', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'restore_and_verify'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--b17c0072-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000007', 'secops_ng.step.name': 'restore_and_verify', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'restore_and_verify'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--b17c0072-0000-4000-8000-000000000007'"
        )

RESTORE_AND_VERIFY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def post_incident_review(event_id: str, recovery_result: str, notification_ref: str) -> str:
    """SKELETON — persist the post-incident-review record for the event: lessons learned, corrective actions, and any BCM-plan revisions surfaced by the event. Records __pir_ref__ on the operator's evidence store keyed to __event_id__. Feeds the operator's accountability posture and any downstream regulator query (Art. 23 final-report supplement, Art. 32 supervisory-authority information request). TODO (CORE): pin the PIR record schema, the evidence-store retention discipline, and the BCM-plan revision handoff.

    CACAO step_id: action--b17c0072-0000-4000-8000-000000000008
    """
    with _TRACER.start_as_current_span(
        name='activity.action--b17c0072-0000-4000-8000-000000000008',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000008', 'secops_ng.step.name': 'post_incident_review', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'post_incident_review'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--b17c0072-0000-4000-8000-000000000008', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000008', 'secops_ng.step.name': 'post_incident_review', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'post_incident_review'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--b17c0072-0000-4000-8000-000000000008'"
        )

POST_INCIDENT_REVIEW_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookBusinessContinuityV1Workflow:
    """SKELETON — CACAO v2 scaffold for the operator-side business continuity lifecycle a NIS2 essential or important entity runs when a business-continuity event (major outage, ransomware containment escalation, dependency failure, or facility loss) is declared against an in-scope service. Covers the three discipline surfaces NIS2 Art. 21(2)(c) names — backup management, disaster recovery, and crisis management — as a single continuity envelope. The lifecycle chains seven steps: detect-and-declare-bcm-event → activate-bcm-plan (retrieve and activate the documented BCM plan artifact) → isolate-affected-systems (contain the failure surface where applicable) → switch-to-backup (failover to the documented backup site, data replica, or standby capacity) → notify-competent-authority (NIS2 Art. 23 significant-incident reporting path where the event crosses the significant- incident threshold) → restore-and-verify (return the primary service to a known-good state and validate) → post-incident-review (lessons-learned record for the operator's Art. 5(2)-equivalent accountability posture and any regulator query). This SKELETON scaffolds the plan-lifecycle side of the continuity surface; the periodic non-destructive restore-drill discipline that continuously exercises the backup-and-recovery apparatus lives on the sibling backup_recovery playbook (both pin nis2:art-21-2-c and co-anchor the clause, plan-lifecycle vs exercise-lifecycle). A sibling CORE card lands the full workflow logic (adapter bindings for the BCM-plan store, isolation surface, failover surface, and NCA notification path); a sibling EXTEND card lands the cookbook walkthrough and advanced features.

    CACAO playbook id : playbook--b17c0072-0000-4000-8000-000000000001
    stable_id         : playbook.business_continuity@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--b17c0072-0000-4000-8000-000000000001
    activities        : detect_and_declare_bcm_event, activate_bcm_plan, isolate_affected_systems, switch_to_backup, notify_competent_authority, restore_and_verify, post_incident_review
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.business_continuity@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.business_continuity@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.business_continuity@v1'"
            )

WORKFLOW = PlaybookBusinessContinuityV1Workflow
ACTIVITIES = (detect_and_declare_bcm_event, activate_bcm_plan, isolate_affected_systems, switch_to_backup, notify_competent_authority, restore_and_verify, post_incident_review,)
RETRY_POLICIES = (DETECT_AND_DECLARE_BCM_EVENT_RETRY_POLICY, ACTIVATE_BCM_PLAN_RETRY_POLICY, ISOLATE_AFFECTED_SYSTEMS_RETRY_POLICY, SWITCH_TO_BACKUP_RETRY_POLICY, NOTIFY_COMPETENT_AUTHORITY_RETRY_POLICY, RESTORE_AND_VERIFY_RETRY_POLICY, POST_INCIDENT_REVIEW_RETRY_POLICY,)
