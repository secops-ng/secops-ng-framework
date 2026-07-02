# on_call_rotation — cookbook walkthrough

Responder-readiness workflow under NIS2 Article 21(2)(b), NIS2 Article
23(4)(a), DORA Article 6(4), DORA Article 19(4)(a), and CRA Article
13(12). The `playbook.on_call_rotation@v1` CACAO playbook operates the
on-call rotation as durable, auditable state: it reads the current
rotation roster against the evaluated shift window, resolves who holds
the primary slot and who receives the next shift, binds the escalation
chain (primary / secondary / manager) the operator's paging system fans
out through, and — when the evaluated window crosses a rotation
boundary — composes a structured handoff brief from open incidents,
recent alerts, outstanding escalations, and the ack-latency snapshot
for the prior shift, and delivers it to the incoming on-call along the
operator's pre-bound channel.

The rotation is the **head of the regulator-notification clock**. The
NIS2 Art. 23(4)(a) 24-hour early-warning window and the DORA Art.
19(4)(a) 4-hour initial-notification window both start at the
responder's first acknowledgement, so an unbound primary slot or a
slow ack delays every downstream notification step regardless of how
fast those steps themselves run. Everything the per-incident playbooks
(`ransomware_containment`, `data_exfil`, `identity_compromise`,
`phishing_triage`, `post_incident_review`) do sits on top of a
populated primary slot and a delivered handoff brief.

The playbook is reentrant and side-effect-free outside the handoff
window; the only durable change in steady state is the bound
escalation chain published to the paging system's runtime
configuration. A steady-state mid-shift execution runs the load-roster
and bind-escalation steps and closes at `end` without generating or
delivering a brief.

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the roster
resolution, the escalation-chain binding, the handoff brief, and the
delivery dispatch flow in each target.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/on_call_rotation/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA overlay
└── playbook.cacao.json          # canonical CACAO v2 source (playbook.on_call_rotation@v1)

content/mappings/nis2/article-21-2-b.yaml
                                  # NIS2 Art. 21(2)(b) inbound anchor —
                                  # incident-handling capability;
                                  # backlinks playbook.on_call_rotation@v1 as the
                                  # responder-readiness precondition
content/mappings/nis2/article-23.yaml
                                  # NIS2 Art. 23(4)(a) inbound anchor —
                                  # 24-hour early-warning notification;
                                  # the rotation is the head of the clock
content/mappings/dora/article-19-and-28.yaml
                                  # DORA Art. 19(4)(a) inbound anchor —
                                  # 4-hour post-classification initial-notification window
content/mappings/dora/article-6-governance.yaml
                                  # DORA Art. 6(4) inbound anchor —
                                  # clearly assigned functions and
                                  # communication-cooperation-coordination arrangements
content/mappings/cra/article-13-12-spoc-on-call-rotation.yaml
                                  # CRA Art. 13(12) inbound anchor —
                                  # after-hours reachability slice of the SPOC obligation
content/mappings/gdpr/data-flow-on_call_rotation.md
                                  # GDPR Art. 30 Record of Processing Activity for
                                  # roster attributes, ack-latency snapshot, and
                                  # inherited incident metadata
