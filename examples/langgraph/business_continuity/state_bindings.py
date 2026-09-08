# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.business_continuity@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookBusinessContinuityV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.business_continuity@v1.

    Playbook id: playbook--b17c0072-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __activation__
    # Activation envelope composed by activation.activate_bcm_plan: event_id, plan_on_file, plan_ref, isolation_targets, failover_targets, recovery_objectives (null without a plan), significant_incident. The adapter extracts __bcm_plan_ref__ and __significant_incident__; the isolate, switch, restore and review bindings read it.
    activation: dict[str, object]
    # playbook_variable: __authority_record__
    # The Art. 23 record composed by notification.compose_authority_notification — one of two exclusive shapes: disposition notification (notification_ref, phase, phase_deadline, assessment fields) or disposition no_notification_determination (determination_ref, rationale). Delivered by the competent-authority adapter; the adapter extracts __notification_ref__.
    authority_record: dict[str, object]
    # playbook_variable: __bcm_event__
    # Event envelope composed by declaration.declare_bcm_event: event_id (bcm-..., content-derived), trigger_class, affected_service, source_ref, event_declared_ts. The adapter extracts __event_id__ and __event_declared_ts__; the activation binding consumes the whole envelope.
    bcm_event: dict[str, object]
    # playbook_variable: __bcm_plan_ref__
    # Reference to the activated BCM plan artifact resolved from the operator's BCM-plan store. Enumerates the documented isolation targets, failover targets, and recovery objectives (RTO / RPO) the workflow reads at switch-to-backup and restore-and-verify. Extracted at the adapter seam from __activation__.plan_ref; null when no plan is on file (reported, not blocking).
    bcm_plan_ref: str
    # playbook_variable: __event_declared_ts__
    # ISO 8601 timestamp of the business-continuity event declaration. Anchors the NIS2 Art. 23 24h early-warning / 72h incident- notification / 1-month final-report clock when the significant- incident threshold is crossed. Supplied on the raw trigger by the declaring surface and extracted at the adapter seam from __bcm_event__.event_declared_ts.
    event_declared_ts: str
    # playbook_variable: __event_id__
    # Business-continuity event identifier assigned at declaration. Correlation key across activate, isolate, switch-to-backup, notify, restore-and-verify, and post-incident-review so a reviewer can join the full continuity lifecycle into a single reportable-event ledger keyed to the operator's accountability surface. Extracted at the compile target's adapter seam from __bcm_event__.event_id.
    event_id: str
    # playbook_variable: __failover_order__
    # Failover order composed by failover.select_failover_target: event_id, failover_engaged, failover_ref, failover_target, not_engaged_reason, cutover_order. Executed by the failover adapter; the adapter extracts __failover_target__.
    failover_order: dict[str, object]
    # playbook_variable: __failover_target__
    # Reference to the failover target resolved by switch-to-backup against __bcm_plan_ref__ (the documented backup site, data replica, or standby capacity the service is switched to). Feeds restore-and-verify for the cutback validation. Extracted at the adapter seam from __failover_order__.failover_target; null when failover is not engaged (the order carries not_engaged_reason).
    failover_target: str
    # playbook_variable: __isolation_result__
    # Isolation scope composed by isolation.resolve_isolation_scope: event_id, scope_id (bcm-iso-... or empty), skipped, targets. Executed by the isolation adapter; the adapter extracts __isolation_scope__.
    isolation_result: dict[str, object]
    # playbook_variable: __isolation_scope__
    # Reference to the isolation scope resolved by isolate-affected- systems against __bcm_plan_ref__ (the affected primary systems, network segments, or upstream dependencies contained to prevent cascade). Empty when the event does not require isolation. Extracted at the adapter seam from __isolation_result__.scope_id; empty when the plan documents no isolation step (skipped as data).
    isolation_scope: str
    # playbook_variable: __no_notification_rationale__
    # The non-empty rationale for the locally-logged no-notification determination when the event does not cross the significance threshold; null when it does. Retained for accountability. Consumed by notification.compose_authority_notification.
    no_notification_rationale: str
    # playbook_variable: __notification_assessment__
    # The controller's assessment carried on a significant-incident notification: preliminary_assessment and impact_scope (non-empty text, carried opaquely) and cross_border_effect (real boolean). Null when the event is not significant. Consumed by notification.compose_authority_notification.
    notification_assessment: dict[str, object]
    # playbook_variable: __notification_phase__
    # Which Art. 23 phase the record is composed for when the event is significant: early_warning (24h), incident_notification (72h) or final_report (one calendar month). Null when the event is not significant — the primitive refuses a phase on the determination branch. Consumed by notification.compose_authority_notification.
    notification_phase: str
    # playbook_variable: __notification_ref__
    # Reference to the NIS2 Art. 23 notification artifact emitted by notify-competent-authority when the event crosses the significant-incident threshold. Empty otherwise. Extracted at the adapter seam from __authority_record__.notification_ref; empty on the no-notification-determination branch.
    notification_ref: str
    # playbook_variable: __pir_corrective_actions__
    # JSON-native list of corrective-action records for review.compose_pir_record, each with action (non-empty text) and owner_ref (role-shaped); may be empty.
    pir_corrective_actions: str
    # playbook_variable: __pir_lessons__
    # JSON-native list of the non-empty lessons-learned texts for review.compose_pir_record; at least one is mandatory.
    pir_lessons: str
    # playbook_variable: __pir_linked_refs__
    # Role-shaped references the adapter assembles onto the review record, keyed by name: the notification or determination ref from __authority_record__, recovery_ref from __recovery_record__, failover_ref from __failover_order__. Empty-string values are dropped so the no-notification branch joins cleanly. Consumed by review.compose_pir_record.
    pir_linked_refs: dict[str, object]
    # playbook_variable: __pir_plan_revisions__
    # JSON-native list of the BCM-plan revision texts the event surfaced, for review.compose_pir_record; may be empty.
    pir_plan_revisions: str
    # playbook_variable: __pir_record__
    # Post-incident-review record composed by review.compose_pir_record: pir_ref (bcm-pir-...), event_id, markers (ran_without_plan when applicable), lessons_learned, corrective_actions, plan_revisions, linked_refs. Persisted by the evidence-store adapter; the adapter extracts __pir_ref__.
    pir_record: dict[str, object]
    # playbook_variable: __pir_ref__
    # Reference to the post-incident-review record persisted at post- incident-review. The audit-evident record of lessons learned, corrective actions, and BCM-plan revisions the operator's accountability posture reads. Extracted at the adapter seam from __pir_record__.pir_ref.
    pir_ref: str
    # playbook_variable: __plan_register__
    # The operator's BCM-plan register handed over by the plan-store adapter: plans — rows with service, plan_ref, isolation_targets, failover_targets (either list may be empty) and rto_seconds / rpo_seconds. The list may be empty: an operator with no plans on file still declares events. Consumed by activation.activate_bcm_plan.
    plan_register: dict[str, object]
    # playbook_variable: __raw_trigger__
    # Trigger record handed over by the declaring surface for declaration.declare_bcm_event: trigger_class (major_outage_escalation | ransomware_containment_escalation | upstream_dependency_failure | facility_loss_declaration), affected_service (role-shaped), source_ref (the escalating lane's record), declared_ts (Zulu instant — the Art. 23 anchor).
    raw_trigger: dict[str, object]
    # playbook_variable: __recovery_observations__
    # The adapter's observations across the recovery for recovery.evaluate_recovery: cutback_completed and primary_health_ok (real booleans), observed_rto_seconds and observed_rpo_seconds (non-negative integers). Recovery is verified against these observations, never asserted.
    recovery_observations: dict[str, object]
    # playbook_variable: __recovery_record__
    # Recovery record composed by recovery.evaluate_recovery: recovery_ref, event_id, objectives_documented, rto and rpo (observed, documented, signed delta, met), cutback_completed, primary_health_ok, recovered. The adapter extracts __recovery_result__.
    recovery_record: dict[str, object]
    # playbook_variable: __recovery_result__
    # Reference to the recovery-and-verification result produced by restore-and-verify — the observed RTO / RPO against the documented objectives, the primary-service health signal, and the cutback outcome. Feeds post-incident-review. Extracted at the adapter seam from __recovery_record__.recovery_ref.
    recovery_result: str
    # playbook_variable: __significance_policy__
    # The entity's declared NIS2 Art. 23 significance-threshold policy: significant_trigger_classes — the trigger classes that cross the threshold (possibly empty). Entity- and sector- specific; the framework does not prescribe it. Consumed by activation.activate_bcm_plan.
    significance_policy: dict[str, object]
    # playbook_variable: __significant_incident__
    # Whether the event crosses the NIS2 Art. 23 significant- incident threshold. When true, notify-competent-authority dispatches the Art. 23 24h early warning; when false, the notify step short- circuits to a locally-logged no-notification record. Set at activate-bcm-plan against the operator's declared significance- threshold policy. Extracted at the adapter seam from __activation__.significant_incident.
    significant_incident: bool
    # bookkeeping
    # Per-step status map keyed by CACAO step_id. Conventional values: 'pending', 'running', 'ok', 'failed', 'awaiting-human'. The graph builder writes here; conditional-edge routers read it.
    step_status: dict[str, str]
    # bookkeeping
    # Accumulated error messages from failed steps. Use a reducer that appends (e.g. operator.add) when wiring into StateGraph.
    errors: list[str]
    # bookkeeping
    # LangGraph/LangChain message channel for the agentic-extension surface. An LLM-driven node reads/writes here; non-LLM playbooks leave it empty.
    messages: Annotated[list[AnyMessage], add_messages]

