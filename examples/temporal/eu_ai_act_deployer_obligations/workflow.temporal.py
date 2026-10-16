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
async def confirm_intended_use(deployment_id: str, system_reference: str, deployment_record: dict[str, object], instructions_for_use: dict[str, object], workforce_notice: dict[str, object], determined_at: str) -> dict[str, object]:
    """Reconcile the deployment's declared contexts against the contexts the provider's instructions for use permit, per Art. 26(1), and record the determination against __deployment_id__. Where the deployer is an employer deploying at the workplace, the Art. 26(7) notice to workers' representatives and affected workers is a precondition, dated before the determination, because a deployment that proceeds without it cannot be remediated after the fact. The negative case is a first-class outcome: proceed is false, the blocking reasons are named, and the gate that follows ends the cycle, so no downstream step fires. Produces __intended_use_determination__, from which __intended_use_determination_id__ and __deployment_may_proceed__ are extracted.

    CACAO step_id: action--e26d1a00-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e26d1a00-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000002', 'secops_ng.step.name': 'confirm_intended_use', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'confirm_intended_use'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e26d1a00-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000002', 'secops_ng.step.name': 'confirm_intended_use', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'confirm_intended_use'})
        )
        from content.playbooks.eu_ai_act_deployer_obligations.primitives.intended_use import determine_intended_use
        __intended_use_determination__ = determine_intended_use(deployment=__deployment_record__, instructions=__instructions_for_use__, workforce_notice=__workforce_notice__, determined_at=__determined_at__)

CONFIRM_INTENDED_USE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def assess_fundamental_rights_impact(intended_use_determination: dict[str, object], system_profile: dict[str, object], deployer_profile: dict[str, object], fria_assessment: dict[str, object], dpia_record: dict[str, object], art_46_1_exemption: bool, fria_template_ref: str, assessed_at: str) -> dict[str, object]:
    """Perform the Art. 27 fundamental-rights impact assessment before deploying, and record it against __deployment_id__. The first output is the scope determination: Annex III systems other than point 2, for bodies governed by public law and private entities providing public services, and every deployer of a point 5(b) or 5(c) system; out of scope the step closes with a dated record. In scope, the six Art. 27(1)(a)-(f) elements are a checklist, and per Art. 27(4) an element an existing GDPR Art. 35 DPIA already satisfies is recorded as such and not reassessed. The notification of the results to the market-surveillance authority (Art. 27(3)) uses the AI Office's Art. 27(5) template where the operator holds one, and is otherwise recorded as due rather than bound to a guessed shape. An incomplete in-scope assessment blocks deployment, and the gate that follows ends the cycle. Produces __fria_record__, from which __fria_determination_id__ and __fria_blocks_deployment__ are extracted.

    CACAO step_id: action--e26d1a00-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e26d1a00-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000005', 'secops_ng.step.name': 'assess_fundamental_rights_impact', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assess_fundamental_rights_impact'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e26d1a00-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000005', 'secops_ng.step.name': 'assess_fundamental_rights_impact', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assess_fundamental_rights_impact'})
        )
        from content.playbooks.eu_ai_act_deployer_obligations.primitives.fria import assess_fundamental_rights_impact
        __fria_record__ = assess_fundamental_rights_impact(intended_use=__intended_use_determination__, system_profile=__system_profile__, deployer_profile=__deployer_profile__, assessment=__fria_assessment__, dpia=__dpia_record__, art_46_1_exemption=__art_46_1_exemption__, notification_template_ref=__fria_template_ref__, assessed_at=__assessed_at__)

ASSESS_FUNDAMENTAL_RIGHTS_IMPACT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def assign_human_oversight(intended_use_determination: dict[str, object], oversight_assignees: str, assigned_at: str) -> dict[str, object]:
    """Assign human oversight of the deployment to natural persons per Art. 26(2), and record the assignment against __deployment_id__. The obligation has four independently checkable limbs and the record names each assignee against each: competence, training, authority, and the necessary support; an assignee missing any limb, or not a natural person, is uncovered and leaves the assignment incomplete. The capability set an overseer must be able to exercise is fixed by Art. 14(4) and evidenced by the ai_human_oversight playbook. Produces __oversight_assignment__, from which __oversight_assignment_id__ is extracted.

    CACAO step_id: action--e26d1a00-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e26d1a00-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000003', 'secops_ng.step.name': 'assign_human_oversight', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assign_human_oversight'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e26d1a00-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000003', 'secops_ng.step.name': 'assign_human_oversight', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assign_human_oversight'})
        )
        from content.playbooks.eu_ai_act_deployer_obligations.primitives.oversight import compose_oversight_assignment
        __oversight_assignment__ = compose_oversight_assignment(intended_use=__intended_use_determination__, assignees=__oversight_assignees__, assigned_at=__assigned_at__)

ASSIGN_HUMAN_OVERSIGHT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def monitor_operation(intended_use_determination: dict[str, object], oversight_assignment: dict[str, object], monitoring_window: dict[str, object], input_data: dict[str, object], monitoring_findings: str, evaluated_at: str) -> dict[str, object]:
    """Monitor operation on the basis of the instructions for use per Art. 26(5), and record the window against __deployment_id__, with the Art. 26(4) determination that input data the deployer controls is relevant and sufficiently representative, or the dated determination of non-control. The three escalation triggers are kept apart: routine findings feed the provider's Art. 72 loop; an Art. 79(1) risk obliges informing the provider or distributor and the market-surveillance authority and suspending use, without undue delay; and a serious incident obliges immediate sequenced notification, provider first, on the severity-classed Art. 73 clock, with the deployer reporting itself if the provider cannot be reached. Produces __monitoring_observation__, from which __monitoring_observation_id__ and __escalation_trigger_class__ are extracted.

    CACAO step_id: action--e26d1a00-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e26d1a00-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000004', 'secops_ng.step.name': 'monitor_operation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'monitor_operation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e26d1a00-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000004', 'secops_ng.step.name': 'monitor_operation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'monitor_operation'})
        )
        from content.playbooks.eu_ai_act_deployer_obligations.primitives.monitoring import classify_monitoring_window
        __monitoring_observation__ = classify_monitoring_window(intended_use=__intended_use_determination__, oversight=__oversight_assignment__, window=__monitoring_window__, input_data=__input_data__, findings=__monitoring_findings__, evaluated_at=__evaluated_at__)

