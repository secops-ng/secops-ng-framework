# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.patch_management@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookPatchManagementV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.patch_management@v1.

    Playbook id: playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __update_subject__
    # Identifier of the tracked package / image / firmware line the update applies to (matches a row in the operator's documented deployment-inventory: which subject, which ring topology, which patch-criticality taxonomy applies).
    update_subject: str
    # playbook_variable: __update_reference__
    # Identifier of the security update / patch advisory being rolled out (advisory id, vendor reference, or upstream release tag). Supplied by the operator's documented advisory-intake surface (vendor feed, distribution channel, upstream release notification).
    update_reference: str
    # playbook_variable: __patch_criticality__
    # Identifier of the classified patch-criticality bucket for this update against the operator's documented taxonomy: security-critical (rollout deadline measured in hours / days), security-routine (rollout deadline measured in days / weeks), or feature-only (rollout cadenced against the operator's documented maintenance window). Empty when classification could not be completed within the documented intake deadline; an empty value short-circuits into an evidence-capture failure record while still treating the update as security-critical for downstream scheduling.
    patch_criticality: str
    # playbook_variable: __staged_ring_id__
    # Identifier of the canary / test ring the staged-rollout step engaged the update against (e.g. test-fleet reference, canary-cohort reference). Always populated; the value names the ring that received the update on the staged branch even on the short-circuit branch.
    staged_ring_id: str
    # playbook_variable: __canary_healthy__
    # Outcome of the validate-canary step: true when the canary ring is observed inside the documented health gates (functional probes green, error-rate / latency deviation inside the documented thresholds, rollback path verified) for the documented validation window; false when the canary is unhealthy and the rollout must be paused. A false value does not block the evidence-capture and notify branches; the record is published with the failure marker and the fan-out step is skipped so the maintenance owner is paged with full context rather than discovering the failure later.
    canary_healthy: bool
    # playbook_variable: __broad_rollout_id__
    # Identifier of the broad-ring rollout engagement once the canary has reported healthy (deployment reference, change ticket id, distribution-channel push reference). Empty on the canary-unhealthy branch; the empty value is recorded in the evidence record and notified to the maintenance owner alongside the canary failure marker.
    broad_rollout_id: str
    # playbook_variable: __evidence_id__
    # Identifier of the dated patch-application evidence record published to the operator's evidence store. Always populated, including on the short-circuit branch (unclassified update) and the canary-unhealthy branch.
    evidence_id: str
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
async def detect_patch_availability(update_subject: str, update_reference: str) -> None:
    """Resolve the trigger for this run: an advisory landed on the operator's documented advisory-intake surface (vendor feed, distribution channel, upstream release notification) against __update_subject__, an operator-scheduled maintenance window opened, or an operator-initiated trigger landed. Reads __update_subject__ and __update_reference__ to confirm the update applies to a tracked deployment-inventory row; reads the operator's documented deployment-inventory row to surface the ring topology (test / canary / broad) and the patch-criticality taxonomy the downstream steps will classify against.

    CACAO step_id : action--70000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--70000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect patch availability', 'secops_ng.tool.name': 'detect_patch_availability', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--70000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect patch availability', 'secops_ng.tool.name': 'detect_patch_availability', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--70000000-0000-4000-8000-000000000002'"
        )

@tool
async def classify_patch_criticality(update_subject: str, update_reference: str) -> str:
    """Classify the update against the operator's documented patch-criticality taxonomy: security-critical (rollout deadline measured in hours / days, e.g. remotely exploitable RCE with active exploitation, kernel / hypervisor patch), security-routine (rollout deadline measured in days / weeks, e.g. lower-severity advisories without active exploitation), or feature-only (rollout cadenced against the operator's documented maintenance window, no security urgency). Reads the same advisory surface the detect step consulted plus any operator-bound severity / exploit-status enrichment documented for __update_subject__. Sets __patch_criticality__. The classification is best-effort and time-boxed; if classification cannot be completed within the documented intake deadline (so the operator is not held by a perfect-classification stall while the deadline slips), this step leaves __patch_criticality__ empty and the downstream stage-rollout step treats the update as security-critical for scheduling purposes rather than waiting.

    CACAO step_id : action--70000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--70000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify patch criticality', 'secops_ng.tool.name': 'classify_patch_criticality', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--70000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify patch criticality', 'secops_ng.tool.name': 'classify_patch_criticality', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--70000000-0000-4000-8000-000000000003'"
        )

