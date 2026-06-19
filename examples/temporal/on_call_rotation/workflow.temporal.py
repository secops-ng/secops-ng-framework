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
async def load_rotation_roster(shift_window: str) -> dict[str, object]:
    """Read the rotation roster from the operator's source of truth (paging system schedule, calendar feed, or roster file) and resolve who holds the primary slot and who receives the next shift for the evaluated window. The roster source itself is operator-bound; this step normalises its output into __current_on_call__ and __next_on_call__.

    CACAO step_id: action--30000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'load rotation roster', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'load_rotation_roster'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'load rotation roster', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'load_rotation_roster'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--30000000-0000-4000-8000-000000000002'"
        )

LOAD_ROTATION_ROSTER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def bind_escalation_tiers(current_on_call: str) -> dict[str, object]:
    """Resolve the escalation chain the paging system will fan through when an alert is not acknowledged: primary (current_on_call), secondary (back-up slot from the roster), then manager. The bound chain is published to the paging system's runtime configuration so the next page uses it. Detection coverage for unusual-hours authentication anomalies during off-hours rotation handoff and for suspicious privileged-account modification during rotation gaps is wired by the CORE-layer mapping; upstream SigmaHQ rule ids are referenced from the playbook-level external_references (TODO entries until pinned).

    CACAO step_id: action--30000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'bind escalation tiers', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'bind_escalation_tiers'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'bind escalation tiers', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'bind_escalation_tiers'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--30000000-0000-4000-8000-000000000003'"
        )

BIND_ESCALATION_TIERS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def generate_handoff_brief(current_on_call: str, next_on_call: str) -> str:
    """Compose a structured handoff brief covering open incidents, recent alerts within the configured lookback, outstanding escalations, and ack-latency snapshot for the prior shift. The brief is delivered as a structured artifact (markdown + a JSON payload), not free-form prose, so the next on-call ingests it deterministically.

    CACAO step_id: action--30000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'generate handoff brief', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'generate_handoff_brief'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'generate handoff brief', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'generate_handoff_brief'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--30000000-0000-4000-8000-000000000005'"
        )

GENERATE_HANDOFF_BRIEF_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_incoming_on_call(next_on_call: str, brief_id: str) -> None:
    """Deliver the handoff brief to the incoming on-call along the operator's pre-bound channel (paging system DM, chat thread, email). Tracked separately from brief generation so the delivery-SLA KPI can report compose-time and deliver-time independently.

    CACAO step_id: action--30000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--30000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify incoming on-call', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_incoming_on_call'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--30000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--30000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'notify incoming on-call', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_incoming_on_call'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--30000000-0000-4000-8000-000000000006'"
        )

NOTIFY_INCOMING_ON_CALL_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookOnCallRotationV1Workflow:
    """Operate the on-call rotation: load the current rotation roster, bind the escalation tiers (primary / secondary / manager) the operator's paging system will fan out through, and when the workflow runs inside a shift-handoff window, compose a structured handoff brief from open incidents and recent alerts and deliver it to the incoming on-call. The playbook is reentrant and side-effect-free outside the handoff window; the only durable change in steady state is the bound escalation chain. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7
    stable_id         : playbook.on_call_rotation@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--30000000-0000-4000-8000-000000000001
    activities        : load_rotation_roster, bind_escalation_tiers, generate_handoff_brief, notify_incoming_on_call
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.on_call_rotation@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.on_call_rotation@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--30a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b7', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.on_call_rotation@v1'"
            )

WORKFLOW = PlaybookOnCallRotationV1Workflow
ACTIVITIES = (load_rotation_roster, bind_escalation_tiers, generate_handoff_brief, notify_incoming_on_call,)
RETRY_POLICIES = (LOAD_ROTATION_ROSTER_RETRY_POLICY, BIND_ESCALATION_TIERS_RETRY_POLICY, GENERATE_HANDOFF_BRIEF_RETRY_POLICY, NOTIFY_INCOMING_ON_CALL_RETRY_POLICY,)
