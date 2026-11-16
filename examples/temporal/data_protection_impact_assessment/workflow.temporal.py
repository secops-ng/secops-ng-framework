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
async def screen_dpia_triggers(processing_ref: str, screening_answers: dict[str, object], screened_at: str) -> dict[str, object]:
    """Decide whether a DPIA is required for __processing_ref__. The first rule that applies wins: the Article 35(10) exemption, unless the Member State requires a prior DPIA; an existing assessment of similar processing (Article 35(1), last sentence); the Article 35(3) cases; the supervisory authority's Article 35(4) and 35(5) lists; and the WP248 rev.01 rule that two or more criteria call for a DPIA unless the controller documents a justification and, where a DPO is designated, the DPO's views. The controller may always elect a DPIA. A negative screening is retained on the accountability ledger with its basis. Produces __screening__, from which __dpia_case_id__, __dpia_required__ and __screening_result_ref__ are extracted.

    CACAO step_id: action--d91a35c0-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d91a35c0-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000002', 'secops_ng.step.name': 'screen_dpia_triggers', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'screen_dpia_triggers'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d91a35c0-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000002', 'secops_ng.step.name': 'screen_dpia_triggers', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'screen_dpia_triggers'})
        )
        from content.playbooks.data_protection_impact_assessment.primitives.screening import screen_dpia_triggers
        __screening__ = screen_dpia_triggers(processing_ref=__processing_ref__, screened_at=__screened_at__, screening=__screening_answers__)

SCREEN_DPIA_TRIGGERS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def classify_processing_type(screening: dict[str, object], ropa_entry: dict[str, object], classified_at: str) -> dict[str, object]:
    """Classify the processing from its Article 30 record into the shape every later step reads: data and subject categories, special categories, criminal-offence data, vulnerable subjects in the WP248 criterion 7 vocabulary, the controller role and the lawful bases. The DPIA is the controller's, so a record held in the processor role is refused. Lawfulness gaps under Articles 6, 9(2) and 10 are recorded, not decided away. A screening that does not require a DPIA is refused, which is why the gate sits before this step. Produces __classification__.

    CACAO step_id: action--d91a35c0-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d91a35c0-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify_processing_type', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_processing_type'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d91a35c0-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify_processing_type', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_processing_type'})
        )
        from content.playbooks.data_protection_impact_assessment.primitives.classification import classify_processing
        __classification__ = classify_processing(classified_at=__classified_at__, ropa_entry=__ropa_entry__, screening=__screening__)

CLASSIFY_PROCESSING_TYPE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def gather_processing_description(classification: dict[str, object], description_record: dict[str, object], described_at: str) -> dict[str, object]:
    """Assemble the Article 35(7)(a) systematic description: purposes and, where Article 6(1)(f) is relied on, the legitimate interest; recipients and third-country transfers with their Chapter V basis; retention per data category; and the assets the data rely on, as WP248 rev.01 Annex 2 lists them. Missing elements are recorded as gaps rather than refused. Produces __processing_description__, from which __processing_description_ref__ is extracted.

    CACAO step_id: action--d91a35c0-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d91a35c0-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000004', 'secops_ng.step.name': 'gather_processing_description', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'gather_processing_description'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d91a35c0-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000004', 'secops_ng.step.name': 'gather_processing_description', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'gather_processing_description'})
        )
        from content.playbooks.data_protection_impact_assessment.primitives.description import compose_processing_description
        __processing_description__ = compose_processing_description(classification=__classification__, described_at=__described_at__, description=__description_record__)

GATHER_PROCESSING_DESCRIPTION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def assess_necessity_and_proportionality(classification: dict[str, object], processing_description: dict[str, object], necessity_record: dict[str, object], necessity_assessed_at: str) -> dict[str, object]:
    """Assess necessity and proportionality under Article 35(7)(b). A less intrusive alternative that suffices defeats necessity; every classified data category is checked for minimisation (Article 5(1)(c)) and storage limitation (Article 5(1)(e)); lawfulness gaps and the rights measures not yet in place are listed as owed. The outcome feeds the risk assessment and the document; it does not stop the assessment. Produces __necessity_assessment__.

    CACAO step_id: action--d91a35c0-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d91a35c0-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000005', 'secops_ng.step.name': 'assess_necessity_and_proportionality', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assess_necessity_and_proportionality'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d91a35c0-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000005', 'secops_ng.step.name': 'assess_necessity_and_proportionality', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assess_necessity_and_proportionality'})
        )
        from content.playbooks.data_protection_impact_assessment.primitives.necessity import assess_necessity_and_proportionality
        __necessity_assessment__ = assess_necessity_and_proportionality(assessed_at=__necessity_assessed_at__, assessment=__necessity_record__, classification=__classification__, description=__processing_description__)

