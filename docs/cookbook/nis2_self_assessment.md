# nis2_self_assessment — cookbook walkthrough

Operator-side self-assessment lifecycle an essential or important
entity runs on a documented cadence to produce a single dated
attestation demonstrating coverage of the ten NIS2 Article 21(2)(a–j)
cybersecurity risk-management measures. The
`playbook.nis2_self_assessment@v1` CACAO playbook operates the
collect-to-attest chain across the four steps that aggregate per-
clause evidence into one whole-Article roll-up: collect evidence
across every producing playbook the ten sub-clauses anchor against,
bind each record to the sub-clause it discharges, score coverage
against the operator's documented rubric, and emit the dated
attestation the supervisory authority reads against Chapter VII.

The playbook is the **portable description of the self-assessment
discharge**. It does not choose the operator's evidence store, does
not embed the operator's coverage rubric, does not schedule the
self-assessment cadence, and does not ship the attestation-record
template. It describes the workflow shape the operator's stack
should run so the four-step lifecycle (collect → map → score →
report) is auditable, replayable, and restart-safe — as a shipped
Digital Commons artifact.

Distinct from the per-clause playbooks that discharge each Article
21(2) obligation on its own axis (`alert_triage`, `backup_recovery`,
`supply_chain_security`, `vuln_intake`, `detection_engineering`,
`cyber_hygiene_training`, `crypto_posture_management`, `iam_auditor`,
`mfa_secured_comms`, and the other producing playbooks the outbound
overlay enumerates) and from the F-CP-06 effectiveness loop (which
emits per-metric snapshots on an evaluation-window cadence): this
walkthrough covers the **whole-Article roll-up** an operator produces
on the self-assessment cadence they document, keyed on the ten sub-
clause atoms rather than the per-playbook fan-out.

This walkthrough wires the shipped playbook through all three
reference compile targets (n8n, Temporal, LangGraph) and shows where
each lifecycle stage — collect, map, score, attest — lands in each.
Adapter bodies (evidence-store adapter, coverage rubric, declared-
exception register, self-assessment cadence surface, attestation
sink) are declared as adapter-bound surfaces the operator wires; the
shipped CORE artifact lands the byte-parity emitter fan-out under
`examples/{n8n,temporal,langgraph}/nis2_self_assessment/` and the
G-03 cross-target parity test.

> The framework is framework-agnostic by construction. n8n /
> Temporal / LangGraph are *three of three* reference targets;
> the same CACAO source compiles into all of them. Operators
> run whichever target already lives in their stack.

## 1. Why this matters

NIS2 Article 21(1) requires essential and important entities to
take appropriate and proportionate technical, operational and
organisational measures to manage the risks posed to the security
of network and information systems they use for their operations or
for the provision of their services. Article 21(2) enumerates the
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

Supervisory authorities under Chapter VII exercise their supervisory
tasks (Art. 32 for essential entities; Art. 33 for important
entities) against the whole Article 21(2) control surface. An
operator that ships thirty-one playbooks discharging individual
clauses still owes a coherent roll-up when the supervisory authority
asks *are you covered across all ten sub-clauses, and where are the
gaps?* Reading ten disjoint per-clause outputs is not that roll-up; a
dated attestation keyed on the ten sub-clause atoms is.

This playbook is that roll-up. Wiring the self-assessment into an
orchestration surface that survives worker restart, records the
four-step lifecycle as durable evidence, and closes on a dated
attestation is the audit-evident discharge of the whole-Article
coverage posture; assembling the roll-up "on best effort" in a
spreadsheet the day before the supervisory authority visits is not.

## 2. When to run the self-assessment

Three run-triggers land in the operator's cadence configuration and
supply `__assessment_window__` at lifecycle entry. The playbook does
not pick one; it accepts whichever the operator's scheduler names.

- **Scheduled cadence.** The operator's documented periodic self-
  assessment interval (typically annual, sometimes semi-annual for
  essential entities with high change-rates on their processing
  substrate). `__assessment_window__` names the cadence period
  (e.g. `2026-H2`, `2026-annual`). This is the primary Article
  21(2)(f) effectiveness-assessment discharge cadence the operator
  documents in their risk-management policy under Article 21(2)(a).
