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
async def collect_clause_evidence(assessment_window: str) -> dict[str, object]:
    """TODO (CORE): per-clause evidence-collection primitive. The action body reads the operator's evidence store for the current self-assessment window and pulls every evidence record whose producing playbook is one of the twenty-two playbooks the ten Art. 21(2)(a–j) sub-clauses currently anchor against (see content/playbooks/nis2_self_assessment/mappings.yaml). Sets __clause_atoms__ to the fixed ten-atom set nis2:art-21-2-a through nis2:art-21-2-j and __evidence_set_id__ to the durable identifier of the per-clause evidence set for the window. Read-only against the evidence store: the collection step does not write back into the source records, it composes a per-window view keyed on the ten sub-clause atoms. SKELETON pins the topology + ID + regulatory anchor refs; the deterministic per-source pull, normalisation, and sub-clause-attribution carry are owned by CORE-PRIM. Detection bindings for collection-side failures (evidence-store endpoint unreachable, partial pull inside the window, missing producing-playbook attribution on a record) are owned by CORE-FANOUT cards once upstream rule ids are selected.

    CACAO step_id: action--91000000-0000-4000-8000-000000000002
    """
    with _TRACER.start_as_current_span(
        name='activity.action--91000000-0000-4000-8000-000000000002',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--91a2b3c4-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--91000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'collect clause evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'collect_clause_evidence'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--91000000-0000-4000-8000-000000000002', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--91a2b3c4-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--91000000-0000-4000-8000-000000000002', 'secops_ng.step.name': 'collect clause evidence', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'collect_clause_evidence'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--91000000-0000-4000-8000-000000000002'"
        )

COLLECT_CLAUSE_EVIDENCE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def map_evidence_to_clauses(assessment_window: str, clause_atoms: str, evidence_set_id: str) -> str:
    """TODO (CORE): per-record evidence-to-clause mapping primitive. The action body binds each evidence record in __evidence_set_id__ to (i) the Art. 21(2) sub-clause atom it discharges (one of nis2:art-21-2-a through nis2:art-21-2-j), (ii) the playbook slug that produced it, and (iii) the SecOps-NG content-model overlay refs (control_refs, telemetry_refs, metric_refs) that carry across from the producing playbook, using the outbound overlay declared at content/playbooks/<slug>/mappings.yaml as the join key. Sets __clause_mapping__. The mapping is best-effort; evidence records that do not bind to a documented sub-clause atom are recorded as unbound and flagged on the report rather than dropped so the audit trail carries the gap explicitly. Empty per-clause sub-sets are emitted explicitly (a clause with no evidence in the window is still enumerated) so the downstream scoring records absent-uncovered rather than silently dropping the clause. SKELETON pins the topology + ID + control / telemetry refs; the deterministic mapping-and-normalisation is owned by CORE-PRIM.

    CACAO step_id: action--91000000-0000-4000-8000-000000000003
    """
    with _TRACER.start_as_current_span(
        name='activity.action--91000000-0000-4000-8000-000000000003',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--91a2b3c4-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--91000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'map evidence to clauses', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'map_evidence_to_clauses'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--91000000-0000-4000-8000-000000000003', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--91a2b3c4-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--91000000-0000-4000-8000-000000000003', 'secops_ng.step.name': 'map evidence to clauses', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'map_evidence_to_clauses'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--91000000-0000-4000-8000-000000000003'"
        )

