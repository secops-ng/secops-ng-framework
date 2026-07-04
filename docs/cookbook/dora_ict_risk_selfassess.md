# dora_ict_risk_selfassess — cookbook walkthrough

Operator-side self-assessment lifecycle a DORA-in-scope financial
entity runs on the Article 6(5) annual review cadence — plus the
post-major-incident review trigger the same paragraph names — to
produce a single dated attestation demonstrating coverage of the
five Chapter II ICT risk management section atoms (Articles 6, 7,
8, 10, and 11). The `playbook.dora_ict_risk_selfassess@v1` CACAO
playbook operates the collect-to-attest chain across the four steps
that aggregate per-section evidence into one whole-Chapter roll-up:
collect evidence across every producing playbook the five section
atoms anchor against, bind each record to the section it discharges,
score coverage against the operator's documented rubric, and emit
the dated attestation the competent authority reads against DORA's
supervisory posture.

The playbook is the **portable description of the ICT risk
management self-assessment discharge**. It does not choose the
operator's evidence store, does not embed the operator's coverage
rubric, does not schedule the Article 6(5) annual review, and does
not ship the attestation-record template. It describes the workflow
shape the operator's stack should run so the four-step lifecycle
(collect → map → score → report) is auditable, replayable, and
restart-safe — as a shipped Digital Commons artifact for the
financial-services community.

Distinct from the per-section playbooks that discharge each Chapter
II obligation on its own axis (framework and governance,
systems/protocols/tools, identification, detection, response and
recovery) and from the F-CP-06 effectiveness loop (which emits
per-metric snapshots on an evaluation-window cadence): this
walkthrough covers the **whole-Chapter roll-up** an operator produces
on the Article 6(5) annual review cadence (plus the post-major-
incident review trigger), keyed on the five section atoms rather
than the per-playbook fan-out.

This walkthrough wires the shipped playbook through all three
reference compile targets (n8n, Temporal, LangGraph) and shows where
each lifecycle stage — collect, map, score, attest — lands in each.
Adapter bodies (evidence-store adapter, coverage rubric, declared-
exception register, self-assessment cadence surface, attestation
sink) are declared as adapter-bound surfaces the operator wires; the
shipped CORE artifact lands the byte-parity emitter fan-out under
`examples/{n8n,temporal,langgraph}/dora_ict_risk_selfassess/` and the
G-03 cross-target parity test.

> The framework is framework-agnostic by construction. n8n /
> Temporal / LangGraph are *three of three* reference targets;
> the same CACAO source compiles into all of them. Operators
> run whichever target already lives in their stack.

## 1. Why this matters

DORA Article 5 places the ICT risk management framework under the
management body of a financial entity, with ultimate responsibility
for managing ICT risk. Chapter II (Articles 6 to 14) prescribes the
substance of that framework — the five sections this playbook rolls
up against being:

- **Art. 6** — ICT risk management framework: the documented
  framework itself (policies, procedures, protocols, tools) the
  financial entity maintains to protect information and ICT assets.
  Art. 6(5) fixes the **annual review cadence** and names the
  **post-major-incident review trigger** the whole roll-up
  discharges against.
- **Art. 7** — ICT systems, protocols and tools: the requirement to
  use reliable, resilient, and technologically current systems and
  the associated protocols and tools.
- **Art. 8** — Identification: continuous identification of all
  sources of ICT risk, in particular the risk exposure to and from
  other financial entities, and the ICT-asset inventory the
  identification discipline depends on.
- **Art. 10** — Detection: mechanisms to promptly detect anomalous
  activities in accordance with Article 17, including ICT
  network-performance issues and ICT-related incidents.
- **Art. 11** — Response and recovery: the ICT business continuity
  policy and associated ICT response and recovery plans, backup
  policies, restoration procedures, and communication plans.

Chapter IV places the supervisory posture in the hands of the
financial entity's competent authority. The competent authority
exercises its supervisory tasks against the whole Chapter II ICT
risk management surface. A financial entity that ships a wide
per-section playbook portfolio still owes a coherent roll-up when
the competent authority asks *are you covered across all five
Chapter II sections, and where are the gaps?* Reading five disjoint
per-section outputs is not that roll-up; a dated attestation keyed
on the five section atoms is.

