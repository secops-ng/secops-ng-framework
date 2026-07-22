# nis2_art20_governance — cookbook walkthrough

Management-body cybersecurity governance lifecycle an essential or
important entity runs on a documented cadence to discharge the two
NIS2 Directive (EU) 2022/2555 Article 20 obligations: Article 20(1)
management-body approval of the Article 21 cybersecurity risk-
management measures and oversight of their implementation, and
Article 20(2) mandatory cybersecurity training for members of the
management body. The `playbook.nis2_art20_governance@v1` CACAO
playbook operates the four-step approval cycle that produces the
dated governance-record evidence artifact the auditable-lifecycle
obligation names: schedule the management-body review, present the
current Article 21(2)(a)–(j) risk-posture to the management body,
record the management-body approval (carrying the Article 20(2)
training-completion attestation for management-body members), and
emit the dated governance-record artifact.

The playbook is the **portable description of the governance-body
approval discipline**. It does not choose the operator's management-
body forum, does not schedule the review cadence, does not author
the risk-management measures (those come out of Article 21 and are
composed for the management body by the sibling `nis2_self_
assessment` playbook), and does not ship the operator-facing
governance-record template. It describes the workflow shape the
operator's stack should run so the four-step lifecycle
(schedule → present → approve → log) is auditable, replayable, and
restart-safe — as a shipped Digital Commons artifact.

Distinct from the sibling `nis2_self_assessment` playbook (the
whole-Article-21 evidence roll-up on the operator's declared self-
assessment cadence — this walkthrough at
[`nis2_self_assessment.md`](nis2_self_assessment.md)) and from the
F-CP-06 effectiveness loop (per-metric snapshots on the evaluation-
window cadence): this walkthrough covers the **management-body
approval discipline** the Article 20(1) obligation names on the
governance-body axis, keyed on the four-step approval-cycle atoms
rather than the per-clause evidence fan-out. The self-assessment
composes the risk-posture the management body reads; the Article 20
governance cycle records the management body's decision on that
posture and closes the governance ledger.

This walkthrough wires the shipped playbook through all three
reference compile targets (n8n, Temporal, LangGraph) and shows where
each lifecycle stage — schedule, present, approve, log — lands in
each. Adapter bodies (governance-cadence catalogue, evidence-store
read, management-body-decision record surface, training-completion
attestation source, evidence sink) are declared as adapter-bound
surfaces the operator wires; the shipped CORE artifact lands the
byte-parity emitter fan-out under
`examples/{n8n,temporal,langgraph}/nis2_art20_governance/` and the
G-03 cross-target parity contract.

> The framework is framework-agnostic by construction. n8n /
> Temporal / LangGraph are *three of three* reference targets;
> the same CACAO source compiles into all of them. Operators
> run whichever target already lives in their stack.

## 1. Why this matters

NIS2 Article 20(1) requires the **management bodies of essential
and important entities** to approve the cybersecurity risk-
management measures taken by those entities to comply with Article
21, oversee their implementation, and be held liable for
infringements. Article 20(2) requires the **members of the
management body** to follow training on a regular basis so they
gain sufficient knowledge and skills to identify risks and assess
cybersecurity risk-management practices and their impact on the
services provided by the entity, and to encourage the entity to
offer similar training to all employees on a regular basis.

Together, Article 20 makes the management body a first-class actor
on the operator's cybersecurity control surface: not a downstream
recipient of a compliance report, but the governance-body decision
maker whose approval is a precondition for the Article 21 measures
being in force. Supervisory authorities under Chapter VII exercise
their supervisory tasks against Article 20 alongside Article 21;
Article 32 (essential entities) and Article 33 (important entities)
both name management-body oversight explicitly. An operator that
ships a full Article 21(2) playbook set still owes the supervisory
authority a coherent answer to *did the management body approve
these measures, on what cadence, and are its members trained?*
Reading loose meeting minutes is not that answer; a dated,
deterministic governance-record artifact keyed on the four-step
approval-cycle atoms is.

This playbook is that governance-record producer. Wiring the
Article 20 approval cycle into an orchestration surface that
survives worker restart, records the four-step lifecycle as durable
evidence, and closes on a dated governance-record artifact is the
audit-evident discharge of the management-body approval and
training obligations; producing the same posture "on best effort"
in a slide deck the day before the supervisory authority visits is
not.

