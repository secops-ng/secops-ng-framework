# GDPR data flow — alert_triage

Per-workflow GDPR data-flow entry for the `alert_triage` cookbook
playbook (`playbook.alert_triage@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/alert_triage/`](../../playbooks/alert_triage/)
(workflow-local module tree) plus the source playbook at
[`content/playbooks/alert_triage.cacao.yaml`](../../playbooks/alert_triage.cacao.yaml).

---

## 1. Purpose

The workflow exists to triage inbound detection alerts so the response
team can act on the high-priority cases, suppress already-seen and
known-benign repeats inside a configurable window without paging, and
route the remaining cases by disposition to the right response branch.
Two source shapes are ingested — push from the detection pipeline and
pull from a shared alert store — and a deterministic prioritisation
policy applies; free-text fields on the alert (analyst narrative) may
be routed through a DSPy module, the priority decision itself stays
in code. The purpose is bounded to that triage decision and the
metric hooks it produces — the workflow does not retain alert payloads
for analytics independent of the case it opens or the suppression
record it links onto.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(f) — legitimate interests**. The operator
has a legitimate interest in operating a security-operations capability
that triages detection alerts and routes them to response, and the
processing here is necessary and proportionate to that interest. The
data subjects (own employees whose accounts or endpoints appear in the
alert; external actors whose identifiers are observed in the alert
context) have a reasonable expectation that detection telemetry
crossing the operator's monitored boundary is subject to security
review.

Secondary: where the operator runs in a regulated sector and is
obliged to maintain detection and incident-handling capability under
**NIS2 Art. 21(2)(b)** as transposed nationally — or under **DORA
Art. 10** for in-scope financial entities — **Art. 6(1)(c) — legal
obligation** also applies to the portion of the workflow that feeds
the incident_management chain.

Special-category data (Art. 9) is not the target of the workflow but
may be incidentally observed inside alert payloads (for example, a
healthcare operator whose detection rule fires on access to a patient
record). The workflow does not extract or persist Art. 9 attributes
independently of the alert-payload retention in §5; the prioritisation
policy operates on metadata, not on Art. 9 content.

## 3. Categories of data subjects and personal data

Data subjects:

- **Employees of the operator** named as the principal in the alert
  (account identifier, endpoint owner, on-call responder receiving
  the page).
- **External actors** whose identifiers are observed in the alert
  context (source IP addresses, external account identifiers
  appearing in authentication or access events).
- **Third parties** named or linked from alert metadata when the
  alert context carries a supply-chain or peer-operator dependency.

Categories of personal data:

- **Identifiers** — work email addresses, account identifiers,
  endpoint hostnames bound to a named owner, on-call responder
  identifier.
- **Network identifiers** — source and destination IP addresses,
  hostnames, user-agent strings.
- **Authentication metadata** — login event attributes, MFA
  outcomes, session identifiers as carried on the alert.
- **Detection metadata** — rule identifier, severity, OCSF Finding
  (2001) and related activity records, the typed alert envelope
  fields the workflow-local payload model validates.
- **Free-text narrative** — the analyst-narrative field that may be
  shaped through the DSPy signature; the field carries observation
  text authored or appended by the responder, not auto-extracted
  personal data.

The workflow processes the typed alert envelope plus an enrichment
projection; the underlying raw telemetry (full log records,
endpoint forensic captures) is not pulled into the workflow's own
state — it stays on the operator's telemetry store and is referenced
by identifier.

## 4. Recipients

Internal recipients:

- The **response team** owning the per-disposition response branch
  (escalate to incident_management, route to a specialist queue,
  suppress against a known-benign or repeat record, close as
  false-positive).
- The **on-call rotation** workflow when the disposition triggers a
  page.
- The **metrics layer** consuming `kpi.mttd@v1`,
  `kpi.mttr_triage@v1`, `kri.alert_suppression_rate@v1`, and the
  prioritisation-policy quality metrics — recipient is the
  aggregated counter, not the per-alert identifier.

External / processor recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **detection pipeline** providing the push source shape (a
  SIEM, EDR console, or detection-as-code pipeline the operator
  runs).
- The **shared alert store** providing the pull source shape
  (typically the same SIEM or an aggregated case-store).