```

The CACAO source is canonical. The four action steps and one
conditional branch are the deterministic policy the playbook *means* —
a linear roster-and-bind chain feeding a two-lane branch on the
shift-handoff-window predicate, then a linear brief-and-deliver chain
on the true lane. The three worked examples under
`examples/{n8n,temporal,langgraph}/on_call_rotation/` are the same
playbook compiled into three orchestrator idioms. Everything else —
the roster source of truth, the paging system, the open-incident
store, the recent-alert source, the ack-latency-snapshot source, the
structured handoff store, and the incoming-responder notification
channel — is the operator's data plane.

## 2. CACAO topology and lifecycle binding

The playbook ships seven steps: one `start`, four `action`, one
`if-condition`, one `end`. The single conditional branch fires on the
`__handoff_window__` predicate — a `true` reading routes into
handoff-brief generation and notification of the incoming responder;
a `false` reading closes the run with the escalation chain bound but
no handoff side effects.

| Step suffix | Step                        | Discipline                                                                                        | Status         |
|-------------|-----------------------------|---------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | rotation-start              | edge wiring only — no body                                                                        | n/a            |
| `…000002`   | load rotation roster        | read the operator's roster source of truth against the evaluated shift window (`__current_on_call__`, `__next_on_call__`) | operator-bound |
| `…000003`   | bind escalation tiers       | resolve the primary / secondary / manager chain and publish to the paging system's runtime config (`__escalation_chain__`, `__handoff_window__`) | operator-bound |
| `…000004`   | shift handoff window?       | `if-condition` — branches on `__handoff_window__`                                                 | n/a            |
| `…000005`   | generate handoff brief      | compose the structured brief (open incidents, recent alerts, outstanding escalations, ack-latency snapshot) as `__brief_id__` | operator-bound |
| `…000006`   | notify incoming on-call     | deliver the brief reference to the incoming responder along the operator's pre-bound channel      | operator-bound |
| `…000007`   | rotation-end                | edge wiring only — no body                                                                        | n/a            |

All four action steps carry the CACAO I/O contract (`in_args` /
`out_args`) plus `x_secops_ng` reference bundles (control, telemetry,
metric). One execution emits at most one bound escalation chain per
shift window and, when the handoff branch fires, at most one brief
artifact and one delivery record. Steady-state mid-shift executions
run the roster and bind-escalation steps and close without a brief.

> The playbook maturity is `experimental` on the workflow-local
> content marker. The overlay pins the control and regulatory
> surface; the n8n reference emitter ships a committed
> `workflow.n8n.json` today, and the Temporal / LangGraph siblings
> ship deterministic emitter output with `NotImplementedError`
> activity / tool bodies pending the per-target CORE cards.
> Cross-target byte-parity goldens land under
> `tests/examples/on_call_rotation/` (and the shared CACAO fixture
> under `tests/compilers/_shared/fixtures/on_call_rotation.cacao.json`).

## 3. Lifecycle contract — the four action states

The per-execution payload — roster slot bindings, escalation-chain
identifiers, handoff-window predicate, brief-artifact reference — is
governance-and-notification content that carries limited personal data
of natural persons (responder handles as identified by the operator's
roster source). The inbound GDPR Art. 30 Record of Processing Activity
at
[`content/mappings/gdpr/data-flow-on_call_rotation.md`](../../content/mappings/gdpr/data-flow-on_call_rotation.md)
covers the responder-identifier, roster-attribute, ack-latency-snapshot,
and inherited-incident-metadata processing the steps below operate on,
lawful-basis-grounded in GDPR Art. 6(1)(f) legitimate interests with
Art. 6(1)(c) legal obligation as the secondary basis where NIS2 Art.
21(2)(b) or DORA Art. 6 transposition applies. The framework treats
`__current_on_call__` and `__next_on_call__` as roster-scoped opaque
identifiers under the operator's own naming convention (paging-system
identifier, employee identifier, or work email).

**load rotation roster** (`…000002`)
:   Roster-resolution step. Reads the operator's roster source of
    truth (paging system schedule, calendar feed, or roster file) and
    normalises its output into per-shift slot bindings against
    `__shift_window__`. Sets `__current_on_call__` (the responder
    holding the primary slot for the evaluated window) and
    `__next_on_call__` (the responder receiving the next shift; empty
    when the workflow runs mid-shift). Anchored on OSCAL AC-2 (Account
    Management) — the roster slots resolved here are the per-shift
    managed-account view of the responder population — and on MITRE
    D3FEND v1.0.0 `D3-AM` (Account Monitoring) — the Detect-tactic
    account-monitoring discipline on the responder population.
    Deliberately not pinned to IR-4 (Incident Handling): the
    incident-handling capability itself is operated by the
    per-incident playbooks. Feeds
    `kpi.coverage_on_call_schedule@v1` (share of in-scope on-call
    hours with at least one named primary responder assigned).

**bind escalation tiers** (`…000003`)
:   Escalation-binding step. Resolves the escalation chain the paging
    system will fan through when an alert is not acknowledged —
    primary (current on-call), secondary (back-up slot from the
    roster), then manager — and publishes the bound chain to the
    paging system's runtime configuration so the next page uses it.
    Sets `__escalation_chain__` and `__handoff_window__` (the boolean
    predicate the if-condition reads). Anchored on OSCAL IR-8
    (Incident Response Plan) — the escalation chain is the
    per-execution materialisation of the plan's escalation-path
    element — and on MITRE D3FEND v1.0.0 `D3-AM` (Account Monitoring)
    — the durable record of which managed accounts are in scope for
    paging on the evaluated shift window. Deliberately not pinned to
    AC-5 (Separation of Duties): the escalation chain encodes tier
    ordering, not a separation-of-duties assertion. Feeds
    `kpi.mttr_on_call_ack@v1` (median time from page dispatch to first
    acknowledgement — the head of the NIS2 Art. 23 24-hour clock and
    the DORA Art. 19 4-hour clock) and `kri.escalation_tier_breach@v1`
    (count of pages that fell through the bound chain to an
    out-of-band escalation in the evaluation window).

**shift handoff window?** (`…000004`, `if-condition`)
:   Deterministic branch on `__handoff_window__`. `true` routes into
    `generate handoff brief`; `false` routes directly to `end` with
    the escalation chain bound but no brief generated and no delivery
    dispatched. The condition is lossless: whichever branch runs, the
    bound escalation chain is durable in the paging system's runtime
    configuration and audited by the coverage KPI.

**generate handoff brief** (`…000005`)
:   Brief-composition step. Composes a structured handoff brief
    covering open incidents, recent alerts within the configured
    lookback, outstanding escalations, and the ack-latency snapshot
    for the prior shift. The brief is emitted as a structured artifact
    (markdown + a JSON payload), not free-form prose, so the incoming
    on-call ingests it deterministically. Sets `__brief_id__` — the
    identifier of the persisted brief artifact in the operator's
    structured handoff store. Anchored on OSCAL IR-7 (Incident
    Response Assistance) — the audit-evident discharge of the
    assistance obligation across the rotation boundary. Deliberately
    not pinned to a D3FEND technique: brief composition is a
    responder-readiness governance discipline, not a runtime
    countermeasure, mirroring the `iam_auditor` D3-UAP gap note and
    the `crypto_posture_management` / `backup_recovery` /
    `infra_posture_management` precedents. Feeds
    `kpi.handoff_brief_delivery_sla@v1` (compose-time contribution).
    Two upstream SigmaHQ rule names — off-hours / unusual-hours
    authentication anomaly and suspicious privileged-account
    modification — are cited in the playbook's
    `external_references` so the brief surfaces rotation-gap risk in
    the incoming responder's window explicitly rather than implicitly;
    upstream rule ids are pinned by the CORE-layer detection mapping
    (see § 8).

**notify incoming on-call** (`…000006`)
:   Delivery step. Delivers the handoff brief reference (via
    `__brief_id__` and `__next_on_call__`) to the incoming responder
    along the operator's pre-bound channel — paging system DM, chat
    thread, or email. Tracked as a distinct step from brief
    composition so `kpi.handoff_brief_delivery_sla@v1` can report
    compose-time and deliver-time independently, and so a brief
    written but never delivered is a different failure mode than a
    brief not written at all. Deliberately not pinned to a D3FEND
    technique: delivery is a notification discipline, mirroring the
    `backup_recovery` notify-continuity-owner gap note and the
    `crypto_posture_management` notify-crypto-owner gap note.

The four action states are operator-bound runtime seams: the framework
ships neither the roster source of truth, the paging system, the
open-incident store, the recent-alert source, the ack-latency-snapshot
source, the structured handoff store, nor the notification channel.
The playbook is the portable description of *what* the operator's
stack should do on each shift window; binding those seams to real
endpoints is the operator's job.

> **LM determinism.** Roster resolution, escalation-chain binding,
> brief composition (from structured inputs), and notification
> delivery are structured reads and writes against operator-owned
> surfaces, not free-text reasoning steps. The playbook binds no DSPy
> signature — there is no LM-driven step at this layer. See
> [`docs/FOUNDATION.md`](../FOUNDATION.md) § LLM determinism. If an
> operator wires an LM-driven summariser on top of the brief-
> composition or notification step (a private, forward-looking
> extension), the framework-wide EU-resident LM endpoint guard
> re-applies the check at process startup — see
> [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 4. Regulatory anchors

**NIS2 Article 21(2)(b)** — incident-handling capability. The clause
requires essential and important entities to operate an
incident-handling capability (detect, triage, contain, remediate,
capture lessons learned). The on_call_rotation playbook discharges the
**responder-readiness precondition** of that capability: without a
bound primary slot, a populated escalation chain, and a delivered
shift-handoff brief, the detect / triage / contain steps the
per-incident playbooks operate have no durable responder to dispatch
against. Inbound anchor at
[`content/mappings/nis2/article-21-2-b.yaml`](../../content/mappings/nis2/article-21-2-b.yaml)
(`nis2:art-21-2-b`) backlinks `playbook.on_call_rotation@v1` and pins
the paired metrics (`kpi.coverage_on_call_schedule@v1`,
`kpi.mttr_on_call_ack@v1`, `kpi.handoff_brief_delivery_sla@v1`,
`kri.escalation_tier_breach@v1`).

**NIS2 Article 23(4)(a)** — 24-hour early-warning notification. The
clause sets a 24-hour window from awareness of a significant incident
during which the entity submits an early-warning notification to the
CSIRT or competent authority. The **24-hour clock starts at the
responder's first acknowledgement**, so the awareness-to-ack latency
`kpi.mttr_on_call_ack@v1` audits, plus the coverage guarantee
`kpi.coverage_on_call_schedule@v1` audits on the primary slot, jointly
determine how much of the 24-hour window is consumed before any
downstream notification step can run. Inbound anchor at
[`content/mappings/nis2/article-23.yaml`](../../content/mappings/nis2/article-23.yaml)
(`nis2:art-23-early-warning`) lists this playbook alongside the
per-incident playbooks that operate the classification and submission
steps.

**DORA Article 19(4)(a)** — 4-hour post-classification initial
notification. The clause requires financial entities to submit an
initial notification of a major ICT-related incident to the competent
authority within 4 hours of classification as major (and no later than
24 hours from awareness). The **4-hour post-classification clock also
starts at the responder's first acknowledgement**; an unbound primary
slot or a slow ack delays the whole notification chain regardless of
how fast the submission step itself runs. Inbound anchor at
[`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml)
(`dora:art-19-initial-4h`) closes the graph.

