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
async def detect_and_classify(incident_id: str, classification_criteria: dict[str, object], classified_at: str, aggregation: dict[str, object]) -> dict[str, object]:
    """Apply the Art. 8(1) combination rule of Delegated Regulation (EU) 2024/1772 to the operator's per-criterion determinations: an incident is major when a critical service is affected and either malicious unauthorised access that may result in data losses was identified, or at least two materiality thresholds are met. Recurring incidents with the same apparent root cause are classified on their collective impact. Produces __classification__, from which __classification_decision_id__ and __incident_major__ are extracted; the not-major gate reads the latter.

    CACAO step_id: action--71000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--71000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect and classify', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_and_classify'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--71000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect and classify', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_and_classify'})
        )
        from content.playbooks.dora_major_incident_reporting.primitives.classification import classify_major_incident
        __classification__ = classify_major_incident(incident_id=__incident_id__, criteria=__classification_criteria__, classified_at=__classified_at__, aggregation=__aggregation__)

DETECT_AND_CLASSIFY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_authority_initial(classification: dict[str, object], reporting_window: str, aware_at: str, initial_submitted_at: str, initial_impact: dict[str, object], initial_mitigation: dict[str, object], source_url: str, initial_submission_ref: str) -> dict[str, object]:
    """Compose the Art. 19(4)(a) initial notification as a schema-conforming report, due within four hours of classification and no later than 24 hours after awareness, or four hours after a classification made more than 24 hours after awareness (Delegated Regulation (EU) 2025/301, Art. 5(1)(a) and 5(2)). Submission to the competent authority is the adapter's. Produces __initial_notification__, from which __initial_notification_id__ is extracted.

    CACAO step_id: action--71000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--71000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'notify authority initial', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_authority_initial'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--71000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'notify authority initial', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_authority_initial'})
        )
        from content.playbooks.dora_major_incident_reporting.primitives.notification import compose_initial_notification
        __initial_notification__ = compose_initial_notification(classification=__classification__, reporting_window=__reporting_window__, aware_at=__aware_at__, submitted_at=__initial_submitted_at__, impact=__initial_impact__, mitigation=__initial_mitigation__, source_url=__source_url__, submission_ref=__initial_submission_ref__)

NOTIFY_AUTHORITY_INITIAL_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_authority_intermediate(classification: dict[str, object], initial_notification: dict[str, object], reporting_window: str, aware_at: str, intermediate_submitted_at: str, intermediate_impact: dict[str, object], intermediate_mitigation: dict[str, object], source_url: str, intermediate_submission_ref: str) -> dict[str, object]:
    """Compose the Art. 19(4)(b) intermediate report, linked to the initial notification, due within 72 hours of the submission of the initial notification (Delegated Regulation (EU) 2025/301, Art. 5(1)(b)), not of classification. An updated intermediate report is owed when regular activities have recovered. Produces __intermediate_report__, from which __intermediate_report_id__ is extracted.

    CACAO step_id: action--71000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--71000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'notify authority intermediate', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_authority_intermediate'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--71000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'notify authority intermediate', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_authority_intermediate'})
        )
        from content.playbooks.dora_major_incident_reporting.primitives.notification import compose_intermediate_report
        __intermediate_report__ = compose_intermediate_report(classification=__classification__, initial=__initial_notification__, reporting_window=__reporting_window__, aware_at=__aware_at__, submitted_at=__intermediate_submitted_at__, impact=__intermediate_impact__, mitigation=__intermediate_mitigation__, source_url=__source_url__, submission_ref=__intermediate_submission_ref__)

NOTIFY_AUTHORITY_INTERMEDIATE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_authority_final(classification: dict[str, object], intermediate_report: dict[str, object], reporting_window: str, aware_at: str, final_submitted_at: str, final_impact: dict[str, object], final_mitigation: dict[str, object], source_url: str, final_submission_ref: str) -> dict[str, object]:
    """Compose the Art. 19(4)(c) final report, linked to the intermediate report, due no later than one month after the intermediate report was submitted (Delegated Regulation (EU) 2025/301, Art. 5(1)(c)). Produces __final_report__, from which __final_report_id__ is extracted.

    CACAO step_id: action--71000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--71000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'notify authority final', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_authority_final'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--71000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'notify authority final', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_authority_final'})
        )
        from content.playbooks.dora_major_incident_reporting.primitives.notification import compose_final_report
        __final_report__ = compose_final_report(classification=__classification__, intermediate=__intermediate_report__, reporting_window=__reporting_window__, aware_at=__aware_at__, submitted_at=__final_submitted_at__, impact=__final_impact__, mitigation=__final_mitigation__, source_url=__source_url__, submission_ref=__final_submission_ref__)

