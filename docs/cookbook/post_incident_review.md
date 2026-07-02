# post_incident_review — cookbook walkthrough

Post-incident learning workflow under NIS2 Article 21(2)(b), NIS2
Article 23(4)(d), DORA Article 18(2), DORA Article 19(4)(c), and CRA
Article 14(2). The `playbook.post_incident_review@v1` CACAO playbook
runs *after* an incident has been closed or contained: it collates a
chronological timeline from the artifacts the responders left behind
(ticket comments, chat transcripts, EDR / SIEM exports, network
captures, operator-supplied evidence packages), flags anti-forensics
gaps in the evidence record where the upstream Sigma detections fired
during the incident window, walks a blameless review template against
that timeline (separating contributing factors — process, tooling,
staffing, training, environment — from individual error), and emits a
corrective-action register with owner, due-date, and verification
clause per entry. The playbook does not re-litigate the incident; it
formalises learning into auditable, restartable state.

The corrective-action register is the **deliverable**. Registration is
where this playbook stops: execution and verification of each
corrective action are deliberately out of scope and land on the
operator's existing change / ticketing surface, which carries the CA-5
tracked-to-closure obligation. The playbook is the head of that chain,
not its tail.

Post-incident review is where the **regulator-side lessons-learned
loop closes**. The NIS2 Art. 23(4)(d) final-report clause (root cause,
type of threat, applied and ongoing mitigation measures) and the DORA
Art. 19(4)(c) final-report clause (root-cause analysis, incident
categorisation, mitigation measures applied or planned) both read
against the artefacts this playbook produces — the timeline grounds
the "detailed description", the blameless review's contributing-factors
analysis grounds the root-cause narrative, and the corrective-action
register grounds the "applied and ongoing mitigation measures" clause.
The DORA Art. 18(2) recurring-incident aggregation reads across those
per-incident registers to surface chronic root causes the operator has
not closed.

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the timeline
collation, the blameless review template walk, and the corrective-
action registration flow in each target.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/post_incident_review/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA overlay
└── playbook.cacao.json          # canonical CACAO v2 source (playbook.post_incident_review@v1)

content/mappings/nis2/article-21-2-b.yaml
                                  # NIS2 Art. 21(2)(b) inbound anchor —
                                  # incident-handling capability including
                                  # lessons-learned; backlinks
                                  # playbook.post_incident_review@v1 as
                                  # the operational discharge of the
                                  # lessons-learned slice
content/mappings/nis2/article-23.yaml
                                  # NIS2 Art. 23(4)(d) inbound anchor —
                                  # final report (root cause, type of
                                  # threat, applied and ongoing
                                  # mitigation measures) reads against
                                  # the artefacts this playbook produces
content/mappings/dora/article-19-and-28.yaml
                                  # DORA Art. 19(4)(c) inbound anchor —
                                  # one-month final report reads
                                  # against the same artefacts as the
                                  # NIS2 Art. 23(4)(d) submission; and
                                  # DORA Art. 18(2) recurring-incident
                                  # aggregation reads across the
                                  # corrective-action registers
content/mappings/cra/article-14-and-annex-i.yaml
                                  # CRA Art. 14(2) inbound anchor —
                                  # incident-handling-and-reporting
                                  # obligations, final-report slice
content/mappings/gdpr/data-flow-post_incident_review.md
                                  # GDPR Art. 30 Record of Processing
                                  # Activity for timeline, review
                                  # artefact, and corrective-action
                                  # register processing (responder
                                  # identifiers, affected-subject
                                  # summaries, evidence-gap annotations)
