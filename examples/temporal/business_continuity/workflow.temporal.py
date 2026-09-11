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
async def detect_and_declare_bcm_event(raw_trigger: dict[str, object]) -> dict[str, object]:
    """Receive a business-continuity trigger on the operator's declared event-declaration surface — a major-outage escalation from the incident-management lane, a ransomware-containment escalation from the containment lane, an upstream-dependency failure signal, or a facility-loss declaration: declaration.declare_bcm_event validates the adapter's __raw_trigger__ against the closed trigger-class vocabulary, canonicalises the affected service and the escalating lane's source reference as role-shaped pointers, anchors the NIS2 Art. 23 clock on the supplied declared_ts (a Zulu instant the declaring surface stamped — never a clock read inside the primitive) and derives __event_id__ from the trigger content so the same escalation re-received resolves to the same event. Bound since the CORE-WIRE card: the binding assigns the event envelope to __bcm_event__ and the compile target's adapter extracts __event_id__ and __event_declared_ts__ — the marshalling seam every bound playbook documents. The step's API Activity milestone record is composed at the telemetry seam by primitives.milestones.compose_milestone_record, keyed to the event id.

    CACAO step_id: action--b17c0072-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--b17c0072-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect_and_declare_bcm_event', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_and_declare_bcm_event'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--b17c0072-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect_and_declare_bcm_event', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_and_declare_bcm_event'})
        )
        from content.playbooks.business_continuity.primitives.declaration import declare_bcm_event
        __bcm_event__ = declare_bcm_event(raw_trigger=__raw_trigger__)

DETECT_AND_DECLARE_BCM_EVENT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def activate_bcm_plan(bcm_event: dict[str, object], plan_register: dict[str, object], significance_policy: dict[str, object]) -> dict[str, object]:
    """Activate the documented BCM plan for the affected service, or record its absence: activation.activate_bcm_plan resolves the service against the operator's __plan_register__ (a duplicated row fails loud; an empty register is legitimate — an operator with no plans on file still declares events), reads the documented isolation targets, failover targets and recovery objectives (RTO / RPO) into the activation envelope, and evaluates the event's trigger class against the declared __significance_policy__ to set __significant_incident__. A continuity event with no plan on file is reported as such (plan_on_file false, plan_ref null) rather than blocking — the downstream isolate, switch and restore bindings read that state and record skips and non-engagement as data. The plan register and the significance policy are operator-owned adapter surfaces. The binding assigns the envelope to __activation__; the adapter extracts __bcm_plan_ref__ and __significant_incident__. The step's API Activity milestone record is composed at the telemetry seam by primitives.milestones.compose_milestone_record, keyed to the event id.

    CACAO step_id: action--b17c0072-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--b17c0072-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000003', 'secops_ng.step.name': 'activate_bcm_plan', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'activate_bcm_plan'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--b17c0072-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000003', 'secops_ng.step.name': 'activate_bcm_plan', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'activate_bcm_plan'})
        )
        from content.playbooks.business_continuity.primitives.activation import activate_bcm_plan
        __activation__ = activate_bcm_plan(event=__bcm_event__, plan_register=__plan_register__, significance_policy=__significance_policy__)

ACTIVATE_BCM_PLAN_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def isolate_affected_systems(activation: dict[str, object]) -> dict[str, object]:
    """Resolve the isolation scope where the activated plan documents one: isolation.resolve_isolation_scope reads the activation envelope's isolation targets and emits the content-derived scope over them; where the plan documents no isolation step for the event class (a pure availability outage with no compromise indicator, for example) — or no plan is on file — the scope is skipped as data (skipped true, empty scope id), which is the empty __isolation_scope__ contract, never a failure. Executing the containment against the operator's isolation surface (network-segmentation controller, IAM revocation surface, upstream-dependency circuit-breaker) is the compile target's adapter. The binding assigns the result to __isolation_result__; the adapter extracts __isolation_scope__. The step's API Activity milestone record is composed at the telemetry seam by primitives.milestones.compose_milestone_record, keyed to the event id.

    CACAO step_id: action--b17c0072-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--b17c0072-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000004', 'secops_ng.step.name': 'isolate_affected_systems', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'isolate_affected_systems'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--b17c0072-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000004', 'secops_ng.step.name': 'isolate_affected_systems', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'isolate_affected_systems'})
        )
        from content.playbooks.business_continuity.primitives.isolation import resolve_isolation_scope
        __isolation_result__ = resolve_isolation_scope(activation=__activation__)

ISOLATE_AFFECTED_SYSTEMS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def switch_to_backup(activation: dict[str, object], isolation_scope: str) -> dict[str, object]:
    """Select the failover engagement for the disaster-recovery leg of the Art. 21(2)(c) triplet: failover.select_failover_target reads the activation envelope and selects the first documented failover target in the plan's preference order, composing the cutover order the failover surface executes; with no plan on file or no documented target the order records failover_engaged false with the not_engaged_reason (no_plan_on_file / no_documented_target) as data rather than blocking. Backup integrity the failover relies on is exercised on the sibling backup_recovery playbook's periodic restore-drill lane. Executing the cutover (backup-site routing, data-replica promotion, standby-capacity activation) is the compile target's adapter. The binding assigns the order to __failover_order__; the adapter extracts __failover_target__ (null when not engaged). The step's API Activity milestone record is composed at the telemetry seam by primitives.milestones.compose_milestone_record, keyed to the event id.

    CACAO step_id: action--b17c0072-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--b17c0072-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000005', 'secops_ng.step.name': 'switch_to_backup', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'switch_to_backup'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--b17c0072-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000005', 'secops_ng.step.name': 'switch_to_backup', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'switch_to_backup'})
        )
        from content.playbooks.business_continuity.primitives.failover import select_failover_target
        __failover_order__ = select_failover_target(activation=__activation__)

