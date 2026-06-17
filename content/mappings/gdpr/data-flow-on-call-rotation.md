# GDPR data flow — on-call-rotation

Per-workflow GDPR data-flow entry for the `on-call-rotation` cookbook
playbook (`playbook.on_call_rotation@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/on-call-rotation/`](../../playbooks/on-call-rotation/).

---

## 1. Purpose

The workflow exists to operate the operator's on-call rotation as
durable, auditable state: load the current rotation roster against
the evaluated shift window, resolve who holds the primary slot,
bind the escalation chain (primary / secondary / manager) the
operator's paging system will fan out through, and — when the
evaluated window crosses a rotation boundary — compose a structured
handoff brief covering open incidents, recent alerts, and the
ack-latency snapshot, and deliver it to the incoming on-call. The
purpose is bounded to that rotation-operability decision and the
metric hooks it produces (`kpi.coverage_on_call_schedule@v1`,
`kpi.mttr_on_call_ack@v1`, `kpi.handoff_brief_delivery_sla@v1`,
`kri.escalation_tier_breach@v1`); the workflow does not retain
responder behavioural data for analytics independent of the bound
escalation chain and the per-handoff brief.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(f) — legitimate interests**. The operator
has a legitimate interest in maintaining a documented incident-
response readiness capability — knowing who is on call, who escalates
next, and what the incoming responder is inheriting — and the
processing here (responder identifier, escalation tier, ack-latency
on the prior shift) is necessary and proportionate to that interest.
The data subjects (the operator's own employees serving on the
rotation) have a reasonable expectation that their participation in
the rotation is recorded and that operational metrics on their
acknowledgement timeliness are kept.

Secondary: **GDPR Art. 6(1)(c) — legal obligation** applies where the
operator is in scope for **NIS2 Art. 21(2)(b)** (incident-handling
capability) or **DORA Art. 6** (ICT risk-management framework,
governance roles) as transposed nationally. In those operators, the
existence of a documented on-call rotation with a bound escalation
chain is itself a regulatory expectation, and the per-rotation record
is the evidence the workflow produces.

Special-category data (Art. 9) is not the target of the workflow and
is not expected to be incidentally observed — the workflow handles
roster slots, escalation tiers, and handoff metadata, none of which
carries Art. 9 attributes by construction.

## 3. Categories of data subjects and personal data

Data subjects:

- **Employees of the operator** named on the rotation roster
  (current primary, secondary, manager, and the responder receiving
  the next shift).
- **Employees of the operator** who appear in the handoff brief as
  incident commanders, responders, or signatories on the incidents
  inherited by the incoming on-call.

Categories of personal data:

- **Identifiers** — responder identifier (work email address,
  employee identifier, or paging-system handle, depending on the
  operator's roster source), display name where the operator's
  roster surfaces it.
- **Roster attributes** — slot held (primary / secondary / manager),
  shift window the slot covers, escalation tier ordering.
- **Operational metrics** — ack-latency snapshot for the prior
  shift, escalation-tier-breach observations on the rotation.
- **Inherited incident metadata** — the open-incident and
  recent-alert summaries carried into the handoff brief, scoped to
  identifiers and case labels rather than per-subject incident
  payloads (those remain on the parent incident case).

## 4. Recipients

Internal recipients:

- The **incoming on-call** — primary recipient of the handoff brief.
- The **paging system** — recipient of the bound escalation chain,
  which it consumes at page time to fan out to primary / secondary
  / manager.
- The **metrics layer** consuming `kpi.coverage_on_call_schedule@v1`,
  `kpi.mttr_on_call_ack@v1`, `kpi.handoff_brief_delivery_sla@v1`,
  and `kri.escalation_tier_breach@v1` — recipient is the aggregated
  counter, not the per-responder identifier.
- The **on-call governance** function (the control_ref
  `control.on_call_roster_governance@v1`) that owns roster
  accuracy and the escalation-tier policy.

External / processor recipients (operator-bound, named at the
compile-target binding rather than in the playbook):

- The **roster source of truth** — paging-system schedule, calendar
  feed, or roster file the operator pins. The framework reads from
  this source; it does not write back.
- The **delivery channel** carrying the handoff brief to the
  incoming on-call (paging-system DM, chat thread, email). Tracked
  separately from brief generation so the delivery-SLA KPI can
  report compose-time and deliver-time independently.

Each operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production;
the framework does not ship the DPAs, but the data-flow record
names the dependency so a sovereignty review can verify it.

## 5. Retention

The workflow's durable artefacts are the **bound escalation chain**
(steady-state output) and, on a handoff window, the **handoff brief**
(`__brief_id__`). Retention is the operator's rotation-record window:

- **Bound escalation chains** are short-lived runtime configuration
  published to the paging system; each new run rebinds against the
  current shift window. The framework does not retain a separate
  history beyond the audit trail of the rebinding events.
- **Handoff briefs** are retained for the operator's
  rotation-record window — typically the longest of (a) the
  operator's incident-handling-capability evidence period under
  NIS2 Art. 21(2)(b) / DORA Art. 6 (where in scope), and (b) the
  operator's internal post-rotation review window. The operator
  configures the binding; the framework does not pick a default.
- **Roster snapshots** are not retained by the workflow; the
  source-of-truth roster lives on the operator's paging system or
  calendar feed and follows that system's own retention policy.

The retention boundary is enforced by the handoff-brief artifact
store's lifecycle hook plus the paging system's own configuration
history; the workflow itself is stateless beyond the per-run
bindings and the per-handoff brief.

## 6. Cross-border transfers

**No transfer** is the default scoring. The workflow is designed to
execute end-to-end on the operator's sovereign-hosted runtime (one of
the EU-hostable reference targets — n8n self-host, Temporal self-host,
or LangGraph self-host on Nebul / OVHcloud / Scaleway / Hetzner)
against an EU-resident paging system and roster source.

