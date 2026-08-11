# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.eu_ai_act_risk_management@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookEuAiActRiskManagementV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.eu_ai_act_risk_management@v1.

    Playbook id: playbook--40a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __ai_system_id__
    # Identifier of the AI system under assessment. Resolved against the operator's AI-system inventory.
    ai_system_id: str
    # playbook_variable: __annex_iii_use_case__
    # Annex III high-risk use-case category the system falls under (e.g. biometric identification, critical infrastructure management, employment screening). SKELETON: string; CORE tightens to an enum against the Annex III eight-area catalogue.
    annex_iii_use_case: dict[str, object]
    # playbook_variable: __risk_register_id__
    # Identifier of the risk register emitted by the Art. 9(2)(a)-(b) identification / estimation step and consumed by the Art. 9(2)(d) risk-treatment step.
    risk_register_id: dict[str, object]
    # playbook_variable: __technical_documentation_id__
    # Identifier of the technical documentation bundle assembled per Art. 11 read with Annex IV. Consumed by conformity assessment.
    technical_documentation_id: dict[str, object]
    # playbook_variable: __post_market_signal__
    # Identifier of the post-market monitoring signal fed back into the iterative risk-management cycle under Art. 9(2)(c) read with Art. 72.
    post_market_signal: dict[str, object]
    # playbook_variable: __classification_basis__
    # Which Article 6 path applies: annex_i_product_safety (6(1)), annex_iii_standalone (6(2)) or annex_iii_derogated (6(3)). Asserted by the provider — never inferred from the intended purpose.
    classification_basis: str
    # playbook_variable: __annex_iii_area__
    # One of the eight Annex III areas, matching the eu_ai_act:annex-iii-N-<area> mapping ids. Required on both Annex III paths, forbidden on the Art. 6(1) product-safety path.
    annex_iii_area: str
    # playbook_variable: __union_harmonisation_ref__
    # Reference to the Annex I Union harmonisation legislation entry. Required on the Art. 6(1) path only.
    union_harmonisation_ref: str
    # playbook_variable: __derogation_ground__
    # One of the four Art. 6(3) grounds. Required on the derogated path only.
    derogation_ground: str
    # playbook_variable: __derogation_assessment_ref__
    # Reference to the Art. 6(4) documented assessment supporting an Art. 6(3) derogation. Required on the derogated path only — a derogation with no assessment behind it is not representable.
    derogation_assessment_ref: str
    # playbook_variable: __iteration_id__
    # Identifier of this Art. 9(2) iteration. Art. 9(2) is a continuous iterative process, so every register is scoped to an iteration.
    iteration_id: str
    # playbook_variable: __identified_risks__
    # Risk records for this iteration, each carrying risk_id, origin_paragraph (9(2)(a)/(b)/(c)), residual_score and measure_refs. References into the provider's risk documentation, never hazard prose.
    identified_risks: dict[str, object]
    # playbook_variable: __acceptability_thresholds__
    # Annex III area to Art. 9(5) residual-risk acceptability threshold. The framework ships no default: acceptability is the operator's own policy.
    acceptability_thresholds: dict[str, object]
    # playbook_variable: __annex_iv_sections__
    # Annex IV section key to a reference into the provider's documentation store. Annex IV(5) must reference this iteration's register.
    annex_iv_sections: dict[str, object]
    # playbook_variable: __technical_doc_committed_at__
    # ISO-8601 date the Art. 11 / Annex IV bundle was last committed. Supplied rather than clock-read, which is what makes a run replayable.
    technical_doc_committed_at: str
    # playbook_variable: __instructions_committed_at__
    # ISO-8601 date the Art. 13 instructions for use were last committed. Tracked separately because kri.transparency_doc_freshness_age@v1 takes the maximum of the two ages.
    instructions_committed_at: str
    # playbook_variable: __post_market_observation__
    # One Art. 72 observation: signal_id, signal_kind, observed_at, evidence_ref and optional affects_risk_ids.
    post_market_observation: dict[str, object]
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
async def identify_high_risk_ai_system(ai_system_id: str, annex_iii_area: str, classification_basis: str, derogation_assessment_ref: str, derogation_ground: str, union_harmonisation_ref: str) -> dict[str, object]:
    """Inventory the AI system, resolve whether it is a high-risk AI system under Art. 6 read with Annex III (or against a Union harmonisation-legislation entry per Art. 6(1) and Annex I), and pin the Annex III use-case category the risk-management system will be operated against. SKELETON: stub action; CORE wires the Annex III inventory join, the provider / deployer role determination under Art. 3(3) and (4), and the Art. 6(3) derogation self-declaration.

    CACAO step_id : action--40000000-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--40000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--40a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'identify high-risk AI system', 'secops_ng.tool.name': 'identify_high_risk_ai_system', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--40000000-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--40a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'identify high-risk AI system', 'secops_ng.tool.name': 'identify_high_risk_ai_system', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.eu_ai_act_risk_management.primitives.classification import classify_high_risk_system
        __annex_iii_use_case__ = classify_high_risk_system(ai_system_id=__ai_system_id__, classification_basis=__classification_basis__, annex_iii_area=__annex_iii_area__, union_harmonisation_ref=__union_harmonisation_ref__, derogation_ground=__derogation_ground__, derogation_assessment_ref=__derogation_assessment_ref__)

@tool
async def assess_risk_under_art_9_2(acceptability_thresholds: dict[str, object], annex_iii_use_case: dict[str, object], identified_risks: dict[str, object], iteration_id: str) -> dict[str, object]:
    """Iterate the Art. 9(2) risk-management cycle for the pinned use case: identification and analysis of known and reasonably foreseeable risks under Art. 9(2)(a); estimation and evaluation of risks that may emerge when the system is used in accordance with its intended purpose and under conditions of reasonably foreseeable misuse under Art. 9(2)(b); evaluation of other risks possibly arising, based on the analysis of data gathered from the post-market monitoring system, under Art. 9(2)(c); adoption of appropriate and targeted risk-management measures under Art. 9(2)(d), giving effect to the requirements of Chapter III Section 2. SKELETON: stub action; CORE wires the risk-analysis evidence artifact and the metric hooks measuring residual-risk acceptability under Art. 9(5).

    CACAO step_id : action--40000000-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--40000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--40a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'assess risk under Art. 9(2)', 'secops_ng.tool.name': 'assess_risk_under_art_9_2', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--40000000-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--40a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'assess risk under Art. 9(2)', 'secops_ng.tool.name': 'assess_risk_under_art_9_2', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.eu_ai_act_risk_management.primitives.assessment import assess_art9_risks
        __risk_register_id__ = assess_art9_risks(classification=__annex_iii_use_case__, iteration_id=__iteration_id__, identified_risks=__identified_risks__, acceptability_thresholds=__acceptability_thresholds__)

