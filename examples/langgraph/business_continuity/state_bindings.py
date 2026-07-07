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
    # playbook_variable: __bcm_plan_ref__
    # Reference to the activated BCM plan artifact resolved from the operator's BCM-plan store. Enumerates the documented isolation targets, failover targets, and recovery objectives (RTO / RPO) the workflow reads at switch-to-backup and restore-and-verify.
    bcm_plan_ref: str
    # playbook_variable: __event_declared_ts__
    # ISO 8601 timestamp of the business-continuity event declaration. Anchors the NIS2 Art. 23 24h early-warning / 72h incident-notification / 1-month final-report clock when the significant-incident threshold is crossed.
    event_declared_ts: str
    # playbook_variable: __event_id__
    # Business-continuity event identifier assigned at declaration. Correlation key across activate, isolate, switch-to-backup, notify, restore-and-verify, and post-incident-review so a reviewer can join the full continuity lifecycle into a single reportable-event ledger keyed to the operator's accountability surface.
    event_id: str
    # playbook_variable: __failover_target__
    # Reference to the failover target resolved by switch-to-backup against __bcm_plan_ref__ (the documented backup site, data replica, or standby capacity the service is switched to). Feeds restore-and-verify for the cutback validation.
    failover_target: str
    # playbook_variable: __isolation_scope__
    # Reference to the isolation scope resolved by isolate-affected-systems against __bcm_plan_ref__ (the affected primary systems, network segments, or upstream dependencies contained to prevent cascade). Empty when the event does not require isolation.
    isolation_scope: str
    # playbook_variable: __notification_ref__
    # Reference to the NIS2 Art. 23 notification artifact emitted by notify-competent-authority when the event crosses the significant-incident threshold. Empty otherwise.
    notification_ref: str
    # playbook_variable: __pir_ref__
    # Reference to the post-incident-review record persisted at post-incident-review. The audit-evident record of lessons learned, corrective actions, and BCM-plan revisions the operator's accountability posture reads.
    pir_ref: str
    # playbook_variable: __recovery_result__
    # Reference to the recovery-and-verification result produced by restore-and-verify — the observed RTO / RPO against the documented objectives, the primary-service health signal, and the cutback outcome. Feeds post-incident-review.
    recovery_result: str
    # playbook_variable: __significant_incident__
    # Whether the event crosses the NIS2 Art. 23 significant- incident threshold. When true, notify-competent-authority dispatches the Art. 23 24h early warning; when false, the notify step short-circuits to a locally-logged no-notification record. Set at activate-bcm-plan against the operator's declared significance-threshold policy.
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
async def detect_and_declare_bcm_event() -> dict[str, object]:
    """SKELETON — receive a business-continuity trigger on the operator's declared event-declaration surface (major outage escalation from the incident-management lane, ransomware containment escalation from the containment lane, upstream-dependency failure signal, or facility- loss declaration). Assign __event_id__ and stamp __event_declared_ts__ against the NIS2 Art. 23 clock. TODO (CORE): pin the trigger-surface adapter shape and the initial evidence-capture record.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--b17c0072-0000-4000-8000-000000000002'"
        )

@tool
async def activate_bcm_plan(event_id: str) -> dict[str, object]:
    """SKELETON — retrieve the documented BCM plan artifact for the affected service from the operator's BCM-plan store and activate it. Reads the documented isolation targets, failover targets, and recovery objectives (RTO / RPO) into workflow state. Evaluates the event against the operator's declared significance-threshold policy and sets __significant_incident__ accordingly. TODO (CORE): pin the BCM-plan store adapter, the plan-artifact schema, and the significance-threshold evaluator.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--b17c0072-0000-4000-8000-000000000003'"
        )

@tool
async def isolate_affected_systems(event_id: str, bcm_plan_ref: str) -> str:
    """SKELETON — where the event and the activated plan call for it, contain the failure surface by isolating the affected primary systems, network segments, or upstream dependencies against the operator's isolation surface per __bcm_plan_ref__. Records __isolation_scope__ for the downstream recovery-and-verification cutback discipline. Skipped (empty __isolation_scope__) where the plan documents no isolation step for the event class (e.g. a pure availability outage with no compromise indicator). TODO (CORE): pin the isolation-surface adapter and the isolation-scope schema.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--b17c0072-0000-4000-8000-000000000004'"
        )

@tool
async def switch_to_backup(event_id: str, bcm_plan_ref: str, isolation_scope: str) -> str:
    """SKELETON — failover the affected service to the documented backup site, data replica, or standby capacity per __bcm_plan_ref__. The failover is the disaster- recovery leg of the Art. 21(2)(c) triplet (backup + disaster recovery + crisis management); backup integrity the failover reads is exercised on the sibling backup_recovery playbook's periodic restore-drill lane. Records __failover_target__ for the downstream restore-and-verify cutback discipline. TODO (CORE): pin the failover-surface adapter, the recovery-objective evaluator (observed vs documented RTO / RPO), and the cutover-evidence record.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--b17c0072-0000-4000-8000-000000000005'"
        )

@tool
async def notify_competent_authority(event_id: str, event_declared_ts: str, significant_incident: bool) -> str:
    """SKELETON — where __significant_incident__ is true, dispatch the NIS2 Art. 23 significant-incident notification to the operator's competent authority (national cybersecurity authority per the entity's establishment Member State) on the Art. 23 timeline: 24h early warning, 72h incident notification, one-month final report. The envelope carries __event_id__, __event_declared_ts__, the preliminary assessment, the impact scope, and the cross- border-effect indicator. Where __significant_incident__ is false, the step records a locally-logged no-notification determination (retained for accountability) and short-circuits to restore-and-verify. Records __notification_ref__ for the post-incident-review record. TODO (CORE): pin the competent-authority adapter (per-Member- State delivery surface), the Art. 23 envelope templates (early-warning, incident-notification, final-report), and the significance-determination evidence discipline.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--b17c0072-0000-4000-8000-000000000006'"
        )

@tool
async def restore_and_verify(event_id: str, bcm_plan_ref: str, failover_target: str) -> str:
    """SKELETON — return the primary service to a known-good state per __bcm_plan_ref__ (cutback from __failover_target__ where applicable, dependency revalidation, and health-signal check against the documented recovery objectives). Records __recovery_result__ with the observed RTO / RPO delta against the documented objectives and the primary-service health signal. TODO (CORE): pin the health-signal adapter, the cutback procedure, and the recovery-attestation evidence discipline.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--b17c0072-0000-4000-8000-000000000007'"
        )

@tool
async def post_incident_review(event_id: str, recovery_result: str, notification_ref: str) -> str:
    """SKELETON — persist the post-incident-review record for the event: lessons learned, corrective actions, and any BCM-plan revisions surfaced by the event. Records __pir_ref__ on the operator's evidence store keyed to __event_id__. Feeds the operator's accountability posture and any downstream regulator query (Art. 23 final-report supplement, Art. 32 supervisory-authority information request). TODO (CORE): pin the PIR record schema, the evidence-store retention discipline, and the BCM-plan revision handoff.

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
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--b17c0072-0000-4000-8000-000000000008'"
        )

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

