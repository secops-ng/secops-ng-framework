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
async def collect_section_evidence(assessment_window: str) -> dict[str, object]:
    """TODO (CORE): per-section evidence-collection primitive. The action body reads the operator's evidence store for the current self-assessment window and pulls every evidence record whose producing playbook is one of the playbooks the five DORA Chapter II ICT risk management section atoms currently anchor against (see content/playbooks/dora_ict_risk_selfassess/mappings.yaml). Sets __section_atoms__ to the fixed five-atom set dora:art-6-framework, dora:art-7-systems-protocols-tools, dora:art-8-identification, dora:art-10-detection, dora:art-11-response-recovery and __evidence_set_id__ to the durable identifier of the per-section evidence set for the window. Read-only against the evidence store: the collection step does not write back into the source records, it composes a per-window view keyed on the five section atoms. SKELETON pins the topology + ID + regulatory anchor refs; the deterministic per-source pull, normalisation, and section-attribution carry are owned by CORE-PRIM. Detection bindings for collection-side failures (evidence-store endpoint unreachable, partial pull inside the window, missing producing-playbook attribution on a record) are owned by CORE-FANOUT cards once upstream rule ids are selected.

    CACAO step_id: action--92000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--92000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--92a2b3c4-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--92000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'collect section evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'collect_section_evidence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--92000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--92a2b3c4-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--92000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'collect section evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'collect_section_evidence'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--92000000-0000-4000-8000-000000000002'"
        )

COLLECT_SECTION_EVIDENCE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def map_evidence_to_sections(assessment_window: str, section_atoms: str, evidence_set_id: str) -> str:
    """TODO (CORE): per-record evidence-to-section mapping primitive. The action body binds each evidence record in __evidence_set_id__ to (i) the Chapter II ICT risk management section atom it discharges (one of dora:art-6-framework, dora:art-7-systems-protocols-tools, dora:art-8-identification, dora:art-10-detection, dora:art-11-response-recovery), (ii) the playbook slug that produced it, and (iii) the SecOps-NG content-model overlay refs (control_refs, telemetry_refs, metric_refs) that carry across from the producing playbook, using the outbound overlay declared at content/playbooks/<slug>/mappings.yaml as the join key. Sets __section_mapping__. The mapping is best-effort; evidence records that do not bind to a documented section atom are recorded as unbound and flagged on the report rather than dropped so the audit trail carries the gap explicitly. Empty per-section sub-sets are emitted explicitly (a section with no evidence in the window is still enumerated) so the downstream scoring records absent-uncovered rather than silently dropping the section. SKELETON pins the topology + ID + control / telemetry refs; the deterministic mapping-and-normalisation is owned by CORE-PRIM.

    CACAO step_id: action--92000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--92000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--92a2b3c4-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--92000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'map evidence to sections', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'map_evidence_to_sections'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--92000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--92a2b3c4-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--92000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'map evidence to sections', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'map_evidence_to_sections'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--92000000-0000-4000-8000-000000000003'"
        )

MAP_EVIDENCE_TO_SECTIONS_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def score_per_section_coverage(section_atoms: str, section_mapping: str) -> str:
    """TODO (CORE): per-section coverage-scoring primitive. The action body scores each of the five Chapter II ICT risk management section atoms in __section_mapping__ against the operator's documented coverage rubric: present-and-current (at least one evidence record in the window whose captured_at is inside the operator's declared freshness threshold for the section), present-but-stale (evidence records exist but the freshest is past the declared freshness threshold), absent-with-declared-exception (no evidence records in the window but the operator maintains a documented, dated exception under the Art. 6 ICT risk-management framework naming the compensating measure), or absent-uncovered (no evidence records in the window and no declared exception — the gap the self-assessment surfaces). Per-section internal consistency is enforced at the primitive boundary so an inconsistent scoring (e.g. present-and-current with an empty evidence sub-set) fails loud here rather than at the report boundary downstream. The scoring is best-effort and time-boxed; if scoring cannot be completed within the documented self-assessment deadline (so the operator is not held by a perfect-scoring stall while the Art. 6(5) annual-review window slips), the primitive is invoked with deadline_missed=true and emits the sentinel per-section bucket ['unscored']; the downstream report step records that marker while still treating the per-section bucket as absent-uncovered for the whole-Chapter roll-up. Sets __section_scoring__. SKELETON pins the topology + ID + control / telemetry / metric refs; the deterministic scoring-rubric binding is owned by CORE-PRIM.

    CACAO step_id: action--92000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--92000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--92a2b3c4-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--92000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'score per-section coverage', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'score_per_section_coverage'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--92000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--92a2b3c4-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--92000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'score per-section coverage', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'score_per_section_coverage'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--92000000-0000-4000-8000-000000000004'"
        )

SCORE_PER_SECTION_COVERAGE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def report_attestation(assessment_window: str, section_atoms: str, section_mapping: str, section_scoring: str) -> str:
    """TODO (CORE): dated attestation-emission primitive. The action body composes the JSON-native DORA Chapter II ICT risk management self-assessment attestation record shaped against a schemas/evidence/dora-ict-risk-selfassess.schema.json (stream: attestation) landing in the sibling CORE card, and pins the artifact_id as SHA-256(workflow_id|execution_id|captured_at). compile_target is intentionally NOT part of the id so the three reference compilers re-derive byte-identical bytes from the same primitive output (the byte-parity contract the F-WF-DORA-SELFASSESS CORE-FANOUT siblings assert against). The record carries the assessment window, the five section atoms with their per-section scoring buckets, the unbound-evidence flag (if any), the whole-Chapter roll-up verdict (all-present-and-current / mixed-with-declared-exceptions / partial-coverage-with-gaps / uncovered), and the dated attestation timestamp. This is the audit-evident artifact DORA supervisory-authority reviewers read against the Chapter II ICT risk management surface; missing or stale attestation is the failure mode the operator-side Art. 6(5) annual-review cadence surfaces. The primitive only produces the JSON-native record; the durable emitter wiring (artifact-path, content-addressed filename, atomic write, notification of the operator's accountability owner) is owned by the per-target compilers and lands with the CORE-FANOUT sibling cards. Sets __attestation_id__.

    CACAO step_id: action--92000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--92000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--92a2b3c4-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--92000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'report attestation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'report_attestation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--92000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--92a2b3c4-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--92000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'report attestation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'report_attestation'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--92000000-0000-4000-8000-000000000005'"
        )

