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
async def schedule_management_review(governance_cycle: str, trigger: str) -> str:
    """SKELETON — convene the management-body cybersecurity review cycle per NIS2 Directive (EU) 2022/2555 Article 20(1): resolve the operator's documented governance-cadence catalogue (which management-body forum, which agenda slot, which meeting date) against __governance_cycle__ and record the scheduled review event as __review_id__. Read-only against the governance-cadence catalogue: no calendar entry is mutated here — the operator's governance workflow owns the calendar surface; this step records the resolved slot the review will occupy. On the ad-hoc trigger branch (no scheduled slot) __review_id__ stays empty and the downstream steps proceed against the ad-hoc marker rather than short-circuiting. TODO (CORE): governance-cadence-catalogue probe binding, ad-hoc-trigger propagation, forum-specific agenda-item shape.

    CACAO step_id: action--a2000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--a2000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a2000000-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a2000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'schedule_management_review', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'schedule_management_review'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--a2000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a2000000-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a2000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'schedule_management_review', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'schedule_management_review'})
        )
        from content.playbooks.nis2_art20_governance.primitives.cycle import resolve_governance_cycle
        __review_id__ = resolve_governance_cycle(governance_cycle=__governance_cycle__, trigger=__trigger__)

SCHEDULE_MANAGEMENT_REVIEW_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def present_risk_posture(governance_cycle: str, review_id: str, posture_snapshot_id: str, clauses: dict[str, object], open_exceptions: dict[str, object], training_completion: dict[str, object]) -> str:
    """SKELETON — present the current cybersecurity risk-management posture and NIS2 Article 21(2)(a)–(j) compliance status to the management body for the __governance_cycle__ cycle. Composes __posture_snapshot_id__ as a per-cycle governance view over the operator's evidence store: the current Article 21(2)(a)–(j) coverage buckets (present-and-current / present-but-stale / absent-with-declared-exception / absent-uncovered per sub-clause), the open exceptions inventory, and the material changes since the previous cycle. Read-only against the evidence store: this step does not write back into source records, it composes the per-cycle governance view keyed on the ten Article 21(2) sub-clause atoms. Distinct from playbook.nis2_self_assessment@v1 (the whole-Article-21 attestation-emission discipline on the operator's declared self-assessment cadence): present_risk_posture reads that whole-Article roll-up (and any per-clause playbook evidence records that post-date it) into the management-body-review governance surface. TODO (CORE): evidence-store probe binding, per-cycle snapshot-record shape, delta-since-previous-cycle carry.

    CACAO step_id: action--a2000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--a2000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a2000000-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a2000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'present_risk_posture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'present_risk_posture'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--a2000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a2000000-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a2000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'present_risk_posture', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'present_risk_posture'})
        )
        from content.playbooks.nis2_art20_governance.primitives.review import conduct_art20_review
        __posture_snapshot_id__ = conduct_art20_review(governance_cycle=__governance_cycle__, posture_snapshot_id=__posture_snapshot_id__, clauses=__clauses__, open_exceptions=__open_exceptions__, training_completion=__training_completion__)