NIS2 enforcement went live in July 2026, and Article 20 is the
first-order obligation supervisory authorities test against in the
early enforcement window. Every essential and important entity
owes a discharge on this axis on the first management-body cycle
after their designation.

## 2. When to run the governance cycle

Three run-triggers land in the operator's cadence configuration
and supply `__governance_cycle__` at lifecycle entry. The playbook
does not pick one; it accepts whichever the operator's scheduler
names.

- **Scheduled cadence.** The operator's documented periodic
  management-body cybersecurity-review interval (typically per-
  board-meeting for the cybersecurity agenda-slot, quarterly for
  many operators, or annual for management-body-level programme
  reapproval). `__governance_cycle__` names the cadence period
  (e.g. `2026-Q3`, `2026-annual`). This is the primary Article
  20(1) approval-cycle discharge.
- **On-demand review.** An operator-initiated run outside the
  scheduled cadence, e.g. after a material change to the operator's
  substrate that materially shifts the Article 21(2) posture, or
  after a Chapter VI Article 23 significant-incident that requires
  management-body re-approval of new compensating measures.
  `__governance_cycle__` names the on-demand reference
  (e.g. `2026-post-migration`).
- **Supervisory-authority request.** An Article 32(2) supervisory
  measure (essential entities) or Article 33(2) supervisory
  measure (important entities) directing the operator to produce a
  current management-body approval record on a defined deadline.
  `__governance_cycle__` names the request reference (e.g.
  `sa-request-2026-Q3`). The governance-record artifact's
  `governance_cycle` field carries the reference so the
  supervisory-authority-facing envelope can be cross-referenced by
  the reviewer.

The workflow is idempotent against `__governance_cycle__`: two
runs on the same cycle key resolve to identical inputs into the
evidence emitter and re-derive an `__evidence_id__` that is byte-
identical across compile targets for the same
`(governance_cycle, review_id, approval_record_id, captured_at)`
tuple (§ 8). The operator decides whether to overwrite the prior
record or retain both on the governance ledger; the framework
retains both by default.

## 3. Source of truth

```
content/playbooks/nis2_art20_governance/
├── README.md                    # workflow-local overview and status
├── playbook.cacao.json          # canonical CACAO v2 source (playbook.nis2_art20_governance@v1)
├── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / NIS2 overlay
└── primitives/
    ├── cycle.py                 # resolve_governance_cycle
    ├── review.py                # conduct_art20_review
    ├── approval.py              # record_management_approval
    └── evidence.py              # emit_governance_evidence + derive_governance_evidence_artifact_id

content/mappings/nis2/
└── article-20.yaml              # inbound anchor (nis2:art-20-1, nis2:art-20-2)

examples/{n8n,temporal,langgraph}/nis2_art20_governance/
                                 # three-target reference compilations
```

The CACAO source is canonical. The four-step lifecycle (one `start`,
four `action` steps, one `end`) is the deterministic policy the
playbook *means*. The three worked examples under
`examples/{n8n,temporal,langgraph}/nis2_art20_governance/` are the
same playbook compiled into three orchestrator idioms. The dated
governance-record artifact each execution emits is anchored by a
target-agnostic `artifact_id` derivation so a replay under a
different target produces byte-identical bytes (§ 8).

The G-01 traceability anchor for this workflow closes here: the
ROADMAP entry `F-CACAO-NIS2-ART20` names this cookbook, the shipped
CACAO source, the four deterministic primitives, the compiled
targets, and the outbound overlay as the deliverables that
discharge the Article 20 management-body governance surface on the
content axis; G-03 closes against the byte-parity goldens the
CORE-GOLDENS artifact lands.

## 4. CACAO topology

The workflow is a linear four-step lifecycle. Each action step
carries the CACAO I/O contract (`in_args` / `out_args`) plus
`x_secops_ng` reference bundles pinning the OSCAL control anchors
(PM-2 across all steps, SA-2 additionally on the approve step),
the D3FEND techniques (D3-PSEP on the approve step, D3-OAM on the
log step), and the OCSF telemetry class the log step emits.

