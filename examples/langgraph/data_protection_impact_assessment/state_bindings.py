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
    # playbook_variable: __article_36_determination__
    # Envelope determine_article_36_gate emits: the flag, its basis, the residual high risks and, once submitted, the Article 36(2) windows. __article_36_pre_consultation_flag__ is extracted from it.
    article_36_determination: dict[str, object]
    # playbook_variable: __article_36_pre_consultation_flag__
    # Whether the controller must consult the supervisory authority before the processing begins, extracted from __article_36_determination__ as a real boolean: set when the residual risk is still high (WP248 rev.01 III.E) or Member State law requires it (Article 36(5)).
    article_36_pre_consultation_flag: bool
    # playbook_variable: __article_36_submission__
    # Unset until the controller has consulted; then the supervisory authority's receipt of the request and whether it extended the Article 36(2) period.
    article_36_submission: dict[str, object]
    # playbook_variable: __change_management_ref__
    # The change-management surface the review triggers are pinned to.
    change_management_ref: str
    # playbook_variable: __classification__
    # Envelope classify_processing_type emits: the common shape later steps read, with lawfulness gaps recorded under Articles 6, 9(2) and 10.
    classification: dict[str, object]
    # playbook_variable: __classified_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) of the classification.
    classified_at: str
    # playbook_variable: __consultation_record__
    # The consultation facts: whether a DPO is designated, the DPO and the advice, whether it was followed and the reasons for any departure, the alternative accountability surface where no DPO is designated, and the Article 35(9) data-subject views.
    consultation_record: dict[str, object]
    # playbook_variable: __consulted_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) of the consultation record.
    consulted_at: str
    # playbook_variable: __described_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) of the description.
    described_at: str
    # playbook_variable: __description_record__
    # The Article 35(7)(a) description the operator supplies: purposes, the legitimate interest where relied on, the nature-scope-context and functional description references, recipients and any third-country transfers with their Chapter V mechanism, retention per data category, assets, and approved codes of conduct (Article 35(8)).
    description_record: dict[str, object]
    # playbook_variable: __determined_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) of the Article 36 determination.
    determined_at: str
    # playbook_variable: __document_produced_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) the DPIA document is produced at.
    document_produced_at: str
    # playbook_variable: __dpia_case_id__
    # DPIA case identifier, extracted from __screening__. Correlation key across every step record of the case, so a reviewer can join the lifecycle into one accountability-ledger record.
    dpia_case_id: str
    # playbook_variable: __dpia_document__
    # Envelope produce_dpia_document emits: the joined case, the open items, whether it is final and the conclusion. __dpia_document_ref__ is extracted from it.
    dpia_document: dict[str, object]
    # playbook_variable: __dpia_document_ref__
    # Reference to the DPIA document, the Article 5(2) accountability artifact, extracted from __dpia_document__.
    dpia_document_ref: str
    # playbook_variable: __dpia_required__
    # Whether a DPIA is required (or the controller elected one), extracted from __screening__ as a real boolean. The gate after the screening ends the lifecycle when it is false; the negative screening stays on the accountability ledger under Article 5(2).
    dpia_required: bool
    # playbook_variable: __dpo_consultation__
    # Envelope dpo_consultation emits, with any consultation gaps listed. __dpo_consultation_ref__ is extracted from it.
    dpo_consultation: dict[str, object]
    # playbook_variable: __dpo_consultation_ref__
    # Reference to the Article 35(2) consultation record, extracted from __dpo_consultation__.
    dpo_consultation_ref: str
    # playbook_variable: __execution_id__
    # Identifier of this execution, folded into the DPIA document identifier.
    execution_id: str
    # playbook_variable: __high_risk_floor__
    # The levels on __risk_scale__ at which a risk is high: exactly likelihood and severity.
    high_risk_floor: dict[str, object]
    # playbook_variable: __measures__
    # The measures envisaged as a JSON list, each with its reference, kind (safeguard, security measure or mechanism), the assessed risks it addresses and the controls that implement it.
    measures: str
    # playbook_variable: __member_state_requires_consultation__
    # Whether Member State law requires prior consultation or authorisation for this processing under Article 36(5).
    member_state_requires_consultation: bool
    # playbook_variable: __mitigations__
    # Envelope identify_and_document_mitigations emits: measures, residual levels, residual high risks and untreated high risks. __mitigations_ref__ is extracted from it.
    mitigations: dict[str, object]
    # playbook_variable: __mitigations_documented_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) of the mitigations record.
    mitigations_documented_at: str
    # playbook_variable: __mitigations_ref__
    # Reference to the Article 35(7)(d) measures record, extracted from __mitigations__.
    mitigations_ref: str
    # playbook_variable: __necessity_assessed_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) of the necessity and proportionality assessment.
    necessity_assessed_at: str
    # playbook_variable: __necessity_assessment__
    # Envelope assess_necessity_and_proportionality emits: necessity, proportionality, the outcome and the measures still owed.
    necessity_assessment: dict[str, object]
    # playbook_variable: __necessity_record__
    # The controller's Article 35(7)(b) inputs: the necessity determination and its reasoning, the less intrusive alternatives considered and whether each suffices, data minimisation per classified category, and the six rights measures.
    necessity_record: dict[str, object]
    # playbook_variable: __processing_description__
    # Envelope gather_processing_description emits, with the WP248 Annex 2 elements still missing listed as gaps. __processing_description_ref__ is extracted from it.
    processing_description: dict[str, object]
    # playbook_variable: __processing_description_ref__
    # Reference to the Article 35(7)(a) description, extracted from __processing_description__.
    processing_description_ref: str
    # playbook_variable: __processing_ref__
    # The processing operation under assessment, keyed by its Article 30 record of processing activities. The trigger input.
    processing_ref: str
    # playbook_variable: __residual_risks__
    # The residual likelihood and severity of every assessed risk after the measures, as a JSON list.
    residual_risks: str
    # playbook_variable: __review_cadence__
    # The ISO 8601 maximum interval between reviews, extracted from __review_schedule__ (Article 35(11)).
    review_cadence: str
    # playbook_variable: __review_change_triggers__
    # The changes that prompt a review, as a JSON list from change_of_risk, data_categories, data_subjects, recipients, retention, purpose and technology. A change of risk is always included.
    review_change_triggers: str
    # playbook_variable: __review_max_interval__
    # The longest time between reviews absent a change, as an ISO 8601 date duration such as P1Y.
    review_max_interval: str
    # playbook_variable: __review_schedule__
    # Envelope schedule_review_cadence emits: the cadence, the next review due, the triggers and whether the document it attaches to is final. __review_cadence__ is extracted from it.
    review_schedule: dict[str, object]
    # playbook_variable: __review_scheduled_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) of scheduling.
    review_scheduled_at: str
    # playbook_variable: __risk_assessment__
    # Envelope identify_and_assess_risks emits: each risk on the operator's calibration, the high risks, and any reference event not assessed. __risk_assessment_ref__ is extracted from it.
    risk_assessment: dict[str, object]
    # playbook_variable: __risk_assessment_ref__
    # Reference to the Article 35(7)(c) risk assessment, extracted from __risk_assessment__.
    risk_assessment_ref: str
    # playbook_variable: __risk_register__
    # The assessed risks as a JSON list, each with its reference, reference event, risk sources, threats, impacts, likelihood and severity.
    risk_register: str
    # playbook_variable: __risk_scale__
    # The operator's ordered likelihood-and-severity levels, lowest first, as a JSON list (CACAO has no list type).
    risk_scale: str
    # playbook_variable: __risks_assessed_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) of the risk assessment.
    risks_assessed_at: str
    # playbook_variable: __ropa_entry__
    # The Article 30 record entry for __processing_ref__: the controller role, the personal-data and subject categories, special categories, criminal-offence data and its Article 10 basis, vulnerable subjects, the Article 6(1) lawful bases and the Article 9(2) condition.
    ropa_entry: dict[str, object]
    # playbook_variable: __screened_at__
    # Zulu instant (YYYY-MM-DDTHH:MM:SSZ) of the screening.
    screened_at: str
    # playbook_variable: __screening__
    # Envelope screen_dpia_triggers emits: the outcome, the rule that decided it, the criteria evaluated and the ledger retention. __dpia_case_id__, __dpia_required__ and __screening_result_ref__ are extracted from it.
    screening: dict[str, object]
    # playbook_variable: __screening_answers__
    # The operator's screening answers: the Article 35(3) points the processing meets, the matching supervisory-authority Article 35(4) and 35(5) list entries, the WP248 rev.01 criteria it meets, the Article 35(10) facts, any similar-assessment reference, the not-high-risk justification and the DPO's views on it, whether a DPO is designated, and whether the controller elects a DPIA.
    screening_answers: dict[str, object]
    # playbook_variable: __screening_result_ref__
    # Reference to the screening decision, extracted from __screening__. Retained on the accountability ledger whether or not a DPIA follows.
    screening_result_ref: str
    # playbook_variable: __workflow_id__
    # Identifier of the workflow, folded into the DPIA document identifier.
    workflow_id: str
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
async def screen_dpia_triggers(processing_ref: str, screening_answers: dict[str, object], screened_at: str) -> dict[str, object]:
    """Decide whether a DPIA is required for __processing_ref__. The first rule that applies wins: the Article 35(10) exemption, unless the Member State requires a prior DPIA; an existing assessment of similar processing (Article 35(1), last sentence); the Article 35(3) cases; the supervisory authority's Article 35(4) and 35(5) lists; and the WP248 rev.01 rule that two or more criteria call for a DPIA unless the controller documents a justification and, where a DPO is designated, the DPO's views. The controller may always elect a DPIA. A negative screening is retained on the accountability ledger with its basis. Produces __screening__, from which __dpia_case_id__, __dpia_required__ and __screening_result_ref__ are extracted.

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
        from content.playbooks.data_protection_impact_assessment.primitives.screening import screen_dpia_triggers
        __screening__ = screen_dpia_triggers(processing_ref=__processing_ref__, screened_at=__screened_at__, screening=__screening_answers__)

@tool
async def classify_processing_type(screening: dict[str, object], ropa_entry: dict[str, object], classified_at: str) -> dict[str, object]:
    """Classify the processing from its Article 30 record into the shape every later step reads: data and subject categories, special categories, criminal-offence data, vulnerable subjects in the WP248 criterion 7 vocabulary, the controller role and the lawful bases. The DPIA is the controller's, so a record held in the processor role is refused. Lawfulness gaps under Articles 6, 9(2) and 10 are recorded, not decided away. A screening that does not require a DPIA is refused, which is why the gate sits before this step. Produces __classification__.

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
        from content.playbooks.data_protection_impact_assessment.primitives.classification import classify_processing
        __classification__ = classify_processing(classified_at=__classified_at__, ropa_entry=__ropa_entry__, screening=__screening__)