This playbook is that roll-up. Wiring the self-assessment into an
orchestration surface that survives worker restart, records the
four-step lifecycle as durable evidence, and closes on a dated
attestation is the audit-evident discharge of the whole-Chapter
coverage posture; assembling the roll-up "on best effort" in a
spreadsheet the day before the supervisory review is not.

## 2. When to run the self-assessment

Three run-triggers land in the operator's cadence configuration and
supply `__assessment_window__` at lifecycle entry. The playbook does
not pick one; it accepts whichever the operator's scheduler names.

- **Article 6(5) annual review.** The DORA-named annual review of
  the ICT risk management framework. This is the primary regulatory
  cadence and the trigger every DORA-in-scope financial entity
  discharges at least once a year. `__assessment_window__` names
  the annual reference (e.g. `2026-annual`, `2026-FY`).
- **Post-major-incident review.** Article 6(5) also names the
  review the financial entity conducts **after a major ICT-related
  incident**. The threshold that constitutes "major" is fixed by
  the Article 18 classification criteria and the associated JC RTS
  (Commission Delegated Regulation (EU) 2024/1772). When a
  post-major-incident review fires, `__assessment_window__` names
  the incident reference (e.g. `2026-post-incident-<incident-id>`),
  so the attestation record's `assessment_window` field carries the
  incident-triggered scope and a competent-authority reviewer can
  cross-reference the ICT-related incident report submitted under
  Chapter III.
- **Supervisory-authority request.** A competent-authority
  supervisory measure directing the financial entity to produce a
  current self-assessment on a defined deadline.
  `__assessment_window__` names the request reference
  (e.g. `sa-request-2026-Q3`). The attestation record's
  `assessment_window` field carries this reference so the
  supervisory-authority-facing envelope can be cross-referenced.

The workflow is idempotent against `__assessment_window__`: two
runs on the same window resolve to identical `__section_atoms__`
(the fixed five-atom set) and re-derive an `__attestation_id__` that
is byte-identical across compile targets for the same evidence set
(§ 9). The operator decides whether to overwrite the prior
attestation or retain both on the accountability ledger; the
framework retains both by default.

## 3. Source of truth

```
content/playbooks/dora_ict_risk_selfassess/
├── README.md                    # workflow-local overview and status
├── playbook.cacao.json          # canonical CACAO v2 source (playbook.dora_ict_risk_selfassess@v1)
└── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / DORA overlay

content/mappings/dora/
├── article-6.yaml               # dora:art-6-framework inbound anchor
├── article-7.yaml               # dora:art-7-systems-protocols-tools
├── article-8.yaml               # dora:art-8-identification
├── article-10.yaml              # dora:art-10-detection
└── article-11.yaml              # dora:art-11-response-recovery
```

The CACAO source is canonical. The four-step lifecycle (one `start`,
four `action` steps, one `end`) is the deterministic policy the
playbook *means*. The three worked examples under
`examples/{n8n,temporal,langgraph}/dora_ict_risk_selfassess/` are the
same playbook compiled into three orchestrator idioms. The dated
attestation each execution emits is anchored by a target-agnostic
`artifact_id` derivation so a replay under a different target
produces byte-identical bytes (§ 9).

The G-01 traceability anchor for this workflow closes here: the
ROADMAP entry `F-WF-DORA-SELFASSESS` names this cookbook, the
shipped CACAO source, the compiled targets, and the outbound overlay
as the deliverables that discharge whole-Chapter DORA Chapter II
coverage on the content axis.

## 4. CACAO topology

The workflow is a linear four-step lifecycle. Each action step
carries the CACAO I/O contract (`in_args` / `out_args`) plus
`x_secops_ng` reference bundles pinning the OSCAL control anchors
(CA-2 / CA-7), the D3FEND technique (D3-OAM on the score step), and
the OCSF telemetry class the step emits.

