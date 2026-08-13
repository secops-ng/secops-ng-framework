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
async def define_dort_scope(asset_register: dict[str, object], critical_functions: dict[str, object], testing_window: str, third_party_register: dict[str, object]) -> dict[str, object]:
    """The action body reads the operator's business-service register, ICT-asset register, and ICT third-party service-provider register to compose the DORT-scope catalogue for the current testing-programme window against DORA Art. 24 general-requirements-for-testing scope: the ICT-supported critical or important functions the operator has designated in scope, the supporting ICT assets pinned to each function, and the ICT third-party service providers whose services are in scope. Sets __dort_scope_catalogue__ to a durable identifier of the resolved scope so every downstream step reads against the same catalogue and scope drift is caught at the primitive boundary. Read-only against the operator's declared registers; the primitive does not itself designate functions as critical or important — that is the operator's governance surface upstream. SKELETON pins the topology, the ID, and the regulatory anchor refs; the deterministic per-register pull, function-to-asset-to-provider join, and coverage-review binding are owned by CORE-PRIM.

    CACAO step_id: action--55000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--55000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--55d0e1f2-3a4b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--55000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'define DORT scope', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'define_dort_scope'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--55000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--55d0e1f2-3a4b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--55000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'define DORT scope', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'define_dort_scope'})
        )
        from content.playbooks.dora_tlpt_programme.primitives.scope import define_dort_scope
        __dort_scope_catalogue__ = define_dort_scope(testing_window=__testing_window__, critical_functions=__critical_functions__, asset_register=__asset_register__, third_party_register=__third_party_register__)

DEFINE_DORT_SCOPE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def tlpt_trigger_and_planning_gate(authority_notification_ref: str, declared_cadence_months: int, dort_scope_catalogue: dict[str, object], entity_significance_tier: str, last_tlpt_completed_on: str, tester_posture: str, threat_intelligence_source: str, tlpt_identified: bool) -> dict[str, object]:
    """The action body evaluates whether threat-led penetration testing is mandatory for the operator in the current window against the criteria the JC Joint Guidelines on TLPT (JC 2022 03) name and the operator's declared __entity_significance_tier__ per DORA Art. 26(1). On the mandatory branch the primitive: (a) emits the competent-authority notification (the identifier of the notification adapter binding lives in the sibling CORE card), (b) records the declared programme cadence (per Art. 26(1) the mandatory TLPT cycle is at least every three years unless the competent authority prescribes otherwise), and (c) binds the operator's declared threat-intelligence source and internal-versus-external tester selection posture. On the not-mandatory branch the primitive still emits a dated decision record naming the criteria evaluated so the audit-evident chain is closed rather than silently short-circuiting the programme. Sets __tlpt_trigger_decision__. SKELETON pins the topology, the ID, and the regulatory anchor refs; the deterministic criteria evaluation and the competent-authority notification adapter are owned by CORE-PRIM.

    CACAO step_id: action--55000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--55000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--55d0e1f2-3a4b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--55000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'TLPT trigger and planning gate', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'tlpt_trigger_and_planning_gate'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--55000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--55d0e1f2-3a4b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--55000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'TLPT trigger and planning gate', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'tlpt_trigger_and_planning_gate'})
        )
        from content.playbooks.dora_tlpt_programme.primitives.trigger import evaluate_tlpt_trigger
        __tlpt_trigger_decision__ = evaluate_tlpt_trigger(dort_scope=__dort_scope_catalogue__, entity_significance_tier=__entity_significance_tier__, tlpt_identified=__tlpt_identified__, threat_intelligence_source=__threat_intelligence_source__, tester_posture=__tester_posture__, authority_notification_ref=__authority_notification_ref__, last_tlpt_completed_on=__last_tlpt_completed_on__, declared_cadence_months=__declared_cadence_months__)