| Step suffix | Step                          | Discipline                                                                                                                             | Body                              |
|-------------|-------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------|
| `…000001`   | nis2_art20_governance_start   | edge wiring only — no body                                                                                                             | n/a                               |
| `…000002`   | schedule_management_review    | resolve the operator's documented governance-cadence catalogue against `__governance_cycle__` and record the scheduled review event; set `__review_id__` (empty on the ad-hoc / supervisory_request branch) | `primitives.cycle.resolve_governance_cycle` |
| `…000003`   | present_risk_posture          | compose the per-cycle governance view over the current Article 21(2)(a)–(j) compliance status, open exceptions, and material changes since the previous cycle; set `__posture_snapshot_id__` | `primitives.review.conduct_art20_review` |
| `…000004`   | approve_risk_measures         | record the management-body approval outcome (or referral) and the Article 20(2) training-completion attestation for management-body members; set `__approval_record_id__` (empty on the referral branch) | `primitives.approval.record_management_approval` |
| `…000005`   | log_governance_evidence       | publish the dated OCSF API Activity governance-record artifact and derive the deterministic `__evidence_id__` from `SHA-256(governance_cycle|review_id|approval_record_id|captured_at)` | `primitives.evidence.emit_governance_evidence` |
| `…000006`   | nis2_art20_governance_end     | edge wiring only — no body                                                                                                             | n/a                               |

Sequencing is `on_completion` end-to-end — the playbook is linear,
with no conditional branching at the workflow layer. The two
negative-outcome branches (ad-hoc trigger with no scheduled review
slot; management-body referral with no approval) are carried
explicitly rather than short-circuited: `__review_id__` and
`__approval_record_id__` are emitted as empty strings alongside
their respective markers so the downstream log step captures the
branch outcome rather than silently dropping the cycle.

## 5. Playbook variables

The playbook operates on a small set of workflow-scope variables.
`__governance_cycle__` and `__captured_at__` are external —
supplied by the operator's scheduler (or the compile-target
runtime) at lifecycle entry. The remainder are set by downstream
steps as the run progresses.

| Variable                  | External? | Set by                       | Purpose                                                                                                                                                                                             |
|---------------------------|-----------|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `__governance_cycle__`    | yes       | operator-supplied            | reference to the management-body cybersecurity cycle the run discharges (scheduled cadence, on-demand review, supervisory-authority request)                                                        |
| `__review_id__`           | no        | `schedule_management_review` | scheduled review-event id from the operator's governance-cadence catalogue; empty on the ad-hoc / supervisory_request branch                                                                        |
| `__posture_snapshot_id__` | no        | `present_risk_posture`       | per-cycle composed view of the Article 21(2)(a)–(j) compliance status, open exceptions, and material changes since the previous cycle                                                                |
| `__approval_record_id__`  | no        | `approve_risk_measures`      | signed management-body approval record id; empty on the referral branch (management body did not approve in this cycle)                                                                             |
| `__evidence_id__`         | no        | `log_governance_evidence`    | deterministic id of the emitted governance-record evidence artifact; derives from `SHA-256(governance_cycle\|review_id\|approval_record_id\|captured_at)` and is target-agnostic (§ 8)              |
| `__captured_at__`         | yes       | compile-target runtime       | ISO-8601 UTC `YYYY-MM-DDTHH:MM:SSZ` timestamp of the governance-record capture instant; carried into the deterministic evidence-id derivation so the three reference compilers re-derive byte-identical bytes |

Two branch invariants pin the terminal-path semantics of the
governance cycle:

- **Ad-hoc / supervisory_request trigger + empty review_id.** The
  operator's scheduler cannot resolve a scheduled slot from the
  governance-cadence catalogue for the cycle. `__review_id__` is
  empty; downstream steps and the governance-record artifact
  record the ad-hoc marker on the audit envelope.
- **Referral outcome + empty approval_record_id.** The management
  body referred the presented measures back with conditions
  rather than approving in this cycle. `__approval_record_id__`
  is empty; the governance-record artifact records `outcome`
  = `referred` and the audit envelope carries the negative-outcome
  record. The referral is a first-class discharge — a supervisory
  authority reading the ledger sees that the cycle ran, the
  management body reviewed the posture, and the outcome was
  referral.

## 6. Adapter-bound surfaces

Five operator-owned surfaces sit behind adapter shims in the
lifecycle. The framework describes the CACAO contract each surface
writes into; it does not ship the surface.

### 6.1 Governance-cadence catalogue