NOTIFY_AUTHORITY_FINAL_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def close_and_archive(classification: dict[str, object], initial_notification: dict[str, object], intermediate_report: dict[str, object], final_report: dict[str, object], cross_regime_refs: str, workflow_id: str, execution_id: str, captured_at: str) -> dict[str, object]:
    """Compose the dated cycle-archival record on both branches: the classification, the three reports with their deadline outcomes for a major incident, none for a non-major one, and references to the notifications filed under other regimes (NIS2 Art. 23, GDPR Art. 33). A major cycle without its complete chain, or a non-major one with a report attached, fails loud. Produces __cycle_archive__, from which __cycle_archive_id__ is extracted.

    CACAO step_id: action--71000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--71000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'close and archive', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'close_and_archive'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--71000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'close and archive', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'close_and_archive'})
        )
        from content.playbooks.dora_major_incident_reporting.primitives.archive import compose_cycle_archive
        __cycle_archive__ = compose_cycle_archive(classification=__classification__, initial=__initial_notification__, intermediate=__intermediate_report__, final=__final_report__, cross_regime_refs=__cross_regime_refs__, workflow_id=__workflow_id__, execution_id=__execution_id__, captured_at=__captured_at__)

CLOSE_AND_ARCHIVE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookDoraMajorIncidentReportingV1Workflow:
    """SKELETON — CACAO v2 scaffold for the DORA Chapter III major-ICT-related incident reporting lifecycle a financial entity discharges to its competent authority per DORA Regulation (EU) 2022/2554 Article 19. Composes the operator-side notification cycle keyed on the three DORA-specific milestones (initial notification within 4h of major classification / no later than 24h from awareness per Art. 19(4)(a); intermediate report within 72h of major classification per Art. 19(4)(b); final report no later than one month after the intermediate report per Art. 19(4)(c)) plus a closing archival step. Distinct from playbook.incident_management@v1 which is the NIS2 Art. 23 shaped notification engine (early-warning within 24h, notification within 72h, final report within one month against the CSIRT / competent authority chain); this playbook is the DORA-flavoured lifecycle keyed on the ESA / NCA authority chain and the Commission ITS content shape (Commission Implementing Regulation (EU) 2024/2956). Distinct also from playbook.dora_tlpt_programme@v1 which is the Chapter IV testing-programme discipline. Chapter III classification is handled upstream by the deterministic classifier (Commission Delegated Regulation (EU) 2024/1772); this playbook consumes a classified-as-major decision at the detect-and-classify step and drives the three-milestone reporting cycle to closure. SKELETON only — the deterministic per-milestone submission adapters, the competent-authority notification channel bindings, and the per-target compile examples are owned by CORE / EXTEND sibling cards.

    CACAO playbook id : playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d
    stable_id         : playbook.dora_major_incident_reporting@v1
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--71000000-0000-4000-8000-000000000001
    activities        : detect_and_classify, notify_authority_initial, notify_authority_intermediate, notify_authority_final, close_and_archive
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.dora_major_incident_reporting@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.dora_major_incident_reporting@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.dora_major_incident_reporting@v1'"
            )

WORKFLOW = PlaybookDoraMajorIncidentReportingV1Workflow
ACTIVITIES = (detect_and_classify, notify_authority_initial, notify_authority_intermediate, notify_authority_final, close_and_archive,)
RETRY_POLICIES = (DETECT_AND_CLASSIFY_RETRY_POLICY, NOTIFY_AUTHORITY_INITIAL_RETRY_POLICY, NOTIFY_AUTHORITY_INTERMEDIATE_RETRY_POLICY, NOTIFY_AUTHORITY_FINAL_RETRY_POLICY, CLOSE_AND_ARCHIVE_RETRY_POLICY,)