ASSESS_NECESSITY_AND_PROPORTIONALITY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def identify_and_assess_risks(necessity_assessment: dict[str, object], risk_scale: str, high_risk_floor: dict[str, object], risk_register: str, risks_assessed_at: str) -> dict[str, object]:
    """Assess the risks to data subjects under Article 35(7)(c). Every risk names its sources, threats and impacts, with likelihood and severity on the operator's scale; a risk is high when both reach the operator's floor. Each of the three reference events (illegitimate access, undesired modification, disappearance) must be covered, or the event not assessed is named. Produces __risk_assessment__, from which __risk_assessment_ref__ is extracted.

    CACAO step_id: action--d91a35c0-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d91a35c0-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000006', 'secops_ng.step.name': 'identify_and_assess_risks', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'identify_and_assess_risks'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d91a35c0-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000006', 'secops_ng.step.name': 'identify_and_assess_risks', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'identify_and_assess_risks'})
        )
        from content.playbooks.data_protection_impact_assessment.primitives.risk import assess_risks
        __risk_assessment__ = assess_risks(assessed_at=__risks_assessed_at__, high_risk_floor=__high_risk_floor__, necessity=__necessity_assessment__, risks=__risk_register__, scale=__risk_scale__)

IDENTIFY_AND_ASSESS_RISKS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def identify_and_document_mitigations(risk_assessment: dict[str, object], measures: str, residual_risks: str, mitigations_documented_at: str) -> dict[str, object]:
    """Record the Article 35(7)(d) measures against the assessed risks and the residual level of every risk after them. A residual level above the assessed one is refused; a high risk no measure addresses is a gap. The residual levels are what the Article 36 gate reads. Produces __mitigations__, from which __mitigations_ref__ is extracted.

    CACAO step_id: action--d91a35c0-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d91a35c0-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000007', 'secops_ng.step.name': 'identify_and_document_mitigations', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'identify_and_document_mitigations'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d91a35c0-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000007', 'secops_ng.step.name': 'identify_and_document_mitigations', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'identify_and_document_mitigations'})
        )
        from content.playbooks.data_protection_impact_assessment.primitives.mitigations import document_mitigations
        __mitigations__ = document_mitigations(documented_at=__mitigations_documented_at__, measures=__measures__, residual_risks=__residual_risks__, risk_assessment=__risk_assessment__)