`schedule_management_review` resolves the operator's documented
management-body cadence configuration against the current
`__governance_cycle__`: which management-body forum owns the
cybersecurity agenda-slot for this cycle, which scheduled meeting
carries it, which agenda position it occupies, and what date the
meeting is scheduled for. The framework ships **no default cadence
catalogue**: the operator's catalogue may be a calendar file, a
Confluence-space page, a governance-tooling record, or a plain
YAML checked into the operator's own governance repository. What
the framework declares is the read-only contract and the closed
`(scheduled | ad_hoc | supervisory_request)` trigger vocabulary the
`resolve_governance_cycle` primitive validates against.

### 6.2 Evidence store — Article 21(2) posture read

`present_risk_posture` reads the operator's evidence store for the
per-clause Article 21(2)(a)–(j) coverage buckets and the open
exceptions inventory. The typical operator wiring reads against
the most recent `nis2_self_assessment` attestation record for the
window (§ 11), plus any per-clause playbook evidence records that
post-date the last-scheduled self-assessment. The framework
declares the read shape and the ten-clause closed vocabulary; it
does not ship the store.

### 6.3 Management-body-decision record surface

`approve_risk_measures` writes to the operator's management-body-
decision record surface: which risk-management measures were
approved, which were referred with conditions, which were rejected,
which signatory role signed off, and when. The framework declares
the closed `(approved | referred_with_conditions | rejected)`
per-measure decision vocabulary and the role-shaped signatory
identifier pattern; the surface itself (a governance-tooling
record, a signed PDF in an evidence repository, a compliance-
platform record) is operator-owned. The role-shaped signatory
constraint is deliberate: the framework refuses to record
personal-name-shaped signatories at this boundary so the public
artifact carries no personal-data leak.

### 6.4 Training-completion attestation source

`approve_risk_measures` also reads the Article 20(2) management-
body training-completion attestation for management-body members:
which members completed the declared training in the reporting
period, which are overdue, and which the operator has declared
`not_required` (e.g. new members within their onboarding grace
window). The completion source is typically the operator's
learning-management surface or a governance-office register; the
framework declares the closed
`(completed | overdue | not_required)` per-member status
vocabulary. The management-body member roster carried here is a
distinct roster from the general-staff training roster the
Article 21(2)(g) `cyber_hygiene_training` and
`security_awareness_training` playbooks discharge against —
Article 20(2)'s "similar training to all employees" clause is
covered under those playbooks, not this one.

### 6.5 Evidence sink

`log_governance_evidence` publishes the emitted OCSF API Activity
governance-record artifact into the operator's evidence store as
the durable audit-evident artifact. The sink is typically the
same evidence store the present step reads against, though the
write path is separate — the governance-record is a first-class
evidence record with its own producing-playbook slug
(`nis2_art20_governance`) so a future `nis2_self_assessment`
collect step against the same store surfaces prior governance-
records under the (a) risk-management policies sub-clause.

## 7. Regulatory anchors

**NIS2 Directive (EU) 2022/2555.** The directive prescribes the
Article 20 management-body governance surface — Article 20(1)
approval of Article 21 measures, oversight of their implementation,
and management-body liability for infringements; Article 20(2)
mandatory training for management-body members and encouragement
of similar training for all employees. Inbound anchors live under
[`content/mappings/nis2/article-20.yaml`](../../content/mappings/nis2/article-20.yaml)
(`nis2:art-20-1` for the management-body approval discipline;
`nis2:art-20-2` for the management-body training discipline). Both
anchors backlink `playbook.nis2_art20_governance@v1` as the
governance-cadence discharge.

**OSCAL controls** — from
[`content/playbooks/nis2_art20_governance/mappings.yaml`](../../content/playbooks/nis2_art20_governance/mappings.yaml):

- **PM-2** *(Information Security Program Leadership Role)* —
  anchors the playbook end-to-end as the management-body
  leadership-role discipline. PM-2 requires the organisation to
  appoint a senior official with the mission and resources to
  coordinate, develop, implement, and maintain an organisation-
  wide information security program; the management-body approval
  cycle NIS2 Article 20(1) names is the board-level oversight
  discipline that closes over that leadership role.
- **SA-2** *(Allocation of Resources)* — additionally anchored on
  the approve step. SA-2 requires the organisation to determine
  security requirements for each system, allocate the resources
  required to protect the system, and establish a discrete line
  item for those resources in organisational programming and
  budgeting documentation. The management-body approval cycle is
  the governance-body decision surface that closes over resource
  allocation for the Article 21 risk-management measures: an
  approved measure that is not resourced is not a discharged
  measure.

