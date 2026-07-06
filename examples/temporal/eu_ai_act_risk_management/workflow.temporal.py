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
async def identify_high_risk_ai_system(ai_system_id: str) -> str:
    """Inventory the AI system, resolve whether it is a high-risk AI system under Art. 6 read with Annex III (or against a Union harmonisation-legislation entry per Art. 6(1) and Annex I), and pin the Annex III use-case category the risk-management system will be operated against. SKELETON: stub action; CORE wires the Annex III inventory join, the provider / deployer role determination under Art. 3(3) and (4), and the Art. 6(3) derogation self-declaration.

    CACAO step_id: action--40000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--40000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--40a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'identify high-risk AI system', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'identify_high_risk_ai_system'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--40000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--40a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'identify high-risk AI system', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'identify_high_risk_ai_system'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--40000000-0000-4000-8000-000000000002'"
        )

IDENTIFY_HIGH_RISK_AI_SYSTEM_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def assess_risk_under_art_9_2(annex_iii_use_case: str) -> str:
    """Iterate the Art. 9(2) risk-management cycle for the pinned use case: identification and analysis of known and reasonably foreseeable risks under Art. 9(2)(a); estimation and evaluation of risks that may emerge when the system is used in accordance with its intended purpose and under conditions of reasonably foreseeable misuse under Art. 9(2)(b); evaluation of other risks possibly arising, based on the analysis of data gathered from the post-market monitoring system, under Art. 9(2)(c); adoption of appropriate and targeted risk-management measures under Art. 9(2)(d), giving effect to the requirements of Chapter III Section 2. SKELETON: stub action; CORE wires the risk-analysis evidence artifact and the metric hooks measuring residual-risk acceptability under Art. 9(5).

    CACAO step_id: action--40000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--40000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--40a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'assess risk under Art. 9(2)', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assess_risk_under_art_9_2'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--40000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--40a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'assess risk under Art. 9(2)', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assess_risk_under_art_9_2'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--40000000-0000-4000-8000-000000000003'"
        )

ASSESS_RISK_UNDER_ART_9_2_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def assemble_technical_documentation(risk_register_id: str) -> str:
    """Assemble the technical documentation the provider draws up before the high-risk AI system is placed on the market or put into service and keeps up to date under Art. 11 read with Annex IV: general description of the AI system, detailed description of its elements and of the process for its development, information about the monitoring, functioning and control of the AI system, description of the appropriateness of the performance metrics, detailed description of the risk-management system per Art. 9, and a list of the harmonised standards applied. SKELETON: stub action; CORE wires the Annex IV section-by-section bundle assembly and the conformity-assessment intake handoff under Art. 43.

    CACAO step_id: action--40000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--40000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--40a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'assemble technical documentation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assemble_technical_documentation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--40000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--40a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'assemble technical documentation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assemble_technical_documentation'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--40000000-0000-4000-8000-000000000004'"
        )

ASSEMBLE_TECHNICAL_DOCUMENTATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def monitor_post_market_signals() -> str:
    """Operate the post-market monitoring feedback loop the iterative Art. 9(2)(c) cycle depends on: the provider establishes and documents a post-market monitoring system under Art. 72, actively and systematically collects, documents and analyses relevant data on the performance of the high-risk AI system throughout its lifetime, and feeds the resulting signals back into the Art. 9 iteration so residual-risk acceptability under Art. 9(5) stays defended. SKELETON: stub action; CORE wires the Art. 72 post-market monitoring plan template and the loop-back edge into the Art. 9(2)(c) step of the next iteration.

    CACAO step_id: action--40000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--40000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--40a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'monitor post-market signals', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'monitor_post_market_signals'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--40000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--40a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--40000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'monitor post-market signals', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'monitor_post_market_signals'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--40000000-0000-4000-8000-000000000005'"
        )

MONITOR_POST_MARKET_SIGNALS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookEuAiActRiskManagementV1Workflow:
    """CACAO v2 scaffold for the risk-management system Article 9 of the EU AI Act (Regulation (EU) 2024/1689) requires providers of high-risk AI systems to establish, implement, document and maintain. The playbook inventories a high-risk AI system against Annex III, iterates the Art. 9(2) identify / analyse / evaluate cycle, generates the technical documentation Art. 11 and Annex IV pin, and closes the loop with the post-market monitoring feedback Art. 9(2)(c) reads together with Art. 72. CORE tier: real OSCAL pins (RA-3, PM-9, PL-2), D3FEND anchor (D3-OAM on the risk-assessment step), and reference compile targets emitted under examples/{n8n,temporal,langgraph}/eu_ai_act_risk_management/. Portable content; runtime is the operator's choice — n8n, Temporal, or LangGraph.

    CACAO playbook id : playbook--40a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8
    stable_id         : playbook.eu_ai_act_risk_management@v1
    content_version   : 0.2.0
    maturity          : experimental
    workflow_start    : start--40000000-0000-4000-8000-000000000001
    activities        : identify_high_risk_ai_system, assess_risk_under_art_9_2, assemble_technical_documentation, monitor_post_market_signals
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.eu_ai_act_risk_management@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--40a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.2.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.eu_ai_act_risk_management@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--40a1b2c3-d4e5-4f60-8a1b-c2d3e4f5a6b8', 'secops_ng.playbook.version': '0.2.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.eu_ai_act_risk_management@v1'"
            )

WORKFLOW = PlaybookEuAiActRiskManagementV1Workflow
ACTIVITIES = (identify_high_risk_ai_system, assess_risk_under_art_9_2, assemble_technical_documentation, monitor_post_market_signals,)
RETRY_POLICIES = (IDENTIFY_HIGH_RISK_AI_SYSTEM_RETRY_POLICY, ASSESS_RISK_UNDER_ART_9_2_RETRY_POLICY, ASSEMBLE_TECHNICAL_DOCUMENTATION_RETRY_POLICY, MONITOR_POST_MARKET_SIGNALS_RETRY_POLICY,)
