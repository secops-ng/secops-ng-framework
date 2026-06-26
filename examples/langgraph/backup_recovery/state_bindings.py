# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.backup_recovery@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookBackupRecoveryV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.backup_recovery@v1.

    Playbook id: playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __drill_window__
    # ISO 8601 interval describing the restore-drill window being evaluated. Supplied by the scheduler that triggers this playbook (cron, Temporal schedule, or n8n trigger), or by an operator-initiated trigger.
    drill_window: str
    # playbook_variable: __backup_scope__
    # Identifier of the in-scope data set for this drill (matches a row in the operator's documented backup-scope catalogue: which systems, which datasets, RPO/RTO band).
    backup_scope: str
    # playbook_variable: __candidate_backup_id__
    # Identifier of the most recent backup artifact selected for the drill, resolved against __backup_scope__ and the drill window.
    candidate_backup_id: str
    # playbook_variable: __integrity_ok__
    # Outcome of the validate-backup-integrity step: true when the backup's documented integrity checks (checksum, manifest, decryption key availability) all pass; false when any check fails. A false value short-circuits the drill into the evidence-capture and notify branches with a failure record rather than executing the restore.
    integrity_ok: bool
    # playbook_variable: __drill_result__
    # Identifier of the executed restore-drill artifact: the durable record of the non-destructive restore exercise (target environment, restored object inventory, RTO/RPO observed). Empty when the drill was skipped due to a failed integrity check.
    drill_result: str
    # playbook_variable: __attestation_id__
    # Identifier of the dated backup-attestation + drill-evidence record published to the operator's evidence store. Always populated, including the integrity-failure branch (which emits an attestation recording the failure).
    attestation_id: str
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
async def detect_restore_drill_trigger(drill_window: str, backup_scope: str) -> str:
    """Resolve the trigger for this run: a scheduled drill window matured (cron / Temporal schedule), an operator-initiated drill request landed, or a continuity event up the chain raised the drill cadence. Reads __drill_window__ and __backup_scope__ and selects __candidate_backup_id__ — the most recent backup artifact for the in-scope data set that is eligible for a non-destructive drill against an isolated target.

    CACAO step_id : action--50000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--50000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect restore-drill trigger', 'secops_ng.tool.name': 'detect_restore_drill_trigger', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--50000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect restore-drill trigger', 'secops_ng.tool.name': 'detect_restore_drill_trigger', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--50000000-0000-4000-8000-000000000002'"
        )

@tool
async def validate_backup_integrity(candidate_backup_id: str) -> bool:
    """Run the documented integrity checks on the candidate backup: checksum / manifest verification, decryption-key availability against the operator's key-management surface, and a presence check against the documented backup-scope inventory (no silently-dropped objects). Sets __integrity_ok__. A false outcome short-circuits the drill into the evidence-capture step (failure attestation) without executing the restore, so the operator's continuity owner is notified of the integrity gap rather than discovering it under real recovery pressure.

    CACAO step_id : action--50000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--50000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'validate backup integrity', 'secops_ng.tool.name': 'validate_backup_integrity', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--50000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'validate backup integrity', 'secops_ng.tool.name': 'validate_backup_integrity', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--50000000-0000-4000-8000-000000000003'"
        )

@tool
async def execute_restore_drill(candidate_backup_id: str, backup_scope: str) -> str:
    """Execute the non-destructive restore drill against the operator's documented isolated drill target (not production). Restore the in-scope objects from __candidate_backup_id__, record the observed RTO / RPO against the documented objectives, capture the restored object inventory, and emit __drill_result__. The drill is non-destructive by construction; production state is untouched. Detection bindings for restore-target misconfiguration (restore landing in production, drill target reachable from production network) are owned by CORE-layer cards once upstream rule ids are selected. A restore-drill-cadence KPI catalogue entry is owned by a sibling EXTEND card; this step intentionally does not pin a step-level metric_ref until that catalogue entry lands.

    CACAO step_id : action--50000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--50000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'execute restore drill', 'secops_ng.tool.name': 'execute_restore_drill', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--50000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'execute restore drill', 'secops_ng.tool.name': 'execute_restore_drill', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--50000000-0000-4000-8000-000000000005'"
        )

@tool
async def evidence_capture(candidate_backup_id: str, integrity_ok: bool, drill_result: str) -> str:
    """Compose and publish the dated attestation + drill-evidence record to the operator's evidence store. The record carries the candidate backup id, integrity-check outcome, executed drill result (or the failure marker for the short-circuit branch), observed RTO/RPO, restored inventory, and the drill window. This is the audit-evident artifact that NIS2 Art.21(2)(c) and DORA Art.12 reviewers read; missing or stale attestations are the failure mode the metrics surface.

    CACAO step_id : action--50000000-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--50000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'evidence capture', 'secops_ng.tool.name': 'evidence_capture', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--50000000-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'evidence capture', 'secops_ng.tool.name': 'evidence_capture', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--50000000-0000-4000-8000-000000000006'"
        )

@tool
async def notify_continuity_owner(attestation_id: str, backup_scope: str) -> None:
    """Deliver the attestation reference to the continuity owner along the operator's pre-bound channel (ticketing system, chat thread, email). Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently; an attestation written but never delivered to the owner is itself a continuity gap.

    CACAO step_id : action--50000000-0000-4000-8000-000000000007
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--50000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify continuity owner', 'secops_ng.tool.name': 'notify_continuity_owner', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--50000000-0000-4000-8000-000000000007', attributes={'secops_ng.playbook.id': 'playbook--50a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6ba', 'secops_ng.step.id': 'action--50000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify continuity owner', 'secops_ng.tool.name': 'notify_continuity_owner', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--50000000-0000-4000-8000-000000000007'"
        )

async def llm_step(state: PlaybookBackupRecoveryV1State) -> dict:
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

STATE_SCHEMA = PlaybookBackupRecoveryV1State
TOOLS = (detect_restore_drill_trigger, validate_backup_integrity, execute_restore_drill, evidence_capture, notify_continuity_owner,)
AGENTIC_HOOK = llm_step