SWITCH_TO_BACKUP_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_competent_authority(event_id: str, event_declared_ts: str, significant_incident: bool, notification_phase: str, notification_assessment: dict[str, object], no_notification_rationale: str) -> dict[str, object]:
    """Compose the NIS2 Art. 23 record for the event: notification.compose_authority_notification takes __significant_incident__ and, when true, the __notification_phase__ (early_warning — 24h; incident_notification — 72h; final_report — one calendar month, end-of-month clamped) and the __notification_assessment__ (preliminary assessment, impact scope, cross-border-effect indicator) and composes the notification envelope with its phase deadline derived from __event_declared_ts__; when false, it composes the locally-logged no-notification determination from the required __no_notification_rationale__ (retained for accountability) — the two dispositions are exclusive and the primitive refuses the inputs of the other branch. Delivering the envelope to the competent authority (national cybersecurity authority per the entity's establishment Member State — portal, S/MIME, sector-specific API) is the compile target's adapter. The binding assigns the record to __authority_record__; the adapter extracts __notification_ref__ (empty on the determination branch). The step's Incident Finding milestone record is composed at the telemetry seam by primitives.milestones.compose_incident_finding_record, keyed to the event id.

    CACAO step_id: action--b17c0072-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--b17c0072-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify_competent_authority', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_competent_authority'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--b17c0072-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify_competent_authority', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_competent_authority'})
        )
        from content.playbooks.business_continuity.primitives.notification import compose_authority_notification
        __authority_record__ = compose_authority_notification(assessment=__notification_assessment__, event_declared_ts=__event_declared_ts__, event_id=__event_id__, no_notification_rationale=__no_notification_rationale__, phase=__notification_phase__, significant_incident=__significant_incident__)

NOTIFY_COMPETENT_AUTHORITY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def restore_and_verify(activation: dict[str, object], failover_target: str, recovery_observations: dict[str, object]) -> dict[str, object]:
    """Verify the recovery against the documented objectives, never assert it: recovery.evaluate_recovery reads the activation envelope's recovery objectives (null when no plan is on file — objectives_documented false and the RTO / RPO verdicts recorded as undetermined rather than met) and the adapter's __recovery_observations__ (cutback completed, primary health signal, observed RTO and RPO seconds) and records the signed observed-versus-documented deltas and the recovered verdict. Cutback from __failover_target__, dependency revalidation and the health-signal probe are the compile target's adapter. The binding assigns the record to __recovery_record__; the adapter extracts __recovery_result__. The step's API Activity milestone record is composed at the telemetry seam by primitives.milestones.compose_milestone_record, keyed to the event id.

    CACAO step_id: action--b17c0072-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--b17c0072-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000007', 'secops_ng.step.name': 'restore_and_verify', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'restore_and_verify'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--b17c0072-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000007', 'secops_ng.step.name': 'restore_and_verify', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'restore_and_verify'})
        )
        from content.playbooks.business_continuity.primitives.recovery import evaluate_recovery
        __recovery_record__ = evaluate_recovery(activation=__activation__, observed=__recovery_observations__)

