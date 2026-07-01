# detection_engineering — cookbook walkthrough

Detection-rule lifecycle under NIS2 Article 21(2)(f). The
`playbook.detection_engineering@v1` CACAO playbook operates each rule
version through a durable four-state machine: **propose** (intake the
candidate rule version and its rationale into the operator's detection
store), **review** (peer-review against the operator's review
checklist and record the verdict), **ship** (promote the approved
rule version to production status in the operator's detection store),
and **measure** (emit a per-rule-version effectiveness-metric snapshot
that the F-CP-06 effectiveness evidence stream consumes). Each
shipped rule version carries a paired effectiveness snapshot pinned
to the exact `(__rule_id__, __rule_version__)` the lifecycle is
operating on — the audit-evident artifact that discharges the NIS2
Article 21(2)(f) effectiveness-assessment obligation across the
detection-rule population.

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the deterministic
lifecycle bindings, the per-rule-version effectiveness-snapshot
adapter, and the OpenTelemetry / `AuditTrail` mirror live in each.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/detection_engineering/
├── README.md                    # workflow-local overview and pending work
├── mappings.yaml                # outbound playbook-mappings overlay
└── playbook.cacao.yaml          # canonical CACAO v2 source (playbook.detection_engineering@v1)

schemas/evidence/rule-effectiveness-snapshot.schema.json
                                  # per-rule-version effectiveness-snapshot artifact schema
                                  # (definition, unit, calc_method, OCSF source_data shape, ref_viz)

schemas/evidence/effectiveness.schema.json
                                  # F-CP-06 effectiveness evidence stream — consumes the
                                  # per-rule snapshot into its `measurement` block

content/mappings/nis2/article-21-2-f.yaml
                                  # NIS2 Art. 21(2)(f) inbound anchor — backlinks
                                  # playbook.detection_engineering@v1 on `playbook_refs`

content/mappings/cra/annex-i-1-l-logging-monitoring-detection-engineering.yaml
                                  # CRA Annex I §1(l) rule-content-side inbound anchor
```

The CACAO source is canonical. The four lifecycle states are the
deterministic policy the playbook *means*. The three worked examples
under `examples/{n8n,temporal,langgraph}/detection_engineering/` are
the same playbook compiled into three orchestrator idioms. Everything
else — runtime, detection-store proposal intake, peer-review system,
production-status promotion endpoint, effectiveness-snapshot metric
sink — is the operator's data plane.

## 2. CACAO topology and lifecycle binding

The playbook ships six steps: one `start`, four `action`, one `end`.
Transitions in the shipped artifact are unconditional — each state
declares exactly one `on_completion` successor. Gating predicates on
`review → ship` (verdict = approved) and `ship → measure`
(`__ship_status__` = production) are follow-up sibling work; the
review-verdict variable and the shipped-status flag already flow on
the wire so the switch inserts without touching the surrounding
states.

| Step suffix | Step                       | Discipline                                                                          | Status         |
|-------------|----------------------------|--------------------------------------------------------------------------------------|----------------|
| `…000001`   | start                      | edge wiring only — no body                                                          | n/a            |
| `…000002`   | propose-rule-version       | proposal-envelope write against the operator's detection store (rule_id, version, rationale) | operator-bound |
| `…000003`   | review-rule-version        | verdict-record write against the operator's peer-review system (`__review_verdict__ ∈ {approved, changes_requested, rejected}`) | operator-bound |
| `…000004`   | ship-rule-version          | production-status transition write against the detection store (`__ship_status__ ∈ {production, staged, withdrawn}`) | operator-bound |
| `…000005`   | measure-rule-version       | per-rule-version effectiveness-metric snapshot shaped per `schemas/evidence/rule-effectiveness-snapshot.schema.json` | bound (n8n)    |
| `…000006`   | end                        | edge wiring only — no body                                                          | n/a            |

The four action bodies carry the CACAO I/O contract (`in_args` /
`out_args`) plus `x_secops_ng` reference bundles (control, telemetry,
metric). One per-rule-version lifecycle execution emits exactly one
effectiveness snapshot at `measure`; the snapshot is what the F-CP-06
effectiveness stream consumes into the operator's metric sink for
archival and trend analysis.

> Per-target byte-parity goldens covering all four lifecycle states
> under `tests/examples/detection_engineering/` and the Temporal /
> LangGraph reference emitters land in follow-up sibling cards; the
> n8n reference emitter is wired today.

## 3. Lifecycle contract — the four states

The lifecycle payload — rule identifier, version label, proposal
rationale, review verdict, shipped-status flag, per-rule-version
effectiveness snapshot — is detection *content*, not personal data
of a natural person. The inbound GDPR data-flow record at
[`content/mappings/gdpr/data-flow-detection_engineering.md`](../../content/mappings/gdpr/data-flow-detection_engineering.md)
declares this workflow **out of scope** for GDPR processing; the
framework treats `__rule_id__`, `__rule_version__`, and
`__proposal_rationale__` as role-shaped opaque strings.

**propose-rule-version** (`…000002`)
:   Intake step. The proposer submits a candidate rule version — a
    Sigma rule, a KQL query, an EQL rule, or the operator's chosen
    detection-content format — alongside a free-text rationale
    (typically citing the threat the rule addresses, the gap the
    rule closes, or the false-positive it removes). Sigma or any
    other detection-content format is the *payload* the lifecycle
    moves, not an external reference the lifecycle pins against:
    per-rule Sigma identifiers attach to the `__rule_id__` binding
    the operator's detection store assigns. Anchored on OSCAL SI-2
    (Flaw Remediation) and CM-3 (Configuration Change Control).

**review-rule-version** (`…000003`)
:   Peer-review step. A reviewer assesses the proposed rule version
    against the operator's documented review checklist — the operator
    authors the checklist; the framework does not. Typical items:
    false-positive risk against baseline telemetry, ATT&CK-technique
    coverage claim, query-cost ceiling against the operator's SIEM
    budget, on-call alert-volume impact, rollback readiness. The
    recorded outcome is `__review_verdict__ ∈ {approved,
    changes_requested, rejected}`. Anchored on OSCAL CA-2 (Control
    Assessments) and CM-3 (Configuration Change Control) as the
    explicit-approval discipline.

**ship-rule-version** (`…000004`)
:   Promotion step. The approved rule version is promoted to
    production status in the operator's detection store. The recorded
    outcome is `__ship_status__ ∈ {production, staged, withdrawn}` —
    `withdrawn` carries the same audit-evidence weight as
    `production` because it explicitly removes a flawed detection
    from the operator's runtime surface. Anchored on OSCAL SI-2
    (Flaw Remediation) and CM-3.

**measure-rule-version** (`…000005`)
:   Effectiveness-snapshot emission. The step emits a per-rule-version
    effectiveness-metric snapshot shaped per
    [`schemas/evidence/rule-effectiveness-snapshot.schema.json`](../../schemas/evidence/rule-effectiveness-snapshot.schema.json).
    The snapshot pins the indicator value — detection coverage,
    false-positive rate, control-effectiveness signal — to the
    exact `(__rule_id__, __rule_version__)` the lifecycle is
    operating on, and the F-CP-06 effectiveness evidence stream
    consumes those snapshots into the operator's metric sink.
    Anchored on OSCAL CA-7 (Continuous Monitoring) end-to-end;
    MITRE D3FEND v1.0.0 `D3-DA` (Detection Analytics) is the
    matching defensive-technique tag — the per-rule effectiveness
    assessment is the meta-analytic that audits whether the
    operator's analytic surface is itself fit for purpose.

The three upstream states are operator-bound runtime seams: the
framework ships neither the proposal-intake mailbox, the peer-review
system, nor the production-status promotion endpoint. The `measure`
state is bound on the n8n reference emitter today (the effectiveness-
snapshot adapter at `compilers/n8n/evidence/rule_effectiveness_node.py`
writes the artifact per the schema); Temporal and LangGraph reference
emitters land with the CORE-TEMPORAL / CORE-LANGGRAPH sibling cards.

> **LM determinism.** Proposal intake, verdict recording, status
> promotion, and effectiveness-snapshot emission are structured
> writes and reads against operator-owned surfaces, not free-text
> reasoning steps. The playbook binds no DSPy signature — there is
> no LM-driven step at this layer. See
> [`docs/FOUNDATION.md`](../FOUNDATION.md) § LLM determinism. If an
> operator wires an LM-driven proposal-triage node on top of the
> `propose` state (a private, forward-looking extension), the
> framework-wide EU-resident LM endpoint guard re-applies the check
> at process startup — see
> [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 4. Regulatory anchors

**NIS2 Article 21(2)(f)** — policies and procedures to assess the
effectiveness of cybersecurity risk-management measures, with results
archived. The measure-rule-version step is the per-rule-version
materialisation of that effectiveness assessment: each shipped rule
version carries a paired effectiveness snapshot that pins the
indicator value to the exact `(rule_id, rule_version)` the lifecycle
is operating on. Inbound anchor at
[`content/mappings/nis2/article-21-2-f.yaml`](../../content/mappings/nis2/article-21-2-f.yaml)
(`nis2:art-21-2-f`) backlinks `playbook.detection_engineering@v1` on
`playbook_refs` and lifts the playbook-side metrics
(`kpi.control_effectiveness_coverage@v1`, `kri.control_effectiveness@v1`,
`kri.overdue_effectiveness_tests@v1`) onto its `metric_refs`.

**DORA Article 10 (Chapter II — Detection)** — mechanisms to promptly
detect anomalous activities with multiple layers of control and
*defined alert thresholds and criteria*. The propose → review → ship
→ measure rule lifecycle is the audit-evident discipline that keeps
those thresholds and criteria fit for purpose. Inbound anchor at
[`content/mappings/dora/article-10.yaml`](../../content/mappings/dora/article-10.yaml)
(`dora:art-10-detection`) backlinks this playbook on `playbook_refs`
and lifts `kpi.false_positive_rate@v1` and
`kri.control_effectiveness@v1` alongside the pre-existing
`kpi.detection_coverage@v1` and `kpi.mttd@v1`.

**CRA Annex I §1(l)** — products with digital elements must provide
security-related information by recording and monitoring relevant
internal activity. Inbound anchor at
[`content/mappings/cra/annex-i-1-l-logging-monitoring-detection-engineering.yaml`](../../content/mappings/cra/annex-i-1-l-logging-monitoring-detection-engineering.yaml)
(`cra:annex-i-1-l-logging-monitoring-detection-engineering`) — the
rule-content side of §1(l): each shipped rule version carries a
paired effectiveness snapshot the F-CP-06 stream consumes,
materialising "is the monitoring capability working" on the
rule-content side. The runtime-recording catch-all
(`cra:annex-i-1-logging-monitoring`) and the operational-triage half
(`cra:annex-i-1-l-logging-monitoring-alert-triage`) are anchored
separately.

**OSCAL controls** exercised by the lifecycle (from
[`content/playbooks/detection_engineering/mappings.yaml`](../../content/playbooks/detection_engineering/mappings.yaml)):
CA-7 (Continuous Monitoring — anchors `measure` end-to-end), CA-2
(Control Assessments — anchors `review`), SI-2 (Flaw Remediation —
anchors `propose` and `ship`), CM-3 (Configuration Change Control —
anchors the propose → review → ship transition as a whole).

**MITRE D3FEND v1.0.0** — `D3-DA` (Detection Analytics) at
`measure-rule-version`. The `propose`, `review`, and `ship` steps
are deliberately not pinned to a D3FEND technique because D3FEND
v1.0.0 frames its defensive techniques around runtime countermeasures
against adversary behaviours; content-engineering upstream of runtime
countermeasures is anchored on the OSCAL controls above instead. The
in-line gap note in `mappings.yaml` documents the deliberate absence,
mirroring the `iam_auditor` / `on_call_rotation` precedent.

**OCSF v1.3.0** — the propose, review, and ship steps consume and
emit `API Activity` (class_uid 6003, category 6 Application Activity)
records against the operator's detection store and review-system
endpoints. The measure step emits a `Detection Finding` (class_uid
2004, category 2 Findings) *meta-finding* — not a per-event
detection finding fired in production (those are emitted by the
shipped rules themselves at runtime), but the meta-finding that
describes the rule version itself as a detection asset, anchored
against the per-rule-version effectiveness snapshot. The snapshot's
`source_data` field references the OCSF class identifier for the
*shape* of the data the rule queries against in production, so the
Detection Finding emission carries both the meta-finding payload and
the structural pointer the F-CP-06 stream needs to trend the
indicator across rule versions.

## 5. Per-target hand-off

### 5.1 n8n — operator-edited Set rows + effectiveness-snapshot adapter

`examples/n8n/detection_engineering/workflow.n8n.json` carries the
CACAO topology as n8n nodes (`manualTrigger`, `set`, `noOp`), with
node ids preserving the CACAO step ids verbatim. The four action
steps emit `n8n-nodes-base.set` nodes carrying the CACAO I/O
contract as editable assignment rows plus the `x_secops_ng`
reference bundles. Operators bind the Set rows to their connectors:

- `propose-rule-version` → detection-store proposal-intake surface
  (webhook / API call against the operator's rule-content store; the
  Set rows record `__rule_id__`, `__rule_version__`, and
  `__proposal_rationale__`).
- `review-rule-version` → operator's peer-review system (ticketing
  webhook, code-review board, PR comment thread — whichever the
  operator has picked for detection-content review); the recorded
  outcome is `__review_verdict__ ∈ {approved, changes_requested,
  rejected}`.
- `ship-rule-version` → detection-store production-status transition
  endpoint; the recorded outcome is `__ship_status__ ∈ {production,
  staged, withdrawn}`.
- `measure-rule-version` → the per-rule-version effectiveness-snapshot
  adapter at `compilers/n8n/evidence/rule_effectiveness_node.py`,
  which writes the artifact per
  `schemas/evidence/rule-effectiveness-snapshot.schema.json` to the
  operator's configured `output_dir` (the volume the operator's
  metric sink ingests from). The worked-example snapshot at
  `examples/n8n/detection_engineering/evidence/rule-effectiveness-snapshot.json`
  shows the on-disk bytes the adapter writes for one representative
  rule version.

To run the worked example locally from the repo root:

```sh
# Regenerate the compiled workflow artifact
./examples/n8n/detection_engineering/regenerate.sh

# Regenerate the per-rule-version effectiveness-snapshot artifact
PYTHONPATH=. python examples/n8n/detection_engineering/regenerate.py
```

To import into an n8n instance: open the workflows list, choose
**Import from File**, and select
`examples/n8n/detection_engineering/workflow.n8n.json`. The workflow
is inactive by default — review and bind the Set rows to your own
connectors before activating. The emitted workflow is a *snapshot of
intent*, not a runnable playbook.

### 5.2 Temporal — `@activity.defn` bodies (reference emitter pending)

`examples/temporal/detection_engineering/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action, with the four action
activities documenting their operator-bound seam (proposal write,
verdict write, status-transition write, effectiveness-snapshot
emission). The committed stub raises `NotImplementedError` in the
activity bodies pending the CORE-TEMPORAL sibling card that wires
the deterministic effectiveness-snapshot adapter into the Temporal
target; operators can drop the module next to their worker today to
see the topology and the activity signatures.

Temporal is the natural fit for the four-state lifecycle: each
per-rule-version execution becomes one workflow run; the review
window becomes a Temporal timer; replay against the same Temporal
event history re-derives the same snapshot bytes (once the
effectiveness-snapshot adapter is wired, the deterministic
`(rule_id, rule_version, captured_at)` key gives byte-identical
re-emission).

The sibling `_audit_mirror.py` carries the `AuditRecord` /
`AuditTrail` types — no `compilers.*` import in the emitted artifact,
so the worker module is a self-contained drop-in.

### 5.3 LangGraph — `@tool` wrappers + agentic-extension hook (reference emitter pending)

`examples/langgraph/detection_engineering/state_bindings.py` carries
the `TypedDict` state and the `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (nodes, edges);
`assemble.py` is the hand-written reference assembly that wires the
GraphSpec + bindings into a `langgraph.graph.StateGraph`. The
committed `state_bindings.py` is a generated stub: each tool's
docstring names the operator-bound seam it discharges and the body
raises `NotImplementedError` until the CORE-LANGGRAPH sibling card
wires the effectiveness-snapshot adapter into the LangGraph target.

LangGraph is the agentic target — an operator who wants to layer an
LM-driven proposal-triage node on top of the `propose` state fills
that as a private extension. The framework-wide EU-resident LM
endpoint guard re-applies the check at process startup
(`compilers/_shared/lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
The compiler never embeds an LLM SDK.

### 5.4 Cross-target parity

All three reference targets are present in the tree today
(`examples/n8n/detection_engineering/`,
`examples/temporal/detection_engineering/`,
`examples/langgraph/detection_engineering/`); the n8n target is the
reference emitter that ships the deterministic effectiveness-snapshot
adapter, and the Temporal / LangGraph targets ship stub artifacts
pending the CORE-TEMPORAL / CORE-LANGGRAPH sibling cards. When those
land, the per-target byte-parity goldens under
`tests/examples/detection_engineering/` pin (a) the per-target
workflow artefact and (b) the per-target effectiveness-snapshot
artifact against a fresh emitter run from the canonical CACAO source
— the cross-target byte-parity property the framework relies on.

## 6. Observability — OTel + AuditTrail in every target

Every emitted action opens an OpenTelemetry span and appends an
`AuditRecord` to a context-local `AuditTrail` *before* the operator-
bound seam call or the (pending) primitive body. The mirror runs
unconditionally, ahead of any OTLP exporter, so the audit property
holds even when the operator has not configured a collector —
typical for disconnected, sovereign, or air-gapped deployments.

Span attributes use the shared `secops_ng.*` keyspace and are stable
across the three targets:

| Attribute key                | Carries                                              |
|------------------------------|------------------------------------------------------|
| `secops_ng.playbook.id`      | CACAO playbook id (`playbook--…`).                   |
| `secops_ng.playbook.version` | Content version pinned in the playbook.              |
| `secops_ng.step.id`          | CACAO step id (`action--…`).                         |
| `secops_ng.step.name`        | Human-readable step label.                           |
| `secops_ng.step.type`        | CACAO step type (`action`, `start`, `end`).          |
| `secops_ng.tool.name`        | Emitted tool / activity / Code-node function name.   |
| `secops_ng.compile.target`   | `n8n` / `temporal` / `langgraph` discriminator.      |

Span boundaries per target:

- **n8n** — the compiled workflow is a snapshot of intent; OTel
  instrumentation is a per-node operator concern documented per
  node-id, not a runtime guarantee of the emitted JSON.
- **Temporal** — workflow span (`workflow.<stable_id>`) at workflow
  entry; activity span (`activity.<step_id>`) on every activity body,
  with retries opening a fresh child span per Temporal attempt.
- **LangGraph** — node span (`node.<step_id>`) wrapping every node
  assembled from `graph_spec.json`; tool span (`tool.<step_id>`)
  inside the `@tool` wrapper.

The OTLP exporter endpoint is operator-supplied
(`OTEL_EXPORTER_OTLP_ENDPOINT`). The compiler never sets a default and
never imports a vendor SDK; pointing the exporter at a managed APM is
a downstream choice the operator owns end-to-end. The sovereignty
posture asks for an EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline.

## 7. Metrics — what the lifecycle exposes

Four indicator catalogue entries surface the detection-engineering
lifecycle posture to the operator's metrics dashboard. The catalogue
entries live under `content/metrics/` and read against the per-rule-
version effectiveness snapshots the `measure` state emits.

- **`kpi.detection_coverage@v1`** — share of the operator's tracked
  ATT&CK-technique coverage claim materialised by shipped detection
  rules in the evaluation window. Catalogue:
  [`content/metrics/detection_coverage.yaml`](../../content/metrics/detection_coverage.yaml).
- **`kpi.false_positive_rate@v1`** — false-positive rate the shipped
  rule population exhibits against the operator's baseline telemetry
  in the evaluation window. Catalogue:
  [`content/metrics/false_positive_rate.yaml`](../../content/metrics/false_positive_rate.yaml).
- **`kri.control_effectiveness@v1`** — control-effectiveness risk
  signal for the shipped detection-rule population, materialised by
  the per-rule-version effectiveness snapshots the lifecycle emits.
- **`kpi.control_effectiveness_coverage@v1`** and
  **`kri.overdue_effectiveness_tests@v1`** — the coverage / overdue
  slice of the same effectiveness-assessment stream, lifted by the
  NIS2 Article 21(2)(f) inbound anchor onto its `metric_refs`.

The catalogue entries pin the field-level read contract; the
framework does not ship a hosted dashboard. Operators dashboard the
KPI / KRI series against their own metrics backend.

## 8. Operator customisation points

The playbook is a lifecycle machine; the *content* it moves through
that machine is the operator's. The customisation seams:

- **Rule-review checklist.** The `review-rule-version` step records
  the outcome as `__review_verdict__ ∈ {approved, changes_requested,
  rejected}`, but the operator authors the checklist the reviewer
  assesses against. Typical items: false-positive risk against
  baseline telemetry, ATT&CK-technique coverage claim, query-cost
  ceiling against the operator's SIEM budget, on-call alert-volume
  impact, rollback readiness. The framework does not prescribe the
  checklist — a small operator running a single-analyst SOC will
  compress it; a regulated operator with a dedicated detection
  engineering team will formalise it against a change-approval board.
- **Detection-content format.** Sigma, KQL, EQL, native SIEM-rule
  syntax — the framework treats the rule payload as an opaque string
  attached to the operator-assigned `__rule_id__` / `__rule_version__`.
  The lifecycle moves whichever format the operator's detection
  store speaks natively.
- **Ship-status vocabulary.** The three-value closed vocabulary
  `{production, staged, withdrawn}` is the operator's audit-evident
  record of the shipping outcome. Operators who need a richer
  vocabulary (e.g. splitting `staged` into `staged-canary` /
  `staged-broad`) fork the state's Set-row assignments; the framework
  does not override at runtime.
- **Effectiveness-snapshot destination.** The per-rule-version
  snapshot the `measure` state emits is shaped per
  `schemas/evidence/rule-effectiveness-snapshot.schema.json`; sinking
  it is the operator's choice resolved at the compile target's
  config layer. Point the n8n adapter's `output_dir` at the volume
  the operator's metric sink ingests from (Prometheus scrape target,
  OTLP-receiving collector, evidence-store query layer, or the
  F-CP-06 effectiveness stream's inbound directory). The framework
  ships **no** hosted-SaaS default endpoint.
- **Proposal-intake surface.** The `propose-rule-version` step
  accepts the proposal from whichever surface the operator's
  detection-content authoring stack exposes — a code-review PR
  against a rule repository, a ticketing-system webhook, a chat
  command against an ops bot, or a direct API call against the
  operator's rule-content store.

## 9. Replay and audit story

The byte-parity drift guards land with the CORE-TEMPORAL /
CORE-LANGGRAPH sibling cards under
`tests/examples/detection_engineering/`. Each per-target golden pins
the committed worked-example artifact to a fresh emitter run from the
canonical CACAO source; if the compiler or the playbook changes,
regenerate via the per-target `regenerate.sh` and commit the diff
intentionally.

The cross-target replay property is the harder one: the same
per-rule-version execution, fed through n8n / Temporal / LangGraph,
produces a byte-identical effectiveness snapshot once each target's
adapter is wired against the same `schemas/evidence/rule-effectiveness-
snapshot.schema.json` shape. The `(rule_id, rule_version,
captured_at)` key is the string a regulator can diff to confirm the
property holds across targets.

## 10. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys.
  Connectors are operator-bound at runtime against environment
  variables documented per target.
- **Runtime detection.** The rules this playbook ships fire runtime
  detections against the operator's SIEM downstream; the SI-4
  monitoring control surface those rules drive is operated by the
  per-detection playbooks (`alert_triage`, `incident_management`,
  the per-incident containment playbooks) and by the operator's
  SIEM under its own SI-4 policy. The mappings overlay's
  file-header deliberately omits SI-4 for exactly this reason.
- **Incident handling.** The rules feed incident detection
  downstream, but the handling capability itself is operated by the
  per-incident playbooks. IR-4 is anchored on those playbooks, not
  on this one.
- **Risk assessment.** The proposal rationale typically cites the
  threat the rule addresses, but the organisational risk-assessment
  surface — what threats are in scope, what the residual risk
  posture is — is the F-GO-* governance layer's responsibility.
- **Gating predicates on `review → ship` and `ship → measure`.**
  Tracked as a sibling card; transitions are unconditional in the
  shipped artifact today. The review-verdict variable and the
  shipped-status flag already flow on the wire so the switch
  inserts without touching the surrounding states.

## 11. References

- [`content/playbooks/detection_engineering/README.md`](../../content/playbooks/detection_engineering/README.md)
  — canonical CACAO source overview and pending sibling work.
- [`content/playbooks/detection_engineering/mappings.yaml`](../../content/playbooks/detection_engineering/mappings.yaml)
  — outbound OSCAL / D3FEND / OCSF / NIS2 / CRA overlay with per-step
  control anchors and the in-line closure notes for the deliberate
  OSCAL / D3FEND / DORA / GDPR omissions.
- [`schemas/evidence/rule-effectiveness-snapshot.schema.json`](../../schemas/evidence/rule-effectiveness-snapshot.schema.json)
  — per-rule-version effectiveness-snapshot artifact schema.
- [`schemas/evidence/effectiveness.schema.json`](../../schemas/evidence/effectiveness.schema.json)
  — F-CP-06 effectiveness evidence stream that consumes the
  per-rule snapshot into its `measurement` block.
- [`examples/n8n/detection_engineering/README.md`](../../examples/n8n/detection_engineering/README.md)
- [`examples/temporal/detection_engineering/README.md`](../../examples/temporal/detection_engineering/README.md)
- [`examples/langgraph/detection_engineering/README.md`](../../examples/langgraph/detection_engineering/README.md)
- [`content/mappings/nis2/article-21-2-f.yaml`](../../content/mappings/nis2/article-21-2-f.yaml)
  — NIS2 Article 21(2)(f) inbound anchor.
- [`content/mappings/dora/article-10.yaml`](../../content/mappings/dora/article-10.yaml)
  — DORA Article 10 (Detection) inbound anchor.
- [`content/mappings/cra/annex-i-1-l-logging-monitoring-detection-engineering.yaml`](../../content/mappings/cra/annex-i-1-l-logging-monitoring-detection-engineering.yaml)
  — CRA Annex I §1(l) rule-content-side inbound anchor.
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
- [`ROADMAP.md`](../../ROADMAP.md) § F-WF-04.
