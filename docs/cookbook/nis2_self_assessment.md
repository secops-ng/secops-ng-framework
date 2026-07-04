# nis2_self_assessment — cookbook walkthrough

Operator-side self-assessment lifecycle an essential or important
entity runs to produce a single dated attestation demonstrating
coverage of the ten NIS2 Article 21(2)(a–j) cybersecurity risk-
management measures. The `playbook.nis2_self_assessment@v1` CACAO
playbook aggregates the per-clause evidence the ten obligations
produce across the operator's shipped playbook set into one
coherent output, on the self-assessment cadence the operator
documents.

The playbook is the **portable description of the self-assessment
discharge**. It does not choose the operator's evidence store, does
not embed the operator's coverage rubric, and does not schedule the
self-assessment cadence. It describes the workflow shape the
operator's stack should run so the four-step lifecycle (collect →
map → score → report) is auditable, replayable, and restart-safe —
as a shipped Digital Commons artifact.

Distinct from the per-clause playbooks that discharge each Article
21(2) obligation on its own axis, and from the F-CP-06 effectiveness
loop (which emits per-metric snapshots on an evaluation-window
cadence): this walkthrough covers the **whole-Article roll-up** an
operator produces on the self-assessment cadence they document,
keyed on the ten sub-clause atoms rather than the per-playbook
fan-out.

> The framework is framework-agnostic by construction. n8n /
> Temporal / LangGraph are *three of three* reference targets;
> the same CACAO source compiles into all of them. Operators
> run whichever target already lives in their stack.

Status: **SKELETON walkthrough**. The lifecycle shape and adapter-
bound surfaces are pinned; the per-target compiled examples
(byte-parity goldens) land in the sibling CORE-FANOUT card.

## 1. Why this matters

NIS2 Article 21(1) requires essential and important entities to
take appropriate and proportionate technical, operational and
organisational measures to manage the risks posed to the security
of network and information systems. Article 21(2) enumerates the
minimum measures — the ten sub-clauses (a) through (j):

- **Art. 21(2)(a)** — policies on risk analysis and information-
  system security.
- **Art. 21(2)(b)** — incident handling.
- **Art. 21(2)(c)** — business continuity, including backup
  management and disaster recovery, and crisis management.
- **Art. 21(2)(d)** — supply-chain security, including security-
  related aspects concerning the relationships between each entity
  and its direct suppliers or service providers.
- **Art. 21(2)(e)** — security in network and information systems
  acquisition, development and maintenance, including vulnerability
  handling and disclosure.
- **Art. 21(2)(f)** — policies and procedures to assess the
  effectiveness of cybersecurity risk-management measures.
- **Art. 21(2)(g)** — basic cyber-hygiene practices and
  cybersecurity training.
- **Art. 21(2)(h)** — policies and procedures regarding the use of
  cryptography and, where appropriate, encryption.
- **Art. 21(2)(i)** — human resources security, access-control
  policies and asset management.
- **Art. 21(2)(j)** — the use of multi-factor authentication or
  continuous authentication solutions, secured voice, video and
  text communications and secured emergency-communication systems
  within the entity, where appropriate.

Supervisory authorities under Chapter VII exercise their
supervisory tasks (Art. 32 for essential entities; Art. 33 for
important entities) against the whole Article 21(2) control
surface. An operator that ships thirty-one playbooks discharging
individual clauses still owes a coherent roll-up when the
supervisory authority asks *are you covered across all ten
sub-clauses, and where are the gaps?* Reading ten disjoint
per-clause outputs is not that roll-up; a dated attestation
keyed on the ten sub-clause atoms is.

This playbook is that roll-up.

## 2. Source of truth

```
content/playbooks/nis2_self_assessment/
├── README.md                    # workflow-local overview and status
├── playbook.cacao.json          # CACAO v2 SKELETON artifact
└── mappings.yaml                # outbound cross-references (OSCAL, D3FEND, OCSF, NIS2)
```

The CACAO artifact is the portable source; the reference compilers
under `compilers/{n8n,temporal,langgraph}/` read it and emit target-
specific artifacts. Byte-parity between compilers is asserted by the
per-example goldens under `tests/examples/`.

## 3. Lifecycle

The playbook chains four steps under a single start → end skeleton:

1. **collect_clause_evidence** — read the operator's evidence store
   for the current self-assessment window (named by
   `__assessment_window__`) and pull every evidence record whose
   producing playbook is one of the playbooks the ten Art. 21(2)(a–j)
   sub-clauses anchor against. Sets `__clause_atoms__` (fixed
   ten-atom set nis2:art-21-2-a through nis2:art-21-2-j) and
   `__evidence_set_id__`. Read-only against the evidence store.
2. **map_evidence_to_clauses** — bind each evidence record in the
   set to (i) the sub-clause atom it discharges, (ii) the playbook
   slug that produced it, and (iii) the SecOps-NG content-model
   overlay refs that carry across from the producing playbook.
   Best-effort: records that do not bind to a documented sub-clause
   atom are recorded as unbound and flagged on the report rather
   than dropped. Empty per-clause sub-sets are emitted explicitly
   so the downstream scoring records absent-uncovered rather than
   silently dropping the clause. Records `__clause_mapping__`.
