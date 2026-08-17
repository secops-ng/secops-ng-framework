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
async def ingest_contract(raw_contract: str, contract_ref: str) -> str:
    """Read the supplier-contract record referenced by __contract_ref__ from the operator-supplied document store and bind it to a normalised in-workflow contract record (contract_id, supplier_ref, effective_at, expires_at, jurisdiction). Read-only by contract; the workflow MUST NOT mutate the source document. Document-store endpoint is operator-configured — the framework ships no default non-EU endpoint and no hosted DMS dependency.

    CACAO step_id: action--10101010-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--10101010-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--10101010-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--10101010-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest-contract', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_contract'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--10101010-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--10101010-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--10101010-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest-contract', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'ingest_contract'})
        )
        from content.playbooks.contractual_obligations_tracker.primitives.ingest import ingest_contract
        __contract_record_ref__ = ingest_contract(raw_contract=__raw_contract__, contract_ref=__contract_ref__)

INGEST_CONTRACT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def extract_obligations(raw_obligations: str, contract_record_ref: str) -> str:
    """Walk the ingested contract record and extract the per-clause obligations the operator has accepted from that contract. Per obligation, capture the clause reference, the obligation text (operator-canonicalised string — no commentary, no rewrites at this layer), the obligation kind (security-control commitment, audit-right window, attestation cadence, sub-processor disclosure, breach-notification cadence, data-localisation, other), and any contractual review/expiry cadence the clause itself declares. Deterministic on the same contract record — re-extraction under the same inputs re-derives the same obligation set.

    CACAO step_id: action--10101010-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--10101010-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--10101010-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--10101010-0000-4000-8000-000000000003', 'secops_ng.step.name': 'extract-obligations', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'extract_obligations'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--10101010-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--10101010-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--10101010-0000-4000-8000-000000000003', 'secops_ng.step.name': 'extract-obligations', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'extract_obligations'})
        )
        from content.playbooks.contractual_obligations_tracker.primitives.obligations import extract_obligations
        __obligation_set_ref__ = extract_obligations(raw_obligations=__raw_obligations__, contract=__contract_record_ref__)

EXTRACT_OBLIGATIONS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def schedule_review(obligation_set_ref: str, review_policy: str, captured_at: str) -> str:
    """Derive the per-obligation review schedule from the extracted obligation set and the operator's review-cadence policy. For each obligation, compute the next-review-due timestamp deterministically from (last_reviewed_at, contractual cadence declared by the clause, operator-policy fallback cadence). Pure derivation — the workflow MUST NOT contact the supplier on this step, and the schedule is computed in-band from the obligation record, the policy, and the captured_at anchor alone.

    CACAO step_id: action--10101010-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--10101010-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--10101010-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--10101010-0000-4000-8000-000000000004', 'secops_ng.step.name': 'schedule-review', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'schedule_review'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--10101010-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--10101010-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--10101010-0000-4000-8000-000000000004', 'secops_ng.step.name': 'schedule-review', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'schedule_review'})
        )
        from content.playbooks.contractual_obligations_tracker.primitives.schedule import schedule_reviews
        __review_schedule_ref__ = schedule_reviews(obligations=__obligation_set_ref__, review_policy=__review_policy__, captured_at=__captured_at__)

SCHEDULE_REVIEW_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def emit_obligation_evidence(workflow_id: str, execution_id: str, regulation_refs: str, control_refs: str, contract_record_ref: str, obligation_set_ref: str, review_schedule_ref: str, owner_role: str, owner_assigned_at: str, captured_at: str, source_url: str) -> str:
    """Combine the ingested contract record, the extracted obligation set, and the per-obligation review schedule into one obligation-evidence artifact shaped against schemas/evidence/contractual-obligations.schema.json (stream: contractual-obligations). The artifact carries the workflow id, execution id, regulation_refs (nis2:art-21-2-d, optionally nis2:art-22 for the Union-level overlay), control_refs, the contract id, the obligation set, the per-obligation review-state, the owner block, and the provenance envelope. Emission is byte-stable: same execution inputs re-derive the same artifact_id (SHA-256 of workflow_id|execution_id|contract.contract_id|captured_at). Destination is operator-configured — no default non-EU endpoint.

    CACAO step_id: action--10101010-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--10101010-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--10101010-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--10101010-0000-4000-8000-000000000005', 'secops_ng.step.name': 'emit-obligation-evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'emit_obligation_evidence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--10101010-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--10101010-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--10101010-0000-4000-8000-000000000005', 'secops_ng.step.name': 'emit-obligation-evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'emit_obligation_evidence'})
        )
        from content.playbooks.contractual_obligations_tracker.primitives.artifact import build_obligation_artifact
        __obligation_artifact_ref__ = build_obligation_artifact(workflow_id=__workflow_id__, execution_id=__execution_id__, regulation_refs=__regulation_refs__, control_refs=__control_refs__, contract=__contract_record_ref__, obligations=__obligation_set_ref__, review_schedule=__review_schedule_ref__, owner_role=__owner_role__, owner_assigned_at=__owner_assigned_at__, captured_at=__captured_at__, source_url=__source_url__)

EMIT_OBLIGATION_EVIDENCE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookContractualObligationsTrackerV1Workflow:
    """Supplier-contract obligation tracking workflow under NIS2 Article 21(2)(d) supply-chain security. On each execution, ingest a supplier contract reference, extract the per-clause obligations the operator has accepted from that contract, schedule the next review date for each obligation against the operator's review-cadence policy, and emit one obligation-evidence artifact pinning the contract id, the extracted obligation set, the per-obligation review-state, and the provenance envelope. CORE: the four action bodies bind to deterministic primitives in content.playbooks.contractual_obligations_tracker.primitives; CORE-FANOUT-N8N pins the n8n adapter and the byte-parity golden — TMP and LG follow in sibling cards. Opens the NIS2 Article 21(2)(d) supply-chain control family at the workflow layer (per-entity supplier-contract obligation surface).

    CACAO playbook id : playbook--10101010-0000-4000-8000-000000000001
    stable_id         : playbook.contractual_obligations_tracker@v1
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--10101010-0000-4000-8000-000000000001
    activities        : ingest_contract, extract_obligations, schedule_review, emit_obligation_evidence
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.contractual_obligations_tracker@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--10101010-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.contractual_obligations_tracker@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--10101010-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.contractual_obligations_tracker@v1'"
            )

WORKFLOW = PlaybookContractualObligationsTrackerV1Workflow
ACTIVITIES = (ingest_contract, extract_obligations, schedule_review, emit_obligation_evidence,)
RETRY_POLICIES = (INGEST_CONTRACT_RETRY_POLICY, EXTRACT_OBLIGATIONS_RETRY_POLICY, SCHEDULE_REVIEW_RETRY_POLICY, EMIT_OBLIGATION_EVIDENCE_RETRY_POLICY,)