The technical controls that hold this scoring:

- The reference compile targets are framework-agnostic and run on
  the operator's own sovereign-hosted runtime; no SecOps-NG-hosted
  egress path exists in the workflow.
- The roster source is operator-supplied through playbook
  variables; the framework ships no default endpoint and no
  fallback that could route a roster read outside the EU.
- The handoff-brief delivery channel is operator-supplied; the
  framework does not call any default external delivery endpoint.
- The brief is composed locally from inherited incident metadata
  already resident on the operator's case store; no external
  aggregation is invoked.

If an operator binds a non-EU paging system, a non-EU roster source,
a non-EU delivery channel for the handoff brief, or any external AI
classifier on the brief's narrative fields, this scoring breaks —
the operator MUST re-score this section under "transfer under
SCCs / BCRs / derogation" and document the supplementary measures
(encryption-at-rest with operator-held keys, pseudonymisation of
responder identifiers before egress) before the binding goes live.
Sovereignty review at compile time is the gate.

## 7. Data subject rights

- **Access (Art. 15).** A subject who exercises a SAR against the
  operator can be answered by querying the handoff-brief artifact
  store on the responder identifier from §3, plus the paging
  system's own rotation history. The escalation-chain bindings are
  short-lived runtime configuration; the auditable record is the
  rebinding event log against the paging system's audit trail.
- **Rectification (Art. 16).** Applicable where a roster slot or
  responder identifier is recorded incorrectly. Rectification
  flows through the operator's roster source of truth (paging-
  system schedule, calendar feed); the workflow inherits the
  corrected slot on the next run. The framework does not introduce
  a separate rectification path.
- **Erasure (Art. 17).** The retention hooks in §5 are the
  operational erasure pathway: handoff briefs age out on the
  operator's rotation-record window, and bound escalation chains
  are rebound each run. A standalone subject-initiated erasure
  request against an active rotation is constrained by the
  operator's incident-handling-capability evidence obligation
  under §2 where Art. 6(1)(c) applies; the operator's DPO is the
  gate.
- **Objection (Art. 21).** Where the lawful basis is **Art. 6(1)(f)**
  (the primary basis in §2), a data subject can object on grounds
  relating to their particular situation. The operational handling
  is to record the objection on the rotation-governance control
  and route the slot reassignment through the operator's HR /
  roster-governance process; the workflow does not auto-suppress
  a responder from the rotation. Where the secondary
  Art. 6(1)(c) basis applies, Art. 21 does not reach the
  regulator-evidence portion of the processing.
- **Automated decision-making (Art. 22).** The rotation-handoff
  branch is a window-driven routing decision (handoff window
  true / false); the only step that produces an outbound
  side effect is the delivery of the brief to the incoming on-call,
  which is a notification, not a decision producing a legal or
  similarly significant effect on the subject. Art. 22 does not
  apply to the workflow as shipped. If an operator binds a
  classifier whose output triggers an automated adverse action
  against a responder (auto-removal from the rotation, automated
  performance-management consequence on the ack-latency snapshot),
  the operator MUST re-score this section.
