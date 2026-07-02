# executive_metrics — cookbook walkthrough

Recurring KPI/KRI rollup into a board-ready summary artifact under
NIS2 Article 21(2)(f) and DORA Articles 5 and 6. The
`playbook.executive_metrics@v1` CACAO playbook operates the
per-cadence rollup discipline the operator's effectiveness-assessment
policy owes: it loads the pinned KPI/KRI catalogue version against
the declared rollup window, validates each entry against the
content-model metrics schema, evaluates every catalogue entry against
the operator's telemetry / workflow / control-attestation sources,
groups the evaluations by `control_ref` to derive a composite
control-effectiveness score, branches on whether any evaluation
matched its breach band to annotate a board-attention flag, and
emits a structured board-ready summary artifact for handoff to the
operator's downstream board pack pipeline.

The playbook is the **reporting-side materialisation** of the
periodic-review obligation the risk-management framework carries.
It is the aggregation companion to the per-workflow measurement
disciplines the framework's other playbooks operate: `alert_triage`,
`detection_engineering`, `mfa_secured_comms`,
`crypto_posture_management`, `infra_posture_management`,
`iam_auditor`, `onboarding_offboarding_tracker`, `backup_recovery`,
`patch_management`, `post_incident_review`, and the rest each emit
KPIs and KRIs into the catalogue against their own audit-evident
surfaces; `executive_metrics` reads that catalogue on a cadence and
produces the board-facing rollup a reviewer, board member, or
supervisory authority reads.

```
per-workflow playbooks (audit / detection / posture / response)
    └── emit KPI / KRI evaluations against telemetry / attestation

executive_metrics (recurring, per-window rollup)
    └── resolve catalogue ─► evaluate metrics ─► score control effectiveness
        ─► raise board-attention flag (if breach) ─► emit board summary
```

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the catalogue
resolution, per-metric evaluation, control-effectiveness scoring,
board-attention branching, and board-summary emission land in each
target.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/executive_metrics/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / OCSF / CRA overlay
└── playbook.cacao.json          # canonical CACAO v2 source (playbook.executive_metrics@v1)

content/mappings/cra/article-13-2-3-risk-assessment-metrics.yaml
                                  # CRA Art. 13(2)–(3) inbound anchor —
                                  # recurring KPI/KRI materialisation of
                                  # the manufacturer risk-assessment
                                  # obligation, sibling to
                                  # article-13-risk-assessment (the
                                  # procedural shell)
