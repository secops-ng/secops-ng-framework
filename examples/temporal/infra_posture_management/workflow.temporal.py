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
async def collect_posture(raw_posture: str, scope_ref: str) -> str:
    """Walk the in-scope infrastructure manifest at __scope_ref__ and collect the current posture-state snapshot: per-resource configuration state read from the operator's posture sources (cloud account read APIs, identity-provider read APIs, network-baseline read APIs). Read-only by contract; the workflow MUST NOT mutate any resource on the collect path. Source endpoints are operator-configured — the framework ships no default non-EU endpoint and no hosted-SaaS dependency.

    CACAO step_id: action--06f06f06-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--06f06f06-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--06f06f06-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--06f06f06-0000-4000-8000-000000000002', 'secops_ng.step.name': 'collect-posture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'collect_posture'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--06f06f06-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--06f06f06-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--06f06f06-0000-4000-8000-000000000002', 'secops_ng.step.name': 'collect-posture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'collect_posture'})
        )
        from content.playbooks.infra_posture_management.primitives.collect import collect_posture_state
        __posture_state_ref__ = collect_posture_state(raw_posture=__raw_posture__, scope_ref=__scope_ref__)

COLLECT_POSTURE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def evaluate_controls(posture_state_ref: str, posture_policy: str) -> str:
    """Evaluate each control declared in the operator's posture policy against the collected posture state. Per (control_ref, scoped-resource-id) pair, classify the attestation state as effective, partially_effective, or ineffective; capture the deviation list (configuration values that differ from the declared baseline) on partially_effective / ineffective entries. Deterministic on the same posture snapshot and the same policy version — re-evaluation under the same inputs re-derives the same result set so a reviewer can re-derive the evaluation off the committed artifact.

    CACAO step_id: action--06f06f06-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--06f06f06-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--06f06f06-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--06f06f06-0000-4000-8000-000000000003', 'secops_ng.step.name': 'evaluate-controls', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evaluate_controls'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--06f06f06-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--06f06f06-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--06f06f06-0000-4000-8000-000000000003', 'secops_ng.step.name': 'evaluate-controls', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evaluate_controls'})
        )
        from content.playbooks.infra_posture_management.primitives.controls import evaluate_controls
        __control_evaluation_ref__ = evaluate_controls(posture_state=__posture_state_ref__, posture_policy=__posture_policy__)

EVALUATE_CONTROLS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def emit_posture_evidence(workflow_id: str, execution_id: str, compile_target: str, regulation_refs: str, control_refs: str, policy_version: str, posture_state_ref: str, control_evaluation_ref: str, evaluated_at: str, captured_at: str, source_url: str) -> str:
    """Combine the posture-state snapshot and the per-control evaluation result set into one posture-evidence artifact shaped against schemas/evidence/posture.schema.json (stream: posture). The artifact carries the workflow id, execution id, compile target, regulation_refs (nis2:art-21-2-a), control_refs, the evaluated_at timestamp, the policy version under which the evaluation ran, and the provenance envelope. Emission is byte-stable: same execution inputs, same compile target, same policy version re-derive the same artifact_id (SHA-256 of workflow_id|execution_id|compile_target|policy_version.value). Destination is operator-configured — no default non-EU endpoint.

    CACAO step_id: action--06f06f06-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--06f06f06-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--06f06f06-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--06f06f06-0000-4000-8000-000000000004', 'secops_ng.step.name': 'emit-posture-evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'emit_posture_evidence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--06f06f06-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--06f06f06-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--06f06f06-0000-4000-8000-000000000004', 'secops_ng.step.name': 'emit-posture-evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'emit_posture_evidence'})
        )
        from content.playbooks.infra_posture_management.primitives.artifact import build_posture_artifact
        __posture_artifact_ref__ = build_posture_artifact(workflow_id=__workflow_id__, execution_id=__execution_id__, compile_target=__compile_target__, regulation_refs=__regulation_refs__, control_refs=__control_refs__, policy_version=__policy_version__, posture_state=__posture_state_ref__, control_evaluation=__control_evaluation_ref__, evaluated_at=__evaluated_at__, captured_at=__captured_at__, source_url=__source_url__)

EMIT_POSTURE_EVIDENCE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookInfraPostureManagementV1Workflow:
    """Continuous infrastructure-posture-management workflow. On each scheduled re-execution, collect the current posture state of the in-scope infrastructure (cloud accounts, identity boundaries, network baseline), evaluate each declared control against that state, then emit one posture-evidence artifact shaped against schemas/evidence/posture.schema.json so a regulator-facing reviewer can re-derive what the posture was at evaluation time. CORE: the three action bodies bind to deterministic primitives in content.playbooks.infra_posture_management.primitives; the per-target byte-parity goldens land alongside the worked examples. Continuous variant of the F-WF-02 posture-audit workflow under NIS2 Article 21(2)(a).

    CACAO playbook id : playbook--06f06f06-0000-4000-8000-000000000001
    stable_id         : playbook.infra_posture_management@v1
    content_version   : 0.2.0
    maturity          : experimental
    workflow_start    : start--06f06f06-0000-4000-8000-000000000001
    activities        : collect_posture, evaluate_controls, emit_posture_evidence
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.infra_posture_management@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--06f06f06-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.infra_posture_management@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--06f06f06-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.2.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.infra_posture_management@v1'"
            )

WORKFLOW = PlaybookInfraPostureManagementV1Workflow
ACTIVITIES = (collect_posture, evaluate_controls, emit_posture_evidence,)
RETRY_POLICIES = (COLLECT_POSTURE_RETRY_POLICY, EVALUATE_CONTROLS_RETRY_POLICY, EMIT_POSTURE_EVIDENCE_RETRY_POLICY,)
