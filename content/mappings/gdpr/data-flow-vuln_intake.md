# GDPR data flow — vuln_intake

Per-workflow GDPR data-flow entry for the `vuln_intake` cookbook
playbook (`playbook.vuln_intake@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/vuln_intake/`](../../playbooks/vuln_intake/).

---

## 1. Purpose

The workflow exists to receive an inbound coordinated vulnerability
disclosure (researcher report, vendor advisory, CVE feed hit, or
internal scan finding), acknowledge the reporter against the CRA
single-point-of-contact obligation, correlate the affected component
against the operator's SBOM and asset inventory, score the case with
CVSS and EPSS, assess whether the disclosure trips the CRA Article 14
actively-exploited or severe-incident reporting clock, fire the CRA
regulator-notification chain when it does, and route the case to a
per-severity response branch (patch and advisory dissemination,
scheduled remediation, or accept-risk). The purpose is bounded to
that disclosure-handling decision chain and the case record it
produces — the workflow does not retain reporter identifiers beyond
what the CRA acknowledgement and the case record require.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(c) — legal obligation**. The processing is
necessary for compliance with the operator's CRA Annex I §2(5)
coordinated-vulnerability-disclosure-policy obligation, the CRA
Annex I §2(1) SBOM obligation, the CRA Annex I §2(7) security-update
dissemination duty, and the CRA Article 14 regulator-notification
chain. The lawful basis is the regulatory duty itself; the personal
data carried inside the acknowledgement to the reporter and the
regulator submissions is processed only to the extent the regulator
template and the disclosure policy require.

Secondary: **GDPR Art. 6(1)(f) — legitimate interests** applies to
the internal triage, asset-correlation, and response portions of the
workflow that go beyond the strict CRA-template scope. The operator
has a legitimate interest in defending the organisation and its
downstream users against an exploitable vulnerability, and the data
subjects (the reporter, named maintainers in the SBOM, named contacts
on the asset inventory) have a reasonable expectation that a
disclosure crossing the operator's intake will be triaged and
remediated.

A separate optional basis arises if the reporter explicitly
consents (Art. 6(1)(a)) to public attribution in the advisory the
response branch disseminates — the consent is captured on the case
and is independent of the primary basis above.

Special-category data (Art. 9) is not the target of the workflow and
is not expected on a typical disclosure intake. If a disclosure
incidentally carries Art. 9 attributes (for example, a vulnerability
report whose proof-of-concept involves health-record data), the
operator's DPO is the escalation route at the intake step.

## 3. Categories of data subjects and personal data

Data subjects:

- **The reporter** (researcher, external user, vendor contact, or
  internal scanner operator) whose contact details accompany the
  inbound disclosure.
- **Named maintainers** in the SBOM entries the affected-component
  correlation step lands on.
- **Named contacts** on the asset-inventory entries the correlation
  step lands on (asset owner, business owner).
- **Employees of the operator** named as the disclosure handler,
  the response-branch owner, or the signatory on the CRA
  regulator-notification chain submissions.
- **Downstream users of the affected component** whose aggregate
  counts may appear in the CRA Article 14 actively-exploited or
  severe-incident scoring; the workflow handles counts and
  category labels, not per-user identifiers, on the regulator-
  facing submissions.

Categories of personal data:

- **Identifiers** — reporter name, reporter email address or
  pseudonymous handle, work email addresses of named maintainers
  and asset contacts, signatory names on the regulator
  submissions.
- **Disclosure metadata** — title, summary, affected-component
  identifier, CVSS vector and score, EPSS percentile, OCSF
  Vulnerability Finding (2002) records.
- **Free-text narrative** — the disclosure body, proof-of-concept
  description, and remediation guidance as authored by the
  reporter or the response branch.