@tool
async def gather_processing_description(classification: dict[str, object], description_record: dict[str, object], described_at: str) -> dict[str, object]:
    """Assemble the Article 35(7)(a) systematic description: purposes and, where Article 6(1)(f) is relied on, the legitimate interest; recipients and third-country transfers with their Chapter V basis; retention per data category; and the assets the data rely on, as WP248 rev.01 Annex 2 lists them. Missing elements are recorded as gaps rather than refused. Produces __processing_description__, from which __processing_description_ref__ is extracted.

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
        from content.playbooks.data_protection_impact_assessment.primitives.description import compose_processing_description
        __processing_description__ = compose_processing_description(classification=__classification__, described_at=__described_at__, description=__description_record__)

@tool
async def assess_necessity_and_proportionality(classification: dict[str, object], processing_description: dict[str, object], necessity_record: dict[str, object], necessity_assessed_at: str) -> dict[str, object]:
    """Assess necessity and proportionality under Article 35(7)(b). A less intrusive alternative that suffices defeats necessity; every classified data category is checked for minimisation (Article 5(1)(c)) and storage limitation (Article 5(1)(e)); lawfulness gaps and the rights measures not yet in place are listed as owed. The outcome feeds the risk assessment and the document; it does not stop the assessment. Produces __necessity_assessment__.

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
        from content.playbooks.data_protection_impact_assessment.primitives.necessity import assess_necessity_and_proportionality
        __necessity_assessment__ = assess_necessity_and_proportionality(assessed_at=__necessity_assessed_at__, assessment=__necessity_record__, classification=__classification__, description=__processing_description__)

