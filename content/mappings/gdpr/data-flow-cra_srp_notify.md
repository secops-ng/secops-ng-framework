# GDPR data flow — cra_srp_notify

Per-workflow GDPR data-flow entry for the `cra_srp_notify` cookbook
playbook (`playbook.cra_srp_notify@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow, and §8 documents the outbound
personal-data transfer legs under GDPR Chapter V (Art. 44–49) for
the CRA Article 14 notification chain.

Workflow source of truth:
[`content/playbooks/cra_srp_notify/`](../../playbooks/cra_srp_notify/).

---

## 1. Purpose

The workflow exists to drive the Cyber Resilience Act (EU) 2024/2847
Article 14 manufacturer-reporting chain: file the 24-hour early
warning, file the 72-hour full notification, and file the final
report — 14 days after the initial early warning for an actively-
exploited vulnerability under Art. 14(2), or one month after the
initial early warning for a severe incident under Art. 14(3) — to
the manufacturer's main-establishment CSIRT through the EU Single
Reporting Platform, with simultaneous availability to ENISA per
Article 14. The purpose is bounded to that regulator-reporting
decision chain and the three submission envelopes it produces —
early-warning, full-notification, and final-report — correlated
against the upstream case identifier so a reviewer can join the
three receipts into a single reportable-event ledger. The workflow
does not perform vulnerability triage or incident classification;
those are decisions made by the upstream vuln_intake or
incident_management playbook that hands the case in. The workflow
does not retain personal data for analytics independent of the
submission envelopes, and the free-text narrative fields on the
final report are scoped to product-and-vulnerability description,
severity assessment, and applied mitigations only.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(c) — legal obligation**. The processing
is necessary for compliance with the manufacturer's Cyber Resilience
Act Article 14 reporting duty: the 24-hour early warning, the
72-hour full notification, and the final report (14 days under
Art. 14(2) for actively-exploited vulnerabilities, or one month
under Art. 14(3) for severe incidents) are mandatory submissions to
the main-establishment CSIRT through the Single Reporting Platform.
The lawful basis is the CRA reporting duty itself; the personal
data carried inside the SRP submissions is processed only to the
extent the SRP intake template requires (product identifiers,
manufacturer point-of-contact, severity, corrective-action
description).

Secondary: **GDPR Art. 6(1)(f) — legitimate interests** applies to
the third-party processors involved in the notification chain when
the operator binds them — the case-management / evidence-pack store
that carries the correlation record across the three clocks, the
document-signing service if the operator wires one for regulator-
submission signatures, and the paging system that delivers the
final-report review request to the responsible manufacturer sign-
off. The operator has a legitimate interest in operating a
deterministic notification chain across the three CRA clocks and
producing the durable receipts the regulator record-keeping
obligation depends on.

Special-category data (Art. 9) is not the target of the workflow.
The SRP submission envelopes carry product, manufacturer, and
vulnerability or incident metadata, not health, biometric, or other
Art. 9 attributes. Where an underlying incident that trips the
Art. 14(3) severe-incident clock incidentally implicated Art. 9
categories (a health-sector product whose vulnerability affected
patient identifiers, a criminal-conviction record incidentally
touched by the incident), the extraction of that context lives in
the upstream incident_management or vuln_intake playbook and its
own data-flow doc; the SRP notification chain does not carry
Art. 9 attributes into the regulator submission envelope beyond
what the SRP template line-items require.

## 3. Categories of data subjects and personal data

Data subjects:

- **Manufacturer point-of-contact** named on the SRP submission
  envelopes — typically the CRA-responsible party at the
  manufacturer, whose name, work email address, and organisational
  role appear on the early-warning, full-notification, and final-
  report envelopes as the signatory / responsible-person entry the
  SRP intake template requires.
- **Manufacturer sign-off responder** paged for the final-report
  review before submission, whose contact channel is dereferenced
  by the workflow's staging step and whose page record is linked
  onto the correlation record.
- **CSIRT and ENISA points of contact** named on the submission
  destinations, in an organisational-role capacity where the SRP
  intake template allows (competent-authority contact rather than
  individual identifier).
- **End users of the affected product**, incidentally implicated
  through aggregate affected-user counts and affected-product
  identifiers where the Art. 14(2) actively-exploited-vulnerability
  clock or the Art. 14(3) severe-incident clock trips a reporting
  obligation whose severity classification carries counts of the
  installed base or affected users. The workflow carries counts and
  category labels, not per-subject identifiers.

Categories of personal data:

- **Identifiers** — manufacturer point-of-contact name, work email
  address, organisational role; signatory names on the three
  submission envelopes.
- **Affected-user counts and category labels** — aggregate counts
  of end users of the affected product, broken out by category
  where the CRA severity classification or the cross-jurisdictional
  scope requires it; per-subject identifiers are not carried on the
  regulator-facing submission.
- **Product and vulnerability metadata** — product identifier
  (name, version, SBOM anchor), vulnerability identifier (CVE /
  GHSA / OSV where assigned), severity score, actively-exploited
  status, exploitation observables where they are non-personal
  (indicators of compromise stripped of subject identifiers).
- **Free-text narrative** — product-and-vulnerability description,
  severity assessment, and applied-mitigations text on the final-
  report envelope, authored by the manufacturer's responder, scoped
  to what the SRP template requires.
- **Correlation identifiers** — the upstream case identifier
  (`__case_id__`), the CRA clock kind (`__clock_kind__`), the
  awareness timestamp (`__awareness_ts__`), and the three
  SRP-issued submission identifiers (`__srp_early_warning_id__`,
  `__srp_full_notification_id__`, `__srp_final_report_id__`)
  persisted onto the correlation record.

## 4. Recipients

Internal recipients:

- The **upstream case owner** — the vuln_intake or
  incident_management playbook that handed the case in, whose
  correlation record inherits the three SRP submission identifiers
  once each clock's receipt lands.
- The **manufacturer sign-off responder** paged for the final-
  report review before submission.
- The **legal and compliance function** at the manufacturer that
  authorises the final-report submission and signs the envelope.
- The **metrics layer** consuming the CRA Article 14 timeliness
  KPIs (`kpi.cra_early_warning_on_time@v1`,
  `kpi.cra_notification_72h_on_time@v1`,
  `kpi.cra_final_report_on_time@v1`,
  `kpi.cra_severe_incident_on_time@v1`) — the recipient is the
  aggregated counter, not the per-submission identifier.

External / regulator recipients:

- The **manufacturer's main-establishment CSIRT** — the competent
  authority under CRA Article 14, addressed through the Single
  Reporting Platform. The SRP intake surface routes the submission
  to the main-establishment CSIRT and makes it simultaneously
  available to ENISA as Article 14 requires; both are EU-resident
  by construction.
- **ENISA**, as the simultaneous recipient of the three envelopes
  per Article 14.

External / processor recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **case-management / evidence-pack store** carrying the
  correlation record across the three clocks and the persisted
  SRP submission identifiers.
- The **document-signing service** if the operator wires one for
  regulator-submission signatures on the final-report envelope.
- The **paging / communications system** used to deliver the
  final-report review request to the manufacturer sign-off
  responder.

The CSIRT and ENISA are not data processors under GDPR Art. 28 —
they are independent controllers acting under their own statutory
mandate. The Art. 30 entry records the recipient category; the
lawful-basis analysis in §2 carries the disclosure authority. Each
operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production.

## 5. Retention

The workflow's durable artifact is the **correlation record** that
joins the three SRP submission identifiers (early warning, full
notification, final report) against the upstream case identifier,
plus the three submission envelopes as persisted on the
manufacturer's evidence-pack store. Retention is anchored on the
CRA statutory record-keeping period the manufacturer is bound by
and the operator's evidence-pack expiry:

- **In-flight submissions** — between the awareness timestamp and
  the final-report receipt, the correlation record is retained for
  the duration of the reporting cascade. The 24-hour, 72-hour, and
  14-day-or-1-month clocks are anchored on `__awareness_ts__`; the
  correlation record persists each SRP-issued identifier as its
  clock's submission lands.
- **Closed correlations** — once the final-report receipt is
  persisted on the correlation record, it ages into the
  manufacturer's post-submission retention window, which is the
  longest of (a) the CRA Article 14 record-keeping period as
  determined by the manufacturer's national implementing
  legislation, (b) the manufacturer's product-support-window
  retention for the affected product under CRA Annex I §2, and (c)
  the operator's evidence-pack expiry on the upstream case owner
  (`incident_management` or `vuln_intake`).
- **Submission envelopes** — the three envelopes as filed carry
  the same retention as the correlation record and are stored on
  the manufacturer's evidence-pack store; the SRP's own copy is
  held by the CSIRT and ENISA under their statutory record-keeping
  rules and is out of the operator's reach.

The retention boundary is enforced by the correlation-record
store's lifecycle hook plus the evidence-pack expiry rule shared
with the upstream case owner; the workflow itself is stateless
beyond the correlation record it attaches submissions to.

## 6. Cross-border transfers

**No transfer** is the default scoring. The workflow addresses
CRA-mandated destinations that are EU-resident by construction: the
manufacturer's main-establishment CSIRT is a Member-State competent
authority, ENISA is a Union agency, and the Single Reporting
Platform is the Commission-operated intake surface hosting both
recipients. The workflow is designed to execute end-to-end on the
operator's sovereign-hosted runtime (one of the EU-hostable
reference targets — n8n self-host, Temporal self-host, or LangGraph
self-host on Nebul / OVHcloud / Scaleway / Hetzner) with EU-pinned
processor endpoints for the operator-bound case-management,
document-signing, and paging dependencies.

The technical controls that hold this scoring (FOUNDATION
property #3 — sovereignty):

- The SRP address surface is Commission-operated and EU-resident;
  the framework ships no fallback endpoint that could route a
  submission outside the EU.
- The reference compile targets are framework-agnostic and run on
  the operator's own sovereign-hosted runtime; no SecOps-NG-hosted
  egress path exists in the workflow.
- The correlation record and the three submission envelopes are
  persisted on the operator's evidence-pack store under the
  operator's region pinning; no external aggregation is invoked.
- No public-cloud-AI endpoint is called during envelope
  composition; the SRP template is populated deterministically
  from the upstream case fields and the responder-authored final-
  report narrative.

Re-score gates — if an operator binds any of the following at
compile time, this scoring breaks and the operator MUST re-score
this section under "transfer under SCCs / BCRs / derogation", name
the third country and the transfer instrument, and document the
supplementary measures (encryption-at-rest with operator-held
keys, pseudonymisation of manufacturer-contact identifiers before
egress) before the binding goes live:

- A **non-EU-hosted evidence-pack store** for the correlation
  record and the three submission envelopes.
- A **non-EU document-signing service** for the final-report
  submission signature.
- A **non-EU-hosted paging vendor** for the final-report review
  page to the manufacturer sign-off responder.

Sovereignty review at compile time is the gate. The default
workflow as shipped — EU-pinned on every operator-bound endpoint —
remains scored **no transfer**.

## 7. Data subject rights

- **Access (Art. 15).** A manufacturer point-of-contact or sign-off
  responder who exercises a Subject Access Request against the
  operator can be answered by querying the correlation record on
  the case identifier and the persisted submission envelopes on
  the evidence-pack store. Where the CSIRT's or ENISA's own copy
  is also held under Article 14, the SAR against that controller
  is separate and outside the operator's reach.
- **Rectification (Art. 16).** Applicable where the correlation
  record or a submission envelope carries an attribute that is
  incorrect at submission time. Corrections after submission are
  handled through the SRP amendment procedure: Article 14 provides
  for updated reporting between the early-warning and 72-hour
  stages and between the 72-hour and final-report stages, and the
  amendment is recorded on the correlation record rather than
  overwriting the prior envelope.
- **Erasure (Art. 17) / Restriction (Art. 18) / Notification of
  rectification or erasure (Art. 19).** The retention hook in §5
  is the operational erasure pathway: the correlation record and
  the three submission envelopes age into the manufacturer's
  post-submission retention window and are purged on TTL once the
  incident is resolved and the CRA statutory record-keeping period
  closes. A standalone subject-initiated erasure or restriction
  request against an open or recently-closed correlation is
  constrained by the CRA legal-obligation basis in §2 and by the
  manufacturer's product-support-window retention obligation under
  CRA Annex I §2; the operator's DPO is the gate. Art. 19
  notifications to downstream recipients are handled through the
  same SRP amendment procedure as Art. 16 rectifications.
- **Objection (Art. 21).** The primary lawful basis in §2 is
  **Art. 6(1)(c) legal obligation**, so Art. 21 does not apply to
  the CRA-mandated submission chain itself. For the secondary
  **Art. 6(1)(f)** basis covering the operator-bound processor
  legs (case-management, document-signing, paging), a data subject
  can object on grounds relating to their particular situation;
  the operational handling is to record the objection on the
  correlation record and route the manual-review fields through
  the operator's DPO, with the overriding-legitimate-interest
  assessment as the gate.
- **Automated decision-making (Art. 22).** The severity
  classification and the CRA clock selection are performed by the
  upstream vuln_intake or incident_management playbook and handed
  in as `__clock_kind__`; this workflow's steps are deterministic
  timer waits and template-driven envelope composition, with the
  final-report submission gated by a human sign-off. The workflow
  as shipped does not produce a legal or similarly significant
  effect on a data subject in its own right, so Art. 22 does not
  apply. If an operator binds an automated classifier upstream
  whose output triggers a submission without human review, the
  applicability of Art. 22 lives in the upstream playbook's
  data-flow doc, not here.
