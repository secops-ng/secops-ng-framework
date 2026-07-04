# AUTO-GENERATED — do not edit by hand.
# Source: SecOps-NG CACAO v2 playbook (see x_secops_ng.stable_id below).
# Regenerate via `python -m compilers.langgraph.state <playbook.cacao.json>`.
#
# This file is a stub. State reducers and tool bodies are intentionally
# raise NotImplementedError until a human integrator wires them to the
# operator's runtime.
"""Generated LangGraph state + tool bindings for playbook.data_protection_impact_assessment@v1."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

from opentelemetry import trace

_TRACER = trace.get_tracer(__name__)

from ._audit_mirror import AuditRecord, AuditTrail

class PlaybookDataProtectionImpactAssessmentV1State(TypedDict, total=False):
    """LangGraph state for CACAO playbook playbook.data_protection_impact_assessment@v1.

    Playbook id: playbook--d91a35c0-0000-4000-8000-000000000001

    Field origins:
      - playbook_variable: declared in playbook_variables
      - step_variable:     declared on a single workflow step
      - bookkeeping:       added by the compiler for graph control
    """
    # playbook_variable: __article_36_pre_consultation_flag__
    # Whether the assessment concludes that the residual risk, absent measures taken to mitigate it, would result in a high risk under Article 36(1) and therefore triggers prior consultation with the supervisory authority before the processing may begin. Set by determine_article_36_gate against the risk-and- mitigations pair.
    article_36_pre_consultation_flag: bool
    # playbook_variable: __dpia_case_id__
    # DPIA case identifier assigned at screen_dpia_triggers. Correlation key across screening, description gathering, necessity assessment, risk assessment, mitigation documentation, DPO consultation, Article 36 gating, document production, and review scheduling so a reviewer can join the full assessment lifecycle into a single accountability-ledger record.
    dpia_case_id: str
    # playbook_variable: __dpia_document_ref__
    # Reference to the durable DPIA document artifact produced by produce_dpia_document. Records the assembled Article 35(7)(a)-(d) content, the DPO advice under Article 35(2), the Article 36 gate outcome, and the review-cadence schedule; the artifact is the operator's accountability record under Article 5(2) and the primary response to any subsequent Article 58(1)(a) supervisory- authority information order.
    dpia_document_ref: str
    # playbook_variable: __dpia_required__
    # Whether the screening step concludes that a DPIA is required for __processing_ref__. Set by screen_dpia_triggers against the Article 35(3)(a-c) mandatory-DPIA triggers, the operator's supervisory- authority Article 35(4) blacklist, and the general Article 35(1) high-risk test. A false outcome short- circuits the workflow with a documented screening result; the operator retains the negative screening as part of the Article 5(2) accountability record.
    dpia_required: bool
    # playbook_variable: __dpo_consultation_ref__
    # Reference to the DPO consultation record produced by dpo_consultation per Article 35(2). Where the controller has designated a Data Protection Officer, that officer's advice on the assessment is recorded on the case; where no DPO has been designated (Article 37 does not require it), the record documents that fact instead.
    dpo_consultation_ref: str
    # playbook_variable: __mitigations_ref__
    # Reference to the measures envisaged to address the risks documented by identify_and_document_mitigations per Article 35(7)(d): safeguards, security measures, and mechanisms to ensure the protection of personal data and demonstrate compliance with the Regulation, taking into account the rights and legitimate interests of data subjects and other persons concerned.
    mitigations_ref: str
    # playbook_variable: __processing_description_ref__
    # Reference to the systematic description of the envisaged processing operations and their purposes assembled by gather_processing_description per Article 35(7)(a): purposes, categories of personal data and data subjects, recipients, envisaged retention, and where applicable the legitimate interest pursued by the controller.
    processing_description_ref: str
    # playbook_variable: __processing_ref__
    # Reference to the processing operation under assessment, resolved against the operator's processing-inventory surface (the Article 30 record of processing activities is the canonical join key). Read by every downstream step to scope the assessment to a single processing envelope.
    processing_ref: str
    # playbook_variable: __review_cadence__
    # ISO 8601 duration recording the scheduled DPIA review cadence set by schedule_review_cadence per Article 35(11). At minimum, the review is triggered on any material change to the processing envelope; the cadence duration records the maximum interval between reviews absent such a change.
    review_cadence: str
    # playbook_variable: __risk_assessment_ref__
    # Reference to the assessment of the risks to the rights and freedoms of data subjects produced by identify_and_assess_risks per Article 35(7)(c). Records the risk taxonomy applied, the per-risk likelihood-and- severity determination, and the residual-risk profile that feeds determine_article_36_gate.
    risk_assessment_ref: str
    # playbook_variable: __screening_result_ref__
    # Reference to the screening-decision artifact produced by screen_dpia_triggers. Records the trigger set evaluated, the outcome, and the reasoning; retained on the accountability ledger whether or not a full DPIA is subsequently produced.
    screening_result_ref: str
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
async def screen_dpia_triggers(processing_ref: str) -> dict[str, object]:
    """SKELETON — screen __processing_ref__ against the Article 35(3)(a-c) mandatory-DPIA triggers (systematic and extensive evaluation of personal aspects based on automated processing; large-scale processing of special categories of data or personal data relating to criminal convictions and offences; systematic monitoring of a publicly accessible area on a large scale), against the operator's supervisory-authority Article 35(4) list of processing kinds that require a DPIA in the operator's jurisdiction, and against the general Article 35(1) likely-to-result-in-a-high-risk test taking into account the nature, scope, context and purposes of the processing. Assigns __dpia_case_id__, sets __dpia_required__, and records __screening_result_ref__ on the accountability ledger. A false outcome short- circuits the lifecycle with the negative screening retained as part of the operator's Article 5(2) accountability record. TODO (CORE): pin the operator's supervisory-authority Article 35(4) list adapter and the novel-technology signal (WP248 rev.01 criteria).

    CACAO step_id : action--d91a35c0-0000-4000-8000-000000000002
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d91a35c0-0000-4000-8000-000000000002',
        attributes={'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000002', 'secops_ng.step.name': 'screen_dpia_triggers', 'secops_ng.tool.name': 'screen_dpia_triggers', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d91a35c0-0000-4000-8000-000000000002', attributes={'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000002', 'secops_ng.step.name': 'screen_dpia_triggers', 'secops_ng.tool.name': 'screen_dpia_triggers', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d91a35c0-0000-4000-8000-000000000002'"
        )