```

The CACAO source is canonical. The three action steps and two
`start` / `end` wiring nodes are the deterministic policy the playbook
*means* — a linear chain from timeline collation, through the blameless
review template walk, into corrective-action registration, closing at
a single `end`. There are no conditional branches: the playbook does
not re-litigate the incident, so every run walks the full three-step
chain. The three worked examples under
`examples/{n8n,temporal,langgraph}/post_incident_review/` are the same
playbook compiled into three orchestrator idioms. Everything else —
the incident record store, the timeline / evidence collator source,
the review-document store, the corrective-action register /
ticketing system, and the anti-forensics detection stack — is the
operator's data plane.

## 2. CACAO topology and lifecycle binding

The playbook ships five steps: one `start`, three `action`, one `end`.
No conditional branches. The three action steps run in strict sequence
against the incident-close handoff envelope.

| Step suffix | Step                          | Discipline                                                                                                                                                                       | Status         |
|-------------|-------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | post_incident_review_start    | edge wiring only — no body                                                                                                                                                       | n/a            |
| `…000002`   | timeline collation            | chronological reconstruction of the incident from the operator's audit-record stream, EDR / SIEM exports, ticket comments, chat transcripts, and evidence packages; anti-forensics detection hits set `__evidence_gaps_present__` | operator-bound |
| `…000003`   | blameless review template     | walk of the operator's review template against the collated timeline, separating contributing factors (process / tooling / staffing / training / environment) from individual error; `__evidence_gaps_present__` == true makes the evidence-gaps section mandatory | operator-bound |
| `…000004`   | corrective-action tracking    | extraction of corrective actions from the review artefact and registration of each entry (owner, due-date, verification clause) onto the operator's change / ticketing surface   | operator-bound |
| `…000005`   | post_incident_review_end      | edge wiring only — no body                                                                                                                                                       | n/a            |

All three action steps carry the CACAO I/O contract (`in_args` /
`out_args`) plus `x_secops_ng` reference bundles (detection, control,
telemetry, metric). One execution emits one timeline artefact, one
review artefact, and one corrective-action register per closed
incident. The register is the durable deliverable; the timeline and
review artefacts are its supporting evidence.

> The playbook maturity is `experimental` on the workflow-local
> content marker. The overlay pins the control, detection, telemetry,
> and metric surface; the n8n reference emitter ships a committed
> `workflow.n8n.json` today, and the Temporal / LangGraph siblings
> ship deterministic emitter output with `NotImplementedError`
> activity / tool bodies pending the per-target CORE cards.
> Cross-target byte-parity goldens land under
> `tests/examples/post_incident_review/` (with the shared CACAO
> fixture at
> `tests/compilers/_shared/fixtures/post_incident_review.cacao.json`).

## 3. Lifecycle contract — the three action states

The per-execution payload — the timeline artefact, the review
document, the corrective-action register — is post-incident learning
content that carries personal data of natural persons (responder
identifiers, affected-subject summaries where the closed incident
touched personal data, evidence-gap annotations correlated with
authentication and process-activity records). The inbound GDPR Art. 30
Record of Processing Activity at
[`content/mappings/gdpr/data-flow-post_incident_review.md`](../../content/mappings/gdpr/data-flow-post_incident_review.md)
covers the timeline, review-artefact, and corrective-action-register
processing the steps below operate on, lawful-basis-grounded in GDPR
Art. 6(1)(c) legal obligation (transposition of NIS2 Art. 21(2)(b),
DORA Art. 6, and CRA Art. 14) with Art. 6(1)(f) legitimate interests
as the secondary basis for the operator's own resilience-improvement
loop. Where the closed incident was a confirmed personal-data breach,
the three artefacts also materialise the operator's GDPR Art. 33(5)
breach-documentation obligation.

**timeline collation** (`…000002`)
:   Reconstruction step. Reads the operator's audit-record stream (EDR
    / SIEM exports, eventlog snapshots), the incident-record store's
    ticket comments and chat transcripts, and any evidence packages
    responders attached during the incident, and lays them out
    chronologically against the incident window. Anti-forensics /
    audit-tampering signals from the upstream Sigma detections pinned
    on `x_secops_ng.detection_refs` — eventlog cleared,
    security-eventlog cleared, important-eventlog cleared,
    eventlog-clear configuration change, event auditing disabled,
    auditpol tampering, PowerShell timestomp — surface here as
    evidence-gap annotations rather than silently smoothing them over,
    and set `__evidence_gaps_present__` for the review step to read.
    Anchored on OSCAL IR-5 (Incident Monitoring — the collated timeline
    and its evidence-gap annotation are the durable monitoring
    artefact), OSCAL AU-6 (Audit Record Review, Analysis, and
    Reporting — the audit-record stream is reviewed for indications of
    inappropriate or unusual activity as part of the reconstruction),
    and OSCAL SI-4 (System Monitoring — the anti-forensics detections
    run on the operator's system-monitoring layer). Anchored on MITRE
    D3FEND v1.0.0 `D3-IRA` (Incident Response Analysis) — the
    Analyze-tactic discipline the timeline reconstruction discharges.
    Feeds `kpi.timeline_completeness@v1`.

**blameless review template** (`…000003`)
:   Review step. Walks the operator's review template against the
    collated timeline. The template separates **contributing factors**
    (process, tooling, staffing, training, environment) from
    **individual error** by construction — decisions taken during the
    incident are read against the evidence available at the time, not
    against hindsight-informed knowledge. When
    `__evidence_gaps_present__` is `true`, the evidence-gaps section
    of the review artefact is **mandatory** rather than optional: the
    reviewer records where the timeline is partial, what decisions
    were made under partial evidence, and what the operator's
    detection stack would need to see to close the gap in future.
    Anchored on OSCAL IR-4 (Incident Handling — the lessons-learned
    slice of the incident-handling capability) and on MITRE D3FEND
    v1.0.0 `D3-IRA`. Feeds `kpi.review_completion_sla@v1`.

**corrective-action tracking** (`…000004`)
:   Registration step. Extracts corrective actions from the review
    artefact and registers each entry — owner, due-date, verification
    clause — onto the operator's change / ticketing surface. The
    register is a **plan-of-action-and-milestones (POA&M) artefact**;
    execution and verification of each corrective action run on the
    operator's existing change management, not inside this playbook.
    Anchored on OSCAL CA-5 (Plan of Action and Milestones) — the
    corrective-action register produced here is the POA&M for the
    closed incident, and the operator's ticketing surface holds the
    tracked-to-closure obligation — and on OSCAL IR-4 (Incident
    Handling) — the lessons-learned loop is auditably closed by the
    registration step. Anchored on MITRE D3FEND v1.0.0 `D3-IRA`. Feeds
    `kpi.corrective_action_close_rate@v1` (share of registered actions
    closed within their due-date window against total registered) and
    `kri.corrective_action_overdue@v1` (count of registered actions
    past their due-date, an audit-evident measurement of the drift
    IR-4 lessons-learned and CA-5 POA&M discipline warn against).

The three action states are operator-bound runtime seams: the
framework ships neither the incident record store, the timeline /
evidence collator source, the review-document store, the corrective-
action register / ticketing system, nor the anti-forensics detection
stack. The playbook is the portable description of *what* the
operator's stack should do once an incident is closed; binding those
seams to real endpoints is the operator's job.

> **LM determinism.** Timeline collation, blameless-review template
> walk (against structured template rows), and corrective-action
> registration are structured reads and writes against operator-owned
> surfaces, not free-text reasoning steps. The playbook binds no DSPy
> signature — there is no LM-driven step at this layer. See
> [`docs/FOUNDATION.md`](../FOUNDATION.md) § LLM determinism. If an
> operator wires an LM-driven summariser on top of the timeline-
> collation step (condensing chat transcripts into a chronological
> narrative slice) or on top of the review step (drafting the
> contributing-factors narrative from the collated timeline), the
> framework-wide EU-resident LM endpoint guard re-applies the check
> at process startup — see
> [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 4. Regulatory anchors

**NIS2 Article 21(2)(b)** — incident-handling capability. The clause
requires essential and important entities to operate an
incident-handling capability covering detection, triage, containment,
remediation, **and capture of lessons learned**. The
post_incident_review playbook is the operational discharge of the
**lessons-learned slice** of that obligation: the timeline grounds
what happened, the blameless review template grounds why, and the
corrective-action register grounds what changes. Inbound anchor at
[`content/mappings/nis2/article-21-2-b.yaml`](../../content/mappings/nis2/article-21-2-b.yaml)
(`nis2:art-21-2-b`) backlinks `playbook.post_incident_review@v1`.

**NIS2 Article 23(4)(d)** — final report (one month after
notification). The clause requires a final report submitted no later
than one month after the incident notification, including a detailed
description of the incident, the type of threat or root cause that
likely triggered it, applied and ongoing mitigation measures, and
(where applicable) the cross-border impact. The three artefacts this
playbook produces are the evidence the final report reads against —
the timeline grounds the "detailed description", the blameless
review's contributing-factors analysis grounds the "type of threat or
root cause", and the corrective-action register grounds the "applied
and ongoing mitigation measures" clause. Inbound anchor at
[`content/mappings/nis2/article-23.yaml`](../../content/mappings/nis2/article-23.yaml)
(`nis2:art-23-final-report`) backlinks
`playbook.post_incident_review@v1`.

**DORA Article 19(4)(c)** — one-month final report. The clause
requires financial entities to submit a final report no later than
one month after the initial incident notification, including the
root-cause analysis, the categorisation of the incident, and the
mitigation measures applied or planned to prevent recurrence. The
post_incident_review artefacts feed the DORA final report the same
way they feed the NIS2 Art. 23(4)(d) submission: the blameless
review's contributing-factors analysis grounds the root-cause
narrative, and the corrective-action register grounds the "mitigation
measures applied or planned" clause. Inbound anchor at
[`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml)
(`dora:art-19-final-one-month`) closes the graph.