```

The CACAO source is canonical. The five action steps, one
`if-condition` step, and the `start` / `end` wiring nodes are the
deterministic policy the playbook *means* — a resolve → evaluate →
score → (branch on any breach band) → optionally annotate → emit
chain. The three worked examples under
`examples/{n8n,temporal,langgraph}/executive_metrics/` are the same
playbook compiled into three orchestrator idioms. Everything else —
the KPI/KRI catalogue store the resolve step reads, the telemetry /
workflow / control-attestation sources the evaluate step reads, and
the board pack pipeline endpoint the emit step hands off to — is the
operator's data plane.

The rollup operates on aggregate evaluations and per-control scores
rather than on personal data directly; where per-responder or
per-principal identifiers appear in the contributing playbooks'
metric evaluations (e.g. ack-latency snapshots, per-principal
enforcement state), those are inherited from those playbooks' own
GDPR Art. 30 Records of Processing Activity. `executive_metrics`
therefore has no per-workflow RoPA of its own — the personal-data
surface is upstream.

## 2. CACAO topology and lifecycle binding

The playbook ships eight steps: one `start`, five `action`, one
`if-condition`, and one `end`. The topology is a linear
resolve → evaluate → score chain, then a single branch on the
breach-band question, with both branches converging on the same emit
step so the rollup is single-output.

| Step suffix | Step                                | Discipline                                                                                                                                                                                                                              | Status         |
|-------------|-------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | rollup-start                         | edge wiring only — no body                                                                                                                                                                                                              | n/a            |
| `…000002`   | resolve KPI/KRI catalogue            | load the pinned catalogue version from `__catalog_ref__`; validate each entry against `content-model/metrics.schema.json`; entries failing validation are recorded for the corrective-action register and excluded from the score      | operator-bound |
| `…000003`   | evaluate metrics over window         | compute each entry's `measurement.formula` over `__rollup_window__` against the operator's telemetry / workflow / control-attestation sources; carry the matched threshold band and the lower-layer input bindings on each evaluation  | operator-bound |
| `…000004`   | score control effectiveness          | group evaluations by `control_refs[]`, derive a composite per-control score, aggregate to a programme-level score in `0.0..1.0`; scoring policy (weighting, KRI penalty, missing-evidence treatment) is operator-supplied               | deterministic  |
| `…000005`   | any breach band hit? (if-condition)  | branch on whether any evaluation matched its `breach` threshold band                                                                                                                                                                    | deterministic  |
| `…000006`   | raise board-attention flag           | annotate the in-flight summary with a board-attention flag so the downstream pack pipeline surfaces the breach band on the cover page; pure annotation — no notification is sent here                                                   | deterministic  |
| `…000007`   | emit board summary                   | render the structured board-ready summary artifact and hand it off to the operator's board pack pipeline endpoint                                                                                                                       | operator-bound |
| `…000008`   | rollup-end                           | edge wiring only — no body                                                                                                                                                                                                              | n/a            |

All five action steps carry the CACAO I/O contract (`in_args` /
`out_args`) plus `x_secops_ng` reference bundles (control, metric).
One execution runs the chain exactly once per declared rollup window.

> The playbook maturity is `experimental` on the workflow-local
> content marker. The mappings overlay pins the control and telemetry
> surface (OSCAL CA-2 / CA-7 / PM-6 / PM-9 / RA-3, OCSF API Activity)
> and documents the intentional D3FEND / SigmaHQ absences (see § 4).
> The n8n, Temporal, and LangGraph reference emitters ship
> deterministic emitter output under
> `examples/{n8n,temporal,langgraph}/executive_metrics/`.

## 3. Lifecycle contract — the five action states

The per-window payload — the resolved catalogue entries (validated
against `content-model/metrics.schema.json`), the per-metric
evaluations (observed value, matched threshold band, lower-layer
artifact bindings), the composite control-effectiveness score in
`0.0..1.0`, the optional board-attention flag, and the emitted
board-ready summary artifact — is aggregate reporting content. The
personal-data surface is inherited from the contributing playbooks
(their RoPAs govern per-responder / per-principal identifiers that
appear in upstream metric inputs); the rollup does not introduce a
new personal-data surface of its own.

**resolve KPI/KRI catalogue** (`…000002`)
:   Read step. Loads the operator's pinned KPI/KRI catalogue version
    from `__catalog_ref__` (path, registry URI, or content-store
    reference). Each entry MUST validate against
    `content-model/metrics.schema.json` before it enters the rollup;
    entries that fail validation are recorded for the corrective-
    action register and excluded from the score so a malformed entry
    cannot inflate or deflate effectiveness. Anchored on OSCAL RA-3
    (Risk Assessment) — the recurring per-entry validation against
    the metrics schema is the per-cadence materialisation of the
    risk-assessment discipline against the KPI/KRI corpus. Feeds
    `kri.corrective_action_overdue@v1` on validation failures.
    Read-only: no catalogue mutation, no metric authorship.

**evaluate metrics over window** (`…000003`)
:   Read + derive step. For each catalogue entry, computes the value
    defined by the metric's `measurement.formula` over
    `__rollup_window__` against the operator's telemetry /
    workflow / control-attestation source. Each evaluation carries
    the matched threshold band (target / warn / breach) and
    references the lower-layer artifacts (playbook step, detection,
    control, telemetry) the metric is bound to via its `inputs[]`.
    Anchored on OSCAL CA-7 (Continuous Monitoring) — the recurring
    per-cadence rollup is the per-window materialisation of the
    continuous-monitoring strategy against the catalogue. Also
    anchored on OSCAL PM-6 (Information Security and Privacy
    Measures of Performance) as the measures-of-performance surface
    the per-metric evaluations discharge. Binds against the
    operator's telemetry surface; emits `__metric_evaluations__`.
    Feeds `kpi.review_completion_sla@v1` and
    `kpi.corrective_action_close_rate@v1`. Read-only: no source
    mutation, no metric authorship.

**score control effectiveness** (`…000004`)
:   Deterministic in-band derivation. Groups the evaluations by
    `control_refs[]` and computes a composite control-effectiveness
    score per control; aggregates to a programme-level score in
    `0.0..1.0`. The scoring policy (per-control weighting, KRI
    penalty function, missing-evidence treatment) is operator-
    supplied; the playbook pins only the input contract and the
    output shape so the score is reproducible from the same
    evaluations. Anchored on OSCAL CA-2 (Control Assessments) as the
    per-cadence assessment surface, and on OSCAL PM-9 (Risk
    Management Strategy) as the programme-level aggregation surface.
    Emits `__control_effectiveness_score__`. Feeds
    `kri.control_effectiveness@v1`.

**any breach band hit?** (`…000005`, if-condition)
:   Deterministic in-band branch. `on_success` (true — at least one
    evaluation matched its `breach` band) routes to the raise-board-
    attention-flag step; `on_failure` (false) skips the annotation
    and goes straight to emit. Both branches converge on the emit
    step so the rollup is single-output regardless of branch. No
    body, no external surface, no side effect.

**raise board-attention flag** (`…000006`)
:   Deterministic in-band annotation. Sets the board-attention flag
    on the in-flight summary so the downstream pack pipeline
    surfaces the breach band on the cover page. Pure annotation —
    no notification is sent here, no ticket is opened, no incident
    is escalated. The board pack pipeline owns the distribution
    channel and cadence; this step's job is to make the flag
    visible on the artifact the pipeline picks up.

**emit board summary** (`…000007`)
:   Emit step. Renders the structured board-ready summary artifact
    (window, per-metric evaluations with threshold bands, per-control
    effectiveness scores, programme-level score, and — if set — the
    board-attention flag) and hands it off to the operator's board
    pack pipeline endpoint. Anchored on OSCAL PM-6 alongside the
    evaluate step. Emits `__board_summary_id__`. Output is content-
    only — distribution, signing, and archival of the emitted summary
    are out of scope of the playbook and are discharged by the
    operator's existing board pack pipeline.

The three surface-touching action steps (resolve, evaluate, emit) are
operator-bound runtime seams: the framework ships neither the
catalogue store, the telemetry sources, nor the board pack pipeline
endpoint. The score and annotate steps are deterministic derivations
in-band against the resolved evaluations. The playbook is the
portable description of *what* the operator's stack should do per
rollup window; binding the surface seams to real endpoints is the
operator's job.

> **LM determinism.** Catalogue validation, per-metric evaluation,
> control-effectiveness scoring, breach-band branching, and board-
> summary emission are structured reads and derivations against
> operator-owned surfaces, not free-text reasoning steps. The
> playbook binds no DSPy signature — there is no LM-driven step at
> this layer. See [`docs/FOUNDATION.md`](../FOUNDATION.md) § LLM
> determinism. If an operator wires an LM-driven enrichment on top of
> the emit-board-summary step (rendering the structured artifact into
> a board-narrative paragraph, for instance) as a private extension,
> the framework-wide EU-resident LM endpoint guard re-applies the
> check at process startup — see
> [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 4. Regulatory anchors

**NIS2 Article 21(2)(f)** — policies and procedures to assess the
effectiveness of cybersecurity risk-management measures, with
results archived. NIS2 enforcement crossed on 2 July 2026; the
effectiveness-assessment obligation is one of the audit-evident
measures a supervisory authority reads first when assessing the
operator's Art. 21 posture. The `executive_metrics` playbook is the
**per-cadence materialisation of the KPI/KRI rollup and control-
effectiveness scoring half of that obligation** — the per-rule-version
measure-state half sits with `detection_engineering`. The two
playbooks discharge complementary halves of the effectiveness-
assessment surface: `detection_engineering` at the per-rule-version
measure-state layer, `executive_metrics` at the KPI/KRI rollup and
control-effectiveness scoring layer. The inbound anchor at
[`content/mappings/nis2/article-21-2-f.yaml`](../../content/mappings/nis2/article-21-2-f.yaml)
currently lists `playbook.detection_engineering@v1` on its
`playbook_refs`; the outbound overlay on `executive_metrics`
deliberately holds its NIS2 Art. 21(2)(f) pin pending a separate
inbound-closure card that adds `playbook.executive_metrics@v1`
alongside the existing detection_engineering entry, mirroring the
iam_auditor / post_incident_review / codebase_vuln_management /
onboarding_offboarding_tracker / contractual_obligations_tracker
precedent that gap notes are separate cards, not scope creep on a
single-purpose mappings PR. The playbook's own
`external_references` in `playbook.cacao.json` cite NIS2 Art. 21(2)(f)
directly as the primary regulatory anchor.

**DORA Article 6** — ICT risk-management framework, periodic
review. Regulation (EU) 2022/2554 Art. 6 requires financial entities
to maintain an ICT risk-management framework as part of their overall
risk-management system and to periodically review and, where
appropriate, update it. The recurring KPI/KRI rollup and the dated
control-effectiveness score are the audit-evident discharge of the
periodic-review obligation — the operator can point at the per-window
board-summary artifacts as evidence the framework is under active
measurement rather than sitting on a shelf. The playbook's outbound
pin against `dora:art-6-framework` is held for the same reason as the
NIS2 Art. 21(2)(f) pin: the inbound entry at
[`content/mappings/dora/article-6.yaml`](../../content/mappings/dora/article-6.yaml)
currently carries `playbook_refs: []` and does not backlink
`playbook.executive_metrics@v1`; the outbound pin lands together with
the inbound update on a separate inbound-closure card.

**DORA Article 5** — governance and organisation. Regulation (EU)
2022/2554 Art. 5 requires the management body to define, approve,
oversee, and be accountable for the implementation of the ICT
risk-management framework, including through periodic reporting on
its effectiveness. The board-ready summary artifact emitted at the
rollup tail is the reporting-surface materialisation of the Art. 5
oversight discipline — the same surface that discharges Art. 6's
periodic review also gives the management body the dated evidence
Art. 5 asks for. As with Art. 6, the outbound pin against
`dora:art-5-governance` (inbound at
[`content/mappings/dora/article-5.yaml`](../../content/mappings/dora/article-5.yaml),
`playbook_refs: []`) is held pending the inbound-closure card.

**CRA Article 13(2)–(3)** — cybersecurity risk assessment across the
product lifecycle. Regulation (EU) 2024/2847 Art. 13(2)–(3) requires
manufacturers of products with digital elements to undertake a
cybersecurity risk assessment and to take its outcome into account
across the design, development, production, delivery, and maintenance
phases. The `executive_metrics` playbook is the **recurring KPI/KRI
materialisation** that shows the risk posture remains live: per-window
evaluations against the pinned catalogue, per-control effectiveness
score, and the board-attention flag on breach-band excursions.
Inbound anchor at
[`content/mappings/cra/article-13-2-3-risk-assessment-metrics.yaml`](../../content/mappings/cra/article-13-2-3-risk-assessment-metrics.yaml)
(`cra:art-13-2-3-risk-assessment-metrics`) — the metrics companion to
`cra:art-13-risk-assessment` in `article-13.yaml`, which covers the
procedural shell (dated risk-management policy + recurring framework
review). The outbound CRA pin is present on the mappings overlay
because the CRA inbound explicitly backlinks the playbook.

**OSCAL controls** exercised by the workflow (from
[`content/playbooks/executive_metrics/mappings.yaml`](../../content/playbooks/executive_metrics/mappings.yaml)):
CA-2 (Control Assessments — anchors the score-control-effectiveness
step as the per-cadence assessment surface), CA-7 (Continuous
Monitoring — anchors the evaluate-metrics step's recurring rollup
discipline), PM-6 (Information Security and Privacy Measures of
Performance — anchors the evaluate-metrics and emit-board-summary
steps as the measures-of-performance surface), PM-9 (Risk Management
Strategy — anchors the score-control-effectiveness step's programme-
level aggregation), and RA-3 (Risk Assessment — anchors the resolve-
catalogue and evaluate-metrics steps' input-validation surface).
IR-4 (Incident Handling) and AU-2 (Event Logging) are intentionally
NOT pinned — the rollup consumes incident-derived KPIs / KRIs as
input evaluations but does not itself detect / triage / contain /
remediate any incident (that surface is carried by the per-incident
playbooks), and the emitted board-summary artifact is a content
artifact handed off to the operator's board pack pipeline, not an
audit-event emission (the underlying API Activity records are consumed
by the operator's existing OCSF store under its own AU-2 policy,
upstream of this playbook).

**MITRE D3FEND v1.0.0** — **intentionally not referenced.** The
`d3fend` array on the mappings overlay is empty by design. D3FEND
v1.0.0 frames its defensive techniques around runtime countermeasures
(account monitoring, software inventory, network isolation,
configuration inventory, and so on) — techniques applied against an
adversary in progress on a live surface. An executive rollup is a
control-effectiveness assessment and reporting surface: resolve
catalogue, evaluate metrics, score effectiveness, branch on breach
band, emit summary. No attack is being defended against in this
workflow, so no D3FEND technique applies without misrepresenting the
technique. This mirrors the documented-absence discipline established
by the `on_call_rotation` handoff-brief gap note, the
`contractual_obligations_tracker` schedule-review and emit-obligation-
evidence gap notes, and the `infra_posture_management` emit-posture-
evidence gap note: pin the closest available technique only where the
discipline matches, and document the absence in-line where it does
not, rather than inventing coverage.

**OCSF v1.3.0** — one class binding.
`API Activity` (class_uid 6003, category Application Activity),
direction `both`, is consumed at the resolve-catalogue step (the read
call against `__catalog_ref__` that hydrates the per-entry KPI/KRI
bodies) and at the evaluate-metrics step (the per-metric measurement
reads over `__rollup_window__` against the operator's telemetry /
workflow / control-attestation sources); emitted at the emit-board-
summary step (the dispatch of the structured board-ready summary
artifact to the operator's board pack pipeline endpoint). The
`api_activity` records carry the request metadata that
`kpi.review_completion_sla@v1` reads to report per-window rollup-
delivery freshness; failures or delays surface against the
`kri.corrective_action_overdue@v1` annotation surface. The score-
control-effectiveness and raise-board-attention-flag steps are
deterministic in-band derivations against `__metric_evaluations__`
and do not touch the telemetry surface.

**SigmaHQ** — **intentionally not referenced.** An executive rollup
is a reporting workflow, not a detection workflow; no Sigma rule IDs
are pinned on this overlay. The per-workflow playbooks that feed the
catalogue with detection-derived KPIs and KRIs carry their own Sigma
references where the discipline matches.

## 5. Per-target hand-off

### 5.1 n8n — operator-edited Set rows over the rollup topology

`examples/n8n/executive_metrics/workflow.n8n.json` carries the CACAO
topology as n8n nodes (`manualTrigger`, five `set` nodes for the
action bodies, an `if` node for the breach-band branch, and one
`noOp` terminal), with node ids preserving the CACAO step ids
verbatim. The five action steps emit `n8n-nodes-base.set` nodes
carrying the CACAO I/O contract as editable assignment rows plus the
`x_secops_ng` reference bundles (control, metric). The linear
sequencing plus the single branch carry via `on_completion` /
`on_success` / `on_failure` edges on the emitted `connections` block.
The lossy translations are recorded in `meta.secops_ng_notes` so the
integrator sees exactly which seams need attention.

Operators bind the Set rows to their connectors:

- `resolve KPI/KRI catalogue` → the operator's KPI/KRI catalogue
  store (path on a content-repo mount, a registry URI, a policy-as-
  code artifact store, or a GRC platform's metric catalogue API)
  exposing per-entry KPI/KRI bodies validated against
  `content-model/metrics.schema.json`; writes the resolved catalogue
  into the workflow state.
- `evaluate metrics over window` → the operator's telemetry /
  workflow / control-attestation sources (SIEM query surface, OCSF
  event store, workflow-execution telemetry, control-attestation
  store) exposing the per-formula reads over `__rollup_window__`;
  writes `__metric_evaluations__`.
- `emit board summary` → the operator's board pack pipeline endpoint
  (an object store the pack pipeline reads from, a GRC platform
  ingest API, a document store, or a scheduled-report handoff queue);
  writes `__board_summary_id__`.

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/executive_metrics/regenerate.sh
```

