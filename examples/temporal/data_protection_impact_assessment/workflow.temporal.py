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
async def screen_dpia_triggers(processing_ref: str) -> dict[str, object]:
    """SKELETON — screen __processing_ref__ against the Article 35(3)(a-c) mandatory-DPIA triggers (systematic and extensive evaluation of personal aspects based on automated processing; large-scale processing of special categories of data or personal data relating to criminal convictions and offences; systematic monitoring of a publicly accessible area on a large scale), against the operator's supervisory-authority Article 35(4) list of processing kinds that require a DPIA in the operator's jurisdiction, and against the general Article 35(1) likely-to-result-in-a-high-risk test taking into account the nature, scope, context and purposes of the processing. Assigns __dpia_case_id__, sets __dpia_required__, and records __screening_result_ref__ on the accountability ledger. A false outcome short- circuits the lifecycle with the negative screening retained as part of the operator's Article 5(2) accountability record. TODO (CORE): pin the operator's supervisory-authority Article 35(4) list adapter and the novel-technology signal (WP248 rev.01 criteria).

    CACAO step_id: action--d91a35c0-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d91a35c0-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000002', 'secops_ng.step.name': 'screen_dpia_triggers', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'screen_dpia_triggers'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d91a35c0-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000002', 'secops_ng.step.name': 'screen_dpia_triggers', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'screen_dpia_triggers'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d91a35c0-0000-4000-8000-000000000002'"
        )

SCREEN_DPIA_TRIGGERS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def classify_processing_type(dpia_case_id: str, processing_ref: str) -> None:
    """SKELETON — classify the processing envelope against the operator's processing-inventory surface (the Article 30 record of processing activities as canonical join key) so downstream steps read a common shape: personal-data categories, special-category involvement, subject categories (including vulnerable-subject axes such as children, employees, patients), controller-vs-processor role, and the lawful-basis attribution the processing relies on under Article 6 (and where applicable Article 9(2)). Anchors the assessment scope; does not itself perform the risk determination. TODO (CORE): pin the RoPA-inventory adapter and the vulnerable-subject axis catalogue.

    CACAO step_id: action--d91a35c0-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d91a35c0-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify_processing_type', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_processing_type'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d91a35c0-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000003', 'secops_ng.step.name': 'classify_processing_type', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'classify_processing_type'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d91a35c0-0000-4000-8000-000000000003'"
        )

CLASSIFY_PROCESSING_TYPE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def gather_processing_description(dpia_case_id: str, processing_ref: str) -> str:
    """SKELETON — assemble the systematic description of the envisaged processing operations and their purposes per Article 35(7)(a): purposes of the processing, categories of personal data and of data subjects, recipients or categories of recipients (including any transfers to third countries or international organisations), envisaged retention periods or the criteria used to determine them, and where applicable the legitimate interests pursued by the controller. Records __processing_description_ref__ so downstream steps read a stable description surface. TODO (CORE): pin the RoPA-extraction adapter and the transfer-legs cross-reference.

    CACAO step_id: action--d91a35c0-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d91a35c0-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000004', 'secops_ng.step.name': 'gather_processing_description', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'gather_processing_description'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d91a35c0-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000004', 'secops_ng.step.name': 'gather_processing_description', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'gather_processing_description'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d91a35c0-0000-4000-8000-000000000004'"
        )

GATHER_PROCESSING_DESCRIPTION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def assess_necessity_and_proportionality(dpia_case_id: str, processing_description_ref: str) -> None:
    """SKELETON — assess the necessity and proportionality of the processing operations in relation to the purposes per Article 35(7)(b). Necessity: whether the processing is required to achieve the purpose or whether a less- intrusive alternative would suffice. Proportionality: whether the categories of data and the scope of the processing are commensurate with the purpose and not excessive. Records the reasoning on the case; the outcome feeds the risk assessment and the mitigations identification downstream. TODO (CORE): pin the necessity-and-proportionality assessment template.

    CACAO step_id: action--d91a35c0-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d91a35c0-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000005', 'secops_ng.step.name': 'assess_necessity_and_proportionality', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assess_necessity_and_proportionality'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d91a35c0-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000005', 'secops_ng.step.name': 'assess_necessity_and_proportionality', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'assess_necessity_and_proportionality'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d91a35c0-0000-4000-8000-000000000005'"
        )

