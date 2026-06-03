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
async def enrich_finding(finding_id: str) -> str:
    """Pull asset, owner, and exposure context for the finding.

    CACAO step_id: action--22222222-2222-4222-8222-222222222222
    """
    with _TRACER.start_as_current_span(
        name='activity.action--22222222-2222-4222-8222-222222222222',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--22222222-2222-4222-8222-222222222222', 'secops_ng.step.name': 'enrich finding', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enrich_finding'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--22222222-2222-4222-8222-222222222222', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--22222222-2222-4222-8222-222222222222', 'secops_ng.step.name': 'enrich finding', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'enrich_finding'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--22222222-2222-4222-8222-222222222222'"
        )

ENRICH_FINDING_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def open_critical_ticket() -> None:
    """Open a P1 ticket with the asset owner and link the advisory.

    CACAO step_id: action--44444444-4444-4444-8444-444444444444
    """
    with _TRACER.start_as_current_span(
        name='activity.action--44444444-4444-4444-8444-444444444444',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--44444444-4444-4444-8444-444444444444', 'secops_ng.step.name': 'open critical ticket', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'open_critical_ticket'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--44444444-4444-4444-8444-444444444444', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--44444444-4444-4444-8444-444444444444', 'secops_ng.step.name': 'open critical ticket', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'open_critical_ticket'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--44444444-4444-4444-8444-444444444444'"
        )

OPEN_CRITICAL_TICKET_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def queue_routine_ticket() -> None:
    """Queue a routine remediation ticket on the team's backlog.

    CACAO step_id: action--55555555-5555-4555-8555-555555555555
    """
    with _TRACER.start_as_current_span(
        name='activity.action--55555555-5555-4555-8555-555555555555',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--55555555-5555-4555-8555-555555555555', 'secops_ng.step.name': 'queue routine ticket', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'queue_routine_ticket'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--55555555-5555-4555-8555-555555555555', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--55555555-5555-4555-8555-555555555555', 'secops_ng.step.name': 'queue routine ticket', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'queue_routine_ticket'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--55555555-5555-4555-8555-555555555555'"
        )

QUEUE_ROUTINE_TICKET_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookVulnIntakeV1Workflow:
    """CACAO playbook used by the shared parser tests. Triages an incoming vulnerability advisory, branches on critical severity, then opens a remediation ticket. Authoring of the canonical vuln-intake playbook under content/ is tracked on a separate card; this copy is a parser fixture only.

    CACAO playbook id : playbook--aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa
    stable_id         : playbook.vuln_intake@v1
    content_version   : 0.1.0
    maturity          : draft
    workflow_start    : start--11111111-1111-4111-8111-111111111111
    activities        : enrich_finding, open_critical_ticket, queue_routine_ticket
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.vuln_intake@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.vuln_intake@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.vuln_intake@v1'"
            )

WORKFLOW = PlaybookVulnIntakeV1Workflow
ACTIVITIES = (enrich_finding, open_critical_ticket, queue_routine_ticket,)
RETRY_POLICIES = (ENRICH_FINDING_RETRY_POLICY, OPEN_CRITICAL_TICKET_RETRY_POLICY, QUEUE_ROUTINE_TICKET_RETRY_POLICY,)
