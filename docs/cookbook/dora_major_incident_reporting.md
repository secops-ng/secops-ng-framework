# dora_major_incident_reporting — cookbook walkthrough

Operator-side DORA Chapter III major-ICT-related-incident reporting
lifecycle a DORA-in-scope financial entity runs against a live incident
— from the Article 18 classification decision through the three
Article 19 milestone submissions to a dated cycle-archival record — to
produce the audit-evident chain the competent authority reads on the
supervisory-review side. The `playbook.dora_major_incident_reporting@v1`
CACAO playbook operates the classification-to-archive chain across the
five steps that pin the Article 18 / 19 obligation set: evaluate the
incident against the Art. 18 classification criteria (Commission
Delegated Regulation (EU) 2024/1772), package and dispatch the
Art. 19(4)(a) initial notification (4h / 24h clock), package and
dispatch the Art. 19(4)(b) intermediate report (72h clock), package
and dispatch the Art. 19(4)(c) final report (one month after
intermediate), and compose the dated cycle-archival record referencing
the classification decision, the three submissions, the authority
acknowledgements, and any cross-regime parallel-notification chains.

The playbook is the **portable description of the DORA Chapter III
reporting spine**. It does not choose the operator's incident
register, does not embed the operator's Art. 18 classification
threshold values, does not ship the ITS submission-body template, does
not hardcode the ESA / NCA notification channel, and does not author
the archival-record schema. It describes the workflow shape the
operator's stack should run so the classification-to-archive lifecycle
is auditable, replayable, and restart-safe — as a shipped Digital
Commons artifact for the EU financial-services community.

Distinct from `playbook.incident_management@v1` (the NIS2 Art. 23-
flavoured significant-incident notification lane against the CSIRT /
competent-authority chain) and from `playbook.dora_tlpt_programme@v1`
(the DORA Chapter IV testing-programme discipline covering Art. 24
general testing requirements and Art. 26 threat-led penetration
testing): this walkthrough covers the **DORA Chapter III reporting
lifecycle keyed on Art. 19's three-milestone clock upstream of the
Art. 18 classification decision**, distinct from the NIS2-flavoured
Art. 23 reporting lane and from the DORA-flavoured Chapter IV
testing lane.

This walkthrough wires the shipped playbook through all three
reference compile targets (n8n, Temporal, LangGraph) and shows where
each lifecycle stage — detect-and-classify, notify-authority-initial,
notify-authority-intermediate, notify-authority-final,
close-and-archive — lands in each. Adapter bodies (incident register,
Art. 18 classification-decision store, ITS submission-body composer,
competent-authority notification channel, evidence-archival store,
cross-regime notification-chain surface) are declared as adapter-bound
surfaces the operator wires; the shipped CORE artifact lands the
byte-parity emitter fan-out under
`examples/{n8n,temporal,langgraph}/dora_major_incident_reporting/`
and the cross-target parity test.

> The framework is framework-agnostic by construction. n8n /
> Temporal / LangGraph are *three of three* reference targets;
> the same CACAO source compiles into all of them. Operators
> run whichever target already lives in their stack.

## 1. Why this matters

DORA Chapter III (Articles 17 to 23) places ICT-related-incident
management and major-incident reporting under the same accountability
envelope as the Chapter II ICT risk management framework: the
management body of a financial entity remains ultimately responsible
for the incidents the entity carries, and Chapter IV places the
supervisory posture in the hands of the competent authority. The four
obligation atoms this playbook operates against are:

- **Art. 18(1)** — classification decision. The financial entity
  classifies every ICT-related incident against the major-ICT-related-
  incident criteria the Commission Delegated Regulation (EU) 2024/1772
  fixes (seven primary criteria plus materiality thresholds; Art. 18(2)
  recurring-incident rule). Only incidents that cross the major bar
  enter the Art. 19 reporting cycle; incidents below the bar still
  receive a dated classification decision so the audit-evident chain
  is closed at the classification gate.
- **Art. 19(4)(a)** — initial notification. As soon as possible,
  within 4 hours of classification as major and no later than 24 hours
  from awareness of the incident, the financial entity submits the
  initial notification to the competent authority on the ITS content
  shape (Commission Implementing Regulation (EU) 2024/2956).
- **Art. 19(4)(b)** — intermediate report. Within 72 hours of
  classification as major (or earlier if regular activities have
  recovered), the financial entity submits the intermediate report —
  updated timestamps, affected functions and clients, indicators of
  compromise, and mitigation actions in flight — against the ITS
  intermediate-report template.
- **Art. 19(4)(c)** — final report. No later than one month after
  the intermediate report, the financial entity submits the final
  report carrying the root-cause analysis, final impact figures,
  completed remediation actions, lessons learned, action plan, and
  residual-risk statement against the ITS final-report template.

A financial entity that maintains a shared incident-tracking channel
plus a mailbox of manually authored regulator letters still owes a
coherent, dated, replayable lifecycle when the competent authority
asks *when did you classify this incident as major, what was your
initial notification content and dispatch time, when did the
intermediate report update the picture, what did the final report
close on, and what is the dated cycle-archival record joining all
of them?* This playbook is that lifecycle. Wiring the five steps
into an orchestration surface that survives worker restart, records
each step as durable evidence, and closes on a dated archival record
is the audit-evident discharge of the Chapter III reporting
obligation set; assembling the answer from four inboxes and a
spreadsheet on the supervisory-review clock is not.

