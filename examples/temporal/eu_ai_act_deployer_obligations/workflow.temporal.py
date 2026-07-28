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
async def confirm_intended_use(deployment_id: str, system_reference: str) -> str:
    """reconcile the operator's declared deployment context against the intended purpose stated in the provider's instructions for use, per Art. 26(1), and record the conformance determination against __deployment_id__. The negative case is a first-class outcome: where the declared context exceeds the intended-purpose boundary the determination records that the deployment must not proceed on this system, and no downstream step fires. Where the deployer is an employer and the deployment is at the workplace, this step also gates on the Art. 26(7) duty to inform workers' representatives and affected workers BEFORE putting the system into service — the dated notice record is a precondition of the determination, not a parallel task, because a deployment that proceeds without it cannot be remediated after the fact. Read-only against the operator's deployment register and the provider-supplied instructions; the register is an adapter-bound surface this playbook does not author.

    CACAO step_id: action--e26d1a00-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e26d1a00-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000002', 'secops_ng.step.name': 'confirm_intended_use', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'confirm_intended_use'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e26d1a00-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000002', 'secops_ng.step.name': 'confirm_intended_use', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'confirm_intended_use'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--e26d1a00-0000-4000-8000-000000000002'"
        )

CONFIRM_INTENDED_USE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def assign_human_oversight(deployment_id: str, intended_use_determination_id: str) -> str:
    """assign human oversight of the deployment to natural persons per Art. 26(2) and record the assignment against __deployment_id__. The obligation has four independently checkable limbs and the record names the assignee against each rather than asserting oversight generically: competence, training, authority, and the necessary support. Competence and training bind to the operator's training-attestation surface; authority is a delegation record the operator's governance surface owns. The capability set an oversight assignee must be able to exercise — understand the system's capacity and limits, remain aware of automation bias, correctly interpret output, decide not to use the system or disregard its output, and intervene or halt — is fixed by Art. 14(4) and is mapped by a sibling card; on its merge this step's reference bundle gains the Art. 14 anchor.

    CACAO step_id: action--e26d1a00-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e26d1a00-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000003', 'secops_ng.step.name': 'assign_human_oversight', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assign_human_oversight'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e26d1a00-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000003', 'secops_ng.step.name': 'assign_human_oversight', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assign_human_oversight'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--e26d1a00-0000-4000-8000-000000000003'"
        )

ASSIGN_HUMAN_OVERSIGHT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def monitor_operation(deployment_id: str, system_reference: str, oversight_assignment_id: str) -> dict[str, object]:
    """monitor operation of the high-risk AI system on the basis of the instructions for use, per Art. 26(5), and record the per-window monitoring observation against __deployment_id__. Where the deployer exercises control over the input data, the same window records the Art. 26(4) determination that input data is relevant and sufficiently representative in view of the intended purpose; where it does not exercise that control, the dated determination of non-control is itself the evidence and no representativeness assessment is owed. This step carries the lifecycle's only escalation edge, and its three triggers have different consequences that must not be collapsed: routine observations feed the provider's Art. 72 post-market loop; a determination that use in accordance with the instructions may present a risk within the meaning of Art. 79(1) compels informing the provider or distributor and the market-surveillance authority AND suspending use, without undue delay; and identification of a serious incident compels immediate sequenced notification — provider first, then importer or distributor, then the market-surveillance authorities. The serious-incident branch hands off to the provider-side Art. 73 reporting chain; the deployer's notification is an input to that chain, never a substitute for it.

    CACAO step_id: action--e26d1a00-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e26d1a00-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000004', 'secops_ng.step.name': 'monitor_operation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'monitor_operation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e26d1a00-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000004', 'secops_ng.step.name': 'monitor_operation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'monitor_operation'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--e26d1a00-0000-4000-8000-000000000004'"
        )

MONITOR_OPERATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def assess_fundamental_rights_impact(deployment_id: str, intended_use_determination_id: str) -> str:
    """perform the Art. 27 fundamental-rights impact assessment prior to deploying, and record it against __deployment_id__. The step applies only to deployers in scope of Art. 27: bodies governed by public law, private entities providing public services, and deployers of the Annex III(5)(b)-(c) creditworthiness and life-and-health-insurance risk-assessment systems — so the first recorded output is the in-scope determination, and an out-of-scope determination closes the step with a dated record rather than an empty assessment. In scope, the emitted assessment satisfies the six Art. 27(1)(a)-(f) elements as a checklist: the processes the system will be used in, the period and frequency of intended use, the categories of natural persons and groups likely to be affected, the specific risks of harm to those categories informed by the Art. 13 provider information, the implementation of human-oversight measures, and the measures on risk materialisation including internal governance and complaint mechanisms. Per Art. 27(4) the assessment complements rather than duplicates an existing GDPR Art. 35 DPIA: where the operator holds a DPIA for the same processing, the step reads it and records which Art. 27(1) elements it already satisfies, assessing only the remainder. The step closes by notifying the market-surveillance authority of the results; the Art. 27(5) template is not yet published by the AI Office, so the notification contract is declared and the dated notification record emitted, rather than a template shape being invented.

    CACAO step_id: action--e26d1a00-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e26d1a00-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000005', 'secops_ng.step.name': 'assess_fundamental_rights_impact', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assess_fundamental_rights_impact'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e26d1a00-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000005', 'secops_ng.step.name': 'assess_fundamental_rights_impact', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assess_fundamental_rights_impact'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--e26d1a00-0000-4000-8000-000000000005'"
        )

