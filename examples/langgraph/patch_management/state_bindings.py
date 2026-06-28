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
    """Detect-patch-availability step. Binds against the deterministic primitive at content.playbooks.patch_management.primitives.detect.detect_patch_availability: normalises the advisory observation that landed on the operator's documented advisory-intake surface (vendor feed, distribution channel, upstream release notification) against the operator-supplied tracked deployment-inventory and emits a canonical update-subject + update-reference record (plus the advisory_kind and the in_scope marker). Reads __update_subject__ and __update_reference__; the operator's deployment-inventory row supplies the ring topology and the patch-criticality taxonomy the downstream steps will classify against. The detect step is read-only against the advisory-intake surface and the deployment-inventory; the framework does not author either.

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
    """Classify-patch-criticality step. Binds against the deterministic primitive at content.playbooks.patch_management.primitives.classify.classify_patch_criticality: resolves the update against the operator's documented patch-criticality taxonomy (security-critical, security-routine, feature-only) over the closed severity-band + exploit-status + feature-only inputs. Reads the same advisory surface the detect step consulted plus any operator-bound severity / exploit-status enrichment documented for __update_subject__. Sets __patch_criticality__. The classification is best-effort and time-boxed; when the documented intake deadline elapses the primitive is invoked with deadline_missed=true and emits the sentinel 'unclassified' so the operator is not held by a perfect-classification stall while the rollout deadline slips; the downstream stage-rollout step treats the unclassified sentinel (and the empty wire shape) as security-critical for scheduling purposes rather than waiting.

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
    """Stage-rollout-to-canary-ring step. Binds against the deterministic primitive at content.playbooks.patch_management.primitives.stage.stage_rollout_to_canary_ring: derives a SHA-256 staged_ring_id over the canonical (update_subject, update_reference, canary_ring, cadence) tuple, where the canary cohort is the second entry of the operator's documented test/canary/broad ring topology and the cadence is selected by the classified __patch_criticality__ (security-critical -> immediate, security-routine -> next-window, feature-only -> maintenance-window; the unclassified sentinel and the empty wire shape both map to immediate). The compile target's runtime engages the update against the operator's distribution channel upstream; the primitive only emits the durable identifier. Sets __staged_ring_id__. Detection bindings for canary-engagement misconfiguration (update pushed to wrong ring, distribution channel returned partial success, cohort membership stale) are owned by CORE-FANOUT cards once upstream rule ids are selected.

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
    """Validate-canary step. Binds against the deterministic primitive at content.playbooks.patch_management.primitives.validate.validate_canary: evaluates the closed health-gate inputs (functional_probe in {green, red, unknown}, error_rate_within_threshold, latency_within_threshold, rollback_ready) and emits __canary_healthy__ true iff the functional probe is green and all three threshold gates are true. The compile target's runtime reads the documented canary-health endpoints upstream; the primitive only evaluates the resulting closed gate combination. A false outcome does not block downstream steps — the evidence-capture record is published with the failure marker, the fan-out step is the deterministic skip path, and the notify step pages the maintenance owner with full context so the next maintenance lever (rollback the canary, escalate the advisory, hold the broad rollout) can be engaged. The mean-time-to-containment KPI (kpi.mttr_containment@v1) reads this step's __canary_healthy__ observation alongside the evidence-capture timestamp to measure validation-window discharge.

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
    """Fan-out-to-broad-rings step. Binds against the deterministic primitive at content.playbooks.patch_management.primitives.fanout.fan_out_to_broad_rings: on a healthy canary (__canary_healthy__ true) derives a SHA-256 broad_rollout_id over the canonical (update_subject, update_reference, staged_ring_id, sorted broad_rings) tuple; on an unhealthy canary the step is the deterministic skip path leaving __broad_rollout_id__ empty with the explicit broad_rollout_skip_reason='canary_unhealthy' marker so the evidence-capture step records the skip in the audit-evident chain without forcing the broad rollout against a failing canary. The compile target's runtime engages the update against the operator's distribution channel upstream; the primitive only emits the durable identifier or the skip marker. Reads __update_subject__, __update_reference__, __staged_ring_id__, and __canary_healthy__; emits __broad_rollout_id__. The conditional shape is intentionally explicit at the description level rather than at a CACAO conditional-step level for SKELETON simplicity; CORE-layer cards may refactor into a `playbook-condition` step once the conditional shape is exercised by the worked-example fan-out.

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
    """Evidence-capture step. Binds against the deterministic primitive at content.playbooks.patch_management.primitives.artifact.build_patch_application_evidence_artifact: composes the JSON-native patch-application evidence record shaped against schemas/evidence/patch.schema.json (stream: patch) and pins the artifact_id as SHA-256(workflow_id|execution_id|captured_at). compile_target is intentionally NOT part of the id so the three reference compilers re-derive byte-identical bytes from the same primitive output (the byte-parity contract the F-WF-PATCH CORE-FANOUT siblings assert against). The record carries the update subject, the advisory reference, the classified criticality (or the unclassified sentinel on the short-circuit branch), the staged ring id, the canary health outcome and the closed health-observations block, the broad rollout id (or the empty wire shape with the canary_unhealthy skip marker on the unhealthy-canary branch), and the dated capture timestamp. The skip-marker invariant and the canary_healthy <-> gate-combination invariant are enforced at the primitive boundary so an inconsistent record fails loud here rather than at the schema-validation boundary downstream. This is the audit-evident artifact NIS2 Art. 21(2)(e) reviewers read against a maintenance / patch-rollout obligation; missing or stale evidence is the failure mode the maintenance metrics surface. The primitive only produces the JSON-native record; the durable emitter wiring (artifact-path, content-addressed filename, atomic write) is owned by the per-target compilers and lands with the CORE-FANOUT sibling cards.

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

