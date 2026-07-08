# GDPR data flow — cra_cvd

Per-workflow GDPR data-flow entry for the `cra_cvd` cookbook playbook
(`playbook.cra_cvd@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow, and §8 documents the outbound
personal-data transfer legs under GDPR Chapter V (Art. 44–49) for
the reporter-communication and public-advisory chain the
coordinated-vulnerability-disclosure (CVD) lifecycle runs.

Workflow source of truth:
[`content/playbooks/cra_cvd/`](../../playbooks/cra_cvd/).

Status: CORE. The seven-step CVD lifecycle now binds two of its
action steps against CORE primitives: the `ack_to_reporter` step
against
[`content.playbooks.cra_cvd.primitives.reporter.send_acknowledgement`](../../playbooks/cra_cvd/primitives/reporter.py),
which emits a deterministic CRA Article 14 §6 acknowledgement
envelope keyed on `__case_id__` with reporter contact carried on
the operator-supplied SMTP endpoint handle; and the
`publish_advisory` step against
[`content.playbooks.cra_cvd.primitives.disclosure.build_advisory_artifact`](../../playbooks/cra_cvd/primitives/disclosure.py),
which emits a CSAF 2.0-shaped advisory envelope with
`__reporter_credit_display__` rendered into the CSAF acknowledgments
block only when the reporter has consented (the literal
`reporter chose to remain anonymous` marker otherwise). The
personal-data surface those two primitives operate against —
reporter contact for the acknowledgement envelope, reporter-credit
display for the advisory — is stable across CORE and EXTEND; the
acknowledgement-letter human-readable body, the CVE-request adapter,
and the CSIRT-coordination adapter remain EXTEND scope and do not
widen the ROPA below.

---

## 1. Purpose

The workflow exists to operate the manufacturer-side coordinated
vulnerability disclosure (CVD) lifecycle a manufacturer of a product
with digital elements runs when a reporter (security researcher,
downstream operator, finder) submits a vulnerability report against
a shipped product: acknowledge the reporter within the operator CVD
policy window, triage the report, develop and validate a fix,
coordinate the public disclosure date with the reporter, and
publish the advisory. The purpose is bounded to that
triage-to-public-advisory chain and the per-case correlation record
that joins the reporter-communication and advisory-publication
milestones into a single reportable-event ledger keyed on
`__case_id__`. The workflow does not perform regulator submission
against CRA Article 14(1)–(3) — that regulator-facing chain runs in
the sibling `cra_srp_notify` playbook when the case trips the
actively-exploited or severe-incident classification — and does not
perform incident classification against NIS2 Art. 23 or GDPR
Art. 33; those are decisions made by the sibling
`incident_management` playbook when the case crosses those regimes'
thresholds.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(c) — legal obligation**. The processing
is necessary for compliance with the manufacturer's Cyber
Resilience Act Article 14 §1 duty to operate a coordinated
vulnerability disclosure policy and §6 duty to acknowledge received
reports within the policy-declared window. The lawful basis is the
CRA CVD-policy duty itself; the personal data carried inside the
acknowledgement, coordinate-disclosure, and advisory-publication
envelopes is processed only to the extent the operator CVD policy
and the public advisory template require (reporter contact for the
acknowledgement and coordinate-disclosure legs, reporter-credit
attribution on the advisory where the reporter has consented,
manufacturer sign-off contact for the CVE-request adapter).

Secondary: **GDPR Art. 6(1)(f) — legitimate interests** applies to
the third-party processors involved in the CVD chain when the
operator binds them — the case-management / evidence-pack store
that carries the correlation record across the lifecycle, the
document-signing service if the operator wires one for the
acknowledgement letter, the CVE-request adapter if the operator
binds a CVE Numbering Authority (CNA) for identifier assignment,
and the advisory-publication surface (CSAF 2.0 emitter and
operator-hosted advisory page). The operator has a legitimate
interest in operating a deterministic disclosure chain that
discharges the Annex I §2(2) and §2(5) obligations and produces
the durable receipts the CRA record-keeping obligation depends on.

Special-category data (Art. 9) is not the target of the workflow.
Reporter contact and manufacturer-role contact carry name and
work-contact attributes, not health, biometric, or other Art. 9
attributes. Where the underlying vulnerability incidentally
implicates Art. 9 categories (a health-sector product whose
vulnerability affected patient identifiers, a criminal-conviction
record incidentally touched by the vulnerability), the extraction
of that context lives in the upstream vuln_intake or
incident_management playbook and its own data-flow doc; the CVD
lifecycle here does not carry Art. 9 attributes into the reporter
communication or the public advisory beyond what the operator CVD
policy and the CSAF advisory template line-items require.

## 3. Categories of data subjects and personal data

Data subjects:

- **External reporters** (security researchers, finders,
  downstream operators, users), whose reporter-supplied contact
  channel (email address, PGP key identifier, security.txt-
  dereferenced handle) is stored on the case record as
  `__reporter_contact__` and referenced by the ack_to_reporter and
  coordinate_disclosure steps.
- **Manufacturer point-of-contact** named on the operator's public
  CVD policy and on the acknowledgement letter — typically the
  CVD-responsible party at the manufacturer, whose name, work
  email, and organisational role appear on the outbound reporter-
  facing envelopes as the operator-side signatory.
- **Manufacturer sign-off responder** paged for the coordinate-
  disclosure and publish-advisory approvals before publication,
  whose contact channel is dereferenced by the coordinate_
  disclosure step and whose page record is linked onto the
  correlation record.
- **End users of the affected product**, incidentally implicated
  through aggregate affected-user counts and affected-product
  identifiers where the triage step's severity assessment
  references user-impact estimates; per-user identifiers are NOT
  carried into the advisory.
- **CVE Numbering Authority (CNA) point-of-contact** where the
  operator binds a CNA for CVE-identifier assignment on the
  publish_advisory step, in an organisational-role capacity where
  the CNA intake template allows.

Personal data:

- Reporter contact channel (email address, PGP key id / fingerprint,
  security.txt handle) and, where the reporter opts in, name and
  organisational affiliation for reporter-credit attribution on the
  advisory.
- Manufacturer-side contact record (name, work email, role) for the
  acknowledgement-letter signatory and the coordinate-disclosure
  approver.
- CNA / coordinating-CSIRT organisational-role contact record where
  bound.
- Case correlation record: `__case_id__`, submission and receipt
  timestamps, reporter-communication timestamps, disclosure-target
  date, advisory identifier, and free-text narrative fields scoped
  to product-and-vulnerability description, severity assessment,
  and applied mitigations only.

## 4. Recipients

Recipients of the personal data the workflow emits:

- **Internal to the operator** — the case-management / evidence-
  pack store that carries the correlation record, the paging
  system that routes the manufacturer sign-off review, the
  operator's CVD-policy owner (organisational role, not
  individual) for the acknowledgement-letter signatory.
- **Downstream sibling playbooks** — the sibling
  `cra_srp_notify` playbook when the case trips the actively-
  exploited or severe-incident classification (case correlation
  record only; the reporter's contact channel is NOT forwarded to
  the SRP submission), and the sibling `incident_management` /
  `data_exfil` playbooks when the case crosses NIS2 Art. 23 or
  GDPR Art. 33 thresholds.
- **External reporter** — the acknowledgement letter and the
  coordinate-disclosure communication, carrying the operator's
  acknowledgement and the agreed disclosure date, addressed to
  the reporter's supplied contact channel.
- **Coordinating CSIRT** (where the operator or reporter engages
  one) — the coordinate-disclosure envelope carrying the case
  metadata and the agreed disclosure date.
- **CVE Numbering Authority (CNA)** — the CVE-request envelope
  emitted by the publish_advisory step where a CVE identifier is
  requested. Bound by a CNA-scoped agreement that the operator
  holds outside the framework; the workflow records the CNA the
  case was assigned to.
- **Public** — the published advisory, carrying affected products
  / versions, fix reference, and (where the reporter has
  consented to attribution) reporter-credit.

Where a processor is involved (managed evidence-pack store,
document-signing service, paging vendor), a Data Processing
Agreement (DPA) is in place under GDPR Art. 28; the agreement
itself lives outside the framework, but the data-flow doc records
the dependency.

## 5. Retention

- Case correlation record: retained for the operator's declared
  advisory-support window (typically the CRA support period of the
  affected product) so a future reporter, downstream operator, or
  regulator query against a published advisory can be answered
  from durable state. Enforced by evidence-pack expiry keyed on the
  advisory publication date plus the support-period offset.
- Reporter contact channel: retained only for the case's active
  lifecycle plus the operator's declared retention window on the
  reporter-communication log (typically the same advisory-support
  window, minimising exposure). Reporter opt-out of retention
  beyond the acknowledgement window is honoured on request under
  the erasure hook in §7.
- Reporter-credit attribution (where the reporter has consented):
  retained on the published advisory for the duration the advisory
  is publicly hosted; the consent capture record is retained on
  the case record for the same period.
- Public advisory: retained on the operator's advisory surface for
  the duration the affected product is supported plus a documented
  post-EOL archive window so downstream operators can still
  reference the advisory.

## 6. Cross-border transfers

**Default posture: no transfer.** All processing stays within the
EU/EEA when the operator runs the workflow on a sovereign-hosted
runtime with region-pinned processor endpoints. The technical
control that holds this is the SecOps-NG sovereignty-first
foundation (see `docs/FOUNDATION.md`): compile-target artifacts
default to EU-resident processor bindings and no public-cloud-AI
call is emitted on the outbound reporter-communication or
advisory-publication legs.

Two named transfer scenarios can arise depending on the operator's
bindings, both scored in §8:

- The reporter's supplied contact channel is outside the EU/EEA
  (an external reporter based in a third country). The outbound
  acknowledgement / coordinate-disclosure leg to that reporter is
  a transfer under GDPR Chapter V; §8 scores the Art. 6(1)(c)
  legal-obligation ground for the operator's disclosure-policy
  obligation and the technical control (encryption in transit,
  PGP-encrypted body where the reporter's key is available).
- The CVE Numbering Authority the operator binds is
  US-headquartered (MITRE-operated CVE program). The outbound
  CVE-request leg is a transfer under Chapter V; §8 names the
  transfer instrument (typically SCCs Module 1 under the CVE
  program's participant agreement, or the CVE program's public-
  interest posture as a coordination surface).

## 7. Data subject rights

- **Access (Art. 15)** — a reporter's Subject Access Request is
  answered from the case correlation record and the reporter-
  communication log, keyed by the reporter's contact channel; the
  operator's DPO surface routes the request to the CVD-policy
  owner. Where reporter-credit attribution has been published on
  the advisory, the advisory URL is included in the response.
- **Rectification (Art. 16)** — applicable to reporter-supplied
  contact channel and to reporter-credit attribution on the
  advisory (where the reporter requests a name change or
  correction on an already-published attribution).
- **Erasure (Art. 17)** — the retention hooks in §5 are the
  enforcement mechanism; reporter opt-out of retention beyond the
  acknowledgement window is honoured on request, subject to the
  operator's overriding CRA record-keeping obligation on the case
  correlation record for the advisory-support window. Reporter-
  credit attribution on a published advisory can be withdrawn on
  request; the withdrawal is applied on the next advisory
  revision.
- **Objection (Art. 21)** — applicable only to the
  Art. 6(1)(f)-grounded processing (processor bindings around
  case management, paging, document signing); a reporter
  cannot object to the Art. 6(1)(c)-grounded lifecycle itself
  because the operator's CRA CVD-policy duty is a legal
  obligation.
- **Automated decision-making (Art. 22)** — not applicable. The
  triage verdict is a manual assessment by the operator's
  vulnerability-response team; the workflow's routing decisions
  are deterministic against `__triage_verdict__` and
  `__actively_exploited__` but do not have legal or similarly
  significant effect on the reporter as a data subject.

## 8. Outbound personal-data transfer

Outbound legs the CVD lifecycle emits, each scored against GDPR
Chapter V:

- **ack_to_reporter → reporter** — outbound acknowledgement letter
  to the reporter's supplied contact channel. Destination class:
  external reporter. Transfer mechanism: **no transfer** by default
  (EU-resident reporter, EU-hosted mail transport); where the
  reporter is in a third country, **adequacy (Art. 45)** where the
  country has an adequacy decision, otherwise **SCCs (Art. 46)** on
  the operator's mail-transport processor plus supplementary
  measures (encryption in transit, PGP-encrypted body when the
  reporter's public key is available at intake). EU-residency
  posture: EU-hosted mail transport pinned on the operator's
  compile-target binding; a non-EU mail-transport swap breaks the
  scoring and requires re-scoring. Data minimisation: the
  acknowledgement carries `__case_id__` and the operator's CVD
  policy reference only, no case narrative.
- **coordinate_disclosure → reporter (+ coordinating CSIRT where
  bound)** — outbound coordinate-disclosure envelope. Destination
  class: external reporter + (optionally) coordinating CSIRT under
  a cooperation duty. Transfer mechanism: same posture as
  ack_to_reporter for the reporter leg; the CSIRT leg is
  EU-resident by construction (EU national CSIRTs). Data
  minimisation: the envelope carries `__case_id__`,
  `__fix_ref__`, and the agreed `__disclosure_target_date__`; the
  reporter-supplied contact is NOT forwarded to the CSIRT.
- **publish_advisory → CVE Numbering Authority (where bound)** —
  outbound CVE-request envelope. Destination class: CNA (organis-
  ational-role recipient). Transfer mechanism: **no transfer**
  where the operator binds an ENISA-affiliated EU CNA (preferred
  under the sovereignty-first posture); **SCCs (Art. 46)** where
  the operator binds the MITRE-operated US CNA program, plus
  supplementary measures (encryption in transit; the CVE program's
  intake accepts organisational-role contact only, so no per-
  reporter identifier egresses on this leg). EU-residency posture:
  the operator's compile-target binding pins the CNA choice;
  swapping to the US CNA breaks the scoring and requires re-
  scoring. Data minimisation: the CVE-request envelope carries
  product / affected-versions metadata and a coordination-point
  operator-role contact; reporter contact and reporter-credit
  attribution are NOT forwarded to the CNA on the request leg.
- **publish_advisory → public advisory surface** — outbound
  publication of the advisory (operator-hosted advisory page and
  CSAF 2.0 emission). Destination class: public. Transfer
  mechanism: not applicable — publication to the public is not a
  Chapter V transfer to a named recipient. The relevant data-
  protection surface here is data minimisation (Art. 5(1)(c)): the
  advisory carries product / affected-versions / fix / severity
  metadata, and reporter-credit attribution ONLY where the
  reporter has consented at coordinate_disclosure. Per-user
  impact figures on the advisory are aggregate counts, not
  per-user identifiers.

Cross-reference §6: the two named third-country scenarios (external
reporter outside the EU/EEA; US-bound CVE-request) are the only
outbound legs that break the `no transfer` default; both are
scored above under Chapter V, so §6 remains consistent with §8.