**DORA Article 18(2)** — recurring-incident aggregation. The clause
requires identification of incidents that, while individually below
the major-classification threshold, recur with the same apparent root
cause and aggregate to a major incident. Post-incident review feeds
that aggregation: the blameless review's contributing-factors
analysis and the corrective-action register are the per-incident
inputs the operator's recurring-incident-clusters view groups across
incidents to surface chronic root causes that have not been closed.
Inbound anchor at
[`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml)
(`dora:art-18-recurring-incident`) closes the graph.

**CRA Article 14(2)** — final-report slice of the incident-handling-
and-reporting obligations. Manufacturers of products with digital
elements report exploited-vulnerability and severe-incident findings
and issue a final report; the corrective-action register and root-
cause narrative produced by this playbook feed the CRA final-report
lane. Inbound anchor at
[`content/mappings/cra/article-14-and-annex-i.yaml`](../../content/mappings/cra/article-14-and-annex-i.yaml)
(`cra:art-14-final-report`) backlinks
`playbook.post_incident_review@v1`.

**GDPR Article 30** — Record of Processing Activity. The per-workflow
RoPA for post_incident_review lives at
[`content/mappings/gdpr/data-flow-post_incident_review.md`](../../content/mappings/gdpr/data-flow-post_incident_review.md)
and covers the timeline, review-artefact, and corrective-action-
register processing. Where the closed incident was a confirmed
personal-data breach, the three artefacts also materialise the
operator's GDPR Art. 33(5) breach-documentation obligation.

**OSCAL controls** exercised by the workflow (from
[`content/playbooks/post_incident_review/mappings.yaml`](../../content/playbooks/post_incident_review/mappings.yaml)):
IR-4 (Incident Handling — anchors the playbook end-to-end as the
lessons-learned discharge), IR-5 (Incident Monitoring — anchors
timeline collation as the durable monitoring artefact), CA-5 (Plan of
Action and Milestones — anchors corrective-action tracking as the
POA&M for the closed incident), AU-6 (Audit Record Review, Analysis,
and Reporting — anchors the audit-record surface the timeline
collation step reads), SI-4 (System Monitoring — anchors the
anti-forensics detection surface). CA-7 (Continuous Monitoring),
CM-3 (Configuration Change Control), CP-2 (Contingency Plan), and
AU-12 (Audit Record Generation) are deliberately **not** pinned —
closure-tracking, configuration-change application, contingency-plan
update, and audit-record generation are the operator's downstream
surfaces, not this playbook's. The in-line note at the top of
`mappings.yaml` documents each omission.

**MITRE D3FEND v1.0.0** — `D3-IRA` (Incident Response Analysis)
anchors all three action steps: timeline collation, blameless review
template, and corrective-action tracking. The Analyze-tactic
incident-response-analysis discipline is the shared spine of the
lessons-learned loop, so pinning D3-IRA per step rather than per
playbook keeps the step-to-technique correspondence explicit.

**OCSF v1.3.0** — `Process Activity` (class_uid 1007, category 1
System Activity), direction `consumes`. Consumed at the timeline-
collation step: process-creation / process-termination records carry
the auditpol-tampering, timestomp-via-PowerShell, and
suspicious-eventlog-clear signals that contribute to the
`__evidence_gaps_present__` verdict. `File Activity` (class_uid 1001,
category 1 System Activity), direction `consumes`. Consumed at the
timeline-collation step: file-write / file-attribute-change records
carry the timestomp and log-tampering signals that also feed the
evidence-gap verdict. `Authentication` (class_uid 3002, category 3
Identity & Access Management), direction `consumes`. Consumed at the
timeline-collation step: authentication records anchor the
responder-action and identity-activity slices of the chronological
timeline. `Incident Finding` (class_uid 2005, category 2 Findings),
direction `emits`. Emitted by the blameless-review-template and
corrective-action-tracking steps: each milestone (review-artefact
reference, corrective-action register reference, evidence-gaps
verdict) is recorded as an Incident Finding keyed to the closed
incident so the timeline-completeness, review-completion-SLA,
corrective-action close-rate, and corrective-action-overdue metrics
declared on the playbook's `x_secops_ng.metric_refs` can audit timing
and completeness.

## 5. Per-target hand-off

### 5.1 n8n — operator-edited Set rows over the review topology

`examples/n8n/post_incident_review/workflow.n8n.json` carries the
CACAO topology as five n8n nodes (`manualTrigger`, three `set` nodes,
one `noOp`), with node ids preserving the CACAO step ids verbatim.
The three action steps emit `n8n-nodes-base.set` nodes carrying the
CACAO I/O contract as editable assignment rows plus the `x_secops_ng`
reference bundles. There are no conditional or switch nodes: the
review chain is linear. The lossy translations (operator-bound seams,
absent bodies) are recorded in `meta.secops_ng_notes` so the
integrator sees exactly which rows need attention.

Operators bind the Set rows to their connectors:

- `timeline collation` → the operator's incident record store
  (ticket-comment fetch), chat-transcript store, EDR / SIEM
  export API, and evidence-package store; the Set row records
  `__timeline_ref__` and `__evidence_gaps_present__` (fed by the
  anti-forensics detection surface running the upstream Sigma
  references on the operator's detection stack).
- `blameless review template` → the operator's review-document
  store (template read and completed-review write) plus the
  timeline reference from the previous step; the Set row records
  `__review_artefact_ref__`.
- `corrective-action tracking` → the operator's change / ticketing
  system (register write) with owner, due-date, and verification
  clause per entry; the Set row records
  `__corrective_action_register_ref__`.

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/post_incident_review/regenerate.sh
```

To import into an n8n instance: open the workflows list, choose
**Import from File**, and select
`examples/n8n/post_incident_review/workflow.n8n.json`. The workflow
is inactive by default — review and bind the Set rows to your own
connectors before activating. The emitted workflow is a *snapshot of
intent*, not a runnable playbook.

### 5.2 Temporal — `@activity.defn` bodies (SKELETON stub)

`examples/temporal/post_incident_review/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action, with the three action
activities documenting their operator-bound seam (timeline collation,
review-template walk, corrective-action registration). The committed
stub raises `NotImplementedError` in the activity bodies pending the
CORE-TEMPORAL sibling card that wires the deterministic activity
implementations into the Temporal target; operators can drop the
module next to their worker today to see the topology and the
activity signatures.

Temporal is a natural fit for the post-review discipline: each closed
incident becomes one workflow run; each of the three activities
retries against transient failures on the operator's record store,
review-document store, or ticketing surface with first-class Temporal
retry policy; replay against the same Temporal event history
re-derives the same timeline artefact, review artefact, and
corrective-action register once the activity bodies are wired.

### 5.3 LangGraph — `@tool` wrappers + agentic-extension hook (SKELETON stub)

`examples/langgraph/post_incident_review/state_bindings.py` carries
the `TypedDict` state and the `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (three nodes,
linear edges through the review chain to `end`); `assemble.py` is the
hand-written reference assembly that wires the GraphSpec + bindings
into a `langgraph.graph.StateGraph`. The committed `state_bindings.py`
is a generated stub: each tool's docstring names the operator-bound
seam it discharges and the body raises `NotImplementedError` until
the CORE-LANGGRAPH sibling card wires the deterministic tool
implementations into the LangGraph target.

LangGraph is the agentic target — an operator who wants to layer an
LM-driven summariser on top of the `timeline collation` state
(condensing chat transcripts into a chronological narrative) or on
top of the `blameless review template` state (drafting the
contributing-factors narrative from the collated timeline) fills that
as a private extension. The framework-wide EU-resident LM endpoint
guard re-applies the check at process startup
(`compilers/_shared/lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
The compiler never embeds an LLM SDK.

### 5.4 Cross-target parity

All three reference targets are present in the tree today
(`examples/n8n/post_incident_review/`,
`examples/temporal/post_incident_review/`,
`examples/langgraph/post_incident_review/`). The n8n target ships a
committed workflow artifact; the Temporal and LangGraph targets ship
deterministic emitter output with `NotImplementedError` activity /
tool bodies pending the per-target CORE cards. Cross-target byte-
parity goldens land under `tests/examples/post_incident_review/`
(with the shared CACAO fixture at
`tests/compilers/_shared/fixtures/post_incident_review.cacao.json`)
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

## 7. Metrics — what post-incident review exposes

Four indicator catalogue entries surface the post-incident-review
posture to the operator's metrics dashboard. The catalogue entries
live under `content/metrics/` and read against the Incident Finding
records the review-template-walk and corrective-action-tracking steps
emit.

- **`kpi.timeline_completeness@v1`** — share of closed incidents
  whose timeline artefact reaches the operator's documented
  completeness threshold (all required responder-facing artefact
  classes present) to total closed incidents in the evaluation
  window. Catalogue:
  [`content/metrics/timeline_completeness.yaml`](../../content/metrics/timeline_completeness.yaml).
  Reports the head of the lessons-learned chain: if the timeline is
  incomplete, the review and the corrective-action register that read
  against it are grounded in partial evidence.
- **`kpi.review_completion_sla@v1`** — share of closed incidents
  whose blameless review artefact is written within the operator's
  documented review-completion window to total closed incidents in
  the evaluation window. Catalogue:
  [`content/metrics/review_completion_sla.yaml`](../../content/metrics/review_completion_sla.yaml).
  Rising slippage indicates the lessons-learned loop is drifting
  behind the incident-handling capability that IR-4 audits.
- **`kpi.corrective_action_close_rate@v1`** — share of registered
  corrective actions closed within their due-date window to total
  registered actions in the evaluation window. Catalogue:
  [`content/metrics/corrective_action_close_rate.yaml`](../../content/metrics/corrective_action_close_rate.yaml).
  The audit-evident measurement of whether the POA&M discipline
  CA-5 anchors is being honoured downstream.
- **`kri.corrective_action_overdue@v1`** — count of registered
  corrective actions past their due-date without a closure record in
  the evaluation window. Catalogue:
  [`content/metrics/corrective_action_overdue.yaml`](../../content/metrics/corrective_action_overdue.yaml).
  Rising values indicate chronic root causes the operator has
  registered but not closed — the recurring-incident-aggregation
  signal DORA Art. 18(2) reads against.

The catalogue entries pin the field-level read contract; the
framework does not ship a hosted dashboard. Operators dashboard the
KPI / KRI series against their own metrics backend.

## 8. Detection references — the SigmaHQ anti-forensics rules

The playbook cites seven upstream **SigmaHQ rule references** on
`x_secops_ng.detection_refs` (rule ids pinned in the workflow-local
`README.md`; SecOps-NG does not re-author Sigma):

- **Eventlog cleared** (`a62b37e0-…`),
  **Security Eventlog cleared** (`d99b79d2-…`), and
  **Important Windows Eventlog cleared** (`100ef69e-…`) — three
  variant rules matching the eventlog-clear operation across scope
  (all logs / security-only / individually-important channels).
- **Suspicious Eventlog Clearing or Configuration Change Activity**
  (`cc36992a-…`) — configuration-change slice that would silently
  reduce log retention without an explicit clear.
- **Windows Event Auditing Disabled** (`69aeb277-…`) — disable of the
  audit subsystem itself, upstream of the individual clears.
- **Audit Policy Tampering Via Auditpol** (`0a13e132-…`) — auditpol
  invocation modifying the audit-policy scope.
- **PowerShell Timestomp** (`c6438007-…`) — file-attribute tampering
  that shifts the observed timeline for artefacts on disk.

All seven signals attach at the **timeline collation** step and feed
the `__evidence_gaps_present__` verdict the review-template-walk step
reads. They do not attach at the review or registration steps — those
consume the verdict, they do not re-derive it. See
[`content/playbooks/post_incident_review/README.md`](../../content/playbooks/post_incident_review/README.md)
for the rule-reference discipline and the outbound
`x_secops_ng.detection_refs` slot on the playbook.

## 9. Operator customisation points

The playbook is a lessons-learned machine; the *policy* it exercises
is the operator's. The customisation seams:

- **Timeline source artifacts.** The `timeline collation` step reads
  the operator's own audit-record stream, incident-record store,
  chat / transcript store, and evidence-package store. The framework
  does not prescribe the vendors or the fetch APIs; operators wire
  the step to whichever surfaces their incident-handling capability
  runs on (self-hosted, managed vendor, or hybrid). The evidence-
  package format is operator-canonical.
- **Review template.** The `blameless review template` step walks
  the operator's own review template. The framework does not ship a
  template — every organisation has its own house style — but does
  pin the required section boundaries the template must expose
  (contributing factors separated from individual error; an
  evidence-gaps section that is mandatory when
  `__evidence_gaps_present__` is `true`).
- **Corrective-action destination.** The `corrective-action tracking`
  step writes the register to the operator's change / ticketing
  system (Jira, GitLab issues, ServiceNow, or an on-prem ticketing
  tool). The framework does not prescribe the destination; the
  `kpi.corrective_action_close_rate@v1` and
  `kri.corrective_action_overdue@v1` catalogue entries audit the
  timing regardless of the underlying tool.
- **Anti-forensics gap detection behaviour.** The seven Sigma
  detections on `x_secops_ng.detection_refs` run on the operator's
  detection stack, not inside this playbook. Operators tune the
  rule set (adding house-specific anti-forensics signals or
  disabling rules that are too noisy on their environment) at the
  detection layer; the `__evidence_gaps_present__` verdict this
  playbook reads is the boolean output of that policy. The
  evidence-gaps section of the review artefact is the durable
  record of what the detection stack surfaced within the incident
  window.
- **Review-completion SLA.** The window the
  `kpi.review_completion_sla@v1` catalogue entry reads against is
  the operator's documented lessons-learned SLA (typical values:
  one week, two weeks, one month — aligned or tighter than the
  NIS2 Art. 23(4)(d) one-month final-report window). The framework
  does not prescribe the window; the catalogue entry reads against
  whichever window the operator's incident-response programme
  documents.

## 10. Relationship to `incident_management` — the pre-incident / response / review chain

The `post_incident_review` playbook is the **tail** of a three-lane
chain the framework composes:

1. **`playbook.on_call_rotation@v1`** discharges the responder-
   readiness precondition (populated primary slot, bound escalation
   chain, delivered shift-handoff brief) — see
   [`docs/cookbook/on_call_rotation.md`](./on_call_rotation.md).
2. **`playbook.incident_management@v1`** intakes a significant-
   incident signal, classifies it, opens a deterministic timeline
   against the F-PT-02 incident-timeline pattern, and submits the
   NIS2 Art. 23 three-stage notifications (24-hour early warning,
   72-hour notification, one-month final report) — see
   [`docs/cookbook/incident_management.md`](./incident_management.md).
3. **`playbook.post_incident_review@v1`** consumes the closed
   incident (once `incident_management`'s timeline is closed and,
   where applicable, the one-month final report has been submitted)
   and formalises the lessons learned — the timeline artefact, the
   blameless review document, and the corrective-action register.

The **handoff** from `incident_management` to `post_incident_review`
is the closed-incident envelope: the incident id, the closed
timeline reference, and the final-report reference (where the
incident crossed the significance threshold and a final report was
submitted). `post_incident_review` reads those references, extends
the timeline with the responder-facing artefacts it collates, and
produces the review + register artefacts the NIS2 Art. 23(4)(d) and
DORA Art. 19(4)(c) final reports reference for their root-cause and
mitigation slices. The two cookbooks form the pre-incident /
response / review chain the operator's incident-handling capability
runs end-to-end.

The corrective-action register produced here does **not** loop back
into `incident_management` — the register lands on the operator's
change / ticketing surface, and each corrective action is executed
and verified by the operator's downstream lanes (patch management,
detection engineering, IAM, on-call-rotation policy edits, etc.). The
post-review playbook is deliberately open-ended at that seam so the
operator's programme retains full control of the remediation lane.

## 11. Replay and audit story

The byte-parity drift guards land with the CORE-TEMPORAL /
CORE-LANGGRAPH sibling cards under
`tests/examples/post_incident_review/`. Each per-target golden pins
the committed worked-example artifact to a fresh emitter run from
the canonical CACAO source; if the compiler or the playbook changes,
regenerate via the per-target `regenerate.sh` and commit the diff
intentionally.

The cross-target replay property is the harder one: the same closed
incident, fed through n8n / Temporal / LangGraph, produces a
byte-identical timeline artefact reference, review artefact
reference, and corrective-action register reference once each
target's activity / tool bodies are wired against the same operator
seams and the same OSCAL / OCSF / D3FEND reference bundles. The
`(incident_id, timeline_ref, review_artefact_ref,
corrective_action_register_ref, evidence_gaps_present)` key is the
string a regulator can diff to confirm the property holds across
targets.

## 12. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys for the
  incident record store, the chat / transcript store, the EDR /
  SIEM export API, the evidence-package store, the review-document
  store, or the change / ticketing surface. Connectors are operator-
  bound at runtime against environment variables documented per
  target.
- **Closure tracking.** The `corrective-action tracking` step
  **registers** each corrective action; **execution** and
  **verification** run on the operator's change / ticketing surface,
  which holds the CA-5 tracked-to-closure obligation. This playbook
  is the head of the POA&M chain, not its tail. OSCAL CA-7
  (Continuous Monitoring) is deliberately not pinned for exactly
  that reason.
- **Configuration-change application.** Corrective actions that
  demand a configuration change are registered as work items here;
  the change itself is applied by the playbook that lands the
  configuration edit (e.g. `cloud_misconfiguration`'s guided-
  remediation step, `patch_management`, `detection_engineering`).
  OSCAL CM-3 (Configuration Change Control) is deliberately not
  pinned.
- **Contingency-plan update.** Business-continuity improvements
  identified during the review are recorded as corrective actions
  and registered downstream; the contingency-plan update itself is
  exercised by the operator's BCM surface. OSCAL CP-2 (Contingency
  Plan) is deliberately not pinned.
- **Audit-record generation.** The timeline-collation step consumes
  audit records the operator's audit-generation discipline already
  produced; the playbook does not generate audit records itself
  beyond the OCSF Incident Finding case envelope captured under
  SI-4. OSCAL AU-12 (Audit Record Generation) is deliberately not
  pinned.
- **Incident re-litigation.** The playbook is a lessons-learned
  discipline, not a post-mortem re-adjudication of responder
  decisions. The blameless review template's contributing-factors /
  individual-error separation is load-bearing here: reviewing
  responder decisions against the evidence available at the time is
  in scope; reviewing them against hindsight-informed knowledge is
  not.
- **SigmaHQ rule id pinning.** The playbook cites seven upstream
  Sigma anti-forensics rule references. Stable upstream rule ids
  are pinned by the workflow-local `README.md` and by the CORE-layer
  detection mapping, not by this cookbook; SecOps-NG does not
  re-author Sigma.

## 13. References

- [`content/playbooks/post_incident_review/README.md`](../../content/playbooks/post_incident_review/README.md)
  — canonical CACAO source overview and status.
- [`content/playbooks/post_incident_review/mappings.yaml`](../../content/playbooks/post_incident_review/mappings.yaml)
  — outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA overlay with
  per-step control anchors and the in-line closure notes for the
  deliberate OSCAL omissions.
- [`content/mappings/nis2/article-21-2-b.yaml`](../../content/mappings/nis2/article-21-2-b.yaml)
  — NIS2 Article 21(2)(b) inbound anchor.
- [`content/mappings/nis2/article-23.yaml`](../../content/mappings/nis2/article-23.yaml)
  — NIS2 Article 23(4)(d) inbound anchor.
- [`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml)
  — DORA Article 19(4)(c) and Article 18(2) inbound anchors.
- [`content/mappings/cra/article-14-and-annex-i.yaml`](../../content/mappings/cra/article-14-and-annex-i.yaml)
  — CRA Article 14(2) inbound anchor.
- [`content/mappings/gdpr/data-flow-post_incident_review.md`](../../content/mappings/gdpr/data-flow-post_incident_review.md)
  — GDPR Article 30 Record of Processing Activity.
- [`docs/cookbook/incident_management.md`](./incident_management.md)
  — pre-incident / response cookbook that feeds this one.
- [`docs/cookbook/on_call_rotation.md`](./on_call_rotation.md)
  — responder-readiness cookbook that feeds `incident_management`.
- [`examples/n8n/post_incident_review/README.md`](../../examples/n8n/post_incident_review/README.md)
  — n8n worked-example walkthrough and import instructions.
- [`examples/temporal/post_incident_review/README.md`](../../examples/temporal/post_incident_review/README.md)
  — Temporal worked-example stub.
- [`examples/langgraph/post_incident_review/README.md`](../../examples/langgraph/post_incident_review/README.md)
  — LangGraph worked-example stub.
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