@tool
async def identify_and_assess_risks(necessity_assessment: dict[str, object], risk_scale: str, high_risk_floor: dict[str, object], risk_register: str, risks_assessed_at: str) -> dict[str, object]:
    """Assess the risks to data subjects under Article 35(7)(c). Every risk names its sources, threats and impacts, with likelihood and severity on the operator's scale; a risk is high when both reach the operator's floor. Each of the three reference events (illegitimate access, undesired modification, disappearance) must be covered, or the event not assessed is named. Produces __risk_assessment__, from which __risk_assessment_ref__ is extracted.

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
        from content.playbooks.data_protection_impact_assessment.primitives.risk import assess_risks
        __risk_assessment__ = assess_risks(assessed_at=__risks_assessed_at__, high_risk_floor=__high_risk_floor__, necessity=__necessity_assessment__, risks=__risk_register__, scale=__risk_scale__)

@tool
async def identify_and_document_mitigations(risk_assessment: dict[str, object], measures: str, residual_risks: str, mitigations_documented_at: str) -> dict[str, object]:
    """Record the Article 35(7)(d) measures against the assessed risks and the residual level of every risk after them. A residual level above the assessed one is refused; a high risk no measure addresses is a gap. The residual levels are what the Article 36 gate reads. Produces __mitigations__, from which __mitigations_ref__ is extracted.

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
        from content.playbooks.data_protection_impact_assessment.primitives.mitigations import document_mitigations
        __mitigations__ = document_mitigations(documented_at=__mitigations_documented_at__, measures=__measures__, residual_risks=__residual_risks__, risk_assessment=__risk_assessment__)