TLPT_TRIGGER_AND_PLANNING_GATE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def red_team_scoping_approval(dort_scope_catalogue: dict[str, object], scoping_outcome: str, tester_certification_ref: str, tester_independence_attestation_ref: str, tester_ref: str, third_party_carve_outs: dict[str, object], tlpt_trigger_decision: dict[str, object]) -> dict[str, object]:
    """The action body packages the red-team scoping submission per DORA Art. 26(3): scope statement bound to __dort_scope_catalogue__, tester selection (internal or external) against the certification and independence criteria the JC RTS on ICT risk-management framework names (external testers must satisfy the reputation, expertise, technical-and-organisational-standards, and professional-indemnity-insurance criteria), the declared threat-intelligence source, and the operator's rules of engagement. The submission package is dispatched to the competent authority against the adapter binding declared under patterns.dora_tlpt_programme (owned by the sibling EXTEND card); the primitive records the competent-authority response (approved / deferred / rejected) into __red_team_scoping_id__ once the response is bound. On the deferred / rejected branches the primitive emits the response record and short-circuits the downstream engagement — the operator does not proceed with the red-team engagement without competent-authority approval on the scoping document. SKELETON pins the topology, the ID, and the regulatory anchor refs; the deterministic scoping-submission packaging and the approval-binding adapter are owned by CORE-PRIM and EXTEND respectively.

    CACAO step_id: action--55000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--55000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--55d0e1f2-3a4b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--55000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'red-team scoping approval', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'red_team_scoping_approval'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--55000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--55d0e1f2-3a4b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--55000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'red-team scoping approval', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'red_team_scoping_approval'})
        )
        from content.playbooks.dora_tlpt_programme.primitives.scoping import approve_red_team_scoping
        __red_team_scoping_id__ = approve_red_team_scoping(dort_scope=__dort_scope_catalogue__, tlpt_trigger=__tlpt_trigger_decision__, tester_ref=__tester_ref__, outcome=__scoping_outcome__, tester_certification_ref=__tester_certification_ref__, tester_independence_attestation_ref=__tester_independence_attestation_ref__, third_party_carve_outs=__third_party_carve_outs__)

RED_TEAM_SCOPING_APPROVAL_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def remediation_tracking(captured_at: str, dort_scope_catalogue: dict[str, object], engagement_findings: dict[str, object], execution_id: str, red_team_scoping_id: dict[str, object], severity_rubric: dict[str, object], workflow_id: str) -> dict[str, object]:
    """The action body composes the findings register from the red-team engagement bound to __red_team_scoping_id__: per-finding record with id, severity against the operator's declared severity rubric, affected critical or important function, affected ICT asset, evidence pointer into the operator's evidence store, and initial remediation timeline. Sets __findings_register_id__. The primitive then composes the dated competent-authority remediation attestation per DORA Art. 26(8): remediation-status roll-up per finding, aggregated closure rate, remaining-open backlog against the declared severity thresholds, and the attestation timestamp. The attestation record is published to the operator's evidence store; the artifact_id is SHA-256(workflow_id|execution_id|captured_at) so compile_target does not enter the identifier and the three reference compilers re-derive byte-identical bytes from the same primitive output. Sets __remediation_attestation_id__. The primitive is idempotent per (workflow_id, execution_id): re-running the remediation-tracking step against the same engagement produces the same artifact_id, updating the per-finding status roll-up in place rather than emitting a duplicate attestation. SKELETON pins the topology, the ID, and the regulatory anchor refs; the deterministic findings-register schema, severity-rubric binding, and attestation-emitter wiring are owned by CORE-PRIM and land alongside the byte-parity examples.

    CACAO step_id: action--55000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--55000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--55d0e1f2-3a4b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--55000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'remediation tracking', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'remediation_tracking'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--55000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--55d0e1f2-3a4b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.2.0', 'secops_ng.step.id': 'action--55000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'remediation tracking', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'remediation_tracking'})
        )
        from content.playbooks.dora_tlpt_programme.primitives.remediation import track_remediation
        __remediation_attestation_id__ = track_remediation(dort_scope=__dort_scope_catalogue__, red_team_scoping=__red_team_scoping_id__, findings=__engagement_findings__, severity_rubric=__severity_rubric__, workflow_id=__workflow_id__, execution_id=__execution_id__, captured_at=__captured_at__)