@tool
async def detect_and_declare_bcm_event(raw_trigger: dict[str, object]) -> dict[str, object]:
    """Receive a business-continuity trigger on the operator's declared event-declaration surface — a major-outage escalation from the incident-management lane, a ransomware-containment escalation from the containment lane, an upstream-dependency failure signal, or a facility-loss declaration: declaration.declare_bcm_event validates the adapter's __raw_trigger__ against the closed trigger-class vocabulary, canonicalises the affected service and the escalating lane's source reference as role-shaped pointers, anchors the NIS2 Art. 23 clock on the supplied declared_ts (a Zulu instant the declaring surface stamped — never a clock read inside the primitive) and derives __event_id__ from the trigger content so the same escalation re-received resolves to the same event. Bound since the CORE-WIRE card: the binding assigns the event envelope to __bcm_event__ and the compile target's adapter extracts __event_id__ and __event_declared_ts__ — the marshalling seam every bound playbook documents. The step's API Activity milestone record is composed at the telemetry seam by primitives.milestones.compose_milestone_record, keyed to the event id.

    CACAO step_id : action--b17c0072-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--b17c0072-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect_and_declare_bcm_event', 'secops_ng.tool.name': 'detect_and_declare_bcm_event', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--b17c0072-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect_and_declare_bcm_event', 'secops_ng.tool.name': 'detect_and_declare_bcm_event', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.business_continuity.primitives.declaration import declare_bcm_event
        __bcm_event__ = declare_bcm_event(raw_trigger=__raw_trigger__)

@tool
async def activate_bcm_plan(bcm_event: dict[str, object], plan_register: dict[str, object], significance_policy: dict[str, object]) -> dict[str, object]:
    """Activate the documented BCM plan for the affected service, or record its absence: activation.activate_bcm_plan resolves the service against the operator's __plan_register__ (a duplicated row fails loud; an empty register is legitimate — an operator with no plans on file still declares events), reads the documented isolation targets, failover targets and recovery objectives (RTO / RPO) into the activation envelope, and evaluates the event's trigger class against the declared __significance_policy__ to set __significant_incident__. A continuity event with no plan on file is reported as such (plan_on_file false, plan_ref null) rather than blocking — the downstream isolate, switch and restore bindings read that state and record skips and non-engagement as data. The plan register and the significance policy are operator-owned adapter surfaces. The binding assigns the envelope to __activation__; the adapter extracts __bcm_plan_ref__ and __significant_incident__. The step's API Activity milestone record is composed at the telemetry seam by primitives.milestones.compose_milestone_record, keyed to the event id.

    CACAO step_id : action--b17c0072-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--b17c0072-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000003', 'secops_ng.step.name': 'activate_bcm_plan', 'secops_ng.tool.name': 'activate_bcm_plan', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--b17c0072-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000003', 'secops_ng.step.name': 'activate_bcm_plan', 'secops_ng.tool.name': 'activate_bcm_plan', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.business_continuity.primitives.activation import activate_bcm_plan
        __activation__ = activate_bcm_plan(event=__bcm_event__, plan_register=__plan_register__, significance_policy=__significance_policy__)