ASSESS_NECESSITY_AND_PROPORTIONALITY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def identify_and_assess_risks(dpia_case_id: str, processing_description_ref: str) -> str:
    """SKELETON — identify and assess the risks to the rights and freedoms of natural persons the processing generates per Article 35(7)(c). Applies the operator's declared risk taxonomy over the risk-source, risk- event, and impact axes (illegitimate access, unauthorised modification, disappearance of personal data — the three EDPB reference risk categories — plus operator-declared context-specific axes). Records per-risk likelihood and severity and the residual-risk profile that determine_article_36_gate reads downstream. Records __risk_assessment_ref__. TODO (CORE): pin the risk-taxonomy binding and the residual- risk calibration surface.

    CACAO step_id: action--d91a35c0-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d91a35c0-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000006', 'secops_ng.step.name': 'identify_and_assess_risks', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'identify_and_assess_risks'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d91a35c0-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000006', 'secops_ng.step.name': 'identify_and_assess_risks', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'identify_and_assess_risks'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d91a35c0-0000-4000-8000-000000000006'"
        )

IDENTIFY_AND_ASSESS_RISKS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def identify_and_document_mitigations(dpia_case_id: str, risk_assessment_ref: str) -> str:
    """SKELETON — identify and document the measures envisaged to address the risks per Article 35(7)(d): safeguards, security measures, and mechanisms to ensure the protection of personal data and demonstrate compliance with the Regulation, taking into account the rights and legitimate interests of data subjects and other persons concerned. Records __mitigations_ref__ and pins the per-risk mitigation attribution so determine_article_36_gate can read the residual risk after mitigation. TODO (CORE): pin the safeguards catalogue and the security-measure control-reference binding.

    CACAO step_id: action--d91a35c0-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d91a35c0-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000007', 'secops_ng.step.name': 'identify_and_document_mitigations', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'identify_and_document_mitigations'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d91a35c0-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000007', 'secops_ng.step.name': 'identify_and_document_mitigations', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'identify_and_document_mitigations'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d91a35c0-0000-4000-8000-000000000007'"
        )

IDENTIFY_AND_DOCUMENT_MITIGATIONS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def dpo_consultation(dpia_case_id: str, processing_description_ref: str, risk_assessment_ref: str, mitigations_ref: str) -> str:
    """SKELETON — seek the advice of the Data Protection Officer where the controller has designated one, per Article 35(2). The DPO reviews the assembled description, necessity-and-proportionality assessment, risk assessment, and mitigations documentation and records advice on the DPIA case. Where the controller has not designated a DPO because Article 37 does not require it, the record documents that fact and the alternative accountability surface the controller relies on. Records __dpo_consultation_ref__. TODO (CORE): pin the DPO-consultation intake adapter and the alternative-accountability-surface record where no DPO is designated.

    CACAO step_id: action--d91a35c0-0000-4000-8000-000000000008
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d91a35c0-0000-4000-8000-000000000008',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000008', 'secops_ng.step.name': 'dpo_consultation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'dpo_consultation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d91a35c0-0000-4000-8000-000000000008', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000008', 'secops_ng.step.name': 'dpo_consultation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'dpo_consultation'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d91a35c0-0000-4000-8000-000000000008'"
        )

DPO_CONSULTATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def determine_article_36_gate(dpia_case_id: str, risk_assessment_ref: str, mitigations_ref: str) -> bool:
    """SKELETON — determine whether the residual risk, absent measures taken by the controller to mitigate it, would result in a high risk under Article 36(1) and therefore triggers prior consultation with the supervisory authority before the processing may begin. Reads the risk assessment against the applied mitigations and sets __article_36_pre_consultation_flag__. Where the flag is true, the controller must consult the supervisory authority under Article 36(1) and the processing may not begin until the consultation window completes (Article 36(2): up to eight weeks, extendable by six weeks taking into account the complexity of the intended processing). TODO (CORE): pin the supervisory- authority pre-consultation submission chain and the Article 36(2) consultation-window gate.

    CACAO step_id: action--d91a35c0-0000-4000-8000-000000000009
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d91a35c0-0000-4000-8000-000000000009',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000009', 'secops_ng.step.name': 'determine_article_36_gate', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'determine_article_36_gate'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d91a35c0-0000-4000-8000-000000000009', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-000000000009', 'secops_ng.step.name': 'determine_article_36_gate', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'determine_article_36_gate'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d91a35c0-0000-4000-8000-000000000009'"
        )

