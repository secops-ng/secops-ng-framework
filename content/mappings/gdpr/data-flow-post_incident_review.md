# GDPR data flow — post_incident_review

Per-workflow GDPR data-flow entry for the `post_incident_review`
cookbook playbook (`playbook.post_incident_review@v1`). Filled in
against [`_data-flow-template.md`](./_data-flow-template.md). Together
the seven sections below form the Art. 30 Record of Processing
Activity entry for this workflow.

Workflow source of truth:
[`content/playbooks/post_incident_review/`](../../playbooks/post_incident_review/).

---

## 1. Purpose

The workflow exists to formalise learning after an incident has been
closed or contained: collate a chronological timeline of the incident
from the artifacts the responders left behind (ticket comments,
chat transcripts, EDR / SIEM exports, network captures, evidence
packages), flag gaps in the evidence record where anti-forensics
signals were observed (cleared eventlogs, disabled audit policy,
timestomped files), walk a blameless review template that separates
contributing factors from individual error, and emit a corrective-
action register with owner, due-date, and verification clause per
entry. The purpose is bounded to that learning-and-tracking decision
and the metric hooks it produces (`kpi.timeline_completeness@v1`,
`kpi.review_completion_sla@v1`, `kpi.corrective_action_close_rate@v1`,
`kri.corrective_action_overdue@v1`); the workflow does not re-litigate
the incident, does not extract per-subject behavioural profiles from
the timeline, and does not retain responder communication content
beyond the timeline artifact and the review document.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(c) — legal obligation**. The processing is
necessary for compliance with the operator's incident-handling-and-
learning obligations under **NIS2 Art. 21(2)(b)** (incident-handling
capability) and, where the operator is in scope, **DORA Art. 6** (ICT
risk-management framework, learning from incidents) and **CRA
Art. 14** (incident-handling-and-reporting obligations) as transposed
nationally. The retained timeline, review document, and corrective-
action register are the evidence the operator presents to demonstrate
the learning obligation has been discharged.

Where the closed incident was a confirmed personal-data breach, the
same three artefacts materialise the operator's **GDPR Art. 33(5)**
obligation to "document any personal-data breaches, comprising the
facts relating to the personal-data breach, its effects and the
remedial action taken" — the timeline records the facts and effects,
the blameless review document records the contributing-factor
analysis, and the corrective-action register records the remedial
action with owner, due-date, and verification clause. The workflow
does not itself decide whether a closed incident was a personal-data
breach (the parent incident-management workflow carries the
Art. 33(1) notifiability decision); it produces the Art. 33(5)
documentation record for cases where that decision was positive.

Secondary: **GDPR Art. 6(1)(f) — legitimate interests** applies to
the internal blameless-review portion of the workflow that is not
strictly mandated by the regulator template — capturing contributing
factors, training and tooling gaps, and the operator's own learning
record. The operator has a legitimate interest in improving its
incident-response capability, and the data subjects (responders,
affected employees, third parties named in the timeline) have a
reasonable expectation that incidents are reviewed under the
operator's incident-handling capability.

