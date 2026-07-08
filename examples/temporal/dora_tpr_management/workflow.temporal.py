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
async def onboarding_risk_assessment(provider_handle: str, function_supported: str) -> dict[str, object]:
    """TODO (CORE): pre-contractual risk-assessment primitive. The action body scores a candidate ICT third-party service provider against the operator's documented pre-contractual risk-assessment rubric, keyed on the function the provider supports (`__function_supported__`) and the provider handle (`__provider_handle__`). The rubric axes DORA Article 28(4) names — function criticality (does the function this provider supports qualify as critical or important under the operator's declared critical-or-important-function register), sub-outsourcing chain (declared sub-outsourcing depth and per-node criticality carry), data-location (EU / EEA / third-country processing locations declared by the provider), and concentration exposure (the operator's current concentration on this provider on the same function axis) — are composed into the closed risk-assessment block the register row consumes. Sets `__criticality_determination__` and `__risk_assessment_ref__`. Read-only against the provider's declared shape: the assessment step does not mutate the provider's declared attestations, it composes an operator-side view keyed on the rubric axes. SKELETON pins the topology + ID + regulatory anchor refs; the deterministic rubric application, sub-outsourcing chain traversal, and concentration-risk scoring are owned by CORE-PRIM.

    CACAO step_id: action--d07a7970-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d07a7970-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d07a7970-0000-4000-8000-000000000002', 'secops_ng.step.name': 'onboarding risk assessment', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'onboarding_risk_assessment'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d07a7970-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d07a7970-0000-4000-8000-000000000002', 'secops_ng.step.name': 'onboarding risk assessment', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'onboarding_risk_assessment'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d07a7970-0000-4000-8000-000000000002'"
        )

ONBOARDING_RISK_ASSESSMENT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def contractual_provisions_check(provider_handle: str, contract_ref: str) -> str:
    """TODO (CORE): Article 30 clause-presence verification primitive. The action body reads the negotiated ICT third-party contract instance (`__contract_ref__`) and verifies the DORA Article 30(2) and 30(3) closed clause set is present — service description, data-processing locations, exit-strategy obligations, audit rights, termination rights, sub-contracting conditions, service-level descriptions, insolvency and resolution provisions. Each clause is scored present / present_with_deviation / absent against the operator's declared clause-shape rubric; the block carries the per-clause status plus the deviation notes for downstream register-row composition. Sets `__clause_check_ref__`. Absent-clause status is a hard signal onto the register row: the row is still composed (the register carries an entry for every ICT third-party service provider under contract, per Article 28), but the row is flagged as clause-incomplete so the operator's governance surface can drive the negotiation lever. SKELETON pins the topology + ID + regulatory anchor refs; the deterministic clause-presence check body, deviation-note capture, and per-clause-status vocabulary binding are owned by CORE-PRIM.

    CACAO step_id: action--d07a7970-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d07a7970-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d07a7970-0000-4000-8000-000000000003', 'secops_ng.step.name': 'contractual provisions check', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'contractual_provisions_check'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d07a7970-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d07a7970-0000-4000-8000-000000000003', 'secops_ng.step.name': 'contractual provisions check', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'contractual_provisions_check'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d07a7970-0000-4000-8000-000000000003'"
        )

