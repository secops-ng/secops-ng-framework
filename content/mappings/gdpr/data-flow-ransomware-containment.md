# GDPR data flow — ransomware-containment

Per-workflow GDPR data-flow entry for the `ransomware-containment`
cookbook playbook (`playbook.ransomware_containment@v1`). Filled in
against [`_data-flow-template.md`](./_data-flow-template.md). Together
the seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/ransomware-containment/`](../../playbooks/ransomware-containment/).

---

## 1. Purpose

The workflow exists to contain an in-progress or just-detected
ransomware event on an endpoint or identity so the response team can
stop further encryption and lateral spread, preserve the option of
clean recovery, and meet the operator's statutory notification
obligations on time. Concretely, the workflow triages the originating
detection signal against the host and identity it implicates;
isolates the affected host through the operator's EDR agent or, when
the agent is unreachable, through a network-ACL deny at the operator's
egress chokepoint; revokes the implicated identity at the operator's
identity provider (account disable, active-session revocation,
refresh/access-token invalidation, Kerberos TGT invalidation where
supported); locates and integrity-verifies the most recent
known-good backup snapshot that pre-dates the event window; and
drives a comms step that pages the IR lead and the comms officer
and stages the NIS2 Article 23 early-warning pre-notification for
human sign-off within the 24-hour clock. The purpose is bounded to
that containment-and-notification decision and the metric hooks it
produces; the workflow does not restore from backup (the recovery
playbook is a separate, out-of-scope artifact), does not retain
process or file telemetry for analytics, and does not train any
downstream model on the material it sees.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(f) — legitimate interests**. The operator
has a legitimate interest in containing a confirmed ransomware event
— stopping further encryption of the operator's systems, preserving
the recovery path, and limiting blast radius to the implicated host
and identity — and the processing here (host isolation, identity
revocation, backup-snapshot verification, notification drafting) is
necessary and proportionate to that interest. The principal whose
account is revoked and the device user whose host is isolated have a
reasonable expectation that an active ransomware signal against their
host or identifier triggers immediate containment and that the
operator may interrupt their sessions and quarantine the device in
response.

Secondary: where the operator is a regulated entity under the
**NIS2 Directive** and is obliged to maintain an incident-handling
capability under **NIS2 Art. 21(2)(b)** and to file the 24-hour
early-warning under **NIS2 Art. 23** as transposed nationally,
**Art. 6(1)(c) — legal obligation** also applies. Operators subject
to sector-specific incident-reporting rules (DORA Art. 19 for
financial entities, the equivalent regulatory baselines for critical
infrastructure, healthcare, or trust-service operators) inherit the
same secondary basis, which becomes primary for the comms-plan step
because the notification draft is the statutory artifact.

Special-category data (Art. 9) is not the target of the workflow.
Process and file activity, network activity, authentication telemetry,
and backup-snapshot metadata as enumerated in §3 do not carry Art. 9
attributes by design; the workflow does not extract or persist Art. 9
attributes independently. If an operator's IdP carries Art. 9
attributes in the principal's directory record, or the affected host
holds Art. 9 attributes inside the file artifacts the snapshot
covers, the workflow does not read or propagate them — the snapshot
verification step inspects the catalogue hash, not the snapshot
contents.

## 3. Categories of data subjects and personal data

Data subjects:

- **The affected device user** — the employee, contractor, or
  workload owner attached to the host identified by
  `__affected_host__`. Where the host is a shared endpoint, every
  user with an active session on the device at the time of isolation
  is incidentally affected because the EDR isolate or network-ACL
  deny terminates their session.
- **The implicated identity principal** — the user or
  service-account owner identified by `__affected_identity__` whose
  IdP account is disabled and whose active sessions and refresh
  tokens are revoked.
- **The IR lead and comms officer** — the operator's on-call
  incident responder and communications officer whose contact
  details are dereferenced by the comms-plan step to page them
  along the operator's pre-bound channels.
- **Third parties named on the regulator early-warning
  pre-notification** — individuals whose identifiers appear in the
  drafted NIS2 Article 23 notification because they are the
  operator's nominated contact, the affected device user, or the
  implicated principal. Authorship of the final notification is the
  human sign-off step, not the workflow.

Categories of personal data:

- **Host identifiers** — hostname or asset identifier carried by
  `__affected_host__`, device-registration metadata observed during
  triage and EDR isolate (operating-system version, device-management
  tag, last-logged-on user attribute where the EDR exposes it).
- **Identity identifiers** — IdP subject identifier
  (`__affected_identity__`), user principal name, email address,
  display name, and the group and role memberships observed at the
  point of revocation.
- **Authentication metadata** — active session identifiers and
  refresh-token identifiers enumerated for revocation, Kerberos TGT
  identifiers invalidated where supported, sign-in records
  (timestamps, authentication-method-used, originating IP)
  projected through `telemetry.ocsf.authentication@v1`. The token
  material itself is processed transiently and is not persisted.
- **Network identifiers** — source and destination IP addresses,
  port and protocol observed on the affected host during the event
  window and during the network-ACL deny fallback, projected through
  `telemetry.ocsf.network_activity@v1`.
- **Process and file activity** — process-execution records
  (parent-child process trees, command lines, image paths) and
  file-rename, file-deletion, and shadow-copy-deletion records
  observed on the affected host during the event window, projected
  through `telemetry.ocsf.process_activity@v1` and
  `telemetry.ocsf.file_activity@v1`. Command-line arguments may
  incidentally contain identifiers (a username embedded in a path,
  a script-argument referencing a user share); these are captured as
  observed for the containment record but are not extracted as
  separate fields.
- **Backup-snapshot metadata** — the snapshot identifier carried by
  `__latest_known_good_snapshot__`, the catalogue-recorded integrity
  hash, the snapshot creation timestamp, and the catalogue-recorded
  pointer to the host or volume the snapshot covers. The snapshot
  contents themselves are not read by the verification step.
- **Comms-plan artifacts** — the IR lead and comms officer
  identifiers and contact channels dereferenced for paging, and the
  drafted NIS2 Article 23 early-warning pre-notification (which
  carries the affected-host and affected-identity identifiers, the
  detection summary, and the operator's nominated contact).
- **Incident-finding records** — the parent incident-case
  identifier and the projected
  `telemetry.ocsf.incident_finding@v1` record stamped at the
  comms-plan step.

The full plaintext of session tokens, refresh tokens, Kerberos
tickets, and any credential material is processed transiently for
the revocation step; only the inventories, revocation counts, and
catalogue references above are persisted past the workflow's
lifetime.

## 4. Recipients

Internal recipients:

- The **response team** owning the containment branch — the
  operator's incident responders who run the triage decision, the
  EDR isolate or network-ACL deny action, the identity revocation,
  and the backup-verification step.
- The **IR lead** and the **comms officer**, paged at the
  comms-plan step along the operator's pre-bound channels.
- The **device user** whose host is isolated and the **principal**
  whose identity is revoked, who are notified through the
  operator's existing notification path so they can re-authenticate
  and re-enroll factors at next sign-in once the principal is
  reinstated. The workflow does not reinstate the principal — that
  is a separate recovery decision.
- The **metrics layer** consuming `kpi.mttd_ransomware@v1`,
  `kpi.mttr_containment@v1`,
  `kpi.backup_integrity_pass_rate@v1`,
  `kpi.notification_sla_compliance@v1`,
  `kpi.timeline_completeness@v1`, and
  `kri.regulator_notification_overrun@v1` — the recipient is the
  aggregated counter, not the per-host or per-identity record.

External / processor recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **EDR vendor or self-hosted EDR control plane** owning the
  host-isolation action on the affected host, when the EDR-primary
  path is taken.
- The **network control plane** (firewall, switchport controller,
  SDN policy engine) executing the network-ACL deny at the
  operator's egress chokepoint, when the EDR fallback is taken.
- The **identity provider** (Azure AD / Entra ID, Okta, Google
  Workspace, AWS IAM Identity Center, or equivalent) that owns the
  account-disable, session-revocation, refresh-token-invalidation,
  and Kerberos-TGT-invalidation actions for the implicated
  principal.
- The **backup catalogue and snapshot store** (the operator's
  backup product or sovereign-hosted backup service) queried for
  the snapshot identifier and integrity hash.
- The **telemetry / SIEM store** receiving the OCSF Process
  Activity (1007), File Activity (1001), Network Activity (4001),
  Authentication (3002), and Security Finding (2001) activity
  records emitted across triage, containment, revocation, and
  verification.
- The **case-management / ticketing system** carrying the parent
  incident case the workflow opens on confirmation.
- The **paging / communications system** (the operator's on-call
  tool and the channel used to deliver the staged regulator
  pre-notification draft to the comms officer for sign-off).

External / non-processor recipients:

- The **NIS2 competent authority** (and, for DORA-scope operators,
  the **financial-sector competent authority**) is the eventual
  recipient of the early-warning notification once the human
  sign-off completes; the workflow drafts and stages the
  notification but does not transmit it. The regulator is a
  controller-to-controller recipient, not a processor, and is
  named here so the dependency is visible.

Each operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production;
the framework does not ship the DPAs, but the data-flow record
names the dependency so a sovereignty review can verify it.

## 5. Retention

The workflow itself is stateless — the durable retention horizon is
the parent **incident case** opened on confirmed ransomware and the
operator-owned telemetry, backup-catalogue, and case-management
stores:

- **Triage record and detection-signal context** are linked onto
  the incident case as the opening evidence and inherit that case's
  retention (typically incident-open + the operator's
  post-incident-review window; bounded by the operator's
  evidence-pack expiry on the incident-management playbook).
- **EDR isolate action records or network-ACL deny records** are
  linked onto the same incident case as containment evidence and
  follow the case's retention.
- **Identity-revocation artifacts** — the session-revocation
  inventory, the refresh-token revocation count, and the Kerberos
  TGT invalidation record — are linked onto the case and follow
  the case's retention. The token plaintext is not retained beyond
  the revocation span.
- **Backup-verification artifacts** — the snapshot identifier
  carried by `__latest_known_good_snapshot__`, the
  catalogue-recorded integrity hash, and the
  `__snapshot_integrity_ok__` verdict — are linked onto the case
  as recovery-option evidence and follow the case's retention.
  The underlying snapshot itself is retained on the operator's
  backup-product retention policy, not the case's.
- **Comms-plan artifacts** — the page record to the IR lead and
  comms officer and the drafted NIS2 Article 23 early-warning
  pre-notification — are linked onto the case as statutory-
  reporting evidence. The notification draft and the eventual
  signed-off submission inherit the operator's regulatory record-
  keeping period for incident reports, which is typically longer
  than the case's evidence-pack expiry and is the binding
  retention for that artifact.
- **OCSF activity records** emitted during triage, containment,
  revocation, and verification follow the operator's telemetry
  retention policy on the underlying OCSF store.
- **False-positive close-out** (the `ransomware confirmed?`
  branch's failure path, `__ransomware_confirmed__ = false`)
  produces no durable artifact beyond the triage record on the
  originating signal; the operator's telemetry retention policy
  governs that record.

No copy of session tokens, refresh tokens, Kerberos tickets, or
other credential material is retained by the workflow beyond the
revocation span; the durable artifacts are the inventories, counts,
catalogue references, and finding records in §3.

## 6. Cross-border transfers

**No transfer.** The workflow is designed to execute end-to-end on
the operator's sovereign-hosted runtime (one of the EU-hostable
reference targets — n8n self-host, Temporal self-host, or
LangGraph self-host on Nebul / OVHcloud / Scaleway / Hetzner) with
EU-pinned processor endpoints for the operator-bound EDR, network-
control-plane, identity-provider, backup-catalogue, telemetry-store,
case-management, and paging dependencies.

The technical controls that hold this scoring (FOUNDATION
property #3 — sovereignty):

- The reference compile targets are framework-agnostic and run on
  the operator's own sovereign-hosted runtime; no SecOps-NG-hosted
  egress path exists in the workflow. The orchestrator the
  operator already runs is the execution boundary.
- The EDR isolate, network-ACL deny, identity-revocation,
  backup-verification, and case-management calls are
  operator-bound at compile time and target the operator's
  EU-region tenants directly; the playbook itself does not call a
  hosted SecOps-NG containment service.
- The OCSF activity records emit to the operator's telemetry store
  under the operator's region pinning; no external aggregation is
  invoked.
- No public-cloud-AI endpoint is called during triage, containment,
  revocation, verification, or comms drafting; the triage decision
  is human-run and the comms-plan draft is generated from a
  template against the workflow's own outputs.
- The NIS2 Article 23 early-warning pre-notification is staged for
  human sign-off and is delivered to the operator's competent
  authority by the human along the operator's existing regulatory
  channel; the workflow itself does not perform that transmission
  and does not invoke a third-country regulator endpoint.

Re-score gates — if an operator binds any of the following at
compile time, this scoring breaks and the operator MUST re-score
this section under "transfer under SCCs / BCRs / derogation",
name the third country and the transfer instrument, and document
the supplementary measures (encryption-at-rest with operator-held
keys, pseudonymisation of host or principal identifiers before
egress, header stripping on the OCSF projection) before the
binding goes live:

- A **non-EU EDR vendor cloud** (a US-hosted EDR control plane, a
  non-EU-region tenant of an EU-hosted vendor) for the
  endpoint-isolation primary path. The EDR vendor is the most
  common third-country dependency in this workflow and the most
  likely re-score trigger.
- A **non-EU IdP tenant** (a US-region Azure AD tenant, a
  US-region Okta cell) for the identity-revocation step.
- A **non-EU-hosted backup service or backup catalogue** for the
  verification step.
- A **non-EU telemetry / SIEM processor** for the OCSF activity
  records.
- A **non-EU-hosted threat-intelligence enrichment endpoint** if
  the operator binds one into the triage decision (the playbook
  as shipped does not bind one, but a common operator extension
  does).
- A **non-EU case-management or paging vendor** for the IR lead /
  comms officer notification and the regulator-notification
  staging.

Sovereignty review at compile time is the gate. The default
workflow as shipped — EU-pinned on every operator-bound endpoint —
remains scored **no transfer**.

## 7. Data subject rights

- **Access (Art. 15).** A device user or principal who exercises a
  Subject Access Request against the operator can be answered by
  querying the incident-case store on the host and identity
  identifiers from §3 and the operator's telemetry / OCSF store on
  the same identifiers across the activity records the workflow
  emitted. The backup-catalogue record produced by the verification
  step is reached through the same case linkage. The workflow does
  not introduce a separate storage location beyond those parents.
  The IR lead and comms officer answer requests against their own
  identifiers through the operator's standard staff-records
  procedure, not the incident case.
- **Rectification (Art. 16).** The workflow does not store
  subject-supplied attributes that are intended to be updated;
  host identifiers, identity identifiers, process and file activity,
  network identifiers, and backup-snapshot metadata are
  captured-as-observed and rectification at the subject's request
  is not operationally meaningful for the containment record. A
  miscategorised signal is corrected by the triage branch
  (`ransomware confirmed?` set to false, false-positive close-out
  path) as a downstream operational fix, not as an Art. 16
  rectification. The NIS2 Article 23 early-warning
  pre-notification, where it is signed off and submitted with
  factual errors, is corrected through the operator's regulatory
  amendment procedure (NIS2 Art. 23 itself provides for an updated
  intermediate report at 72 hours and a final report), not through
  an Art. 16 rectification against the framework artifact.
- **Erasure (Art. 17).** The retention hooks in §5 are the
  operational erasure pathway: closing the parent incident case
  and ageing the OCSF activity records on the operator's telemetry
  retention TTL erases the workflow's copy of the metadata. The
  drafted and signed-off regulator notification is bound by the
  operator's regulatory record-keeping period and is not erased
  on subject request while that period runs; the legal-obligation
  basis under NIS2 Art. 23 (and DORA Art. 19 where applicable)
  named in §2 is the lawful basis for retaining the notification
  past the case's evidence-pack expiry. A standalone
  subject-initiated erasure request against the case flows
  through the incident-case store's erasure procedure, which the
  workflow inherits.
- **Objection (Art. 21).** Where the lawful basis is
  **Art. 6(1)(f)** (the containment, revocation, and verification
  steps for most operators), a data subject can object to the
  processing on grounds relating to their particular situation.
  The operational handling is to record the objection on the
  incident case; the operator's overriding legitimate-interest
  assessment — anchored in the duty to stop active encryption,
  protect downstream systems and other data subjects, and preserve
  the operator's recovery option — is the gate on whether the
  objection prevails during an active ransomware event, and will
  almost always prevail. Operators under the **NIS2 Art. 21(2)(b)**
  and **NIS2 Art. 23** secondary basis from §2 (and DORA Art. 19
  where applicable) should note that the legal-obligation basis is
  not displaced by Art. 21 objection, which leaves the comms-plan
  step and the regulator-notification draft unaffected by
  objection.
- **Automated decision-making (Art. 22).** The containment
  decision is gated by the `ransomware confirmed?` step, which is
  set during human-run triage by the responder, not by an
  automated classifier with a legal or similarly significant
  effect; the EDR isolate or network-ACL deny, the identity
  revocation, and the backup verification that follow are bulk
  operations the human authorised, and the comms-plan
  pre-notification is staged for human sign-off rather than
  auto-sent. Art. 22 therefore does not apply to the workflow as
  shipped. If an operator binds an automated triage classifier
  whose output sets `__ransomware_confirmed__` without human
  review and triggers the containment branch — isolating the host
  and disabling the principal automatically — the operator MUST
  re-score this section, surface the Art. 22 applicability, and
  document the safeguards (right to obtain human intervention,
  right to contest the decision) the operator provides.