@tool
async def assemble_technical_documentation(annex_iv_sections: dict[str, object], instructions_committed_at: str, risk_register_id: dict[str, object], technical_doc_committed_at: str) -> dict[str, object]:
    """Assemble the technical documentation the provider draws up before the high-risk AI system is placed on the market or put into service and keeps up to date under Art. 11 read with Annex IV: general description of the AI system, detailed description of its elements and of the process for its development, information about the monitoring, functioning and control of the AI system, description of the appropriateness of the performance metrics, detailed description of the risk-management system per Art. 9, and a list of the harmonised standards applied. SKELETON: stub action; CORE wires the Annex IV section-by-section bundle assembly and the conformity-assessment intake handoff under Art. 43.

    CACAO step_id : action--40000000-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--40000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--40a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'assemble technical documentation', 'secops_ng.tool.name': 'assemble_technical_documentation', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--40000000-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--40a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'assemble technical documentation', 'secops_ng.tool.name': 'assemble_technical_documentation', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.eu_ai_act_risk_management.primitives.documentation import assemble_technical_documentation
        __technical_documentation_id__ = assemble_technical_documentation(risk_register=__risk_register_id__, annex_iv_sections=__annex_iv_sections__, technical_doc_committed_at=__technical_doc_committed_at__, instructions_committed_at=__instructions_committed_at__)

@tool
async def monitor_post_market_signals(post_market_observation: dict[str, object], risk_register_id: dict[str, object]) -> dict[str, object]:
    """Operate the post-market monitoring feedback loop the iterative Art. 9(2)(c) cycle depends on: the provider establishes and documents a post-market monitoring system under Art. 72, actively and systematically collects, documents and analyses relevant data on the performance of the high-risk AI system throughout its lifetime, and feeds the resulting signals back into the Art. 9 iteration so residual-risk acceptability under Art. 9(5) stays defended. SKELETON: stub action; CORE wires the Art. 72 post-market monitoring plan template and the loop-back edge into the Art. 9(2)(c) step of the next iteration.

    CACAO step_id : action--40000000-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--40000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--40a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'monitor post-market signals', 'secops_ng.tool.name': 'monitor_post_market_signals', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--40000000-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--40a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'monitor post-market signals', 'secops_ng.tool.name': 'monitor_post_market_signals', 'secops_ng.workflow.run_id': ''})
        )
        from content.playbooks.eu_ai_act_risk_management.primitives.post_market import record_post_market_signal
        __post_market_signal__ = record_post_market_signal(risk_register=__risk_register_id__, observation=__post_market_observation__)

async def llm_step(state: PlaybookEuAiActRiskManagementV1State) -> dict:
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

STATE_SCHEMA = PlaybookEuAiActRiskManagementV1State
TOOLS = (identify_high_risk_ai_system, assess_risk_under_art_9_2, assemble_technical_documentation, monitor_post_market_signals,)
AGENTIC_HOOK = llm_step

