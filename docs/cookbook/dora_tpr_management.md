# dora_tpr_management — cookbook walkthrough

Operator-side ICT third-party risk management lifecycle a DORA-in-
scope financial entity runs against every ICT third-party service
provider it contracts with — from pre-contractual risk assessment
through register maintenance and periodic re-scoring to a documented
exit — to produce the audit-evident chain the Chapter IV supervisor
reads as the Chapter V discharge. The `playbook.dora_tpr_management@v1`
CACAO playbook operates the onboarding-to-exit chain across the five
steps that pin the DORA Article 28 / 30 obligation set: score the
candidate provider against the operator's documented pre-contractual
risk-assessment rubric, verify the negotiated contract carries the
Article 30(2)/(3) closed clause set, compose and publish the Article
28 register-of-information row, re-score criticality on the operator's
documented periodic-review cadence with the runtime supply-chain-
evidence stream folded in, and emit the dated Article 28(8) exit-
strategy attestation on a documented trigger.

The playbook is the **portable description of the DORA Chapter V
contract-lifecycle spine**. It does not choose the operator's evidence
store, does not embed the operator's pre-contractual risk-assessment
rubric, does not author the Article 30 clause-shape rubric, does not
schedule the periodic-review cadence, and does not ship the register-
row template. It describes the workflow shape the operator's stack
should run so the five-step lifecycle (onboarding → clause-check →
register-entry → periodic-review → exit-assessment) is auditable,
replayable, and restart-safe — as a shipped Digital Commons artifact
for the EU financial-services community.

Distinct from `playbook.supply_chain_security@v1` (the runtime
supply-chain-signal spine anchored on NIS2 Article 21(2)(d) — SBOM
correlation, supplier-attestation lookup, per-execution supply-chain-
evidence emission) and from
`playbook.contractual_obligations_tracker@v1` (the per-obligation
clause-attestation cadence across every declared contractual
obligation regardless of counterparty type): this walkthrough covers
the **whole-lifecycle third-party governance workflow the DORA register
anchors**, keyed on the five DORA Chapter V lifecycle atoms rather
than on the runtime supply-chain signal or the per-obligation
attestation cadence. Also distinct from
`playbook.dora_ict_risk_selfassess@v1` (the whole-Chapter II ICT risk
management self-assessment roll-up on Articles 6/7/8/10/11): DORA
Chapter V third-party risk is deliberately out of scope for the
Chapter II roll-up, and this playbook is the dedicated Chapter V
discharge.

This walkthrough wires the shipped playbook through all three
reference compile targets (n8n, Temporal, LangGraph) and shows where
each lifecycle stage — onboarding, clause-check, register-entry,
periodic-review, exit-assessment — lands in each. Adapter bodies
(critical-or-important-function register, pre-contractual risk-
assessment rubric, contract repository, Article 30 clause-shape
rubric, register sink, runtime supply-chain-evidence source, exit-
strategy discipline) are declared as adapter-bound surfaces the
operator wires; the shipped CORE artifact lands the byte-parity
emitter fan-out under `examples/{n8n,temporal,langgraph}/dora_tpr_management/`
and the G-03 cross-target parity test.

> The framework is framework-agnostic by construction. n8n /
> Temporal / LangGraph are *three of three* reference targets;
> the same CACAO source compiles into all of them. Operators
> run whichever target already lives in their stack.

## 1. Why this matters

DORA Chapter V (Articles 28 to 44) places ICT third-party risk
management under the same accountability envelope as the Chapter II
ICT risk management framework: the management body of a financial
entity remains ultimately responsible for the risks the entity carries
through its ICT third-party service providers, and Chapter IV places
the supervisory posture in the hands of the competent authority.
The five obligation atoms this playbook operates against are:

- **Art. 28(4)** — pre-contractual risk assessment. Before entering
  a contractual arrangement with an ICT third-party service provider,
  the financial entity assesses the risks the arrangement introduces,
  keyed on function criticality, sub-outsourcing chain, data-location,
  and concentration exposure.
- **Art. 30(2)/(3)** — key contractual provisions. Every ICT third-
  party contract must carry a closed clause set (service description,
  data-processing locations, exit-strategy obligations, audit rights,
  termination rights, sub-contracting conditions, service-level
  descriptions, insolvency and resolution provisions). Article 30(3)
  adds heightened clauses for contracts supporting critical or
  important functions.
- **Art. 28(3)** — register of information. The financial entity
  maintains a register of information on all its contractual
  arrangements with ICT third-party service providers, on the shape
  Commission Implementing Regulation (EU) 2024/2956 (ITS on the
  standard templates for the register of information) fixes.
- **Art. 28(1)(a)** — monitoring cadence. The financial entity
  monitors the ICT third-party risk of its arrangements on a
  documented cadence, so that the register reflects the current
  criticality and current runtime posture, not the position at
  contract signature.
- **Art. 28(8)** — exit strategy. For contracts supporting critical
  or important functions, the financial entity maintains a
  documented exit strategy and discharges it on election, provider
  failure, contractual termination, provider insolvency, or
  regulatory direction.