Special-category data (Art. 9) is not the target of the workflow but
may be incidentally observed inside the parent incident's timeline
(for example, a healthcare operator's incident touching patient
identifiers, or an employment-context incident touching union or
health attributes carried into the responders' narrative). The
workflow does not extract or persist Art. 9 attributes independently
of the parent incident-case retention in §5, and the blameless-
review template treats Art. 9 exposure as an evidence-handling flag
the operator's DPO reviews before the review document is closed.

## 3. Categories of data subjects and personal data

Data subjects:

- **Employees of the operator** acting as responders, incident
  commanders, or signatories on the parent incident — named in the
  timeline as authors of ticket comments, chat messages, and
  evidence-package attributions.
- **Employees of the operator** named in the timeline as affected
  accounts, change owners, or decision authorities during the
  incident.
- **Customers, citizens, or other end users** of the operator's
  services whose identifiers may appear in the timeline's incident
  scope or in the corrective-action register where an action
  references a subject-specific remediation.
- **Third parties** (suppliers, processors, peer operators) named
  in the timeline when the incident touched a shared dependency.

Categories of personal data:

- **Identifiers** — work email addresses, employee identifiers,
  ticket-comment author names, chat-handle attributions, signatory
  names on the review document and the corrective-action register.
- **Narrative attributions** — responder-authored ticket comments,
  chat-transcript excerpts, evidence-package summaries; persisted
  as the timeline artifact's narrative layer rather than re-
  authored.
- **Incident telemetry projections** — OCSF Incident Finding
  (2005), Process Activity (1007), File Activity (1001), and
  Authentication (3002) records carried into the timeline
  collation step.
- **Anti-forensics flags** — boolean and per-rule references
  recording that the timeline collation step detected one of the
  upstream SigmaHQ rules enumerated in the playbook's
  `external_references` (cleared eventlogs, audit policy disabled,
  timestomp). The flag itself is metadata; any subject identifier
  bound to it is inherited from the parent incident.
- **Corrective-action attributions** — owner identifier, due-date,
  and verification-clause text per register entry.

## 4. Recipients

Internal recipients:

- The **incident commander** and the **response team** that owned
  the parent incident — primary recipients of the review document
  for sign-off.
- The **legal and compliance function** that signs off on the
  corrective-action register and on the evidence-handling treatment
  of any Art. 9 exposure flagged during the review.
- The **change / ticketing system** that owns execution and
  verification of each corrective-action entry — recipient of the
  register, not the underlying timeline.
- The **metrics layer** consuming `kpi.timeline_completeness@v1`,
  `kpi.review_completion_sla@v1`, `kpi.corrective_action_close_rate@v1`,
  and `kri.corrective_action_overdue@v1` — recipient is the
  aggregated counter, not the per-incident identifier.
- The **control-effectiveness rollup** (the
  `control.blameless_review@v1` and
  `control.corrective_action_register@v1` controls) feeding the
  operator's executive_metrics rollup.

External / processor recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **review-document store** holding the blameless-review
  artifact (operator's GRC tool, document store, or wiki).
- The **corrective-action register store** holding the register
  entry (typically the operator's existing change / ticketing
  system).

The review-document store and the corrective-action register store
are operator-bound processors under GDPR Art. 28; each MUST have a
Data Processing Agreement in place before the binding is wired in
production. The framework does not ship the DPAs, but the data-flow
record names the dependency so a sovereignty review can verify it.

## 5. Retention

The workflow's durable artefacts are the **timeline artifact**
(`__timeline_artifact__`), the **review document**
(`__review_artifact__`), and the **corrective-action register
entry** (`__corrective_action_register__`). Retention is the parent
incident case's lifetime plus the operator's evidence-pack expiry:

- **Open corrective-action register entries** are retained for the
  duration the action is open — until the operator's change /
  ticketing system records execution and verification.
- **Closed corrective-action register entries** age into the
  operator's post-incident retention window — typically the
  longest of (a) the regulator's statutory record-keeping period
  for the standard the parent incident was filed under (NIS2
  Art. 23, DORA Art. 19, CRA Art. 14), (b) the operator's
  litigation-hold policy, and (c) the operator's evidence-pack
  expiry on the parent incident_management playbook. The operator
  configures the binding; the framework does not pick a default.
- **Timeline artifacts and review documents** inherit the parent
  incident case's retention. They are not standalone records;
  closing the parent incident case ages them under the same TTL.
- **OCSF telemetry projections** emitted into the timeline follow
  the operator's telemetry retention policy on the underlying
  OCSF store, independent of the parent case's lifetime.

The retention boundary is enforced by the review-document store's
lifecycle hook, the corrective-action register store's lifecycle
hook, and the OCSF store's policy; the workflow itself is stateless
beyond the artifacts it produces against the parent case.

## 6. Cross-border transfers

**No transfer** is the default scoring. The workflow is designed to
execute end-to-end on the operator's sovereign-hosted runtime (one of
the EU-hostable reference targets — n8n self-host, Temporal self-host,
or LangGraph self-host on Nebul / OVHcloud / Scaleway / Hetzner) with
EU-resident review-document and corrective-action register stores
inherited from the operator's existing GRC and change-management
stack.

The technical controls that hold this scoring:

- The reference compile targets are framework-agnostic and run on
  the operator's own sovereign-hosted runtime; no SecOps-NG-hosted
  egress path exists in the workflow.
- The review-document store and the corrective-action register
  store are operator-supplied through compile-target binding; the
  framework ships no default endpoint and no fallback that could
  route an artifact outside the EU.
- The timeline collation step reads from artifact sources already
  resident on the operator's incident-case store; no external
  aggregation is invoked.
- The blameless-review template walk is human-authored against the
  collated timeline; no external AI classifier is called.

If an operator binds a non-EU review-document store, a non-EU
corrective-action register, a non-EU evidence-source connector for
the timeline collation step, or any external AI classifier on the
review-narrative fields, this scoring breaks — the operator MUST
re-score this section under "transfer under SCCs / BCRs /
derogation" and document the supplementary measures (encryption-at-
rest with operator-held keys, pseudonymisation of responder and
affected-subject identifiers before egress) before the binding goes
live. Sovereignty review at compile time is the gate.

## 7. Data subject rights

- **Access (Art. 15).** A subject who exercises a SAR against the
  operator can be answered by querying the timeline artifact, the
  review document, and the corrective-action register on the
  subject's identifiers from §3. Each artifact is searchable on
  the parent incident case's identifier; the workflow does not
  introduce a storage location beyond the artifact stores named
  in §4.
- **Rectification (Art. 16).** Applicable where the timeline
  artifact or the review document carries an attribute that is
  incorrect at the time of the review. Corrections to the
  responder-authored narrative are handled through the review
  document's amendment procedure and recorded on the timeline
  rather than overwriting the prior version — the immutability of
  the timeline is part of the evidence value the regulator
  obligations in §2 rely on.
- **Erasure (Art. 17).** The retention hook in §5 is the
  operational erasure pathway: the artifacts age into the
  operator's post-incident retention window and are purged on
  TTL. A standalone subject-initiated erasure request against an
  open or recently-closed review is constrained by the regulatory
  record-keeping obligation in §2 and by litigation-hold; the
  operator's DPO is the gate.
- **Objection (Art. 21).** Where the lawful basis is
  **Art. 6(1)(c) legal obligation** (the primary basis in §2),
  Art. 21 does not apply to the regulator-evidence portion of the
  processing. For the secondary **Art. 6(1)(f)** basis covering
  the internal blameless-review portion, a data subject can
  object on grounds relating to their particular situation; the
  operational handling is to record the objection on the review
  document, route the affected sections through the operator's
  DPO, and rely on the overriding-legitimate-interest assessment
  for incidents whose learning value depends on the disputed
  section.
- **Automated decision-making (Art. 22).** The blameless-review
  template walk and the corrective-action extraction are human-
  authored steps that hand off to a human-owned change /
  ticketing system; no automated decision producing legal or
  similarly significant effects on a data subject is taken by
  the workflow as shipped. Art. 22 does not apply. If an operator
  binds a classifier whose output triggers an automated adverse
  action against a responder named in the timeline (automated
  performance-management consequence, automated suspension from
  the rotation, automated regulator-facing attribution), the
  operator MUST re-score this section.