The two OSCAL anchors ship as SKELETON placeholders on this
playbook's `mappings.yaml`; the sibling
[`content/controls/control.ict_risk_governance@v1.yaml`](../../content/controls/control.ict_risk_governance@v1.yaml)
consolidates the PM-2 anchor for the wider governance surface.

**MITRE D3FEND v1.0.0** — `D3-PSEP` *Policy and Standards
Enforcement Process* is selected on `approve_risk_measures` as
the closest-fitting defensive technique for the governance-
decision discipline the step discharges: the management-body
approval of the cybersecurity risk-management measures is the
policy-and-standards-enforcement-process discipline on the
governance-body axis — the decision that pins which measures the
operator is committed to implement, on what timeline, and with
which resource allocation. **D3-OAM** *(Operational Activity
Mapping)* additionally anchors `log_governance_evidence`: emitting
the dated governance record that joins the cycle, review,
posture-snapshot, and approval identifiers into the evidence
stream is the operational-activity-mapping discipline, consistent
with the catalogue's D3-OAM anchors on the
`dora_major_incident_reporting` and `cra_srp_notify`
record-composition steps (this supersedes the overlay's earlier
deliberate omission on the log step). The schedule and present
steps carry no D3FEND technique: both are read-only composition
passes over the operator's cadence catalogue and evidence store.