**DORA Article 6(4)** — clearly assigned functions and communication /
cooperation / coordination arrangements. The clause requires the ICT
risk-management framework to carry clearly assigned functions and
responsibilities for all ICT-related tasks and the arrangements for
effective communication, cooperation, and coordination among them on a
continuous basis. The on_call_rotation playbook is the per-shift
materialisation of the on-call responsibility arrangement: the roster
step identifies the named responder discharging the ICT-related
incident-response function for the evaluated shift window; the
bind-escalation step publishes the communication-cooperation-
coordination arrangement to the paging system's runtime configuration;
the brief-and-deliver steps carry the arrangement across the rotation
boundary so the framework remains operable on a continuous basis.
Inbound anchor at
[`content/mappings/dora/article-6-governance.yaml`](../../content/mappings/dora/article-6-governance.yaml)
(`dora:art-6-governance`) backlinks `playbook.on_call_rotation@v1`.
The annual-review-and-audit-cycle slice of Art. 6 (sibling
`article-6.yaml`, `dora:art-6-framework`) is deliberately **not**
pinned — that file is annual-review and ICT-auditor-cycle scoped and
does not discharge per-shift on-call responsibility.

**CRA Article 13(12)** — single point of contact, after-hours
reachability slice. The clause requires manufacturers to provide a
single point of contact for users to communicate directly and rapidly
with them, including for the reporting of vulnerabilities. The
on_call_rotation playbook is the **after-hours reachability
continuation** of that SPOC obligation — the rotation carries the
Annex I §2(5) coordinated-vulnerability-disclosure intake outside
business hours. Inbound anchor at
[`content/mappings/cra/article-13-12-spoc-on-call-rotation.yaml`](../../content/mappings/cra/article-13-12-spoc-on-call-rotation.yaml)
(`cra:art-13-12-spoc-on-call-rotation`) closes the graph. Sibling to
the business-hours edge filed against the same Art. 13(12) SPOC
clause for the `it_security_support_agent` playbook.