- The **enrichment providers** invoked during the enrichment step
  (asset inventory, identity directory, threat-intel lookups).
- The **paging gateway** and **notification channels** for the
  on-call rotation.

Each operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production;
the framework does not ship the DPAs, but the data-flow record names
the dependency so a sovereignty review can verify it.

## 5. Retention

The workflow itself is stateless — the durable retention horizon is
the parent **case record** or **suppression record** it feeds:

- **Triaged-escalate alerts** are linked onto the incident case
  opened by the incident_management chain and inherit that case's
  retention (the retention hook in
  [data-flow-incident_management.md](./data-flow-incident_management.md)
  § 5).
- **Triaged-specialist alerts** are linked onto the specialist
  queue's case record and inherit that queue's retention policy.
- **Suppressed alerts** are linked onto the existing known-benign
  or repeat record; the suppression record itself retains the
  alert envelope and enrichment projection for the rolling
  suppression window the operator configures, and is purged on
  TTL.
- **Closed-false-positive alerts** retain the envelope on the
  closure record for the operator's quality-review window
  (typically aligned with the prioritisation-policy review cadence)
  and are then purged.
- **OCSF activity records** emitted during enrichment follow the
  operator's telemetry retention policy on the underlying OCSF
  store.

No copy of the underlying raw telemetry is retained by the workflow
beyond the enrichment projection; the durable artifact is the typed
envelope plus enrichment metadata in §3.

## 6. Cross-border transfers

**No transfer.** The workflow is designed to execute end-to-end on
the operator's sovereign-hosted runtime (one of the EU-hostable
reference targets — n8n self-host, Temporal self-host, or LangGraph
self-host on Nebul / OVHcloud / Scaleway / Hetzner) with EU-pinned
processor endpoints for the operator-bound detection-pipeline,
shared-alert-store, and enrichment dependencies.

The technical controls that hold this scoring:

- The reference compile targets are framework-agnostic and run on
  the operator's own sovereign-hosted runtime; no SecOps-NG-hosted
  egress path exists in the workflow.
- The DSPy module for the free-text analyst-narrative field binds
  to the operator's chosen model at compile time; the playbook
  does not call any public-cloud-AI endpoint. Where the operator
  binds a sovereign-hosted model, no transfer occurs.
- The OCSF activity records emit to the operator's telemetry
  store; no external aggregation is invoked.

If an operator binds a non-EU enrichment provider, a non-EU shared
alert store, or a non-EU AI classifier for the prioritisation or
narrative-shaping step, this scoring breaks — the operator MUST
re-score this section under "transfer under SCCs / BCRs /
derogation" and document the supplementary measures (encryption-at-
rest with operator-held keys, pseudonymisation of subject and
account identifiers before egress) before the binding goes live.
Sovereignty review at compile time is the gate.

## 7. Data subject rights

- **Access (Art. 15).** A subject who exercises a SAR against the
  operator can be answered by querying the case-store and
  suppression-record store on the subject's account identifiers
  and other identifiers from §3. The workflow does not introduce a
  separate storage location beyond those parents; the underlying
  telemetry SAR runs against the operator's OCSF / telemetry
  store.
- **Rectification (Art. 16).** The workflow does not store
  subject-supplied attributes that are intended to be updated;
  enrichment metadata is captured-as-observed from the operator's
  directory and asset inventory, and rectification at the subject's
  request flows through those upstream systems, not through the
  triage record. A miscategorised disposition is corrected by the
  response branch as a downstream operational fix, not as an
  Art. 16 rectification.
- **Erasure (Art. 17).** The retention hooks in §5 are the
  operational erasure pathway: closing the parent case and ageing
  the suppression record on TTL erases the workflow's copy of the
  envelope. A standalone subject-initiated erasure request flows
  through the case-store's erasure procedure, which the workflow
  inherits.
- **Objection (Art. 21).** Where the lawful basis is **Art. 6(1)(f)**
  (most operators), a data subject can object to processing on
  grounds relating to their particular situation. The operational
  handling is to flag the subject's identifier on the suppression
  record so subsequent alerts touching that subject are routed to
  manual review rather than automated suppression, and to record
  the objection alongside the relevant case. The operator's
  overriding-legitimate-interest assessment is the gate on whether
  the objection prevails. Where the secondary **Art. 6(1)(c)**
  basis from §2 applies to the incident-handling portion, Art. 21
  does not.