MAP_EVIDENCE_TO_CLAUSES_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def score_per_clause_coverage(clause_atoms: str, clause_mapping: str) -> str:
    """TODO (CORE): per-clause coverage-scoring primitive. The action body scores each of the ten Art. 21(2)(a–j) sub-clauses in __clause_mapping__ against the operator's documented coverage rubric: present-and-current (at least one evidence record in the window whose captured_at is inside the operator's declared freshness threshold for the clause), present-but-stale (evidence records exist but the freshest is past the declared freshness threshold), absent-with-declared-exception (no evidence records in the window but the operator maintains a documented, dated exception under their Art. 21(2)(a) risk-analysis policy naming the compensating measure), or absent-uncovered (no evidence records in the window and no declared exception — the gap the self-assessment surfaces). Per-clause internal consistency is enforced at the primitive boundary so an inconsistent scoring (e.g. present-and-current with an empty evidence sub-set) fails loud here rather than at the report boundary downstream. The scoring is best-effort and time-boxed; if scoring cannot be completed within the documented self-assessment deadline (so the operator is not held by a perfect-scoring stall while the attestation window slips), the primitive is invoked with deadline_missed=true and emits the sentinel per-clause bucket ['unscored']; the downstream report step records that marker while still treating the per-clause bucket as absent-uncovered for the whole-Article roll-up. Sets __clause_scoring__. SKELETON pins the topology + ID + control / telemetry / metric refs; the deterministic scoring-rubric binding is owned by CORE-PRIM.

    CACAO step_id: action--91000000-0000-4000-8000-000000000004
    """
    with _TRACER.start_as_current_span(
        name='activity.action--91000000-0000-4000-8000-000000000004',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--91a2b3c4-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--91000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'score per-clause coverage', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'score_per_clause_coverage'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--91000000-0000-4000-8000-000000000004', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--91a2b3c4-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--91000000-0000-4000-8000-000000000004', 'secops_ng.step.name': 'score per-clause coverage', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'score_per_clause_coverage'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--91000000-0000-4000-8000-000000000004'"
        )