- **Acknowledgement and advisory artefacts** — the acknowledgement
  message sent back to the reporter under CRA Annex I §2(5), and
  any public advisory the response branch disseminates under CRA
  Annex I §2(7) (the public advisory is subject to a separate
  publication policy and is the operator's controller decision).

The workflow processes the disclosure envelope plus the
correlation and scoring projections; it does not pull underlying
proof-of-concept artefacts (exploit code, captured payloads) into
its own state — those stay on the operator's evidence store and are
referenced by identifier.

## 4. Recipients

Internal recipients:

- The **disclosure handler** acknowledging the reporter under the
  CRA single-point-of-contact obligation.
- The **response-branch owner** for the disposition the per-
  severity switch routes onto (critical patch and advisory, high
  patch and advisory, scheduled remediation, accept-risk).
- The **incident commander** of the parallel incident_management
  workflow, when the CRA Article 14 assessment trips the clock and
  hands off to the regulator-notification chain documented in
  [data-flow-incident_management.md](./data-flow-incident_management.md).
- The **metrics layer** consuming `kpi.vuln_disclosure_sla@v1`,
  `kri.cvd_intake_aging@v1`, `kri.releases_without_sbom@v1`, the
  CRA Article 14 timeliness KPIs
  (`kpi.cra_early_warning_on_time@v1`,
  `kpi.cra_notification_72h_on_time@v1`,
  `kpi.cra_final_report_on_time@v1`,
  `kpi.cra_severe_incident_on_time@v1`),
  `kpi.patch_disseminated_on_time@v1`, and `kpi.mttr_critical@v1`
  — recipient is the aggregated counter, not the per-case
  identifier.

External / regulator recipients:

- The **reporter**, as the destination of the CRA acknowledgement
  and (if separately consented) any updates on the disclosure's
  remediation trajectory.
- The **regulator destination** the operator has configured for the
  CRA Article 14 early warning, the 72-hour notification, and the
  one-month final report on the actively-exploited or severe-
  incident clock. As with the incident_management workflow, the
  destination is operator-supplied through playbook variables —
  the framework ships no default endpoint.
- The **downstream user population** of the affected component, as
  the destination of the public advisory the response branch
  disseminates under CRA Annex I §2(7). The advisory is published
  under the operator's separate publication policy and is the
  operator's own controller decision; the framework records the
  recipient category here for completeness.

External processor recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **CVE feed** providing the CVE-hit source shape (NVD mirror
  or sovereign equivalent).
- The **EPSS provider** invoked during the scoring step.
- The **SBOM store** the correlation step queries.

Each operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production
where the processor handles personal data on the operator's behalf;
where the feed is a one-way public source (NVD mirror, EPSS API
operated on a non-personal-data basis) the Art. 28 relationship is
not engaged. The data-flow record names the dependency so a
sovereignty review can verify it.

## 5. Retention

The workflow's durable artefact is the **disclosure case** and its
attached scoring, correlation, acknowledgement, and (where fired)
CRA regulator-submission envelopes:

- **Open disclosures** are retained for the duration the case is
  open through to remediation, dissemination, or accept-risk
  closure.
- **Closed disclosures** age into the operator's CVD record-
  retention window — typically the longest of (a) the regulator's
  statutory record-keeping period for any CRA Article 14
  submission filed on the case, (b) the operator's litigation-hold
  policy, (c) the operator's coordinated-vulnerability-disclosure
  policy retention horizon (commonly aligned with the affected
  component's support lifetime so the advisory remains
  discoverable), and (d) the post-incident review workflow's
  evidence-pack expiry when an incident_management chain ran in
  parallel. The operator configures the binding; the framework
  does not pick a default.
- **Reporter contact details** are retained on the case for the
  duration the operator's CVD policy requires the relationship be
  maintained (typically through to dissemination plus a
  reasonable follow-up window) and are then minimised on the case
  record. Where the reporter requested pseudonymity at intake the
  case carries the handle only.
- **OCSF Vulnerability Finding records** emitted during the
  workflow follow the operator's telemetry retention policy on the
  underlying OCSF store.

The retention boundary is enforced by the case-store's lifecycle
hook plus the OCSF store's policy; the workflow itself is stateless
beyond the case it attaches submissions to.

## 6. Cross-border transfers

**No transfer** is the default scoring. The workflow is designed to
execute end-to-end on the operator's sovereign-hosted runtime (one
of the EU-hostable reference targets — n8n self-host, Temporal self-
host, or LangGraph self-host on Nebul / OVHcloud / Scaleway /
Hetzner) with EU-pinned regulator-destination endpoints (national
CSIRT portals and CRA-competent authority submission gateways are
EU-resident by construction) and EU-pinned operator-bound processor
endpoints.

