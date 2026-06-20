# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.contractual_obligations_tracker@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookContractualObligationsTrackerV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.contractual_obligations_tracker@v1.

    Playbook id: playbook--10101010-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __workflow_id__
    # Stable workflow stable-id from content/playbooks/<workflow>/. Joined into the obligation-evidence artifact_id derivation; constant per playbook (`contractual_obligations_tracker`) and supplied as a flat token so the CORE primitive call mirrors the F-WF-06 / F-WF-07 binding convention.
    workflow_id: str
    # playbook_variable: __execution_id__
    # Per-execution identifier issued by the compile target's workflow runtime (n8n execution id, Temporal workflow run id, LangGraph thread/checkpoint id). Pinned by the upstream runtime; the workflow reads it for the obligation-evidence artifact join.
    execution_id: str
    # playbook_variable: __contract_ref__
    # Opaque operator-side pointer to the supplier-contract record under review on this execution. Operator-configured; the workflow reads it as the opaque pointer to a contract held in the operator's document store. The framework ships no default document-store endpoint and no vendor SDK bundling — the operator supplies whatever store is in scope (a sovereign EU object store, an on-prem document management system, a Git-managed contract repository).
    contract_ref: str
    # playbook_variable: __raw_contract__
    # Operator-supplied JSON-native supplier-contract record the runtime fetched from the document store pointed at by `__contract_ref__`. Required keys: `contract_id`, `supplier_ref`, `effective_at`; optional: `expires_at`, `jurisdiction`. The framework ships the schema, not the catalogue.
    raw_contract: str
    # playbook_variable: __raw_obligations__
    # Operator-supplied JSON-native list of obligation records extracted from the contract upstream. One entry per declared obligation with `obligation_id`, `clause_ref`, `obligation_kind`, `text`, and optional `cadence`. The framework does not parse contract text; it canonicalises and validates the operator-supplied list.
    raw_obligations: str
    # playbook_variable: __review_policy__
    # Operator-supplied JSON-native review-cadence policy. Required keys: `fallback_cadence` (ISO-8601 duration), `due_soon_window` (ISO-8601 duration); optional `last_reviewed_at` map and `waived_obligation_ids` list. Pinned by the operator's procurement-governance config; the workflow does no calendar arithmetic outside this policy.
    review_policy: str
    # playbook_variable: __regulation_refs__
    # Schema-shaped regulation references the artifact attests (typically `["nis2:art-21-2-d"]`, optionally `nis2:art-22` for the Union-level Cooperation-Group overlay). JSON-native list; pinned by the compile target's boot config so the operator can extend without re-compiling.
    regulation_refs: str
    # playbook_variable: __control_refs__
    # Control stable-ids the artifact attests. JSON-native list; the primitive validates each entry against the `control.<id>@v<n>` shape. Typically `control.supplier_inventory@v1` and `control.provider_attestation@v1`.
    control_refs: str
    # playbook_variable: __owner_role__
    # Role-shaped ownership pointer for the supplier-inventory attestation chain — a working-group mailbox, a generic role title, or a community handle. Personal names are out of scope per AGENTS.md §3 and rejected at the artifact-builder boundary.
    owner_role: str
    # playbook_variable: __owner_assigned_at__
    # ISO-8601 date (`YYYY-MM-DD`) on which the role was assigned ownership of the contractual-obligations attestation chain.
    owner_assigned_at: str
    # playbook_variable: __captured_at__
    # ISO-8601 UTC second-precision timestamp (`...Z`) pinned at emission time by the upstream runtime; carried on the artifact's top-level `captured_at`, on `provenance.captured_at`, and as the time anchor the review-schedule primitive derives state against.
    captured_at: str
    # playbook_variable: __source_url__
    # URL of the workflow run that produced this artifact. Compile targets supply their own run-id URLs; the URL itself is opaque to the schema.
    source_url: str
    # playbook_variable: __contract_record_ref__
    # Pointer to the canonical contract block produced by ingest-contract — contract-id keyed, supplier-classification and effective-date envelope valued. Consumed by extract-obligations and emit-obligation-evidence.
    contract_record_ref: str
    # playbook_variable: __obligation_set_ref__
    # Pointer to the per-contract obligation set produced by extract-obligations — one entry per declared obligation with the clause reference, obligation text, obligation kind, and the contractual review/expiry cadence. Sorted by `obligation_id` for byte-stable replay. Consumed by schedule-review and emit-obligation-evidence.
    obligation_set_ref: str
    # playbook_variable: __review_schedule_ref__
    # Pointer to the per-obligation review schedule produced by schedule-review — one entry per obligation paired one-to-one with `__obligation_set_ref__`, with the next-review-due timestamp derived deterministically from the obligation's contractual cadence and the operator's review-policy. Consumed by emit-obligation-evidence.
    review_schedule_ref: str
    # playbook_variable: __obligation_artifact_ref__
    # Pointer to the obligation-evidence artifact emitted by emit-obligation-evidence, shaped against schemas/evidence/contractual-obligations.schema.json.
    obligation_artifact_ref: str
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
async def ingest_contract(raw_contract: str, contract_ref: str) -> str:
    """Read the supplier-contract record referenced by __contract_ref__ from the operator-supplied document store and bind it to a normalised in-workflow contract record (contract_id, supplier_ref, effective_at, expires_at, jurisdiction). Read-only by contract; the workflow MUST NOT mutate the source document. Document-store endpoint is operator-configured — the framework ships no default non-EU endpoint and no hosted DMS dependency.

    CACAO step_id : action--10101010-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--10101010-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--10101010-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--10101010-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest-contract', 'secops_ng.tool.name': 'ingest_contract', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--10101010-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--10101010-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--10101010-0000-4000-8000-000000000002', 'secops_ng.step.name': 'ingest-contract', 'secops_ng.tool.name': 'ingest_contract', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.contractual_obligations_tracker.primitives.ingest import ingest_contract
        __contract_record_ref__ = ingest_contract(raw_contract=__raw_contract__, contract_ref=__contract_ref__)

@tool
async def extract_obligations(raw_obligations: str, contract_record_ref: str) -> str:
    """Walk the ingested contract record and extract the per-clause obligations the operator has accepted from that contract. Per obligation, capture the clause reference, the obligation text (operator-canonicalised string — no commentary, no rewrites at this layer), the obligation kind (security-control commitment, audit-right window, attestation cadence, sub-processor disclosure, breach-notification cadence, data-localisation, other), and any contractual review/expiry cadence the clause itself declares. Deterministic on the same contract record — re-extraction under the same inputs re-derives the same obligation set.

    CACAO step_id : action--10101010-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--10101010-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--10101010-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--10101010-0000-4000-8000-000000000003', 'secops_ng.step.name': 'extract-obligations', 'secops_ng.tool.name': 'extract_obligations', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--10101010-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--10101010-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--10101010-0000-4000-8000-000000000003', 'secops_ng.step.name': 'extract-obligations', 'secops_ng.tool.name': 'extract_obligations', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.contractual_obligations_tracker.primitives.obligations import extract_obligations
        __obligation_set_ref__ = extract_obligations(raw_obligations=__raw_obligations__, contract=__contract_record_ref__)