MONITOR_OPERATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def retain_logs_and_evidence(intended_use_determination: dict[str, object], oversight_assignment: dict[str, object], monitoring_observation: dict[str, object], fria_record: dict[str, object], log_retention: dict[str, object], workflow_id: str, execution_id: str, captured_at: str) -> dict[str, object]:
    """Record the retention disposition for the logs the system generates automatically, per Art. 26(6), and emit the dated cycle-evidence artifact joining the intended-use determination, the fundamental-rights record, the oversight assignment and the monitoring observation against __deployment_id__. The obligation binds only to logs under the deployer's control; for those the period is appropriate to the intended purpose and at least six months, unless applicable Union or national law provides otherwise, in either direction, which the record cites. The log store is an operator-owned surface. Produces __retention_evidence__, from which __retention_evidence_id__ is extracted.

    CACAO step_id: action--e26d1a00-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e26d1a00-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000006', 'secops_ng.step.name': 'retain_logs_and_evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'retain_logs_and_evidence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e26d1a00-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000006', 'secops_ng.step.name': 'retain_logs_and_evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'retain_logs_and_evidence'})
        )
        from content.playbooks.eu_ai_act_deployer_obligations.primitives.retention import compose_retention_evidence
        __retention_evidence__ = compose_retention_evidence(intended_use=__intended_use_determination__, oversight=__oversight_assignment__, observation=__monitoring_observation__, fria=__fria_record__, log_retention=__log_retention__, workflow_id=__workflow_id__, execution_id=__execution_id__, captured_at=__captured_at__)

RETAIN_LOGS_AND_EVIDENCE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookEuAiActDeployerObligationsV1Workflow:
    """CACAO v2 playbook for the operator-side EU AI Act (Regulation (EU) 2024/1689) Article 26 deployer-obligation lifecycle, gated by the Article 27 fundamental-rights impact assessment. Every other EU AI Act surface in this catalogue anchors on the provider — Art. 9 risk management, Art. 11 technical documentation, Art. 13 transparency, Art. 15 robustness, Art. 72 post-market monitoring, Art. 73 serious-incident reporting. This playbook is the first on the deployer side: the operator who runs a third-party high-risk AI system in production rather than placing one on the market. The lifecycle runs confirm-intended-use (Art. 26(1) instruction-conformant use and the Art. 26(7) worker-representative information duty as a pre-deployment gate), assign-human-oversight (Art. 26(2), recording competence, training, authority and support against a named person or role), monitor-operation (Art. 26(4) input-data relevance where the deployer controls the input surface, and the Art. 26(5) monitoring duty with its escalation edge to suspension and sequenced notification), assess-fundamental-rights-impact (Art. 27(1)(a)-(f), complementing rather than duplicating an existing GDPR Art. 35 DPIA per Art. 27(4), and notifying the market-surveillance authority of the result), and retain-logs-and-evidence (Art. 26(6) retention of automatically generated logs under deployer control for a period appropriate to the intended purpose and at least six months). CORE scope: the five action steps thread a deterministic variable chain from the external deployment identifier through the intended-use determination, the oversight assignment, the monitoring observation and its escalation trigger class, the fundamental-rights determination and the retention-evidence artifact, and each step carries its control, telemetry and metric bindings. The deployment register, the oversight-assignment record, the input-data control surface, the monitoring signal source, the FRIA template and the log store remain operator-owned adapter-bound surfaces — this playbook declares and evidences the contract against them and ships none of them. The EXTEND sibling lands the cookbook walkthrough and the deployer-side KPI/KRI pair.

    CACAO playbook id : playbook--e26d1a00-0000-4000-8000-000000000001
    stable_id         : playbook.eu_ai_act_deployer_obligations@v1
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--e26d1a00-0000-4000-8000-000000000001
    activities        : confirm_intended_use, assess_fundamental_rights_impact, assign_human_oversight, monitor_operation, retain_logs_and_evidence
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.eu_ai_act_deployer_obligations@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.eu_ai_act_deployer_obligations@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.eu_ai_act_deployer_obligations@v1'"
            )

WORKFLOW = PlaybookEuAiActDeployerObligationsV1Workflow
ACTIVITIES = (confirm_intended_use, assess_fundamental_rights_impact, assign_human_oversight, monitor_operation, retain_logs_and_evidence,)
RETRY_POLICIES = (CONFIRM_INTENDED_USE_RETRY_POLICY, ASSESS_FUNDAMENTAL_RIGHTS_IMPACT_RETRY_POLICY, ASSIGN_HUMAN_OVERSIGHT_RETRY_POLICY, MONITOR_OPERATION_RETRY_POLICY, RETAIN_LOGS_AND_EVIDENCE_RETRY_POLICY,)
