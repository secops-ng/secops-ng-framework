# agentic_threat_response — cookbook walkthrough

Detection and initial response for fully-agentic adversary activity —
autonomous LLM-driven credential harvest, lateral movement, and
encryption chains observed at machine-speed decision cadence. The
`playbook.agentic_threat_response@v1` CACAO v2 playbook ingests an
agentic-threat indicator, isolates the affected credential set at the
IdP, interrupts the resolved lateral edge, hands the case envelope off
to `playbook.incident_management@v1` for the NIS2 Article 23
notification chain, and preserves the correlated evidence bundle the
downstream regulator-submission engine consumes.

Static SOAR playbooks are miscalibrated for the sub-minute
self-correction cadence documented in the first wave of fully-agentic
operations. This playbook is the detect-through-contain slice
purpose-built for that case set; it is not a replacement for the
operator's `identity_compromise`, `ransomware_containment`, or
`incident_management` playbooks, but the machine-speed front stage
that hands off into them.

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the ingest,
credential-isolation, lateral-movement-containment, escalate, and
evidence-preservation steps land in each target.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/agentic_threat_response/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / NIS2 overlay
└── playbook.cacao.json          # canonical CACAO v2 source (playbook.agentic_threat_response@v1)

content/metrics/mttd_agentic_threat.yaml
content/metrics/mttd_agentic_threat.viz.md
                                  # KPI — mean time to detect an
                                  # agentic-threat indicator, keyed to
                                  # the ingest step's OCSF Detection
                                  # Finding intake
content/metrics/mttc_agentic_threat.yaml
content/metrics/mttc_agentic_threat.viz.md
                                  # KPI — mean time to contain from
                                  # ingest through the credential-set
                                  # isolation and lateral-edge
                                  # containment steps
