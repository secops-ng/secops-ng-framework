# GDPR data flow — phishing_triage

Per-workflow GDPR data-flow entry for the `phishing_triage` cookbook
playbook (`playbook.phishing_triage@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/phishing_triage/`](../../playbooks/phishing_triage/).

---

## 1. Purpose

The workflow exists to triage inbound user-reported or
mailbox-sweep emails so that the response team can act on the
malicious ones, suppress the already-seen and known-benign noise
without paging, and route the remaining cases by intent (phishing,
credential harvest, malware-attached, business-email-compromise, or
unknown). The purpose is bounded to that triage decision and the
metric hooks it produces — the workflow does not retain message
content for analytics or train any downstream model on the
material it sees.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(f) — legitimate interests**. The operator
has a legitimate interest in defending the organisation against
phishing, credential theft, and business-email compromise, and the
processing here is necessary and proportionate to that interest.
The data subjects (own employees who report; external senders
whose envelopes are inspected) have a reasonable expectation that
inbound mail crossing the organisation's perimeter is subject to
security inspection.

Secondary: where the operator runs in a regulated sector and is
obliged to maintain incident-handling capability under **NIS2
Art. 21(2)(b)** as transposed nationally, **Art. 6(1)(c) — legal
obligation** also applies.

Triage is also the step that backs the operator's readiness against
**GDPR Art. 33(1)** — the personal-data-breach notifiability decision
and its "unless the personal-data breach is unlikely to result in a
risk to the rights and freedoms of natural persons" likelihood-of-risk
threshold. A reported phishing or credential-harvest event becomes a
notifiable personal-data breach only when that threshold is crossed
(for example, a successful credential capture against a mailbox
holding personal data of identifiable subjects). The triage step is
what classifies inbound mail by intent and severity up to the
decision boundary where the case-management workflow takes over and
formally evaluates notifiability under Art. 33(1); the triage workflow
itself does not make that notifiability call.

Special-category data (Art. 9) is not the target of the workflow,
but may be incidentally observed inside reported message bodies;
the workflow does not extract or persist Art. 9 attributes
independently of the message envelope retention in §5.

## 3. Categories of data subjects and personal data

Data subjects:

- **Employees of the operator** who report suspicious mail (the
  reporter identified by `__report_source__`).
- **Employees of the operator** named as recipients of the
  inspected message.
- **External senders** whose envelopes, headers, and authentication
  records (SPF / DKIM / DMARC) are inspected.
- **Third parties** named or linked from message bodies and
  attachments (URLs, attached document authors).

Categories of personal data:

- **Identifiers** — work email addresses, display names, reporter
  identifier.
- **Network identifiers** — sender IP addresses, originating mail
  server hostnames, user-agent strings from the reporting client.
- **Authentication metadata** — SPF / DKIM / DMARC results bound to
  the sender domain.
- **Content metadata** — subject lines, URL strings extracted from
  the body, attachment filenames and hashes, OCSF Email (4009) /
  URL (4002) / File (1001) activity records.

Message body and attachment payloads are processed transiently for
the enrichment and classification steps; only the metadata
projections above are persisted past the workflow's lifetime.

## 4. Recipients

Internal recipients:

- The **response team** owning the per-intent response branch
  (phishing, credential-harvest, malware-attached, BEC, manual
  review).
- The **metrics layer** consuming `kpi.mttd_phishing@v1`,
  `kpi.mttr_phishing_triage@v1`, `kpi.phishing_sim_click_rate@v1`,
  and `kri.phishing_suppression_rate@v1` — recipient is the
  aggregated counter, not the per-message identifier.

External / processor recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- **Email-security platform** providing envelope and header
  sources.
- **URL-reputation provider** and **attachment analyser** invoked
  during enrichment.
- **Paging gateway** and **notification channel** for each response
  branch.

Each operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production;
the framework does not ship the DPAs, but the data-flow record
names the dependency so a sovereignty review can verify it.

## 5. Retention

The workflow itself is stateless — the durable retention horizon is
the parent **incident case** or **suppression record** it feeds:

- **Triaged-malicious messages** are linked onto the incident case
  opened by the per-intent response branch and inherit that case's
  retention (typically incident-open + the operator's
  post-incident review window; bounded by the operator's evidence-
  pack expiry on the incident_management playbook).
- **Suppressed messages** are linked onto the existing
  known-benign-sender record or the open case they correlate to;
  the suppression record itself retains envelope and authentication
  metadata for the rolling window the operator configures on
  `kri.phishing_suppression_rate@v1` and is purged on TTL.