## 2. When to run each step

The lifecycle is not a single-shot workflow: the five steps land on
different clocks and different operator triggers.

- **Detect-and-classify.** Fires once per ICT-related incident on
  the operator's incident register, on the awareness event that
  crosses the operator's declared classification-review threshold.
  The Art. 18 classifier gate evaluates the incident against the
  Commission Delegated Regulation (EU) 2024/1772 criteria (clients,
  financial counterparts and transactions affected; reputational
  impact; duration and service downtime; geographical spread;
  data-losses; criticality of services affected; economic impact)
  and emits the classification-decision record. On the not-major
  branch the notification chain short-circuits; the dated decision
  is still emitted so the audit-evident chain closes at the gate.
- **Notify-authority-initial.** Fires on the major-classification
  edge. Within 4 hours of classification (and no later than 24 hours
  from awareness), the step packages the initial notification against
  the ITS content shape and dispatches to the competent authority.
  The dispatch is durable — a worker restart mid-dispatch replays
  against the same submission-body bytes and the same authority
  reference without redispatching a duplicate to the authority.
- **Notify-authority-intermediate.** Fires no later than 72 hours
  post-classification, or earlier on the operator's early-recovery
  edge. The step reads the incident register for the current
  timestamp, affected-functions, indicators-of-compromise, and
  mitigation-actions state, packages the intermediate report against
  the ITS intermediate-report template, and dispatches. The 72-hour
  clock is the same wall-clock the Art. 18 classification decision
  started; the intermediate step reads its clock from the
  classification-decision timestamp, not from wall time inside the
  step body (§ 9 on the deterministic-timestamp invariant).
- **Notify-authority-final.** Fires no later than one month after
  the intermediate report. The step reads the incident register for
  the closed root-cause analysis, final impact figures, completed
  remediation, lessons learned, action plan, and residual-risk
  statement, packages the final report against the ITS final-report
  template, and dispatches.
- **Close-and-archive.** Fires immediately after the final report
  is dispatched. The step composes the dated cycle-archival record
  referencing the classification decision, the three submissions,
  the authority acknowledgements, and any cross-regime parallel-
  notification chains (NIS2 Art. 23, GDPR Art. 33-34) the same
  underlying incident triggered. The archival record is the
  audit-evident cycle closure the competent authority reads on
  supervisory review.

The workflow is idempotent against the derivation inputs at each
step: two initial-notification runs on the same
`(workflow_id, execution_id, captured_at)` triple re-derive an
identical `__initial_notification_id__` that is byte-identical across
compile targets, and the same holds for the intermediate, final, and
cycle-archive ids (§ 9).

## 3. Source of truth

```
content/playbooks/dora_major_incident_reporting/
├── README.md                    # workflow-local overview and status
├── playbook.cacao.json          # canonical CACAO v2 source
│                                # (playbook.dora_major_incident_reporting@v1)
└── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / DORA / NIS2 / GDPR overlay

content/mappings/dora/
├── article-19-and-28.yaml       # dora:art-18-classification,
│                                # dora:art-19-initial-4h,
│                                # dora:art-19-intermediate-72h,
│                                # dora:art-19-final-one-month inbound anchors
```

The CACAO source is canonical. The five-step lifecycle (one `start`,
five `action` steps, one `end`) is the deterministic policy the
playbook *means*. The three worked examples under
`examples/{n8n,temporal,langgraph}/dora_major_incident_reporting/` are
the same playbook compiled into three orchestrator idioms. The dated
classification decision, the three submission records, and the dated
cycle-archival record each execution emits are anchored by a target-
agnostic `artifact_id` derivation so a replay under a different target
produces byte-identical bytes (§ 9).

The G-01 traceability anchor for this workflow closes here: the
ROADMAP entry `F-DORA-ART19` names this cookbook, the shipped CACAO
source, the compiled targets, and the outbound overlay as the
deliverables that discharge DORA Chapter III major-incident reporting
on the content axis.

## 4. CACAO topology

The workflow is a linear five-step lifecycle. Each action step
carries the CACAO I/O contract (`in_args` / `out_args`) plus
`x_secops_ng` reference bundles pinning the OSCAL control anchors
(IR-8 Incident Response Plan on classification, IR-6 Incident
Reporting on the three submission steps, IR-5 Incident Monitoring on
the archive step and the timeline signals underpinning each
submission) and the OCSF telemetry class each step reads or emits.