REPORT_ATTESTATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookDoraIctRiskSelfassessV1Workflow:
    """SKELETON — CACAO v2 scaffold for the DORA Chapter II ICT risk management framework operator-side self-assessment report. Aggregates the per-section evidence the five DORA ICT risk management sections (Art. 6 ICT risk-management framework, Art. 7 ICT systems / protocols / tools, Art. 8 identification, Art. 10 detection, Art. 11 response and recovery) produce across the operator's shipped playbook set into a single dated attestation artifact so a financial entity can demonstrate coverage of the whole Chapter II ICT risk management surface in one coherent output rather than as five disjoint per-section reads. Distinct from the per-section playbooks that discharge each obligation on its own axis (infra_posture_management, on_call_rotation for Art. 6; crypto_posture_management for Art. 7; asset_management, supply_chain_security for Art. 8; detection_engineering, alert_triage for Art. 10; incident_management, backup_recovery, ransomware_containment for Art. 11) and from the F-CP-06 effectiveness loop (which emits per-metric snapshots on an evaluation-window cadence): this is the whole-Chapter roll-up an operator produces on the Art. 6(5) annual-review cadence they document, keyed on the five ICT risk management section atoms rather than the per-playbook fan-out. The lifecycle chains four steps: collect_section_evidence against the operator's evidence store for each Chapter II ICT risk management section, keyed on the inbound mapping atoms (dora:art-6-framework, dora:art-7-systems-protocols-tools, dora:art-8-identification, dora:art-10-detection, dora:art-11-response-recovery) → map_evidence_to_sections under the SecOps-NG content-model overlay so each collected evidence record is bound to the section it discharges plus the playbook slug that produced it → score_per_section_coverage against the operator's documented coverage rubric (present-and-current / present-but-stale / absent-with-declared-exception / absent-uncovered) → report_attestation as a dated JSON-native attestation record published to the operator's evidence store. SKELETON pins the topology, the five-atom set, and the OSCAL / D3FEND anchors; the per-step deterministic primitives and the byte-parity compile artifacts land with the CORE-FANOUT sibling cards under examples/{n8n,temporal,langgraph}/dora_ict_risk_selfassess/.

    CACAO playbook id : playbook--92a2b3c4-0000-4000-8000-000000000001
    stable_id         : playbook.dora_ict_risk_selfassess@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--92000000-0000-4000-8000-000000000001
    activities        : collect_section_evidence, map_evidence_to_sections, score_per_section_coverage, report_attestation
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.dora_ict_risk_selfassess@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--92a2b3c4-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.dora_ict_risk_selfassess@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--92a2b3c4-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.dora_ict_risk_selfassess@v1'"
            )

WORKFLOW = PlaybookDoraIctRiskSelfassessV1Workflow
ACTIVITIES = (collect_section_evidence, map_evidence_to_sections, score_per_section_coverage, report_attestation,)
RETRY_POLICIES = (COLLECT_SECTION_EVIDENCE_RETRY_POLICY, MAP_EVIDENCE_TO_SECTIONS_RETRY_POLICY, SCORE_PER_SECTION_COVERAGE_RETRY_POLICY, REPORT_ATTESTATION_RETRY_POLICY,)