PRESENT_RISK_POSTURE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def approve_risk_measures(governance_cycle: str, review_id: str, posture_snapshot_id: str, review_outcome: str, measures: dict[str, object], signatories: dict[str, object], approved_at_iso: str) -> str:
    """SKELETON — record the management-body approval of the cybersecurity risk-management measures presented in __posture_snapshot_id__, per NIS2 Directive (EU) 2022/2555 Article 20(1) (management-body approval of Article 21 measures) and Article 20(2) (cybersecurity training for management-body members). Composes __approval_record_id__ pinning which risk-management measures were approved, which were referred back with conditions, the associated exception acknowledgements, and the Article 20(2) training-completion attestation for management-body members (which members completed the declared training and when). The management-body approval discipline is documentary — the record captures the governance-decision outcome rather than mutating any operational control surface. On the referral branch (management body referred measures back rather than approving) __approval_record_id__ is emitted with the referral marker and the referral conditions, not dropped, so the audit trail carries the negative-outcome record. TODO (CORE): governance-decision-record shape, referral-condition carry, training-completion-attestation binding against the management-body member roster.

    CACAO step_id: action--a2000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--a2000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a2000000-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a2000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'approve_risk_measures', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'approve_risk_measures'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--a2000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a2000000-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a2000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'approve_risk_measures', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'approve_risk_measures'})
        )
        from content.playbooks.nis2_art20_governance.primitives.approval import record_management_approval
        __approval_record_id__ = record_management_approval(governance_cycle=__governance_cycle__, review_id=__review_id__, posture_snapshot_id=__posture_snapshot_id__, outcome=__review_outcome__, measures=__measures__, signatories=__signatories__, approved_at_iso=__approved_at_iso__)

APPROVE_RISK_MEASURES_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def log_governance_evidence(governance_cycle: str, trigger: str, review_id: str, posture_snapshot_id: str, approval_record_id: str, review_outcome: str, captured_at: str, workflow_id: str, execution_id: str, compile_target: str) -> str:
    """SKELETON — publish the dated governance-record evidence artifact to the operator's evidence store as an OCSF v1.3.0 API Activity (class_uid 6003) record. Record pins __governance_cycle__, __review_id__, __posture_snapshot_id__, __approval_record_id__, and __captured_at__ so the NIS2 Directive (EU) 2022/2555 Article 20(1) auditable-lifecycle obligation is discharged on every terminal path (including the ad-hoc-trigger branch and the referral branch, which are recorded with their respective markers rather than dropped). Records __evidence_id__. The evidence artifact is a plain JSON governance-record; no proprietary governance-tooling surface is assumed. TODO (CORE): evidence-record schema pin against a schemas/evidence/governance.schema.json envelope landing in the sibling CORE card, evidence-sink adapter binding, deterministic evidence_id derivation from SHA-256(governance_cycle|review_id|captured_at).

    CACAO step_id: action--a2000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--a2000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a2000000-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a2000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'log_governance_evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'log_governance_evidence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--a2000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a2000000-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--a2000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'log_governance_evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'log_governance_evidence'})
        )
        from content.playbooks.nis2_art20_governance.primitives.evidence import emit_governance_evidence
        __evidence_id__ = emit_governance_evidence(governance_cycle=__governance_cycle__, trigger=__trigger__, review_id=__review_id__, posture_snapshot_id=__posture_snapshot_id__, approval_record_id=__approval_record_id__, outcome=__review_outcome__, captured_at=__captured_at__, workflow_id=__workflow_id__, execution_id=__execution_id__, compile_target=__compile_target__)

LOG_GOVERNANCE_EVIDENCE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookNis2Art20GovernanceV1Workflow:
    """SKELETON — CACAO v2 scaffold for the operator-side NIS2 Directive (EU) 2022/2555, Article 20 management-body cybersecurity governance lifecycle. Article 20(1) requires the management bodies of essential and important entities to approve the cybersecurity risk-management measures taken by those entities to comply with Article 21, oversee their implementation, and be held liable for infringements; Article 20(2) requires the members of the management body to follow training and to encourage entities to offer similar training to all employees on a regular basis so they gain sufficient knowledge and skills to identify risks and assess cybersecurity risk-management practices and their impact on the services provided. This playbook is the governance-cadence discharge of both obligations: convene the management-body cybersecurity review cycle on the documented cadence, present the current Article 21(2)(a)–(j) risk-posture and compliance status to the management body, record the management approval of the cybersecurity risk-management measures (and the associated training completion for management-body members per Article 20(2)), and emit the dated governance-record evidence artifact (OCSF API Activity class_uid 6003) so the auditable-lifecycle obligation is closed on every cycle. Distinct from the sibling nis2_self_assessment playbook (the whole-Article-21 evidence roll-up on the operator's declared cadence) and from the F-CP-06 effectiveness loop (per-metric snapshots on the evaluation-window cadence): this is the management-body approval discipline the Article 20(1) obligation names on the governance-body axis, keyed on the four-step approval-cycle atoms rather than the per-clause evidence fan-out. SKELETON only: the per-step primitive bodies, per-target compiler emissions, and byte-parity goldens are owned by CORE sibling cards; the cookbook walkthrough is owned by an EXTEND sibling card. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--a2000000-0000-4000-8000-000000000001
    stable_id         : playbook.nis2_art20_governance@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--a2000000-0000-4000-8000-000000000001
    activities        : schedule_management_review, present_risk_posture, approve_risk_measures, log_governance_evidence
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.nis2_art20_governance@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a2000000-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.nis2_art20_governance@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--a2000000-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.nis2_art20_governance@v1'"
            )

WORKFLOW = PlaybookNis2Art20GovernanceV1Workflow
ACTIVITIES = (schedule_management_review, present_risk_posture, approve_risk_measures, log_governance_evidence,)
RETRY_POLICIES = (SCHEDULE_MANAGEMENT_REVIEW_RETRY_POLICY, PRESENT_RISK_POSTURE_RETRY_POLICY, APPROVE_RISK_MEASURES_RETRY_POLICY, LOG_GOVERNANCE_EVIDENCE_RETRY_POLICY,)