| Step suffix | Step                             | Discipline                                                                                                                                                                                             | Status         |
|-------------|----------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | dora_ict_risk_selfassess_start   | edge wiring only — no body                                                                                                                                                                             | n/a            |
| `…000002`   | collect_section_evidence         | read the operator's evidence store for the current self-assessment window and pull every evidence record whose producing playbook is one of the section-anchored playbook set; set `__section_atoms__` (fixed five-atom set) and `__evidence_set_id__` | adapter-bound  |
| `…000003`   | map_evidence_to_sections         | bind each collected evidence record to (i) the section atom it discharges, (ii) the producing playbook slug, and (iii) the SecOps-NG content-model overlay refs that carry across; set `__section_mapping__` | adapter-bound  |
| `…000004`   | score_per_section_coverage       | score each of the five sections against the operator's documented four-bucket coverage rubric; set `__section_scoring__`                                                                                | adapter-bound  |
| `…000005`   | report_attestation               | compose the dated DORA Chapter II ICT risk management self-assessment attestation record; set `__attestation_id__`                                                                                       | adapter-bound  |
| `…000006`   | dora_ict_risk_selfassess_end     | edge wiring only — no body                                                                                                                                                                             | n/a            |

Sequencing is `on_completion` end-to-end — the playbook is linear,
with no conditional branching at the workflow layer. An unbound
evidence record surfaced at `map_evidence_to_sections` does not
branch the workflow; it lands as a flagged entry on the attestation
record under the unbound-evidence field. An empty per-section
sub-set is carried through explicitly rather than dropped: the
scoring step records `absent-uncovered` for that section, and the
attestation records the gap.

## 5. Playbook variables

The playbook operates on a small set of workflow-scope variables.
`__assessment_window__` is external — supplied by the operator's
scheduler, on-demand trigger, or supervisory-authority request at
lifecycle entry. The remainder are set by downstream steps as the
run progresses.

| Variable                  | External? | Set by                        | Purpose                                                                                                                                                                                             |
|---------------------------|-----------|-------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `__assessment_window__`   | yes       | operator-supplied             | reference to the self-assessment cohort the run reports against (Article 6(5) annual review reference, post-major-incident review reference, supervisory-authority request reference)                |
| `__section_atoms__`       | no        | `collect_section_evidence`    | fixed five-atom set (`dora:art-6-framework`, `dora:art-7-systems-protocols-tools`, `dora:art-8-identification`, `dora:art-10-detection`, `dora:art-11-response-recovery`) resolved from `mappings.yaml` |
| `__evidence_set_id__`     | no        | `collect_section_evidence`    | opaque identifier of the per-section evidence set the collect step composed for the window; the map / score / report steps read against this set                                                    |
| `__section_mapping__`     | no        | `map_evidence_to_sections`    | per-record binding to (section atom, producing playbook slug, content-model overlay refs); unbound records are recorded as unbound and flagged                                                       |
| `__section_scoring__`     | no        | `score_per_section_coverage`  | per-section bucket assignment (`present-and-current` / `present-but-stale` / `absent-with-declared-exception` / `absent-uncovered`) plus the operator's freshness thresholds applied                 |
| `__attestation_id__`      | no        | `report_attestation`          | opaque identifier of the emitted attestation record; derives from `SHA-256(workflow_id|execution_id|captured_at)` and is target-agnostic (§ 9)                                                       |

The four-bucket coverage rubric is the invariant that pins the
scoring semantics of the whole roll-up:

- **`present-and-current`** — at least one evidence record in the
  window whose `captured_at` is inside the operator's declared
  freshness threshold for the section. The section is covered.
- **`present-but-stale`** — evidence records exist but the freshest
  is past the declared freshness threshold. The section is
  historically covered; the coverage is not current.
- **`absent-with-declared-exception`** — no evidence records in the
  window but the operator maintains a documented, dated exception
  under their Article 6 ICT risk management framework naming the
  compensating measure. The section is not covered by the primary
  playbook set, but the compensating measure is on the ledger.
- **`absent-uncovered`** — no evidence records in the window and no
  declared exception. This is the gap the self-assessment surfaces.

The rubric is documented once in the operator's ICT risk management
framework; the playbook applies it, it does not author it.

## 6. Adapter-bound surfaces