- **On-demand attestation.** An operator-initiated run outside the
  scheduled cadence, e.g. after a material change to the operator's
  substrate that invalidates the last-scheduled attestation's
  scope, or after a Chapter VI Article 23 significant-incident that
  triggers a control-effectiveness re-check. `__assessment_window__`
  names the on-demand reference (e.g. `2026-post-migration`).
- **Supervisory-authority request.** An Article 32(2) supervisory
  measure (essential entities) or Article 33(2) supervisory measure
  (important entities) directing the operator to produce a current
  self-assessment on a defined deadline. `__assessment_window__`
  names the request reference (e.g. `sa-request-2026-Q3`). The
  attestation record's `assessment_window` field carries this
  reference so the supervisory-authority-facing envelope can be
  cross-referenced by the reviewer.

The workflow is idempotent against `__assessment_window__`: two
runs on the same window resolve to identical `__clause_atoms__`
(the fixed ten-atom set) and re-derive an `__attestation_id__` that
is byte-identical across compile targets for the same evidence set
(§ 8). The operator decides whether to overwrite the prior
attestation or retain both on the accountability ledger; the
framework retains both by default.

## 3. Source of truth

```
content/playbooks/nis2_self_assessment/
├── README.md                    # workflow-local overview and status
├── playbook.cacao.json          # canonical CACAO v2 source (playbook.nis2_self_assessment@v1)
└── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / NIS2 overlay

content/mappings/nis2/
├── article-21-2-a.yaml          # per-clause inbound anchor
├── article-21-2-b.yaml
├── ...                          # one file per Art. 21(2)(a–j) sub-clause
└── article-21-2-f-effectiveness.md
```

The CACAO source is canonical. The four-step lifecycle (one `start`,
four `action` steps, one `end`) is the deterministic policy the
playbook *means*. The three worked examples under
`examples/{n8n,temporal,langgraph}/nis2_self_assessment/` are the
same playbook compiled into three orchestrator idioms. The dated
attestation each execution emits is anchored by a target-agnostic
`artifact_id` derivation so a replay under a different target
produces byte-identical bytes (§ 8).

The G-01 traceability anchor for this workflow closes here: the
ROADMAP entry `F-WF-NIS2-SELF-ASSESS` names this cookbook, the
shipped CACAO source, the compiled targets, and the outbound overlay
as the deliverables that discharge whole-Article Article 21(2)
coverage on the content axis; G-03 closes against the byte-parity
goldens the CORE artifact lands.

## 4. CACAO topology

The workflow is a linear four-step lifecycle. Each action step
carries the CACAO I/O contract (`in_args` / `out_args`) plus
`x_secops_ng` reference bundles pinning the OSCAL control anchors
(CA-2 / CA-7), the D3FEND technique (D3-OAM on the score step), and
the OCSF telemetry class the step emits.

| Step suffix | Step                          | Discipline                                                                                                                             | Status         |
|-------------|-------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | nis2_self_assessment_start    | edge wiring only — no body                                                                                                             | n/a            |
| `…000002`   | collect_clause_evidence       | read the operator's evidence store for the current self-assessment window and pull every evidence record whose producing playbook is one of the sub-clause-anchored playbook set; set `__clause_atoms__` (fixed ten-atom set) and `__evidence_set_id__` | adapter-bound  |
| `…000003`   | map_evidence_to_clauses       | bind each collected evidence record to (i) the sub-clause atom it discharges, (ii) the producing playbook slug, and (iii) the SecOps-NG content-model overlay refs that carry across; set `__clause_mapping__`      | adapter-bound  |
| `…000004`   | score_per_clause_coverage     | score each of the ten sub-clauses against the operator's documented four-bucket coverage rubric; set `__clause_scoring__`             | adapter-bound  |
| `…000005`   | report_attestation            | compose the dated NIS2 Art. 21 self-assessment attestation record; set `__attestation_id__`                                            | adapter-bound  |
| `…000006`   | nis2_self_assessment_end      | edge wiring only — no body                                                                                                             | n/a            |