**OCSF v1.3.0** — one class binding.
**API Activity** (class_uid 6003, category Application Activity),
direction `both`. Consumed at the schedule step (read against the
operator's governance-cadence catalogue), at the present step
(read against the operator's evidence store for the current
Article 21(2) posture), and at the approve step (read against the
operator's management-body-decision record surface); emitted at
the log step as the dated governance-record artifact. Envelope
carries `activity_id` 6 (Other) since the OCSF API Activity
vocabulary has no governance-approval verb; the specific
governance semantic is carried in `unmapped.secops_ng`.

## 8. Per-target hand-off

The step outline above is the portable description all three
compilers read against. n8n compiles it into a linear six-node
workflow (`manualTrigger` + four `set` nodes + `noOp`); Temporal
compiles it into a workflow with four activity invocations chained
by `await`; LangGraph compiles it into a `StateGraph` with six
nodes and unconditional-edge topology.

### 8.1 n8n — Set nodes over the four-step lifecycle

[`examples/n8n/nis2_art20_governance/workflow.n8n.json`](../../examples/n8n/nis2_art20_governance/workflow.n8n.json)
carries the CACAO topology as n8n nodes (one `manualTrigger`, four
`set` nodes, one `noOp` terminal). Node ids preserve the CACAO
step ids verbatim. Each action node emits a
`n8n-nodes-base.set` carrying the CACAO I/O contract as editable
assignment rows plus the `x_secops_ng` reference bundles.

Operators bind the Set rows to their connectors:

- `schedule_management_review` → the operator's governance-cadence
  catalogue connector (HTTP Request node against a governance-
  tooling API; Function node evaluating a YAML catalogue checked
  into the operator's governance repository). Writes
  `__review_id__` from the resolved meeting id, or the empty
  string on the ad-hoc / supervisory_request branch.
- `present_risk_posture` → the evidence-store read connector
  (Postgres node against an evidence-record table; HTTP Request
  node against an evidence-store API; S3 node against a sovereign-
  hosted object store carrying the per-producing-playbook
  evidence prefix). Writes `__posture_snapshot_id__`.
- `approve_risk_measures` → the management-body-decision record
  surface plus the training-completion attestation source
  (Function node composing the approval-record shape; HTTP
  Request or Postgres write against the operator's governance-
  tooling record). Writes `__approval_record_id__`, or the empty
  string on the referral branch.
- `log_governance_evidence` → the evidence-sink connector (the
  same Postgres / HTTP / S3 surface the present step read
  against, though the write path is separate). Writes
  `__evidence_id__`.

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/nis2_art20_governance/regenerate.sh
```

Equivalent direct invocation:

```sh
PYTHONPATH=. python -m tools.compile \
    content/playbooks/nis2_art20_governance/playbook.cacao.json \
    --target n8n \
    --out examples/n8n/nis2_art20_governance/workflow.n8n.json
```

The byte-parity golden test under
[`tests/examples/n8n/nis2_art20_governance/test_golden.py`](../../tests/examples/n8n/nis2_art20_governance/test_golden.py)
reruns the same pipeline and fails if the committed artifact
drifts.

### 8.2 Temporal — activities over the four-step lifecycle

[`examples/temporal/nis2_art20_governance/workflow.temporal.py`](../../examples/temporal/nis2_art20_governance/workflow.temporal.py)
carries the CACAO topology as a Temporal workflow with one
activity per action step. `__governance_cycle__` and
`__captured_at__` are threaded through the workflow signature so
the schedule read, the posture composition, the approval record,
and the evidence emit all read against those external playbook-
scoped inputs rather than from a worker-local scope. A worker
restart mid-workflow re-hydrates the same scope against
Temporal's event-history replay contract, so a re-emission of the
governance-record artifact produces a byte-identical
`__evidence_id__`.

Operators bind the activity bodies to real connectors:

- `schedule_management_review` — the governance-cadence catalogue
  read activity; the reference binding resolves the trigger
  branch and returns the scheduled review slot (or empty for
  ad-hoc / supervisory_request).
- `present_risk_posture` — the evidence-store read activity
  composing the per-cycle Article 21(2) view.
- `approve_risk_measures` — the management-body-decision record
  activity plus the training-completion attestation read. On
  the referral branch the activity returns the referral marker
  with empty `approval_record_id`; the workflow does not
  branch, the negative outcome is carried through.
- `log_governance_evidence` — the evidence-emission and sink
  activity. The `__evidence_id__` derivation happens at the
  primitive layer (not the compile layer) — the activity
  computes the hash and writes the record to the operator's
  declared sink.

To regenerate the compiled artifact from the repo root:

```sh
./examples/temporal/nis2_art20_governance/regenerate.sh
```

The byte-parity golden test under
[`tests/examples/temporal/nis2_art20_governance/test_golden.py`](../../tests/examples/temporal/nis2_art20_governance/test_golden.py)
reruns the emitter and fails if the committed artifact drifts.
Activity bodies remain `NotImplementedError` stubs by design in
the shipped example; the operator supplies the bindings.

### 8.3 LangGraph — nodes and state over the four-step lifecycle

[`examples/langgraph/nis2_art20_governance/graph_spec.json`](../../examples/langgraph/nis2_art20_governance/graph_spec.json)
carries the CACAO topology as a target-neutral GraphSpec (nodes,
edges, conditional edges — the last being empty for this linear
playbook); [`state_bindings.py`](../../examples/langgraph/nis2_art20_governance/state_bindings.py)
emits the `TypedDict` state and the `@tool`-decorated action
wrappers plus the agentic-extension hook. `__governance_cycle__`
and `__captured_at__` are expressed as state fields threaded
through node bodies, so a checkpoint reload re-hydrates the same
scope.

The GraphSpec `nodes` array carries only the four intermediate
action step ids; start and end sentinels are pinned structurally
via `entry` and `end_sentinel` (this is the LangGraph projection
contract the G-03 parity test asserts against — the same canonical
CACAO step space is present, in a different structural shape than
n8n's node array).

The audit-mirror sibling [`_audit_mirror.py`](../../examples/langgraph/nis2_art20_governance/_audit_mirror.py)
(see [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md))
carries the OTel-free durable audit trail on LangGraph runs where
the operator has not wired an OTLP collector.

Operators bind the tool bodies to real connectors:

- `schedule_management_review` → governance-cadence catalogue
  read tool.
- `present_risk_posture` → evidence-store read tool composing
  the Article 21(2) posture view.
- `approve_risk_measures` → management-body-decision record
  tool plus the optional agentic-extension hook (an LLM-
  assisted reviewer that drafts the natural-language rationale
  for the referral outcome or for the per-measure conditions,
  as a supplement to the deterministic decision-vocabulary
  record, not a replacement).
- `log_governance_evidence` → evidence-emission and sink tool.

To regenerate the compiled artifacts from the repo root:

```sh
./examples/langgraph/nis2_art20_governance/regenerate.sh
```

## 9. Byte-parity across compile targets — the G-03 invariant

The governance-record artifact each execution emits is anchored by
a deterministic `artifact_id` derivation:

```
artifact_id = "ev_" + SHA-256(governance_cycle | review_id | approval_record_id | captured_at)[:16]
```

The input is UTF-8, with single pipe separators and no surrounding
whitespace, and the `compile_target` is **deliberately not part of
the input**. A replay of the same
`(governance_cycle, review_id, approval_record_id, captured_at)`
tuple under n8n, Temporal, or LangGraph produces byte-identical
governance-record bytes. Both empty-string branches (ad-hoc
trigger with empty `review_id`; referral outcome with empty
`approval_record_id`) hash through cleanly — the pipe separators
carry the empty positions verbatim.

Concretely, across the three targets:

- **n8n** — the evidence emitter reads `execution_id` from the
  workflow-execution scope and `captured_at` from the emitting
  node's evaluation. The `artifact_id` derivation is authored in
  the emitter template, not in the target-specific Function
  nodes, so re-executions and n8n version changes do not drift
  the hash.
- **Temporal** — the emitter activity reads `execution_id` as the
  Temporal workflow-run id and `captured_at` from a workflow-
  local timestamp threaded through the activity call, not from
  `datetime.utcnow()` inside the activity body. A history-replay
  re-derives the identical hash.
- **LangGraph** — the emitter tool reads `execution_id` from the
  LangGraph thread/checkpoint id and `captured_at` from state,
  not from `time.time()` inside the tool body. A checkpoint
  reload re-derives the identical hash.

The byte-parity invariant is asserted across all three targets by
the golden tests under
[`tests/examples/nis2_art20_governance/`](../../tests/examples/nis2_art20_governance/)
and per-target under
[`tests/examples/n8n/nis2_art20_governance/`](../../tests/examples/n8n/nis2_art20_governance/)
and
[`tests/examples/temporal/nis2_art20_governance/`](../../tests/examples/temporal/nis2_art20_governance/).

The reason for the target-agnostic anchor is regulatory, not
stylistic. The Chapter VII supervisory posture is a posture about
the *operator's management-body approval discipline*, not about
the *orchestrator that runs the approval cycle*. An operator who
migrates from n8n to Temporal (or runs two cycles concurrently on
different targets during a migration) must be able to consolidate
their governance ledger without dedup drift; the framework
refuses the drift-shape by construction.

## 10. Exporting results as supervisory-reporting evidence

Under Chapter VII the operator is expected to produce, on
supervisory-authority request, the current state of their
Article 20 management-body approval discipline. Four fields on
the emitted governance-record artifact are the supervisory-facing
surface:

- **`governance_cycle`** — the identifier from
  `__governance_cycle__`. Supervisory correspondence quotes this
  reference so the operator's response can be joined against the
  supervisory-authority's request record.
- **`trigger`** — one of `scheduled`, `ad_hoc`,
  `supervisory_request`. The supervisory reader learns whether
  this cycle ran on the operator's documented cadence, on an
  operator-initiated on-demand basis, or against a supervisory-
  authority request.
- **`outcome`** — one of `approved` or `referred`. The
  supervisory reader learns whether the management body approved
  the presented measures or referred them back with conditions.
- **`review_id` and `approval_record_id`** — the per-cycle
  references into the operator's own governance surfaces so the
  supervisory reader can request the underlying artifacts (the
  meeting minutes, the signed approval record) as follow-up.

The governance-record artifact is the audit-evident artifact
retained on the operator's evidence store. Wiring it into the
supervisory-authority-facing envelope is an operator
responsibility: the framework does not ship the per-authority
submission channel (each EU competent authority publishes its own
reporting portal, submission format, and reference-number
allocation). What the framework produces is the canonical, dated,
byte-deterministic record the operator's submission wraps.

Referral outcomes on the governance ledger are the leading signal
for the operator's re-approval-cycle planning — a `referred`
outcome on cycle *n* names the follow-up cycle *n+1* the same
governance body must run once the referral conditions are met.

## 11. Playbook chain — where nis2_art20_governance sits

The Article 20 governance cycle interacts with sibling playbooks
on the operator's substrate. The interactions are documented at
the CACAO source and in `mappings.yaml`, and are worth calling
out in a cookbook context so a reader can situate the workflow:

- **`nis2_self_assessment` — Article 21(2) roll-up.** The
  present step reads the most recent whole-Article-21 attestation
  record composed by
  [`nis2_self_assessment.md`](nis2_self_assessment.md), plus any
  per-clause playbook evidence records that post-date it. The two
  playbooks are complementary: the self-assessment composes the
  posture the management body reads; the Article 20 governance
  cycle records the management body's decision on that posture
  and closes the governance ledger. An operator running both on
  aligned cadences (self-assessment on the (f)-effectiveness
  cadence, Article 20 approval on the following management-body
  meeting) has a two-artifact discharge covering both the
  posture and the approval discipline.
- **`cyber_hygiene_training` and `security_awareness_training` —
  Article 21(2)(g) general-staff training.** Article 20(2)'s
  "similar training to all employees" clause is discharged
  under these two Article 21(2)(g) sibling playbooks
  ([`cyber_hygiene_training.md`](cyber_hygiene_training.md),
  [`security_awareness_training.md`](security_awareness_training.md)) —
  not under this playbook. The Article 20(2) training-
  completion attestation this playbook carries narrows to the
  management-body member roster specifically; that roster is a
  distinct roster from the general-staff training roster.
- **`incident_management` — Chapter VI Article 23.** A
  significant-incident event that triggers Chapter VI reporting
  may also require an on-demand Article 20 approval cycle to
  approve the operator's compensating measures put in place
  after the incident. Practice is to run an on-demand cycle
  against a fresh `__governance_cycle__` after any Article 23-
  significant incident so the supervisory-facing management-body
  approval record reflects the current substrate.
- **The operator's risk-management policy under Art. 21(2)(a).**
  The management-body approval this playbook records is the
  approval of the Article 21 risk-management measures — the
  policy authoring surface, the policy content itself, and the
  operator's threshold and cadence documentation all live
  upstream of this playbook. The workflow applies the approval
  discipline against a documented programme; it does not author
  the programme.

## 12. What this cookbook deliberately does not cover

- **The governance-cadence catalogue.** Which management-body
  forum, which meeting cadence, which agenda-slot conventions —
  all operator-owned. The framework describes the read contract
  and the closed trigger vocabulary; it does not ship the
  catalogue.
- **The management-body member roster.** The roster the Article
  20(2) training-completion attestation reads against lives in
  the operator's governance documentation upstream of the
  playbook. The framework declares the closed
  `(completed | overdue | not_required)` per-member status
  vocabulary; it does not ship the roster.
- **The training programme itself.** Article 20(2) requires
  management-body training; the operator authors the curriculum,
  chooses the delivery format, and picks the training provider.
  The framework records the completion attestation; it does not
  author or deliver the training.
- **The management-body-decision record surface.** The signed
  approval record surface (governance-tooling record, signed PDF
  in an evidence repository, compliance-platform record) is
  operator-owned. The framework declares the closed per-measure
  decision vocabulary and the role-shaped signatory identifier
  pattern; it does not ship the surface.
- **The evidence-sink write path.** The dated governance-record
  artifact is a plain JSON envelope; where the operator persists
  it (Postgres, S3-compatible object store on EU sovereign
  infrastructure, compliance platform, governance-tooling
  record) is operator-owned.
- **The supervisory-authority submission channel.** Each EU
  competent authority publishes its own Chapter VII submission
  surface (per-authority form, per-authority reference-number
  allocation, per-authority channel of record). The framework
  produces the governance-record artifact; the operator wraps it
  into the per-authority envelope.
- **DORA cross-regime management-body approval.** DORA's
  equivalent management-body governance surface (Art. 5(2)(a)
  governance and organisation; Art. 5(2)(b) approval of the ICT
  risk-management framework by the management body) is regime-
  specific to financial entities and anchors on a different
  approval-cycle catalogue. A future card may add a
  DORA-side inbound anchor once the atom is confirmed as a
  distinct scope rather than a lift of the NIS2 anchor. Until
  then the closure lands via the NIS2 Article 20 umbrella.

## 13. References

- OASIS CACAO v2.0 specification.
- NIS2 Directive (EU) 2022/2555 — Article 20(1) (management-body
  approval of Article 21 measures, oversight, liability),
  Article 20(2) (management-body training, encouragement of
  similar training for all employees), Article 21(2)(a–j)
  (minimum measures — the downstream obligation surface Art.
  20(1) anchors on), Chapter VI (Article 23, significant-
  incident reporting), Chapter VII (Articles 32–33, supervision
  and enforcement).
- NIST SP 800-53 Rev. 5 — PM-2 (Information Security Program
  Leadership Role), SA-2 (Allocation of Resources).
- MITRE D3FEND v1.0.0 — D3-PSEP Policy and Standards Enforcement
  Process.
- OCSF v1.3.0 — API Activity (class_uid 6003) event class.
- ENISA — technical implementation guidance for NIS2 Article 20
  management-body governance and cybersecurity training
  obligations.