A financial entity that maintains a per-provider spreadsheet plus a
folder of signed contracts still owes a coherent, dated, replayable
lifecycle when the competent authority asks *how did you decide this
provider was fit for use, where does the current contract carry the
Article 30 clause set, when did you last re-score criticality, and
what is your documented exit posture?* This playbook is that
lifecycle. Wiring the five steps into an orchestration surface that
survives worker restart, records each step as durable evidence, and
closes on a dated exit attestation is the audit-evident discharge of
the Chapter V obligation set; assembling the answer from four
spreadsheets and a mailbox at the request-response deadline is not.

## 2. When to run each step

The lifecycle is not a single-shot workflow: the five steps land on
different cadences and different operator triggers.

- **Onboarding risk assessment.** Fires once per candidate ICT
  third-party service provider, before contract signature. The
  operator's procurement or vendor-onboarding surface enqueues the
  run against `__provider_handle__` and `__function_supported__`.
- **Contractual provisions check.** Fires once per negotiated
  contract instance, before signature. The operator's contract-
  management surface enqueues the run against `__contract_ref__`
  once the counterparty has returned the negotiated draft. Re-runs
  are enqueued on every amendment.
- **Register entry.** Fires immediately after both the risk
  assessment and the clause check have closed successfully. The
  register row is content-addressed against the derived
  `artifact_id`, so a replay of the same window re-emits byte-
  identical bytes — the register is idempotent by construction.
- **Periodic review.** Fires on the operator's documented review
  cadence (`__review_window__`). Article 28(1)(a) fixes the
  monitoring obligation without fixing the interval; typical
  operator practice is quarterly for critical-function providers
  and annually for the remainder. A review is also enqueued on
  material change signalled by the operator's contract-management
  surface (amendment, sub-outsourcing declaration, function
  reassignment) and on drift signalled by the runtime supply-
  chain-evidence stream (a `watch` or `confirmed_compromise`
  verdict from `playbook.supply_chain_security@v1` against the
  provider handle).
- **Exit assessment.** Fires on a documented `__exit_trigger__` —
  operator election, periodic-review failure, contractual
  termination, provider insolvency, or regulatory direction. Never
  auto-invoked: the periodic-review step surfaces a criticality-
  threshold cross for the operator's governance surface to
  consume, but the exit decision stays on the operator.

The workflow is idempotent against the derivation inputs at each
step: two register-entry runs on the same
`(workflow_id, execution_id, captured_at)` triple re-derive an
identical `__register_row_id__` that is byte-identical across
compile targets, and the same holds for `__exit_attestation_id__`
on the exit-assessment step (§ 9).

## 3. Source of truth

```
content/playbooks/dora_tpr_management/
├── README.md                    # workflow-local overview and status
├── playbook.cacao.json          # canonical CACAO v2 source (playbook.dora_tpr_management@v1)
└── mappings.yaml                # outbound OSCAL / OCSF / DORA overlay

content/mappings/dora/
├── article-19-and-28.yaml       # dora:art-28-third-party-register inbound anchor
└── article-30.yaml              # dora:art-30-contractual-clauses (Art. 30 axis)
```

The CACAO source is canonical. The five-step lifecycle (one `start`,
five `action` steps, one `end`) is the deterministic policy the
playbook *means*. The three worked examples under
`examples/{n8n,temporal,langgraph}/dora_tpr_management/` are the same
playbook compiled into three orchestrator idioms. The dated register
row and the dated exit attestation each execution emits are anchored
by a target-agnostic `artifact_id` derivation so a replay under a
different target produces byte-identical bytes (§ 9).

The G-01 traceability anchor for this workflow closes here: the
ROADMAP entry `F-WF-DORA-TPR` names this cookbook, the shipped CACAO
source, the compiled targets, and the outbound overlay as the
deliverables that discharge DORA Chapter V third-party risk on the
content axis.

## 4. CACAO topology

The workflow is a linear five-step lifecycle. Each action step
carries the CACAO I/O contract (`in_args` / `out_args`) plus
`x_secops_ng` reference bundles pinning the OSCAL control anchors
(SR-3 supply-chain controls-and-processes, SR-6 supplier assessments-
and-reviews) and the OCSF telemetry class each step reads or emits.