@tool
async def classify_processing_type(dpia_case_id: str, processing_ref: str) -> None:
    """SKELETON — classify the processing envelope against the operator's processing-inventory surface (the Article 30 record of processing activities as canonical join key) so downstream steps read a common shape: personal-data categories, special-category involvement, subject categories (including vulnerable-subject axes such as children, employees, patients), controller-vs-processor role, and the lawful-basis attribution the processing relies on under Article 6 (and where applicable Article 9(2)). Anchors the assessment scope; does not itself perform the risk determination. TODO (CORE): pin the RoPA-inventory adapter and the vulnerable-subject axis catalogue.

    CACAO step_id : action--d91a35c0-0000-4000-8000-000000000003
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d91a35c0-0000-4000-8000-000000000003',
        attributes={'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify_processing_type', 'secops_ng.tool.name': 'classify_processing_type', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d91a35c0-0000-4000-8000-000000000003', attributes={'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify_processing_type', 'secops_ng.tool.name': 'classify_processing_type', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d91a35c0-0000-4000-8000-000000000003'"
        )

@tool
async def gather_processing_description(dpia_case_id: str, processing_ref: str) -> str:
    """SKELETON — assemble the systematic description of the envisaged processing operations and their purposes per Article 35(7)(a): purposes of the processing, categories of personal data and of data subjects, recipients or categories of recipients (including any transfers to third countries or international organisations), envisaged retention periods or the criteria used to determine them, and where applicable the legitimate interests pursued by the controller. Records __processing_description_ref__ so downstream steps read a stable description surface. TODO (CORE): pin the RoPA-extraction adapter and the transfer-legs cross-reference.

    CACAO step_id : action--d91a35c0-0000-4000-8000-000000000004
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d91a35c0-0000-4000-8000-000000000004',
        attributes={'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000004', 'secops_ng.step.name': 'gather_processing_description', 'secops_ng.tool.name': 'gather_processing_description', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d91a35c0-0000-4000-8000-000000000004', attributes={'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000004', 'secops_ng.step.name': 'gather_processing_description', 'secops_ng.tool.name': 'gather_processing_description', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d91a35c0-0000-4000-8000-000000000004'"
        )

