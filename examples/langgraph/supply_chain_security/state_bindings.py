# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.supply_chain_security@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookSupplyChainSecurityV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.supply_chain_security@v1.

    Playbook id: playbook--5c5c5c5c-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __workflow_id__
    # Stable workflow stable-id from content/playbooks/<workflow>/. Joined into the supply-chain-evidence artifact_id derivation; constant per playbook (`supply_chain_security`) and supplied as a flat token so the CORE primitive call mirrors the F-WF-08 / F-WF-10 binding convention.
    workflow_id: str
    # playbook_variable: __execution_id__
    # Per-execution identifier issued by the compile target's workflow runtime (n8n execution id, Temporal workflow run id, LangGraph thread/checkpoint id). Pinned by the upstream runtime; the workflow reads it for the supply-chain-evidence artifact join.
    execution_id: str
    # playbook_variable: __signal_class__
    # Short operator-defined token classifying the upstream supply-chain signal source. One of `sbom_diff`, `supplier_attestation`, `upstream_advisory`, `threat_intel`, `operator_report`. Pinned by the compile target's boot config so the assess-supplier-signal primitive can canonicalise without a free-text shape.
    signal_class: str
    # playbook_variable: __signal_verdict__
    # Operator-side disposition emitted by the scoring policy upstream of this workflow. One of `no_impact`, `watch`, `confirmed_compromise`. The framework ships no default scoring policy; the operator's compile target supplies the verdict per its own SBOM-correlation / supplier-attestation / threat-intel logic.
    signal_verdict: str
    # playbook_variable: __signal_supplier_handle__
    # Stable operator-side supplier identifier in `provider.<id>@v<n>` shape — mirrors the F-CP-03 dependencies[].provider_id vocabulary so the assessment round-trips into the supply-chain-evidence artifact without re-canonicalisation. Personal names and contact-shaped strings fail loud at the assess-supplier-signal primitive boundary per the public-bar discipline.
    signal_supplier_handle: str
    # playbook_variable: __signal_component_set__
    # JSON-native list of PURL pointers (`pkg:<type>/<namespace?>/<name>@<version?>`) for the components implicated on this execution. Operator-supplied; the assess-supplier-signal primitive canonicalises (NFKC + dedup + sort) so two replays of the same signal collapse to byte-identical bytes. Empty list is valid for supplier-level signals or `no_impact` verdicts.
    signal_component_set: str
    # playbook_variable: __signal_received_at__
    # ISO-8601 UTC second-precision timestamp (`...Z`) pinned by the upstream signal source at the moment the signal was received. Not derived in the workflow; no clock reads.
    signal_received_at: str
    # playbook_variable: __signal_id__
    # Optional opaque operator-side signal identifier for cross-referencing back to the source feed entry. Free string, <= 200 chars. Pinned by the compile target's signal-ingest path.
    signal_id: str
    # playbook_variable: __signal_scoring_notes__
    # Optional short operator-side rationale for the scoring decision. Free text, <= 400 chars. Captured on the assessment block for downstream review.
    signal_scoring_notes: str
    # playbook_variable: __assessment_ref__
    # Pointer to the closed supply-chain-impact assessment block produced by assess-supplier-signal — verdict-keyed (no_impact | watch | confirmed_compromise), affected-supplier-handle and affected-component-set valued, received_at and signal_class anchored. Consumed by emit-supply-chain-evidence.
    assessment_ref: str
    # playbook_variable: __dependencies__
    # JSON-native list of dependency objects matching the F-CP-03 dependencies[] shape (provider_id, kind, call_count, sovereignty_classification, attestation, optional version / risk_notes). Operator-supplied — the framework ships no default dependency catalogue; the operator's supplier-inventory is the source of truth. The assessment block's affected_supplier_handle MUST appear among these entries or the emit-supply-chain-evidence primitive rejects the call (no silently-orphaned artifacts).
    dependencies: str
    # playbook_variable: __aggregates__
    # Optional JSON-native pre-computed aggregate counts the operator already tracks (total_providers, sovereign_count, eu_hosted_count, non_eu_count, ai_provider_count). Forwarded verbatim onto the artifact when present; omitted entirely when absent.
    aggregates: str
    # playbook_variable: __regulation_refs__
    # Schema-shaped regulation references the artifact attests (typically `["nis2:art-21-2-d"]`). JSON-native list; pinned by the compile target's boot config so the operator can extend without re-compiling.
    regulation_refs: str
    # playbook_variable: __control_refs__
    # Control stable-ids the artifact attests. JSON-native list; the shared emitter validates each entry against the `control.<id>@v<n>` shape.
    control_refs: str
    # playbook_variable: __owner_role__
    # Role-shaped operator-side owner handle for the supplier-inventory attestation (non-empty, <= 200 chars). Carried on the artifact's owner block. Personal names are out of scope per the public-bar discipline.
    owner_role: str
    # playbook_variable: __owner_assigned_at__
    # ISO-8601 date (`YYYY-MM-DD`) the named owner role was assigned the supplier-inventory attestation. Pinned by operator policy; not derived in the workflow.
    owner_assigned_at: str
    # playbook_variable: __captured_at__
    # ISO-8601 UTC second-precision timestamp (`...Z`) pinned at emission time by the upstream runtime; carried on the artifact's top-level captured_at and on provenance.captured_at. Part of the deterministic artifact_id derivation alongside workflow_id and execution_id.
    captured_at: str
    # playbook_variable: __source_url__
    # URL of the workflow run that produced this artifact. Compile targets supply their own run-id URLs; the URL itself is opaque to the schema.
    source_url: str
    # playbook_variable: __supply_chain_artifact_ref__
    # Pointer to the supply-chain-evidence artifact emitted by emit-supply-chain-evidence, shaped against schemas/evidence/supply-chain.schema.json. Anchored against the F-CP-03 supply-chain evidence stream so the NIS2 Article 21(2)(d) supplier-security obligation has a per-execution audit-trail entry.
    supply_chain_artifact_ref: str
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
async def assess_supplier_signal(signal_class: str, signal_verdict: str, signal_supplier_handle: str, signal_received_at: str, signal_component_set: str, signal_id: str, signal_scoring_notes: str) -> str:
    """Canonicalise the operator-supplied raw supply-chain signal envelope into the closed assessment block the downstream emit step consumes. The operator's compile target performs the upstream I/O (signal-feed ingestion, SBOM correlation against the operator's component inventory, supplier-attestation lookup, scoring policy) and supplies the result as JSON-native arguments; this step is the shape-and-discipline gate at the step boundary so a free-text signal class, an unknown verdict, or a personal-name supplier reference fails loud here rather than at the artifact-emit boundary downstream. Read-only against the operator's signal source by contract; the workflow MUST NOT mutate the source signal on this step.

    CACAO step_id : action--5c5c5c5c-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--5c5c5c5c-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--5c5c5c5c-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--5c5c5c5c-0000-4000-8000-000000000002', 'secops_ng.step.name': 'assess-supplier-signal', 'secops_ng.tool.name': 'assess_supplier_signal', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--5c5c5c5c-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--5c5c5c5c-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--5c5c5c5c-0000-4000-8000-000000000002', 'secops_ng.step.name': 'assess-supplier-signal', 'secops_ng.tool.name': 'assess_supplier_signal', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.supply_chain_security.primitives.assess import assess_supplier_signal
        __assessment_ref__ = assess_supplier_signal(signal_class=__signal_class__, verdict=__signal_verdict__, affected_supplier_handle=__signal_supplier_handle__, received_at=__signal_received_at__, affected_component_set=__signal_component_set__, signal_id=__signal_id__, scoring_notes=__signal_scoring_notes__)

@tool
async def emit_supply_chain_evidence(workflow_id: str, execution_id: str, regulation_refs: str, control_refs: str, assessment_ref: str, dependencies: str, owner_role: str, owner_assigned_at: str, captured_at: str, source_url: str, aggregates: str) -> str:
    """Combine the execution metadata, the closed assessment block, and the operator-declared dependency surface into one supply-chain-evidence artifact shaped against schemas/evidence/supply-chain.schema.json (stream: supply-chain). The primitive wires through the F-CP-03 shared emitter at compilers/_shared/evidence/supply_chain.py and pins the supply-chain-security-side join: the affected_supplier_handle on the assessment block MUST appear among the declared dependencies[] on this execution, so the artifact actually documents the implicated supplier rather than producing a silent orphan. Emission is byte-stable: same execution inputs re-derive the same artifact_id (SHA-256 of workflow_id|execution_id|captured_at). The artifact carries the NIS2 Article 21(2)(d) regulation reference so the per-execution audit-trail entry has a regulatory anchor. Destination is operator-configured — no default non-EU endpoint.

    CACAO step_id : action--5c5c5c5c-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--5c5c5c5c-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--5c5c5c5c-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--5c5c5c5c-0000-4000-8000-000000000003', 'secops_ng.step.name': 'emit-supply-chain-evidence', 'secops_ng.tool.name': 'emit_supply_chain_evidence', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--5c5c5c5c-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--5c5c5c5c-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--5c5c5c5c-0000-4000-8000-000000000003', 'secops_ng.step.name': 'emit-supply-chain-evidence', 'secops_ng.tool.name': 'emit_supply_chain_evidence', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.supply_chain_security.primitives.artifact import build_supply_chain_evidence_artifact
        __supply_chain_artifact_ref__ = build_supply_chain_evidence_artifact(workflow_id=__workflow_id__, execution_id=__execution_id__, regulation_refs=__regulation_refs__, control_refs=__control_refs__, assessment=__assessment_ref__, dependencies=__dependencies__, owner_role=__owner_role__, owner_assigned_at=__owner_assigned_at__, captured_at=__captured_at__, source_url=__source_url__, aggregates=__aggregates__)

async def llm_step(state: PlaybookSupplyChainSecurityV1State) -> dict:
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

STATE_SCHEMA = PlaybookSupplyChainSecurityV1State
TOOLS = (assess_supplier_signal, emit_supply_chain_evidence,)
AGENTIC_HOOK = llm_step

