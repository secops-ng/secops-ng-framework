# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.dora_tpr_management@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookDoraTprManagementV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.dora_tpr_management@v1.

    Playbook id: playbook--d07a7970-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __provider_handle__
    # Stable operator-side ICT third-party service provider identifier in `provider.<id>@v<n>` shape — mirrors the F-CP-03 dependencies[].provider_id vocabulary so the register row and the runtime supply-chain-evidence stream join on the same key without re-canonicalisation. Personal names and contact-shaped strings fail loud at the onboarding-risk-assessment primitive boundary per the public-bar discipline.
    provider_handle: str
    # playbook_variable: __function_supported__
    # Short operator-defined token naming the business or ICT function the third-party service provider supports (for example `payments_settlement`, `identity_provider`, `cloud_iaas`). Consumed by the onboarding risk assessment to key the criticality determination against the operator's documented critical-or-important-function register, and carried onto the Article 28 register row.
    function_supported: str
    # playbook_variable: __criticality_determination__
    # Identifier of the criticality determination the onboarding step composed for the provider on the current lifecycle window against the operator's documented pre-contractual risk-assessment rubric. Values are drawn from the operator's declared bucket set (typically {non_critical, important, critical} plus a supporting-critical bucket where the supported function itself is a critical-or-important function). Carried onto the register row and re-scored on every periodic-review invocation.
    criticality_determination: str
    # playbook_variable: __risk_assessment_ref__
    # Pointer to the closed pre-contractual risk-assessment block produced by onboarding-risk-assessment — criticality-determination keyed, sub-outsourcing-chain enumerated, data-location declared, concentration-exposure scored against the operator's documented concentration-risk rubric. Consumed by register-entry and by exit-assessment.
    risk_assessment_ref: str
    # playbook_variable: __contract_ref__
    # Operator-side pointer to the negotiated ICT third-party contract instance (contract identifier, version, effective date) contractual-provisions-check reads against for the Article 30(2)/(3) closed clause set. Free string, <= 200 chars. Pinned by the compile target's contract-repository binding.
    contract_ref: str
    # playbook_variable: __clause_check_ref__
    # Pointer to the closed clause-presence check produced by contractual-provisions-check — per-clause status (present / present_with_deviation / absent) against the Article 30(2) and 30(3) closed clause set (service description, data-processing locations, exit-strategy obligations, audit rights, termination rights, sub-contracting conditions, service-level descriptions, insolvency and resolution provisions). Consumed by register-entry.
    clause_check_ref: str
    # playbook_variable: __register_row_id__
    # Identifier of the Article 28 register-of-information row register-entry composed and published for the provider on the current lifecycle window, joined to the criticality determination, the accepted-clause set, the sub-outsourcing chain, and the data-location indicators. Populated on both the net-new-provider onboarding branch and the periodic-review re-emission branch so the register carries a per-window row for every ICT third-party service provider in scope.
    register_row_id: str
    # playbook_variable: __review_window__
    # Identifier of the periodic-review window this run discharges. For DORA, the primary anchor is the operator's documented periodic-review cadence for the criticality bucket the provider sits in (typically annual for critical, biennial for important, on-change for non-critical) plus the on-change trigger (material change to the contract, the sub-outsourcing chain, the function supported, or the supply-chain-evidence stream). Pinned by the compile target's boot config; not derived in the workflow.
    review_window: str
    # playbook_variable: __runtime_supply_chain_evidence_ref__
    # Pointer to the current supply-chain-evidence artifact set the runtime supply-chain-security workflow has emitted against this provider handle since the last periodic-review invocation. Consumed by periodic-review so drift on the runtime surface (a `watch` or `confirmed_compromise` verdict from playbook.supply_chain_security@v1 against `__provider_handle__`) re-enters the register and re-scores criticality. Empty when no supply-chain-evidence has been emitted against the provider in the window; the empty case is still carried explicitly so the review records `no_runtime_drift` rather than silently dropping the join.
    runtime_supply_chain_evidence_ref: str
    # playbook_variable: __periodic_review_ref__
    # Pointer to the closed periodic-review block produced by periodic-review — re-scored criticality, re-emitted register row identifier, runtime-drift verdict, and the operator's declared next-review-window anchor. Consumed by exit-assessment when the review triggers an exit decision.
    periodic_review_ref: str
    # playbook_variable: __exit_trigger__
    # Reason the operator invokes the exit-assessment step for the provider. One of `operator_election`, `periodic_review_failure`, `contractual_termination`, `provider_insolvency`, `regulatory_direction`. Pinned by the compile target's exit-decision path; the framework ships no default policy — exit is always an operator decision anchored on the operator's documented exit-strategy discipline.
    exit_trigger: str
    # playbook_variable: __exit_attestation_id__
    # Identifier of the dated exit-assessment attestation artifact exit-assessment publishes to the operator's evidence store, joined to the register row identifier, the risk-assessment block, the clause-check block, and the periodic-review block. Discharges the Article 28(8) exit-strategy obligation on the operator side; the destination sink is operator-configured (no default non-EU endpoint).
    exit_attestation_id: str
    # playbook_variable: __captured_at__
    # ISO-8601 UTC second-precision timestamp (`...Z`) pinned at each attestation-emission time by the upstream runtime. Part of the deterministic register-row-id and exit-attestation-id derivations alongside workflow_id and execution_id.
    captured_at: str
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
async def onboarding_risk_assessment(provider_handle: str, function_supported: str) -> dict[str, object]:
    """TODO (CORE): pre-contractual risk-assessment primitive. The action body scores a candidate ICT third-party service provider against the operator's documented pre-contractual risk-assessment rubric, keyed on the function the provider supports (`__function_supported__`) and the provider handle (`__provider_handle__`). The rubric axes DORA Article 28(4) names — function criticality (does the function this provider supports qualify as critical or important under the operator's declared critical-or-important-function register), sub-outsourcing chain (declared sub-outsourcing depth and per-node criticality carry), data-location (EU / EEA / third-country processing locations declared by the provider), and concentration exposure (the operator's current concentration on this provider on the same function axis) — are composed into the closed risk-assessment block the register row consumes. Sets `__criticality_determination__` and `__risk_assessment_ref__`. Read-only against the provider's declared shape: the assessment step does not mutate the provider's declared attestations, it composes an operator-side view keyed on the rubric axes. SKELETON pins the topology + ID + regulatory anchor refs; the deterministic rubric application, sub-outsourcing chain traversal, and concentration-risk scoring are owned by CORE-PRIM.

    CACAO step_id : action--d07a7970-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d07a7970-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d07a7970-0000-4000-8000-000000000002', 'secops_ng.step.name': 'onboarding risk assessment', 'secops_ng.tool.name': 'onboarding_risk_assessment', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d07a7970-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d07a7970-0000-4000-8000-000000000002', 'secops_ng.step.name': 'onboarding risk assessment', 'secops_ng.tool.name': 'onboarding_risk_assessment', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d07a7970-0000-4000-8000-000000000002'"
        )

@tool
async def contractual_provisions_check(provider_handle: str, contract_ref: str) -> str:
    """TODO (CORE): Article 30 clause-presence verification primitive. The action body reads the negotiated ICT third-party contract instance (`__contract_ref__`) and verifies the DORA Article 30(2) and 30(3) closed clause set is present — service description, data-processing locations, exit-strategy obligations, audit rights, termination rights, sub-contracting conditions, service-level descriptions, insolvency and resolution provisions. Each clause is scored present / present_with_deviation / absent against the operator's declared clause-shape rubric; the block carries the per-clause status plus the deviation notes for downstream register-row composition. Sets `__clause_check_ref__`. Absent-clause status is a hard signal onto the register row: the row is still composed (the register carries an entry for every ICT third-party service provider under contract, per Article 28), but the row is flagged as clause-incomplete so the operator's governance surface can drive the negotiation lever. SKELETON pins the topology + ID + regulatory anchor refs; the deterministic clause-presence check body, deviation-note capture, and per-clause-status vocabulary binding are owned by CORE-PRIM.

    CACAO step_id : action--d07a7970-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d07a7970-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d07a7970-0000-4000-8000-000000000003', 'secops_ng.step.name': 'contractual provisions check', 'secops_ng.tool.name': 'contractual_provisions_check', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d07a7970-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d07a7970-0000-4000-8000-000000000003', 'secops_ng.step.name': 'contractual provisions check', 'secops_ng.tool.name': 'contractual_provisions_check', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d07a7970-0000-4000-8000-000000000003'"
        )