@tool
async def assess_necessity_and_proportionality(dpia_case_id: str, processing_description_ref: str) -> None:
    """SKELETON — assess the necessity and proportionality of the processing operations in relation to the purposes per Article 35(7)(b). Necessity: whether the processing is required to achieve the purpose or whether a less- intrusive alternative would suffice. Proportionality: whether the categories of data and the scope of the processing are commensurate with the purpose and not excessive. Records the reasoning on the case; the outcome feeds the risk assessment and the mitigations identification downstream. TODO (CORE): pin the necessity-and-proportionality assessment template.

    CACAO step_id : action--d91a35c0-0000-4000-8000-000000000005
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d91a35c0-0000-4000-8000-000000000005',
        attributes={'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000005', 'secops_ng.step.name': 'assess_necessity_and_proportionality', 'secops_ng.tool.name': 'assess_necessity_and_proportionality', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d91a35c0-0000-4000-8000-000000000005', attributes={'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000005', 'secops_ng.step.name': 'assess_necessity_and_proportionality', 'secops_ng.tool.name': 'assess_necessity_and_proportionality', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d91a35c0-0000-4000-8000-000000000005'"
        )

@tool
async def identify_and_assess_risks(dpia_case_id: str, processing_description_ref: str) -> str:
    """SKELETON — identify and assess the risks to the rights and freedoms of natural persons the processing generates per Article 35(7)(c). Applies the operator's declared risk taxonomy over the risk-source, risk- event, and impact axes (illegitimate access, unauthorised modification, disappearance of personal data — the three EDPB reference risk categories — plus operator-declared context-specific axes). Records per-risk likelihood and severity and the residual-risk profile that determine_article_36_gate reads downstream. Records __risk_assessment_ref__. TODO (CORE): pin the risk-taxonomy binding and the residual- risk calibration surface.

    CACAO step_id : action--d91a35c0-0000-4000-8000-000000000006
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d91a35c0-0000-4000-8000-000000000006',
        attributes={'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000006', 'secops_ng.step.name': 'identify_and_assess_risks', 'secops_ng.tool.name': 'identify_and_assess_risks', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d91a35c0-0000-4000-8000-000000000006', attributes={'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000006', 'secops_ng.step.name': 'identify_and_assess_risks', 'secops_ng.tool.name': 'identify_and_assess_risks', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d91a35c0-0000-4000-8000-000000000006'"
        )

@tool
async def identify_and_document_mitigations(dpia_case_id: str, risk_assessment_ref: str) -> str:
    """SKELETON — identify and document the measures envisaged to address the risks per Article 35(7)(d): safeguards, security measures, and mechanisms to ensure the protection of personal data and demonstrate compliance with the Regulation, taking into account the rights and legitimate interests of data subjects and other persons concerned. Records __mitigations_ref__ and pins the per-risk mitigation attribution so determine_article_36_gate can read the residual risk after mitigation. TODO (CORE): pin the safeguards catalogue and the security-measure control-reference binding.

    CACAO step_id : action--d91a35c0-0000-4000-8000-000000000007
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d91a35c0-0000-4000-8000-000000000007',
        attributes={'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000007', 'secops_ng.step.name': 'identify_and_document_mitigations', 'secops_ng.tool.name': 'identify_and_document_mitigations', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d91a35c0-0000-4000-8000-000000000007', attributes={'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000007', 'secops_ng.step.name': 'identify_and_document_mitigations', 'secops_ng.tool.name': 'identify_and_document_mitigations', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d91a35c0-0000-4000-8000-000000000007'"
        )

@tool
async def dpo_consultation(dpia_case_id: str, processing_description_ref: str, risk_assessment_ref: str, mitigations_ref: str) -> str:
    """SKELETON — seek the advice of the Data Protection Officer where the controller has designated one, per Article 35(2). The DPO reviews the assembled description, necessity-and-proportionality assessment, risk assessment, and mitigations documentation and records advice on the DPIA case. Where the controller has not designated a DPO because Article 37 does not require it, the record documents that fact and the alternative accountability surface the controller relies on. Records __dpo_consultation_ref__. TODO (CORE): pin the DPO-consultation intake adapter and the alternative-accountability-surface record where no DPO is designated.

    CACAO step_id : action--d91a35c0-0000-4000-8000-000000000008
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d91a35c0-0000-4000-8000-000000000008',
        attributes={'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000008', 'secops_ng.step.name': 'dpo_consultation', 'secops_ng.tool.name': 'dpo_consultation', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d91a35c0-0000-4000-8000-000000000008', attributes={'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000008', 'secops_ng.step.name': 'dpo_consultation', 'secops_ng.tool.name': 'dpo_consultation', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d91a35c0-0000-4000-8000-000000000008'"
        )