ASSESS_FUNDAMENTAL_RIGHTS_IMPACT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def retain_logs_and_evidence(deployment_id: str, oversight_assignment_id: str, monitoring_observation_id: str, fria_determination_id: str) -> str:
    """record the retention disposition for the logs the high-risk AI system generates automatically, per Art. 26(6), and emit the dated cycle-evidence artifact joining the intended-use determination, the oversight assignment, the monitoring observations, and the fundamental-rights assessment against __deployment_id__. The obligation binds only to the extent those logs are under the deployer's control, so the record states the control determination alongside the retention period applied. Six months is the floor, not the target: the governing standard is a period appropriate to the intended purpose of the system, and applicable Union or national law may require longer. The log store is an operator-owned adapter-bound surface — this step declares and evidences the retention contract and never ships a store. The content those logs must carry is fixed by Art. 12; a sibling card lands that mapping and this step's reference bundle gains the anchor on its merge.

    CACAO step_id: action--e26d1a00-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--e26d1a00-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000006', 'secops_ng.step.name': 'retain_logs_and_evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'retain_logs_and_evidence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--e26d1a00-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--e26d1a00-0000-4000-8000-000000000006', 'secops_ng.step.name': 'retain_logs_and_evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'retain_logs_and_evidence'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--e26d1a00-0000-4000-8000-000000000006'"
        )

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
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--e26d1a00-0000-4000-8000-000000000001
    activities        : confirm_intended_use, assign_human_oversight, monitor_operation, assess_fundamental_rights_impact, retain_logs_and_evidence
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.eu_ai_act_deployer_obligations@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.eu_ai_act_deployer_obligations@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--e26d1a00-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.eu_ai_act_deployer_obligations@v1'"
            )

WORKFLOW = PlaybookEuAiActDeployerObligationsV1Workflow
ACTIVITIES = (confirm_intended_use, assign_human_oversight, monitor_operation, assess_fundamental_rights_impact, retain_logs_and_evidence,)
RETRY_POLICIES = (CONFIRM_INTENDED_USE_RETRY_POLICY, ASSIGN_HUMAN_OVERSIGHT_RETRY_POLICY, MONITOR_OPERATION_RETRY_POLICY, ASSESS_FUNDAMENTAL_RIGHTS_IMPACT_RETRY_POLICY, RETAIN_LOGS_AND_EVIDENCE_RETRY_POLICY,)
