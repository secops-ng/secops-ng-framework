# GDPR data flow — mfa_secured_comms

Per-workflow GDPR data-flow entry for the `mfa_secured_comms`
cookbook playbook (`playbook.mfa_secured_comms@v1`). Filled in
against [`_data-flow-template.md`](./_data-flow-template.md).
Together the seven sections below form the Art. 30 Record of
Processing Activity entry for this workflow.

Workflow source of truth:
[`content/playbooks/mfa_secured_comms/`](../../playbooks/mfa_secured_comms/).

---

## 1. Purpose

The workflow exists to exercise the operator's authentication and
secured-communications posture surface required by NIS2 Art.
21(2)(j): probe the identity-provider surface to confirm MFA
coverage across in-scope principals, assess whether continuous-
authentication signals are observed on long-lived sessions, verify
the out-of-band emergency communications channel is reachable
independently of the primary information-system path, capture a
dated posture-attestation artifact, and notify the authentication
owner. The purpose is bounded to that exercise decision and the
metric hooks it produces (`kri.mfa_coverage_gaps@v1`); the workflow
does not author the operator's authentication or secured-
communications policy itself, does not enrol or revoke
authenticators, does not invalidate or step up sessions, and does
not deliver a real emergency notification on the out-of-band
channels it tests.

## 2. Lawful basis

**Art. 6(1)(f) — legitimate interests**, with **Art. 6(1)(c) —
legal obligation** available as a secondary basis where the
operator runs under NIS2-implementing national law that compels
the periodic-testing discipline this playbook operates.

The legitimate-interests case rests on the operator's interest in
maintaining the authentication and secured-communications posture
of the entity, balanced against the limited intrusion the workflow
makes into personal data: it reads principal identifiers and
enrolment/enforcement state from the identity-provider surface,
session identifiers and re-authentication timestamps from the
session-management surface, and channel-owner identifiers from the
operator's notification catalogue. No special-category data within
the meaning of GDPR Art. 9 is inspected by the workflow; principal
identifiers are work-account identifiers, not biometric or other
Art. 9 categories. Where the operator runs under a NIS2-implementing
national law that compels this exercise, Art. 6(1)(c) carries the
same processing under a stronger basis.

The personal data the workflow touches is bounded to authentication-
posture metadata about employees and other in-scope principals; it
does not read or persist authentication-secret material (passwords,
factor seeds, recovery codes) and does not inspect the contents of
any communication carried over the OOB channels it tests.

## 3. Categories of data subjects and personal data