| Step suffix | Step                             | Discipline                                                                                                                                                                                                                                              | Status         |
|-------------|----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | dora_tpr_management_start        | edge wiring only — no body                                                                                                                                                                                                                              | n/a            |
| `…000002`   | onboarding_risk_assessment       | score the candidate provider against the operator's documented pre-contractual risk-assessment rubric on the four axes Art. 28(4) names (function criticality, sub-outsourcing chain, data-location, concentration exposure); set `__criticality_determination__` and `__risk_assessment_ref__` | adapter-bound  |
| `…000003`   | contractual_provisions_check     | verify the negotiated contract carries the Art. 30(2)/(3) closed clause set (per-clause status `present` / `present_with_deviation` / `absent`); set `__clause_check_ref__`                                                                              | adapter-bound  |
| `…000004`   | register_entry                   | compose and publish the Art. 28 register-of-information row for the provider on the current window, joined to the risk-assessment block and the clause-check block; set `__register_row_id__`                                                            | adapter-bound  |
| `…000005`   | periodic_review                  | re-read the register row on the operator's documented review cadence (`__review_window__`) and re-score criticality against the current runtime supply-chain-evidence stream (`__runtime_supply_chain_evidence_ref__`); set `__periodic_review_ref__`      | adapter-bound  |
| `…000006`   | exit_assessment                  | on a documented `__exit_trigger__`, emit the dated Art. 28(8) exit-strategy attestation joining the register row, the risk-assessment block, the clause-check block, and the periodic-review block; set `__exit_attestation_id__`                        | adapter-bound  |
| `…000007`   | dora_tpr_management_end          | edge wiring only — no body                                                                                                                                                                                                                              | n/a            |

Sequencing is `on_completion` end-to-end — the playbook is linear,
with no conditional branching at the workflow layer. An `absent`
clause status at `contractual_provisions_check` does not branch the
workflow: the register row is still composed (the register carries an
entry for every ICT third-party service provider under contract per
Article 28) and is flagged clause-incomplete so the operator's
governance surface can drive the negotiation lever. A criticality
threshold cross at `periodic_review` does not auto-invoke
`exit_assessment`: the review block is emitted, and the operator's
governance surface consumes it to decide whether to invoke exit.

## 5. Playbook variables

The playbook operates on a small set of workflow-scope variables.
`__provider_handle__`, `__function_supported__`, `__contract_ref__`,
`__review_window__`, `__runtime_supply_chain_evidence_ref__`,
`__exit_trigger__`, and `__captured_at__` are external — supplied by
the operator's onboarding, contract-management, cadence, runtime, and
governance surfaces at lifecycle entry to each step. The remainder are
set by downstream steps as the run progresses.

| Variable                                  | External? | Set by                          | Purpose                                                                                                                                                                                       |
|-------------------------------------------|-----------|---------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `__provider_handle__`                     | yes       | operator-supplied               | stable operator-side ICT third-party service provider identifier in `provider.<id>@v<n>` shape; joins the register row and the runtime supply-chain-evidence stream on the same key            |
| `__function_supported__`                  | yes       | operator-supplied               | short operator-defined token naming the business or ICT function the provider supports; keys the criticality determination against the operator's critical-or-important-function register     |
| `__contract_ref__`                        | yes       | operator-supplied               | operator-side pointer to the negotiated contract instance the clause-presence check reads against                                                                                              |
| `__review_window__`                       | yes       | operator-supplied               | reference to the periodic-review window the re-scoring runs against (typically a quarter or year reference; on material change, a change-triggered reference)                                  |
| `__runtime_supply_chain_evidence_ref__`   | yes       | operator-supplied               | pointer to the runtime supply-chain-evidence artifact set `playbook.supply_chain_security@v1` has emitted against `__provider_handle__` since the last invocation                              |
| `__exit_trigger__`                        | yes       | operator-supplied               | documented trigger for the exit assessment (operator election, periodic-review failure, contractual termination, provider insolvency, regulatory direction)                                    |
| `__captured_at__`                         | yes       | operator-supplied               | RFC 3339 timestamp threaded through the register-entry and exit-assessment steps for the deterministic `artifact_id` derivation (§ 9)                                                          |
| `__criticality_determination__`           | no        | `onboarding_risk_assessment`    | bucket assignment from the operator's declared bucket set (typically `{non_critical, important, critical}` plus a supporting-critical bucket); carried onto the register row                    |
| `__risk_assessment_ref__`                 | no        | `onboarding_risk_assessment`    | pointer to the closed pre-contractual risk-assessment block (criticality-keyed, sub-outsourcing enumerated, data-location declared, concentration-exposure scored); consumed by register entry |
| `__clause_check_ref__`                    | no        | `contractual_provisions_check`  | pointer to the closed clause-presence check block (per-clause status against the Art. 30(2)/(3) closed clause set plus deviation notes); consumed by register entry                            |
| `__register_row_id__`                     | no        | `register_entry`                | opaque content-addressed identifier of the emitted register row; derives from `SHA-256(workflow_id|execution_id|captured_at)` and is target-agnostic (§ 9)                                     |
| `__periodic_review_ref__`                 | no        | `periodic_review`               | pointer to the re-scored review block (re-scored criticality, material-change record, runtime-drift verdict, next-review anchor); consumed by exit assessment                                  |
| `__exit_attestation_id__`                 | no        | `exit_assessment`               | opaque content-addressed identifier of the emitted exit attestation record; derives from `SHA-256(workflow_id|execution_id|captured_at)` and is target-agnostic (§ 9)                          |

The four-bucket criticality vocabulary is the invariant that pins the
onboarding-risk-assessment and periodic-review outputs:

