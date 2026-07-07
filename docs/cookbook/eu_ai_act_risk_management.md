# eu_ai_act_risk_management — cookbook walkthrough

EU AI Act (Regulation (EU) 2024/1689) Article 9 requires providers of
high-risk AI systems to establish, implement, document and maintain
a risk-management system as a continuous iterative process planned
and run throughout the entire lifecycle of the system. The
`playbook.eu_ai_act_risk_management@v1` CACAO v2 playbook is the
portable, framework-agnostic scaffold for that discipline: it
inventories a high-risk AI system against Annex III, iterates the
Article 9(2) identify / estimate / evaluate / adopt cycle, assembles
the Article 11 read with Annex IV technical documentation bundle,
and closes the loop with the Article 72 post-market monitoring
feedback edge that feeds the Article 9(2)(c) evaluation of
post-market signals in the next iteration.

The playbook is the **product-lifecycle risk-management anchor** for
the AI-system stream: it sits alongside the operator-side
risk-management lane (`dora_ict_risk_selfassess`,
`nis2_self_assessment`) rather than replacing it — those two lanes
govern the operator's ICT / cybersecurity self-assessment surface,
while this playbook governs the *provider*-side product-lifecycle
obligation Article 9 places on high-risk AI systems specifically.
Downstream evidence flows into two lanes:

```
eu_ai_act_risk_management ─► detection_engineering
                          └► post_incident_review     (on residual-risk breach)
```

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the
Annex III use-case inventory, the Article 9(2) assessment loop, the
Article 11 + Annex IV documentation bundle, and the Article 72
post-market monitoring feedback edge land in each target.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/eu_ai_act_risk_management/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA overlay
└── playbook.cacao.json          # canonical CACAO v2 source (playbook.eu_ai_act_risk_management@v1)

content/metrics/residual_risk_threshold_breach_count.yaml
content/metrics/residual_risk_threshold_breach_count.viz.md
                                  # KRI — count of residual-risk
                                  # observations that cross the
                                  # operator-scoped Art. 9(5)
                                  # acceptability threshold in the
                                  # window, keyed to the Art. 9(2)
                                  # assessment step and the Art. 72
                                  # monitoring step
content/metrics/transparency_doc_freshness_age.yaml
content/metrics/transparency_doc_freshness_age.viz.md
                                  # KRI — age in days of the freshest
                                  # committed Art. 11 + Annex IV /
                                  # Art. 13 documentation bundle per
                                  # high-risk AI system in scope