| Step suffix | Step                                | Discipline                                                                                                                                                                                                                                                          | Status         |
|-------------|-------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | dora_major_incident_reporting_start | edge wiring only — no body                                                                                                                                                                                                                                          | n/a            |
| `…000002`   | detect_and_classify                 | evaluate the incident register entry against the Commission Delegated Regulation (EU) 2024/1772 major-ICT-related-incident classification criteria; emit the dated classification-decision record; set `__classification_decision_id__`                              | adapter-bound  |
| `…000003`   | notify_authority_initial            | package the Art. 19(4)(a) initial notification against the ITS content shape (Commission Implementing Regulation (EU) 2024/2956) and dispatch to the competent authority within 4h of classification / 24h from awareness; set `__initial_notification_id__`         | adapter-bound  |
| `…000004`   | notify_authority_intermediate       | package the Art. 19(4)(b) intermediate report against the ITS intermediate-report template and dispatch within 72h of classification (or earlier on early-recovery edge); set `__intermediate_report_id__`                                                            | adapter-bound  |
| `…000005`   | notify_authority_final              | package the Art. 19(4)(c) final report (root-cause, final impact, remediation, lessons learned, action plan, residual-risk statement) against the ITS final-report template and dispatch no later than one month after the intermediate report; set `__final_report_id__` | adapter-bound  |
| `…000006`   | close_and_archive                   | compose the dated cycle-archival record referencing the classification decision, the three submissions, the authority acknowledgements, and any cross-regime parallel-notification chains; set `__cycle_archive_id__`                                                   | adapter-bound  |
| `…000007`   | dora_major_incident_reporting_end   | edge wiring only — no body                                                                                                                                                                                                                                          | n/a            |

Sequencing is `on_completion` end-to-end — the playbook is linear at
the workflow layer with no conditional branching. A **not-major**
classification at `detect_and_classify` does not branch the workflow
into a separate sub-flow: the dated classification decision is still
emitted, the notification steps short-circuit (each becomes a no-op
that records a dated *skipped* record referencing the not-major
decision), and `close_and_archive` still composes the archival record
against a classification-only cycle. The audit-evident chain remains
closed for below-threshold incidents.

Early-recovery on the intermediate-report step likewise does not
branch: the intermediate report is submitted early, the final-report
clock keeps its one-month-from-intermediate offset, and the archival
record captures the early-recovery edge.

## 5. Playbook variables

The playbook operates on a small set of workflow-scope variables.
`__incident_id__` and `__reporting_window__` are external — supplied
by the operator's incident register and cadence surfaces at lifecycle
entry. The remainder are set by downstream steps as the run progresses.

| Variable                        | External? | Set by                            | Purpose                                                                                                                                                          |
|---------------------------------|-----------|-----------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `__incident_id__`               | yes       | operator-supplied                 | stable operator-side incident identifier that joins the incident register, the classification decision, the three submissions, and the archival record on one key |
| `__reporting_window__`          | yes       | operator-supplied                 | reference to the awareness window the Art. 18 gate evaluates against (RFC 3339 interval); joins the classification decision to the operator's incident-register slice |
| `__classification_decision_id__`| no        | `detect_and_classify`             | opaque content-addressed identifier of the emitted classification-decision record; derives from `SHA-256(workflow_id|execution_id|captured_at)` and is target-agnostic (§ 9) |
| `__initial_notification_id__`   | no        | `notify_authority_initial`        | opaque content-addressed identifier of the emitted Art. 19(4)(a) initial-notification record; target-agnostic derivation                                          |
| `__intermediate_report_id__`    | no        | `notify_authority_intermediate`   | opaque content-addressed identifier of the emitted Art. 19(4)(b) intermediate-report record; target-agnostic derivation                                           |
| `__final_report_id__`           | no        | `notify_authority_final`          | opaque content-addressed identifier of the emitted Art. 19(4)(c) final-report record; target-agnostic derivation                                                  |
| `__cycle_archive_id__`          | no        | `close_and_archive`               | opaque content-addressed identifier of the emitted cycle-archival record; target-agnostic derivation                                                              |

The classification decision is a first-class artifact, not a boolean
predicate: the record carries the per-criterion evaluation, the
materiality-threshold arithmetic, the recurring-incident rule
disposition (Art. 18(2)), and the dated classifier version so a
supervisory reviewer can reconstruct the decision without re-running
the classifier. That is what makes the not-major branch audit-safe:
the operator can show a below-threshold incident *was* evaluated on
the same rubric as the major ones.

## 6. Adapter-bound surfaces

Six operator-owned surfaces sit behind adapter shims in the lifecycle.
The framework describes the CACAO contract each surface writes into;
it does not ship the surface.

### 6.1 Incident register

`detect_and_classify` reads the operator's declared incident register
against `__incident_id__` and `__reporting_window__`. The framework
declares the read shape (per-incident awareness timestamp, affected-
service surface, per-criterion signal inputs); the operator's
incident-management surface authors and maintains the register. The
same register is the read source for the intermediate step's
current-state fields (updated affected functions, indicators of
compromise, mitigation actions in flight) and for the final step's
closed root-cause block.

### 6.2 Art. 18 classification-decision store

`detect_and_classify` emits the classification-decision record into
the operator's evidence store. The record shape follows Commission
Delegated Regulation (EU) 2024/1772: seven primary criteria (clients,
financial counterparts and transactions affected; reputational
impact; duration and service downtime; geographical spread; data-
losses; criticality of services affected; economic impact) plus the
materiality-threshold arithmetic and the Art. 18(2) recurring-
incident-rule disposition. The framework declares the record shape;
the operator's evidence store retains it as the durable dated
classification decision.

### 6.3 ITS submission-body composer

Each notification step composes the outbound submission body against
the ITS content shape Commission Implementing Regulation (EU)
2024/2956 fixes. The three ITS templates (initial, intermediate,
final) are the outbound envelope the competent authority reads
against. The framework declares the per-step composer contract; the
operator's implementation binds the composer to the operator's
data model.

### 6.4 Competent-authority notification channel

