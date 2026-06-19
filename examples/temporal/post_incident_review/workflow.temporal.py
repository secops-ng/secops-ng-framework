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
async def timeline_collation(incident_id: str) -> dict[str, object]:
    """Collate a chronological timeline of the incident from the artifacts the responders left behind: ticket comments, chat transcripts, EDR / SIEM exports, network captures, and operator-supplied evidence packages. The step must flag gaps in the evidence record where anti-forensics signals (cleared eventlogs, disabled audit policy, timestomped files) are present — these are recorded in __evidence_gaps_present__ rather than silently smoothed over, so the review template can address decisions made under partial evidence. Produces __timeline_artifact__ and __evidence_gaps_present__.

    CACAO step_id: action--40000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--40000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--40a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b9', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'timeline collation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'timeline_collation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--40000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--40a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b9', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'timeline collation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'timeline_collation'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--40000000-0000-4000-8000-000000000002'"
        )

TIMELINE_COLLATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def blameless_review_template(incident_id: str, timeline_artifact: str, evidence_gaps_present: bool) -> str:
    """Walk the operator's blameless review template against the collated timeline. The template separates contributing factors (process, tooling, staffing, training, environment) from individual error, and explicitly captures decisions that were reasonable given the evidence available at the time. If __evidence_gaps_present__ is true the template's evidence-gaps section is mandatory rather than optional. Produces __review_artifact__.

    CACAO step_id: action--40000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--40000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--40a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b9', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'blameless review template', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'blameless_review_template'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--40000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--40a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b9', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'blameless review template', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'blameless_review_template'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--40000000-0000-4000-8000-000000000003'"
        )

BLAMELESS_REVIEW_TEMPLATE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def corrective_action_tracking(incident_id: str, review_artifact: str) -> str:
    """Extract corrective actions from the review artifact and register each one with owner, due-date, and verification clause. Registration is the deliverable here — execution and verification of each action are out of scope for this playbook (they live on the operator's existing change / ticketing system). Produces __corrective_action_register__.

    CACAO step_id: action--40000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--40000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--40a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b9', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'corrective-action tracking', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'corrective_action_tracking'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--40000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--40a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b9', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'corrective-action tracking', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'corrective_action_tracking'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--40000000-0000-4000-8000-000000000004'"
        )

CORRECTIVE_ACTION_TRACKING_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookPostIncidentReviewV1Workflow:
    """Run the post-incident review after an incident has been closed or contained: collate the timeline from the artifacts the responders left behind, walk a blameless review template that separates contributing factors from individual error, and emit a corrective-action register that downstream tracking can consume. The playbook does not re-litigate the incident — it formalises learning into auditable, restartable state. CACAO v2 + SecOps-NG content-model extensions. Forward-public artifact: detection bindings reference upstream SigmaHQ rule IDs by ID only (anti-forensics / audit-tampering signals that the timeline collation step should be aware of so gaps in the log record are flagged rather than silently glossed); SecOps-NG does not re-author Sigma rules.

    CACAO playbook id : playbook--40a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b9
    stable_id         : playbook.post_incident_review@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--40000000-0000-4000-8000-000000000001
    activities        : timeline_collation, blameless_review_template, corrective_action_tracking
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.post_incident_review@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--40a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b9', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.post_incident_review@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--40a0b0c0-d0e0-4f00-8a1b-c2d3e4f5a6b9', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.post_incident_review@v1'"
            )

WORKFLOW = PlaybookPostIncidentReviewV1Workflow
ACTIVITIES = (timeline_collation, blameless_review_template, corrective_action_tracking,)
RETRY_POLICIES = (TIMELINE_COLLATION_RETRY_POLICY, BLAMELESS_REVIEW_TEMPLATE_RETRY_POLICY, CORRECTIVE_ACTION_TRACKING_RETRY_POLICY,)
