# GDPR data flow — incident-management

Per-workflow GDPR data-flow entry for the `incident-management`
cookbook playbook (`playbook.incident_management@v1`). Filled in
against [`_data-flow-template.md`](./_data-flow-template.md). Together
the seven sections below form the Art. 30 Record of Processing
Activity entry for this workflow.

Workflow source of truth:
[`content/playbooks/incident-management/`](../../playbooks/incident-management/).

---

## 1. Purpose

The workflow exists to drive a significant security incident through
the NIS2 Article 23 three-stage regulator timeline: intake the
originating signal, classify significance and cross-border scope,
open a deterministic incident timeline, submit the 24-hour early
warning, submit the 72-hour notification, submit the one-month final
report, and close the timeline so the regulator-shaped JSON artefact
is persisted as durable evidence. The purpose is bounded to that
regulator-reporting decision chain and the case-record it produces —
the workflow does not retain incident telemetry for analytics
independent of the case, and the free-text fields on the final report
are scoped to narrative, root cause, and applied mitigations only.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(c) — legal obligation**. The processing is
necessary for compliance with the operator's NIS2 Article 23 incident-
notification obligation as transposed nationally, and (where the
operator is in scope) the parallel reporting obligations under DORA
Article 19 and CRA Article 14. The lawful basis is the regulatory
duty itself; the personal data carried inside the regulator
submissions is processed only to the extent the regulator's template
requires.

Secondary: **GDPR Art. 6(1)(f) — legitimate interests** applies to the
internal incident-handling portion of the workflow that is not strictly
mandated by the regulator template (analyst notes, internal routing,
post-incident review hooks). The operator has a legitimate interest in
defending the organisation and learning from the incident, and the
data subjects have a reasonable expectation that incidents crossing
their identifiers will be subject to the operator's incident-handling
capability.

Special-category data (Art. 9) is not the target of the workflow but
may be incidentally observed inside intake signals (for example, a
healthcare operator whose incident touches patient identifiers). The
workflow does not extract or persist Art. 9 attributes independently
of the incident-case retention in §5, and the operator's significance
classification at intake is where any Art. 9 exposure is flagged.

## 3. Categories of data subjects and personal data

Data subjects:

- **Employees of the operator** named in the originating signal as
  affected accounts, on-call responders, incident commanders, or
  signatories on the regulator submissions.
- **Customers, citizens, or other end users** of the operator's
  services whose identifiers may appear in the incident's affected-
  subjects count or in the cross-border-scope classification.
- **Third parties** (suppliers, processors, peer operators) named in
  the incident timeline when the incident touches a shared
  dependency.
- **Regulator points of contact** named on the submission
  destinations (organisational role, not individual identifier
  where the regulator template allows).

Categories of personal data:

- **Identifiers** — work email addresses, employee identifiers,
  signatory names on the early-warning / 72-hour / final-report
  submissions.
- **Affected-subject counts and categories** — aggregate counts of
  end users impacted, broken out by category where the significance
  classification or the cross-border scope requires it; the
  workflow handles counts and category labels, not per-subject
  identifiers, on the regulator-facing submissions.
- **Incident telemetry** — log excerpts, OCSF Finding (2001) and
  Incident Finding (2005) records, evidence-pack artefacts attached
  to the case.
- **Free-text narrative** — the final-report fields scoped to
  narrative, root cause, and applied mitigations, as authored by
  the responder (DSPy-shaped only where the playbook's signature
  permits, never auto-extracted personal data).

## 4. Recipients

Internal recipients:

- The **incident commander** and the **response team** for the
  branch the significance classification routes onto.
- The **legal and compliance function** that signs off on the
  regulator submissions.
- The **post-incident review** workflow which inherits the case at
  closure.
- The **metrics layer** consuming the NIS2 Article 23 timeliness
  KPIs (`kpi.nis2_early_warning_on_time@v1`,
  `kpi.nis2_notification_72h_on_time@v1`,
  `kpi.nis2_final_report_on_time@v1`) — the recipient is the
  aggregated counter, not the per-incident identifier.

External / regulator recipients:

- The **regulator destination** the operator has configured for the
  early warning, the 72-hour notification, and the one-month final
  report. The destination is operator-supplied through playbook
  variables — the framework ships no default endpoint, on
  sovereignty-stack grounds — and is one or more of the
  operator's competent authorities under NIS2 (national CSIRT,
  sectoral regulator) and any parallel destinations required by
  DORA Article 19 or CRA Article 14 for in-scope operators.
- **Affected operators or processors** named in the incident, where
  the incident's cross-border or supply-chain scope requires
  notification of the dependency.

The regulator destinations are not data processors under GDPR
Art. 28 — they are independent controllers acting under their own
statutory mandate. The Art. 30 entry records the recipient
category; the lawful-basis analysis in §2 carries the disclosure
authority.

## 5. Retention