Sequencing is `on_completion` end-to-end — the playbook is linear,
with no conditional branching at the workflow layer. An unbound
evidence record surfaced at `map_evidence_to_clauses` does not branch
the workflow; it lands as a flagged entry on the attestation record
under the unbound-evidence field. An empty per-clause sub-set is
carried through explicitly rather than dropped: the scoring step
records `absent-uncovered` for that clause, and the attestation
records the gap.

## 5. Playbook variables

The playbook operates on a small set of workflow-scope variables.
`__assessment_window__` is external — supplied by the operator's
scheduler, on-demand trigger, or supervisory-authority request at
lifecycle entry. The remainder are set by downstream steps as the
run progresses.

| Variable                  | External? | Set by                       | Purpose                                                                                                                                                                                             |
|---------------------------|-----------|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `__assessment_window__`   | yes       | operator-supplied            | reference to the self-assessment cohort the run reports against (scheduled-cadence period, on-demand attestation reference, supervisory-authority request reference)                                |
| `__clause_atoms__`        | no        | `collect_clause_evidence`    | fixed ten-atom set (`nis2:art-21-2-a` through `nis2:art-21-2-j`) resolved from `mappings.yaml`                                                                                                       |
| `__evidence_set_id__`     | no        | `collect_clause_evidence`    | opaque identifier of the per-clause evidence set the collect step composed for the window; the map / score / report steps read against this set                                                     |
| `__clause_mapping__`      | no        | `map_evidence_to_clauses`    | per-record binding to (sub-clause atom, producing playbook slug, content-model overlay refs); unbound records are recorded as unbound and flagged                                                   |
| `__clause_scoring__`      | no        | `score_per_clause_coverage`  | per-clause bucket assignment (`present-and-current` / `present-but-stale` / `absent-with-declared-exception` / `absent-uncovered`) plus the operator's freshness thresholds applied                  |
| `__attestation_id__`      | no        | `report_attestation`         | opaque identifier of the emitted attestation record; derives from `SHA-256(workflow_id|execution_id|captured_at)` and is target-agnostic (§ 8)                                                       |

The four-bucket coverage rubric is the invariant that pins the
scoring semantics of the whole roll-up:

- **`present-and-current`** — at least one evidence record in the
  window whose `captured_at` is inside the operator's declared
  freshness threshold for the clause. The clause is covered.
- **`present-but-stale`** — evidence records exist but the freshest
  is past the declared freshness threshold. The clause is
  historically covered; the coverage is not current.
- **`absent-with-declared-exception`** — no evidence records in the
  window but the operator maintains a documented, dated exception
  under their Art. 21(2)(a) risk-analysis policy naming the
  compensating measure. The clause is not covered by the primary
  playbook set, but the compensating measure is on the ledger.
- **`absent-uncovered`** — no evidence records in the window and no
  declared exception. This is the gap the self-assessment surfaces.

The rubric is documented once in the operator's risk-management
policy; the playbook applies it, it does not author it.

## 6. Adapter-bound surfaces

Five operator-owned surfaces sit behind adapter shims in the
lifecycle. The framework describes the CACAO contract each surface
writes into; it does not ship the surface.

### 6.1 Evidence store

`collect_clause_evidence` reads the operator's addressable evidence
repository against the sub-clause-anchored producing-playbook set for
the current window. The evidence store's canonical requirement is
that each record carry **producing-playbook attribution** — the
originating playbook slug (e.g. `backup_recovery`, `vuln_intake`,
`iam_auditor`) — so the downstream map step can bind the record to
the correct sub-clause atom via the inbound overlay under
`content/mappings/nis2/`. The framework ships **no default evidence
store**: the operator's store may be a Postgres table, an S3-
compatible object store on EU sovereign infrastructure, a Delta
Lake on a data-plane the operator controls, or a compliance-platform
export surface. What the framework declares is the read-only contract
and the per-record attribution invariant.

### 6.2 Coverage rubric

