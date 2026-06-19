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