3. **score_per_clause_coverage** — score each of the ten sub-clauses
   against the operator's documented four-bucket coverage rubric:
   - **present-and-current** — at least one evidence record in the
     window whose captured_at is inside the operator's declared
     freshness threshold for the clause.
   - **present-but-stale** — evidence records exist but the
     freshest is past the declared freshness threshold.
   - **absent-with-declared-exception** — no evidence records in
     the window but the operator maintains a documented, dated
     exception under their Art. 21(2)(a) risk-analysis policy
     naming the compensating measure.
   - **absent-uncovered** — no evidence records in the window and
     no declared exception. This is the gap the self-assessment
     surfaces.
   Time-boxed against the operator's self-assessment deadline;
   unscored clauses are recorded as `['unscored']` and treated as
   absent-uncovered for the whole-Article roll-up. Records
   `__clause_scoring__`.
4. **report_attestation** — compose the JSON-native NIS2 Art. 21
   self-assessment attestation record shaped against the
   `schemas/evidence/nis2-self-assessment.schema.json` (stream:
   attestation, landing in the sibling CORE card). Pins the
   `artifact_id` as `SHA-256(workflow_id|execution_id|captured_at)`
   so the three reference compilers re-derive byte-identical bytes
   from the same primitive output (the byte-parity contract the
   F-WF-NIS2-SELF-ASSESS CORE-FANOUT siblings assert against). The
   record carries the assessment window, the ten sub-clause atoms
   with their per-clause scoring buckets, the unbound-evidence
   flag (if any), the whole-Article roll-up verdict
   (all-present-and-current / mixed-with-declared-exceptions /
   partial-coverage-with-gaps / uncovered), and the dated
   attestation timestamp. Sets `__attestation_id__`.

## 4. Adapter-bound surfaces the operator wires

The SKELETON pins the topology and the ID / regulatory anchor refs.
Deterministic bindings for the following surfaces land with the
sibling CORE card:

- **Evidence store** — the operator's declared, addressable
  evidence repository the collect step reads against, with
  producing-playbook attribution present on each record.
- **Coverage rubric** — the operator's documented four-bucket
  rubric plus the per-clause freshness thresholds.
- **Declared-exception register** — the operator's dated register
  of Art. 21(2)(a) risk-analysis exceptions naming the compensating
  measure per clause.
- **Self-assessment cadence** — the surface `__assessment_window__`
  names against (scheduled-cadence, on-demand attestation,
  supervisory-authority request).
- **Attestation sink** — the operator's evidence store the dated
  attestation record is published to.

## 5. Compile targets (SKELETON)

At the SKELETON tier the CACAO artifact declares
`compile_targets: [n8n, temporal, langgraph]` and the reference
compilers accept the artifact but do not yet emit per-target
worked examples. The three per-target examples under
`examples/{n8n,temporal,langgraph}/nis2_self_assessment/`, along
with the byte-parity goldens under
`tests/examples/nis2_self_assessment/`, land in the sibling
**CORE-FANOUT** card once the four per-step primitives are pinned.

The step outline above is the portable description all three
compilers read against. n8n compiles it into a linear four-node
workflow; Temporal compiles it into a workflow with four activity
invocations chained by `await`; LangGraph compiles it into a
StateGraph with four nodes and a single-edge topology. The
attestation record's `artifact_id` is derived at the primitive
layer (not the compile layer) so all three targets emit byte-
identical attestation records from the same input evidence set —
the byte-parity contract the CORE-FANOUT goldens assert against.

## 6. What is intentionally out of scope

- **Per-clause producing playbooks.** The self-assessment is a
  roll-up; it does not itself discharge any of the ten sub-clause
  obligations. Each producing playbook (infra_posture_management,
  alert_triage, backup_recovery, threat_intel_ingest, vuln_intake,
  detection_engineering, cyber_hygiene_training,
  crypto_posture_management, iam_auditor, mfa_secured_comms, and
  the other eleven playbooks the outbound overlay enumerates)
  remains the audit-evident discharge on its own axis. The
  self-assessment reads their evidence; it does not replace them.
- **Plan of action for uncovered clauses.** The self-assessment
  surfaces the gap; the operator's plan-of-action authoring
  surface lives upstream of this playbook in their governance
  documentation. OSCAL CA-5 (Plan of Action and Milestones) is
  not pinned at the SKELETON layer for this reason; a CORE-PRIM
  card revisits the pin once the attestation record's uncovered-
  clause structure is fixed and the operator's plan-of-action
  authoring surface is bound.
- **DORA / CRA cross-regime attestation.** DORA's equivalent
  whole-framework self-assessment (Art. 6(5) ICT-risk-management
  framework annual review plus Art. 24 digital-operational-
  resilience-testing programme) is regime-specific to financial
  entities and anchors on a different producing-playbook set; a
  dedicated DORA self-assessment playbook is the appropriate
  discharge there. CRA Annex I is product-by-product manufacturer
  scope, not an operator-side self-assessment surface. Both are
  recorded as reviewed skips under
  `content/mappings/{dora,cra}/_orphan_skip.yaml` rather than as
  cross-pins.
- **Continuous-monitoring cadence authoring.** The self-assessment
  cadence is authored upstream of this playbook in the operator's
  continuous-monitoring documentation. OSCAL PM-31 (Continuous
  Monitoring Strategy) is not pinned at the SKELETON layer for
  this reason.

## 7. Sources

- OASIS CACAO v2.0 specification.
- NIS2 Directive (EU) 2022/2555 — Article 21(1) (general
  obligation), Article 21(2)(a–j) (minimum measures), Article
  21(2)(f) (effectiveness assessment), Chapter VII (supervision
  and enforcement).
- NIST SP 800-53 Rev. 5 — CA-2 (Control Assessments), CA-7
  (Continuous Monitoring).
- ENISA — technical implementation guidance for NIS2 Article 21
  cybersecurity risk-management measures.
- OCSF v1.3.0 — API Activity (class_uid 6003) event class.