To import into an n8n instance: open the workflows list, choose
**Import from File**, and select
`examples/n8n/executive_metrics/workflow.n8n.json`. The workflow is
inactive by default — review and bind the Set rows to your own
connectors before activating. The emitted workflow is a *snapshot of
intent*, not a runnable playbook.

### 5.2 Temporal — `@activity.defn` bodies

`examples/temporal/executive_metrics/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action, with the branch handled
inside the workflow method as a straight Python `if` against the
evaluated metric list. Each activity documents its operator-bound
seam (resolve / evaluate / emit) or its deterministic derivation
(score / annotate).

Temporal is a natural fit for the recurring rollup discipline: each
declared rollup window becomes one workflow run; retries against
transient failures on the catalogue store, the telemetry surface, or
the board pack pipeline endpoint get first-class Temporal semantics
(activity retry policy per seam); replay against the same Temporal
event history re-derives the same evaluation list, the same control-
effectiveness score, and the same board-summary artifact because the
scoring policy is deterministic against the resolved evaluations.
Schedules (Temporal `Schedule`) give the operator a durable per-
cadence trigger — monthly, quarterly, or an operator-supplied cadence
against `__rollup_window__` — without a bespoke cron surface.

### 5.3 LangGraph — `@tool` wrappers + agentic-extension hook

`examples/langgraph/executive_metrics/state_bindings.py` carries the
`TypedDict` state and the `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (nodes and the
on-completion / on-success / on-failure edges from resolve-catalogue
through emit-board-summary to the terminal end); `assemble.py` is the
hand-written reference assembly that wires the GraphSpec + bindings
into a `langgraph.graph.StateGraph`.