CONTRACTUAL_PROVISIONS_CHECK_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def register_entry(provider_handle: str, function_supported: str, criticality_determination: str, risk_assessment_ref: str, clause_check_ref: str, captured_at: str) -> str:
    """TODO (CORE): Article 28 register-of-information row-composition primitive. The action body composes and publishes the Article 28 register row for the provider on the current lifecycle window, joining `__provider_handle__`, `__function_supported__`, `__criticality_determination__`, `__risk_assessment_ref__`, and `__clause_check_ref__` into the register-row shape the Commission Implementing Regulation (EU) 2024/2956 ITS on standard templates for the register of information declares. The row is content-addressed against the artifact_id derivation SHA-256(workflow_id|execution_id|captured_at) so a replay of the same window re-derives byte-identical bytes (the byte-parity contract the CORE-FANOUT siblings assert against). Sets `__register_row_id__`. The primitive only produces the JSON-native register row; the durable emitter wiring (register-artifact-path, content-addressed filename, atomic write, notification of the operator's accountability owner) is owned by the per-target compilers and lands with the CORE-FANOUT sibling cards. Read-only against the risk-assessment and clause-check blocks by contract; the row composition does not mutate the upstream blocks.

    CACAO step_id: action--d07a7970-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d07a7970-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d07a7970-0000-4000-8000-000000000004', 'secops_ng.step.name': 'register entry', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'register_entry'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d07a7970-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d07a7970-0000-4000-8000-000000000004', 'secops_ng.step.name': 'register entry', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'register_entry'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d07a7970-0000-4000-8000-000000000004'"
        )

REGISTER_ENTRY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def periodic_review(provider_handle: str, register_row_id: str, review_window: str, runtime_supply_chain_evidence_ref: str) -> str:
    """TODO (CORE): periodic-review-and-drift-detection primitive. The action body re-reads the published register row (`__register_row_id__`) on the operator's documented periodic-review cadence (`__review_window__`) and re-scores criticality against the current runtime supply-chain-evidence stream (`__runtime_supply_chain_evidence_ref__` — the artifact set playbook.supply_chain_security@v1 has emitted against this provider handle since the last invocation). The re-score composes three inputs: (i) the standing risk-assessment block, (ii) any material change declared on the contract, the sub-outsourcing chain, or the function supported since the last invocation, and (iii) the runtime-drift verdict derived from the supply-chain-evidence stream (an active `watch` or `confirmed_compromise` verdict against the provider re-enters the register on this join). The primitive emits a re-scored criticality determination, re-emits the register row on the current window, and pins the operator's declared next-review-window anchor for the next invocation. Sets `__periodic_review_ref__`. When a re-scored criticality bucket crosses a documented exit-decision threshold, the operator's governance surface consumes the review block to invoke exit-assessment; the review primitive itself does not auto-invoke exit — exit is always an operator decision. SKELETON pins the topology + ID + regulatory anchor refs; the deterministic re-scoring, runtime-drift join, and next-window anchor derivation are owned by CORE-PRIM.

    CACAO step_id: action--d07a7970-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d07a7970-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d07a7970-0000-4000-8000-000000000005', 'secops_ng.step.name': 'periodic review', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'periodic_review'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d07a7970-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d07a7970-0000-4000-8000-000000000005', 'secops_ng.step.name': 'periodic review', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'periodic_review'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d07a7970-0000-4000-8000-000000000005'"
        )