@tool
async def register_entry(provider_handle: str, function_supported: str, criticality_determination: str, risk_assessment_ref: str, clause_check_ref: str, captured_at: str) -> str:
    """TODO (CORE): Article 28 register-of-information row-composition primitive. The action body composes and publishes the Article 28 register row for the provider on the current lifecycle window, joining `__provider_handle__`, `__function_supported__`, `__criticality_determination__`, `__risk_assessment_ref__`, and `__clause_check_ref__` into the register-row shape the Commission Implementing Regulation (EU) 2024/2956 ITS on standard templates for the register of information declares. The row is content-addressed against the artifact_id derivation SHA-256(workflow_id|execution_id|captured_at) so a replay of the same window re-derives byte-identical bytes (the byte-parity contract the CORE-FANOUT siblings assert against). Sets `__register_row_id__`. The primitive only produces the JSON-native register row; the durable emitter wiring (register-artifact-path, content-addressed filename, atomic write, notification of the operator's accountability owner) is owned by the per-target compilers and lands with the CORE-FANOUT sibling cards. Read-only against the risk-assessment and clause-check blocks by contract; the row composition does not mutate the upstream blocks.

    CACAO step_id : action--d07a7970-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d07a7970-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d07a7970-0000-4000-8000-000000000004', 'secops_ng.step.name': 'register entry', 'secops_ng.tool.name': 'register_entry', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d07a7970-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d07a7970-0000-4000-8000-000000000004', 'secops_ng.step.name': 'register entry', 'secops_ng.tool.name': 'register_entry', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d07a7970-0000-4000-8000-000000000004'"
        )

@tool
async def periodic_review(provider_handle: str, register_row_id: str, review_window: str, runtime_supply_chain_evidence_ref: str) -> str:
    """TODO (CORE): periodic-review-and-drift-detection primitive. The action body re-reads the published register row (`__register_row_id__`) on the operator's documented periodic-review cadence (`__review_window__`) and re-scores criticality against the current runtime supply-chain-evidence stream (`__runtime_supply_chain_evidence_ref__` — the artifact set playbook.supply_chain_security@v1 has emitted against this provider handle since the last invocation). The re-score composes three inputs: (i) the standing risk-assessment block, (ii) any material change declared on the contract, the sub-outsourcing chain, or the function supported since the last invocation, and (iii) the runtime-drift verdict derived from the supply-chain-evidence stream (an active `watch` or `confirmed_compromise` verdict against the provider re-enters the register on this join). The primitive emits a re-scored criticality determination, re-emits the register row on the current window, and pins the operator's declared next-review-window anchor for the next invocation. Sets `__periodic_review_ref__`. When a re-scored criticality bucket crosses a documented exit-decision threshold, the operator's governance surface consumes the review block to invoke exit-assessment; the review primitive itself does not auto-invoke exit — exit is always an operator decision. SKELETON pins the topology + ID + regulatory anchor refs; the deterministic re-scoring, runtime-drift join, and next-window anchor derivation are owned by CORE-PRIM.

    CACAO step_id : action--d07a7970-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d07a7970-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d07a7970-0000-4000-8000-000000000005', 'secops_ng.step.name': 'periodic review', 'secops_ng.tool.name': 'periodic_review', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d07a7970-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d07a7970-0000-4000-8000-000000000005', 'secops_ng.step.name': 'periodic review', 'secops_ng.tool.name': 'periodic_review', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d07a7970-0000-4000-8000-000000000005'"
        )