```

The CACAO source is canonical. The five action steps and the
`start` / `end` wiring nodes are the deterministic policy the playbook
*means* — an ingest step feeding a credential-isolation step, feeding
a lateral-movement-containment step, feeding an escalate step that
hands the case envelope off to `playbook.incident_management@v1`,
feeding an evidence-preservation step that persists the correlated
bundle for the NIS2 Article 23 chain. The three worked examples under
`examples/{n8n,temporal,langgraph}/agentic_threat_response/` are the
same playbook compiled into three orchestrator idioms. Everything else
— the detection-layer feed the ingest step reads, the IdP the
credential-isolation step calls into, the network-segmentation control
plane the containment step exercises, and the evidence store the
preservation step commits into — is the operator's data plane.

## 2. CACAO topology

The playbook ships seven steps: one `start`, five `action`, one `end`.
The workflow is linear on the ingest arm — no branching gate — and
the machine-speed cadence property is expressed by the step order and
the operator's own scheduling of the workflow against the detection
layer's Detection Finding stream.

| Step suffix | Step                                       | Discipline                                                                                                                                                                                                    |
|-------------|--------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `…000001`   | agentic-threat-start                       | edge wiring only — no body                                                                                                                                                                                    |
| `…000002`   | ingest agentic-threat indicator            | receive the indicator (anomalous LLM API call volume, rapid credential-enumeration burst, lateral movement inside the observed self-correction window) and hydrate with principal / source-destination context |
| `…000003`   | isolate affected credential set            | revoke sessions, refresh and access tokens for the implicated principal at the IdP; disable the principal for the containment window; alert the IAM auditor lane for the parallel scope audit                  |
| `…000004`   | contain lateral-movement path              | apply a network micro-segmentation call along the resolved lateral edge so the agentic operator cannot pivot off the implicated path during the containment window                                             |
| `…000005`   | escalate to incident-management            | hand off the case envelope to `playbook.incident_management@v1` — the NIS2 Article 23 regulator-notification chain is dispatched by the incident-management engine, not by this playbook                       |
| `…000006`   | preserve evidence for notification chain   | persist an evidence bundle (LLM API call logs, credential-enumeration timeline, lateral-movement graph, containment-action ledger) consumed by the downstream regulator-submission engine                     |
| `…000007`   | agentic-threat-end                         | edge wiring only — no body                                                                                                                                                                                    |

All five action steps carry the CACAO I/O contract (`in_args` /
`out_args`) plus `x_secops_ng` reference bundles (control, telemetry,
metric). The `escalate` step is a cross-playbook reference — this
playbook deliberately does not itself render a regulator submission;
the Article 23 early-warning / 72-hour / one-month chain is anchored
on `incident_management@v1` and this playbook is the upstream case
generator.

## 3. Regulatory anchors

**NIS2 Directive (EU) 2022/2555.** The playbook is the per-iteration
execution surface for two Article 21 obligations, and the case
generator upstream of the Article 23 notification chain:

- **Art. 21(2)(b)** — incident-handling capability. Anchored
  end-to-end on this playbook; the ingest → isolate → contain →
  escalate → preserve chain is the operational incident-handling
  capability for the machine-speed-agentic case set. Inbound edge on
  `content/mappings/nis2/article-21-2-b.yaml`
  (id `nis2:art-21-2-b`).
- **Art. 21(2)(e)** — security in acquisition, development and
  maintenance, including the agentic-tool supply-chain surface (LLM
  API endpoints, agent frameworks, and downstream toolchains an
  autonomous adversary composes against). The ingest step's
  anomalous-LLM-API-call-volume signal is the operator-side
  observable this obligation demands surveillance over. Inbound edge
  on `content/mappings/nis2/article-21-2-e.yaml`
  (id `nis2:art-21-2-e`).
- **Art. 23** — significant-incident notification. Dispatched
  downstream by `playbook.incident_management@v1` from the case
  envelope the escalate step hands off. This playbook is the case
  generator, not the notification renderer.

**OSCAL controls** exercised by the workflow (from
[`content/playbooks/agentic_threat_response/mappings.yaml`](../../content/playbooks/agentic_threat_response/mappings.yaml)):

- **SI-4** (System Monitoring) — anchors the ingest step; the
  agentic-threat indicator arrives from the detection layer that
  SI-4 governs.
- **IR-4** (Incident Handling) — anchors the playbook end-to-end as
  the incident-handling capability for the machine-speed-agentic
  case set.
- **AC-2(13)** (Account Management | Disable Accounts for High-Risk
  Individuals) — anchors the credential-isolation step's IdP disable
  action for the containment window.
- **AC-4** (Information Flow Enforcement) — anchors the lateral-
  movement containment step's interruption of the resolved
  source→destination information flow.
- **SC-7** (Boundary Protection) — anchors the network-boundary
  application of the micro-segmentation policy along the implicated
  lateral edge.
- **IR-6** (Incident Reporting) — anchors the escalate step's
  hand-off to the downstream incident-management engine that renders
  the Article 23 submission.
- **AU-6** (Audit Record Review, Analysis, and Reporting) — anchors
  the evidence-preservation step's correlated review of LLM API call
  logs, credential-enumeration timeline, lateral-movement graph, and
  containment-action ledger persisted as the evidence bundle.

**MITRE D3FEND v1.0.0** technique tags per step:

- `D3-IRA` (Incident Response Analysis) and `D3-UBA` (User Behavior
  Analysis) on the **ingest** step — analysis of the incoming
  indicator plus behaviour-analysis on the sub-minute self-correction
  cadence and enumeration-burst fingerprint an autonomous adversary
  leaves that classical rule-based triage misses.
- `D3-ACI` (Authentication Cache Invalidation) and `D3-AL` (Account
  Locking) on the **credential-isolation** step — invalidation of
  live sessions / refresh and access tokens, plus disable of the
  implicated principal at the IdP for the containment window.
- `D3-NI` (Network Isolation) on the **lateral-movement-containment**
  step — micro-segmentation call along the resolved lateral edge so
  the agentic operator cannot pivot off the implicated path during
  the containment window.

The escalate and evidence-preservation steps are lifecycle-handoff
and audit-record disciplines that D3FEND's runtime-countermeasure
taxonomy does not cover cleanly, and are deliberately not pinned.

## 4. Per-target hand-off

The three reference targets share the CACAO source. Each target
compiles the same five action steps into its native idiom. All three
worked examples ship under
`examples/{n8n,temporal,langgraph}/agentic_threat_response/`, each
directory carrying a mirror of the canonical `playbook.cacao.json`
alongside the compiled artifact and a `regenerate.sh` that re-emits
via the unified `tools.compile` CLI.

### 4.1 n8n — importable workflow JSON

`examples/n8n/agentic_threat_response/workflow.n8n.json` carries the
CACAO topology as n8n nodes (`manualTrigger`, `set`, `noOp`), with
node ids preserving the CACAO step ids verbatim. The five action
steps land as `n8n-nodes-base.set` nodes carrying the CACAO I/O
contract as editable assignment rows an operator binds to their
connectors:

- ingest → detection-layer feed (SIEM / detection-engineering
  output) carrying the OCSF Detection Finding class shape
- credential-isolation → IdP administrative endpoint for session /
  token revocation and account disable
- lateral-movement containment → network segmentation control plane
- escalate → intake seam on the operator's deployed
  `incident_management` workflow (any of the three targets)
- evidence-preservation → operator's evidence store (object store,
  case management system, or persistence backend under change
  control)

Import the JSON directly into an n8n instance; the Set-row
assignments are the seams the operator wires against their
credentials in the n8n credentials store.

### 4.2 Temporal — deterministic workflow module

`examples/temporal/agentic_threat_response/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action. Activity bodies raise
`NotImplementedError` after opening the span and appending an
`AuditRecord` on the context-local `AuditTrail`, so an integrator
sees exactly which seam they still have to wire against their IdP,
segmentation control plane, and evidence store.