DETERMINE_ARTICLE_36_GATE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def produce_dpia_document(dpia_case_id: str, processing_description_ref: str, risk_assessment_ref: str, mitigations_ref: str, dpo_consultation_ref: str, article_36_pre_consultation_flag: bool) -> str:
    """SKELETON — produce the durable DPIA document artifact for the case. Assembles the Article 35(7)(a)-(d) content (systematic description, necessity-and- proportionality, risk assessment, mitigations), the Article 35(2) DPO advice, the Article 36 gate outcome, and the review-cadence schedule into the operator's declared DPIA-document template. Records __dpia_document_ref__ on the accountability ledger. The document is the primary response to any subsequent Article 58(1)(a) supervisory-authority information order and the operator's Article 5(2) accountability artifact for this processing envelope. TODO (CORE): pin the DPIA-document template and the evidence-store binding.

    CACAO step_id: action--d91a35c0-0000-4000-8000-00000000000a
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d91a35c0-0000-4000-8000-00000000000a',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-00000000000a', 'secops_ng.step.name': 'produce_dpia_document', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'produce_dpia_document'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d91a35c0-0000-4000-8000-00000000000a', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-00000000000a', 'secops_ng.step.name': 'produce_dpia_document', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'produce_dpia_document'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d91a35c0-0000-4000-8000-00000000000a'"
        )

PRODUCE_DPIA_DOCUMENT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def schedule_review_cadence(dpia_case_id: str, dpia_document_ref: str) -> str:
    """SKELETON — schedule the DPIA review cadence per Article 35(11). At minimum, the review is triggered on any material change to the risk represented by the processing envelope (change in categories of data, subjects, recipients, retention, purpose, or underlying-technology substrate). Records __review_cadence__ as the maximum interval between reviews absent such a change, and pins the review trigger to the operator's change-management surface. TODO (CORE): pin the change-management adapter and the review-trigger evidence-emission binding.

    CACAO step_id: action--d91a35c0-0000-4000-8000-00000000000b
    """
    with _TRACER.start_as_current_span(
        name='activity.action--d91a35c0-0000-4000-8000-00000000000b',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'schedule_review_cadence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'schedule_review_cadence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--d91a35c0-0000-4000-8000-00000000000b', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--d91a35c0-0000-4000-8000-00000000000b', 'secops_ng.step.name': 'schedule_review_cadence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'schedule_review_cadence'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--d91a35c0-0000-4000-8000-00000000000b'"
        )

SCHEDULE_REVIEW_CADENCE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookDataProtectionImpactAssessmentV1Workflow:
    """SKELETON — CACAO v2 scaffold for the operator-side data protection impact assessment (DPIA) lifecycle a controller runs before deploying processing that is likely to result in a high risk to the rights and freedoms of natural persons under GDPR Article 35. Distinct from the after-the-fact breach-notification lane (Articles 33-34) and from the subject-initiated rights lifecycle (Articles 15-22): this is the proactive ex-ante assessment lane that runs before the processing is bound to production. The lifecycle chains ten steps: screen_dpia_triggers against the Article 35(3) mandatory-DPIA triggers (novel technology, large-scale processing, systematic-monitoring) and the operator's supervisory-authority Article 35(4) blacklist → classify_processing_type against the processing-inventory surface → gather_processing_description (Article 35(7)(a): purposes, categories of data and subjects, recipients, retention) → assess_necessity_and_proportionality (Article 35(7)(b)) → identify_and_assess_risks to rights and freedoms (Article 35(7)(c)) → identify_and_document_mitigations (Article 35(7)(d): safeguards, security measures, mechanisms) → dpo_consultation to obtain the Data Protection Officer's advice under Article 35(2) → determine_article_36_gate on the residual-risk threshold that triggers prior consultation with the supervisory authority under Article 36(1) → produce_dpia_document as the durable artifact recording the assessment for the operator's Article 5(2) accountability posture → schedule_review_cadence with a re-assessment hook at each material processing change under Article 35(11). Evidence outputs: dpia-screening-result, dpia-document, dpo-consultation- record, article-36-pre-consultation-flag (boolean). SKELETON only: the processing-inventory adapter, the risk-taxonomy binding, and the DPIA-document template are declared as adapter-bound surfaces the operator wires; a sibling CORE card lands the templates, the OSCAL binding closure, and the supervisory-authority pre-consultation submission chain. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--d91a35c0-0000-4000-8000-000000000001
    stable_id         : playbook.data_protection_impact_assessment@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--d91a35c0-0000-4000-8000-000000000001
    activities        : screen_dpia_triggers, classify_processing_type, gather_processing_description, assess_necessity_and_proportionality, identify_and_assess_risks, identify_and_document_mitigations, dpo_consultation, determine_article_36_gate, produce_dpia_document, schedule_review_cadence
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.data_protection_impact_assessment@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.data_protection_impact_assessment@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--d91a35c0-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.data_protection_impact_assessment@v1'"
            )

WORKFLOW = PlaybookDataProtectionImpactAssessmentV1Workflow
ACTIVITIES = (screen_dpia_triggers, classify_processing_type, gather_processing_description, assess_necessity_and_proportionality, identify_and_assess_risks, identify_and_document_mitigations, dpo_consultation, determine_article_36_gate, produce_dpia_document, schedule_review_cadence,)
RETRY_POLICIES = (SCREEN_DPIA_TRIGGERS_RETRY_POLICY, CLASSIFY_PROCESSING_TYPE_RETRY_POLICY, GATHER_PROCESSING_DESCRIPTION_RETRY_POLICY, ASSESS_NECESSITY_AND_PROPORTIONALITY_RETRY_POLICY, IDENTIFY_AND_ASSESS_RISKS_RETRY_POLICY, IDENTIFY_AND_DOCUMENT_MITIGATIONS_RETRY_POLICY, DPO_CONSULTATION_RETRY_POLICY, DETERMINE_ARTICLE_36_GATE_RETRY_POLICY, PRODUCE_DPIA_DOCUMENT_RETRY_POLICY, SCHEDULE_REVIEW_CADENCE_RETRY_POLICY,)