`score_per_clause_coverage` applies the operator's documented four-
bucket rubric plus per-clause freshness thresholds. The rubric is
authored once in the operator's risk-management policy (under Art.
21(2)(a)) and referenced by the score step; the framework describes
the four buckets and the per-clause freshness-threshold shape, it
does not fix threshold values. Typical operator practice sets the
freshness threshold at one cadence period for each clause (annual
for policy-shaped clauses, per-quarter for operational clauses such
as vulnerability handling), but the value is operator-owned.

### 6.3 Declared-exception register

`score_per_clause_coverage` reads the operator's dated register of
Art. 21(2)(a) risk-analysis exceptions to distinguish
`absent-with-declared-exception` from `absent-uncovered`. Each
entry in the register names (i) the sub-clause atom the exception
covers, (ii) the compensating measure, (iii) the dated review
horizon after which the exception is re-evaluated. The register
is operator-owned; the framework declares the read shape and the
`absent-with-declared-exception` bucket that reads against it.

### 6.4 Self-assessment cadence surface

The surface `__assessment_window__` names against — the operator's
cadence configuration, on-demand trigger surface, and supervisory-
authority request handler. The framework declares the string-typed
external variable; the operator's scheduler wires the cadence
(cron-workflow on Temporal, a Cron node on n8n, a scheduled thread
launcher on LangGraph) and threads the window reference through.

### 6.5 Attestation sink