```

The CACAO source is canonical. The four action steps and one `start`
/ one `end` wiring node are the deterministic policy the playbook
*means* — an identify step feeding an Article 9(2) assessment loop,
feeding an Article 11 + Annex IV documentation-assembly step, feeding
an Article 72 post-market monitoring step whose signals loop back
into the Article 9(2)(c) evaluation on the next iteration. The three
worked examples under
`examples/{n8n,temporal,langgraph}/eu_ai_act_risk_management/` are
the same playbook compiled into three orchestrator idioms.
Everything else — the AI-system inventory the identify step reads,
the risk-register store the assessment step writes into, the
technical-documentation bundle store the assembly step commits into,
and the post-market-monitoring signal source the monitoring step
reads — is the operator's data plane.

## 2. CACAO topology and lifecycle binding

The playbook ships six steps: one `start`, four `action`, one `end`.
The workflow is linear on the ingest arm — no branching gate — and
the Article 9 iterative property is expressed by the feedback edge
from the post-market monitoring step's output signal into the next
Article 9(2)(c) evaluation on the following iteration, rather than
as an in-workflow loop node. This keeps the CACAO topology auditable
per iteration; the multi-iteration discipline is the operator's
scheduling of the workflow, not an in-artifact loop.

| Step suffix | Step                              | Discipline                                                                                                                                                                                                                        | Status         |
|-------------|-----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | eu-ai-act-rm-start                | edge wiring only — no body                                                                                                                                                                                                        | n/a            |
| `…000002`   | identify high-risk AI system      | inventory the AI system, resolve whether it is a high-risk AI system under Art. 6 read with Annex III (or against a Union-harmonisation-legislation entry per Art. 6(1) and Annex I), pin the Annex III use-case category         | operator-bound |
| `…000003`   | assess risk under Art. 9(2)       | iterate the Art. 9(2)(a)–(d) identify / estimate / evaluate / adopt cycle for the pinned use case; emit a Compliance Finding per scored residual-risk observation for the Art. 9(5) acceptability judgement                        | operator-bound |
| `…000004`   | assemble technical documentation  | draw up the Art. 11 read with Annex IV technical documentation before the system is placed on the market and keep it up to date; commit the Art. 13 instructions-for-use bundle in the same assembly step                          | operator-bound |
| `…000005`   | monitor post-market signals       | operate the Art. 72 post-market monitoring plan; emit a Detection Finding when a signal represents an anomaly that pushes a residual-risk observation across the Art. 9(5) acceptability threshold                                 | operator-bound |
| `…000006`   | eu-ai-act-rm-end                  | edge wiring only — no body                                                                                                                                                                                                        | n/a            |

All four action steps carry the CACAO I/O contract (`in_args` /
`out_args`) plus `x_secops_ng` reference bundles (control, telemetry,
metric). One execution runs the linear four-step chain exactly once
per scheduled iteration of the risk-management system; a persistent
non-zero value on
`kri.residual_risk_threshold_breach_count@v1` across successive
iterations is the operator-side signal that the Article 9(2)(d)
targeted-measures set is not converging on the Article 9(5)
acceptability line.

> The playbook maturity is `experimental` on the workflow-local
> content marker. The overlay pins the control, defensive-technique,
> telemetry, and metric surface; the three reference emitters ship
> committed workflow artefacts today, with deterministic emitter
> output and byte-parity goldens under
> `tests/examples/eu_ai_act_risk_management/`.

## 3. Lifecycle contract — the four action states

The per-iteration payload — AI-system identifier, Annex III use-case
category, risk register identifier, technical documentation bundle
identifier, and post-market signal identifier — is
product-lifecycle-governance content whose personal-data surface is
thin: the payload does not carry personal data of the AI system's
subjects. The AI system may *itself* process personal data (Annex III
categories 1, 3, 4, 6, and 8 all admit systems that do), in which
case GDPR Article 35 DPIA obligations interact with the Article 9
risk-management cycle; that interaction is picked up on the sibling
G-02 card that opens the `eu_ai_act ↔ gdpr` edge, and does not
change this playbook's own personal-data surface.

**identify high-risk AI system** (`…000002`)
:   Inventory step. Reads the operator's AI-system inventory,
    resolves whether the system is a high-risk AI system under
    Article 6 read with Annex III (or against a Union harmonisation-
    legislation entry per Article 6(1) and Annex I), determines the
    provider / deployer role under Article 3(3) and (4), and pins
    the Annex III use-case category the risk-management system will
    be operated against. If the system is not a high-risk AI system,
    the Article 6(3) derogation self-declaration is the artefact
    committed here. Anchored on OSCAL PM-9 (Risk Management
    Strategy) — the establishment surface for the risk-management
    system as a whole. The playbook does not pin a D3FEND technique
    on this step: the Annex III inventory-classification slice is a
    deterministic content-model overlay lookup, not a defensive-
    technique discharge against the operator's deployed estate.

**assess risk under Art. 9(2)** (`…000003`)
:   Assessment step. Iterates the Article 9(2) cycle for the pinned
    use case: identification and analysis of known and reasonably
    foreseeable risks under 9(2)(a); estimation and evaluation of
    risks that may emerge under intended purpose and under
    conditions of reasonably foreseeable misuse under 9(2)(b);
    evaluation of other risks possibly arising, based on the
    analysis of data gathered from the post-market monitoring
    system, under 9(2)(c); adoption of appropriate and targeted
    risk-management measures under 9(2)(d), giving effect to the
    requirements of Chapter III Section 2. Anchored on OSCAL RA-3
    (Risk Assessment) and PM-9 (Risk Management Strategy) and on
    MITRE D3FEND v1.0.0 `D3-OAM` (Operational Activity Mapping) —
    the identify / estimate / evaluate cycle maps operator
    activities and evidence onto the operator's documented risk-
    management model. Emits an OCSF Compliance Finding
    (class_uid 2003) per scored residual-risk observation carrying
    the scored value, the pinned Annex III use-case category, and
    the reference to the risk register entry the observation
    belongs to. Feeds
    `kri.residual_risk_threshold_breach_count@v1` — the count of
    residual-risk observations above the operator-scoped Article 9(5)
    acceptability threshold in the window.

**assemble technical documentation** (`…000004`)
:   Documentation-assembly step. Draws up and keeps up to date the
    technical documentation the provider must have in place before
    the high-risk AI system is placed on the market or put into
    service under Article 11 read with Annex IV: general description
    of the AI system, detailed description of its elements and of
    the process for its development, information about the
    monitoring, functioning and control of the system, description
    of the appropriateness of the performance metrics, detailed
    description of the risk-management system per Article 9, and a
    list of the harmonised standards applied. The Article 13
    instructions-for-use bundle for deployers is committed alongside
    on the same step (Article 11 and Article 13 share the
    documentation surface). Anchored on OSCAL PL-2 (System Security
    and Privacy Plans) — the closest 800-53 anchor for the document-
    authoring-and-maintenance discipline. The playbook does not pin
    a D3FEND technique on this step: the Article 11 + Annex IV
    documentation-assembly slice is a document-authoring-and-
    maintenance discipline that D3FEND's runtime-countermeasure
    taxonomy does not cover cleanly. Emits an OCSF Compliance
    Finding (class_uid 2003) per committed bundle carrying the
    bundle identifier and the assembly time; the assembly-time
    stream feeds `kri.transparency_doc_freshness_age@v1` — the age
    in days of the latest committed bundle per high-risk AI system
    in scope.

**monitor post-market signals** (`…000005`)
:   Post-market monitoring step. Operates the post-market monitoring
    feedback loop the iterative Article 9(2)(c) cycle depends on:
    the provider establishes and documents a post-market monitoring
    system under Article 72, actively and systematically collects,
    documents and analyses relevant data on the performance of the
    high-risk AI system throughout its lifetime, and feeds the
    resulting signals back into the Article 9 iteration so residual-
    risk acceptability under Article 9(5) stays defended. Anchored
    on OSCAL RA-3 (Risk Assessment) — the recurring-risk-assessment
    surface the post-market loop re-triggers. Emits an OCSF
    Detection Finding (class_uid 2004) when a signal represents an
    anomaly that pushes a residual-risk observation across the
    operator-scoped Article 9(5) acceptability threshold; the
    Detection Finding is the machine-readable trigger for the next
    Article 9(2)(c) evaluation to re-score the affected risk
    register entries, and a second input into
    `kri.residual_risk_threshold_breach_count@v1` alongside the
    Compliance Finding observation stream from the assessment step.
    The re-assessment discipline itself is covered by the `D3-OAM`
    pin on the assess step; pinning the monitoring loop separately
    would double-count the technique.

## 4. Regulatory anchors

**EU AI Act — Regulation (EU) 2024/1689.** The playbook is the
per-iteration execution surface for Article 9 read with Article 11,
Article 13, and Article 72:

- **Art. 9(1)** — establishment, implementation, documentation, and
  maintenance of a risk-management system for a high-risk AI
  system. Anchored end-to-end on this playbook.
- **Art. 9(2)** — iterative identify / estimate / evaluate / adopt
  cycle. Anchored on the *assess risk under Art. 9(2)* step;
  Art. 9(2)(c) closes with the *monitor post-market signals* step.
- **Art. 9(5)** — residual-risk acceptability. Measured on
  `kri.residual_risk_threshold_breach_count@v1`; the KRI counts
  residual-risk observations above the operator-scoped
  acceptability threshold and is the operator-side signal that the
  Article 9(2)(d) targeted-measures set is not converging.
- **Art. 11 read with Annex IV** — technical documentation. Anchored
  on the *assemble technical documentation* step; measured on
  `kri.transparency_doc_freshness_age@v1`.
- **Art. 13** — transparency and provision of information to
  deployers (instructions for use). The instructions-for-use bundle
  is committed on the same assembly step and feeds the same
  freshness KRI. A dedicated deployer-facing playbook may be
  authored later under G-01; this playbook remains the provider-
  side execution surface.
- **Art. 43** — conformity assessment. The Article 11 + Annex IV
  bundle assembled here is the input the Article 43 conformity-
  assessment intake reads; the intake handoff itself is downstream
  of this playbook and out of scope.
- **Art. 72** — post-market monitoring by providers. The
  Article 9(2)(c) loop-back edge reads its signals from the
  Article 72 plan operated on the *monitor post-market signals*
  step.

**NIS2 Directive (EU) 2022/2555.** Article 21(2)(a) — policies on
risk analysis and information-system security. The Article 9(2)
risk-analysis step of this playbook is the AI-system-specific
execution surface for the risk-analysis policy obligation NIS2
imposes on essential and important entities. Inbound YAML edge at
`content/mappings/nis2/article-21-2-a.yaml` is deferred to the
sibling G-02 card; the placeholder is retained in this playbook's
`mappings.yaml` so the graph closure is programmatically
discoverable.

**Adjacent regimes (feasibility notes).** GDPR Article 35 DPIA
interacts with the Article 9 risk-management cycle when the
high-risk AI system processes personal data; Recital 9 of
Regulation (EU) 2024/1689 preserves GDPR obligations. DORA Article 6
ICT risk-management applies to financial entities and is anchored
on the operator-side incident-management / `dora_ict_risk_selfassess`
lane, not on the product-lifecycle surface Article 9 governs. CRA
Annex I product-security obligations for products with digital
elements are adjacent to Article 9 for AI systems that are
themselves CRA-covered products. The sibling G-02 card reviews all
three edges; the current reading is that they are adjacent-but-
distinct and any inbound edge lands on that card, not this one.

**OSCAL controls** exercised by the workflow (from
[`content/playbooks/eu_ai_act_risk_management/mappings.yaml`](../../content/playbooks/eu_ai_act_risk_management/mappings.yaml)):
PM-9 (Risk Management Strategy — anchors the establishment surface
for the risk-management system as a whole), RA-3 (Risk Assessment —
anchors the assessment and post-market monitoring steps' recurring-
risk-assessment surface), and PL-2 (System Security and Privacy
Plans — anchors the documentation-assembly step).

**MITRE D3FEND v1.0.0** — `D3-OAM` (Operational Activity Mapping) at
`assess risk under Art. 9(2)`. The identify, documentation-assembly,
and post-market-monitoring steps are lifecycle-governance surfaces
that D3FEND's runtime-countermeasure taxonomy does not cover
cleanly, and are deliberately not pinned; see the D3FEND omissions
block in `mappings.yaml` for the rationale.

**OCSF v1.3.0 telemetry classes** consumed and emitted (from
[`content/playbooks/eu_ai_act_risk_management/mappings.yaml`](../../content/playbooks/eu_ai_act_risk_management/mappings.yaml)):
Compliance Finding (class_uid 2003) emitted on the assessment and
documentation-assembly steps; Detection Finding (class_uid 2004)
emitted on the post-market-monitoring step when a signal crosses
the operator-scoped Article 9(5) acceptability threshold.

## 5. Per-target hand-off

The three reference targets share the CACAO source. Each target
compiles the same four action steps into its native idiom.

- **n8n** (`examples/n8n/eu_ai_act_risk_management/workflow.n8n.json`).
  Import the JSON directly into an n8n instance. The four action
  steps land as placeholder `Set` nodes that an operator binds to
  their AI-system inventory connector, risk-register store,
  technical-documentation bundle store, and post-market monitoring
  signal source respectively.
- **Temporal** (`examples/temporal/eu_ai_act_risk_management/workflow.temporal.py`).
  The compiler emits a deterministic Python workflow whose activity
  bodies raise `NotImplementedError` until the operator wires the
  activity implementations against their own AI-system inventory
  and evidence stores. Determinism guarantees at the workflow layer
  survive the placeholder activity bodies.
- **LangGraph** (`examples/langgraph/eu_ai_act_risk_management/`).
  The compiler emits a graph specification, a state binding module,
  and an audit-mirror scaffold. Tool bodies raise
  `NotImplementedError` until the operator wires them; the state
  machine is exercisable end-to-end from the start node so the
  graph shape can be inspected without operator bindings.

Each target directory ships a `regenerate.sh` that re-emits the
worked-example artifact from the canonical CACAO source via the
unified `tools.compile` CLI. Regenerate after any change to the
playbook or the corresponding compiler.

## 6. Observability — OTel + AuditTrail in every target

The three reference targets share the same observability contract:
each action step transition is recorded on the shared `AuditTrail`
envelope alongside the framework's OpenTelemetry span emissions, so
the four-layer content model (playbook, control, telemetry,
metric) is auditable across a full Article 9 iteration without
target-specific instrumentation. The OCSF Compliance Finding and
Detection Finding class shapes wired on the mappings overlay are the
externally-consumable audit trail per iteration; the internal
`AuditTrail` records are the replay substrate documented at
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md).

## 7. Metrics — what the risk-management iteration exposes

The Article 9 iteration exposes two KRIs on the catalogue:

- **`kri.residual_risk_threshold_breach_count@v1`** — count of
  residual-risk observations above the operator-scoped Article 9(5)
  acceptability threshold within the evaluation window. Two inputs:
  the OCSF Compliance Finding stream from the assessment step
  (scored residual-risk observations) and the OCSF Detection Finding
  stream from the post-market monitoring step (anomaly triggers that
  push observations across the threshold). A persistent non-zero
  value across successive iterations is the operator-side flag that
  the Article 9(2)(d) targeted-measures set is not converging. See
  [`content/metrics/residual_risk_threshold_breach_count.viz.md`](../../content/metrics/residual_risk_threshold_breach_count.viz.md)
  for the reference visualisation.
- **`kri.transparency_doc_freshness_age@v1`** — age in days of the
  freshest committed Article 11 + Annex IV / Article 13
  documentation bundle per high-risk AI system in scope, rolled up
  as the maximum across systems. A value drifting upward across
  evaluation windows is the operator-side flag that the
  documentation-assembly cadence is falling behind the risk-
  management-system iteration cadence, and the Article 43
  conformity-assessment intake is running against stale material.
  See [`content/metrics/transparency_doc_freshness_age.viz.md`](../../content/metrics/transparency_doc_freshness_age.viz.md)
  for the reference visualisation.

SecOps-NG does not set the Article 9(5) acceptability threshold or
the documentation-freshness policy — those are the provider's
judgement under Article 9(3) state of the art and the operator's
own documentation-refresh policy respectively. The catalogue entries
name the shape and the source; operators wire scoped overrides for
each pinned Annex III use-case category.

Adjacent catalogue entries that operators typically render alongside
these two KRIs include `kpi.control_effectiveness@v1` (whole-
programme rollup) and `kpi.eu_regulatory_reference_coverage@v1`
(catalogue-coverage sanity check).

## 8. Operator customisation points

The playbook binds the topology, not the vendor. The operator owns
every seam:

- **AI-system inventory source.** Whether the `identify high-risk AI
  system` step reads from a CMDB, an internal registry, or a
  spreadsheet — that binding is operator-owned. The framework
  requires only that the resolved system identifier and the pinned
  Annex III use-case category flow onto the next step.
- **Risk register store.** The Article 9(2) assessment step commits
  scored residual-risk observations to a store the operator picks:
  a dedicated GRC platform, an internal issue tracker, or a
  spreadsheet under change control. The store is operator-bound; the
  Compliance Finding class shape is the audit trail contract.
- **Technical documentation bundle store.** The Article 11 + Annex IV
  bundle is committed to a store the operator picks — typically a
  documentation repository under version control alongside the
  system's source. The catalogue does not prescribe the store; the
  Compliance Finding on assembly is the audit trail contract.
- **Article 72 monitoring signal source.** The `monitor post-market
  signals` step reads from the operator's post-market monitoring
  plan implementation — a telemetry pipeline, a user-feedback
  intake, an incident log, or (typically) a composite of all three.
  The framework binds the class shape on the anomaly-trigger
  Detection Finding; the pipeline itself is operator-owned.
- **Acceptability threshold and freshness policy.** The Article 9(5)
  acceptability threshold and the documentation-freshness policy
  are the operator's under Article 9(3) state of the art. The
  catalogue does not prescribe numeric values; operators wire scoped
  overrides for each pinned Annex III use-case category.

## 9. Replay and audit story

The byte-parity drift guards live at
`tests/examples/eu_ai_act_risk_management/`. Each per-target golden
pins the committed worked-example artifact to a fresh emitter run
from the canonical CACAO source; if the compiler or the playbook
changes, regenerate via the per-target `regenerate.sh` and commit
the diff intentionally.

The cross-target replay property is the harder one: the same
AI-system input, fed through n8n / Temporal / LangGraph, produces
byte-identical risk-register commits, byte-identical technical
documentation bundle identifiers, and byte-identical post-market
signal receipts once each target's activity / tool bodies are wired
against the same operator seams and the same OSCAL / OCSF / D3FEND
reference bundles. The `(ai_system_id, annex_iii_use_case,
risk_register_id, technical_documentation_id, post_market_signal)`
key is the string an operator can diff to confirm the property
holds across targets.

## 10. Playbook chain — where eu_ai_act_risk_management sits

The provider-side product-lifecycle chain expresses itself as one
iteration workflow whose output is the audit trail of the
Article 9 discipline and whose signals feed the detection lane and
the incident-review lane:

```
eu_ai_act_risk_management ─► detection_engineering
                          └► post_incident_review     (on residual-risk breach)
