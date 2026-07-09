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
async def detect_and_classify(incident_id: str, reporting_window: str) -> str:
    """TODO (CORE): Art. 18 classification-decision primitive. The action body reads the incident-register entry bound to __incident_id__ and evaluates whether the incident meets the major-ICT-related-incident threshold against the criteria the Commission Delegated Regulation (EU) 2024/1772 RTS names (seven primary criteria — clients affected, reputational impact, data-loss impact, service duration, geographical spread, economic impact, criticality of services affected — plus the materiality thresholds and the Art. 18(2) recurring-incident rule). Sets __classification_decision_id__ to a durable identifier of the classification record. On the not-major branch the primitive emits a dated decision record naming the criteria evaluated and short-circuits the downstream notification chain; on the major branch it opens the reporting window and hands off to notify-authority-initial. DORA Art. 19 anchor: this step is the entry gate to Art. 19's three-milestone reporting cycle, per Art. 19(1) which conditions the reporting obligation on the Art. 18(1) classification outcome. SKELETON pins the topology, the ID, and the regulatory anchor refs; the deterministic per-criterion evaluation is owned by CORE-PRIM and reuses the existing content.dora_major_classifier@v1 primitive.

    CACAO step_id: action--71000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--71000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect and classify', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_and_classify'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--71000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'detect and classify', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'detect_and_classify'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--71000000-0000-4000-8000-000000000002'"
        )

DETECT_AND_CLASSIFY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_authority_initial(incident_id: str, classification_decision_id: str) -> str:
    """TODO (CORE): initial-notification submission primitive per DORA Art. 19(4)(a). The action body packages the initial notification against the Commission Implementing Regulation (EU) 2024/2956 ITS content shape (initial-notification template): incident identifier, classification-decision reference, awareness timestamp, classification timestamp, affected critical or important functions, impact assessment at the initial stage, and where available a first-cut indicators-of-compromise block. The submission is dispatched to the competent authority (ESA sectoral supervisor / NCA per the operator's designated authority chain) against the adapter binding declared under patterns.dora_major_incident_reporting (owned by the sibling EXTEND card). The step MUST fire as soon as possible and within 4 hours of classification as major, and no later than 24 hours from awareness of the incident. Sets __initial_notification_id__; populated with the authority acknowledgement reference once the response is bound. DORA Art. 19 anchor: Art. 19(4)(a) initial-notification milestone.

    CACAO step_id: action--71000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--71000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'notify authority initial', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_authority_initial'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--71000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'notify authority initial', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_authority_initial'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--71000000-0000-4000-8000-000000000003'"
        )

NOTIFY_AUTHORITY_INITIAL_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_authority_intermediate(incident_id: str, initial_notification_id: str) -> str:
    """TODO (CORE): intermediate-report submission primitive per DORA Art. 19(4)(b). The action body packages the intermediate report against the ITS content shape (intermediate-report template): updated timestamps, refreshed affected-functions and affected-clients figures, indicators of compromise, mitigation actions in flight, and any preliminary root-cause hypothesis. The step MUST fire within 72 hours of classification of the incident as major, or earlier if regular activities have recovered in the interim. Sets __intermediate_report_id__; populated with the authority acknowledgement reference once the response is bound. The primitive reads the notification-adapter binding declared under patterns.dora_major_incident_reporting so the submission channel is consistent across the three milestones on the same reporting-cycle window. DORA Art. 19 anchor: Art. 19(4)(b) intermediate-report milestone.

    CACAO step_id: action--71000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--71000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'notify authority intermediate', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_authority_intermediate'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--71000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'notify authority intermediate', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_authority_intermediate'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--71000000-0000-4000-8000-000000000004'"
        )

NOTIFY_AUTHORITY_INTERMEDIATE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_authority_final(incident_id: str, intermediate_report_id: str) -> str:
    """TODO (CORE): final-report submission primitive per DORA Art. 19(4)(c). The action body packages the final report against the ITS content shape (final-report template): full root-cause analysis, final impact figures on the affected critical or important functions and clients, completed remediation actions, lessons-learned narrative, action plan for the residual and structural gaps, and the operator's residual-risk statement. The step MUST fire no later than one month after the submission of the intermediate report. Sets __final_report_id__; populated with the authority acknowledgement reference once the response is bound. Consumes __intermediate_report_id__ to carry the reporting-cycle chain forward and to guarantee the ITS timeline field ordering is coherent across the three milestones. DORA Art. 19 anchor: Art. 19(4)(c) final-report milestone.

    CACAO step_id: action--71000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--71000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'notify authority final', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_authority_final'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--71000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'notify authority final', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_authority_final'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--71000000-0000-4000-8000-000000000005'"
        )

NOTIFY_AUTHORITY_FINAL_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def close_and_archive(incident_id: str, classification_decision_id: str, initial_notification_id: str, intermediate_report_id: str, final_report_id: str) -> str:
    """TODO (CORE): cycle-archival primitive. The action body composes the dated cycle-archival record referencing __classification_decision_id__, the three submission artifacts (__initial_notification_id__, __intermediate_report_id__, __final_report_id__), the authority acknowledgement references, and any cross-regime notification-chain outputs (the NIS2 Art. 23 notification submitted in parallel where the operator is also in scope of NIS2 as an essential or important entity; the GDPR Art. 33 personal-data-breach notification where the incident involves personal data; the GDPR Art. 34 data-subject communication where the high-risk threshold is met). The archival record is published to the operator's evidence store; the artifact_id is SHA-256(workflow_id|execution_id|captured_at) so compile_target does not enter the identifier and the three reference compilers re-derive byte-identical bytes from the same primitive output. Sets __cycle_archive_id__. Always emitted so the audit-evident chain is closed even on the not-major branch. DORA Art. 19 anchor: Art. 19(3) which requires the operator to keep the reporting chain evidence-bound across the three milestones.

    CACAO step_id: action--71000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--71000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'close and archive', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'close_and_archive'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--71000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--71000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'close and archive', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'close_and_archive'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--71000000-0000-4000-8000-000000000006'"
        )

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
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--71000000-0000-4000-8000-000000000001
    activities        : detect_and_classify, notify_authority_initial, notify_authority_intermediate, notify_authority_final, close_and_archive
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.dora_major_incident_reporting@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.dora_major_incident_reporting@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--7a1b4c9d-2e3f-4a5b-8c6d-9e0f1a2b3c4d', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.dora_major_incident_reporting@v1'"
            )

WORKFLOW = PlaybookDoraMajorIncidentReportingV1Workflow
ACTIVITIES = (detect_and_classify, notify_authority_initial, notify_authority_intermediate, notify_authority_final, close_and_archive,)
RETRY_POLICIES = (DETECT_AND_CLASSIFY_RETRY_POLICY, NOTIFY_AUTHORITY_INITIAL_RETRY_POLICY, NOTIFY_AUTHORITY_INTERMEDIATE_RETRY_POLICY, NOTIFY_AUTHORITY_FINAL_RETRY_POLICY, CLOSE_AND_ARCHIVE_RETRY_POLICY,)