- **`non_critical`** — the function the provider supports is not on
  the operator's critical-or-important-function register, the sub-
  outsourcing chain is shallow, the data-location declaration is
  within the operator's declared acceptable set, and the
  concentration exposure is below the operator's declared threshold.
- **`important`** — the function is important under the operator's
  register (below the critical bar), or a rubric axis crosses a
  medium-tier threshold (data-location includes a third country, the
  sub-outsourcing chain declares two or more hops, or concentration
  exposure crosses the medium threshold).
- **`critical`** — the function is critical under the operator's
  register, or a rubric axis crosses a high-tier threshold.
- **`supporting-critical`** — the provider supports a function
  another provider critically depends on; the criticality carry from
  the primary provider transfers onto this arrangement.

The rubric is documented once in the operator's ICT risk management
framework; the playbook applies it, it does not author it.

## 6. Adapter-bound surfaces

Seven operator-owned surfaces sit behind adapter shims in the
lifecycle. The framework describes the CACAO contract each surface
writes into; it does not ship the surface.

### 6.1 Critical-or-important-function register

`onboarding_risk_assessment` reads the operator's declared register of
the business or ICT functions that qualify as critical or important
under DORA Article 3(22) and the operator's own governance
documentation. Consumed to key the criticality determination against
the supported function (`__function_supported__`). The framework
declares the read shape (per-function id, criticality bucket, dated
review horizon); the operator's governance surface authors and
maintains the register.

### 6.2 Pre-contractual risk-assessment rubric

`onboarding_risk_assessment` applies the operator's documented rubric
with the four axes Article 28(4) names — function criticality, sub-
outsourcing chain, data-location, concentration exposure — plus the
operator's declared threshold set. The rubric is authored once in the
operator's ICT risk management framework under Chapter II (as an ICT
risk management framework element) and referenced by the onboarding
step; the framework describes the four axes and the four-bucket
criticality vocabulary, it does not fix threshold values.

### 6.3 Contract repository

`contractual_provisions_check` reads the negotiated ICT third-party
contract instance (`__contract_ref__`) against the operator's contract
repository. The framework declares the read-only contract; the store
may be a document-management system, an S3-compatible object store on
EU sovereign infrastructure, a contract-lifecycle-management platform
export surface, or a git repository of signed PDFs. What the framework
requires is that the reference resolves to a durable, addressable
contract artifact for the negotiation instance being verified.

### 6.4 Article 30 clause-shape rubric

`contractual_provisions_check` applies the operator's declared per-
clause shape for the Article 30(2)/(3) closed clause set. The rubric
fixes the clause vocabulary (service description, data-processing
locations, exit-strategy obligations, audit rights, termination
rights, sub-contracting conditions, service-level descriptions,
insolvency and resolution provisions) and the per-clause criteria the
check reads against. Article 30(3) additions (heightened clauses for
critical-or-important-function contracts) are keyed off the criticality
determination from the onboarding step so the same rubric handles both
Art. 30(2) baseline and Art. 30(3) heightened contracts.

### 6.5 Register sink

`register_entry` publishes the emitted register row into the
operator's evidence store as the durable Article 28 register-of-
information artifact. The row shape follows Commission Implementing
Regulation (EU) 2024/2956 (ITS on the standard templates for the
register of information); the operator's sink typically is the same
evidence store other Chapter II / V evidence lands in, though the
per-authority submission surface (where the register is periodically
handed to the competent authority) sits downstream.

### 6.6 Runtime supply-chain-evidence source

`periodic_review` reads the runtime supply-chain-evidence artifact
set `playbook.supply_chain_security@v1` has emitted against
`__provider_handle__` since the last invocation. The join key is the
provider handle: because both playbooks share the same
`provider.<id>@v<n>` vocabulary (F-CP-03 dependencies surface), no
re-canonicalisation is needed. A `watch` or `confirmed_compromise`
verdict from the runtime stream re-enters the DORA register on this
join.

### 6.7 Exit-strategy discipline

`exit_assessment` writes the emitted exit attestation into the
operator's declared exit-strategy discipline surface — typically the
same evidence store the register row lands in, plus (for critical-or-
important-function providers) the operator's exit-plan surface where
the transition-of-service documentation, alternative-provider
identification, and contractual-termination artifacts sit. The
framework declares the record shape; the operator's exit-plan surface
consumes it as one input among several.

## 7. Regulatory anchors

**DORA — Regulation (EU) 2022/2554.** The regulation prescribes the
Chapter V ICT third-party risk management surface, the Article 28
register-of-information obligation, the Article 30(2)/(3) closed
clause set, and the Chapter IV supervisory posture the lifecycle
discharges into. Inbound anchors live under `content/mappings/dora/`:

- `content/mappings/dora/article-19-and-28.yaml` carries the
  `dora:art-28-third-party-register` atom that backlinks
  `playbook.dora_tpr_management@v1` (alongside
  `playbook.contractual_obligations_tracker@v1` and
  `playbook.supply_chain_security@v1`) for the Article 28 register
  discipline.
