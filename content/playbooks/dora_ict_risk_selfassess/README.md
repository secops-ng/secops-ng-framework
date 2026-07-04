# dora_ict_risk_selfassess

CACAO v2 SKELETON playbook operationalising the operator-side
**DORA Chapter II ICT risk management self-assessment report** a
financial entity produces to demonstrate coverage of the five ICT
risk management sections (Articles 6, 7, 8, 10, 11) in a single
dated attestation artifact.

Distinct from the per-section playbooks that discharge each Chapter
II obligation on its own axis (framework and governance, systems and
protocols, identification, detection, response and recovery) and from
the F-CP-06 effectiveness loop (which emits per-metric snapshots on
an evaluation-window cadence): this playbook is the **whole-Chapter
roll-up** an operator produces on the Article 6(5) annual-review
cadence (plus the post-major-incident review trigger the same
paragraph names), keyed on the five section atoms rather than the
per-playbook fan-out.

Status: **SKELETON**. Action steps are scaffolded as CACAO v2 actions
with `control_refs` / `telemetry_refs` / `metric_refs` stubs; the
per-section evidence-collection primitive, the evidence-to-section
mapping primitive, the coverage-scoring rubric, and the dated
attestation-emission are placeholders that a sibling CORE card lands.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.dora_ict_risk_selfassess@v1`), authored as JSON per the
  finalisation-marker convention (`.cacao.json` or `.cacao.yaml`
  both counted as finalised).
- `mappings.yaml` — outbound cross-references to the OSCAL controls,
  MITRE D3FEND techniques, OCSF event classes, and EU regulatory
  clauses this playbook operationalises. The SKELETON overlay pins
  the five Chapter II section atoms (Art. 6/7/8/10/11) as outbound
  backlinks, the OSCAL CA-2 (Control Assessments) and CA-7
  (Continuous Monitoring) anchors, and the D3-OAM D3FEND anchor on
  the score-per-section-coverage step.

## Compile targets

`compile_targets` declares `[n8n, temporal, langgraph]`. Emitted
artifacts under `examples/{n8n,temporal,langgraph}/dora_ict_risk_selfassess/`
land in a follow-on CORE-FANOUT card once the per-section evidence-
collection primitive, the mapping primitive, the coverage-scoring
rubric, and the attestation-emission primitive are populated.

## Step outline

1. **collect_section_evidence** — read the operator's evidence store
   for the current self-assessment window and pull every evidence
   record whose producing playbook is one of the playbooks the five
   Chapter II section atoms anchor against. Sets `__section_atoms__`
   (fixed five-atom set dora:art-6-framework,
   dora:art-7-systems-protocols-tools, dora:art-8-identification,
   dora:art-10-detection, dora:art-11-response-recovery) and
   `__evidence_set_id__`.
2. **map_evidence_to_sections** — bind each evidence record to (i)
   the section atom it discharges, (ii) the playbook slug that
   produced it, and (iii) the SecOps-NG content-model overlay refs
   (control, telemetry, metric) that carry across from the
   producing playbook. Records `__section_mapping__`.
3. **score_per_section_coverage** — score each of the five sections
   against the operator's documented coverage rubric
   (present-and-current / present-but-stale / absent-with-declared-
   exception / absent-uncovered). Records `__section_scoring__`.
4. **report_attestation** — compose the dated JSON-native DORA
   Chapter II ICT risk management self-assessment attestation record
   and publish it to the operator's evidence store. Sets
   `__attestation_id__`.

## Regulatory anchors

| Step (playbook axis)              | Clause                                       |
| --------------------------------- | -------------------------------------------- |
| Per-section evidence collection   | DORA Chapter II (Articles 6, 7, 8, 10, 11)   |
| Evidence-to-section mapping       | DORA Chapter II (Articles 6, 7, 8, 10, 11)   |
| Per-section coverage scoring      | DORA Article 6(5) annual review              |
| Dated attestation emission        | DORA Chapter II whole-Chapter roll-up        |

Inbound mappings live at
[`content/mappings/dora/article-6.yaml`](../../mappings/dora/article-6.yaml)
(dora:art-6-framework),
[`article-7.yaml`](../../mappings/dora/article-7.yaml)
(dora:art-7-systems-protocols-tools),
[`article-8.yaml`](../../mappings/dora/article-8.yaml)
(dora:art-8-identification),
[`article-10.yaml`](../../mappings/dora/article-10.yaml)
(dora:art-10-detection), and
[`article-11.yaml`](../../mappings/dora/article-11.yaml)
(dora:art-11-response-recovery). Each of the five section atoms
carries an outbound backlink to `playbook.dora_ict_risk_selfassess@v1`
so the orphan-CI graph closes end-to-end on the DORA axis without a
skip entry. NIS2, CRA, and GDPR axes are recorded as reviewed skips
in the respective `_orphan_skip.yaml` files; rationale is documented
there.

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
  per-section freshness threshold that separates present-and-current
  from present-but-stale.
- **Declared-exception register** — the operator's dated register
  of Art. 6 ICT-risk-management-framework exceptions naming the
  compensating measure for each section the operator has consciously
  chosen not to discharge with an evidence-producing playbook.
- **Self-assessment cadence** — the operator's documented cadence
  the `__assessment_window__` external variable names against. The
  primary DORA anchor is the Art. 6(5) annual review of the ICT
  risk-management framework plus the post-major-incident review
  trigger the same paragraph names; on-demand supervisory-authority
  requests and the operator's documented interim review cadence are
  the secondary triggers. The playbook does not itself schedule the
  cadence.
- **Attestation sink** — the operator's evidence store the dated
  attestation record is published to at the report step, with the
  content-addressed filename derived from the artifact_id
  `SHA-256(workflow_id|execution_id|captured_at)`.

## Sources

- OASIS CACAO v2.0 specification.
- DORA — Regulation (EU) 2022/2554, Chapter II (Articles 6–14) ICT
  risk management; Article 6(5) annual review of the ICT
  risk-management framework.
- NIST SP 800-53 Rev. 5 — CA-2 (Control Assessments), CA-7
  (Continuous Monitoring).
- Commission Delegated Regulation (EU) 2024/1774 — JC RTS on the
  ICT risk-management framework and simplified ICT risk-management
  framework.
- OCSF v1.3.0 — API Activity (class_uid 6003) event class.