The technical controls that hold this scoring:

- The reference compile targets are framework-agnostic and run on
  the operator's own sovereign-hosted runtime; no SecOps-NG-hosted
  egress path exists in the workflow.
- The regulator destinations are operator-supplied through
  playbook variables; the framework ships no default endpoint and
  no fallback that could route a CRA submission outside the EU.
- The SBOM store and asset-inventory store are operator-hosted
  systems by construction.
- The scoring step calls CVSS arithmetic locally and an EPSS
  endpoint the operator configures; sovereign mirrors of EPSS
  and the CVE feed are available and are the default the
  framework documents.

Two specific egress risks to flag:

- **Reporter acknowledgement** is sent to the reporter's contact
  address; where the reporter is outside the EU/EEA the
  acknowledgement is a transfer in itself, justified by Art. 49
  derogation (necessary for the establishment, exercise, or
  defence of legal claims, or for compelling legitimate interests
  in the operator's vulnerability handling). The transfer is
  bounded to the acknowledgement and the dissemination
  notification and is recorded on the case.
- **Public advisory dissemination** under CRA Annex I §2(7) is
  worldwide by design and is not a Chapter V transfer in the
  controller-to-controller sense — the advisory is published, not
  transferred to a determinate recipient. Personal data inside the
  advisory is limited to the attribution the reporter consented to
  in §2 and to the operator's response-branch signatory.

If an operator binds a non-EU CVE feed mirror, a non-EU EPSS
provider, a non-EU SBOM store, or any external AI classifier on the
disclosure narrative, the default scoring breaks — the operator MUST
re-score this section under "transfer under SCCs / BCRs / derogation"
and document the supplementary measures (encryption-at-rest with
operator-held keys, pseudonymisation of reporter and maintainer
identifiers before egress) before the binding goes live. Sovereignty
review at compile time is the gate.

## 7. Data subject rights

- **Access (Art. 15).** A reporter or named maintainer who
  exercises a SAR against the operator can be answered by querying
  the disclosure-case store on the subject's identifiers from §3.
  CRA Article 14 submissions and the public advisory are part of
  the case record and are searchable as such. Where the regulator's
  own copy of a CRA submission is also held, the SAR against that
  controller is separate and outside the operator's reach.
- **Rectification (Art. 16).** Applicable where the case record or
  a regulator-submission envelope carries an attribute that is
  incorrect at submission time. Reporter contact details are
  rectified on subject request directly on the case;
  acknowledgement re-issuance is handled by the response branch.
  Corrections to a CRA submission after filing flow through the
  regulator's amendment procedure (CRA Article 14 allows updated
  reporting between stages).
- **Erasure (Art. 17).** The retention hook in §5 is the
  operational erasure pathway: the case ages into the operator's
  CVD retention window and is purged on TTL. Reporter contact
  minimisation at the end of the relationship window is the
  intra-lifetime erasure step. A standalone subject-initiated
  erasure request against an open or recently-closed disclosure
  is constrained by the regulatory record-keeping obligation in
  §2 and by litigation-hold; the operator's DPO is the gate.
  Public advisory attribution, once consented and published under
  CRA Annex I §2(7), is not erasable from the public record by
  the operator alone — the operator can withdraw the advisory but
  not the copies already distributed.
- **Objection (Art. 21).** Where the lawful basis is **Art. 6(1)(c)
  legal obligation** (the primary basis in §2), Art. 21 does not
  apply to that part of the processing — the operator cannot
  refuse a CRA acknowledgement or submission on objection
  grounds. For the secondary **Art. 6(1)(f)** basis covering
  internal triage and asset correlation, a data subject can
  object on grounds relating to their particular situation; the
  operational handling is to record the objection on the case and
  route the manual-review fields through the operator's DPO. For
  the optional **Art. 6(1)(a)** consent basis covering public
  advisory attribution, consent is withdrawable at any time and
  the response branch re-issues the advisory without attribution
  if withdrawal lands before dissemination.