LangGraph is the agentic target — an operator who wants to layer an
LM-driven enrichment on top of the `emit board summary` step
(rendering the structured artifact into a board-narrative paragraph,
for instance) fills that as a private extension. The framework-wide
EU-resident LM endpoint guard re-applies the check at process startup
(`compilers/_shared/lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
The compiler never embeds an LLM SDK.

### 5.4 Cross-target parity

All three reference targets are present in the tree today
(`examples/n8n/executive_metrics/`,
`examples/temporal/executive_metrics/`,
`examples/langgraph/executive_metrics/`). Each ships a committed
emitter artifact (n8n workflow JSON, Temporal worker module,
LangGraph GraphSpec + bindings). The deterministic derivations
(score-control-effectiveness against `__metric_evaluations__`, the
breach-band branch, the board-attention annotation) re-derive the
same output bytes on n8n / Temporal / LangGraph against the same
resolved evaluations — the CORE-FANOUT byte-parity contract holds on
this playbook as it does on the per-workflow measurement siblings.

## 6. Observability — OTel + AuditTrail in every target

Every emitted action opens an OpenTelemetry span and appends an
`AuditRecord` to a context-local `AuditTrail` *before* the operator-
bound seam call or the deterministic derivation. The mirror runs
unconditionally, ahead of any OTLP exporter, so the audit property
holds even when the operator has not configured a collector —
typical for disconnected, sovereign, or air-gapped deployments.

Span attributes use the shared `secops_ng.*` keyspace and are stable
across the three targets:

| Attribute key                | Carries                                              |
|------------------------------|------------------------------------------------------|
| `secops_ng.playbook.id`      | CACAO playbook id (`playbook--…`).                   |
| `secops_ng.playbook.version` | Content version pinned in the playbook.              |
| `secops_ng.step.id`          | CACAO step id (`action--…` / `if-condition--…`).     |
| `secops_ng.step.name`        | Human-readable step label.                           |
| `secops_ng.step.type`        | CACAO step type (`action`, `if-condition`, ...).     |
| `secops_ng.tool.name`        | Emitted tool / activity / Code-node function name.   |
| `secops_ng.compile.target`   | `n8n` / `temporal` / `langgraph` discriminator.      |

The OTLP exporter endpoint is operator-supplied
(`OTEL_EXPORTER_OTLP_ENDPOINT`). The compiler never sets a default
and never imports a vendor SDK; pointing the exporter at a managed
APM is a downstream choice the operator owns end-to-end. The
sovereignty posture asks for an EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline.

## 7. Metrics — what the rollup discipline exposes

The rollup is itself instrumented against the same catalogue it
reads. Four catalogue entries are stamped by the playbook's own
steps:

- **`kri.corrective_action_overdue@v1`** — per-window count of
  catalogue entries that failed validation at the resolve step and
  were routed to the corrective-action register, plus any evaluation
  that arrived past its declared freshness on the emit-board-summary
  dispatch. Rising values indicate the catalogue is drifting away
  from the metrics schema faster than the operator's remediation
  cadence.
- **`kpi.review_completion_sla@v1`** — per-window measurement of
  rollup-delivery freshness against the declared cadence. Stamped by
  the evaluate-metrics and emit-board-summary steps. Falling values
  indicate the rollup is delivering late against the periodic-review
  cadence NIS2 Art. 21(2)(f) and DORA Art. 6 anchor.
- **`kpi.corrective_action_close_rate@v1`** — per-window rate at
  which the corrective actions the previous rollup raised were
  closed against the declared close-out policy. Stamped by the
  evaluate-metrics step.
- **`kri.control_effectiveness@v1`** — the composite programme-level
  score itself, exposed on the catalogue for downstream dashboarding
  and trend analysis. Stamped by the score-control-effectiveness
  step.

The catalogue entries pin the field-level read contract; the
framework does not ship a hosted dashboard. Operators dashboard the
series against their own metrics backend.

## 8. Operator customisation points

The playbook is a per-window rollup machine; the *policy* it
exercises is the operator's. The customisation seams:

- **Catalogue version pinning.** `__catalog_ref__` is the operator's
  pointer to the pinned KPI/KRI catalogue version for the run (a
  path, a registry URI, a policy-as-code artifact reference, or a
  GRC catalogue-API URL). Pinning lets the operator re-run the same
  window against the same catalogue at any later date and reproduce
  the score bit-for-bit. The framework binds neither the catalogue
  store nor the version-selection policy — the operator owns the
  catalogue's own governance.
- **Rollup window and cadence.** `__rollup_window__` is an ISO 8601
  window externally supplied by the scheduler so multiple cadences
  (monthly, quarterly, an ad-hoc audit-driven window) reuse the same
  playbook without workflow duplication. The framework binds no
  cadence; NIS2 Art. 21(2)(f) and DORA Art. 6 anchor the
  periodic-review obligation, but the specific interval is the
  operator's choice against their governance calendar.
- **Telemetry / workflow / control-attestation sources.** The
  evaluate-metrics step reads whatever surfaces the operator has
  bound against each catalogue entry's `measurement.formula`. The
  framework binds the seam (a read call against a source that can
  answer the formula) but not the source — SIEM query, OCSF event
  store, workflow-execution telemetry, control-attestation store,
  or an aggregating warehouse the operator prefers.
- **Scoring policy.** The score-control-effectiveness step's
  per-control weighting, KRI penalty function, missing-evidence
  treatment, and programme-level aggregation are the operator's
  policy choices. The playbook pins the input contract
  (`__metric_evaluations__` grouped by `control_refs[]`) and the
  output contract (composite score in `0.0..1.0`); the function
  itself is bound at the operator's compile target.
- **Board pack pipeline handoff.** The emit-board-summary step
  dispatches the structured artifact to the operator's board pack
  pipeline endpoint (object store, GRC platform, document store, or
  scheduled-report queue). Distribution, signing, and archival of
  the emitted summary are out of scope of the playbook and are
  discharged by the operator's existing pipeline.

## 9. Relationship to other playbooks

`executive_metrics` sits as the **rollup companion** to every
per-workflow measurement discipline in the framework and as the
**G-04 KPI/KRI catalogue's** in-tree consumer:

- **Upstream contributors.** Every per-workflow playbook that ships a
  metric emitter into the catalogue is an upstream input. The
  detection lane (`alert_triage`, `detection_engineering`,
  `threat_intel_ingest`), the posture lane (`mfa_secured_comms`,
  `crypto_posture_management`, `infra_posture_management`,
  `iam_auditor`, `onboarding_offboarding_tracker`, `patch_management`,
  `backup_recovery`, `codebase_vuln_management`), the response lane
  (`ransomware_containment`, `data_exfil`, `identity_compromise`,
  `phishing_triage`, `incident_management`, `post_incident_review`),
  the governance lane (`asset_management`,
  `contractual_obligations_tracker`, `supply_chain_security`,
  `cyber_hygiene_training`, `on_call_rotation`), and the intake lane
  (`cloud_misconfiguration`, `vuln_intake`) all contribute — each
  playbook stamps its own KPI / KRI series on the catalogue at the
  step boundaries documented in its own cookbook entry, and
  `executive_metrics` reads that catalogue on a cadence.
- **Sibling: `detection_engineering`.** Both playbooks discharge
  complementary halves of the NIS2 Art. 21(2)(f) effectiveness-
  assessment surface: `detection_engineering` at the per-rule-version
  measure-state layer (the rule-lifecycle discipline), and
  `executive_metrics` at the KPI/KRI rollup and control-effectiveness
  scoring layer (the reporting discipline). Neither subsumes the
  other; both are audit-evident.
- **Companion: the G-04 KPI/KRI catalogue.** The catalogue itself
  (`content/metrics/`) is the content-model layer this playbook
  operates against. Adding, removing, or repointing an entry in the
  catalogue immediately shows up in the next rollup without any
  playbook change — the rollup's input contract is the catalogue's
  own schema, not a hard-coded list.
- **Downstream: the operator's board pack pipeline.** The emit-
  board-summary step hands the structured artifact off; distribution,
  signing, archival, and any presentation-layer rendering (deck,
  PDF, portal page) are the pipeline's job. The framework binds the
  handoff, not the pipeline.

## 10. Replay and audit story

The byte-parity drift guards under
`tests/examples/{n8n,temporal,langgraph}/executive_metrics/` each pin
the committed worked-example artifact to a fresh emitter run from
the canonical CACAO source; if the compiler or the playbook changes,
regenerate via the per-target `regenerate.sh` and commit the diff
intentionally.

The rollup's replay property has two axes:

- **Deterministic derivation replay.** Given the same
  `__metric_evaluations__`, the score-control-effectiveness step and
  the breach-band branch produce the same output on all three
  targets. The operator can diff the composite score and the
  board-attention flag across targets as a byte-parity check.
- **End-to-end replay.** Given the same catalogue version pinned via
  `__catalog_ref__` and the same read results on the operator's
  telemetry / workflow / control-attestation surfaces over
  `__rollup_window__`, the full rollup produces the same evaluations,
  the same score, and the same emitted board-summary artifact. The
  surface reads are the non-deterministic axis — the operator's SIEM
  or event store must itself be replayable against the same window
  for the property to hold end-to-end.

## 11. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys for the
  catalogue store, the telemetry sources, or the board pack pipeline
  endpoint. Connectors are operator-bound at runtime against
  environment variables documented per target.
- **Catalogue authorship.** The playbook operates the recurring
  rollup discipline against a pinned catalogue; it does not author
  the KPI / KRI entries. Metric authorship is the operator's
  content-governance concern, discharged against
  `content-model/metrics.schema.json` on the operator's own
  contribution flow.
- **Scoring policy authorship.** The per-control weighting, KRI
  penalty function, and missing-evidence treatment the score-
  control-effectiveness step applies are the operator's policy.
  The playbook binds the input and output contracts; the policy
  itself is out of scope of the framework.
- **Board pack rendering.** The emit-board-summary step hands a
  structured artifact to the operator's board pack pipeline; the
  pipeline owns the deck / PDF / portal-page rendering, the
  signing story, and the archival cadence. Those surfaces are out
  of scope of this playbook.
- **Distribution to individual board members.** The board-attention
  flag surfaces on the artifact's cover page for the pack pipeline
  to route on; the playbook itself does not notify anyone directly.
  Notification cadence and channel are the pipeline's concern.
- **Sigma rule ids.** An executive rollup is a reporting workflow;
  no Sigma rule IDs are pinned on this overlay. Detection-side
  emitters that feed the catalogue carry their own Sigma references
  where the discipline matches.

## 12. References

- [`content/playbooks/executive_metrics/README.md`](../../content/playbooks/executive_metrics/README.md)
  — canonical CACAO source overview and status.
- [`content/playbooks/executive_metrics/mappings.yaml`](../../content/playbooks/executive_metrics/mappings.yaml)
  — outbound OSCAL / OCSF / CRA overlay with per-step control anchors
  and the documented NIS2 / DORA / D3FEND / SigmaHQ absences.
- [`content/mappings/cra/article-13-2-3-risk-assessment-metrics.yaml`](../../content/mappings/cra/article-13-2-3-risk-assessment-metrics.yaml)
  — CRA Article 13(2)–(3) inbound anchor (recurring KPI/KRI
  materialisation of the manufacturer risk-assessment obligation).
- [`content/mappings/nis2/article-21-2-f.yaml`](../../content/mappings/nis2/article-21-2-f.yaml)
  — NIS2 Article 21(2)(f) inbound anchor (effectiveness assessment
  of cybersecurity risk-management measures).
- [`content/mappings/dora/article-6.yaml`](../../content/mappings/dora/article-6.yaml)
  — DORA Article 6 inbound anchor (ICT risk-management framework,
  periodic review).
- [`content/mappings/dora/article-5.yaml`](../../content/mappings/dora/article-5.yaml)
  — DORA Article 5 inbound anchor (governance and organisation).
- [`examples/n8n/executive_metrics/README.md`](../../examples/n8n/executive_metrics/README.md)
  — n8n worked-example walkthrough and import instructions.
- [`examples/temporal/executive_metrics/README.md`](../../examples/temporal/executive_metrics/README.md)
  — Temporal worked-example walkthrough.
- [`examples/langgraph/executive_metrics/README.md`](../../examples/langgraph/executive_metrics/README.md)
  — LangGraph worked-example walkthrough.
- [`docs/cookbook/detection_engineering.md`](./detection_engineering.md)
  — sibling cookbook under NIS2 Article 21(2)(f) (per-rule-version
  measure-state discipline).
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
