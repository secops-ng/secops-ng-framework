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
async def schedule_assessment(training_window: str, training_scope: str) -> str:
    """Schedule the training-needs assessment against the in-scope programme surface: resolve the required awareness and role-based training tracks per cohort, identify residual gaps against the operator's declared training policy, and pin the per-cohort priority for this cycle. Emits __assessment_id__ as a per-cohort record. Read-only against the operator's HR / identity / policy surfaces; does not mutate roster or policy state.

    CACAO step_id: action--54000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--54000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'schedule assessment', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'schedule_assessment'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--54000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'schedule assessment', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'schedule_assessment'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--54000000-0000-4000-8000-000000000002'"
        )

SCHEDULE_ASSESSMENT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def design_content(assessment_id: str, training_scope: str) -> str:
    """Author or update the per-track training curriculum against the assessment artifact: learning objectives, module content references, source citations, and next review dates. Emits __curriculum_id__ as a per-track record. The curriculum is the programme-level content-authoring surface; individual per-cycle delivery lives downstream on this playbook and on the operational cyber_hygiene_training playbook.

    CACAO step_id: action--54000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--54000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'design content', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'design_content'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--54000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'design content', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'design_content'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--54000000-0000-4000-8000-000000000003'"
        )

DESIGN_CONTENT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def deliver_training(curriculum_id: str, training_scope: str) -> str:
    """Deliver the cycle's curriculum to the in-scope cohorts along the operator's declared training channel(s) (learning-management surface, live session, self-paced module). Emits __delivery_id__ as a per-cohort delivery record. The delivery step writes delivery-intent records to the training surface; the operator's LMS owns final scheduling and per-staff dispatch.

    CACAO step_id: action--54000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--54000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'deliver training', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'deliver_training'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--54000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'deliver training', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'deliver_training'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--54000000-0000-4000-8000-000000000004'"
        )

DELIVER_TRAINING_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def record_completion(delivery_id: str, training_window: str) -> str:
    """Read per-staff completion state from the operator's learning-management surface against the delivery artifact and roll up to per-cohort aggregate. Emits __completion_id__ as per-staff (staff id, track id, completion state, completed at, overdue-by-days) with per-cohort completion-rate. Read-only against the LMS; does not mark completion on the operator's behalf.

    CACAO step_id: action--54000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--54000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'record completion', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'record_completion'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--54000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'record completion', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'record_completion'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--54000000-0000-4000-8000-000000000005'"
        )

RECORD_COMPLETION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def report_gaps(completion_id: str, assessment_id: str) -> str:
    """Compose the residual-gap report for the cycle: missed-mandatory tracks, overdue role-based tracks, cohorts below the declared completion-rate target, and any uncovered regulatory training requirement the assessment surfaced but the curriculum did not close. Emits __gap_report_id__. The report is the programme-owner-facing summary of what did NOT close this cycle.

    CACAO step_id: action--54000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--54000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'report gaps', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'report_gaps'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--54000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'report gaps', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'report_gaps'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--54000000-0000-4000-8000-000000000006'"
        )

REPORT_GAPS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def review_cycle(assessment_id: str, curriculum_id: str, delivery_id: str, completion_id: str, gap_report_id: str, training_window: str) -> str:
    """Close the cycle with a dated cycle-review record referencing the assessment, curriculum, delivery, completion, and gap-report artifacts, plus programme-level recommendations feeding the next cycle's assessment (curriculum updates, cohort-scope changes, regulatory drivers). The cycle-review record is the audit-evident programme-governance artifact NIS2 Art. 21(2)(g) reviewers read against the operator's declared training policy.

    CACAO step_id: action--54000000-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--54000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'review cycle', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'review_cycle'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--54000000-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--54000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'review cycle', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'review_cycle'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--54000000-0000-4000-8000-000000000007'"
        )

REVIEW_CYCLE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookSecurityAwarenessTrainingV1Workflow:
    """SKELETON scaffold for the structured security-awareness training programme lifecycle required by NIS2 Art. 21(2)(g). The playbook operates the recurring training-programme cycle upstream of the reactive phishing and hygiene disciplines: schedule the training-needs assessment, design or update the training content against identified gaps, deliver the training to the in-scope staff cohorts, record per-staff completion, report the residual gap set to the training owner, and close the review cycle with a dated cycle-review artifact. This is the PROGRAMME layer of NIS2 Art. 21(2)(g) — the training-cycle governance surface — distinct from the operational per-cycle materialisation the already-shipped playbook.cyber_hygiene_training@v1 covers (roster inventory, cycle assignment, phishing-simulation dispatch, completion tracking, attestation, notify). The two playbooks are complementary siblings under the same clause: this one authors what training the operator's programme requires; cyber_hygiene_training discharges the individual per-cycle execution against that programme. SKELETON only — control bindings, telemetry emit shapes, per-target compile examples, and golden tests are owned by CORE / EXTEND siblings.

    CACAO playbook id : playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901
    stable_id         : playbook.security_awareness_training@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--54000000-0000-4000-8000-000000000001
    activities        : schedule_assessment, design_content, deliver_training, record_completion, report_gaps, review_cycle
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.security_awareness_training@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.security_awareness_training@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--9e4d5f60-7182-4b33-ae4f-05c6d7e8f901', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.security_awareness_training@v1'"
            )

WORKFLOW = PlaybookSecurityAwarenessTrainingV1Workflow
ACTIVITIES = (schedule_assessment, design_content, deliver_training, record_completion, report_gaps, review_cycle,)
RETRY_POLICIES = (SCHEDULE_ASSESSMENT_RETRY_POLICY, DESIGN_CONTENT_RETRY_POLICY, DELIVER_TRAINING_RETRY_POLICY, RECORD_COMPLETION_RETRY_POLICY, REPORT_GAPS_RETRY_POLICY, REVIEW_CYCLE_RETRY_POLICY,)