- **Automated decision-making (Art. 22).** The per-severity switch
  is a deterministic routing decision driven by CVSS / EPSS
  scoring and CRA Article 14 assessment, and it hands off to a
  human-owned response branch; the scoring itself is arithmetic,
  not a profiling decision. The workflow as shipped does not
  produce a legal or similarly significant effect on a data
  subject in its own right, so Art. 22 does not apply. If an
  operator binds an external classifier whose output triggers an
  automated adverse action against a subject named in the
  disclosure (account lockout against a reporter, automated
  regulator filing without human review), the operator MUST
  re-score this section.

## 8. Outbound personal-data transfer

The workflow has four classes of outbound leg that carry personal
data outside the operator's disclosure-case store. Each is scored
below against GDPR Chapter V (Art. 44–49); the EU-residency posture
is sovereignty-first by default per Directive 1, and the operator's
compile-time bindings are the knobs that can break the scoring.

**Leg A — CRA Article 14 regulator submissions (early warning,
72-hour notification, one-month final report on actively-exploited
or severe-incident clocks).**

- *Destination class.* The operator's competent authority under
  CRA Article 14 — typically the national CSIRT designated for CRA
  reporting, or the sectoral regulator where one is statutorily
  named. The framework ships no default endpoint; the destination
  is operator-supplied through playbook variables, exactly as the
  parallel `incident_management` workflow's NIS2 / DORA submissions.
- *Transfer mechanism.* **No transfer.** EU competent authorities
  under CRA Article 14 are EU/EEA-resident by construction. The
  technical control that holds this is that the regulator portal
  URLs are operator-supplied through compile-time variables and
  sovereignty review at compile time refuses any non-EU endpoint.
- *EU-residency posture (Directive 1).* Default is EU-resident CRA
  competent-authority destinations only. A non-EU binding (a
  third-country authority notified because a cross-border statute
  binds the operator) MUST be re-scored under **SCCs (Art. 46)**
  with operator-held encryption keys on the submission envelope,
  or under **Art. 49(1)(d) "important reasons of public interest"**
  derogation where the cross-border notification is mandated by
  statute the operator is bound by.
- *Data minimisation on egress (Art. 5(1)(c)).* The CRA template
  carries affected-component identifiers (PURL + version), the
  vulnerability identifier (CVE / GHSA / OSV), the operator's
  signatory name on the early-warning / 72-hour / final-report
  submissions, and free-text narrative scoped to the regulator
  template (technical description, mitigation, dissemination
  status). Reporter contact details are NOT transmitted to the
  regulator; the reporter's relationship is bilateral between
  reporter and operator under the CVD policy. Where the reporter
  requested pseudonymity at intake, the case-side handle alone
  appears in any submission narrative that references the
  disclosure source.

**Leg B — Coordinated-disclosure egress to a CVE Numbering
Authority / advisory database (MITRE / GHSA / national CSIRT-run
CNA, OSV).**

- *Destination class.* A CVE Numbering Authority or advisory-
  database controller — typically MITRE (or a delegated CNA, where
  the operator IS a CNA for its own components), the GitHub
  Security Advisory database for GHSA-shaped publications, or the
  national-CSIRT-run CNA where the operator's jurisdiction has one.
  The destination is the controller of the assigned advisory
  identifier and the public advisory record.
- *Transfer mechanism.* **No transfer** when the advisory database
  is EU-hosted (a national-CSIRT-run CNA, an EU mirror of OSV). A
  non-EU CNA — MITRE in the US, GHSA on a US-hosted GitHub control
  plane — MUST be re-scored under **SCCs (Art. 46)** with the
  EU-US Data Privacy Framework cited where the recipient is a
  certified US controller; for a US-based CNA acting under its own
  statutory mandate, an alternative scoring is **Art. 49(1)(d)
  "important reasons of public interest"** where the coordinated-
  disclosure submission is made in the public interest of network
  and information security and a structural instrument is not
  available. Supplementary measures are minimisation of personal-
  data fields in the CVE record (reporter attribution only where
  the reporter consented at intake per §2; no operator-internal
  responder identifiers in the public record).
- *EU-residency posture (Directive 1).* The default published in
  this workflow is a national-CSIRT-run CNA or an EU-hosted
  advisory database where one is available for the affected
  component class. Operators submitting to MITRE / GHSA as the
  primary CNA MUST flag the binding at compile time and re-score
  this section.