IDENTIFY_AND_DOCUMENT_MITIGATIONS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def dpo_consultation(mitigations: dict[str, object], consultation_record: dict[str, object], consulted_at: str) -> dict[str, object]:
    """Record the DPO's advice under Article 35(2), or the alternative accountability surface where no DPO is designated, and the Article 35(9) views of data subjects. A departure from the advice or from the views needs its documented reasons, and a decision not to seek the views needs a justification. Anything missing is a gap. Produces __dpo_consultation__, from which __dpo_consultation_ref__ is extracted.

    CACAO step_id: action--d91a35c0-0000-4000-8000-000000000008
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d91a35c0-0000-4000-8000-000000000008',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000008', 'secops_ng.step.name': 'dpo_consultation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'dpo_consultation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d91a35c0-0000-4000-8000-000000000008', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000008', 'secops_ng.step.name': 'dpo_consultation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'dpo_consultation'})
        )
        from content.playbooks.data_protection_impact_assessment.primitives.consultation import record_dpo_consultation
        __dpo_consultation__ = record_dpo_consultation(consultation=__consultation_record__, consulted_at=__consulted_at__, mitigations=__mitigations__)

DPO_CONSULTATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def determine_article_36_gate(mitigations: dict[str, object], member_state_requires_consultation: bool, article_36_submission: dict[str, object], determined_at: str) -> dict[str, object]:
    """Set the Article 36(1) prior-consultation flag on the residual risk, as WP248 rev.01 section III.E reads it, or because Member State law requires consultation under Article 36(5). Once the authority has received the request, record the nominal Article 36(2) windows: written advice within eight weeks, extendable by six, with the extension notified within one month. Produces __article_36_determination__, from which __article_36_pre_consultation_flag__ is extracted.

    CACAO step_id: action--d91a35c0-0000-4000-8000-000000000009
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d91a35c0-0000-4000-8000-000000000009',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000009', 'secops_ng.step.name': 'determine_article_36_gate', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'determine_article_36_gate'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d91a35c0-0000-4000-8000-000000000009', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000009', 'secops_ng.step.name': 'determine_article_36_gate', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'determine_article_36_gate'})
        )
        from content.playbooks.data_protection_impact_assessment.primitives.prior_consultation import determine_prior_consultation
        __article_36_determination__ = determine_prior_consultation(determined_at=__determined_at__, member_state_requires_consultation=__member_state_requires_consultation__, mitigations=__mitigations__, submission=__article_36_submission__)

DETERMINE_ARTICLE_36_GATE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def produce_dpia_document(screening: dict[str, object], classification: dict[str, object], processing_description: dict[str, object], necessity_assessment: dict[str, object], risk_assessment: dict[str, object], mitigations: dict[str, object], dpo_consultation: dict[str, object], article_36_determination: dict[str, object], workflow_id: str, execution_id: str, document_produced_at: str) -> dict[str, object]:
    """Join the nine step records of the case into the DPIA document, refusing records from another case or chain. The document is final only when nothing is left open: description gaps, measures owed, reference events not assessed, untreated high risks and consultation gaps keep it a draft. The conclusion is the first that applies: do_not_proceed, prior_consultation_required, may_proceed. It is the Article 5(2) accountability artifact and the answer to an Article 58(1)(a) information order. Produces __dpia_document__, from which __dpia_document_ref__ is extracted.

    CACAO step_id: action--d91a35c0-0000-4000-8000-00000000000a
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d91a35c0-0000-4000-8000-00000000000a',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-00000000000a', 'secops_ng.step.name': 'produce_dpia_document', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'produce_dpia_document'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d91a35c0-0000-4000-8000-00000000000a', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-00000000000a', 'secops_ng.step.name': 'produce_dpia_document', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'produce_dpia_document'})
        )
        from content.playbooks.data_protection_impact_assessment.primitives.document import compose_dpia_document
        __dpia_document__ = compose_dpia_document(classification=__classification__, consultation=__dpo_consultation__, description=__processing_description__, determination=__article_36_determination__, execution_id=__execution_id__, mitigations=__mitigations__, necessity=__necessity_assessment__, produced_at=__document_produced_at__, risk_assessment=__risk_assessment__, screening=__screening__, workflow_id=__workflow_id__)

PRODUCE_DPIA_DOCUMENT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def schedule_review_cadence(dpia_document: dict[str, object], review_max_interval: str, review_change_triggers: str, change_management_ref: str, review_scheduled_at: str) -> dict[str, object]:
    """Schedule the Article 35(11) review. A change of risk always triggers one; the operator may add specific changes, pinned to its change-management surface. The next review falls due no later than the maximum interval. A draft document is scheduled too, and the schedule says so. Produces __review_schedule__, from which __review_cadence__ is extracted.

    CACAO step_id: action--d91a35c0-0000-4000-8000-00000000000b
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d91a35c0-0000-4000-8000-00000000000b',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'schedule_review_cadence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'schedule_review_cadence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d91a35c0-0000-4000-8000-00000000000b', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'schedule_review_cadence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'schedule_review_cadence'})
        )
        from content.playbooks.data_protection_impact_assessment.primitives.review import schedule_review
        __review_schedule__ = schedule_review(change_management_ref=__change_management_ref__, change_triggers=__review_change_triggers__, document=__dpia_document__, max_interval=__review_max_interval__, scheduled_at=__review_scheduled_at__)

