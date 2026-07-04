# nis2_self_assessment

CACAO v2 SKELETON playbook operationalising the operator-side
**NIS2 Article 21 self-assessment report** an essential or important
entity produces to demonstrate coverage of the ten Article 21(2)(a–j)
cybersecurity risk-management measures in a single dated attestation
artifact.

Distinct from the per-clause playbooks that discharge each Article
21(2) obligation on its own axis (posture, incident-handling, backup,
supply-chain, vulnerability, effectiveness, hygiene, crypto, IAM,
MFA) and from the F-CP-06 effectiveness loop (which emits per-metric
snapshots on an evaluation-window cadence): this playbook is the
**whole-Article roll-up** an operator produces on the self-assessment
cadence they document, keyed on the ten sub-clause atoms rather than
the per-playbook fan-out.

Status: **SKELETON**. Action steps are scaffolded as CACAO v2 actions
with `control_refs` / `telemetry_refs` / `metric_refs` stubs; the
per-clause evidence-collection primitive, the evidence-to-clause
mapping primitive, the coverage-scoring rubric, and the dated
attestation-emission are placeholders that a sibling CORE card lands.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.nis2_self_assessment@v1`), authored as JSON per the
  finalisation-marker convention (`.cacao.json` or `.cacao.yaml`
  both counted as finalised).
- `mappings.yaml` — outbound cross-references to the OSCAL controls,
  MITRE D3FEND techniques, OCSF event classes, and EU regulatory
  clauses this playbook operationalises. The SKELETON overlay pins
  all ten Art. 21(2)(a–j) sub-clause atoms as outbound backlinks,
  the OSCAL CA-2 (Control Assessments) and CA-7 (Continuous
  Monitoring) anchors, and the D3-OAM D3FEND anchor on the
  score-per-clause-coverage step.

## Compile targets

`compile_targets` declares `[n8n, temporal, langgraph]`. Emitted
artifacts under `examples/{n8n,temporal,langgraph}/nis2_self_assessment/`
land in a follow-on CORE-FANOUT card once the per-clause evidence-
collection primitive, the mapping primitive, the coverage-scoring
rubric, and the attestation-emission primitive are populated.

## Step outline

1. **collect_clause_evidence** — read the operator's evidence store
   for the current self-assessment window and pull every evidence
   record whose producing playbook is one of the playbooks the ten
   Art. 21(2)(a–j) sub-clauses anchor against. Sets
   `__clause_atoms__` (fixed ten-atom set nis2:art-21-2-a … -j) and
   `__evidence_set_id__`.
2. **map_evidence_to_clauses** — bind each evidence record to (i)
   the sub-clause atom it discharges, (ii) the playbook slug that
   produced it, and (iii) the SecOps-NG content-model overlay refs
   (control, telemetry, metric) that carry across from the
   producing playbook. Records `__clause_mapping__`.
3. **score_per_clause_coverage** — score each of the ten sub-clauses
   against the operator's documented coverage rubric
   (present-and-current / present-but-stale / absent-with-declared-
   exception / absent-uncovered). Records `__clause_scoring__`.
4. **report_attestation** — compose the dated JSON-native NIS2
   Art. 21 self-assessment attestation record and publish it to
   the operator's evidence store. Sets `__attestation_id__`.

## Regulatory anchors

| Step (playbook axis)              | Clause                                    |
| --------------------------------- | ----------------------------------------- |
| Per-clause evidence collection    | NIS2 Article 21(2)(a–j)                   |
| Evidence-to-clause mapping        | NIS2 Article 21(2)(a–j)                   |
| Per-clause coverage scoring       | NIS2 Article 21(2)(f) (effectiveness)     |
| Dated attestation emission        | NIS2 Article 21(2) whole-Article roll-up  |

Inbound mappings live at
[`content/mappings/nis2/article-21-2-a.yaml`](../../mappings/nis2/article-21-2-a.yaml)
through
[`article-21-2-j.yaml`](../../mappings/nis2/article-21-2-j.yaml).
Each of the ten sub-clause atoms carries an outbound backlink to
`playbook.nis2_self_assessment@v1` so the orphan-CI graph closes
end-to-end on the NIS2 axis without a skip entry. DORA and CRA
axes are recorded as reviewed skips in the respective
`_orphan_skip.yaml` files; rationale is documented there.

## Operator integration notes

The SKELETON declares the following adapter-bound surfaces the
operator wires; the CORE card lands the reference bindings:

- **Evidence store** — the operator's declared, addressable
  evidence repository the collect step reads against for the
  current self-assessment window (per-playbook evidence stream
  attribution required so each record can be joined to a producing
  playbook slug).
- **Coverage rubric** — the operator's documented four-bucket
  coverage rubric (present-and-current / present-but-stale /
  absent-with-declared-exception / absent-uncovered) plus the
  per-clause freshness threshold that separates present-and-current
  from present-but-stale.
- **Declared-exception register** — the operator's dated register
  of Art. 21(2)(a) risk-analysis exceptions naming the compensating
  measure for each clause the operator has consciously chosen not
  to discharge with an evidence-producing playbook.
- **Self-assessment cadence** — the operator's documented cadence
  the `__assessment_window__` external variable names against
  (scheduled-cadence, on-demand attestation, supervisory-authority
  request). The playbook does not itself schedule the cadence.
- **Attestation sink** — the operator's evidence store the dated
  attestation record is published to at the report step, with the
  content-addressed filename derived from the artifact_id
  `SHA-256(workflow_id|execution_id|captured_at)`.

## Sources

- OASIS CACAO v2.0 specification.
- NIS2 Directive (EU) 2022/2555, Article 21(2) — cybersecurity
  risk-management measures (a–j); Article 21(2)(f) — effectiveness
  assessment.
- NIST SP 800-53 Rev. 5 — CA-2 (Control Assessments), CA-7
  (Continuous Monitoring).
- ENISA — technical implementation guidance for NIS2 Article 21
  cybersecurity risk-management measures.
- OCSF v1.3.0 — API Activity (class_uid 6003) event class.