`report_attestation` publishes the emitted attestation record into
the operator's evidence store as the durable audit-evident artifact.
The sink is typically the same evidence store the collect step reads
against, though the write path is separate — the attestation record
is a first-class evidence record with its own producing-playbook
slug (`nis2_self_assessment`) so a future run's `collect_clause_
evidence` step against the same store surfaces prior attestations
under the (f) effectiveness-assessment sub-clause.

## 7. Regulatory anchors

**NIS2 Directive (EU) 2022/2555.** The directive prescribes the
whole-Article Article 21(2) minimum-measure surface, the Article
21(2)(f) effectiveness-assessment obligation, and the Chapter VII
supervisory posture (Article 32 for essential entities, Article 33
for important entities) the self-assessment discharges into.
Inbound anchors live under `content/mappings/nis2/` — one file per
sub-clause (`article-21-2-a.yaml` through `article-21-2-j.yaml`)
plus the effectiveness-assessment overlay
`article-21-2-f-effectiveness.md`. Each backlinks
`playbook.nis2_self_assessment@v1` as the whole-Article roll-up
discharge.

**OSCAL controls** — from
[`content/playbooks/nis2_self_assessment/mappings.yaml`](../../content/playbooks/nis2_self_assessment/mappings.yaml):

- **CA-2** *(Control Assessments)* — anchors the playbook end-to-
  end as the control-assessment capability. CA-2 requires the
  operator to develop, review, and approve a control assessment
  plan, assess the controls in the system to determine the extent
  to which they are implemented correctly, operating as intended,
  and producing the desired outcome with respect to meeting
  established security and privacy requirements, and produce a
  control assessment report. The self-assessment lifecycle
  composes the per-clause evidence set, maps records to sub-
  clause atoms, scores coverage, and emits the dated attestation
  record that is the audit-evident report CA-2 reviewers consume.
- **CA-7** *(Continuous Monitoring)* — covers the collect,
  score, and report steps. CA-7 demands ongoing monitoring of
  security controls and reporting of the security state to
  designated officials. The self-assessment cadence is the
  operator's continuous-monitoring discharge on the NIS2 Article
  21 control surface specifically: per-clause evidence is
  collected on the documented cadence, coverage is scored against
  the documented rubric, and the dated attestation record is the
  audit-evident report continuous-monitoring reviewers consume.

**MITRE D3FEND v1.0.0** — `D3-OAM` *Operational Activity
Mapping* is selected on `score_per_clause_coverage` as the
closest-fitting defensive technique for the coverage-rubric
application discipline the step discharges: mapping the collected
per-clause evidence set onto the operator's documented rubric is
the operational-activity-mapping discipline D3-OAM names — the
mapping of operator activities and evidence onto a documented
model of the obligations the operator must discharge. The other
three action steps carry no D3FEND technique: the workflow is a
whole-Article discharge discipline for a supervisory-visible
control surface, not a runtime countermeasure against an
adversary behaviour.

**OCSF v1.3.0** — one class binding.
**API Activity** (class_uid 6003, category Application Activity),
direction `both`. Consumed at the collect and map / score steps
(read calls against the operator's evidence store and against the
SecOps-NG content-model overlay); emitted at the report step (the
write call publishing the dated attestation record to the operator's
evidence store).

**Producing playbook set.** The collect step reads against the sub-
clause-anchored producing-playbook set enumerated on
`content/playbooks/nis2_self_assessment/mappings.yaml` under the
`nis2` block:

- **21(2)(a)** — `infra_posture_management` posture-evidence stream
  plus the operator's governance documentation upstream of the
  playbook set.
- **21(2)(b)** — `alert_triage`, `phishing_triage`,
  `identity_compromise`, `ransomware_containment`, `data_exfil`
  incident-record streams.
- **21(2)(c)** — `backup_recovery` backup-attestation stream.
- **21(2)(d)** — `threat_intel_ingest`,
  `contractual_obligations_tracker`, `supply_chain_security`
  supplier-attestation stream.
- **21(2)(e)** — `vuln_intake`, `cloud_misconfiguration`,
  `patch_management`, `codebase_vuln_management` vulnerability-
  response and patch-evidence streams.
- **21(2)(f)** — `detection_engineering` per-rule effectiveness-
  snapshot stream (the (f) axis on the detection-rule slice; the
  whole-Article self-assessment composes the (f) bucket at the
  operator level from the per-clause coverage-scoring rubric
  applied across the ten sub-clause atoms — complementary, not
  duplicative).
- **21(2)(g)** — `phishing_triage`, `cyber_hygiene_training`
  training-attestation and phishing-sim streams.
- **21(2)(h)** — `crypto_posture_management` crypto-posture
  stream.
- **21(2)(i)** — `iam_auditor`, `asset_management` IAM-audit and
  asset-inventory streams.
- **21(2)(j)** — `mfa_secured_comms` MFA-coverage stream.

## 8. Per-target hand-off

The step outline above is the portable description all three
compilers read against. n8n compiles it into a linear six-node
workflow (`manualTrigger` + four `set` nodes + `noOp`); Temporal
compiles it into a workflow with four activity invocations chained
by `await`; LangGraph compiles it into a `StateGraph` with six
nodes and unconditional-edge topology.

### 8.1 n8n — Set nodes over the four-step lifecycle

`examples/n8n/nis2_self_assessment/workflow.n8n.json` carries the
CACAO topology as n8n nodes (one `manualTrigger`, four `set` nodes,
one `noOp` terminal). Node ids preserve the CACAO step ids verbatim.
Each action node emits a `n8n-nodes-base.set` carrying the CACAO
I/O contract as editable assignment rows plus the `x_secops_ng`
reference bundles.

Operators bind the Set rows to their connectors:

- `collect_clause_evidence` → the operator's evidence-store
  connector (Postgres node against an evidence-record table;
  HTTP Request node against an evidence-store API; S3 node
  against a sovereign-hosted object store carrying the per-
  producing-playbook evidence prefix). Writes `__clause_atoms__`
  from the fixed ten-atom set declared in `mappings.yaml`, and
  `__evidence_set_id__` as the durable identifier of the pulled
  set.
- `map_evidence_to_clauses` → the mapping surface (Function node
  applying the sub-clause-anchor overlay under
  `content/mappings/nis2/` over the collected records; or an
  HTTP Request node against a shared classifier engine). Writes
  `__clause_mapping__`.
- `score_per_clause_coverage` → the rubric-application surface
  (Function node evaluating each clause against the operator's
  documented four-bucket rubric plus freshness thresholds, reading
  the declared-exception register for the `absent-with-declared-
  exception` bucket). Writes `__clause_scoring__`.
- `report_attestation` → the attestation-assembler and sink
  (Function node materialising the attestation record against the
  operator's template, followed by a Postgres / HTTP / S3 write
  node against the attestation-sink surface). Writes
  `__attestation_id__`.

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/nis2_self_assessment/regenerate.sh
```

