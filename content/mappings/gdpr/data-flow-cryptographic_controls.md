# GDPR data flow — cryptographic_controls

Per-workflow GDPR data-flow entry for the `cryptographic_controls`
cookbook playbook (`playbook.cryptographic_controls@v1`). Filled in
against [`_data-flow-template.md`](./_data-flow-template.md).
Together the sections below form the Art. 30 Record of Processing
Activity entry for this workflow.

Workflow source of truth:
[`content/playbooks/cryptographic_controls/`](../../playbooks/cryptographic_controls/).

Sibling: the read-side posture-attestation lane is documented at
[`data-flow-crypto_posture_management.md`](data-flow-crypto_posture_management.md).
Both overlays anchor NIS2 Art. 21(2)(h); this data-flow doc is the
write-side lifecycle counterpart to that read-side surface.

---

## 1. Purpose

The workflow exists to discharge the write-side lifecycle of the
operator's cryptography and encryption surface required by NIS2
Art. 21(2)(h): resolve the declared cryptography policy at the start
of a lifecycle event (algorithm floor, key-size floor, per-key-class
rotation cadence, TLS-version floor, declared CA / trust anchors,
expiry buffer), discharge the key-lifecycle branch (generation of
new keys against the declared floor, rotation of existing keys
against the declared cadence, revocation of compromised or
scope-exited keys), evaluate the encryption-enforcement gate against
the at-rest and in-transit conditions the policy names, discharge
the certificate-lifecycle branch (issue against the declared CA,
renew ahead of the declared expiry buffer, revoke on compromise or
scope exit), record a dated lifecycle-attestation to the operator's
evidence store, and notify the cryptography owner. The purpose is
bounded to those lifecycle branches; the workflow does not author
the cryptography policy itself, does not perform the read-side
posture-attestation exercise (which the sibling
`crypto_posture_management` playbook operates), and does not inspect
the payloads the resulting cryptographic material protects.

## 2. Lawful basis

**Out of scope: no personal data processed in this workflow.**

The workflow operates on cryptographic-material metadata, not on the
contents of any data the operator's cryptography protects. The
fields it reads and writes are: cryptography-policy snapshots
(algorithm floors, key-size floors, rotation cadences, TLS-version
floors, declared CA / trust anchors, expiry buffers), key
identifiers and their algorithm / key-class / lifecycle-timestamp
records, certificate identifiers and their issuer / not-before /
not-after / renewal / revocation records, enforcement-gate decision
records (workload id, at-rest and in-transit condition observed vs
required, admit / deny outcome), the resulting lifecycle-attestation
identifier, and the cryptography owner's pre-bound channel
identifier. None of these carry personal data within the meaning of
GDPR Art. 4(1): the workflow exercises the key-and-certificate
lifecycle of the cryptography surface, it does not process the
personal-data payload that surface may protect.

The personal data that traverses TLS endpoints or sits at rest under
the keys and certificates this playbook manages has a lawful basis
on the production-side workflows that operate that data — not on
this lifecycle-management playbook. This workflow is the
key-and-certificate-lifecycle discipline that GDPR Art. 32(1)(a)
(pseudonymisation and encryption of personal data) and NIS2 Art.
21(2)(h) implicitly require operators to run against their
cryptography surface; it does not introduce a new processing purpose
against subject data.

If a future revision of this workflow extends scope to inspect
payload contents (for example, to re-encrypt existing records under
a rotated key), this section MUST be revisited and a real lawful
basis declared before that extension ships.

## 3. Categories of data subjects and personal data

Not applicable — no personal data processed. The workflow operates
on cryptographic-material metadata: policy snapshots, key
identifiers and lifecycle timestamps, certificate identifiers and
lifecycle timestamps, enforcement-gate decisions, and attestation
identifiers. No category of natural person is the subject of the
processing.

For completeness: the cryptography owner's pre-bound channel
identifier (ticketing system, chat thread, email) is a contact
endpoint, not a data-subject record — the notify-crypto-owner step
delivers a lifecycle-attestation reference along that channel and
does not introduce or retain a per-subject record beyond what the
operator's notification surface already holds independently.

## 4. Recipients

Not applicable for personal data. For completeness, the recipients
of the non-personal lifecycle-evidence data the workflow emits are:

- the operator's **KMS backend** — recipient of the key-lifecycle
  operations (generate, rotate, revoke) and the emitter of the
  key-material-metadata the workflow records against;