Five operator-owned surfaces sit behind adapter shims in the
lifecycle. The framework describes the CACAO contract each surface
writes into; it does not ship the surface.

### 6.1 Evidence store

`collect_section_evidence` reads the operator's addressable evidence
repository against the section-anchored producing-playbook set for
the current window. The evidence store's canonical requirement is
that each record carry **producing-playbook attribution** — the
originating playbook slug (e.g. `asset_management`, `vuln_intake`,
`detection_engineering`, `incident_management`, `backup_recovery`)
— so the downstream map step can bind the record to the correct
section atom via the inbound overlay under `content/mappings/dora/`.
The framework ships **no default evidence store**: the operator's
store may be a Postgres table, an S3-compatible object store on EU
sovereign infrastructure, a Delta Lake on a data-plane the operator
controls, or a compliance-platform export surface. What the
framework declares is the read-only contract and the per-record
attribution invariant.

### 6.2 Coverage rubric

`score_per_section_coverage` applies the operator's documented four-
bucket rubric plus per-section freshness thresholds. The rubric is
authored once in the operator's ICT risk management framework (under
Article 6) and referenced by the score step; the framework describes
the four buckets and the per-section freshness-threshold shape, it
does not fix threshold values. Typical operator practice sets the
freshness threshold at one cadence period for each section (annual
for framework-shaped sections, per-quarter for operational sections
such as detection and response), but the value is operator-owned.

### 6.3 Declared-exception register

`score_per_section_coverage` reads the operator's dated register of
Article 6 ICT-risk-management-framework exceptions to distinguish
`absent-with-declared-exception` from `absent-uncovered`. Each entry
in the register names (i) the section atom the exception covers,
(ii) the compensating measure, (iii) the dated review horizon after
which the exception is re-evaluated. The register is operator-owned;
the framework declares the read shape and the
`absent-with-declared-exception` bucket that reads against it.

### 6.4 Self-assessment cadence surface

The surface `__assessment_window__` names against — the operator's
cadence configuration, post-major-incident trigger surface, and
supervisory-authority request handler. The framework declares the
string-typed external variable; the operator's scheduler wires the
cadence (cron-workflow on Temporal, a Cron node on n8n, a scheduled
thread launcher on LangGraph) and threads the window reference
through. The post-major-incident trigger typically wires to the
operator's `incident_management` runtime: on classification of an
ICT-related incident as major under Article 18, the incident
handler enqueues a self-assessment run against the incident
reference window.

### 6.5 Attestation sink

`report_attestation` publishes the emitted attestation record into
the operator's evidence store as the durable audit-evident artifact.
The sink is typically the same evidence store the collect step reads
against, though the write path is separate — the attestation record
is a first-class evidence record with its own producing-playbook
slug (`dora_ict_risk_selfassess`) so a future run's
`collect_section_evidence` step against the same store surfaces
prior attestations under the whole-Chapter effectiveness axis.

## 7. Regulatory anchors

**DORA — Regulation (EU) 2022/2554.** The regulation prescribes the
whole-Chapter II ICT risk management surface, the Article 6(5)
annual review cadence (plus the post-major-incident review trigger),
and the Chapter IV supervisory posture the self-assessment
discharges into. Inbound anchors live under `content/mappings/dora/`
— one file per section atom (`article-6.yaml`, `article-7.yaml`,
`article-8.yaml`, `article-10.yaml`, `article-11.yaml`). Each
backlinks `playbook.dora_ict_risk_selfassess@v1` as the whole-
Chapter roll-up discharge. The JC RTS on the ICT risk-management
framework (Commission Delegated Regulation (EU) 2024/1774) sets the
detailed substance for the framework the roll-up attests coverage
of; the RTS is referenced from the operator's framework
documentation, not embedded in the playbook.

**OSCAL controls** — from
[`content/playbooks/dora_ict_risk_selfassess/mappings.yaml`](../../content/playbooks/dora_ict_risk_selfassess/mappings.yaml):