PERIODIC_REVIEW_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def exit_assessment(provider_handle: str, register_row_id: str, risk_assessment_ref: str, clause_check_ref: str, periodic_review_ref: str, exit_trigger: str, captured_at: str) -> str:
    """TODO (CORE): Article 28(8) exit-strategy attestation-emission primitive. The action body composes and publishes the dated exit-assessment attestation for the provider when the operator invokes the step against a documented exit trigger (`__exit_trigger__`) — operator election, periodic-review failure, contractual termination, provider insolvency, or regulatory direction. The attestation joins the register row identifier, the standing risk-assessment block, the clause-check block, and the periodic-review block so the audit-evident chain from onboarding to exit is closed in one artifact. The artifact_id is derived SHA-256(workflow_id|execution_id|captured_at) so the byte-parity contract carries onto the exit surface. Sets `__exit_attestation_id__`. The primitive only produces the JSON-native attestation record; the durable emitter wiring is owned by the per-target compilers. The record discharges the Article 28(8) exit-strategy discipline the operator carries against every critical-or-important-function ICT third-party service provider; the destination sink is operator-configured (no default non-EU endpoint per the public-bar discipline).

    CACAO step_id: action--d07a7970-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d07a7970-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d07a7970-0000-4000-8000-000000000006', 'secops_ng.step.name': 'exit assessment', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'exit_assessment'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d07a7970-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d07a7970-0000-4000-8000-000000000006', 'secops_ng.step.name': 'exit assessment', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'exit_assessment'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d07a7970-0000-4000-8000-000000000006'"
        )

EXIT_ASSESSMENT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookDoraTprManagementV1Workflow:
    """SKELETON — CACAO v2 scaffold for the DORA Chapter V ICT third-party risk management workflow an EU financial entity operates against every ICT third-party service provider it contracts with. Anchored on DORA Regulation (EU) 2022/2554 Article 28 (general principles for the use of ICT third-party service providers — the third-party register, pre-contractual risk assessment, criticality determination, sub-outsourcing surface, and concentration-risk discipline) and Article 30 (key contractual provisions — the closed clause set every ICT third-party contract must carry). Distinct in scope from playbook.supply_chain_security@v1: supply_chain_security is the runtime supply-chain-signal spine (SBOM correlation, supplier-attestation lookup, per-execution supply-chain-evidence emission against NIS2 Article 21(2)(d)); this playbook is the contract-lifecycle third-party governance spine keyed on the DORA Chapter V financial-entity obligation set. Distinct in cadence from playbook.contractual_obligations_tracker@v1: contractual_obligations_tracker is the per-obligation clause-attestation cadence a financial entity runs against every declared contractual obligation regardless of counterparty type; this playbook is the whole-lifecycle third-party governance workflow the DORA register anchors, keyed on the five DORA Chapter V lifecycle atoms onboarding-risk-assessment → contractual-provisions-check → register-entry → periodic-review → exit-assessment. The lifecycle chains five steps: onboarding-risk-assessment scores a candidate ICT third-party service provider against the operator's documented pre-contractual risk-assessment rubric (function criticality, sub-outsourcing chain, data-location, concentration exposure) → contractual-provisions-check verifies the negotiated contract carries the Article 30(2) and 30(3) closed clause set (service description, data-processing locations, exit-strategy obligations, audit rights, termination rights, sub-contracting conditions) → register-entry composes and publishes the Article 28 register-of-information row for the provider, joined to the criticality determination and the accepted-clause set → periodic-review re-reads the register row on the operator's documented review cadence and re-scores criticality against the current runtime supply-chain-evidence stream so drift on the supplier surface re-enters the register → exit-assessment discharges the Article 28(8) exit-strategy discipline when the operator elects to terminate the arrangement or the provider fails a review, emitting the dated exit-assessment attestation the operator's evidence store consumes. SKELETON pins the topology + ID + regulatory anchor refs; the per-step primitive bodies (deterministic rubric application for the risk assessment, deterministic clause-presence check for the contractual-provisions verification, register-row composition against the Article 28 shape, drift detection against the runtime supply-chain-evidence stream, exit-assessment attestation emission) land in the CORE-PRIM sibling. Compile-target fan-out (n8n / Temporal / LangGraph) and per-target byte-parity goldens land in the CORE-FANOUT sibling. Inbound wiring under content/mappings/dora/ (article-19-and-28.yaml + a new article-30.yaml entry) lands in the CORE-EXTEND sibling; the SKELETON is deliberately orphan-tolerant for the 7-day grace window the G-02 orphan-CI lane declares.

    CACAO playbook id : playbook--d07a7970-0000-4000-8000-000000000001
    stable_id         : playbook.dora_tpr_management@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--d07a7970-0000-4000-8000-000000000001
    activities        : onboarding_risk_assessment, contractual_provisions_check, register_entry, periodic_review, exit_assessment
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.dora_tpr_management@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.dora_tpr_management@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.dora_tpr_management@v1'"
            )

WORKFLOW = PlaybookDoraTprManagementV1Workflow
ACTIVITIES = (onboarding_risk_assessment, contractual_provisions_check, register_entry, periodic_review, exit_assessment,)
RETRY_POLICIES = (ONBOARDING_RISK_ASSESSMENT_RETRY_POLICY, CONTRACTUAL_PROVISIONS_CHECK_RETRY_POLICY, REGISTER_ENTRY_RETRY_POLICY, PERIODIC_REVIEW_RETRY_POLICY, EXIT_ASSESSMENT_RETRY_POLICY,)