Operators drop `workflow.temporal.py` next to their worker, register
the activities, and run the worker against their Temporal cluster.
Determinism guarantees at the workflow layer survive the placeholder
activity bodies.

### 4.3 LangGraph — graph spec + state bindings + agentic hook

`examples/langgraph/agentic_threat_response/state_bindings.py`
carries the `TypedDict` state and the `@tool`-decorated action
wrappers; `graph_spec.json` carries the target-neutral topology
(nodes, edges); `assemble.py` is the canonical reference assembly
that wires the spec into a `StateGraph`. Tool bodies raise
`NotImplementedError` until the operator wires them.

The LangGraph target is a natural fit for this playbook: the ingest
step's behaviour-analysis surface is a candidate for an LLM-driven
node filling the framework's `AGENTIC_HOOK` slot on a self-hosted
open-weights inference endpoint or an EU-hosted managed endpoint.
The framework-wide EU-resident LM endpoint guard re-applies at
process startup; see
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 5. Determinism — artifact_id across targets

The compiled artifact identifier is derived from the canonical CACAO
source and the compile target's overlay, and **does not key on the
compile-target discriminator**. The same execution context — same
`__indicator_id__`, same principal, same lateral path, same evidence
bundle identifier — produces byte-identical `AuditRecord` payloads
on the shared `AuditTrail` across n8n / Temporal / LangGraph, and
byte-identical case-envelope contents on the escalate step's Incident
Finding.

The byte-parity drift guards under
`tests/examples/agentic_threat_response/` pin each target's committed
worked-example artifact to a fresh emitter run from the canonical
source. If the compiler or the playbook changes, regenerate via the
per-target `regenerate.sh` and commit the diff intentionally.

The cross-target replay property is the harder one, and it is the
sovereign-security property a regulator can diff against: the same
indicator, fed through all three targets, produces byte-identical
credential-isolation account-change events, byte-identical
containment-action ledger entries, and byte-identical evidence-bundle
receipts once each target's activity / tool bodies are wired against
the same operator seams.

## 6. Observability — OCSF telemetry and KPI hooks

Every emitted action opens an OpenTelemetry span and appends an
`AuditRecord` to a context-local `AuditTrail` *before* the primitive
call or the `NotImplementedError`. The mirror runs unconditionally,
ahead of any OTLP exporter, so the audit property holds even when
the operator has not configured a collector — typical for
disconnected, sovereign, or air-gapped deployments. See
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API.

**OCSF v1.3.0 telemetry bindings** shipped by the workflow (from
`mappings.yaml`):

| Class                                         | Direction | Where                                                                                                                              |
|-----------------------------------------------|-----------|------------------------------------------------------------------------------------------------------------------------------------|
| Detection Finding (class_uid 2004)            | consumes  | ingest — the originating agentic-threat indicator is delivered as a Detection Finding by the upstream detection layer              |
| API Activity (class_uid 6003)                 | consumes  | ingest — LLM API call traces carry the machine-speed volume and self-correction cadence fingerprints                               |
| Authentication (class_uid 3002)               | consumes  | ingest — rapid credential-enumeration burst pattern lateralises through the Authentication event stream                            |
| Account Change (class_uid 3001)               | emits     | credential-isolation — each containment action (session revocation, token revocation, IdP disable) is recorded per Account Change  |
| Incident Finding (class_uid 2005)             | emits     | escalate — the case envelope handed off to `incident_management@v1` is recorded so the downstream engine reads a portable artifact |

**KPI hooks** wired against the `content/metrics/` catalogue:

- `kpi.mttd_agentic_threat@v1` — mean time to detect an
  agentic-threat indicator, keyed to the ingest step's Detection
  Finding intake. See
  [`content/metrics/mttd_agentic_threat.viz.md`](../../content/metrics/mttd_agentic_threat.viz.md).
- `kpi.mttc_agentic_threat@v1` — mean time to contain across the
  credential-isolation and lateral-edge-containment steps. See
  [`content/metrics/mttc_agentic_threat.viz.md`](../../content/metrics/mttc_agentic_threat.viz.md).

Both KPIs share the operator-scoped window and roll up alongside the
whole-programme `kpi.control_effectiveness@v1` rollup. The framework
does not set numeric acceptability thresholds; those are the
operator's under the state-of-the-art clauses of the applicable
regulatory regime.

## 7. Operator customisation points

The playbook binds the topology, not the vendor. The operator owns
every seam:

- **Detection-layer feed.** Whether the ingest step reads from a
  SIEM, from `playbook.detection_engineering@v1` output, or from a
  bespoke agentic-indicator classifier is operator-owned. The
  framework requires only that the resolved indicator carries the
  OCSF Detection Finding class shape.
- **IdP endpoint.** The credential-isolation step's session / token
  revocation and account disable calls are made against the
  operator's IdP administrative surface — no default endpoint, no
  vendor pin.
- **Segmentation control plane.** The lateral-movement-containment
  step's micro-segmentation call is issued against the operator's
  own control plane, gated by the operator-supplied authorisation
  policy.
- **Evidence store.** The evidence-preservation step commits the
  bundle to a store the operator picks; the AU-6 anchor names the
  discipline, not the store.
- **Containment window.** The duration of the IdP disable and the
  segmentation policy are operator-set. The framework does not
  prescribe numeric values.

## 8. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys, no IdP
  admin endpoints, no segmentation control-plane endpoints.
  Connectors are operator-bound at runtime against environment
  variables documented per target; the framework ships no default
  endpoint per the sovereign-stack constraint.
- **Regulator submission rendering.** The escalate step hands the
  case envelope off; the Article 23 early-warning / 72-hour /
  one-month chain is rendered by `playbook.incident_management@v1`,
  documented in
  [`docs/cookbook/incident_management.md`](./incident_management.md).
- **Deeper identity-side audit.** The credential-isolation step
  alerts the IAM auditor lane for the parallel forced-rotation and
  scope-audit follow-on; that discipline lives on
  `playbook.identity_compromise@v1` and `playbook.iam_auditor@v1`.
- **Cross-regime inbound edges.** DORA, CRA, and GDPR inbound edges
  are recorded on the respective `_orphan_skip.yaml` manifests with
  their rationale; see the outbound overlay's inbound-closure
  comment block for the current reading.
- **Per-deployment YAML.** No separate operator-facing `config.yaml`;
  per-case inputs are the CACAO `playbook_variables` block bound at
  compile time via the standard `__double_underscore__` substitution.

## 9. See also

- [`docs/cookbook/incident_management.md`](./incident_management.md)
  — the escalation target; the NIS2 Article 23 early-warning /
  72-hour / one-month notification chain is rendered there from the
  case envelope this playbook hands off.
- [`docs/cookbook/eu_ai_act_risk_management.md`](./eu_ai_act_risk_management.md)
  — agentic-AI posture context on the provider-side lifecycle
  surface (EU AI Act Article 9 iteration, Article 72 post-market
  monitoring feedback). Providers of high-risk AI systems who are
  also NIS2-scope entities typically run both lanes.
- [`content/playbooks/agentic_threat_response/playbook.cacao.json`](../../content/playbooks/agentic_threat_response/playbook.cacao.json)
  — canonical CACAO source.
- [`content/playbooks/agentic_threat_response/mappings.yaml`](../../content/playbooks/agentic_threat_response/mappings.yaml)
  — outbound OSCAL / D3FEND / OCSF / NIS2 overlay.
- [`content/playbooks/agentic_threat_response/README.md`](../../content/playbooks/agentic_threat_response/README.md)
  — workflow-local overview and status.
- [`examples/n8n/agentic_threat_response/README.md`](../../examples/n8n/agentic_threat_response/README.md)
- [`examples/temporal/agentic_threat_response/README.md`](../../examples/temporal/agentic_threat_response/README.md)
- [`examples/langgraph/agentic_threat_response/README.md`](../../examples/langgraph/agentic_threat_response/README.md)
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