- **CA-2** *(Control Assessments)* — anchors the playbook end-to-
  end as the control-assessment capability. CA-2 requires the
  operator to develop, review, and approve a control assessment
  plan, assess the controls in the system to determine the extent
  to which they are implemented correctly, operating as intended,
  and producing the desired outcome with respect to meeting
  established security and privacy requirements, and produce a
  control assessment report. The self-assessment lifecycle
  composes the per-section evidence set, maps records to section
  atoms, scores coverage, and emits the dated attestation record
  that is the audit-evident report CA-2 reviewers consume.
- **CA-7** *(Continuous Monitoring)* — covers the collect,
  score, and report steps. CA-7 demands ongoing monitoring of
  security controls and reporting of the security state to
  designated officials. The Article 6(5) annual review cadence is
  the financial entity's continuous-monitoring discharge on the
  DORA Chapter II control surface specifically: per-section
  evidence is collected on the documented cadence, coverage is
  scored against the documented rubric, and the dated attestation
  record is the audit-evident report continuous-monitoring
  reviewers consume.

**MITRE D3FEND v1.0.0** — `D3-OAM` *Operational Activity
Mapping* is selected on `score_per_section_coverage` as the
closest-fitting defensive technique for the coverage-rubric
application discipline the step discharges: mapping the collected
per-section evidence set onto the operator's documented rubric is
the operational-activity-mapping discipline D3-OAM names — the
mapping of operator activities and evidence onto a documented
model of the obligations the operator must discharge. The other
three action steps carry no D3FEND technique: the workflow is a
whole-Chapter discharge discipline for a supervisory-visible
control surface, not a runtime countermeasure against an
adversary behaviour.