**OSCAL controls** exercised by the workflow (from
[`content/playbooks/on_call_rotation/mappings.yaml`](../../content/playbooks/on_call_rotation/mappings.yaml)):
AC-2 (Account Management — anchors `load rotation roster`), IR-8
(Incident Response Plan — anchors `bind escalation tiers`), IR-7
(Incident Response Assistance — anchors `generate handoff brief` and
`notify incoming on-call`), CP-2 (Contingency Plan — anchors the
continuity surface of the roster and escalation binding as per-shift
personnel identification). IR-4 (Incident Handling), AC-5 (Separation
of Duties), AU-2 (Event Logging), and IA-2 (Identification and
Authentication) are deliberately **not** pinned — the incident-
handling capability lives on the per-incident playbooks, the
escalation chain encodes tier ordering rather than separation-of-
duties, the audit-event policy is upstream of this workflow, and the
responder authentication is performed by the operator's IdP / paging
system rather than by this workflow. The in-line note at the top of
`mappings.yaml` documents each omission.

**MITRE D3FEND v1.0.0** — `D3-AM` (Account Monitoring) at `load
rotation roster` and at `bind escalation tiers`. The brief-composition
and notify steps are deliberately not pinned to a D3FEND technique
because D3FEND v1.0.0 frames its defensive techniques around runtime
countermeasures against adversary behaviours; structured shift-
handoff brief composition and delivery is a responder-readiness
governance discipline, not a runtime countermeasure. The in-line gap
notes in `mappings.yaml` document each deliberate absence, mirroring
the `iam_auditor`, `crypto_posture_management`,
`infra_posture_management`, and `backup_recovery` precedents.

