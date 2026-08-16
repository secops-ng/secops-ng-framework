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
async def collect_criteria_atoms() -> str:
    """Read the Trust Services Criteria crosswalk under content/mappings/soc2/ into per-criterion atoms. The criteria set is data, not a constant in this playbook, so a criterion added to the crosswalk is scored on the next run without a content change here.

    CACAO step_id: action--b7c2e5a1-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--b7c2e5a1-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b7c2e5a1-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b7c2e5a1-0000-4000-8000-000000000002', 'secops_ng.step.name': 'collect criteria atoms', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'collect_criteria_atoms'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--b7c2e5a1-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b7c2e5a1-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b7c2e5a1-0000-4000-8000-000000000002', 'secops_ng.step.name': 'collect criteria atoms', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'collect_criteria_atoms'})
        )
        from content.playbooks.soc2_evidence_collector.primitives.criteria import collect_criteria_atoms
        __criteria_atoms__ = collect_criteria_atoms(crosswalk_entries=__crosswalk_entries__)

COLLECT_CRITERIA_ATOMS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def map_evidence_to_criteria(assessment_window: str, evidence_refs: dict[str, object], criteria_atoms: str) -> str:
    """Join the evidence references available for the window onto the criteria they support. An evidence reference naming a criterion the crosswalk does not carry is reported as unmatched rather than silently dropped.

    CACAO step_id: action--b7c2e5a1-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--b7c2e5a1-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b7c2e5a1-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b7c2e5a1-0000-4000-8000-000000000003', 'secops_ng.step.name': 'map evidence to criteria', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'map_evidence_to_criteria'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--b7c2e5a1-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b7c2e5a1-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b7c2e5a1-0000-4000-8000-000000000003', 'secops_ng.step.name': 'map evidence to criteria', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'map_evidence_to_criteria'})
        )
        from content.playbooks.soc2_evidence_collector.primitives.mapping import map_evidence_to_criteria
        __criteria_mapping__ = map_evidence_to_criteria(atoms=__criteria_atoms__, evidence_refs=__evidence_refs__)

MAP_EVIDENCE_TO_CRITERIA_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def score_per_criterion_coverage(criteria_atoms: str, criteria_mapping: str) -> str:
    """Score each criterion as covered, partially covered or uncovered, and roll the result up per Trust Services category. Coverage resting on a draft mapping is counted separately — a draft crosswalk entry is not audit-ready evidence.

    CACAO step_id: action--b7c2e5a1-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--b7c2e5a1-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b7c2e5a1-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b7c2e5a1-0000-4000-8000-000000000004', 'secops_ng.step.name': 'score per-criterion coverage', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'score_per_criterion_coverage'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--b7c2e5a1-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b7c2e5a1-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b7c2e5a1-0000-4000-8000-000000000004', 'secops_ng.step.name': 'score per-criterion coverage', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'score_per_criterion_coverage'})
        )
        from content.playbooks.soc2_evidence_collector.primitives.scoring import score_criterion_coverage
        __coverage_scoring__ = score_criterion_coverage(atoms=__criteria_atoms__, mapping=__criteria_mapping__)

SCORE_PER_CRITERION_COVERAGE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def report_readiness_attestation(assessment_window: str, criteria_atoms: str, criteria_mapping: str, coverage_scoring: str) -> str:
    """Emit one dated readiness attestation naming covered, partially covered and uncovered criteria, the draft-backed subset, and the owner. It is readiness input for an auditor, never an audit opinion.

    CACAO step_id: action--b7c2e5a1-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--b7c2e5a1-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b7c2e5a1-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b7c2e5a1-0000-4000-8000-000000000005', 'secops_ng.step.name': 'report readiness attestation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'report_readiness_attestation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--b7c2e5a1-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b7c2e5a1-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '1.0.0', 'secops_ng.step.id': 'action--b7c2e5a1-0000-4000-8000-000000000005', 'secops_ng.step.name': 'report readiness attestation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'report_readiness_attestation'})
        )
        from content.playbooks.soc2_evidence_collector.primitives.attestation import build_readiness_attestation
        __attestation_id__ = build_readiness_attestation(workflow_id=__workflow_id__, execution_id=__execution_id__, captured_at=__captured_at__, assessment_window=__assessment_window__, scoring=__coverage_scoring__, owner_role=__owner_role__)

REPORT_READINESS_ATTESTATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookSoc2EvidenceCollectorV1Workflow:
    """Aggregates the evidence the operator's other playbooks already emit into a dated SOC 2 readiness attestation. Reads the Trust Services Criteria crosswalk under content/mappings/soc2/, maps each available evidence reference onto the criteria it supports, scores per-criterion coverage, and reports one attestation naming what is covered, what is uncovered, and what rests on draft mappings. It collects no new telemetry and asserts no audit opinion — SOC 2 attestation is a licensed auditor's act, and this playbook produces readiness input, not a report.

    CACAO playbook id : playbook--b7c2e5a1-0000-4000-8000-000000000000
    stable_id         : playbook.soc2_evidence_collector@v1
    content_version   : 1.0.0
    maturity          : stable
    workflow_start    : start--b7c2e5a1-0000-4000-8000-000000000001
    activities        : collect_criteria_atoms, map_evidence_to_criteria, score_per_criterion_coverage, report_readiness_attestation
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.soc2_evidence_collector@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b7c2e5a1-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '1.0.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.soc2_evidence_collector@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--b7c2e5a1-0000-4000-8000-000000000000', 'secops_ng.playbook.version': '1.0.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.soc2_evidence_collector@v1'"
            )

WORKFLOW = PlaybookSoc2EvidenceCollectorV1Workflow
ACTIVITIES = (collect_criteria_atoms, map_evidence_to_criteria, score_per_criterion_coverage, report_readiness_attestation,)
RETRY_POLICIES = (COLLECT_CRITERIA_ATOMS_RETRY_POLICY, MAP_EVIDENCE_TO_CRITERIA_RETRY_POLICY, SCORE_PER_CRITERION_COVERAGE_RETRY_POLICY, REPORT_READINESS_ATTESTATION_RETRY_POLICY,)
