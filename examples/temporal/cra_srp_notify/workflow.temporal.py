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
async def early_warning(case_id: str, clock_kind: str, awareness_ts: str) -> str:
    """SKELETON — CRA Article 14 24-hour early warning. Compose the early-warning submission body (product / manufacturer / vulnerability or incident metadata) against the SRP intake shape and dispatch it to the manufacturer's main-establishment CSIRT via the SRP, with simultaneous availability to ENISA per Article 14. Records __srp_early_warning_id__ on confirmed receipt. TODO (CORE): SRP intake schema is not yet public (Commission page notes a pre-go-live testing period ahead of 11 September 2026); the submission body shape is a placeholder here and a sibling CORE card lands the schema-conformant payload builder once the SRP schema is published. The 24h clock anchor is __awareness_ts__ + 24 hours.

    CACAO step_id: action--5a509a09-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--5a509a09-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--5a509a09-0000-4000-8000-000000000002', 'secops_ng.step.name': 'early_warning', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'early_warning'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--5a509a09-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--5a509a09-0000-4000-8000-000000000002', 'secops_ng.step.name': 'early_warning', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'early_warning'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--5a509a09-0000-4000-8000-000000000002'"
        )

EARLY_WARNING_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def wait_until_72h_deadline(awareness_ts: str) -> None:
    """SKELETON — durable delay to the CRA Article 14 72-hour deadline. Sleeps until __awareness_ts__ + 72 hours as durable state so the wait survives worker restart on each compile target. TODO (CORE): CACAO v2 does not ship a first-class 'delay' step type; the reference emitters (Temporal timer, n8n Wait node, LangGraph interrupt-then-resume-at-timestamp) each carry the wait in their idiomatic way. The compile-target parity test (roadmap goal G-03) verifies the 72h boundary survives restart without drift on all three targets.

    CACAO step_id: action--5a509a09-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--5a509a09-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--5a509a09-0000-4000-8000-000000000004', 'secops_ng.step.name': 'wait until 72h deadline', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'wait_until_72h_deadline'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--5a509a09-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--5a509a09-0000-4000-8000-000000000004', 'secops_ng.step.name': 'wait until 72h deadline', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'wait_until_72h_deadline'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--5a509a09-0000-4000-8000-000000000004'"
        )

WAIT_UNTIL_72H_DEADLINE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def full_notification(case_id: str, clock_kind: str, awareness_ts: str) -> str:
    """SKELETON — CRA Article 14 72-hour full notification. Compose and dispatch the full notification body (product / manufacturer / vulnerability or incident metadata plus corrective / mitigating measures the manufacturer has taken or recommended) to the SRP, with simultaneous availability to ENISA per Article 14. Records __srp_full_notification_id__ on confirmed receipt. TODO (CORE): SRP intake schema is not yet public; the submission body shape is a placeholder pending the CORE card.

    CACAO step_id: action--5a509a09-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--5a509a09-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--5a509a09-0000-4000-8000-000000000005', 'secops_ng.step.name': 'full_notification', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'full_notification'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--5a509a09-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--5a509a09-0000-4000-8000-000000000005', 'secops_ng.step.name': 'full_notification', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'full_notification'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--5a509a09-0000-4000-8000-000000000005'"
        )

FULL_NOTIFICATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def wait_until_final_report_deadline(clock_kind: str, awareness_ts: str) -> None:
    """SKELETON — durable delay to the CRA Article 14 final-report deadline. For __clock_kind__ = actively_exploited_vulnerability (Art. 14(2)) the wait resolves at __awareness_ts__ + 14 days after a corrective or mitigating measure becomes available; for __clock_kind__ = severe_incident (Art. 14(3)) the wait resolves at __awareness_ts__ + 1 month. Modelled as durable state so the wait survives worker restart on each compile target. TODO (CORE): the 'after a corrective measure becomes available' anchor is an event, not a fixed offset from awareness — the CORE card wires the corrective-measure-available signal from the upstream vulnerability-intake or incident-handling playbook so this delay can start its 14-day clock at the right instant; a placeholder anchor is used in the SKELETON.

    CACAO step_id: action--5a509a09-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--5a509a09-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--5a509a09-0000-4000-8000-000000000006', 'secops_ng.step.name': 'wait until final-report deadline', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'wait_until_final_report_deadline'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--5a509a09-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--5a509a09-0000-4000-8000-000000000006', 'secops_ng.step.name': 'wait until final-report deadline', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'wait_until_final_report_deadline'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--5a509a09-0000-4000-8000-000000000006'"
        )

WAIT_UNTIL_FINAL_REPORT_DEADLINE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def final_report(case_id: str, clock_kind: str, awareness_ts: str) -> str:
    """SKELETON — CRA Article 14 final report. Compose and dispatch the final report (description of the vulnerability, severity and impact, information on actors that have exploited or could exploit the vulnerability, and details of the corrective measures for Art. 14(2); analogous shape for Art. 14(3) severe incidents at the 1-month deadline) to the SRP with simultaneous availability to ENISA. Records __srp_final_report_id__ on confirmed receipt. TODO (CORE): SRP intake schema is not yet public; the submission body shape is a placeholder pending the CORE card.

    CACAO step_id: action--5a509a09-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--5a509a09-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--5a509a09-0000-4000-8000-000000000007', 'secops_ng.step.name': 'final_report', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'final_report'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--5a509a09-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--5a509a09-0000-4000-8000-000000000007', 'secops_ng.step.name': 'final_report', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'final_report'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--5a509a09-0000-4000-8000-000000000007'"
        )

FINAL_REPORT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookCraSrpNotifyV1Workflow:
    """SKELETON — durable-state scaffold for the CRA Article 14 notification workflow that will address the Single Reporting Platform (SRP) once its schema is published. Expresses the 24h / 72h / 14d-or-30d timer cascade as first-class CACAO steps so any of the three reference compile targets (n8n, Temporal, LangGraph) can carry the clocks as durable state. Fired by a sibling incident-handling or vulnerability-intake playbook when the operator's incident-classification step trips the CRA Article 14(2) actively-exploited-vulnerability clock or the Article 14(3) severe-incident clock; this playbook is the shared regulator-notification chain those upstream playbooks hand off to. SKELETON only: submission bodies are placeholder — the SRP intake schema is not yet published (Commission page notes a pre-go-live testing period ahead of 11 September 2026); a sibling CORE card populates the CACAO parallel + delay step bodies against the operator's SRP intake surface once that surface is publicly documented. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--5a509a09-0000-4000-8000-000000000001
    stable_id         : playbook.cra_srp_notify@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--5a509a09-0000-4000-8000-000000000001
    activities        : early_warning, wait_until_72h_deadline, full_notification, wait_until_final_report_deadline, final_report
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.cra_srp_notify@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.cra_srp_notify@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--5a509a09-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.cra_srp_notify@v1'"
            )

WORKFLOW = PlaybookCraSrpNotifyV1Workflow
ACTIVITIES = (early_warning, wait_until_72h_deadline, full_notification, wait_until_final_report_deadline, final_report,)
RETRY_POLICIES = (EARLY_WARNING_RETRY_POLICY, WAIT_UNTIL_72H_DEADLINE_RETRY_POLICY, FULL_NOTIFICATION_RETRY_POLICY, WAIT_UNTIL_FINAL_REPORT_DEADLINE_RETRY_POLICY, FINAL_REPORT_RETRY_POLICY,)