- `content/mappings/dora/article-30.yaml` carries the
  `dora:art-30-contractual-clauses` atom that backlinks
  `playbook.dora_tpr_management@v1` and
  `playbook.contractual_obligations_tracker@v1` for the Article 30
  closed clause set.

**OSCAL controls** — from
[`content/playbooks/dora_tpr_management/mappings.yaml`](../../content/playbooks/dora_tpr_management/mappings.yaml):

- **SR-3** *(Supply Chain Controls and Processes)* — anchors the
  playbook end-to-end as the supply-chain controls-and-processes
  capability. SR-3 requires the organisation to establish a process
  for identifying and addressing weaknesses or deficiencies in the
  supply chain elements and processes, employ acquisition strategies
  and contract tools, and document supply-chain processes. The DORA
  Chapter V lifecycle composes the pre-contractual risk assessment,
  the Article 30 clause-presence check, the Article 28 register row,
  the periodic-review cycle, and the Article 28(8) exit-strategy
  attestation into one closed operator-side process.
- **SR-6** *(Supplier Assessments and Reviews)* — covers the
  onboarding-risk-assessment, contractual-provisions-check, periodic-
  review, and exit-assessment steps. SR-6 demands the organisation
  assess and review the supply-chain-related risks associated with
  suppliers and the services they provide, at a defined frequency.
  The DORA Article 28(1)(a) monitoring cadence, the Article 28(4)
  pre-contractual risk assessment, and the Article 28(8) exit-strategy
  discipline are the DORA-specific discharge of the same SR-6
  assessment-and-review discipline, narrowed to the ICT third-party
  service provider surface financial entities are obligated against.

**MITRE D3FEND v1.0.0** — no per-step D3FEND pin. The DORA Chapter V
contract-lifecycle steps are governance-side disciplines (pre-
contractual risk assessment, clause-presence check, register-row
composition, periodic review, exit-strategy attestation) rather than
defensive-technique discharges against the operator's deployed estate.
D3FEND v1.0.0 does not currently carry a third-party-governance
technique atom that matches these steps without stretching the
taxonomy; a subsequent extension may lift `D3-OAM` (Operational
Activity Mapping) onto the periodic-review drift-detection slice
once a documented mapping is authored upstream.

**OCSF v1.3.0** — one class binding. **API Activity** (class_uid
6003, category Application Activity), direction `both`. Consumed at
the onboarding-risk-assessment step (reads against the critical-or-
important-function register and the pre-contractual rubric), the
contractual-provisions-check step (reads against the contract
repository), and the periodic-review step (reads against the register
sink for the standing row plus the runtime supply-chain-evidence
stream). Emitted at the register-entry step (write call publishing
the Article 28 register row) and the exit-assessment step (write call
publishing the dated Article 28(8) exit-strategy attestation).

**Commission Implementing Regulation (EU) 2024/2956** — the ITS on
the standard templates for the register of information. The register-
entry step composes rows on the shape this ITS fixes; the operator's
evidence-store sink retains them as the durable Article 28 record and
the operator's supervisory-reporting surface aggregates them for
periodic submission to the competent authority.

## 8. Per-target hand-off

The step outline above is the portable description all three
compilers read against. n8n compiles it into a linear seven-node
workflow (`manualTrigger` + five `set` nodes + `noOp`); Temporal
compiles it into a workflow with five activity invocations chained
by `await`; LangGraph compiles it into a `StateGraph` with seven
nodes and unconditional-edge topology.

### 8.1 n8n — Set nodes over the five-step lifecycle

`examples/n8n/dora_tpr_management/workflow.n8n.json` carries the
CACAO topology as n8n nodes (one `manualTrigger`, five `set` nodes,
one `noOp` terminal). Node ids preserve the CACAO step ids verbatim.
Each action node emits a `n8n-nodes-base.set` carrying the CACAO
I/O contract as editable assignment rows plus the `x_secops_ng`
reference bundles.

Operators bind the Set rows to their connectors:

- `onboarding_risk_assessment` → the operator's critical-or-important-
  function register and pre-contractual rubric (Function node applying
  the four-axis rubric over the operator's declared threshold set; or
  an HTTP Request node against a shared risk-scoring engine). Writes
  `__criticality_determination__` and `__risk_assessment_ref__`.
- `contractual_provisions_check` → the contract repository read plus
  the Article 30 clause-shape rubric (Postgres / HTTP / S3 node against
  the contract store, followed by a Function node applying the per-
  clause check). Writes `__clause_check_ref__`.
- `register_entry` → the register-row composer and sink (Function node
  materialising the Article 28 register-row shape against Commission
  Implementing Regulation (EU) 2024/2956, followed by a Postgres /
  HTTP / S3 write node against the register sink). Writes
  `__register_row_id__`.
- `periodic_review` → the review-cadence reader plus the runtime
  supply-chain-evidence join (HTTP Request node against the register
  sink for the standing row, plus a Function node folding the runtime
  supply-chain-evidence stream and the operator's material-change
  declarations). Writes `__periodic_review_ref__`.