**OCSF v1.3.0** — `Account Change` (class_uid 3001, category 3
Identity & Access Management), direction `both`. Consumed at the
load-roster step (roster source mutation records — paging-system
schedule edits, calendar-feed updates — that re-shape the per-shift
slot binding) and emitted at the bind-escalation step (one record per
shift carrying the bound primary / secondary / manager chain).
`API Activity` (class_uid 6003, category 6 Application Activity),
direction `both`. Consumed at the brief-composition step (reads
against the open-incident store, the recent-alert source, and the
ack-latency-snapshot source within the configured lookback) and
emitted at the brief-composition and notify steps (the brief artifact
emission to the structured handoff store and the delivery dispatch to
the incoming responder's pre-bound channel). The API Activity records
carry the request metadata `kpi.handoff_brief_delivery_sla@v1` reads
to report compose-time and deliver-time independently.

## 5. Per-target hand-off

### 5.1 n8n — operator-edited Set rows over the rotation topology

`examples/n8n/on_call_rotation/workflow.n8n.json` carries the CACAO
topology as seven n8n nodes (`manualTrigger`, four `set` nodes, one
`if`, one `noOp`), with node ids preserving the CACAO step ids
verbatim. The four action steps emit `n8n-nodes-base.set` nodes
carrying the CACAO I/O contract as editable assignment rows plus the
`x_secops_ng` reference bundles. The single `if-condition` node
(`shift handoff window?`) emits an `n8n-nodes-base.if` node with a
placeholder condition the operator must wire to the upstream
`out.handoff_window` field. The lossy translation is recorded in
`meta.secops_ng_notes` so the integrator sees exactly which seams
need attention.

Operators bind the Set rows to their connectors:

- `load rotation roster` → the operator's roster source of truth
  (paging system schedule read, calendar-feed pull, or roster file
  fetch); the Set row records `__current_on_call__` and
  `__next_on_call__`.
- `bind escalation tiers` → the operator's paging system's runtime
  configuration (write of the primary / secondary / manager chain);
  the Set row records `__escalation_chain__` and `__handoff_window__`.
- `generate handoff brief` → the operator's open-incident store,
  recent-alert source, and ack-latency-snapshot source (reads within
  the configured lookback) plus the structured handoff store (write
  of the composed artifact); the Set row records `__brief_id__`.
- `notify incoming on-call` → the operator's pre-bound notification
  channel (paging system DM, chat thread, or email); the Set row
  references `__brief_id__` and `__next_on_call__`.

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/on_call_rotation/regenerate.sh
```

To import into an n8n instance: open the workflows list, choose
**Import from File**, and select
`examples/n8n/on_call_rotation/workflow.n8n.json`. The workflow is
inactive by default — review and bind the Set rows to your own
connectors before activating. The emitted workflow is a *snapshot of
intent*, not a runnable playbook.

### 5.2 Temporal — `@activity.defn` bodies (SKELETON stub)

`examples/temporal/on_call_rotation/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action, with the four action
activities documenting their operator-bound seam (roster read,
escalation-chain publish, brief composition, delivery dispatch). The
committed stub raises `NotImplementedError` in the activity bodies
pending the CORE-TEMPORAL sibling card that wires the deterministic
activity implementations into the Temporal target; operators can drop
the module next to their worker today to see the topology and the
activity signatures.

Temporal is the natural fit for the rotation discipline: each
per-shift-window execution becomes one workflow run; the shift-
handoff-window predicate becomes a Temporal condition that gates the
handoff-branch activities; retries against transient failures on the
paging-system publish or the delivery dispatch get first-class
Temporal semantics (activity retry policy against the paging system
and the notification channel); replay against the same Temporal event
history re-derives the same brief payload and delivery dispatch once
the activity bodies are wired.

### 5.3 LangGraph — `@tool` wrappers + agentic-extension hook (SKELETON stub)

`examples/langgraph/on_call_rotation/state_bindings.py` carries the
`TypedDict` state and the `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (nodes,
conditional edge on the handoff-window predicate, linear edges through
brief composition and delivery); `assemble.py` is the hand-written
reference assembly that wires the GraphSpec + bindings into a
`langgraph.graph.StateGraph`. The committed `state_bindings.py` is a
generated stub: each tool's docstring names the operator-bound seam
it discharges and the body raises `NotImplementedError` until the
CORE-LANGGRAPH sibling card wires the deterministic tool
implementations into the LangGraph target.

LangGraph is the agentic target — an operator who wants to layer an
LM-driven summariser on top of the `generate handoff brief` state
(condensing the open-incident and recent-alert cross-section into a
shift-narrative section of the brief) fills that as a private
extension. The framework-wide EU-resident LM endpoint guard re-applies
the check at process startup
(`compilers/_shared/lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
The compiler never embeds an LLM SDK.

### 5.4 Cross-target parity

All three reference targets are present in the tree today
(`examples/n8n/on_call_rotation/`,
`examples/temporal/on_call_rotation/`,
`examples/langgraph/on_call_rotation/`). The n8n target ships a
committed workflow artifact; the Temporal and LangGraph targets ship
deterministic emitter output with `NotImplementedError` activity /
tool bodies pending the per-target CORE cards. Cross-target byte-
parity goldens land under `tests/examples/on_call_rotation/` (with
the shared CACAO fixture at
`tests/compilers/_shared/fixtures/on_call_rotation.cacao.json`) — the
cross-target byte-parity property the framework relies on.

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
| `secops_ng.step.type`        | CACAO step type (`action`, `start`, `end`, `if-condition`). |
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

## 7. Metrics — what the rotation exposes

Four indicator catalogue entries surface the on-call-rotation posture
to the operator's metrics dashboard. The catalogue entries live under
`content/metrics/` and read against the Account Change records the
bind-escalation step emits and the API Activity records the
brief-composition and notify steps produce.

- **`kpi.coverage_on_call_schedule@v1`** — share of in-scope on-call
  hours that have at least one named primary responder assigned to
  total in-scope on-call hours. Catalogue:
  [`content/metrics/coverage_on_call_schedule.yaml`](../../content/metrics/coverage_on_call_schedule.yaml).
  Answers "is the primary slot populated across the rotation
  calendar?" — the coverage guarantee that both the NIS2 Art. 23
  24-hour early-warning clock and the DORA Art. 19 4-hour initial-
  notification clock rely on.
- **`kpi.mttr_on_call_ack@v1`** — median time from page dispatch to
  first acknowledgement in the evaluation window. Catalogue:
  [`content/metrics/mttr_on_call_ack.yaml`](../../content/metrics/mttr_on_call_ack.yaml).
  The awareness-to-ack latency the head of the regulator-notification
  clock reads against. Rising values indicate the ack surface is
  drifting behind the documented objective — the DORA Art. 19 4-hour
  and NIS2 Art. 23 24-hour signals surface here before they surface
  downstream.
- **`kpi.handoff_brief_delivery_sla@v1`** — share of shift-handoff
  briefs delivered within their committed time-window to total
  in-scope handoffs in the evaluation window. Catalogue:
  [`content/metrics/handoff_brief_delivery_sla.yaml`](../../content/metrics/handoff_brief_delivery_sla.yaml).
  Reports compose-time and deliver-time independently so a brief
  written but never delivered is a different signal than a brief not
  written at all.
- **`kri.escalation_tier_breach@v1`** — count of pages that fell
  through the bound escalation chain to an out-of-band escalation
  (manual page, direct-message escalation, or ad-hoc paging outside
  the documented tier ordering) in the evaluation window. Catalogue:
  [`content/metrics/escalation_tier_breach.yaml`](../../content/metrics/escalation_tier_breach.yaml).
  Rising values indicate the bound chain is not being honoured in
  practice — the escalation-plan drift that IR-8 asks the operator
  to detect and correct.

The catalogue entries pin the field-level read contract; the
framework does not ship a hosted dashboard. Operators dashboard the
KPI / KRI series against their own metrics backend.

## 8. Detection references — the SigmaHQ named rules

The playbook cites two upstream **SigmaHQ rule names** in its
`external_references` (rule ids intentionally not fabricated; the
CORE-layer detection mapping pins the stable upstream ids once
selected):

- **Off-hours / unusual-hours authentication anomaly** — a
  logon-outside-working-hours or unusual-time-authentication signal
  observed in the incoming responder's window surfaces rotation-gap
  risk in the handoff brief: the incoming on-call inherits that open
  signal explicitly rather than implicitly.
- **Suspicious privileged-account modification** — a
  privileged-account modification or role assignment outside an
  approved change window observed during the prior shift also surfaces
  in the handoff brief, so a mid-rotation privilege change is not
  invisible to the responder taking over.

Both signals attach at the brief-composition step (`generate handoff
brief`), not at the rotation-binding step: the brief carries the
context, not the binding. See
[`content/playbooks/on_call_rotation/README.md`](../../content/playbooks/on_call_rotation/README.md)
for the rule-reference discipline (SecOps-NG does not re-author
Sigma; upstream rule ids are pinned by the CORE-layer detection
mapping) and the `detection_refs` slot on the playbook's
`x_secops_ng` extension for the outbound anchor on
`detection.sigma.privileged_account_modification@v1`.

## 9. Operator customisation points

The playbook is a rotation-window machine; the *policy* it exercises
is the operator's. The customisation seams:

- **Paging-system binding.** The `bind escalation tiers` step
  publishes the primary / secondary / manager chain to the operator's
  paging system's runtime configuration. The framework binds neither
  the paging vendor nor the on-call-schedule surface it exposes;
  operators wire the step to whichever paging tool their rotation
  policy runs on (open-source, self-hosted, or a managed vendor). The
  emitted Account Change record is the audit-evident record of the
  binding regardless of the underlying tool.
- **Roster source of truth.** The `load rotation roster` step reads
  the operator's own roster catalogue against `__shift_window__`. The
  framework does not prescribe the source (paging schedule, calendar
  feed, or a roster file in the operator's own repo); operators wire
  the step to whichever source their rotation policy documents. The
  normalisation into `__current_on_call__` and `__next_on_call__` is
  the seam the rest of the workflow reads against.
- **Handoff-brief channel.** The `notify incoming on-call` step
  delivers the brief reference along the operator's pre-bound
  channel — paging system DM, chat thread, email, or the operator's
  incident-notification lane. The framework does not prescribe the
  channel; the `kpi.handoff_brief_delivery_sla@v1` catalogue entry
  audits the time-window regardless of the underlying transport.
- **Ack-latency snapshot lookback.** The prior-shift ack-latency
  snapshot the brief composes is windowed against the operator's
  documented lookback (typical values: one shift, one day, one
  week). The framework does not prescribe the window; the catalogue
  entries for `kpi.mttr_on_call_ack@v1` read against whichever
  window the operator's rotation policy documents.
- **Shift-handoff-window predicate.** The `__handoff_window__`
  boolean is `true` when the evaluated `__shift_window__` crosses a
  rotation boundary. The predicate is derived from the operator's
  rotation calendar; operators with a rotating on-call (weekly,
  daily, follow-the-sun) drive the predicate from their rotation
  schedule, and operators with a single-responder rotation may
  short-circuit the handoff branch entirely against their local
  policy without re-authoring the playbook.

## 10. Replay and audit story

The byte-parity drift guards land with the CORE-TEMPORAL /
CORE-LANGGRAPH sibling cards under `tests/examples/on_call_rotation/`.
Each per-target golden pins the committed worked-example artifact to
a fresh emitter run from the canonical CACAO source; if the compiler
or the playbook changes, regenerate via the per-target
`regenerate.sh` and commit the diff intentionally.

The cross-target replay property is the harder one: the same
per-shift execution, fed through n8n / Temporal / LangGraph, produces
a byte-identical Account Change record (the bound escalation chain)
and — when the handoff branch fires — a byte-identical brief artifact
and delivery record once each target's activity / tool bodies are
wired against the same operator seams and the same OSCAL / OCSF /
D3FEND reference bundles. The `(shift_window, current_on_call,
escalation_chain, brief_id)` key is the string a regulator can diff to
confirm the property holds across targets.

## 11. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys for the
  paging system, the roster source of truth, the open-incident store,
  the recent-alert source, the structured handoff store, or the
  notification channel. Connectors are operator-bound at runtime
  against environment variables documented per target.
- **Incident-handling capability itself.** The rotation-readiness
  surface stops at the responder-readiness precondition (populated
  primary slot, bound escalation chain, delivered handoff brief). The
  detect / triage / contain / remediate lifecycle is operated by the
  per-incident playbooks (`ransomware_containment`, `data_exfil`,
  `identity_compromise`, `phishing_triage`, `post_incident_review`).
  OSCAL IR-4 (Incident Handling) is deliberately not pinned on this
  overlay for exactly that reason.
- **Responder authentication.** The workflow names responders by
  roster handle for the purpose of binding the escalation chain and
  addressing the handoff brief; it does not itself authenticate those
  users. Authentication of the responder when they acknowledge or
  page is performed by the operator's IdP / paging system, not by
  this workflow. OSCAL IA-2 (Identification and Authentication) is
  deliberately not pinned for exactly that reason.
- **Separation of duties.** The escalation chain encodes a tier
  ordering, not a separation-of-duties assertion. A separation-of-
  duties anchor belongs on the governance content surface that
  defines the role split (who may approve, who may execute), not on
  the per-execution rotation-binding step here. OSCAL AC-5
  (Separation of Duties) is deliberately not pinned.
- **Audit-event policy authorship.** The playbook emits OCSF Account
  Change and API Activity records; defining the operator's audit-
  event policy is upstream of this workflow. The emitted records are
  consumed by the operator's existing OCSF store under its AU-2
  policy. OSCAL AU-2 (Event Logging) is deliberately not pinned.
- **SigmaHQ rule id pinning.** The playbook cites two upstream Sigma
  rule *names* (off-hours authentication anomaly, suspicious
  privileged-account modification). Stable upstream rule ids are
  pinned by the CORE-layer detection mapping, not by this cookbook;
  SecOps-NG does not re-author Sigma.

## 12. References

- [`content/playbooks/on_call_rotation/README.md`](../../content/playbooks/on_call_rotation/README.md)
  — canonical CACAO source overview and status.
- [`content/playbooks/on_call_rotation/mappings.yaml`](../../content/playbooks/on_call_rotation/mappings.yaml)
  — outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA overlay with
  per-step control anchors and the in-line closure notes for the
  deliberate OSCAL / D3FEND / GDPR omissions.
- [`content/mappings/nis2/article-21-2-b.yaml`](../../content/mappings/nis2/article-21-2-b.yaml)
  — NIS2 Article 21(2)(b) inbound anchor.
- [`content/mappings/nis2/article-23.yaml`](../../content/mappings/nis2/article-23.yaml)
  — NIS2 Article 23(4)(a) inbound anchor.
- [`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml)
  — DORA Article 19(4)(a) inbound anchor.
- [`content/mappings/dora/article-6-governance.yaml`](../../content/mappings/dora/article-6-governance.yaml)
  — DORA Article 6(4) inbound anchor.
- [`content/mappings/cra/article-13-12-spoc-on-call-rotation.yaml`](../../content/mappings/cra/article-13-12-spoc-on-call-rotation.yaml)
  — CRA Article 13(12) inbound anchor (after-hours reachability slice).
- [`content/mappings/gdpr/data-flow-on_call_rotation.md`](../../content/mappings/gdpr/data-flow-on_call_rotation.md)
  — GDPR Article 30 Record of Processing Activity.
- [`examples/n8n/on_call_rotation/README.md`](../../examples/n8n/on_call_rotation/README.md)
  — n8n worked-example walkthrough and import instructions.
- [`examples/temporal/on_call_rotation/README.md`](../../examples/temporal/on_call_rotation/README.md)
  — Temporal worked-example stub.
- [`examples/langgraph/on_call_rotation/README.md`](../../examples/langgraph/on_call_rotation/README.md)
  — LangGraph worked-example stub.
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