@tool
async def isolate_affected_systems(activation: dict[str, object]) -> dict[str, object]:
    """Resolve the isolation scope where the activated plan documents one: isolation.resolve_isolation_scope reads the activation envelope's isolation targets and emits the content-derived scope over them; where the plan documents no isolation step for the event class (a pure availability outage with no compromise indicator, for example) — or no plan is on file — the scope is skipped as data (skipped true, empty scope id), which is the empty __isolation_scope__ contract, never a failure. Executing the containment against the operator's isolation surface (network-segmentation controller, IAM revocation surface, upstream-dependency circuit-breaker) is the compile target's adapter. The binding assigns the result to __isolation_result__; the adapter extracts __isolation_scope__. The step's API Activity milestone record is composed at the telemetry seam by primitives.milestones.compose_milestone_record, keyed to the event id.

    CACAO step_id : action--b17c0072-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--b17c0072-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000004', 'secops_ng.step.name': 'isolate_affected_systems', 'secops_ng.tool.name': 'isolate_affected_systems', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--b17c0072-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000004', 'secops_ng.step.name': 'isolate_affected_systems', 'secops_ng.tool.name': 'isolate_affected_systems', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.business_continuity.primitives.isolation import resolve_isolation_scope
        __isolation_result__ = resolve_isolation_scope(activation=__activation__)

@tool
async def switch_to_backup(activation: dict[str, object], isolation_scope: str) -> dict[str, object]:
    """Select the failover engagement for the disaster-recovery leg of the Art. 21(2)(c) triplet: failover.select_failover_target reads the activation envelope and selects the first documented failover target in the plan's preference order, composing the cutover order the failover surface executes; with no plan on file or no documented target the order records failover_engaged false with the not_engaged_reason (no_plan_on_file / no_documented_target) as data rather than blocking. Backup integrity the failover relies on is exercised on the sibling backup_recovery playbook's periodic restore-drill lane. Executing the cutover (backup-site routing, data-replica promotion, standby-capacity activation) is the compile target's adapter. The binding assigns the order to __failover_order__; the adapter extracts __failover_target__ (null when not engaged). The step's API Activity milestone record is composed at the telemetry seam by primitives.milestones.compose_milestone_record, keyed to the event id.

    CACAO step_id : action--b17c0072-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--b17c0072-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000005', 'secops_ng.step.name': 'switch_to_backup', 'secops_ng.tool.name': 'switch_to_backup', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--b17c0072-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000005', 'secops_ng.step.name': 'switch_to_backup', 'secops_ng.tool.name': 'switch_to_backup', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.business_continuity.primitives.failover import select_failover_target
        __failover_order__ = select_failover_target(activation=__activation__)