Equivalent direct invocation:

```sh
PYTHONPATH=. python -m tools.compile \
    content/playbooks/nis2_self_assessment/playbook.cacao.json \
    --target n8n \
    --out examples/n8n/nis2_self_assessment/workflow.n8n.json
```

The byte-parity golden test under
`tests/examples/n8n/nis2_self_assessment/test_golden.py` reruns the
same pipeline and fails if the committed artifact drifts.

### 8.2 Temporal — activities over the four-step lifecycle

`examples/temporal/nis2_self_assessment/workflow.temporal.py`
carries the CACAO topology as a Temporal workflow with one activity
per action step. `__assessment_window__` is threaded through the
workflow signature as an argument — the evidence-store read, the
mapping, and the scoring all read against that external playbook-
scoped input rather than from a worker-local scope. A worker restart
mid-workflow re-hydrates the same window scope against Temporal's
event-history replay contract, so a re-emission of the attestation
record produces byte-identical `__attestation_id__` bytes.

Operators bind the activity bodies to real connectors:

- `collect_clause_evidence` — the evidence-store read activity;
  the reference binding queries the operator's store for records
  in the window whose producing-playbook slug is in the sub-clause-
  anchored set, stamps `__evidence_set_id__`, and resolves
  `__clause_atoms__` from `mappings.yaml`.
- `map_evidence_to_clauses` — the mapping activity applying the
  inbound overlay.
- `score_per_clause_coverage` — the rubric-application activity.
  Time-boxed against the operator's self-assessment deadline;
  unscored clauses are treated as `absent-uncovered` for the
  whole-Article roll-up.
- `report_attestation` — the attestation-assembly and sink
  activity. The `__attestation_id__` derivation happens at the
  primitive layer (not the compile layer) — the activity computes
  the hash and writes the record to the operator's declared sink.

To regenerate the compiled artifact from the repo root:

```sh
./examples/temporal/nis2_self_assessment/regenerate.sh
```

The byte-parity golden test under
`tests/examples/temporal/nis2_self_assessment/test_golden.py`
reruns the emitter and fails if the committed artifact drifts.
Activity bodies remain `NotImplementedError` stubs by design in
the shipped example; the operator supplies the bindings.

### 8.3 LangGraph — nodes and state over the four-step lifecycle

`examples/langgraph/nis2_self_assessment/graph_spec.json` carries
the CACAO topology as a target-neutral GraphSpec (nodes, edges,
conditional edges — the last being empty for this linear playbook);
`state_bindings.py` emits the `TypedDict` state and the `@tool`-
decorated action wrappers plus the agentic-extension hook.
`__assessment_window__` is expressed as a state field threaded
through node bodies, so a checkpoint reload re-hydrates the same
window scope.

The GraphSpec `nodes` array carries only the four intermediate
action step ids; start and end sentinels are pinned structurally
via `entry` and `end_sentinel` (this is the LangGraph projection
contract the G-03 parity test asserts against — the same canonical
CACAO step space is present, in a different structural shape than
n8n's node array).

The audit-mirror sibling `_audit_mirror.py` (see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md))
carries the OTel-free durable audit trail on LangGraph runs where
the operator has not wired an OTLP collector.

Operators bind the tool bodies to real connectors:

- `collect_clause_evidence` → evidence-store read tool.
- `map_evidence_to_clauses` → mapping tool applying the inbound
  overlay.
- `score_per_clause_coverage` → rubric-application tool + optional
  agentic-extension hook. The agentic-extension surface is where an
  operator running a LangGraph agent can invoke an LLM-assisted
  reviewer against the scoring output — e.g. to draft the natural-
  language justification for an `absent-with-declared-exception`
  clause under the operator's compensating-measure narrative — as
  a supplement to the deterministic bucket assignment, not a
  replacement.
- `report_attestation` → attestation-assembly and sink tool.

To regenerate the compiled artifacts from the repo root:

```sh
./examples/langgraph/nis2_self_assessment/regenerate.sh
```

## 9. Byte-parity across compile targets — the G-03 invariant

The attestation record each execution emits is anchored by a
deterministic `artifact_id` derivation:

```
artifact_id = SHA-256(workflow_id | execution_id | captured_at)
```

The input is UTF-8, with single pipe separators and no surrounding
whitespace, and the `compile_target` is **deliberately not part of
the input**. A replay of the same
`(workflow_id, execution_id, captured_at)` triple under n8n,
Temporal, or LangGraph produces byte-identical attestation bytes.

Concretely, across the three targets:

- **n8n** — the attestation emitter reads `execution_id` from the
  workflow-execution scope and `captured_at` from the emitting
  node's evaluation. The `artifact_id` derivation is authored in
  the emitter template, not in the target-specific Function
  nodes, so re-executions and n8n version changes do not drift
  the hash.
- **Temporal** — the emitter activity reads `execution_id` as the
  Temporal workflow-run id and `captured_at` from a workflow-local
  timestamp threaded through the activity call, not from
  `datetime.utcnow()` inside the activity body. A history-replay
  re-derives the identical hash.
- **LangGraph** — the emitter tool reads `execution_id` from the
  LangGraph thread/checkpoint id and `captured_at` from state, not
  from `time.time()` inside the tool body. A checkpoint reload
  re-derives the identical hash.

The byte-parity invariant is asserted across all three targets by
the G-03 parity test at
`tests/content_model/test_nis2_self_assessment_parity.py`. That
test reruns the emitter fan-out under a synthetic
`(workflow_id, execution_id, captured_at)` fixture and asserts the
emitted attestation bytes are identical across the three targets.

The reason for the target-agnostic anchor is regulatory, not
stylistic. The Chapter VII supervisory posture is a posture about
the *operator's whole-Article coverage*, not about the *orchestrator
that runs the assessment*. An operator who migrates from n8n to
Temporal (or runs two windows concurrently on different targets
during a migration) must be able to consolidate their attestation
ledger without dedup drift; the framework refuses the drift-shape
by construction.

## 10. Exporting results as supervisory-reporting evidence

Under Chapter VII the operator is expected to produce, on
supervisory-authority request, the current state of their Article
21(2) coverage. Three fields on the emitted attestation record are
the supervisory-facing surface:

- **`assessment_window`** — the identifier from
  `__assessment_window__`. Supervisory correspondence quotes this
  reference so the operator's response can be joined against the
  supervisory-authority's request record.
- **`clause_atoms[].bucket`** — the per-clause bucket assignment
  from the four-bucket rubric. The supervisory reader learns, per
  clause: covered and current / covered but stale / covered by
  declared compensating measure / uncovered.
- **`roll_up_verdict`** — the whole-Article verdict aggregated
  from the ten per-clause buckets. The verdicts are:
  - **`all-present-and-current`** — every clause covered and
    current.
  - **`mixed-with-declared-exceptions`** — every clause covered
    or exempt with a documented compensating measure; no
    uncovered gaps.
  - **`partial-coverage-with-gaps`** — one or more clauses in
    `absent-uncovered`; the attestation surfaces the gap.
  - **`uncovered`** — no coverage on any clause (the initial-
    state or reset-state; typically only observed on first-run
    for new operators).

The attestation record is the audit-evident artifact retained on the
operator's evidence store. Wiring it into the supervisory-authority-
facing envelope is an operator responsibility: the framework does
not ship the per-authority submission channel (each EU competent
authority publishes its own reporting portal, submission format, and
reference-number allocation). What the framework produces is the
canonical, dated, byte-deterministic record the operator's
submission wraps.