@tool
async def dpo_consultation(mitigations: dict[str, object], consultation_record: dict[str, object], consulted_at: str) -> dict[str, object]:
    """Record the DPO's advice under Article 35(2), or the alternative accountability surface where no DPO is designated, and the Article 35(9) views of data subjects. A departure from the advice or from the views needs its documented reasons, and a decision not to seek the views needs a justification. Anything missing is a gap. Produces __dpo_consultation__, from which __dpo_consultation_ref__ is extracted.

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
        from content.playbooks.data_protection_impact_assessment.primitives.consultation import record_dpo_consultation
        __dpo_consultation__ = record_dpo_consultation(consultation=__consultation_record__, consulted_at=__consulted_at__, mitigations=__mitigations__)

@tool
async def determine_article_36_gate(mitigations: dict[str, object], member_state_requires_consultation: bool, article_36_submission: dict[str, object], determined_at: str) -> dict[str, object]:
    """Set the Article 36(1) prior-consultation flag on the residual risk, as WP248 rev.01 section III.E reads it, or because Member State law requires consultation under Article 36(5). Once the authority has received the request, record the nominal Article 36(2) windows: written advice within eight weeks, extendable by six, with the extension notified within one month. Produces __article_36_determination__, from which __article_36_pre_consultation_flag__ is extracted.

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
        from content.playbooks.data_protection_impact_assessment.primitives.prior_consultation import determine_prior_consultation
        __article_36_determination__ = determine_prior_consultation(determined_at=__determined_at__, member_state_requires_consultation=__member_state_requires_consultation__, mitigations=__mitigations__, submission=__article_36_submission__)

@tool
async def produce_dpia_document(screening: dict[str, object], classification: dict[str, object], processing_description: dict[str, object], necessity_assessment: dict[str, object], risk_assessment: dict[str, object], mitigations: dict[str, object], dpo_consultation: dict[str, object], article_36_determination: dict[str, object], workflow_id: str, execution_id: str, document_produced_at: str) -> dict[str, object]:
    """Join the nine step records of the case into the DPIA document, refusing records from another case or chain. The document is final only when nothing is left open: description gaps, measures owed, reference events not assessed, untreated high risks and consultation gaps keep it a draft. The conclusion is the first that applies: do_not_proceed, prior_consultation_required, may_proceed. It is the Article 5(2) accountability artifact and the answer to an Article 58(1)(a) information order. Produces __dpia_document__, from which __dpia_document_ref__ is extracted.

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
        from content.playbooks.data_protection_impact_assessment.primitives.document import compose_dpia_document
        __dpia_document__ = compose_dpia_document(classification=__classification__, consultation=__dpo_consultation__, description=__processing_description__, determination=__article_36_determination__, execution_id=__execution_id__, mitigations=__mitigations__, necessity=__necessity_assessment__, produced_at=__document_produced_at__, risk_assessment=__risk_assessment__, screening=__screening__, workflow_id=__workflow_id__)

@tool
async def schedule_review_cadence(dpia_document: dict[str, object], review_max_interval: str, review_change_triggers: str, change_management_ref: str, review_scheduled_at: str) -> dict[str, object]:
    """Schedule the Article 35(11) review. A change of risk always triggers one; the operator may add specific changes, pinned to its change-management surface. The next review falls due no later than the maximum interval. A draft document is scheduled too, and the schedule says so. Produces __review_schedule__, from which __review_cadence__ is extracted.

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
        from content.playbooks.data_protection_impact_assessment.primitives.review import schedule_review
        __review_schedule__ = schedule_review(change_management_ref=__change_management_ref__, change_triggers=__review_change_triggers__, document=__dpia_document__, max_interval=__review_max_interval__, scheduled_at=__review_scheduled_at__)

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