RESTORE_AND_VERIFY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def post_incident_review(event_id: str, activation: dict[str, object], pir_lessons: str, pir_corrective_actions: str, pir_plan_revisions: str, pir_linked_refs: dict[str, object]) -> dict[str, object]:
    """Compose the post-incident-review record: review.compose_pir_record takes the lessons learned (__pir_lessons__ — mandatory; a review without a lesson is not a review), the corrective actions with their owners (__pir_corrective_actions__), any BCM-plan revisions the event surfaced (__pir_plan_revisions__) and the linked references the adapter assembles from the notification or determination, recovery and failover envelopes (__pir_linked_refs__ — empty values dropped, so the no-notification branch joins cleanly), stamps ran_without_plan when the activation found no plan on file, and derives the content-keyed __pir_ref__. Persistence on the operator's evidence store and the retention discipline are the adapter's; the record feeds the accountability posture and any downstream regulator query (Art. 23 final-report supplement, Art. 32 supervisory-authority information request). The binding assigns the record to __pir_record__; the adapter extracts __pir_ref__. The step's Incident Finding milestone record (close) is composed at the telemetry seam by primitives.milestones.compose_incident_finding_record.

    CACAO step_id: action--b17c0072-0000-4000-8000-000000000008
    """
    with _TRACER.start_as_current_span(
        name='activity.action--b17c0072-0000-4000-8000-000000000008',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000008', 'secops_ng.step.name': 'post_incident_review', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'post_incident_review'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--b17c0072-0000-4000-8000-000000000008', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000008', 'secops_ng.step.name': 'post_incident_review', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'post_incident_review'})
        )
        from content.playbooks.business_continuity.primitives.review import compose_pir_record
        __pir_record__ = compose_pir_record(corrective_actions=__pir_corrective_actions__, event_id=__event_id__, lessons_learned=__pir_lessons__, linked_refs=__pir_linked_refs__, plan_on_file=__activation__.plan_on_file, plan_revisions=__pir_plan_revisions__)

POST_INCIDENT_REVIEW_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookBusinessContinuityV1Workflow:
    """CACAO v2 playbook for the operator-side business continuity lifecycle a NIS2 essential or important entity runs when a business- continuity event (major outage, ransomware containment escalation, dependency failure, or facility loss) is declared against an in- scope service. Covers the three discipline surfaces NIS2 Art. 21(2)(c) names — backup management, disaster recovery, and crisis management — as a single continuity envelope. The lifecycle chains seven bound action steps: detect-and-declare-bcm-event → activate- bcm-plan → isolate-affected-systems → switch-to-backup → notify- competent-authority (the NIS2 Art. 23 path where the event crosses the significant-incident threshold; a locally-logged no-notification determination otherwise) → restore-and-verify → post-incident- review. Every action step binds a deterministic primitive under primitives/ (bound since the CORE-WIRE card; stable at content_version 1.0.0): the declaration anchors the Art. 23 clock on the supplied instant, a continuity event with no plan on file is reported as such rather than blocking (skips and non-engagement are data), recovery is verified against observed RTO / RPO rather than asserted, and each lifecycle milestone's OCSF record (API Activity 6003; Incident Finding 2005 at notification and review) is composed by the milestone composers at the telemetry seam, keyed to the event id. The plan register, the isolation and failover surfaces, the competent-authority delivery path and the evidence store are adapter-bound operator surfaces. The periodic non-destructive restore-drill discipline lives on the sibling backup_recovery playbook (both pin nis2:art-21-2-c — plan-lifecycle vs exercise- lifecycle). CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--b17c0072-0000-4000-8000-000000000001
    stable_id         : playbook.business_continuity@v1
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--b17c0072-0000-4000-8000-000000000001
    activities        : detect_and_declare_bcm_event, activate_bcm_plan, isolate_affected_systems, switch_to_backup, notify_competent_authority, restore_and_verify, post_incident_review
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.business_continuity@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.business_continuity@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.business_continuity@v1'"
            )

WORKFLOW = PlaybookBusinessContinuityV1Workflow
ACTIVITIES = (detect_and_declare_bcm_event, activate_bcm_plan, isolate_affected_systems, switch_to_backup, notify_competent_authority, restore_and_verify, post_incident_review,)
RETRY_POLICIES = (DETECT_AND_DECLARE_BCM_EVENT_RETRY_POLICY, ACTIVATE_BCM_PLAN_RETRY_POLICY, ISOLATE_AFFECTED_SYSTEMS_RETRY_POLICY, SWITCH_TO_BACKUP_RETRY_POLICY, NOTIFY_COMPETENT_AUTHORITY_RETRY_POLICY, RESTORE_AND_VERIFY_RETRY_POLICY, POST_INCIDENT_REVIEW_RETRY_POLICY,)
