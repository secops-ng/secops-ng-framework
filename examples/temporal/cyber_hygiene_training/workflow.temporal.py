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
async def inventory_training_roster(training_window: str, training_scope: str) -> str:
    """Resolve the in-scope training roster from the operator's HR / identity source against __training_scope__: which staff cohorts are subject to mandatory awareness training, which staff hold roles that require role-based training, and which cohorts are enrolled in the phishing-simulation programme. Emits __roster_id__ as a per-staff record of (staff id, cohort, mandatory tracks assigned, role-based tracks assigned, joiner/leaver state). The inventory is read-only against the HR and identity surfaces; it does not modify roster assignments. Staff with no declared training requirement in the operator's policy are reported as policy gaps rather than completion gaps; the distinction is preserved so the attestation surfaces the policy-side and operations-side gaps separately.

    CACAO step_id: action--53000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--53000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'inventory training roster', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'inventory_training_roster'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--53000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'inventory training roster', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'inventory_training_roster'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--53000000-0000-4000-8000-000000000002'"
        )

INVENTORY_TRAINING_ROSTER_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def schedule_training_cycle(roster_id: str, training_window: str) -> str:
    """Schedule the per-cycle awareness and role-based training assignments for the roster emitted by inventory-training-roster against the declared training tracks and cadence. Emits __cycle_id__ as a per-cohort record of (cohort id, training track id, assigned at, due at, channel). The scheduling step writes assignment intents to the operator's learning-management surface; it does NOT push training content directly to staff. Tracks with no declared cadence in the operator's policy are reported as policy gaps rather than scheduling failures.

    CACAO step_id: action--53000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--53000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'schedule training cycle', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'schedule_training_cycle'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--53000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'schedule training cycle', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'schedule_training_cycle'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--53000000-0000-4000-8000-000000000003'"
        )

SCHEDULE_TRAINING_CYCLE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def run_phishing_simulation(cycle_id: str, training_scope: str) -> str:
    """Dispatch the cycle's phishing-simulation exercise to the cohorts enrolled in the simulation programme using a documented simulation template. Emits __simulation_id__ as a per-recipient record of (recipient id, template id, delivered at, clicked, reported, time-to-report). The simulation is a clearly-labelled exercise governed by the operator's awareness programme; it does NOT trigger downstream incident response, does NOT inject content into production mailflow controls, and does NOT exfiltrate credentials. Cohorts with no declared simulation cadence are reported as policy gaps rather than simulation failures.

    CACAO step_id: action--53000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--53000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'run phishing simulation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'run_phishing_simulation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--53000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'run phishing simulation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'run_phishing_simulation'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--53000000-0000-4000-8000-000000000004'"
        )

RUN_PHISHING_SIMULATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def track_completion(cycle_id: str, simulation_id: str) -> str:
    """Read completion state for the cycle's training assignments from the operator's learning-management surface and aggregate the phishing-simulation results from __simulation_id__. Emits __completion_id__ as a per-staff record of (staff id, track id, completion state, completed at, overdue-by-days) and per-cohort aggregate of completion-rate, click-rate, and report-rate against the declared targets. The tracking step is read-only against the LMS; it does NOT mark training as complete on the operator's behalf. Tracks past their due date are reported as overdue-completion gaps with the overdue-by-days delta preserved so the attestation surfaces the magnitude of the gap rather than a boolean.

    CACAO step_id: action--53000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--53000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'track completion', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'track_completion'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--53000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'track completion', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'track_completion'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--53000000-0000-4000-8000-000000000005'"
        )

TRACK_COMPLETION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def evidence_capture(roster_id: str, cycle_id: str, simulation_id: str, completion_id: str, training_window: str) -> str:
    """Compose and publish the dated cyber-hygiene and security-training posture attestation to the operator's evidence store. The record carries the training-roster snapshot, the cycle assignments, the simulation results, the completion tracking, the training window, and a top-level gap summary (missed-mandatory-training, overdue-role-based-training, simulation-click counts). This is the audit-evident artifact NIS2 Art.21(2)(g) reviewers read; missing or stale attestations are the failure mode the metrics surface. The attestation is always emitted, including the policy-gap branch (which records missing-policy conditions rather than skipping the attestation).

    CACAO step_id: action--53000000-0000-4000-8000-000000000006
    """
    with _TRACER.start_as_current_span(
        name='activity.action--53000000-0000-4000-8000-000000000006',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'evidence capture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evidence_capture'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--53000000-0000-4000-8000-000000000006', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000006', 'secops_ng.step.name': 'evidence capture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'evidence_capture'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--53000000-0000-4000-8000-000000000006'"
        )

EVIDENCE_CAPTURE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def notify_gaps(attestation_id: str, training_scope: str) -> None:
    """Deliver the attestation reference and the gap summary to the training owner along the operator's pre-bound channel (ticketing system, chat thread, email). Tracked as a distinct step so the evidence-capture artifact and the human-acknowledgement record can be audited independently; an attestation written but never delivered to the owner is itself a posture gap.

    CACAO step_id: action--53000000-0000-4000-8000-000000000007
    """
    with _TRACER.start_as_current_span(
        name='activity.action--53000000-0000-4000-8000-000000000007',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify gaps', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_gaps'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--53000000-0000-4000-8000-000000000007', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--53000000-0000-4000-8000-000000000007', 'secops_ng.step.name': 'notify gaps', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'notify_gaps'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--53000000-0000-4000-8000-000000000007'"
        )

NOTIFY_GAPS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookCyberHygieneTrainingV1Workflow:
    """Operate the basic cyber-hygiene and staff cybersecurity-training posture surface required by NIS2 Art.21(2)(g): inventory the in-scope training roster against the declared training scope, schedule the per-cycle awareness and role-based training assignments, run the cycle's phishing-simulation exercise, track completion of mandatory training and report-rate on the simulation, capture a dated training-attestation artifact, and notify the training owner of any gaps. The playbook is the operationalisation of declared training and hygiene policy; it does not author the policy itself. SKELETON only — control bindings (control.training_attestation@v1, control.phishing_simulation@v1) are pinned but detection bindings (missed-training, simulation-click upstream rule ids), golden tests, and per-target compiler emissions are owned by CORE / EXTEND siblings. The metric_refs pin the catalogue entries kpi.training_completion_rate@v1 and kpi.phishing_sim_click_rate@v1 that already ship under content/mappings/nis2/article-21-2-g.yaml; the CORE/EXTEND siblings add the per-cohort training-overdue KPI and re-pin step-level refs against it. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9
    stable_id         : playbook.cyber_hygiene_training@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--53000000-0000-4000-8000-000000000001
    activities        : inventory_training_roster, schedule_training_cycle, run_phishing_simulation, track_completion, evidence_capture, notify_gaps
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.cyber_hygiene_training@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.cyber_hygiene_training@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--8c3d4e5f-6071-4a22-9d3e-f405b6c7d8e9', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.cyber_hygiene_training@v1'"
            )

WORKFLOW = PlaybookCyberHygieneTrainingV1Workflow
ACTIVITIES = (inventory_training_roster, schedule_training_cycle, run_phishing_simulation, track_completion, evidence_capture, notify_gaps,)
RETRY_POLICIES = (INVENTORY_TRAINING_ROSTER_RETRY_POLICY, SCHEDULE_TRAINING_CYCLE_RETRY_POLICY, RUN_PHISHING_SIMULATION_RETRY_POLICY, TRACK_COMPLETION_RETRY_POLICY, EVIDENCE_CAPTURE_RETRY_POLICY, NOTIFY_GAPS_RETRY_POLICY,)