Each notification step dispatches the composed body to the operator's
designated competent authority — one of the three European
Supervisory Authorities (EBA, ESMA, EIOPA) via the national competent
authority (NCA) chain prescribed by the operator's sector. The
authority chain is an adapter-bound configuration input: for a credit
institution the NCA is typically the national banking supervisor; for
a payment institution or e-money institution it is the payment-
services supervisor; for an insurance undertaking it is the national
insurance supervisor. Each NCA publishes its own submission surface
(portal, per-authority reference-number allocation, per-authority
channel of record). The framework produces the ITS-shaped submission
body; the entity wraps it into the per-authority envelope. The
dispatch is durable — the operator's channel binding provides the
authority-acknowledgement reference which is folded onto the
submission record.

### 6.5 Cross-regime notification-chain surface

`close_and_archive` reads the operator's cross-regime notification-
chain surface for any NIS2 Art. 23 notifications
(`playbook.incident_management@v1`) and any GDPR Art. 33 / 34
breach-notifications (breach-notification cluster) the same
underlying incident triggered. The read is optional at the CACAO
layer — an incident that lands only under DORA Chapter III still
produces a closed cycle-archival record. The join surfaces the
parallel-notification relationship for supervisory readers on the
supervisory-review side.

### 6.6 Evidence-archival store

`close_and_archive` writes the emitted cycle-archival record into
the operator's evidence store — typically the same store the
classification decision and the three submission records land in.
The framework declares the record shape; the operator's store
retains it as the durable dated cycle-archival record supervisory
review reads against.

## 7. Regulatory anchors

**DORA — Regulation (EU) 2022/2554.** The regulation prescribes the
Chapter III ICT-related-incident management surface, the Article 18
classification obligation, the Article 19 three-milestone reporting
obligation, the Article 20 supervisory-follow-up surface, and the
Chapter IV supervisory posture the lifecycle discharges into. Inbound
anchors live under `content/mappings/dora/`:

- `content/mappings/dora/article-19-and-28.yaml` carries the four
  atoms `dora:art-18-classification`, `dora:art-19-initial-4h`,
  `dora:art-19-intermediate-72h`, and `dora:art-19-final-one-month`
  that backlink `playbook.dora_major_incident_reporting@v1`.

**Commission Delegated Regulation (EU) 2024/1772** — the RTS on
incident classification. The `detect_and_classify` step's per-
criterion evaluation and materiality-threshold arithmetic follow the
shape this RTS fixes; the classification-decision record retains the
per-criterion signal so a supervisory reviewer can replay the
decision on the same rubric.

**Commission Implementing Regulation (EU) 2024/2956** — the ITS on
the standard templates for the register of information and for
major-ICT-related-incident reporting. The three notification steps
compose submission bodies on the templates this ITS fixes (initial,
intermediate, final); the operator's evidence store retains each as
the durable Article 19 record and the operator's per-authority
envelope wraps it for the NCA channel.

**OSCAL controls** — from
[`content/playbooks/dora_major_incident_reporting/mappings.yaml`](../../content/playbooks/dora_major_incident_reporting/mappings.yaml):

- **IR-8** *(Incident Response Plan)* — anchors the
  `detect_and_classify` step as the documented incident-response
  plan the operator maintains and against which the Art. 18
  classification decision is discharged. The stable-id
  `control.dora_major_classifier@v1` is the deterministic Art. 18
  classifier primitive reused from the DORA Art. 18/19 mapping.
- **IR-6** *(Incident Reporting)* — anchors the three notification
  steps as the external-reporting discipline (report to
  organisational officials and external authorities on the incident
  within defined timelines). The three DORA Art. 19 milestones are
  the DORA-specific application of that discipline against the ESA /
  NCA authority chain and the ITS content shape.
- **IR-5** *(Incident Monitoring)* — anchors the `close_and_archive`
  step and the timeline signals underpinning each of the three
  milestone submissions. The dated cycle-archival record is the
  audit-evident IR-5 output the competent authority reads on
  supervisory review.

**MITRE D3FEND v1.0.0** — no per-step D3FEND pin. The DORA Chapter
III reporting-lifecycle steps are compliance-notification
disciplines (classification-decision emission, three regulator
submissions, cycle-archival composition) rather than defensive-
technique discharges against the operator's deployed estate. D3FEND
v1.0.0 does not currently carry a regulator-notification technique
atom that matches these steps without stretching the taxonomy; a
subsequent extension may lift `D3-OAM` (Operational Activity Mapping)
onto the `close_and_archive` step against the incident-timeline shape
once a documented mapping is authored upstream. Mirrors the
`dora_tpr_management` precedent for governance-side workflows.