The workflow's durable artefact is the **incident case** and its
attached regulator-submission JSON envelopes (early warning, 72-hour
notification, one-month final report). Retention is the parent
incident case's lifetime plus the operator's evidence-pack expiry:

- **Open incidents** are retained for the duration the case is
  open. The deterministic incident-timeline binding (F-PT-02)
  carries the immutable submission timestamps.
- **Closed incidents** age into the operator's post-incident
  retention window — typically the longest of (a) the regulator's
  statutory record-keeping period for the standard the submission
  was filed under (NIS2 Art. 23, DORA Art. 19, CRA Art. 14), (b)
  the operator's litigation-hold policy, and (c) the post-incident
  review workflow's evidence-pack expiry. The operator configures
  the binding; the framework does not pick a default.
- **Telemetry records** emitted onto the OCSF store during the
  incident follow the operator's telemetry retention policy on the
  underlying store, independent of the case's lifetime.

The retention boundary is enforced by the incident-case store's
lifecycle hook plus the OCSF store's policy; the workflow itself is
stateless beyond the case it attaches submissions to.

## 6. Cross-border transfers

**No transfer** is the default scoring. The workflow is designed to
execute end-to-end on the operator's sovereign-hosted runtime (one of
the EU-hostable reference targets — n8n self-host, Temporal self-host,
or LangGraph self-host on Nebul / OVHcloud / Scaleway / Hetzner) with
EU-pinned regulator-destination endpoints (national CSIRT portals and
sectoral-regulator submission gateways are EU-resident by
construction).

The technical controls that hold this scoring:

- The reference compile targets are framework-agnostic and run on
  the operator's own sovereign-hosted runtime; no SecOps-NG-hosted
  egress path exists in the workflow.
- The regulator destinations are operator-supplied through playbook
  variables; the framework ships no default endpoint and no
  fallback that could route a submission outside the EU.
- The deterministic incident-timeline binding (F-PT-02) is a thin
  in-package adapter that executes locally against the operator's
  store; no external aggregation is invoked.

The cross-border-scope classification step inside the workflow is a
separate concern from the GDPR Chapter V transfer question — it
scores whether the **incident's reach** crosses Member-State borders
for the NIS2 Article 23 cross-border-cooperation clause, not whether
personal data leaves the EU. The two scorings can disagree (an
incident with cross-border reach can still be processed end-to-end
inside the EU), and this section evaluates only the GDPR transfer
question.

If an operator binds a non-EU evidence-pack store, a non-EU document-
signing service for the final-report submission, or any external AI
classifier on the narrative fields, this scoring breaks — the
operator MUST re-score this section under "transfer under SCCs /
BCRs / derogation" and document the supplementary measures
(encryption-at-rest with operator-held keys, pseudonymisation of
affected-subject identifiers before egress) before the binding goes
live. Sovereignty review at compile time is the gate.

## 7. Data subject rights

- **Access (Art. 15).** A subject who exercises a SAR against the
  operator can be answered by querying the incident-case store on
  the subject's identifiers from §3. The regulator-submission
  envelopes (early warning, 72-hour notification, final report)
  are part of the case record and are searchable as such. Where
  the regulator's own copy is also held (NIS2 competent authority,
  DORA / CRA equivalent), the SAR against that controller is
  separate and outside the operator's reach.
- **Rectification (Art. 16).** Applicable where the case record or
  a regulator-submission envelope carries an attribute that is
  incorrect at submission time. Corrections after submission are
  handled through the regulator's amendment procedure (NIS2 Art.
  23 allows updated reporting between the stages) and are recorded
  on the incident timeline rather than overwriting the prior
  envelope.
- **Erasure (Art. 17).** The retention hook in §5 is the
  operational erasure pathway: the case ages into the operator's
  post-incident retention window and is purged on TTL. A standalone
  subject-initiated erasure request against an open or recently-
  closed incident is constrained by the regulatory record-keeping
  obligation in §2 and by litigation-hold; the operator's DPO is
  the gate.
- **Objection (Art. 21).** Where the lawful basis is **Art. 6(1)(c)
  legal obligation** (the primary basis in §2), Art. 21 does not
  apply to that part of the processing. For the secondary
  **Art. 6(1)(f)** basis covering internal incident handling
  beyond the regulator template, a data subject can object on
  grounds relating to their particular situation; the operational
  handling is to record the objection on the case and route the
  manual-review fields through the operator's DPO, with the
  overriding-legitimate-interest assessment as the gate.
- **Automated decision-making (Art. 22).** The significance
  classification and cross-border-scope classification at intake
  are routing decisions that hand off to a human-owned incident
  commander; the regulator-submission free-text fields are
  authored by the responder, not generated end-to-end. The
  workflow as shipped does not produce a legal or similarly
  significant effect on a data subject in its own right, so Art. 22
  does not apply. If an operator binds an external classifier whose
  output triggers an automated adverse action against a subject
  named in the incident (account lockout, automated regulator
  filing without human review), the operator MUST re-score this
  section.
