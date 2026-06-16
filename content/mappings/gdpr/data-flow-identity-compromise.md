# GDPR data flow — identity-compromise

Per-workflow GDPR data-flow entry for the `identity-compromise`
cookbook playbook (`playbook.identity_compromise@v1`). Filled in
against [`_data-flow-template.md`](./_data-flow-template.md). Together
the seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/identity-compromise/`](../../playbooks/identity-compromise/).

---

## 1. Purpose

The workflow exists to respond to a detected account compromise —
credential theft, MFA bypass, anomalous sign-in, suspicious OAuth
grant, or impossible-travel signal — so the response team can contain
the principal's blast radius (force MFA re-enrollment, revoke all
active sessions and refresh tokens across the IdP and downstream
SaaS tenants), hunt for lateral movement attributable to the
compromised identity within a bounded lookback window, and remove
residual persistence (rogue OAuth consents, third-party app grants,
conditional-access exceptions, inbox rules, standing-privilege role
assignments). The purpose is bounded to that containment and
remediation decision and the metric hooks it produces; the workflow
does not retain authentication telemetry for analytics or train any
downstream model on the material it sees.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(f) — legitimate interests**. The operator
has a legitimate interest in defending the organisation against
account takeover, credential reuse, and lateral movement from a
compromised identity, and the processing here — re-authenticating
the principal, revoking sessions, auditing the principal's IAM
surface, and hunting downstream activity — is necessary and
proportionate to that interest. The principal whose account is
under containment has a reasonable expectation that anomalous
sign-in activity attached to their identifier is subject to
security inspection and that the operator may interrupt sessions
and force factor re-enrollment in response.

Secondary: where the operator is a regulated entity under the
**NIS2 Directive** and is obliged to maintain an incident-handling
capability under **NIS2 Art. 21(2)(b)** as transposed nationally,
**Art. 6(1)(c) — legal obligation** also applies. Operators
subject to sector-specific rules (DORA Art. 17 for financial
entities, eIDAS trust-service obligations) inherit the same
secondary basis.

Special-category data (Art. 9) is not the target of the workflow.
Authentication telemetry, IAM-surface metadata, and lateral-movement
findings as enumerated in §3 do not contain Art. 9 attributes by
design; the workflow does not extract or persist Art. 9 attributes
independently. If an operator's IdP carries Art. 9 attributes in
the principal's directory record, the workflow does not read or
propagate them.

## 3. Categories of data subjects and personal data

Data subjects:

- **The compromised principal** — the employee, contractor,
  service-principal owner, or workload-identity owner identified
  by `__principal_id__`. The principal is the central data subject
  for every step of the workflow.
- **Downstream principals touched during the lateral-movement
  hunt** — other employees, contractors, or service-principal
  owners whose identifiers appear in the hunt findings under
  `__lateral_findings_count__` because the compromised principal
  interacted with their resources, role-chained into their
  permissions, or shared a session boundary.
- **Third parties named on residual persistence artifacts** —
  external OAuth-application publishers, third-party SaaS vendors
  whose app grants are reviewed during the IAM audit, and any
  external recipients of inbox-forwarding rules created during
  the compromise window.

Categories of personal data:

- **Identifiers** — IdP subject identifiers (`__principal_id__`,
  downstream principal subjects), user principal names, email
  addresses, display names, group memberships and role
  assignments observed during triage and the IAM audit.
- **Authentication metadata** — MFA factor inventories pre and
  post reset (TOTP / WebAuthn / app-password records, but not the
  factor secrets themselves), sign-in records (timestamps,
  conditional-access verdicts, authentication-method-used,
  authentication-protocol), and the originating identity-protection
  signal record carried by `__signal_id__`.
- **Network identifiers** — sign-in IP addresses, autonomous-system
  attribution, user-agent strings, device identifiers and device
  registrations, and the geographies derived from those addresses
  (the input to the impossible-travel signal).
- **Session artifacts** — active session identifiers, refresh
  tokens, and persistent device grants enumerated for revocation
  (counts are persisted via `__sessions_revoked_count__`; the
  token material itself is not).
- **API-activity records** — STS / AssumeRole chains, cross-tenant
  access events, API-token reuse patterns, and OAuth-grant
  escalations observed during the lateral-movement hunt, projected
  through `telemetry.ocsf.authentication@v1`,
  `telemetry.ocsf.api_activity@v1`, and
  `telemetry.ocsf.account_change@v1`.
- **IAM-surface metadata** — rogue OAuth consents, third-party app
  grants, conditional-access exceptions, inbox-forwarding rules,
  new device registrations, and standing-privilege role
  assignments enumerated during the IAM audit.

Authentication factor secrets, refresh-token plaintext, and any
credential material are processed transiently for the reset and
revocation steps; only the inventories and revocation counts
above are persisted past the workflow's lifetime.

## 4. Recipients

Internal recipients:

- The **response team** owning the containment branch — the
  operator's IAM administrators and incident responders who run
  the MFA reset, session revocation, lateral-movement hunt, and
  IAM-audit actions.
- The **principal whose account is being contained**, who is
  notified through the operator's existing notification path so
  they can re-authenticate and re-enroll factors at next sign-in.
- The **metrics layer** consuming `kpi.mttd_identity_compromise@v1`,
  `kpi.mttc_identity_compromise@v1`, and
  `kpi.lateral_hunt_coverage@v1` — the recipient is the
  aggregated counter, not the per-principal identifier.

External / processor recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **identity provider** (Azure AD / Entra ID, Okta, Google
  Workspace, AWS IAM Identity Center, or equivalent) that owns the
  sign-in signal, the MFA factor store, the session and refresh
  tokens, and the conditional-access surface. The IdP is both the
  source of the authentication telemetry and the target of the
  reset and revocation actions.
- The **downstream SaaS tenants** federated against the IdP, whose
  session and token stores are walked during the revocation step.
- The **telemetry / SIEM store** receiving the OCSF Authentication
  (3002), API Activity (6003), and Account Change (3001) activity
  records emitted during the hunt and audit.
- The **case-management / ticketing system** carrying the parent
  incident case the workflow opens on confirmation.

Each operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production;
the framework does not ship the DPAs, but the data-flow record
names the dependency so a sovereignty review can verify it.

## 5. Retention

The workflow itself is stateless — the durable retention horizon is
the parent **incident case** opened on confirmed compromise and the
operator-owned telemetry store:

- **MFA factor inventories pre / post reset** and the
  **session-revocation count** are linked onto the incident case as
  containment evidence and inherit that case's retention (typically
  incident-open + the operator's post-incident-review window;
  bounded by the operator's evidence-pack expiry on the
  incident-management playbook).
- **Lateral-movement findings** are linked onto the same incident
  case and follow the case's retention. Findings that escalate to
  their own incident case (a downstream principal is itself
  compromised, a service-principal-owned resource is implicated)
  carry forward to that child case under the same rule.
- **IAM-audit artifacts** — removed OAuth grants, removed app
  grants, removed inbox rules, removed conditional-access
  exceptions — are recorded onto the case as remediation evidence
  with the same retention.
- **OCSF activity records** emitted during triage, revocation,
  hunt, and audit follow the operator's telemetry retention policy
  on the underlying OCSF store.
- **False-positive close-out** (the `compromise confirmed?`
  branch's failure path, `__compromise_confirmed__ = false`)
  produces no durable artifact beyond the triage record on the
  originating signal; the operator's telemetry retention policy
  governs that record.

No copy of authentication factor secrets, refresh-token plaintext,
or other credential material is retained by the workflow beyond
the reset and revocation span; the durable artifacts are the
inventories, counts, and IAM-surface diffs in §3.

## 6. Cross-border transfers

**No transfer.** The workflow is designed to execute end-to-end on
the operator's sovereign-hosted runtime (one of the EU-hostable
reference targets — n8n self-host, Temporal self-host, or
LangGraph self-host on Nebul / OVHcloud / Scaleway / Hetzner) with
EU-pinned processor endpoints for the operator-bound identity-
provider, downstream-SaaS, and telemetry-store dependencies.

The technical controls that hold this scoring (FOUNDATION
property #3 — sovereignty):

- The reference compile targets are framework-agnostic and run on
  the operator's own sovereign-hosted runtime; no SecOps-NG-hosted
  egress path exists in the workflow. The orchestrator the
  operator already runs is the execution boundary.
- The identity-provider, SaaS-revocation, and IAM-audit calls are
  operator-bound at compile time and target the operator's
  EU-region tenants directly; the playbook itself does not call a
  hosted SecOps-NG identity service.
- The OCSF activity records emit to the operator's telemetry
  store under the operator's region pinning; no external
  aggregation is invoked.
- No public-cloud-AI endpoint is called during triage, hunt, or
  audit; the triage and hunt decisions are operator-bound and run
  inline against the operator's chosen tooling.

If an operator binds a non-EU IdP tenant (a US-region Azure AD
tenant, a US-region Okta cell), a non-EU SaaS tenant the principal
holds sessions in, or a non-EU telemetry processor at compile time,
this scoring breaks — the operator MUST re-score this section
under "transfer under SCCs / BCRs / derogation", name the third
country and the transfer instrument, and document the
supplementary measures (encryption-at-rest with operator-held
keys, pseudonymisation of principal identifiers before egress,
header stripping on the OCSF projection) before the binding goes
live. Sovereignty review at compile time is the gate.

## 7. Data subject rights

- **Access (Art. 15).** A principal who exercises a Subject Access
  Request against the operator can be answered by querying the
  incident-case store on the principal's identifiers from §3 and
  the operator's telemetry / OCSF store on the same identifiers
  across the activity records the workflow emitted. The workflow
  does not introduce a separate storage location beyond those
  parents. Downstream principals named in lateral-movement
  findings are answered by the same query against the incident
  case the finding attaches to.
- **Rectification (Art. 16).** The workflow does not store
  subject-supplied attributes that are intended to be updated;
  authentication metadata, IAM-surface metadata, and
  lateral-movement findings are captured-as-observed and
  rectification at the subject's request is not operationally
  meaningful for the containment record. A miscategorised signal
  is corrected by the triage branch (`compromise confirmed?` set
  to false, false-positive close-out path) as a downstream
  operational fix, not as an Art. 16 rectification.
- **Erasure (Art. 17).** The retention hooks in §5 are the
  operational erasure pathway: closing the parent incident case
  and ageing the OCSF activity records on the operator's
  telemetry retention TTL erases the workflow's copy of the
  metadata. A standalone subject-initiated erasure request flows
  through the incident-case store's erasure procedure, which the
  workflow inherits.
- **Objection (Art. 21).** Where the lawful basis is
  **Art. 6(1)(f)** (most operators), a data subject can object to
  the processing on grounds relating to their particular
  situation. The operational handling is to record the objection
  on the incident case and route subsequent identity-protection
  signals for the same principal through a manual-review branch
  rather than the automated containment branch. The operator's
  overriding legitimate-interest assessment — anchored in the
  duty to protect downstream principals and the operator's wider
  systems from a confirmed-compromised account — is the gate on
  whether the objection prevails; operators under the **NIS2
  Art. 21(2)(b)** secondary basis from §2 should note that the
  legal-obligation basis is not displaced by Art. 21 objection.
- **Automated decision-making (Art. 22).** The containment
  decision is gated by the `compromise confirmed?` step, which is
  set during human-run triage by the responder, not by an
  automated classifier with a legal or similarly significant
  effect; the MFA reset and session revocation that follow are
  bulk operations the human authorised. Art. 22 therefore does
  not apply to the workflow as shipped. If an operator binds an
  automated triage classifier whose output sets
  `__compromise_confirmed__` without human review and triggers
  the containment branch — locking the principal out of the IdP
  and downstream SaaS without responder confirmation — the
  operator MUST re-score this section, surface the Art. 22
  applicability, and document the safeguards (right to obtain
  human intervention, right to contest the decision) the
  operator provides.