**OCSF v1.3.0** — one class binding. **API Activity** (class_uid
6003, category Application Activity), direction `both`. Consumed at
the `detect_and_classify` step (reads against the incident register
and the Art. 18 classifier output) and at each notification step
(reads against the ITS submission-body composer and the authority
channel). Emitted at each notification step (write call dispatching
the composed body to the competent authority; records the authority
acknowledgement into the submission artifact) and at
`close_and_archive` (write call publishing the dated cycle-archival
record to the operator's evidence store).

**NIS2 Art. 23** — cross-regime sibling. An operator submitting a
DORA Art. 19 notification chain is very likely also in scope of NIS2
Art. 23 as an essential or important entity, and the two regimes
file separate notifications to separate authorities against the same
underlying incident. `content/mappings/nis2/article-23.yaml` carries
`playbook.dora_major_incident_reporting@v1` as a cross-regime
sibling alongside the NIS2-flavoured
`playbook.incident_management@v1`. The `close_and_archive` step
references the NIS2 Art. 23 chain (where fired) so supervisory
readers can navigate the parallel-notification graph.

**GDPR Art. 33 / 34** — cross-regime sibling. Where an in-scope
major ICT-related incident involves personal data, the operator also
discharges the Art. 33 supervisory-authority notification (72h) and,
on the high-risk threshold, the Art. 34 data-subject communication.
This playbook does not itself compose the Art. 33 / 34 submissions
(those are discharged by the breach-notification cluster —
`playbook.data_exfil@v1`, `playbook.identity_compromise@v1`,
`playbook.ransomware_containment@v1`,
`playbook.incident_management@v1`). The `close_and_archive` step
references the GDPR chain (where fired) so supervisory readers can
navigate the parallel-notification graph.

## 8. Per-target hand-off

The step outline above is the portable description all three
compilers read against. n8n compiles it into a linear seven-node
workflow (`manualTrigger` + five `set` nodes + `noOp`); Temporal
compiles it into a workflow with five activity invocations chained
by `await`; LangGraph compiles it into a `StateGraph` with seven
nodes and unconditional-edge topology.

### 8.1 n8n — Set nodes over the five-step lifecycle

`examples/n8n/dora_major_incident_reporting/workflow.n8n.json`
carries the CACAO topology as n8n nodes (one `manualTrigger`, five
`set` nodes, one `noOp` terminal). Node ids preserve the CACAO step
ids verbatim. Each action node emits a `n8n-nodes-base.set` carrying
the CACAO I/O contract as editable assignment rows plus the
`x_secops_ng` reference bundles.

Operators bind the Set rows to their connectors:

- `detect_and_classify` → the incident-register reader plus the
  Art. 18 classifier (HTTP Request / Postgres node against the
  register, followed by a Function node applying the RTS 2024/1772
  criteria over the operator's declared threshold set). Writes
  `__classification_decision_id__`.
- `notify_authority_initial` → the ITS initial-notification composer
  plus the competent-authority dispatch (Function node materialising
  the ITS initial-notification body per Commission Implementing
  Regulation (EU) 2024/2956, followed by an HTTP Request node
  against the operator's NCA submission surface, with the
  acknowledgement reference threaded onto the submission record).
  Writes `__initial_notification_id__`.
- `notify_authority_intermediate` → the ITS intermediate-report
  composer plus the dispatch (same shape as the initial step; reads
  the current incident-register state for updated timestamps,
  affected functions and clients, indicators of compromise, and
  mitigation actions in flight). Writes `__intermediate_report_id__`.
- `notify_authority_final` → the ITS final-report composer plus the
  dispatch (same shape; reads the closed root-cause analysis, final
  impact figures, completed remediation, lessons learned, action
  plan, and residual-risk statement). Writes `__final_report_id__`.
- `close_and_archive` → the cycle-archival composer and evidence-
  store sink (Function node materialising the archival record over
  the classification decision, the three submissions, the authority
  acknowledgements, and any cross-regime notification chains,
  followed by a Postgres / HTTP / S3 write node against the evidence
  store). Writes `__cycle_archive_id__`.

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/dora_major_incident_reporting/regenerate.sh
```

Equivalent direct invocation:

```sh
PYTHONPATH=. python -m tools.compile \
    content/playbooks/dora_major_incident_reporting/playbook.cacao.json \
    --target n8n \
    --out examples/n8n/dora_major_incident_reporting/workflow.n8n.json
```

The byte-parity golden test under
`tests/examples/n8n/dora_major_incident_reporting/test_golden.py`
reruns the same pipeline and fails if the committed artifact drifts.

### 8.2 Temporal — activities over the five-step lifecycle

`examples/temporal/dora_major_incident_reporting/workflow.temporal.py`
carries the CACAO topology as a Temporal workflow with one activity
per action step. `__incident_id__` and `__reporting_window__` are
threaded through the workflow signature as arguments — every
activity reads against workflow-scoped inputs rather than worker-
local state. A worker restart mid-workflow re-hydrates the same
argument scope against Temporal's event-history replay contract, so
a re-emission of any of the five step artifacts produces byte-
identical id bytes.

Operators bind the activity bodies to real connectors:

- `detect_and_classify` — the classifier-application activity. The
  reference binding reads the operator's incident register, applies
  the Commission Delegated Regulation (EU) 2024/1772 criteria over
  the operator's declared thresholds, stamps the per-criterion
  evaluation, and closes the classification-decision record
  referenced by `__classification_decision_id__`.
- `notify_authority_initial` — the initial-notification dispatch
  activity. Composes the ITS initial-notification body, dispatches
  to the competent-authority channel, folds the acknowledgement
  reference onto the submission record, and closes the record.
- `notify_authority_intermediate` — the intermediate-report dispatch
  activity. Same shape as the initial dispatch; reads the current
  incident-register state for the updated fields.
- `notify_authority_final` — the final-report dispatch activity.
  Same shape; reads the closed root-cause block.
- `close_and_archive` — the cycle-archival-composition activity.
  The `__cycle_archive_id__` derivation happens at the primitive
  layer — the activity computes the hash and writes the archival
  record to the operator's evidence store.

To regenerate the compiled artifact from the repo root:

```sh
./examples/temporal/dora_major_incident_reporting/regenerate.sh
```

The byte-parity golden test under
`tests/examples/temporal/dora_major_incident_reporting/test_golden.py`
reruns the emitter and fails if the committed artifact drifts.
Activity bodies remain `NotImplementedError` stubs by design in the
shipped example; the operator supplies the bindings.

### 8.3 LangGraph — nodes and state over the five-step lifecycle

`examples/langgraph/dora_major_incident_reporting/graph_spec.json`
carries the CACAO topology as a target-neutral GraphSpec (nodes,
edges, conditional edges — the last being empty for this linear
playbook); `state_bindings.py` emits the `TypedDict` state and the
`@tool`-decorated action wrappers plus the agentic-extension hook.
`__incident_id__` and `__reporting_window__` are expressed as state
fields threaded through node bodies, so a checkpoint reload
re-hydrates the same argument scope.

The GraphSpec `nodes` array carries only the five intermediate
action step ids; start and end sentinels are pinned structurally
via `entry` and `end_sentinel` (this is the LangGraph projection
contract the cross-target parity test asserts against — the same
canonical CACAO step space is present, in a different structural
shape than n8n's node array).

The audit-mirror sibling `_audit_mirror.py` (see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md))
carries the OTel-free durable audit trail on LangGraph runs where
the operator has not wired an OTLP collector.

Operators bind the tool bodies to real connectors:

- `detect_and_classify` → classifier-application tool + optional
  agentic-extension hook. The agentic extension is where an operator
  running a LangGraph agent can invoke an LLM-assisted reviewer
  against the classification-decision record — e.g. to draft the
  natural-language justification for a materiality-threshold
  disposition — as a supplement to the deterministic classifier
  application, not a replacement.
- `notify_authority_initial` → ITS initial-notification composer +
  dispatch tool.
- `notify_authority_intermediate` → ITS intermediate-report
  composer + dispatch tool.
- `notify_authority_final` → ITS final-report composer + dispatch
  tool.
- `close_and_archive` → cycle-archival composer + evidence-store
  sink tool.

To regenerate the compiled artifacts from the repo root:

```sh
./examples/langgraph/dora_major_incident_reporting/regenerate.sh
```

## 9. Byte-parity across compile targets — the cross-target invariant

The classification decision emitted at `detect_and_classify`, the
three submission records emitted at the notification steps, and the
cycle-archival record emitted at `close_and_archive` are each
anchored by a deterministic `artifact_id` derivation:

```
artifact_id = SHA-256(workflow_id | execution_id | captured_at)
```

The input is UTF-8, with single pipe separators and no surrounding
whitespace, and the `compile_target` is **deliberately not part of
the input**. A replay of the same
`(workflow_id, execution_id, captured_at)` triple under n8n,
Temporal, or LangGraph produces byte-identical classification-
decision bytes, submission-record bytes, and cycle-archival bytes.

Concretely, across the three targets:

- **n8n** — the classifier, notification, and archival emitters read
  `execution_id` from the workflow-execution scope and `captured_at`
  from a workflow-local timestamp threaded through the workflow,
  not from `$now` inside a Function node. The `artifact_id`
  derivation is authored in the emitter templates, not in the
  target-specific Function nodes, so re-executions and n8n version
  changes do not drift the hash.
- **Temporal** — the classifier, notification, and archival
  activities read `execution_id` as the Temporal workflow-run id and
  `captured_at` from a workflow-local timestamp threaded through the
  activity call, not from `datetime.utcnow()` inside the activity
  body. A history-replay re-derives the identical hash.
- **LangGraph** — the classifier, notification, and archival tools
  read `execution_id` from the LangGraph thread/checkpoint id and
  `captured_at` from state, not from `time.time()` inside the tool
  body. A checkpoint reload re-derives the identical hash.

The reason for the target-agnostic anchor is regulatory, not
stylistic. The Chapter IV supervisory posture is a posture about the
*financial entity's incident-reporting discipline*, not about the
*orchestrator that runs the workflow*. A financial entity that
migrates from n8n to Temporal (or runs two operational-population
slices concurrently on different targets during a migration) must be
able to consolidate their per-incident submission ledger without
dedup drift; the framework refuses the drift-shape by construction.

## 10. Exporting results as supervisory-reporting evidence

Under DORA Chapter IV, the financial entity is expected to hand
its major-ICT-related-incident submissions to the competent authority
on the ITS-fixed cadence per milestone, and to produce the closed
cycle-archival record on supervisory-authority request. Fields on
the emitted classification decision, the three submission records,
and the cycle-archival record are the supervisory-facing surface:

- **`incident_id`** (all five artifacts) — the stable operator-
  side identifier. Supervisory correspondence quotes this reference
  so the entity's response can be joined against the ITS-shape
  submission aggregation the NCA has retained.
- **`classification_decision_id`** and **`classification_disposition`**
  (classification decision) — the content-addressed identifier and
  the major / not-major disposition. The supervisory reader learns
  when and on what per-criterion evaluation the entity crossed (or
  did not cross) the Art. 18 major threshold.
- **`initial_notification_id`**, **`intermediate_report_id`**,
  **`final_report_id`** (submission records) — the content-
  addressed identifiers of the three milestone submissions. Each
  carries the ITS-shape body, the dispatch timestamp, and the
  competent-authority acknowledgement reference the entity received
  back through the per-authority channel.
- **`cycle_archive_id`** (cycle-archival record) — the content-
  addressed identifier of the dated cycle-archival record referencing
  the classification decision, the three submissions, the authority
  acknowledgements, and any cross-regime parallel-notification
  chains. The competent authority reads this against the whole-
  cycle discharge for the incident.

The classification decision, the three submission records, and the
cycle-archival record are the audit-evident artifacts retained on
the operator's evidence store. Wiring them into the competent-
authority-facing envelope is a financial-entity responsibility: the
framework does not ship the per-authority submission channel (each
national competent authority under DORA publishes its own Chapter
III submission portal, submission format, and reference-number
allocation, and the ITS on major-ICT-related-incident reporting fixes
the per-milestone body shape rather than the per-authority handoff).
What the framework produces is the canonical, dated, byte-
deterministic record the entity's submission wraps.

## 11. Playbook chain — where dora_major_incident_reporting sits

The five-step lifecycle interacts with several sibling playbooks on
the operator's substrate. The interactions are documented at the
CACAO source and in `mappings.yaml`, and are worth calling out in a
cookbook context so a reader can situate the workflow:

- **`playbook.incident_management@v1` — NIS2 Art. 23 significant-
  incident reporting lane.** Fires on the NIS2 significant-incident
  threshold against the CSIRT / competent-authority chain. A single
  operator may be in scope of both DORA and NIS2 simultaneously —
  most large EU financial entities are — in which case the two
  playbooks fire in parallel on the same underlying incident against
  different authority chains, and the operator files separate
  notifications to separate authorities. `close_and_archive` reads
  the parallel-lane surface (where fired) so the cycle-archival
  record carries the cross-regime relationship.
- **`playbook.dora_ict_risk_selfassess@v1` — whole-Chapter II ICT
  risk management roll-up.** DORA Chapter III (major-incident
  reporting) is deliberately out of scope for the Chapter II
  self-assessment roll-up; the two playbooks are the Chapter II
  discharge and the Chapter III discharge respectively. A financial
  entity discharges both on their respective cadences into the same
  supervisory envelope.
- **`playbook.dora_tpr_management@v1` — DORA Chapter V ICT
  third-party risk management lifecycle.** A material ICT-related
  incident against a third-party provider re-enters
  `dora_tpr_management`'s `periodic_review` step on the operator's
  material-change surface; the DORA Art. 19 report itself remains
  the Chapter III discharge and stays outside the Chapter V
  workflow.
- **`playbook.dora_tlpt_programme@v1` — DORA Chapter IV testing-
  programme discipline.** Distinct Chapter (IV) from this Chapter
  (III). The two playbooks share no runtime touchpoint; a threat-
  led penetration testing programme run under Chapter IV that
  surfaces a live incident hands the incident to Chapter III on
  the incident-register boundary.
- **Breach-notification cluster** (`playbook.data_exfil@v1`,
  `playbook.identity_compromise@v1`,
  `playbook.ransomware_containment@v1`,
  `playbook.incident_management@v1`) — the GDPR Art. 33 / 34
  breach-notification lane. Where the ICT-related incident also
  involves personal data, this cluster fires the GDPR-flavoured
  notification chain in parallel on the same underlying incident.
  `close_and_archive` reads the parallel-lane surface (where fired).
- **The operator's incident management framework under Article 17.**
  The awareness surface, the classification-review threshold, the
  Art. 18 classification rubric (and its per-criterion threshold
  set), the ITS submission-body composer, and the cycle-archival
  schema are all authored under the framework Article 17 requires.
  The playbook applies them; it does not author them.

## 12. Example output snippets

The examples below are illustrative shapes — the actual bytes emitted
depend on the operator's ITS-body composer, the operator's evidence-
store schema, and the incident under evaluation. The `artifact_id`
values shown are `SHA-256(workflow_id | execution_id | captured_at)`
outputs under a target-agnostic derivation (§ 9) and are stable
across n8n, Temporal, and LangGraph replays.

### 12.1 Classification decision (Art. 18)

```
{
  "artifact_type": "dora.art18.classification_decision",
  "artifact_id": "sha256:<64-hex>",
  "incident_id": "inc.<operator-scoped-id>",
  "reporting_window": "2026-01-15T09:00:00Z/2026-01-15T15:00:00Z",
  "captured_at": "2026-01-15T15:22:00Z",
  "criteria": {
    "clients_transactions_affected": { "score": "…", "threshold_crossed": true },
    "reputational_impact":           { "score": "…", "threshold_crossed": false },
    "duration_downtime":             { "score": "…", "threshold_crossed": true  },
    "geographical_spread":           { "score": "…", "threshold_crossed": false },
    "data_losses":                   { "score": "…", "threshold_crossed": true  },
    "criticality_of_services":       { "score": "…", "threshold_crossed": true  },
    "economic_impact":               { "score": "…", "threshold_crossed": false }
  },
  "recurring_incident_rule": { "art_18_2_applicable": false },
  "classifier_version": "control.dora_major_classifier@v1",
  "disposition": "major"
}
```

### 12.2 Initial notification (Art. 19(4)(a))

```
{
  "artifact_type": "dora.art19.initial_notification",
  "artifact_id": "sha256:<64-hex>",
  "incident_id": "inc.<operator-scoped-id>",
  "classification_decision_id": "sha256:<64-hex>",
  "its_template_version": "2024/2956.initial",
  "dispatched_at": "2026-01-15T17:05:00Z",
  "authority_channel_ref": "<per-NCA channel token>",
  "authority_acknowledgement": {
     "acknowledged_at": "2026-01-15T17:07:12Z",
     "authority_reference": "<per-NCA reference-number>"
  }
}
```

### 12.3 Cycle-archival record

```
{
  "artifact_type": "dora.chapter3.cycle_archive",
  "artifact_id": "sha256:<64-hex>",
  "incident_id": "inc.<operator-scoped-id>",
  "classification_decision_id": "sha256:<64-hex>",
  "initial_notification_id":    "sha256:<64-hex>",
  "intermediate_report_id":     "sha256:<64-hex>",
  "final_report_id":            "sha256:<64-hex>",
  "cross_regime_notifications": {
    "nis2_art_23":   { "fired": true,  "chain_ref": "<operator-side ref>" },
    "gdpr_art_33":   { "fired": true,  "chain_ref": "<operator-side ref>" },
    "gdpr_art_34":   { "fired": false }
  },
  "captured_at": "2026-02-16T10:00:00Z"
}
```

## 13. What this cookbook deliberately does not cover

- **The incident register schema.** The per-incident shape, indexing,
  and retention posture are operator-owned. The framework describes
  the read/write contract at each step and the per-record attribution
  invariant; it does not ship the register.
- **The Art. 18 classification threshold values.** The seven primary
  criteria and the materiality-threshold arithmetic are the shape
  Commission Delegated Regulation (EU) 2024/1772 fixes; the per-
  criterion threshold *values* the operator applies live in the
  operator's incident management framework under Article 17. The
  classifier applies them; the framework does not author them.
- **The ITS submission-body composer.** The three ITS templates
  (initial, intermediate, final) are the shape Commission
  Implementing Regulation (EU) 2024/2956 fixes; the operator-side
  composer that fills each template against the operator's data
  model is operator-owned.
- **The competent-authority notification channel.** Each national
  competent authority under DORA publishes its own submission
  portal, per-authority reference-number allocation, and per-
  authority channel of record. The framework produces the ITS-
  shaped submission body; the entity wraps it into the per-
  authority envelope.
- **The awareness threshold.** *When* an operator learns of an
  incident (the awareness edge that starts the 24-hour outer clock
  under Art. 19(4)(a)) is authored on the operator's incident-
  detection surface, not on this playbook. The playbook operates
  from the awareness edge onward.
- **The GDPR Art. 33 / 34 body composition.** GDPR breach-
  notification bodies are composed by the breach-notification
  cluster, not this playbook. The `close_and_archive` step
  references the cross-regime chain; it does not compose the
  cross-regime submission.
- **Articles 20 to 23 — supervisory-follow-up and ESA-aggregation
  surfaces.** Article 20 (supervisory follow-up), Article 21
  (harmonisation of reporting), Article 22 (supervisory feedback),
  and Article 23 (operational or security-payment-related
  incidents) are downstream surfaces on the competent-authority /
  ESA side. The framework produces the entity-side reporting
  artifacts; the aggregation and follow-up surfaces sit outside
  the operator playbook.
- **Voluntary Article 19(3) reporting of significant cyber
  threats.** Article 19(3) is a voluntary reporting lane on
  significant cyber threats distinct from the mandatory major-
  incident lane this playbook covers. A sibling playbook may lift
  Art. 19(3) once the threat-reporting scope is authored.

## 14. Community contribution

Improvements to this walkthrough — clarifications, worked examples,
additional regulatory-reference tightening — are welcome via the
community contribution flow described in
[`CONTRIBUTING.md`](../../CONTRIBUTING.md). The CACAO source, the
compiled examples, and the byte-parity goldens are the source of
truth; the cookbook is the connective narrative and evolves as the
playbook set around it evolves.

## 15. References

- OASIS CACAO v2.0 specification.
- DORA — Regulation (EU) 2022/2554, Chapter III (Articles 17 to 23),
  ICT-related-incident management, classification, and reporting;
  Article 18 classification of ICT-related incidents and cyber
  threats; Article 19 reporting of major ICT-related incidents and
  voluntary notification of significant cyber threats.
- Commission Delegated Regulation (EU) 2024/1772 — RTS on the
  criteria for the classification of ICT-related incidents and cyber
  threats under DORA Article 18.
- Commission Implementing Regulation (EU) 2024/2956 — ITS on the
  standard templates for the register of information under DORA
  Article 28(9) and for the notification of major ICT-related
  incidents under DORA Article 19.
- NIS2 — Directive (EU) 2022/2555, Article 23, significant-incident
  reporting (cross-regime sibling).
- GDPR — Regulation (EU) 2016/679, Articles 33 and 34, personal-
  data-breach notification and communication (cross-regime sibling).
- NIST SP 800-53 Rev. 5 — IR-8 (Incident Response Plan), IR-6
  (Incident Reporting), IR-5 (Incident Monitoring).
- OCSF v1.3.0 — API Activity (class_uid 6003) event class.