**Data subjects**: employees and other in-scope principals of the
operator whose identity records sit in the identity providers
enumerated in `__auth_scope__` (typically all human users of the
operator's information systems), plus the named channel owners of
the out-of-band emergency communications channels (typically a
small set of on-call and incident-response staff).

**Personal data categories**:

- **Principal identifiers** — work-account identifiers (employee
  ID, corporate email address, or directory-service username) read
  by the probe-mfa-coverage step from the identity-provider
  surface, and by the assess-continuous-auth step from the session-
  management surface.
- **Authentication-state metadata** — MFA enrolment state, MFA
  factor types enrolled (without secret material), enforcement
  state, last successful MFA event timestamp.
- **Session metadata** — session identifiers, session age, last
  re-authentication event timestamp, declared re-authentication
  cadence; not the session payload or any data transferred over
  the session.
- **Channel-owner identifiers** — names and contact endpoints of
  the channel owners verified by the verify-oob-channels step and
  of the authentication owner notified by the notify step
  (ticketing system identifier, chat thread identifier, email
  address — the operator's pre-bound channel only).

**Out of scope** (deliberate omission): authentication secrets,
recovery material, biometric templates, the contents of any
communication carried on the OOB channels, and any other Art. 9
special-category data.

## 4. Recipients

- **Operator's evidence store** — primary recipient of the dated
  posture-attestation record (the audit-evident artifact NIS2 Art.
  21(2)(j) reviewers read), which carries principal identifiers in
  aggregate gap counts and may carry per-principal records of MFA
  enrolment-state regressions and stale-session detections.
- **Authentication owner** along their pre-bound channel — receives
  the attestation reference via the notify-authentication-owner
  step. The notification carries the attestation reference, not the
  per-principal records themselves.
- **Catalogue metric pipeline** that reads `kri.mfa_coverage_gaps@v1`
  from the emitted records for programme-level rollup (handled by
  the sibling `executive_metrics` workflow); the rollup operates on
  aggregate counts, not per-principal records.

No external processor is invoked by the default configuration; the
identity-provider surface, the session-management surface, the OOB-
channel test endpoints, the evidence store, and the notification
channel are all operator-bound infrastructure. Operators integrating
a third-party identity provider, session-management product, or
OOB-channel platform engage that provider's own GDPR posture
(typically under a Data Processing Agreement); the DPA itself lives
outside the framework, but the dependency is visible in the
operator's binding of `__auth_scope__`.

## 5. Retention

The dated posture-attestation record is retained as the operator's
NIS2 Art. 21(2)(j) evidence under the operator's regulatory-
retention overlay; the retention mechanism is the evidence-bundle
expiry rule shared with the other evidence streams under
`schemas/evidence/bundle.schema.json`. This workflow does not
maintain its own retention schedule.

The MFA-coverage snapshot, continuous-authentication assessment,
and OOB-channel verification artifacts the workflow produces sit
alongside the attestation under the same retention overlay. Per-
principal records inside those artifacts are bounded to identifiers
and state metadata; once the parent evidence bundle expires, the
per-principal records expire with it.

## 6. Cross-border transfers

**No transfer.** The default configuration runs the MFA-coverage
probe, the continuous-authentication assessment, the OOB-channel
verification, the evidence-capture emission, and the notify
dispatch entirely against operator-bound, EU-resident endpoints
(the operator's identity-provider surface, session-management
surface, OOB-channel test endpoints, evidence store, and
notification channel). No public-cloud-AI dependency is wired on
the workflow's hot path. Operators MAY swap in a non-EU-hosted
identity provider, session-management product, evidence store, or
notification channel; doing so is visible on a fork of this
data-flow doc, but is not the default and is not the configuration
the framework ships.

Where the operator's identity provider is non-EU-hosted on the
production side, the per-principal records this workflow reads
cross a Chapter V boundary on the upstream read; the operator's
overall identity-provider binding (and its DPA / SCC posture)
governs that boundary, not this playbook. This data-flow doc
flags the dependency so it remains visible in review.

## 7. Data subject rights

Subject Access Requests, rectification requests, erasure requests,
and objections that bear on the principal records this workflow
reads are answered against the operator's identity-provider and
session-management surfaces — those surfaces are the authoritative
record-holders for the data subject.

The attestation record and the per-principal records this workflow
emits to the evidence store carry derivative state (MFA enrolment
state, last successful MFA event, session age, last re-auth event)
sourced from the upstream identity surfaces. A subject who has
exercised an erasure right against the upstream identity surface
has had their identity record removed there; the derivative records
held in the evidence store expire under the regulatory-retention
overlay (§5) and the operator's evidence-store erasure procedure
covers the case where erasure is exercised mid-retention. The
playbook does not maintain a parallel subject-record store that
must be erased independently.

Objections to the legitimate-interests basis (§2) against the
authentication-posture exercise itself are answered at the operator
level — the discipline exists to discharge a regulatory obligation
on the operator, not on individual subjects.

## 8. Outbound personal-data transfer

**No outbound personal-data transfer in the default configuration
— N/A.** Per §6, the default binding keeps the MFA-coverage probe,
the continuous-authentication assessment, the OOB-channel
verification, the evidence-capture emission, and the notify dispatch
on operator-bound, EU-resident endpoints; the per-principal records
the workflow produces do not leave the operator's EU-resident
infrastructure.

The non-default-binding case where an operator wires a non-EU-hosted
identity provider, session-management product, evidence store, or
notification channel introduces a Chapter V outbound leg on the
binding the operator chose; that leg's scoring (destination class,
transfer mechanism, EU-residency posture, data minimisation) is the
operator's responsibility on their fork of this data-flow doc, and
the dependency is flagged in §4 and §6 so the swap is visible in
review.

Cross-reference §6: the workflow-as-a-whole cross-border scoring is
**no transfer** under the default configuration and this §8 carries
no contradicting leg under that configuration.

If a future revision binds a non-default identity-provider or
session-management surface, or extends the attestation record to
carry communication contents from the OOB channels, this section
MUST be re-scored against the canonical four-axis shape and §3
amended in the same change.