REMEDIATION_TRACKING_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookDoraTlptProgrammeV1Workflow:
    """SKELETON — CACAO v2 scaffold for the DORA Chapter IV digital operational resilience testing (DORT) programme a financial entity operates against its ICT risk-management framework. Composes the operator-side lifecycle of Article 24 (general requirements for the testing of digital operational resilience — scope, coverage, cadence, coverage-review) and Article 26 (advanced testing of ICT tools, systems and processes based on threat-led penetration testing, the operator-side TLPT lifecycle anchored on TIBER-EU as the implementation reference). Distinct from the dora_ict_risk_selfassess playbook (whole-Chapter II roll-up on the Art. 6(5) annual-review cadence) and from the operator-side sibling posture playbooks (crypto_posture_management, detection_engineering, etc. — the per-section producing surfaces the roll-up aggregates): this playbook is the Chapter IV testing-programme discipline, keyed on the four programme-lifecycle atoms the operator discharges on the mandatory-TLPT cadence prescribed by the competent authority against the operator's designated critical-or-important functions. The lifecycle chains four action steps: define_dort_scope (Art. 24 — identify the ICT-supported critical or important functions, the supporting ICT assets, and the third-party dependencies in scope for the testing programme; sets the operator's declared DORT scope catalogue for the window) → tlpt_trigger_and_planning_gate (Art. 26(1) — evaluate whether TLPT is mandatory for the operator in the current window against the criteria the competent authority names and the operator's tier-of-significance under the JC RTS; notify the competent authority; open the planning gate that carries the programme's declared scope, cadence, threat-intelligence source, and internal / external tester selection posture) → red_team_scoping_approval (Art. 26(3) — bind the red-team scoping submission to the operator's declared providers (internal / external, with the certification / independence criteria the competent authority requires), package the scoping document for competent-authority approval, and record the approval or deferral outcome) → remediation_tracking (Art. 26(8) — compose the findings register from the red-team engagement, bind each finding to a remediation timeline against the operator's declared severity rubric, produce the dated competent-authority attestation with the remediation-status roll-up, and publish the artifact to the operator's evidence store). SKELETON pins the topology, the compliance markers, and the mapping stubs; the sibling CORE card lands the deterministic per-step primitives (scope-catalogue read against the operator's business-service and ICT-asset registers, competent-authority notification adapter, red-team scoping-submission adapter, findings-register schema, remediation-attestation emitter, byte-parity examples). The sibling EXTEND card lands the cookbook walkthrough (TIBER-EU red-team choreography, threat-intelligence-source binding, purple-team lessons-learned loop into detection_engineering).

    CACAO playbook id : playbook--55d0e1f2-3a4b-4c5d-8e6f-1a2b3c4d5e6f
    stable_id         : playbook.dora_tlpt_programme@v1
    content_version   : 0.2.0
    maturity          : experimental
    workflow_start    : start--55000000-0000-4000-8000-000000000001
    activities        : define_dort_scope, tlpt_trigger_and_planning_gate, red_team_scoping_approval, remediation_tracking
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.dora_tlpt_programme@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--55d0e1f2-3a4b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.2.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.dora_tlpt_programme@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--55d0e1f2-3a4b-4c5d-8e6f-1a2b3c4d5e6f', 'secops_ng.playbook.version': '0.2.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.dora_tlpt_programme@v1'"
            )

WORKFLOW = PlaybookDoraTlptProgrammeV1Workflow
ACTIVITIES = (define_dort_scope, tlpt_trigger_and_planning_gate, red_team_scoping_approval, remediation_tracking,)
RETRY_POLICIES = (DEFINE_DORT_SCOPE_RETRY_POLICY, TLPT_TRIGGER_AND_PLANNING_GATE_RETRY_POLICY, RED_TEAM_SCOPING_APPROVAL_RETRY_POLICY, REMEDIATION_TRACKING_RETRY_POLICY,)