- **OCSF activity records** emitted during enrichment follow the
  operator's telemetry retention policy on the underlying OCSF
  store.

No copy of the original message body or attachments is retained by
the workflow beyond the enrichment span; the durable artifact is
the metadata projection in §3.

## 6. Cross-border transfers

**No transfer.** The workflow is designed to execute end-to-end on
the operator's sovereign-hosted runtime (one of the EU-hostable
reference targets — n8n self-host, Temporal self-host, or
LangGraph self-host on Nebul / OVHcloud / Scaleway / Hetzner) with
EU-pinned processor endpoints for the operator-bound URL-reputation
and attachment-analysis dependencies.

The technical controls that hold this scoring:

- The reference compile targets are framework-agnostic and run on
  the operator's own sovereign-hosted runtime; no SecOps-NG-hosted
  egress path exists in the workflow.
- The intent classifier is operator-bound and runs inline against
  the operator's chosen model; the playbook does not call any
  public-cloud-AI endpoint.
- The OCSF activity records emit to the operator's telemetry
  store; no external aggregation is invoked.

If an operator binds a non-EU URL-reputation provider, attachment
sandbox, or AI classifier at compile time, this scoring breaks —
the operator MUST re-score this section under "transfer under
SCCs / BCRs / derogation" and document the supplementary measures
(encryption-at-rest with operator-held keys, pseudonymisation of
envelope addresses before egress) before the binding goes live.
Sovereignty review at compile time is the gate.

## 7. Data subject rights

- **Access (Art. 15).** A subject who exercises a SAR against the
  operator can be answered by querying the incident-case store and
  the suppression record store on the subject's email address and
  identifiers from §3. The workflow does not introduce a separate
  storage location beyond those parents.
- **Rectification (Art. 16).** The workflow does not store
  subject-supplied attributes that are intended to be updated;
  envelope metadata is captured-as-observed and rectification at
  the subject's request is not operationally meaningful for the
  triage record. A miscategorised intent is corrected by the
  response branch as a downstream operational fix, not as an
  Art. 16 rectification.
- **Erasure (Art. 17).** The retention hooks in §5 are the
  operational erasure pathway: closing the parent incident case
  and ageing the suppression record on TTL erases the workflow's
  copy of the metadata. A standalone subject-initiated erasure
  request flows through the incident-case store's erasure
  procedure, which the workflow inherits.
- **Objection (Art. 21).** Where the lawful basis is **Art. 6(1)(f)**
  (most operators), a data subject can object to processing on
  grounds relating to their particular situation. The operational
  handling is to flag the subject's identifier on the suppression
  record so subsequent inbound mail from that subject is routed to
  manual review rather than automated suppression / classification,
  and to record the objection alongside the incident case. The
  operator's overriding legitimate-interest assessment is the gate
  on whether the objection prevails.
- **Automated decision-making (Art. 22).** The intent switch is a
  routing decision that hands off to a human-owned response
  branch; it does not produce a legal or similarly significant
  effect on the data subject in its own right, so Art. 22 does
  not apply to the workflow as shipped. If an operator binds a
  classifier whose output triggers an automated adverse action
  against the subject (account lockout, mailbox quarantine
  without review), the operator MUST re-score this section.

## 8. Outbound personal-data transfer

The workflow has four classes of outbound leg that carry personal
data outside the runtime's own process boundary into operator-bound
processors. Each is scored below against GDPR Chapter V
(Art. 44–49); the EU-residency posture is sovereignty-first by
default per Directive 1, and the operator's compile-time bindings
are the knobs that can break the scoring.

**Leg A — Email-security platform read (envelope and header
sources).**

- *Destination class.* Processor under GDPR Art. 28 — the
  operator's email-security platform feeding envelope and
  authentication-header sources into triage. The framework
  ships no default endpoint.
- *Transfer mechanism.* **No transfer.** The default
  sovereign-stack posture pins the email-security platform to
  an EU-region tenant. The technical control is the operator's
  compile-time region pin on the email-security binding.