The `absent-uncovered` entries on the attestation are the leading
signal for the operator's plan-of-action authoring surface, which
lives upstream of the playbook in the operator's governance
documentation. OSCAL CA-5 (Plan of Action and Milestones) is not
pinned inside this workflow: the self-assessment surfaces the gap,
the operator's plan-of-action surface closes it. The two are
linked by convention (the attestation record's assessment-window
reference joins to the plan-of-action's coverage entry) but not by
CACAO topology.

## 11. Playbook chain — where nis2_self_assessment sits

The self-assessment lifecycle interacts with the producing playbooks
on the operator's substrate. The interactions are documented at the
CACAO source and in `mappings.yaml`, and are worth calling out in a
cookbook context so a reader can situate the workflow:

- **Producing playbooks (§ 7).** The collect step reads their
  emitted evidence; the self-assessment does not itself discharge
  any of the ten sub-clause obligations. Each producing playbook
  remains the audit-evident discharge on its own axis. The self-
  assessment is the roll-up, not the replacement.
- **`detection_engineering` — Art. 21(2)(f) effectiveness.** The
  per-rule effectiveness-snapshot slice discharges (f) on the
  detection-rule axis. The whole-Article self-assessment composes
  the (f) bucket at the operator level from the per-clause
  coverage-scoring rubric across the ten atoms. The two are
  complementary: an operator with excellent per-rule effectiveness
  scores on (f) can still have `absent-uncovered` on other clauses,
  and the self-assessment surfaces that separation.
- **`incident_management` — Chapter VI Article 23.** A significant-
  incident event that triggers Chapter VI reporting may also invalidate
  the last-scheduled self-assessment's scope (the incident revealed a
  control gap not in the prior attestation's ledger). Practice is
  to run an on-demand self-assessment against a fresh
  `__assessment_window__` after any Article 23-significant incident,
  so the supervisory-facing posture reflects the current state.
- **The operator's risk-management policy under Art. 21(2)(a).**
  The self-assessment reads the operator's coverage rubric and the
  declared-exception register from documentation authored under
  the risk-management policy. The playbook applies the policy; it
  does not author it.

## 12. What this cookbook deliberately does not cover

- **The evidence-store schema.** The per-record shape, indexing,
  and retention posture are operator-owned. The framework describes
  the read contract and the per-record attribution invariant; it
  does not ship the store.
- **The coverage rubric and freshness thresholds.** The four
  buckets are named; the per-clause freshness threshold values
  are operator-owned and documented in the operator's risk-
  management policy under Art. 21(2)(a).
- **The declared-exception register.** The register shape is
  operator-owned. The framework declares the read shape and the
  `absent-with-declared-exception` bucket that reads against it.
- **The self-assessment cadence.** The Article 21(2)(f)
  effectiveness-assessment interval is operator-authored (annual /
  semi-annual / event-driven) and lives in the operator's
  continuous-monitoring documentation. OSCAL PM-31 (Continuous
  Monitoring Strategy) sits upstream of the playbook; the workflow
  applies the cadence, it does not schedule it.
- **The attestation-record template.** The evidence schema for
  the attestation record is anchored per compile target on the
  emitter side; the operator-facing rendering template (a PDF,
  a Confluence page, a compliance-platform record) is operator-
  owned and sits downstream of the write to the attestation
  sink.
- **The supervisory-authority submission channel.** Each EU
  competent authority publishes its own Chapter VII submission
  surface (per-authority form, per-authority reference-number
  allocation, per-authority channel of record). The framework
  produces the attestation record; the operator wraps it into
  the per-authority envelope.
- **The plan-of-action authoring for uncovered clauses.** OSCAL
  CA-5 (Plan of Action and Milestones) sits upstream of the
  playbook in the operator's governance documentation. The
  self-assessment surfaces the gap; the plan-of-action surface
  closes it.
- **DORA and CRA cross-regime attestation.** DORA's equivalent
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

## 13. References

- OASIS CACAO v2.0 specification.
- NIS2 Directive (EU) 2022/2555 — Article 21(1) (general
  obligation), Article 21(2)(a–j) (minimum measures), Article
  21(2)(f) (effectiveness assessment), Chapter VI (Article 23,
  significant-incident reporting), Chapter VII (Articles 32–33,
  supervision and enforcement).
- NIST SP 800-53 Rev. 5 — CA-2 (Control Assessments), CA-7
  (Continuous Monitoring), PM-31 (Continuous Monitoring Strategy).
- MITRE D3FEND v1.0.0 — D3-OAM Operational Activity Mapping.
- OCSF v1.3.0 — API Activity (class_uid 6003) event class.
- ENISA — technical implementation guidance for NIS2 Article 21
  cybersecurity risk-management measures.