@tool
async def determine_article_36_gate(dpia_case_id: str, risk_assessment_ref: str, mitigations_ref: str) -> bool:
    """SKELETON — determine whether the residual risk, absent measures taken by the controller to mitigate it, would result in a high risk under Article 36(1) and therefore triggers prior consultation with the supervisory authority before the processing may begin. Reads the risk assessment against the applied mitigations and sets __article_36_pre_consultation_flag__. Where the flag is true, the controller must consult the supervisory authority under Article 36(1) and the processing may not begin until the consultation window completes (Article 36(2): up to eight weeks, extendable by six weeks taking into account the complexity of the intended processing). TODO (CORE): pin the supervisory- authority pre-consultation submission chain and the Article 36(2) consultation-window gate.

    CACAO step_id : action--d91a35c0-0000-4000-8000-000000000009
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d91a35c0-0000-4000-8000-000000000009',
        attributes={'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000009', 'secops_ng.step.name': 'determine_article_36_gate', 'secops_ng.tool.name': 'determine_article_36_gate', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d91a35c0-0000-4000-8000-000000000009', attributes={'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000009', 'secops_ng.step.name': 'determine_article_36_gate', 'secops_ng.tool.name': 'determine_article_36_gate', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d91a35c0-0000-4000-8000-000000000009'"
        )

@tool
async def produce_dpia_document(dpia_case_id: str, processing_description_ref: str, risk_assessment_ref: str, mitigations_ref: str, dpo_consultation_ref: str, article_36_pre_consultation_flag: bool) -> str:
    """SKELETON — produce the durable DPIA document artifact for the case. Assembles the Article 35(7)(a)-(d) content (systematic description, necessity-and- proportionality, risk assessment, mitigations), the Article 35(2) DPO advice, the Article 36 gate outcome, and the review-cadence schedule into the operator's declared DPIA-document template. Records __dpia_document_ref__ on the accountability ledger. The document is the primary response to any subsequent Article 58(1)(a) supervisory-authority information order and the operator's Article 5(2) accountability artifact for this processing envelope. TODO (CORE): pin the DPIA-document template and the evidence-store binding.

    CACAO step_id : action--d91a35c0-0000-4000-8000-00000000000a
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d91a35c0-0000-4000-8000-00000000000a',
        attributes={'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-00000000000a', 'secops_ng.step.name': 'produce_dpia_document', 'secops_ng.tool.name': 'produce_dpia_document', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d91a35c0-0000-4000-8000-00000000000a', attributes={'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-00000000000a', 'secops_ng.step.name': 'produce_dpia_document', 'secops_ng.tool.name': 'produce_dpia_document', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d91a35c0-0000-4000-8000-00000000000a'"
        )

@tool
async def schedule_review_cadence(dpia_case_id: str, dpia_document_ref: str) -> str:
    """SKELETON — schedule the DPIA review cadence per Article 35(11). At minimum, the review is triggered on any material change to the risk represented by the processing envelope (change in categories of data, subjects, recipients, retention, purpose, or underlying-technology substrate). Records __review_cadence__ as the maximum interval between reviews absent such a change, and pins the review trigger to the operator's change-management surface. TODO (CORE): pin the change-management adapter and the review-trigger evidence-emission binding.

    CACAO step_id : action--d91a35c0-0000-4000-8000-00000000000b
    CACAO type    : action
    """
    with _TRACER.start_as_current_span(
        name='tool.action--d91a35c0-0000-4000-8000-00000000000b',
        attributes={'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'schedule_review_cadence', 'secops_ng.tool.name': 'schedule_review_cadence', 'secops_ng.workflow.run_id': ''},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='tool.action--d91a35c0-0000-4000-8000-00000000000b', attributes={'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'schedule_review_cadence', 'secops_ng.tool.name': 'schedule_review_cadence', 'secops_ng.workflow.run_id': ''})
        )
        raise NotImplementedError(
            f"CACAO action tool not implemented: step_id='action--d91a35c0-0000-4000-8000-00000000000b'"
        )

async def llm_step(state: PlaybookDataProtectionImpactAssessmentV1State) -> dict:
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

STATE_SCHEMA = PlaybookDataProtectionImpactAssessmentV1State
TOOLS = (screen_dpia_triggers, classify_processing_type, gather_processing_description, assess_necessity_and_proportionality, identify_and_assess_risks, identify_and_document_mitigations, dpo_consultation, determine_article_36_gate, produce_dpia_document, schedule_review_cadence,)
AGENTIC_HOOK = llm_step