SCHEDULE_REVIEW_CADENCE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookDataProtectionImpactAssessmentV1Workflow:
    """CACAO v2 playbook for the operator-side data protection impact assessment (DPIA) lifecycle a controller runs before deploying processing that is likely to result in a high risk to the rights and freedoms of natural persons under GDPR Article 35. Distinct from the after-the-fact breach-notification lane (Articles 33-34) and from the subject-initiated rights lifecycle (Articles 15-22): this is the proactive ex-ante assessment lane that runs before the processing is bound to production. Every step is bound to a deterministic primitive: screen_dpia_triggers (Article 35(10), similar-assessment coverage, Article 35(3), the supervisory authority's Article 35(4) and 35(5) lists, the WP248 rev.01 two-criteria rule) → a gate that ends the lifecycle on a negative screening, retained on the accountability ledger → classify_processing_type from the Article 30 record → gather_processing_description (Article 35(7)(a)) → assess_necessity_and_proportionality (Article 35(7)(b)) → identify_and_assess_risks (Article 35(7)(c)) on the operator's calibration → identify_and_document_mitigations (Article 35(7)(d)) with the residual risk after them → dpo_consultation (Article 35(2), and the Article 35(9) views of data subjects) → determine_article_36_gate on the residual risk and Article 36(5) → produce_dpia_document, final only with nothing left open → schedule_review_cadence (Article 35(11)). Evidence outputs: dpia-screening-result, dpia-document, dpo-consultation-record, article-36-pre-consultation-flag (boolean). The Article 30 record, the supervisory-authority lists, the risk taxonomy and the evidence store stay adapter-bound operator surfaces. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--d91a35c0-0000-4000-8000-000000000001
    stable_id         : playbook.data_protection_impact_assessment@v1
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--d91a35c0-0000-4000-8000-000000000001
    activities        : screen_dpia_triggers, classify_processing_type, gather_processing_description, assess_necessity_and_proportionality, identify_and_assess_risks, identify_and_document_mitigations, dpo_consultation, determine_article_36_gate, produce_dpia_document, schedule_review_cadence
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.data_protection_impact_assessment@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.data_protection_impact_assessment@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.data_protection_impact_assessment@v1'"
            )

WORKFLOW = PlaybookDataProtectionImpactAssessmentV1Workflow
ACTIVITIES = (screen_dpia_triggers, classify_processing_type, gather_processing_description, assess_necessity_and_proportionality, identify_and_assess_risks, identify_and_document_mitigations, dpo_consultation, determine_article_36_gate, produce_dpia_document, schedule_review_cadence,)
RETRY_POLICIES = (SCREEN_DPIA_TRIGGERS_RETRY_POLICY, CLASSIFY_PROCESSING_TYPE_RETRY_POLICY, GATHER_PROCESSING_DESCRIPTION_RETRY_POLICY, ASSESS_NECESSITY_AND_PROPORTIONALITY_RETRY_POLICY, IDENTIFY_AND_ASSESS_RISKS_RETRY_POLICY, IDENTIFY_AND_DOCUMENT_MITIGATIONS_RETRY_POLICY, DPO_CONSULTATION_RETRY_POLICY, DETERMINE_ARTICLE_36_GATE_RETRY_POLICY, PRODUCE_DPIA_DOCUMENT_RETRY_POLICY, SCHEDULE_REVIEW_CADENCE_RETRY_POLICY,)
