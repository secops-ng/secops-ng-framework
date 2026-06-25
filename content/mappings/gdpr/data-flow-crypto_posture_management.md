# GDPR data flow — crypto_posture_management

Per-workflow GDPR data-flow entry for the `crypto_posture_management`
cookbook playbook (`playbook.crypto_posture_management@v1`). Filled
in against [`_data-flow-template.md`](./_data-flow-template.md).
Together the seven sections below form the Art. 30 Record of
Processing Activity entry for this workflow.

Workflow source of truth:
[`content/playbooks/crypto_posture_management/`](../../playbooks/crypto_posture_management/).

---

## 1. Purpose

The workflow exists to exercise the operator's cryptography &
encryption posture surface required by NIS2 Art. 21(2)(h): inventory
the declared cryptography policy at the start of the posture window
(algorithm floor, key-size floor, declared key-rotation cadence per
key class, TLS-version floor), probe the certificate posture of
declared TLS endpoints (validity, chain, expiry, negotiated TLS
version, negotiated cipher suite), check key-rotation cadence against
the documented rotation schedule, capture a dated posture-attestation
artifact, and notify the cryptography owner. The purpose is bounded
to that exercise decision and the metric hooks it produces
(`kri.expiring_tls_certs@v1`, `kri.overdue_key_rotations@v1`); the
workflow does not author the operator's cryptography policy itself,
does not perform key rotations, and does not connect to endpoints
beyond the read-only handshake required for the posture probe.

## 2. Lawful basis

**Out of scope: no personal data processed in this workflow.**

The workflow operates on cryptography-posture metadata, not on the
contents of any data the operator's cryptography protects. The
fields it reads and writes are: cryptography-policy snapshots
(algorithm floors, key-size floors, rotation cadences, TLS-version
floors), endpoint identifiers and their negotiated TLS handshake
parameters, key identifiers and their last-rotation timestamps,
posture-attestation identifiers, and the cryptography owner's
pre-bound channel identifier. None of these carry personal data
within the meaning of GDPR Art. 4(1): the workflow exercises the
posture-readiness of the cryptography surface, it does not process
the personal-data payload that surface may protect.

The personal data that traverses TLS endpoints in production, or
sits at rest under operator-managed keys, has a lawful basis on the
production-side workflows that operate that data — not on this
posture-exercise playbook. This workflow is the periodic-testing
discipline that GDPR Art. 32 (security of processing) and NIS2 Art.
21(2)(h) require operators to run against their cryptography surface;
it does not introduce a new processing purpose against subject data.

If a future revision of this workflow extends scope to inspect
payload contents (for example, to validate per-record encryption at
rest by reading restored records), this section MUST be revisited
and a real lawful basis declared before that extension ships.

## 3. Categories of data subjects and personal data

Not applicable — no personal data processed. The workflow operates
on cryptography-policy metadata, TLS-handshake parameters, key-
rotation timestamps, and attestation records. No category of natural
person is the subject of the processing.

For completeness: the cryptography owner's pre-bound channel
identifier (ticketing system, chat thread, email) is a contact
endpoint, not a data-subject record — the notify-crypto-owner step
delivers an attestation reference along that channel and does not
introduce or retain a per-subject record beyond what the operator's
notification surface already holds independently.

## 4. Recipients

Not applicable for personal data. For completeness, the recipients
of the non-personal posture-evidence data the workflow emits are:

- the operator's **evidence store** — primary recipient of the
  dated posture-attestation record (the audit-evident artifact
  NIS2 Art. 21(2)(h) reviewers read);
- the operator's **cryptography owner** along their pre-bound
  channel — receives the attestation reference via the
  notify-crypto-owner step;
- the **catalogue metric pipeline** that reads
  `kri.expiring_tls_certs@v1` and `kri.overdue_key_rotations@v1`
  from the emitted records for programme-level rollup (handled by
  the sibling `executive_metrics` workflow).

No external processor is invoked by the default configuration; the
policy store, the certificate endpoints, the key-management surface,
the evidence store, and the notification channel are all operator-
bound infrastructure.

## 5. Retention

Not applicable for personal data. For completeness, the dated
posture-attestation record is retained as the operator's
NIS2 Art. 21(2)(h) evidence under the operator's regulatory-
retention overlay; the retention mechanism is the evidence-bundle
expiry rule shared with the other evidence streams under
`schemas/evidence/bundle.schema.json`. This workflow does not
maintain its own retention schedule.

The certificate-posture probe records and key-rotation status
artifacts the workflow produces sit alongside the attestation under
the same retention overlay; the per-endpoint negotiated-handshake
parameters and per-key last-rotation timestamps the probe surfaces
are operational measurements of operator infrastructure, not subject
records.

## 6. Cross-border transfers

**No transfer.** The default configuration runs the policy-inventory
step, the cert-posture probe, the key-rotation check, the evidence-
capture emission, and the notify dispatch entirely against operator-
bound, EU-resident endpoints (the operator's policy store,
declared TLS endpoints, key-management surface, evidence store, and
notification channel). No public-cloud-AI dependency is wired on the
workflow's hot path. Operators MAY swap in a non-EU-hosted evidence
store or notification channel; doing so is visible on a fork of this
data-flow doc, but is not the default and is not the configuration
the framework ships.

Even where the TLS endpoints the probe inspects terminate cross-
border traffic governed by Chapter V on the production-side
workflows, the posture-exercise discipline this playbook operates
does not itself cross a Chapter V boundary — the probe is read-only
and the handshake parameters surfaced are not subject records.

## 7. Data subject rights

Not applicable — no personal data processed, no data subject to
exercise a right against this workflow. Subject Access Requests,
rectification requests, erasure requests, and objections that bear
on the contents the operator's cryptography protects are answered
against the operator's production-side workflows that own the
subject data; the crypto_posture_management playbook neither creates
a new subject record nor holds a copy of one that a subject could
exercise rights against independently.

The dated posture-attestation record names endpoints by identifier
and keys by identifier; it carries no subject-identifier fields.

## 8. Outbound personal-data transfer

**No outbound personal-data transfer — N/A.** Per §3, the workflow
processes cryptography-policy metadata, TLS-handshake parameters,
key-rotation timestamps, and attestation records; no category of
natural person is the subject of the processing, so no Chapter V
outbound leg exists.

The non-personal-data outbound legs documented elsewhere (evidence-
store publication in §4, crypto-owner notification in §4, the
catalogue-metric pipeline rollup in §4) do not engage Chapter V
because their payloads carry no personal data: the attestation
record names the cryptography surface by identifier and the
notification carries the attestation reference along an
operator-bound channel.

Cross-reference §6: the workflow-as-a-whole cross-border scoring is
**no transfer** and this §8 carries no contradicting leg.

If a future binding wires a non-EU-hosted evidence store, an
attestation field that captures payload excerpts from any inspected
endpoint, or any other surface that introduces personal data into
the posture-exercise discipline, this section MUST be re-scored
against the canonical four-axis shape (destination class, transfer
mechanism, EU-residency posture, data minimisation) and §3 amended
in the same change.