@tool
async def stage_rollout_to_canary_ring(update_subject: str, update_reference: str, patch_criticality: str) -> str:
    """Engage the update against the operator's pre-bound canary ring for __update_subject__: push the update through the documented distribution channel (package mirror, image registry, firmware-distribution surface) to the test / canary cohort. Reads __patch_criticality__ to select the rollout cadence (security-critical → immediate, security-routine → next-window, feature-only → maintenance-window); when __patch_criticality__ is empty the step treats the update as security-critical for scheduling rather than waiting for classification. Emits __staged_ring_id__ — the durable identifier of the canary cohort that received the update (cohort reference, change ticket id, distribution-channel push reference). Detection bindings for canary-engagement misconfiguration (update pushed to wrong ring, distribution channel returned partial success, cohort membership stale) are owned by CORE-layer cards once upstream rule ids are selected.

    CACAO step_id : action--70000000-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--70000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'stage rollout to canary ring', 'secops_ng.tool.name': 'stage_rollout_to_canary_ring', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--70000000-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'stage rollout to canary ring', 'secops_ng.tool.name': 'stage_rollout_to_canary_ring', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--70000000-0000-4000-8000-000000000004'"
        )

@tool
async def validate_canary(update_subject: str, staged_ring_id: str) -> bool:
    """Observe the canary ring against the operator's documented health gates after the staged rollout: functional probes green, error-rate / latency deviation inside the documented thresholds, rollback path verified for the documented validation window. Reads __update_subject__ and __staged_ring_id__; sets __canary_healthy__. A false outcome does not block downstream steps — the evidence-capture record is published with the failure marker, the fan-out step is skipped, and the notify step pages the maintenance owner with the full context so the next maintenance lever (rollback the canary, escalate the advisory, hold the broad rollout) can be engaged. The mean-time-to-containment KPI (kpi.mttr_containment@v1) reads this step's __canary_healthy__ observation alongside the evidence-capture timestamp to measure validation-window discharge.

    CACAO step_id : action--70000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--70000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'validate canary', 'secops_ng.tool.name': 'validate_canary', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--70000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'validate canary', 'secops_ng.tool.name': 'validate_canary', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--70000000-0000-4000-8000-000000000005'"
        )

@tool
async def fan_out_to_broad_rings(update_subject: str, update_reference: str, staged_ring_id: str, canary_healthy: bool) -> str:
    """On a healthy canary (__canary_healthy__ true), engage the update against the remaining rings of the operator's documented deployment-ring topology along the same documented distribution channel. Reads __update_subject__, __update_reference__, __staged_ring_id__, and __canary_healthy__; emits __broad_rollout_id__ — the durable identifier of the broad-ring engagement (deployment reference, change ticket id, distribution-channel push reference). On an unhealthy canary (__canary_healthy__ false) the step is skipped and __broad_rollout_id__ is left empty; the evidence-capture and notify steps record the skip explicitly so the audit-evident chain is closed without forcing the broad rollout against a failing canary. The conditional shape is intentionally explicit at the description level rather than at a CACAO conditional-step level for SKELETON simplicity; CORE-layer cards may refactor into a `playbook-condition` step once the conditional shape is exercised by the worked-example fan-out.

    CACAO step_id : action--70000000-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--70000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'fan out to broad rings', 'secops_ng.tool.name': 'fan_out_to_broad_rings', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--70000000-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'fan out to broad rings', 'secops_ng.tool.name': 'fan_out_to_broad_rings', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--70000000-0000-4000-8000-000000000006'"
        )

@tool
async def evidence_capture(update_subject: str, update_reference: str, patch_criticality: str, staged_ring_id: str, canary_healthy: bool, broad_rollout_id: str) -> str:
    """Compose and publish the dated patch-application evidence record to the operator's evidence store. The record carries the update subject, the advisory reference, the classified criticality (or the empty-classification marker on the short-circuit branch), the staged ring id, the canary health outcome (or the failure marker), the broad rollout id (or the empty marker on the canary-failure branch), and the observed health-gate measurements across the validation window. This is the audit-evident artifact NIS2 Art. 21(2)(e) reviewers read against a maintenance / patch-rollout obligation; missing or stale evidence is the failure mode the maintenance metrics surface.

    CACAO step_id : action--70000000-0000-4000-8000-000000000007
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--70000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'evidence capture', 'secops_ng.tool.name': 'evidence_capture', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--70000000-0000-4000-8000-000000000007', attributes={'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'evidence capture', 'secops_ng.tool.name': 'evidence_capture', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--70000000-0000-4000-8000-000000000007'"
        )

@tool
async def notify_maintenance_owner(evidence_id: str, update_subject: str, canary_healthy: bool) -> None:
    """Deliver the evidence reference to the maintenance owner along the operator's pre-bound channel (ticketing system, chat thread, change-management board). Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently; an evidence record written but never delivered to the owner is itself a maintenance-discipline gap. Notification carries the canary health outcome so a false __canary_healthy__ pages with appropriate urgency for the next maintenance lever (rollback the canary, escalate the advisory, hold the broad rollout).

    CACAO step_id : action--70000000-0000-4000-8000-000000000008
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--70000000-0000-4000-8000-000000000008',
        attributes={'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 'notify maintenance owner', 'secops_ng.tool.name': 'notify_maintenance_owner', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--70000000-0000-4000-8000-000000000008', attributes={'secops_ng.playbook.id': 'playbook--70a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6cc', 'secops_ng.step.id': 'action--70000000-0000-4000-8000-000000000008', 'secops_ng.step.name': 'notify maintenance owner', 'secops_ng.tool.name': 'notify_maintenance_owner', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--70000000-0000-4000-8000-000000000008'"
        )

async def llm_step(state: PlaybookPatchManagementV1State) -> dict:
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

STATE_SCHEMA = PlaybookPatchManagementV1State
TOOLS = (detect_patch_availability, classify_patch_criticality, stage_rollout_to_canary_ring, validate_canary, fan_out_to_broad_rings, evidence_capture, notify_maintenance_owner,)
AGENTIC_HOOK = llm_step