@tool
async def exit_assessment(provider_handle: str, register_row_id: str, risk_assessment_ref: str, clause_check_ref: str, periodic_review_ref: str, exit_trigger: str, captured_at: str) -> str:
    """TODO (CORE): Article 28(8) exit-strategy attestation-emission primitive. The action body composes and publishes the dated exit-assessment attestation for the provider when the operator invokes the step against a documented exit trigger (`__exit_trigger__`) — operator election, periodic-review failure, contractual termination, provider insolvency, or regulatory direction. The attestation joins the register row identifier, the standing risk-assessment block, the clause-check block, and the periodic-review block so the audit-evident chain from onboarding to exit is closed in one artifact. The artifact_id is derived SHA-256(workflow_id|execution_id|captured_at) so the byte-parity contract carries onto the exit surface. Sets `__exit_attestation_id__`. The primitive only produces the JSON-native attestation record; the durable emitter wiring is owned by the per-target compilers. The record discharges the Article 28(8) exit-strategy discipline the operator carries against every critical-or-important-function ICT third-party service provider; the destination sink is operator-configured (no default non-EU endpoint per the public-bar discipline).

    CACAO step_id : action--d07a7970-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d07a7970-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d07a7970-0000-4000-8000-000000000006', 'secops_ng.step.name': 'exit assessment', 'secops_ng.tool.name': 'exit_assessment', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d07a7970-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--d07a7970-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d07a7970-0000-4000-8000-000000000006', 'secops_ng.step.name': 'exit assessment', 'secops_ng.tool.name': 'exit_assessment', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d07a7970-0000-4000-8000-000000000006'"
        )

async def llm_step(state: PlaybookDoraTprManagementV1State) -> dict:
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

STATE_SCHEMA = PlaybookDoraTprManagementV1State
TOOLS = (onboarding_risk_assessment, contractual_provisions_check, register_entry, periodic_review, exit_assessment,)
AGENTIC_HOOK = llm_step