- the operator's **CA backend** — recipient of the
  certificate-lifecycle operations (issue, renew, revoke) and the
  emitter of the certificate-metadata the workflow records against;
- the operator's **provisioning control plane** — recipient of the
  encryption-enforcement gate decision record; the actual admission
  or blocking of the workload is discharged by that control plane
  against the emitted decision (the workflow itself is read-and-
  decide);
- the operator's **evidence store** — primary recipient of the
  dated lifecycle-attestation record (the audit-evident artifact
  NIS2 Art. 21(2)(h) reviewers read on the write side);
- the operator's **cryptography owner** along their pre-bound
  channel — receives the lifecycle-attestation reference via the
  notify-crypto-owner step.

No external processor is invoked by the default configuration; the
KMS backend, the CA backend, the storage-encryption backend, the
TLS-endpoint backend, the evidence store, and the notification
channel are all operator-bound infrastructure.

## 5. Retention

Not applicable for personal data. For completeness, the dated
lifecycle-attestation record is retained as the operator's NIS2
Art. 21(2)(h) write-side evidence under the operator's regulatory-
retention overlay; the retention mechanism is the evidence-bundle
expiry rule shared with the other evidence streams under
`schemas/evidence/bundle.schema.json`. This workflow does not
maintain its own retention schedule.

The key-lifecycle and certificate-lifecycle records the workflow
produces sit alongside the attestation under the same retention
overlay; the per-key algorithm / lifecycle-timestamp fields and the
per-certificate issuer / not-before / not-after / renewal / revocation
fields are operational measurements of operator cryptographic
infrastructure, not subject records.

Cryptographic material itself (private keys, unwrapped key material)
is retained inside the operator's KMS backend under that backend's
own retention rules — the workflow references keys by identifier
and never persists key material outside the KMS.

## 6. Cross-border transfers

**No transfer.** The default configuration runs the policy-inventory
resolution, the key-lifecycle branch, the encryption-enforcement
gate evaluation, the certificate-lifecycle branch, the lifecycle-
evidence emission, and the notify dispatch entirely against
operator-bound, EU-resident endpoints (the operator's policy store,
KMS backend, storage-encryption backend, TLS-endpoint backend, CA
backend, evidence store, and notification channel). No public-
cloud-AI dependency is wired on the workflow's hot path. Operators
MAY swap in a non-EU-hosted KMS backend, CA backend, evidence store,
or notification channel; doing so is visible on a fork of this
data-flow doc, but is not the default and is not the configuration
the framework ships.

The keys and certificates the workflow manages may protect
cross-border traffic governed by Chapter V on the production-side
workflows that use them, but the lifecycle-management discipline
this playbook operates does not itself cross a Chapter V boundary —
the lifecycle records key and certificate identifiers, not the
payloads the keys and certificates ultimately protect.

## 7. Data subject rights

Not applicable — no personal data processed, no data subject to
exercise a right against this workflow. Subject Access Requests,
rectification requests, erasure requests, and objections that bear
on the contents the operator's cryptography protects are answered
against the operator's production-side workflows that own the
subject data; the cryptographic_controls playbook neither creates a
new subject record nor holds a copy of one that a subject could
exercise rights against independently.

The dated lifecycle-attestation record names keys, certificates,
and workloads by identifier; it carries no subject-identifier
fields.

## 8. Outbound personal-data transfer

**No outbound personal-data transfer — N/A.** Per §3, the workflow
processes cryptographic-material metadata, enforcement-gate
decisions, and attestation records; no category of natural person
is the subject of the processing, so no Chapter V outbound leg
exists.

The non-personal-data outbound legs documented elsewhere (KMS
backend and CA backend operations in §4, evidence-store publication
in §4, provisioning-control-plane decision delivery in §4,
crypto-owner notification in §4) do not engage Chapter V because
their payloads carry no personal data: the lifecycle records name
keys, certificates, and workloads by identifier and the notification
carries the attestation reference along an operator-bound channel.

Cross-reference §6: the workflow-as-a-whole cross-border scoring is
**no transfer** and this §8 carries no contradicting leg.

If a future binding wires a non-EU-hosted KMS backend or CA backend,
an attestation field that captures payload excerpts from any
protected workload, or any other surface that introduces personal
data into the lifecycle-management discipline, this section MUST be
re-scored against the canonical four-axis shape (destination class,
transfer mechanism, EU-residency posture, data minimisation) and §3
amended in the same change.