- `exit_assessment` → the exit-attestation assembler and sink
  (Function node materialising the Article 28(8) attestation record
  against the operator's template, followed by a Postgres / HTTP /
  S3 write node against the exit-attestation sink). Writes
  `__exit_attestation_id__`.

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/dora_tpr_management/regenerate.sh
```

Equivalent direct invocation:

```sh
PYTHONPATH=. python -m tools.compile \
    content/playbooks/dora_tpr_management/playbook.cacao.json \
    --target n8n \
    --out examples/n8n/dora_tpr_management/workflow.n8n.json
```

The byte-parity golden test under
`tests/examples/dora_tpr_management/test_golden.py` reruns the same
pipeline (across all three targets) and fails if the committed
artifact drifts.

### 8.2 Temporal — activities over the five-step lifecycle

`examples/temporal/dora_tpr_management/workflow.temporal.py` carries
the CACAO topology as a Temporal workflow with one activity per action
step. `__provider_handle__`, `__contract_ref__`, `__review_window__`,
`__runtime_supply_chain_evidence_ref__`, and `__exit_trigger__` are
threaded through the workflow signature as arguments — every activity
reads against workflow-scoped inputs rather than worker-local state.
A worker restart mid-workflow re-hydrates the same argument scope
against Temporal's event-history replay contract, so a re-emission of
the register row or the exit attestation produces byte-identical
`__register_row_id__` / `__exit_attestation_id__` bytes.

Operators bind the activity bodies to real connectors:

- `onboarding_risk_assessment` — the rubric-application activity.
  The reference binding reads the operator's critical-or-important-
  function register, applies the four-axis rubric, stamps
  `__criticality_determination__`, and closes the risk-assessment
  block referenced by `__risk_assessment_ref__`.
- `contractual_provisions_check` — the clause-presence activity.
  Reads `__contract_ref__` from the contract repository, applies the
  Article 30 clause-shape rubric, and closes the clause-check block.
- `register_entry` — the register-row-composition activity. The
  `__register_row_id__` derivation happens at the primitive layer —
  the activity computes the hash and writes the row to the operator's
  declared register sink.
- `periodic_review` — the re-scoring activity. Time-boxed against
  the operator's review deadline; a `watch` or `confirmed_compromise`
  verdict from `__runtime_supply_chain_evidence_ref__` is a hard
  signal onto the re-scored criticality bucket.
- `exit_assessment` — the exit-attestation-emission activity. The
  `__exit_attestation_id__` derivation happens at the primitive layer;
  the activity computes the hash and writes the attestation to the
  operator's declared exit-strategy discipline surface.

To regenerate the compiled artifact from the repo root:

```sh
./examples/temporal/dora_tpr_management/regenerate.sh
```

The byte-parity golden test under
`tests/examples/dora_tpr_management/test_golden.py` reruns the emitter
and fails if the committed artifact drifts. Activity bodies remain
`NotImplementedError` stubs by design in the shipped example; the
operator supplies the bindings.

### 8.3 LangGraph — nodes and state over the five-step lifecycle

`examples/langgraph/dora_tpr_management/graph_spec.json` carries the
CACAO topology as a target-neutral GraphSpec (nodes, edges,
conditional edges — the last being empty for this linear playbook);
`state_bindings.py` emits the `TypedDict` state and the `@tool`-
decorated action wrappers plus the agentic-extension hook.
`__provider_handle__`, `__contract_ref__`, `__review_window__`,
`__runtime_supply_chain_evidence_ref__`, and `__exit_trigger__` are
expressed as state fields threaded through node bodies, so a
checkpoint reload re-hydrates the same argument scope.

The GraphSpec `nodes` array carries only the five intermediate action
step ids; start and end sentinels are pinned structurally via `entry`
and `end_sentinel` (this is the LangGraph projection contract the
G-03 parity test asserts against — the same canonical CACAO step
space is present, in a different structural shape than n8n's node
array).

The audit-mirror sibling `_audit_mirror.py` (see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md))
carries the OTel-free durable audit trail on LangGraph runs where the
operator has not wired an OTLP collector.

Operators bind the tool bodies to real connectors:

- `onboarding_risk_assessment` → rubric-application tool + optional
  agentic-extension hook. The agentic extension is where an operator
  running a LangGraph agent can invoke an LLM-assisted reviewer
  against the risk-assessment block — e.g. to draft the natural-
  language justification for a `supporting-critical` bucket
  assignment under the operator's carry-criticality narrative — as a
  supplement to the deterministic rubric application, not a
  replacement.
- `contractual_provisions_check` → clause-check tool.
- `register_entry` → register-row-composition and sink tool.
- `periodic_review` → re-scoring tool + runtime-drift-join tool.
- `exit_assessment` → exit-attestation-emission and sink tool.

To regenerate the compiled artifacts from the repo root:

```sh
./examples/langgraph/dora_tpr_management/regenerate.sh
```

## 9. Byte-parity across compile targets — the G-03 invariant

The register row emitted at `register_entry` and the exit attestation
emitted at `exit_assessment` are each anchored by a deterministic
`artifact_id` derivation:

```
artifact_id = SHA-256(workflow_id | execution_id | captured_at)
```

The input is UTF-8, with single pipe separators and no surrounding
whitespace, and the `compile_target` is **deliberately not part of
the input**. A replay of the same
`(workflow_id, execution_id, captured_at)` triple under n8n,
Temporal, or LangGraph produces byte-identical register-row bytes and
byte-identical exit-attestation bytes.

Concretely, across the three targets:

- **n8n** — the register-row and exit-attestation emitters read
  `execution_id` from the workflow-execution scope and `captured_at`
  from `__captured_at__` threaded through the workflow. The
  `artifact_id` derivation is authored in the emitter templates, not
  in the target-specific Function nodes, so re-executions and n8n
  version changes do not drift the hash.
- **Temporal** — the register-entry and exit-assessment activities
  read `execution_id` as the Temporal workflow-run id and
  `captured_at` from a workflow-local timestamp threaded through the
  activity call, not from `datetime.utcnow()` inside the activity
  body. A history-replay re-derives the identical hash.
- **LangGraph** — the register-entry and exit-assessment tools read
  `execution_id` from the LangGraph thread/checkpoint id and
  `captured_at` from state, not from `time.time()` inside the tool
  body. A checkpoint reload re-derives the identical hash.

The reason for the target-agnostic anchor is regulatory, not
stylistic. The Chapter IV supervisory posture is a posture about the
*financial entity's register-of-information and exit-strategy
discipline*, not about the *orchestrator that runs the workflow*. A
financial entity that migrates from n8n to Temporal (or runs two
provider populations concurrently on different targets during a
migration) must be able to consolidate their register and their
exit-attestation ledger without dedup drift; the framework refuses
the drift-shape by construction.

## 10. Exporting results as supervisory-reporting evidence

Under DORA Chapter IV, the financial entity is expected to hand its
register of information to the competent authority on the ITS-fixed
cadence, and to produce the current exit-strategy posture on
supervisory-authority request. Fields on the emitted register row and
exit attestation are the supervisory-facing surface:

- **`provider_handle`** (register row + exit attestation) — the
  stable operator-side identifier. Supervisory correspondence quotes
  this reference so the financial entity's response can be joined
  against the ITS-shape register aggregation submitted to the
  competent authority.
- **`function_supported`** and **`criticality_determination`**
  (register row) — the function the provider supports and the
  criticality bucket. The supervisory reader learns, per arrangement:
  what the provider does for the entity and where it sits on the
  criticality axis.
- **`clause_check_status`** (register row) — the roll-up over the
  per-clause statuses (`complete` / `clause_incomplete`). The
  competent authority reads this against the Article 30(2)/(3)
  discharge posture.
- **`exit_trigger`** and **`exit_attestation_id`** (exit attestation)
  — the trigger under which exit was invoked and the content-
  addressed identifier of the attestation. The competent authority
  reads these against the Article 28(8) discharge for critical-or-
  important-function providers.

The register row and the exit attestation are the audit-evident
artifacts retained on the operator's evidence store. Wiring them into
the competent-authority-facing envelope is a financial-entity
responsibility: the framework does not ship the per-authority
submission channel (each national competent authority under DORA
publishes its own reporting portal, submission format, and reference-
number allocation, and the ITS on the register of information fixes
the aggregation shape rather than the per-authority handoff). What
the framework produces is the canonical, dated, byte-deterministic
record the entity's submission wraps.

The `clause_incomplete`-flagged register rows are the leading signal
for the operator's contract-renegotiation surface, which lives
upstream of the playbook in the operator's ICT risk management
framework. Analogously, the `criticality`-threshold crosses surfaced
by `periodic_review` are the leading signal for the operator's exit-
plan surface. Neither drives the exit decision automatically — exit
stays on the operator per Article 28(8) — but both are the durable
inputs the governance surface reads against.

## 11. Playbook chain — where dora_tpr_management sits

The five-step lifecycle interacts with several sibling playbooks on
the operator's substrate. The interactions are documented at the
CACAO source and in `mappings.yaml`, and are worth calling out in a
cookbook context so a reader can situate the workflow:

- **`playbook.supply_chain_security@v1` — runtime supply-chain-signal
  spine.** The `periodic_review` step joins against the runtime
  supply-chain-evidence stream this playbook emits against the
  provider handle. A `watch` or `confirmed_compromise` verdict on the
  runtime stream re-enters the DORA register on this join. The two
  playbooks are separate: `supply_chain_security` is the runtime
  spine anchored on NIS2 Art. 21(2)(d); `dora_tpr_management` is the
  contract-lifecycle spine anchored on DORA Chapter V. They share the
  `provider.<id>@v<n>` handle vocabulary (F-CP-03) so the join is
  clean.
- **`playbook.contractual_obligations_tracker@v1` — per-obligation
  clause-attestation cadence.** The `contractual_provisions_check`
  step is the DORA-specific Article 30(2)/(3) clause-presence check at
  the contract-onboarding boundary; the ongoing per-obligation
  re-attestation cadence across every declared contractual obligation
  (regardless of counterparty type) is delegated to the
  `contractual_obligations_tracker` playbook. The DORA
  `dora:art-30-contractual-clauses` inbound atom backlinks both.
- **`playbook.dora_ict_risk_selfassess@v1` — whole-Chapter II ICT
  risk management roll-up.** DORA Chapter V (third-party risk) is
  deliberately out of scope for the Chapter II self-assessment
  roll-up; the two playbooks are the Chapter II discharge and the
  Chapter V discharge respectively. A financial entity discharges
  both on their respective cadences into the same supervisory
  envelope.
- **`playbook.incident_management@v1` — DORA Article 19 major-
  incident reporting.** A material ICT-related incident against a
  third-party provider re-enters `periodic_review` on the operator's
  material-change surface; the incident report itself is a distinct
  Chapter III discharge and stays outside this workflow.
- **The operator's ICT risk management framework under Article 6.**
  The pre-contractual rubric, the criticality vocabulary, the
  clause-shape rubric, the review-cadence declaration, and the
  exit-strategy discipline are all authored under the framework the
  Chapter II lifecycle documents. The playbook applies them; it does
  not author them.

## 12. What this cookbook deliberately does not cover

- **The evidence-store schema.** The per-record shape, indexing,
  and retention posture are operator-owned. The framework describes
  the read/write contract and the per-record attribution invariant;
  it does not ship the store.
- **The pre-contractual risk-assessment rubric and threshold
  values.** The four axes are named (function criticality, sub-
  outsourcing chain, data-location, concentration exposure) and the
  four-bucket criticality vocabulary is pinned; the per-axis
  threshold values are operator-owned and documented in the
  operator's ICT risk management framework under Chapter II.
- **The Article 30 clause-shape rubric.** The Article 30(2)/(3)
  closed clause set is named; the per-clause-shape criteria are
  operator-owned. The clause-presence check applies the rubric; it
  does not author it.
- **The periodic-review cadence.** Article 28(1)(a) fixes the
  monitoring obligation; the operator's declared interval (typically
  quarterly for critical-function providers, annually for the
  remainder) lives in the operator's continuous-monitoring
  documentation.
- **The exit-strategy documentation.** Article 28(8) fixes the
  discipline; the transition-of-service plan, alternative-provider
  identification, and contractual-termination artifacts sit
  downstream of the emitted exit attestation on the operator's exit-
  plan surface.
- **The competent-authority submission channel.** Each national
  competent authority under DORA publishes its own Chapter IV
  submission surface (per-authority form, per-authority reference-
  number allocation, per-authority channel of record). The framework
  produces the register row and the exit attestation; the entity
  wraps them into the per-authority envelope.
- **The Article 29 entity-level concentration-risk assessment.**
  Article 29 is a distinct whole-portfolio concentration surface (the
  operator's whole-book view of concentration risk across every
  provider), not the per-provider onboarding view this playbook
  covers. A sibling playbook may lift Article 29 once the whole-
  portfolio scope is authored.
- **Articles 31–44 — Union oversight of critical ICT third-party
  service providers.** These articles govern ESA / Lead Overseer
  actions against critical ICT third-party service providers
  themselves and are not the operational object of an operator-side
  playbook.
- **The GDPR Article 28 data-processor arrangement axis.** GDPR
  Article 28 (data-processor arrangements) sits inside ICT third-
  party contracts where personal data is processed but is a distinct
  obligation surface discharged by a sibling GDPR-axis mapping
  closure. Cross-pinning this DORA playbook onto GDPR Art. 28 would
  conflate the DORA financial-entity ICT-service-provider surface
  with the GDPR data-processor surface.

## 13. Community contribution

Improvements to this walkthrough — clarifications, worked examples,
additional regulatory-reference tightening — are welcome via the
community contribution flow described in
[`CONTRIBUTING.md`](../../CONTRIBUTING.md). The CACAO source, the
compiled examples, and the byte-parity goldens are the source of
truth; the cookbook is the connective narrative and evolves as the
playbook set around it evolves.

## 14. References

- OASIS CACAO v2.0 specification.
- DORA — Regulation (EU) 2022/2554, Chapter V (Articles 28 to 44),
  ICT third-party risk management; Article 28 general principles for
  the use of ICT third-party service providers (register of
  information, pre-contractual risk assessment, criticality, sub-
  outsourcing, exit strategy); Article 30 key contractual provisions.
- Commission Implementing Regulation (EU) 2024/2956 — ITS on the
  standard templates for the register of information under DORA
  Article 28(9).
- NIST SP 800-53 Rev. 5 — SR-3 (Supply Chain Controls and
  Processes), SR-6 (Supplier Assessments and Reviews).
- OCSF v1.3.0 — API Activity (class_uid 6003) event class.