- **Automated decision-making (Art. 22).** The prioritisation
  policy is deterministic, stays in code, and routes the case to a
  human-owned response branch; the DSPy module on the free-text
  narrative is a shaping step, not a routing decision. The
  workflow as shipped does not produce a legal or similarly
  significant effect on a data subject in its own right, so
  Art. 22 does not apply. If an operator binds a classifier whose
  output triggers an automated adverse action against the subject
  (account lockout, endpoint isolation without review), the
  operator MUST re-score this section.

## 8. Outbound personal-data transfer

The workflow has two classes of outbound leg that carry personal
data outside the alert-triage workflow's transient envelope. Each
is scored below against GDPR Chapter V (Art. 44–49); the
EU-residency posture is sovereignty-first by default per Directive
1, and the operator's compile-time bindings are the knobs that can
break the scoring.

**Leg A — Downstream handoff to incident_management / specialist
queue / on_call_rotation.**

- *Destination class.* Internal downstream playbook recipients —
  incident_management on escalation, the operator's specialist
  queue on routing, on_call_rotation on a paging disposition.
  These are framework-internal handoffs, not Art. 28 processor
  destinations.
- *Transfer mechanism.* **No transfer.** The downstream playbooks
  execute on the same sovereign-hosted runtime as the triage
  workflow; the handoff payload moves between framework-internal
  state machines and never crosses the operator's processing
  boundary. The technical control that holds this is the
  framework-agnostic compile target executing all three reference
  runtimes (n8n / Temporal / LangGraph) on the operator's
  EU-hostable infrastructure.
- *EU-residency posture.* Default is EU-resident downstream
  destinations only. If the operator binds a non-EU incident-case
  store or a non-EU specialist-queue runtime, the handoff payload
  inherits the downstream playbook's §8 re-scoring under Art. 46
  SCCs with pseudonymisation of subject and account identifiers
  before egress.
- *Data minimisation on egress.* The handoff envelope carries the
  triage disposition, the inherited alert identifiers, and the
  enrichment projection from §3; it does not duplicate the raw
  telemetry, which stays on the operator's OCSF / telemetry
  store.

**Leg B — Operator-bound processor egress (enrichment providers,
shared alert store, paging gateway).**

- *Destination class.* Operator-bound processors under GDPR
  Art. 28 — asset inventory, identity directory, threat-intel
  lookup, the shared alert store providing the pull-source shape,
  and the paging gateway carrying the on-call disposition. Each
  is operator-supplied through playbook variables; the framework
  ships no default endpoint.
- *Transfer mechanism.* **No transfer** under the default
  binding: the reference compile targets are EU-hostable and the
  framework ships no SecOps-NG-hosted egress path. If the
  operator binds a non-EU enrichment provider, a non-EU shared
  alert store, or a non-EU paging gateway, the binding MUST be
  re-scored under Art. 46 SCCs with supplementary measures
  (encryption-at-rest with operator-held keys, pseudonymisation
  of subject and account identifiers before the enrichment
  lookup or the paging payload egresses) before the binding goes
  live.
- *EU-residency posture.* The compile-time sovereignty review is
  the gate. The framework ships no default processor endpoint
  and no fallback that could route an enrichment lookup, an
  alert-store read, or a paging payload outside the EU; the
  operator's DPA inventory (GDPR Art. 28) is the durable record
  of the binding each dependency depends on.
- *Data minimisation on egress.* The enrichment lookup carries
  the minimum identifier (account name, asset id, indicator
  value) the upstream provider requires to return its
  projection; the paging payload carries the disposition summary
  stripped of the underlying telemetry. Per-alert raw payloads
  are not transmitted to a processor outside the operator's
  primary store.

The §6 cross-border scoring as a whole is **no transfer** —
consistent with both legs above scoring no-transfer under the
default sovereign-stack posture. Any operator re-scoring of a leg
here MUST be reflected in §6 in the same change so the two
sections do not disagree.
