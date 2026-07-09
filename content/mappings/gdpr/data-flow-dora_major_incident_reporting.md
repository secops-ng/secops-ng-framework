# GDPR data flow — dora_major_incident_reporting

Per-workflow GDPR data-flow entry for the `dora_major_incident_reporting`
playbook (`playbook.dora_major_incident_reporting@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the seven
sections below form the Art. 30 Record of Processing Activity entry for
this workflow.

Workflow source of truth:
[`content/playbooks/dora_major_incident_reporting/`](../../playbooks/dora_major_incident_reporting/).

This is the DORA-flavoured cross-regime sibling of the NIS2-flavoured
`playbook.incident_management@v1` reporting lane. Where an operator
is in scope of both DORA and NIS2, the two playbooks run in parallel
on the same underlying incident against different competent-authority
chains; the per-workflow ROPA entries stay separately scoped so the
regulator-notification legs and their retention windows are auditable
per regime.

---

## 1. Purpose

The workflow exists to drive the DORA Regulation (EU) 2022/2554
Article 19 major-ICT-related-incident reporting chain for a financial
entity: submit the initial notification within 4 hours of the Article
18 major classification (and no later than 24 hours from awareness),
submit the intermediate report within 72 hours of classification (or
earlier if regular activities have recovered), and submit the final
report no later than one month after the intermediate report. The
purpose is bounded to that three-milestone regulator-notification
cycle and the four durable artifacts it produces — the Art. 18
classification-decision record and the three ITS-templated submission
envelopes — correlated against the upstream incident identifier so a
reviewer can join the four records into a single reportable-incident
ledger. The workflow does not classify incidents on its own; the
classification decision is composed by the deterministic Art. 18
classifier under Commission Delegated Regulation (EU) 2024/1772
consumed at the detect-and-classify step. The workflow does not
retain personal data for analytics independent of the submission
envelopes, and the free-text narrative fields on the final report
are scoped to the ITS final-report template (root-cause analysis,
final impact figures, remediation actions, lessons learned,
residual-risk statement).

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(c) — legal obligation**. The processing is
necessary for compliance with the operator's DORA Article 19
reporting duty: the initial notification (4h / 24h), the intermediate
report (72h), and the final report (one month after the
intermediate report) are mandatory submissions to the competent
authority (the operator's sectoral supervisor — EBA / ESMA / EIOPA
via the national competent authority) against the ITS content shape
under Commission Implementing Regulation (EU) 2024/2956. The lawful
basis is the DORA reporting duty itself; the personal data carried
inside the submission envelopes is processed only to the extent the
ITS intake template requires.

Secondary: **GDPR Art. 6(1)(f) — legitimate interests** applies to
the operator-bound processors involved in the notification chain
when the operator wires them — the case-management / evidence store
that carries the correlation record across the three clocks, the
document-signing service if the operator wires one for
regulator-submission signatures, and the paging system that delivers
the intermediate-report and final-report review requests to the
responsible sign-off responder. The operator has a legitimate
interest in operating a deterministic notification chain across the
three DORA milestones and producing the durable receipts the
regulator record-keeping obligation depends on.

Special-category data (Art. 9) is not the target of the workflow.
The ITS submission envelopes carry incident, service-impact, and
mitigation metadata, not health, biometric, or other Art. 9
attributes. Where an underlying incident on an in-scope critical or
important function incidentally implicated Art. 9 categories, the
extraction of that context lives in the upstream
`incident_management` or upstream security-workflow playbook and its
own data-flow doc; the DORA Art. 19 notification chain does not
carry Art. 9 attributes into the regulator submission envelope
beyond what the ITS template line-items require.

## 3. Categories of data subjects and personal data

Data subjects:

- **Financial-entity DORA-responsible party** named on the ITS
  submission envelopes — typically the operator's ICT
  risk-management function head or a designated DORA-signatory
  role, whose name, work email address, and organisational role
  appear on the initial, intermediate, and final envelopes as the
  signatory / responsible-person entry the ITS intake template
  requires.
- **Sign-off responder** paged for the intermediate-report and
  final-report review before submission, whose contact channel is
  dereferenced by the workflow's staging step and whose page record
  is linked onto the correlation record.
- **Competent-authority point of contact** (national competent
  authority / ESA sectoral supervisor) named on the submission
  destination, in an organisational-role capacity where the ITS
  intake allows (competent-authority contact rather than individual
  identifier).
- **Affected clients of the financial entity**, incidentally
  implicated through aggregate affected-client counts and
  affected-service identifiers where the ITS content shape requires
  reporting the impact figures on the critical or important
  functions in scope. The workflow carries counts and category
  labels on the regulator-facing submission, not per-client
  identifiers; where an underlying incident touches per-client
  identifiers, that context lives on the upstream incident
  workflow's own data-flow doc.

Categories of personal data:

- **Identifiers** — DORA-responsible party name, work email
  address, organisational role; signatory names on the three
  submission envelopes.
- **Affected-client counts and category labels** — aggregate counts
  of affected clients broken out by category where the ITS severity
  classification or the cross-border scope requires it; per-client
  identifiers are not carried on the regulator-facing submission.
- **Incident and impact metadata** — incident identifier, affected
  critical or important functions, service-duration figures,
  geographical spread indicators, indicators of compromise
  (non-personal where possible; stripped of subject identifiers
  where personal), severity assessment, mitigation actions.
- **Free-text narrative** — the ITS final-report template's root-
  cause analysis, final-impact narrative, remediation-actions
  description, lessons-learned, and residual-risk statement,
  authored by the operator's responder.
- **Correlation identifiers** — the upstream `__incident_id__`, the
  reporting-cycle window (`__reporting_window__`), the four
  workflow-emitted record identifiers (`__classification_decision_id__`,
  `__initial_notification_id__`, `__intermediate_report_id__`,
  `__final_report_id__`), and the closing `__cycle_archive_id__`.

## 4. Recipients

Internal recipients:

- The **upstream incident owner** — the incident-management or
  operational playbook that classified the incident and handed it
  in, whose correlation record inherits the four DORA-cycle record
  identifiers once each clock's receipt lands.
- The **sign-off responder** paged for the intermediate-report and
  final-report review before submission.
- The **legal and compliance function** at the operator that
  authorises the final-report submission and signs the envelope.
- The **metrics layer** consuming the DORA Article 19 timeliness
  KPIs (`kpi.dora_initial_4h_on_time@v1`,
  `kpi.dora_intermediate_72h_on_time@v1`,
  `kpi.dora_final_on_time@v1`, and the paired KRIs
  `kri.dora_initial_missed@v1`,
  `kri.regulator_notification_overrun@v1`) — the recipient is the
  aggregated counter, not the per-submission identifier.

External / regulator recipients:

- The operator's **national competent authority (NCA)**, addressed
  through the ITS submission channel. The NCA is the primary
  competent-authority recipient under DORA Article 19; the NCA
  routes aggregated reporting upward to the operator's sectoral
  **European Supervisory Authority (EBA, ESMA, or EIOPA per sector)**.
- The **cross-regime notification chains** filed in parallel on the
  same underlying incident: the NIS2 Article 23 notification chain
  where the operator is in scope of NIS2, and the GDPR Articles
  33/34 breach-notification chain where the incident involves
  personal data. Those chains are separate lanes with separate
  data-flow docs (`data-flow-incident_management.md` for the NIS2
  lane; the breach-notification cluster docs for the GDPR lane);
  the DORA lane records the parallel-lane relationship in its
  archival record but does not itself compose the NIS2 or GDPR
  envelopes.

External / processor recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **case-management / evidence store** carrying the
  correlation record across the three DORA milestones and the
  persisted submission identifiers.
- The **document-signing service** if the operator wires one for
  regulator-submission signatures on the final-report envelope.
- The **paging / communications system** used to deliver the
  intermediate-report and final-report review requests to the
  sign-off responder.

The NCA, ESA, and any cross-regime authority chain (NIS2 CSIRT,
GDPR supervisory authority) are not data processors under GDPR
Art. 28 — they are independent controllers acting under their own
statutory mandate. The Art. 30 entry records the recipient
category; the lawful-basis analysis in §2 carries the disclosure
authority. Each operator-bound processor MUST have a Data
Processing Agreement (GDPR Art. 28) in place before the binding is
wired in production.

## 5. Retention

The workflow's durable artifacts are the **correlation record**
that joins the classification-decision record and the three
submission-envelope identifiers against the upstream incident
identifier, plus the four submission artifacts as persisted on the
operator's evidence store. Retention is anchored on the DORA
statutory record-keeping period and the operator's evidence-pack
expiry:

- **In-flight cycle** — between the awareness timestamp and the
  final-report receipt, the correlation record is retained for the
  duration of the reporting cascade. The 4h / 24h, 72h, and
  one-month clocks are anchored on the awareness timestamp and the
  Article 18 classification timestamp; the correlation record
  persists each submission identifier as its clock's submission
  lands.
- **Closed cycles** — once the final-report receipt is persisted
  on the correlation record and the close-and-archive step emits
  the dated cycle-archival record, the correlation ages into the
  operator's post-submission retention window, which is the
  longest of (a) the DORA Article 19 record-keeping period as
  determined by the operator's national implementing legislation
  and the ESA guidance in force, (b) the operator's evidence-pack
  expiry on the upstream incident owner
  (`playbook.incident_management@v1`), and (c) the retention
  requirements the operator's national competent authority imposes
  for post-incident audit.
- **Submission envelopes** — the three envelopes as filed carry
  the same retention as the correlation record and are stored on
  the operator's evidence store; the competent authority's own
  copy is held by the NCA / ESA under their statutory
  record-keeping rules and is out of the operator's reach.

The retention boundary is enforced by the correlation-record
store's lifecycle hook plus the evidence-pack expiry rule shared
with the upstream incident owner; the workflow itself is
stateless beyond the correlation record it attaches submissions
to.

## 6. Cross-border transfers

**No transfer** is the default scoring. The workflow addresses
DORA-mandated destinations that are EU-resident by construction:
the operator's national competent authority is a Member-State
supervisor, and the three European Supervisory Authorities (EBA,
ESMA, EIOPA) are Union agencies. The ITS submission channel per
Commission Implementing Regulation (EU) 2024/2956 is operated by
the NCA / ESA chain within the EU. The workflow is designed to
execute end-to-end on the operator's sovereign-hosted runtime (one
of the EU-hostable reference targets — n8n self-host, Temporal
self-host, or LangGraph self-host on Nebul / OVHcloud / Scaleway
/ Hetzner) with EU-pinned processor endpoints for the
operator-bound case-management, document-signing, and paging
dependencies.

The technical controls that hold this scoring (FOUNDATION
property #3 — sovereignty):

- The competent-authority submission channel is NCA-operated and
  EU-resident by regulation; the framework ships no fallback
  endpoint that could route a submission outside the EU.
- The reference compile targets are framework-agnostic and run on
  the operator's own sovereign-hosted runtime; no SecOps-NG-hosted
  egress path exists in the workflow.
- The correlation record and the four submission artifacts are
  persisted on the operator's evidence store under the operator's
  region pinning; no external aggregation is invoked.
- No public-cloud-AI endpoint is called during envelope
  composition; the ITS templates are populated deterministically
  from the upstream incident fields and the responder-authored
  final-report narrative.

Re-score gates — if an operator binds any of the following at
compile time, this scoring breaks and the operator MUST re-score
this section under "transfer under SCCs / BCRs / derogation",
name the third country and the transfer instrument, and document
the supplementary measures (encryption-at-rest with operator-held
keys, pseudonymisation of responder-contact identifiers before
egress) before the binding goes live:

- A **non-EU-hosted evidence store** for the correlation record
  and the four submission artifacts.
- A **non-EU document-signing service** for the final-report
  submission signature.
- A **non-EU-hosted paging vendor** for the review-page delivery
  to the intermediate-report and final-report sign-off responders.

Sovereignty review at compile time is the gate. The default
workflow as shipped — EU-pinned on every operator-bound endpoint
— remains scored **no transfer**.

## 7. Data subject rights

- **Access (Art. 15).** A DORA-responsible party or sign-off
  responder who exercises a Subject Access Request against the
  operator can be answered by querying the correlation record on
  the incident identifier and the persisted submission envelopes
  on the evidence store. Where the NCA's or ESA's own copy is
  also held under Article 19, the SAR against that controller is
  separate and outside the operator's reach.
- **Rectification (Art. 16).** Applicable where the correlation
  record or a submission envelope carries an attribute that is
  incorrect at submission time. Corrections after submission are
  handled through the ITS amendment procedure the NCA supports;
  the amendment is recorded on the correlation record rather than
  overwriting the prior envelope.
- **Erasure (Art. 17) / Restriction (Art. 18) / Notification of
  rectification or erasure (Art. 19).** The retention hook in §5
  is the operational erasure pathway: the correlation record and
  the four submission artifacts age into the operator's
  post-submission retention window and are purged on TTL once the
  DORA statutory record-keeping period closes. A standalone
  subject-initiated erasure or restriction request against an
  open or recently-closed correlation is constrained by the DORA
  legal-obligation basis in §2; the operator's DPO is the gate.
  Art. 19 notifications to downstream recipients are handled
  through the same ITS amendment procedure as Art. 16
  rectifications.
- **Objection (Art. 21).** The primary lawful basis in §2 is
  **Art. 6(1)(c) legal obligation**, so Art. 21 does not apply to
  the DORA-mandated submission chain itself. For the secondary
  **Art. 6(1)(f)** basis covering the operator-bound processor
  legs (case-management, document-signing, paging), a data
  subject can object on grounds relating to their particular
  situation; the operational handling is to record the objection
  on the correlation record and route the manual-review fields
  through the operator's DPO, with the overriding-legitimate-
  interest assessment as the gate.
- **Automated decision-making (Art. 22).** The Article 18
  classification decision that gates entry into the reporting
  cycle is composed by the deterministic Art. 18 classifier under
  Commission Delegated Regulation (EU) 2024/1772; the classifier
  is a rules-driven activity that reads the seven primary criteria
  and applies the materiality thresholds. This workflow's steps
  are deterministic ITS-template composition plus timer waits,
  with the intermediate-report and final-report submissions gated
  by human sign-off. The workflow as shipped does not produce a
  legal or similarly significant effect on a data subject in its
  own right, so Art. 22 does not apply. If an operator binds an
  automated classifier upstream whose output triggers a
  submission without human review, the applicability of Art. 22
  lives in the upstream playbook's data-flow doc, not here.