@tool
async def notify_competent_authority(event_id: str, event_declared_ts: str, significant_incident: bool, notification_phase: str, notification_assessment: dict[str, object], no_notification_rationale: str) -> dict[str, object]:
    """Compose the NIS2 Art. 23 record for the event: notification.compose_authority_notification takes __significant_incident__ and, when true, the __notification_phase__ (early_warning — 24h; incident_notification — 72h; final_report — one calendar month, end-of-month clamped) and the __notification_assessment__ (preliminary assessment, impact scope, cross-border-effect indicator) and composes the notification envelope with its phase deadline derived from __event_declared_ts__; when false, it composes the locally-logged no-notification determination from the required __no_notification_rationale__ (retained for accountability) — the two dispositions are exclusive and the primitive refuses the inputs of the other branch. Delivering the envelope to the competent authority (national cybersecurity authority per the entity's establishment Member State — portal, S/MIME, sector-specific API) is the compile target's adapter. The binding assigns the record to __authority_record__; the adapter extracts __notification_ref__ (empty on the determination branch). The step's Incident Finding milestone record is composed at the telemetry seam by primitives.milestones.compose_incident_finding_record, keyed to the event id.

    CACAO step_id : action--b17c0072-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--b17c0072-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify_competent_authority', 'secops_ng.tool.name': 'notify_competent_authority', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--b17c0072-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify_competent_authority', 'secops_ng.tool.name': 'notify_competent_authority', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.business_continuity.primitives.notification import compose_authority_notification
        __authority_record__ = compose_authority_notification(assessment=__notification_assessment__, event_declared_ts=__event_declared_ts__, event_id=__event_id__, no_notification_rationale=__no_notification_rationale__, phase=__notification_phase__, significant_incident=__significant_incident__)

@tool
async def restore_and_verify(activation: dict[str, object], failover_target: str, recovery_observations: dict[str, object]) -> dict[str, object]:
    """Verify the recovery against the documented objectives, never assert it: recovery.evaluate_recovery reads the activation envelope's recovery objectives (null when no plan is on file — objectives_documented false and the RTO / RPO verdicts recorded as undetermined rather than met) and the adapter's __recovery_observations__ (cutback completed, primary health signal, observed RTO and RPO seconds) and records the signed observed-versus-documented deltas and the recovered verdict. Cutback from __failover_target__, dependency revalidation and the health-signal probe are the compile target's adapter. The binding assigns the record to __recovery_record__; the adapter extracts __recovery_result__. The step's API Activity milestone record is composed at the telemetry seam by primitives.milestones.compose_milestone_record, keyed to the event id.

    CACAO step_id : action--b17c0072-0000-4000-8000-000000000007
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--b17c0072-0000-4000-8000-000000000007',
        attributes={'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000007', 'secops_ng.step.name': 'restore_and_verify', 'secops_ng.tool.name': 'restore_and_verify', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--b17c0072-0000-4000-8000-000000000007', attributes={'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000007', 'secops_ng.step.name': 'restore_and_verify', 'secops_ng.tool.name': 'restore_and_verify', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.business_continuity.primitives.recovery import evaluate_recovery
        __recovery_record__ = evaluate_recovery(activation=__activation__, observed=__recovery_observations__)

@tool
async def post_incident_review(event_id: str, activation: dict[str, object], pir_lessons: str, pir_corrective_actions: str, pir_plan_revisions: str, pir_linked_refs: dict[str, object]) -> dict[str, object]:
    """Compose the post-incident-review record: review.compose_pir_record takes the lessons learned (__pir_lessons__ — mandatory; a review without a lesson is not a review), the corrective actions with their owners (__pir_corrective_actions__), any BCM-plan revisions the event surfaced (__pir_plan_revisions__) and the linked references the adapter assembles from the notification or determination, recovery and failover envelopes (__pir_linked_refs__ — empty values dropped, so the no-notification branch joins cleanly), stamps ran_without_plan when the activation found no plan on file, and derives the content-keyed __pir_ref__. Persistence on the operator's evidence store and the retention discipline are the adapter's; the record feeds the accountability posture and any downstream regulator query (Art. 23 final-report supplement, Art. 32 supervisory-authority information request). The binding assigns the record to __pir_record__; the adapter extracts __pir_ref__. The step's Incident Finding milestone record (close) is composed at the telemetry seam by primitives.milestones.compose_incident_finding_record.

    CACAO step_id : action--b17c0072-0000-4000-8000-000000000008
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--b17c0072-0000-4000-8000-000000000008',
        attributes={'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000008', 'secops_ng.step.name': 'post_incident_review', 'secops_ng.tool.name': 'post_incident_review', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--b17c0072-0000-4000-8000-000000000008', attributes={'secops_ng.playbook.id': 'playbook--b17c0072-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--b17c0072-0000-4000-8000-000000000008', 'secops_ng.step.name': 'post_incident_review', 'secops_ng.tool.name': 'post_incident_review', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.business_continuity.primitives.review import compose_pir_record
        __pir_record__ = compose_pir_record(corrective_actions=__pir_corrective_actions__, event_id=__event_id__, lessons_learned=__pir_lessons__, linked_refs=__pir_linked_refs__, plan_on_file=__activation__.plan_on_file, plan_revisions=__pir_plan_revisions__)

async def llm_step(state: PlaybookBusinessContinuityV1State) -> dict:
    """Agentic-extension hook.

    Insert this function (or a variant) as a LangGraph node when a
    CACAO action step should be driven by an LLM with tool-calling
    rather than by a hand-written activity.

    Contract:
      - Read from ``state`` — every CACAO playbook variable is on
        the typed state under its slugified key (see the state
        TypedDict above).
      - Call your LLM, optionally with the tools emitted in this
        module bound via ``llm.bind_tools([...])`` or routed
        through a ``ToolNode``.
      - Return a dict of state updates; LangGraph merges it into
        the typed state via the reducers the integrator chose.
      - Append assistant / tool messages to ``state['messages']``
        (the channel uses ``add_messages``, so returning a list
        under that key concatenates rather than replaces).

    Provider-neutrality: this stub intentionally does not import a
    specific LLM SDK. Pick one at integration time.
    """
    raise NotImplementedError(
        "LLM step not implemented: integrator must wire an LLM here."
    )

STATE_SCHEMA = PlaybookBusinessContinuityV1State
TOOLS = (detect_and_declare_bcm_event, activate_bcm_plan, isolate_affected_systems, switch_to_backup, notify_competent_authority, restore_and_verify, post_incident_review,)
AGENTIC_HOOK = llm_step