SCORE_PER_CLAUSE_COVERAGE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@activity.defn
async def report_attestation(assessment_window: str, clause_atoms: str, clause_mapping: str, clause_scoring: str) -> str:
    """TODO (CORE): dated attestation-emission primitive. The action body composes the JSON-native NIS2 Art. 21 self-assessment attestation record shaped against a schemas/evidence/nis2-self-assessment.schema.json (stream: attestation) landing in the sibling CORE card, and pins the artifact_id as SHA-256(workflow_id|execution_id|captured_at). compile_target is intentionally NOT part of the id so the three reference compilers re-derive byte-identical bytes from the same primitive output (the byte-parity contract the F-WF-NIS2-SELF-ASSESS CORE-FANOUT siblings assert against). The record carries the assessment window, the ten sub-clause atoms with their per-clause scoring buckets, the unbound-evidence flag (if any), the whole-Article roll-up verdict (all-present-and-current / mixed-with-declared-exceptions / partial-coverage-with-gaps / uncovered), and the dated attestation timestamp. This is the audit-evident artifact NIS2 supervisory-authority reviewers read against the whole Article 21 control surface; missing or stale attestation is the failure mode the operator-side self-assessment cadence surfaces. The primitive only produces the JSON-native record; the durable emitter wiring (artifact-path, content-addressed filename, atomic write, notification of the operator's accountability owner) is owned by the per-target compilers and lands with the CORE-FANOUT sibling cards. Sets __attestation_id__.

    CACAO step_id: action--91000000-0000-4000-8000-000000000005
    """
    with _TRACER.start_as_current_span(
        name='activity.action--91000000-0000-4000-8000-000000000005',
        attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--91a2b3c4-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--91000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'report attestation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'report_attestation'},
    ):
        AuditTrail.current().append(
            AuditRecord(span_name='activity.action--91000000-0000-4000-8000-000000000005', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--91a2b3c4-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0', 'secops_ng.step.id': 'action--91000000-0000-4000-8000-000000000005', 'secops_ng.step.name': 'report attestation', 'secops_ng.step.type': 'action', 'secops_ng.tool.name': 'report_attestation'})
        )
        raise NotImplementedError(
            f"CACAO action stub not implemented: step_id='action--91000000-0000-4000-8000-000000000005'"
        )

REPORT_ATTESTATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

@workflow.defn
class PlaybookNis2SelfAssessmentV1Workflow:
    """SKELETON — CACAO v2 scaffold for the NIS2 Article 21(2) operator-side self-assessment report. Aggregates the per-clause evidence the ten Art. 21(2)(a–j) obligations produce across the operator's shipped playbook set into a single dated attestation artifact so an operator can demonstrate coverage of the whole Article 21 control surface in one coherent output rather than as ten disjoint per-clause reads. Distinct from the per-clause playbooks that discharge each obligation on its own axis (infra_posture_management for (a); alert_triage / phishing_triage / identity_compromise / ransomware_containment / data_exfil for (b); backup_recovery for (c); threat_intel_ingest / contractual_obligations_tracker / supply_chain_security for (d); vuln_intake / cloud_misconfiguration / patch_management / codebase_vuln_management for (e); detection_engineering for (f); phishing_triage / cyber_hygiene_training for (g); crypto_posture_management for (h); identity_compromise / cloud_misconfiguration / iam_auditor / onboarding_offboarding_tracker / asset_management for (i); mfa_secured_comms for (j)) and from the F-CP-06 effectiveness loop (which emits per-metric snapshots on an evaluation-window cadence): this is the whole-Article roll-up an operator produces on the self-assessment cadence they document, keyed on the ten sub-clause atoms rather than the per-playbook fan-out. The lifecycle chains four steps: collect_clause_evidence against the operator's evidence store for each Art. 21(2) sub-clause, keyed on the inbound mapping atoms (nis2:art-21-2-a through nis2:art-21-2-j) → map_evidence_to_clauses under the SecOps-NG content-model overlay so each collected evidence record is bound to the sub-clause it discharges plus the playbook slug that produced it → score_per_clause_coverage against the operator's documented coverage rubric (present-and-current / present-but-stale / absent-with-declared-exception / absent-uncovered) → report_attestation as the durable per-clause attestation artifact that carries the ten sub-clause verdicts plus the whole-Article roll-up verdict and the dated attestation timestamp. Evidence outputs: nis2-self-assessment-report (one per assessment window), per-clause-attestation-record (ten per report). SKELETON only: the operator's evidence-store adapter, the coverage-rubric binding, and the attestation-artifact template are declared as adapter-bound surfaces the operator wires; a sibling CORE card lands the templates, the OSCAL binding closure across CA-2 / CA-7, and the byte-parity goldens across n8n / Temporal / LangGraph. CACAO v2 + SecOps-NG content-model extensions.

    CACAO playbook id : playbook--91a2b3c4-0000-4000-8000-000000000001
    stable_id         : playbook.nis2_self_assessment@v1
    content_version   : 0.1.0
    maturity          : experimental
    workflow_start    : start--91000000-0000-4000-8000-000000000001
    activities        : collect_clause_evidence, map_evidence_to_clauses, score_per_clause_coverage, report_attestation
    """

    @workflow.run
    async def run(self) -> None:
        with _TRACER.start_as_current_span(
            name='workflow.playbook.nis2_self_assessment@v1',
            attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--91a2b3c4-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'},
        ):
            AuditTrail.current().append(
                AuditRecord(span_name='workflow.playbook.nis2_self_assessment@v1', attributes={'secops_ng.compile.target': 'temporal', 'secops_ng.playbook.id': 'playbook--91a2b3c4-0000-4000-8000-000000000001', 'secops_ng.playbook.version': '0.1.0'})
            )
            raise NotImplementedError(
                f"CACAO workflow lowering not implemented: stable_id='playbook.nis2_self_assessment@v1'"
            )

WORKFLOW = PlaybookNis2SelfAssessmentV1Workflow
ACTIVITIES = (collect_clause_evidence, map_evidence_to_clauses, score_per_clause_coverage, report_attestation,)
RETRY_POLICIES = (COLLECT_CLAUSE_EVIDENCE_RETRY_POLICY, MAP_EVIDENCE_TO_CLAUSES_RETRY_POLICY, SCORE_PER_CLAUSE_COVERAGE_RETRY_POLICY, REPORT_ATTESTATION_RETRY_POLICY,)