@tool
async def schedule_review(obligation_set_ref: str, review_policy: str, captured_at: str) -> str:
    """Derive the per-obligation review schedule from the extracted obligation set and the operator's review-cadence policy. For each obligation, compute the next-review-due timestamp deterministically from (last_reviewed_at, contractual cadence declared by the clause, operator-policy fallback cadence). Pure derivation — the workflow MUST NOT contact the supplier on this step, and the schedule is computed in-band from the obligation record, the policy, and the captured_at anchor alone.

    CACAO step_id : action--10101010-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--10101010-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--10101010-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--10101010-0000-4000-8000-000000000004', 'secops_ng.step.name': 'schedule-review', 'secops_ng.tool.name': 'schedule_review', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--10101010-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--10101010-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--10101010-0000-4000-8000-000000000004', 'secops_ng.step.name': 'schedule-review', 'secops_ng.tool.name': 'schedule_review', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.contractual_obligations_tracker.primitives.schedule import schedule_reviews
        __review_schedule_ref__ = schedule_reviews(obligations=__obligation_set_ref__, review_policy=__review_policy__, captured_at=__captured_at__)

@tool
async def emit_obligation_evidence(workflow_id: str, execution_id: str, regulation_refs: str, control_refs: str, contract_record_ref: str, obligation_set_ref: str, review_schedule_ref: str, owner_role: str, owner_assigned_at: str, captured_at: str, source_url: str) -> str:
    """Combine the ingested contract record, the extracted obligation set, and the per-obligation review schedule into one obligation-evidence artifact shaped against schemas/evidence/contractual-obligations.schema.json (stream: contractual-obligations). The artifact carries the workflow id, execution id, regulation_refs (nis2:art-21-2-d, optionally nis2:art-22 for the Union-level overlay), control_refs, the contract id, the obligation set, the per-obligation review-state, the owner block, and the provenance envelope. Emission is byte-stable: same execution inputs re-derive the same artifact_id (SHA-256 of workflow_id|execution_id|contract.contract_id|captured_at). Destination is operator-configured — no default non-EU endpoint.

    CACAO step_id : action--10101010-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--10101010-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--10101010-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--10101010-0000-4000-8000-000000000005', 'secops_ng.step.name': 'emit-obligation-evidence', 'secops_ng.tool.name': 'emit_obligation_evidence', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--10101010-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--10101010-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--10101010-0000-4000-8000-000000000005', 'secops_ng.step.name': 'emit-obligation-evidence', 'secops_ng.tool.name': 'emit_obligation_evidence', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.contractual_obligations_tracker.primitives.artifact import build_obligation_artifact
        __obligation_artifact_ref__ = build_obligation_artifact(workflow_id=__workflow_id__, execution_id=__execution_id__, regulation_refs=__regulation_refs__, control_refs=__control_refs__, contract=__contract_record_ref__, obligations=__obligation_set_ref__, review_schedule=__review_schedule_ref__, owner_role=__owner_role__, owner_assigned_at=__owner_assigned_at__, captured_at=__captured_at__, source_url=__source_url__)

async def llm_step(state: PlaybookContractualObligationsTrackerV1State) -> dict:
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

STATE_SCHEMA = PlaybookContractualObligationsTrackerV1State
TOOLS = (ingest_contract, extract_obligations, schedule_review, emit_obligation_evidence,)
AGENTIC_HOOK = llm_step