```

- **Downstream: `detection_engineering`.** The Detection Finding
  class emitted by the post-market monitoring step arms the wider
  Sigma rule lifecycle on
  `playbook.detection_engineering@v1` when the operator wants a
  detection surface across the post-market signal set. See
  [`docs/cookbook/detection_engineering.md`](./detection_engineering.md).
- **Downstream (on breach): `post_incident_review`.** A residual-
  risk-threshold breach observation is not an incident, but a
  breach that persists across iterations typically feeds the
  post-incident-review lane so the operator-side lessons-learned
  discipline picks up the trend. See
  [`docs/cookbook/post_incident_review.md`](./post_incident_review.md).
- **Adjacent: `dora_ict_risk_selfassess` and
  `nis2_self_assessment`.** These two playbooks govern the
  operator-side ICT / cybersecurity self-assessment surface, and
  are anchored on the same RA-3 / PM-9 OSCAL surface this playbook
  exercises. Operators subject to both AI Act Article 9 and NIS2
  Article 21(2)(a) or DORA Article 6 typically run all three on
  overlapping cadences; the D3FEND `D3-OAM` anchor is the shared
  technique across all three lanes.
- **Adjacent: `data_protection_impact_assessment`.** When the
  high-risk AI system processes personal data (Annex III categories
  that admit personal data), the GDPR Article 35 DPIA obligation
  interacts with the Article 9 cycle. The DPIA playbook is the
  operator's execution surface for that interaction; the AI Act
  side stays on this playbook. Recital 9 of Regulation (EU) 2024/1689
  preserves GDPR obligations.

The chain lets this playbook stay narrowly focused on the
Article 9 discipline while the wider detection lifecycle,
incident-review lane, and adjacent regulatory lanes run on their
own workflows. The chain is not code-coupled — each playbook is a
standalone CACAO artifact that can be run in isolation — but the
audit trail's coherence across the workflows is the sovereign-
security property the framework guarantees.

## 11. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys for the
  AI-system inventory, the risk register store, the technical-
  documentation bundle store, or the post-market monitoring signal
  source. Connectors are operator-bound at runtime against
  environment variables documented per target.
- **Article 43 conformity assessment.** The playbook produces the
  Article 11 + Annex IV bundle the conformity assessment intake
  reads; the intake procedure itself, the notified-body interaction,
  and the CE-marking step are downstream and out of scope.
- **Adjacent AI-Act obligations.** Article 10 (data governance),
  Article 12 (record-keeping), Article 14 (human oversight),
  Article 15 (accuracy / robustness / cybersecurity), and
  Article 72 (post-market monitoring as its own playbook) each
  warrant their own playbook under G-01. This scaffold is the
  Article 9 execution surface and touches Articles 11, 13, and 72
  only where the risk-management cycle depends on their outputs.
- **Inbound regulator-side YAML edges.** The
  `content/mappings/eu_ai_act/` inbound directory does not yet
  exist; the sibling G-02 card lands the per-article inbound YAMLs
  and pins `playbook.eu_ai_act_risk_management@v1` in each entry's
  `playbook_refs` list.
- **Acceptability threshold selection.** The Article 9(5)
  acceptability threshold is the provider's judgement under
  Article 9(3) state of the art. The catalogue names the KRI shape;
  the numeric threshold and the per-use-case policy are the
  operator's.

## 12. References

- [`content/playbooks/eu_ai_act_risk_management/README.md`](../../content/playbooks/eu_ai_act_risk_management/README.md)
  — canonical CACAO source overview and status.
- [`content/playbooks/eu_ai_act_risk_management/mappings.yaml`](../../content/playbooks/eu_ai_act_risk_management/mappings.yaml)
  — outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA overlay with
  per-step control anchors.
- [`content/metrics/residual_risk_threshold_breach_count.yaml`](../../content/metrics/residual_risk_threshold_breach_count.yaml)
  — KRI catalogue entry for residual-risk observations above the
  Article 9(5) acceptability threshold.
- [`content/metrics/transparency_doc_freshness_age.yaml`](../../content/metrics/transparency_doc_freshness_age.yaml)
  — KRI catalogue entry for the Article 11 + Annex IV / Article 13
  documentation bundle freshness age.
- [`examples/n8n/eu_ai_act_risk_management/README.md`](../../examples/n8n/eu_ai_act_risk_management/README.md)
  — n8n worked-example walkthrough and import instructions.
- [`examples/temporal/eu_ai_act_risk_management/README.md`](../../examples/temporal/eu_ai_act_risk_management/README.md)
  — Temporal worked-example stub.
- [`examples/langgraph/eu_ai_act_risk_management/README.md`](../../examples/langgraph/eu_ai_act_risk_management/README.md)
  — LangGraph worked-example stub.
- [`docs/cookbook/detection_engineering.md`](./detection_engineering.md)
  — downstream cookbook (detection rule lifecycle).
- [`docs/cookbook/post_incident_review.md`](./post_incident_review.md)
  — downstream cookbook (lessons-learned lane, on persistent
  residual-risk breach).
- [`docs/cookbook/dora_ict_risk_selfassess.md`](./dora_ict_risk_selfassess.md)
  — adjacent cookbook (operator-side DORA Article 6 ICT
  risk-management self-assessment).
- [`docs/cookbook/nis2_self_assessment.md`](./nis2_self_assessment.md)
  — adjacent cookbook (operator-side NIS2 Article 21(2)
  self-assessment).
- [`docs/cookbook/data_protection_impact_assessment.md`](./data_protection_impact_assessment.md)
  — adjacent cookbook (GDPR Article 35 DPIA, when the high-risk AI
  system processes personal data).
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