**OCSF v1.3.0** — one class binding. **API Activity** (class_uid
6003, category Application Activity), direction `both`. Consumed at
the collect and map / score steps (read calls against the
operator's evidence store and against the SecOps-NG content-model
overlay); emitted at the report step (the write call publishing the
dated attestation record to the operator's evidence store).

**Producing playbook set.** The collect step reads against the
section-anchored producing-playbook set enumerated on
`content/playbooks/dora_ict_risk_selfassess/mappings.yaml` under the
`dora` block:

- **Art. 6 — framework.** `infra_posture_management` posture-
  evidence stream plus the operator's governance documentation
  upstream of the playbook set (the framework itself is authored
  outside the playbook set; the roll-up carries the governance
  reference).
- **Art. 7 — systems, protocols, tools.**
  `infra_posture_management`, `patch_management`,
  `crypto_posture_management` posture streams covering the
  currency and reliability of the ICT systems and their associated
  protocols and tools.
- **Art. 8 — identification.** `asset_management` inventory-delta
  stream plus the identification-focused slice of
  `infra_posture_management` (continuous identification of ICT
  risk sources and the ICT-asset inventory the identification
  depends on).
- **Art. 10 — detection.** `alert_triage`,
  `detection_engineering`, `threat_intel_ingest` detection and
  triage streams (mechanisms to promptly detect anomalous
  activities, including ICT network-performance issues and
  ICT-related incidents).
- **Art. 11 — response and recovery.** `incident_management`,
  `ransomware_containment`, `backup_recovery` response and
  recovery streams (ICT business continuity policy, response and
  recovery plans, backup policies, restoration procedures).

## 8. Per-target hand-off

The step outline above is the portable description all three
compilers read against. n8n compiles it into a linear six-node
workflow (`manualTrigger` + four `set` nodes + `noOp`); Temporal
compiles it into a workflow with four activity invocations chained
by `await`; LangGraph compiles it into a `StateGraph` with six
nodes and unconditional-edge topology.

### 8.1 n8n — Set nodes over the four-step lifecycle

`examples/n8n/dora_ict_risk_selfassess/workflow.n8n.json` carries the
CACAO topology as n8n nodes (one `manualTrigger`, four `set` nodes,
one `noOp` terminal). Node ids preserve the CACAO step ids verbatim.
Each action node emits a `n8n-nodes-base.set` carrying the CACAO
I/O contract as editable assignment rows plus the `x_secops_ng`
reference bundles.

Operators bind the Set rows to their connectors:

- `collect_section_evidence` → the operator's evidence-store
  connector (Postgres node against an evidence-record table;
  HTTP Request node against an evidence-store API; S3 node
  against a sovereign-hosted object store carrying the per-
  producing-playbook evidence prefix). Writes `__section_atoms__`
  from the fixed five-atom set declared in `mappings.yaml`, and
  `__evidence_set_id__` as the durable identifier of the pulled
  set.
- `map_evidence_to_sections` → the mapping surface (Function node
  applying the section-anchor overlay under
  `content/mappings/dora/` over the collected records; or an
  HTTP Request node against a shared classifier engine). Writes
  `__section_mapping__`.
- `score_per_section_coverage` → the rubric-application surface
  (Function node evaluating each section against the operator's
  documented four-bucket rubric plus freshness thresholds, reading
  the declared-exception register for the `absent-with-declared-
  exception` bucket). Writes `__section_scoring__`.
- `report_attestation` → the attestation-assembler and sink
  (Function node materialising the attestation record against the
  operator's template, followed by a Postgres / HTTP / S3 write
  node against the attestation-sink surface). Writes
  `__attestation_id__`.

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/dora_ict_risk_selfassess/regenerate.sh
```

Equivalent direct invocation:

```sh
PYTHONPATH=. python -m tools.compile \
    content/playbooks/dora_ict_risk_selfassess/playbook.cacao.json \
    --target n8n \
    --out examples/n8n/dora_ict_risk_selfassess/workflow.n8n.json
```

The byte-parity golden test under
`tests/examples/n8n/dora_ict_risk_selfassess/test_golden.py` reruns
the same pipeline and fails if the committed artifact drifts.

### 8.2 Temporal — activities over the four-step lifecycle

`examples/temporal/dora_ict_risk_selfassess/workflow.temporal.py`
carries the CACAO topology as a Temporal workflow with one activity
per action step. `__assessment_window__` is threaded through the
workflow signature as an argument — the evidence-store read, the
mapping, and the scoring all read against that external playbook-
scoped input rather than from a worker-local scope. A worker restart
mid-workflow re-hydrates the same window scope against Temporal's
event-history replay contract, so a re-emission of the attestation
record produces byte-identical `__attestation_id__` bytes.

Operators bind the activity bodies to real connectors:

- `collect_section_evidence` — the evidence-store read activity;
  the reference binding queries the operator's store for records
  in the window whose producing-playbook slug is in the section-
  anchored set, stamps `__evidence_set_id__`, and resolves
  `__section_atoms__` from `mappings.yaml`.
- `map_evidence_to_sections` — the mapping activity applying the
  inbound overlay.
- `score_per_section_coverage` — the rubric-application activity.
  Time-boxed against the operator's self-assessment deadline;
  unscored sections are treated as `absent-uncovered` for the
  whole-Chapter roll-up.
- `report_attestation` — the attestation-assembly and sink
  activity. The `__attestation_id__` derivation happens at the
  primitive layer (not the compile layer) — the activity computes
  the hash and writes the record to the operator's declared sink.

To regenerate the compiled artifact from the repo root:

```sh
./examples/temporal/dora_ict_risk_selfassess/regenerate.sh
```

The byte-parity golden test under
`tests/examples/temporal/dora_ict_risk_selfassess/test_golden.py`
reruns the emitter and fails if the committed artifact drifts.
Activity bodies remain `NotImplementedError` stubs by design in
the shipped example; the operator supplies the bindings.

### 8.3 LangGraph — nodes and state over the four-step lifecycle

`examples/langgraph/dora_ict_risk_selfassess/graph_spec.json` carries
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

- `collect_section_evidence` → evidence-store read tool.
- `map_evidence_to_sections` → mapping tool applying the inbound
  overlay.
- `score_per_section_coverage` → rubric-application tool + optional
  agentic-extension hook. The agentic-extension surface is where an
  operator running a LangGraph agent can invoke an LLM-assisted
  reviewer against the scoring output — e.g. to draft the natural-
  language justification for an `absent-with-declared-exception`
  section under the operator's compensating-measure narrative — as
  a supplement to the deterministic bucket assignment, not a
  replacement.
- `report_attestation` → attestation-assembly and sink tool.

To regenerate the compiled artifacts from the repo root:

```sh
./examples/langgraph/dora_ict_risk_selfassess/regenerate.sh
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

The reason for the target-agnostic anchor is regulatory, not
stylistic. The Chapter IV supervisory posture is a posture about
the *financial entity's whole-Chapter coverage*, not about the
*orchestrator that runs the assessment*. A financial entity that
migrates from n8n to Temporal (or runs two windows concurrently on
different targets during a migration) must be able to consolidate
their attestation ledger without dedup drift; the framework refuses
the drift-shape by construction.

## 10. Exporting results as supervisory-reporting evidence

Under DORA Chapter IV, the financial entity is expected to produce,
on competent-authority request, the current state of their Chapter
II coverage. Three fields on the emitted attestation record are the
supervisory-facing surface:

- **`assessment_window`** — the identifier from
  `__assessment_window__`. Supervisory correspondence quotes this
  reference so the financial entity's response can be joined
  against the competent-authority request record (or, in the
  post-major-incident case, against the ICT-related incident
  report submitted under Chapter III).
- **`section_atoms[].bucket`** — the per-section bucket assignment
  from the four-bucket rubric. The supervisory reader learns, per
  section: covered and current / covered but stale / covered by
  declared compensating measure / uncovered.
- **`roll_up_verdict`** — the whole-Chapter verdict aggregated
  from the five per-section buckets. The verdicts are:
  - **`all-present-and-current`** — every section covered and
    current.
  - **`mixed-with-declared-exceptions`** — every section covered
    or exempt with a documented compensating measure; no
    uncovered gaps.
  - **`partial-coverage-with-gaps`** — one or more sections in
    `absent-uncovered`; the attestation surfaces the gap.
  - **`uncovered`** — no coverage on any section (the initial-
    state or reset-state; typically only observed on first-run
    for a new financial entity).

The attestation record is the audit-evident artifact retained on
the operator's evidence store. Wiring it into the competent-
authority-facing envelope is a financial-entity responsibility: the
framework does not ship the per-authority submission channel (each
national competent authority under DORA publishes its own reporting
portal, submission format, and reference-number allocation). What
the framework produces is the canonical, dated, byte-deterministic
record the entity's submission wraps.

The `absent-uncovered` entries on the attestation are the leading
signal for the operator's plan-of-action authoring surface, which
lives upstream of the playbook in the operator's ICT risk management
framework. OSCAL CA-5 (Plan of Action and Milestones) is not pinned
inside this workflow: the self-assessment surfaces the gap, the
operator's plan-of-action surface closes it. The two are linked by
convention (the attestation record's assessment-window reference
joins to the plan-of-action's coverage entry) but not by CACAO
topology.

## 11. Playbook chain — where dora_ict_risk_selfassess sits

The self-assessment lifecycle interacts with the producing playbooks
on the operator's substrate. The interactions are documented at the
CACAO source and in `mappings.yaml`, and are worth calling out in a
cookbook context so a reader can situate the workflow:

- **Producing playbooks (§ 7).** The collect step reads their
  emitted evidence; the self-assessment does not itself discharge
  any of the five Chapter II sections. Each producing playbook
  remains the audit-evident discharge on its own axis. The self-
  assessment is the roll-up, not the replacement.
- **`incident_management` — post-major-incident review trigger.**
  A DORA Article 18 major-incident classification is the direct
  trigger for a post-major-incident self-assessment run. Practice
  is to have `incident_management` enqueue a self-assessment run
  against a fresh `__assessment_window__` on major classification,
  so the supervisory-facing posture reflects the current state
  after the material change the incident revealed. The two
  playbooks are separate — the incident report submitted under
  Chapter III is distinct from the whole-Chapter self-assessment
  attestation — but the enqueue is a first-class integration
  point.
- **`nis2_self_assessment` — a parallel whole-framework roll-up.**
  A financial entity that is *also* an essential/important entity
  under NIS2 discharges both roll-ups on their respective cadences.
  The two playbooks are deliberately separate: NIS2 Art. 21(2)
  keys on ten sub-clauses; DORA Chapter II keys on five section
  atoms. Evidence records can serve both roll-ups where a
  producing playbook is anchored in both regimes; the attestation
  records are separate artifacts submitted into separate
  supervisory channels.
- **The operator's ICT risk management framework under Article
  6.** The self-assessment reads the operator's coverage rubric
  and the declared-exception register from documentation authored
  under the framework. The playbook applies the framework; it
  does not author it.

## 12. What this cookbook deliberately does not cover

- **The evidence-store schema.** The per-record shape, indexing,
  and retention posture are operator-owned. The framework describes
  the read contract and the per-record attribution invariant; it
  does not ship the store.
- **The coverage rubric and freshness thresholds.** The four
  buckets are named; the per-section freshness threshold values
  are operator-owned and documented in the operator's ICT risk
  management framework under Article 6.
- **The declared-exception register.** The register shape is
  operator-owned. The framework declares the read shape and the
  `absent-with-declared-exception` bucket that reads against it.
- **The self-assessment cadence.** The Article 6(5) annual review
  interval is fixed by the regulation; the operator's on-demand
  interim cadence, if any, lives in the operator's continuous-
  monitoring documentation. OSCAL PM-31 (Continuous Monitoring
  Strategy) sits upstream of the playbook; the workflow applies
  the cadence, it does not schedule it.
- **The attestation-record template.** The evidence schema for
  the attestation record is anchored per compile target on the
  emitter side; the operator-facing rendering template (a PDF,
  a Confluence page, a compliance-platform record) is operator-
  owned and sits downstream of the write to the attestation
  sink.
- **The competent-authority submission channel.** Each national
  competent authority under DORA publishes its own Chapter IV
  submission surface (per-authority form, per-authority
  reference-number allocation, per-authority channel of record).
  The framework produces the attestation record; the entity wraps
  it into the per-authority envelope.
- **The plan-of-action authoring for uncovered sections.** OSCAL
  CA-5 (Plan of Action and Milestones) sits upstream of the
  playbook in the operator's ICT risk management framework. The
  self-assessment surfaces the gap; the plan-of-action surface
  closes it.
- **The Article 19 major-incident report itself.** The DORA
  major-incident reporting artifact under Chapter III is a
  separate playbook (`dora_art19_report`, when shipped) with its
  own dedicated cookbook entry. The DORA whole-Chapter II
  self-assessment is triggered *by* a major-incident
  classification via the post-major-incident review; it does not
  itself compose the incident report.
- **NIS2 and CRA cross-regime attestation.** The NIS2 Art. 21(2)
  whole-Article roll-up is discharged by the sibling
  `nis2_self_assessment` playbook. CRA Annex I is product-by-
  product manufacturer scope, not an operator-side self-
  assessment surface. Cross-regime entries are recorded as
  reviewed skips under `content/mappings/{nis2,cra}/_orphan_skip.yaml`
  rather than as cross-pins.

## 13. Community contribution

Improvements to this walkthrough — clarifications, worked
examples, additional regulatory-reference tightening — are welcome
via the community contribution flow described in
[`CONTRIBUTING.md`](../../CONTRIBUTING.md). The CACAO source, the
compiled examples, and the byte-parity goldens are the source of
truth; the cookbook is the connective narrative and evolves as the
playbook set around it evolves.

## 14. References

- OASIS CACAO v2.0 specification.
- DORA — Regulation (EU) 2022/2554, Chapter II (Articles 6 to
  14) ICT risk management; Article 6(5) annual review of the ICT
  risk-management framework and the post-major-incident review
  trigger; Article 18 major-incident classification; Chapter IV
  (supervision and enforcement).
- Commission Delegated Regulation (EU) 2024/1774 — JC RTS on the
  ICT risk-management framework and simplified ICT risk-management
  framework.
- Commission Delegated Regulation (EU) 2024/1772 — JC RTS on the
  criteria for the classification of ICT-related incidents and
  cyber threats as major.
- NIST SP 800-53 Rev. 5 — CA-2 (Control Assessments), CA-7
  (Continuous Monitoring), PM-31 (Continuous Monitoring Strategy).
- MITRE D3FEND v1.0.0 — D3-OAM Operational Activity Mapping.
- OCSF v1.3.0 — API Activity (class_uid 6003) event class.