- *Data minimisation on egress (Art. 5(1)(c)).* The CVE / GHSA
  record carries the vulnerability identifier, the affected
  component (PURL + version range), the technical description,
  the CVSS / EPSS scoring, the reporter attribution where
  consented per §2, and the operator's response-branch signatory
  identifier; reporter contact details, operator-internal incident
  commander identifiers, and the disclosure-case narrative are
  scoped out of the public record.

**Leg C — Reporter acknowledgement and dissemination notification.**

- *Destination class.* The reporter named at intake — an external
  natural person, a security-research team, an operator-of-another-
  product whose own scanning surfaced the issue, or (where the
  reporter requested pseudonymity) a handle resolvable to a
  contact channel.
- *Transfer mechanism.* The acknowledgement is sent to the
  reporter's contact address as supplied; where the reporter is
  EU/EEA-resident the transfer is **no transfer**. Where the
  reporter is outside the EU/EEA, the acknowledgement is a
  transfer in itself, scored under **Art. 49(1)(b) "necessary for
  the performance of a contract"** (the CVD relationship
  established at intake) and **Art. 49(1)(f) "necessary for the
  establishment, exercise, or defence of legal claims"** where
  the disclosure may underlie subsequent legal action. The
  transfer is bounded to the acknowledgement and the dissemination
  notification and is recorded on the case.
- *EU-residency posture (Directive 1).* The framework cannot pin
  reporter location — the reporter chooses their own contact
  channel. The EU-residency posture is held by the operator's
  notification infrastructure (EU-region mail / messaging
  processor); reporter location is the unbound factor and the
  Art. 49 derogation above carries the third-country case.
- *Data minimisation on egress (Art. 5(1)(c)).* The acknowledgement
  carries the case identifier, the receipt confirmation per CRA
  single-point-of-contact, the disposition the response branch
  routed onto, and the operator's response-branch signatory; the
  acknowledgement does NOT carry operator-internal incident
  commander identifiers, post-incident review fields, or any
  other reporter's identifiers from sibling cases.

**Leg D — Operator-bound processor egress (case store, SBOM store,
EPSS / CVE feed providers, telemetry store).**

- *Destination class.* Operator-bound processors under GDPR
  Art. 28 — the operator's sovereign-hosted disclosure-case store,
  the SBOM store the correlation step queries, the EPSS provider
  invoked during the scoring step, the CVE feed (NVD mirror or
  sovereign equivalent) consulted at intake, and the OCSF
  telemetry store the workflow emits Vulnerability Finding records
  into.
- *Transfer mechanism.* **No transfer** under the default sovereign-
  stack posture: EU-hosted case store, EU-hosted SBOM store,
  sovereign mirrors of CVE / EPSS as the documented default, an
  EU-region OCSF telemetry store. A non-EU EPSS / CVE-feed
  provider, a non-EU SBOM SaaS, or a non-EU case-store binding
  MUST be re-scored under **SCCs (Art. 46)** with supplementary
  measures (encryption-at-rest with operator-held keys,
  pseudonymisation of reporter and maintainer identifiers in the
  case record before egress).
- *EU-residency posture (Directive 1).* The compile-time
  sovereignty review is the gate. The framework ships no default
  processor endpoint and no fallback that could route case-store
  writes outside the EU; the operator's DPA inventory (GDPR
  Art. 28) is the durable record of the processor bindings the
  case-store choice depends on. For EPSS and the CVE feed the
  framework documents sovereign mirror endpoints as the default.
- *Data minimisation on egress (Art. 5(1)(c)).* The CVE-feed /
  EPSS calls carry the vulnerability identifier only — no reporter
  or maintainer identifiers leave the operator's boundary on these
  legs. The SBOM-store call carries the affected-component PURL.
  The case-store write carries the full §3 record exactly as
  enumerated; no analytics-only projection is emitted to a
  separate store independent of the case.

Cross-reference §6: the §6 cross-border scoring as a whole is
**no transfer** for the default sovereign-stack posture, with the
two specific egress risks (reporter outside EU/EEA — Art. 49
derogation, public advisory dissemination — non-Chapter V
publication) already flagged. The §8 above enumerates each leg with
its Chapter V mechanism and is consistent with §6: any leg here
re-scored under SCCs (non-EU CNA, non-EU processor binding) MUST
be reflected in §6 in the same change so the two sections do not
disagree.