- *EU-residency posture.* Default is an EU-resident
  email-security platform under an Art. 28 DPA. A non-EU
  binding (a US-region email-security tenant where the
  operator's mailflow telemetry is held) MUST be re-scored
  under Art. 46 SCCs with supplementary measures
  (encryption-at-rest with operator-held keys, pseudonymisation
  of envelope addresses before egress) before the binding goes
  live.
- *Data minimisation on egress.* Only the envelope projection,
  authentication-header projection, and message-metadata fields
  enumerated in §3 are read; the message body and attachments
  are not read into the workflow beyond the enrichment span.

**Leg B — URL-reputation provider and attachment analyser
(enrichment).**

- *Destination class.* Processors under GDPR Art. 28 — the
  operator's URL-reputation provider and the operator's
  attachment-analysis sandbox. Both are operator-bound in the
  compile-target binding rather than the playbook.
- *Transfer mechanism.* **No transfer** is the default scoring
  under the sovereign-stack posture (an EU-resident
  URL-reputation provider and an EU-resident sandbox under
  Art. 28 DPAs are achievable but not universal — most
  commodity providers are US-hosted by default). Where the
  operator binds a third-country URL-reputation provider or
  attachment sandbox, the binding MUST be re-scored under
  Art. 46 SCCs with supplementary measures (the URL submitted
  is stripped of envelope identifiers before egress, attachment
  payloads are submitted as content-hashes where the provider
  supports hash-first lookup, and the operator-held key wraps
  any cached verdict written back). Compile-time sovereignty
  review is the gate and SHOULD surface a non-EU enrichment
  binding for explicit operator acknowledgement.
- *EU-residency posture.* Default is EU-resident enrichment
  providers; the operator's compile-time binding is the knob.
  An EU-region URL-reputation provider and an EU-region
  sandbox under Art. 28 DPAs hold the scoring; absent that,
  re-scoring as above.
- *Data minimisation on egress.* The URL submitted to the
  reputation provider is the URL only — no envelope identifiers,
  no recipient mailbox. The attachment submitted to the sandbox
  is the attachment payload; envelope identifiers and recipient
  context are not transmitted alongside it. Where the provider
  supports it, hash-first lookup is preferred over payload
  submission.

**Leg C — Paging gateway and notification channel (per-intent
response branch).**

- *Destination class.* Processors under GDPR Art. 28 — the
  operator's paging gateway and notification channel for the
  per-intent response branches (phishing, credential-harvest,
  malware-attached, BEC, manual review). The framework ships no
  default endpoint.
- *Transfer mechanism.* **No transfer.** The default
  sovereign-stack posture pins the paging gateway and
  notification channel to EU-region tenants. The technical
  control is the operator's compile-time region pin on each
  binding.
- *EU-residency posture.* Default is EU-resident paging and
  notification tenants under Art. 28 DPAs. A non-EU binding (a
  US-region paging SaaS) MUST be re-scored under Art. 46 SCCs
  with supplementary measures (encryption-at-rest with
  operator-held keys, pseudonymisation of subject envelope
  identifiers in the page body before egress) before the
  binding goes live.
- *Data minimisation on egress.* The page carries the response
  branch verdict and the metadata projection enumerated in §3
  (envelope addresses, intent classification, suppression
  state); message body and attachments are not paged.

**Leg D — Incident-case store, suppression-record store, and
telemetry / SIEM store (durable artefacts of triage).**

- *Destination class.* Processors under GDPR Art. 28 — the
  operator's incident-case store (inherited from the
  incident_management playbook), the operator's
  suppression-record store, and the operator's telemetry / SIEM
  store. No default endpoint ships with the framework.
- *Transfer mechanism.* **No transfer.** The default
  sovereign-stack posture pins each store to an EU-region
  tenant. The technical control is the operator's compile-time
  region pin on each store binding.
- *EU-residency posture.* Default is EU-resident stores under
  Art. 28 DPAs. A non-EU binding MUST be re-scored under
  Art. 46 SCCs with supplementary measures (encryption-at-rest
  with operator-held keys, pseudonymisation of envelope
  addresses before egress) before the binding goes live.
- *Data minimisation on egress.* The case-store payload carries
  the triaged-malicious metadata projection enumerated in §3;
  the suppression record carries envelope and authentication
  metadata only; OCSF activity records carry the enrichment
  span metadata. The original message body and attachments are
  not retained in any of these stores beyond the enrichment
  span, per §5.

The §6 cross-border scoring as a whole is **no transfer** —
consistent with all four legs above scoring no-transfer under the
default sovereign-stack posture (and with the explicit re-scoring
hooks above where an operator binds a non-EU enrichment provider).
Any operator re-scoring of a leg here MUST be reflected in §6 in
the same change so the two sections do not disagree.
