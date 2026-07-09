# GDPR data flow — eidas2_identity_verification

Per-workflow GDPR data-flow entry for the
`eidas2_identity_verification` cookbook playbook
(`playbook.eidas2_identity_verification@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/eidas2_identity_verification/`](../../playbooks/eidas2_identity_verification/).

---

## 1. Purpose

The workflow exists to demonstrate, at the moment a regulated
operator onboards a European Digital Identity Wallet (EUDIW) enabled
principal to a protected access surface, that the presented Person
Identification Data (PID) credential was cryptographically verified
against the EU trust-anchor registry, that the returned Level of
Assurance was mapped to a documented operator-side access tier, and
that a dated audit-evidence artifact was published before any
downstream capability provisioning was triggered. On each run it
issues an EUDIW presentation request against a bounded principal
identifier and access-scope, verifies the returned PID credential
against the declared Member-State Trusted List entry (or its LOTL
aggregator) per Commission Implementing Decision (EU) 2015/1505 as
maintained under eIDAS 2.0, assesses the Level of Assurance,
publishes one identity-verification evidence record projected
through `telemetry.ocsf.account_change@v1`, and hands the verified
principal off to the onboarding_offboarding_tracker workflow. The
purpose is bounded to producing that per-onboarding
identity-verification evidence so an operator can satisfy the
access-control-policy leg of NIS2 Art. 21(2)(i) and the
digital-identity-governance leg of DORA Art. 5 against EUDIW-enabled
principals; the workflow does not retain the presented credential
for analytics, profiling, biometric processing, or model training.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(c) — legal obligation**. Where the
operator is a regulated entity under **NIS2** and is obliged to
implement and evidence human-resources security and access-control
policies under **NIS2 Art. 21(2)(i)** as transposed nationally, or a
financial entity under **DORA Art. 5** obliged to operate a
governance-and-organisation framework for the digital-identity
surface, the per-onboarding identity-verification evidence this
workflow produces is processed to discharge that obligation.
**eIDAS 2.0** (Regulation (EU) 2024/1183) is the sectoral instrument
that authorises the EUDIW presentation transaction itself; the
underlying processing of the PID credential by the operator
(relying party) is grounded in Art. 6(1)(c) read together with the
national law that transposes NIS2 or applies DORA.

Secondary: **GDPR Art. 6(1)(f) — legitimate interests**. An
operator not within scope of a statutory access-management evidence
obligation still has a legitimate interest in continuously
evidencing that access grants against EUDIW-enabled principals were
gated on a cryptographically verified identity attestation and a
documented Level of Assurance; the processing here — issuing a
presentation request, verifying the returned credential, mapping
the Level of Assurance to an access tier, and emitting the dated
evidence record — is necessary and proportionate to that interest.

Special-category data (**Art. 9**) is not the target of the
workflow. The PID credential set defined under eIDAS 2.0 carries
person identification data (family name, given names, date of
birth, unique identifier) but does not by design carry Art. 9
special categories; where an operator's declared authentication
scope explicitly opts in to an EUDIW attribute set that includes an
Art. 9 category (a professional-qualification credential that
happens to reveal trade-union membership, for example), that opt-in
MUST be re-scored against Art. 9(2) before the binding goes live —
it is not the default posture of this workflow.

Biometric verification (holder-to-device binding) is executed on
the wallet-holder's device against the wallet's local secure
element, per ARF v2; the operator does not receive or process the
biometric template, only the resulting holder-binding assertion the
verifier confirms cryptographically.

## 3. Categories of data subjects and personal data

Data subjects:

- **The onboarded principal** — the natural person whose EUDIW is
  presenting the PID credential to the operator as part of the
  onboarding transaction. This is the central data subject for the
  workflow.

Categories of personal data:

- **Person Identification Data (PID)** — the eIDAS 2.0 PID
  attribute set carried on the verified credential referenced by
  `__pid_credential_id__`: family name, given names, date of birth,
  unique identifier, and any additional attributes the operator's
  declared authentication scope requires for the target
  `__auth_scope__`. Personal data by definition.
- **Identity references** — the operator-side principal handle
  carried by `__principal_id__` (a joiner-record correlation id or
  account key), joined to the PID at the verify step.
- **Wallet-transaction metadata** — the presentation-request
  identifier (`__presentation_request_id__`), the holder-binding
  assertion (cnf claim for SD-JWT VC, device-binding record for
  mDoc), and the status-list resolution result from the verify
  step.
- **Assurance metadata** — the Level of Assurance verdict
  (`__loa_verdict__` — high / substantial / low) returned by the
  wallet and confirmed by cryptographic verification, and the
  operator-side access tier (`__access_tier__`) it maps to.
- **Verification outcome** — the boolean verdict
  (`__verification_verdict__`) and the failure-cause label on the
  negative branch (invalid signature, revoked credential,
  holder-binding failure, LoA below scope minimum).
- **Execution metadata** — the per-execution identifier and the
  `__captured_at__` UTC timestamp carried on the emitted audit
  artifact referenced by `__evidence_id__`.

No credential material, factor secret, wallet-side private key, or
biometric template plaintext is read or persisted; the workflow
processes verifier-confirmed references and PID attributes only,
projected through `telemetry.ocsf.account_change@v1`.

## 4. Recipients

Internal recipients:

- The **access-governance / IAM-review function** owning the
  onboarding-side identity-verification attestation — the
  operator's IAM administrators and auditors who consume the
  identity-verification evidence artifacts to evidence that
  EUDIW-gated access grants were preceded by a cryptographically
  verified PID and a documented Level-of-Assurance mapping.
- The **downstream onboarding_offboarding_tracker workflow** — the
  workflow the trigger_access_provisioning step hands the verified
  principal off to for the joiner-side capability-delta
  application; the hand-off carries the principal reference, the
  access tier, and the evidence identifier, not the raw PID
  attributes.

External / processor recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **EU trust-anchor registry** — a Member-State Trusted List
  entry (or the LOTL aggregator per Commission Implementing
  Decision (EU) 2015/1505 as maintained under eIDAS 2.0) resolved
  by the verify_pid_credential step. Read-only against the
  registry; no attribute is written back. The registry surface is
  EU-institutional by definition.
- The **EUDIW verifier** the operator already runs (OpenID4VP
  relying-party surface / ARF v2 verifier) — the wire-protocol
  intermediary between the wallet-holder's device and this
  playbook. Operator-hosted; no SecOps-NG-hosted verifier default.
- The **evidence store** receiving the emitted
  identity-verification artifact. Destination is operator-wired —
  no default non-EU endpoint.
- The **telemetry / SIEM store** receiving the OCSF Account Change
  records emitted during request, verify, assess, and evidence
  emission.

Each operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production;
the framework does not ship the DPAs, but the data-flow record
names the dependency so a sovereignty review can verify it. No
Microsoft / Google EUDIW proxy surface is modelled; the wallet-side
protocol is OpenID4VP / ARF v2 against the operator's own verifier.

## 5. Retention

The workflow itself is stateless — the durable retention horizon is
the operator-owned evidence store and telemetry store:

- The **identity-verification evidence artifact** (principal
  reference + PID attribute subset the operator's scope required +
  LoA verdict + access tier + verification outcome + execution
  metadata) is written to the operator's evidence store and
  inherits that store's retention policy. For continuous-
  attestation use the operator typically retains the per-event
  artifacts for the audit window required by the governing
  regulation (NIS2 / DORA evidence-retention obligations), enforced
  by the store's TTL or evidence-pack expiry.
- **OCSF Account Change records** emitted during request, verify,
  assess, and evidence emission follow the operator's telemetry
  retention policy on the underlying OCSF store.
- The **PID credential itself** (the raw verifiable credential
  received from the wallet) is NOT retained by the workflow beyond
  the verify step: only the verifier-confirmed attribute subset the
  operator's declared scope required is projected into the evidence
  artifact and the OCSF Account Change record; the raw credential
  is dropped after verification. This is the eIDAS 2.0 selective-
  disclosure discipline the wallet-side protocol supports.
- The **wallet-holder's device biometric template** (used for
  holder-to-device binding) is never received by the operator; it
  is processed on the wallet-holder's device against the wallet's
  local secure element, per ARF v2.

No copy of the raw PID credential, the wallet-side private key, or
the biometric template is retained by the workflow.

## 6. Cross-border transfers

**No transfer.** The workflow is designed to execute end-to-end on
the operator's sovereign-hosted runtime (one of the EU-hostable
reference targets — n8n self-host, Temporal self-host, or LangGraph
self-host on Nebul / OVHcloud / Scaleway / Hetzner) with EU-pinned
processor endpoints for the operator-bound verifier, evidence
store, and telemetry-store dependencies. The trust-anchor registry
is EU-institutional by definition (Member-State Trusted Lists and
the LOTL aggregator under Commission Implementing Decision (EU)
2015/1505 as maintained under eIDAS 2.0).

The technical controls that hold this scoring (FOUNDATION
property #3 — sovereignty):

- The reference compile targets are framework-agnostic and run on
  the operator's own sovereign-hosted runtime; no SecOps-NG-hosted
  egress path exists in the workflow.
- The EUDIW verifier the operator wires at
  `request_eudiw_presentation` and `verify_pid_credential` is
  operator-bound at compile time and pinned to an EU-region
  endpoint; no default hosted verifier is bundled.
- The evidence artifact emits to the operator's EU-region-pinned
  evidence store; no external aggregation is invoked.
- No public-cloud-AI endpoint is called during request, verify,
  assess, or evidence emission.
- No Microsoft / Google EUDIW proxy is assumed or defaulted; the
  wallet-side protocol runs directly between the wallet-holder's
  device and the operator's own verifier.

If an operator binds a non-EU verifier, a non-EU evidence store, or
a non-EU telemetry processor at compile time, this scoring breaks —
the operator MUST re-score this section under "transfer under SCCs
/ BCRs / derogation", name the third country and the transfer
instrument, and document the supplementary measures (encryption-at-
rest with operator-held keys, pseudonymisation of the PID attribute
subset before egress) before the binding goes live. Sovereignty
review at compile time is the gate.

## 7. Data subject rights

- **Access (Art. 15).** A Subject Access Request is answered by
  querying the operator's evidence store on the principal
  reference from §3 and the operator's telemetry / OCSF store on
  the same reference across the Account Change records the
  workflow emitted. The workflow introduces no storage location
  beyond those parents; the raw PID credential is not retained (§5).
- **Rectification (Art. 16).** The workflow does not author PID
  attributes — it consumes the credential presented by the
  wallet-holder's own EUDIW. Rectification at the subject's
  request is operationally meaningful only against the upstream
  wallet issuer (a Member-State PID issuer, per eIDAS 2.0); the
  next onboarding presentation reflects the reissued credential.
- **Erasure (Art. 17).** The retention hooks in §5 are the
  operational erasure pathway: ageing the identity-verification
  artifacts and OCSF Account Change records on the operator's
  store TTLs erases the workflow's copy of the metadata. A
  standalone subject-initiated erasure request flows through the
  evidence-store's erasure procedure, which the workflow inherits.
  Where the lawful basis is **Art. 6(1)(c)** legal obligation,
  erasure may be lawfully refused for the statutory
  evidence-retention window.
- **Objection (Art. 21).** Where the lawful basis is
  **Art. 6(1)(f)** legitimate interests, a data subject can object
  on grounds relating to their particular situation; the
  operational handling is to record the objection and route
  onboarding of that principal through a manual identity-review
  procedure rather than the automated verify-and-provision path.
  Where the basis is **Art. 6(1)(c)** legal obligation (most
  regulated operators), Art. 21 objection does not displace the
  obligation but MAY still route through manual review.
- **Automated decision-making (Art. 22).** The workflow's
  Level-of-Assurance to access-tier mapping is a documented
  table-lookup declared by the operator's governance function —
  the workflow does not autonomously score identity risk. The
  verify_pid_credential step is a deterministic cryptographic
  check; the assess_assurance_level step is a deterministic
  table-lookup; the emit_identity_audit_evidence step is a
  deterministic emit. Where the trigger_access_provisioning
  hand-off feeds a downstream automated decision that locks the
  principal out of the target scope without human review (a
  hard-fail on verification_verdict = false), that downstream
  effect MAY qualify as Art. 22 automated decision-making with
  significant effects; the operational discipline is to route
  verification-failure branches through a manual review queue
  before locking the principal out.

## 8. Outbound personal-data transfer

The workflow has three classes of outbound leg that carry personal
data outside the runtime's own process boundary into operator-bound
processors, plus one read-only leg against the EU trust-anchor
registry. Each is scored below against GDPR Chapter V
(Art. 44–49); the EU-residency posture is sovereignty-first by
default per Directive 1, and the operator's compile-time bindings
are the knobs that can break the scoring.

**Leg A — EUDIW verifier read (operator-bound OpenID4VP relying-
party / ARF v2 verifier surface handling the wire-protocol exchange
with the wallet-holder's device).**

- *Destination class.* Processor under GDPR Art. 28 — the
  operator's own EUDIW verifier. No hosted verifier default; no
  vendor SDK bundling; no default non-EU endpoint.
- *Transfer mechanism.* **No transfer.** The default
  sovereign-stack posture pins the verifier to an EU-region
  operator-hosted deployment. The technical control is the
  operator's compile-time endpoint pin on the verifier binding.
- *EU-residency posture.* Default is an EU-resident verifier
  under an Art. 28 DPA (or operator-owned in-house).  A non-EU
  binding (a US-region hosted verifier SaaS) MUST be re-scored
  under Art. 46 SCCs with supplementary measures (encryption-at-
  rest with operator-held keys, pseudonymisation of the principal
  reference before egress) before the binding goes live.
- *Data minimisation on egress.* The verifier receives the
  presentation request and returns the verifier-confirmed
  attribute subset the operator's declared scope required — the
  eIDAS 2.0 selective-disclosure discipline. Additional PID
  attributes beyond the declared scope are not requested.

**Leg B — Trust-anchor registry read (Member-State Trusted List
entry or LOTL aggregator, per Commission Implementing Decision
(EU) 2015/1505 as maintained under eIDAS 2.0).**

- *Destination class.* Not a processor under Art. 28 — the
  Member-State Trusted List and the LOTL aggregator are
  EU-institutional public-register surfaces published by
  designated Member-State bodies and aggregated by the European
  Commission. Read-only.
- *Transfer mechanism.* **No transfer.** The trust-anchor
  registry is EU-institutional by definition.
- *EU-residency posture.* By eIDAS 2.0 construction — no
  operator-side knob can move this surface off-EU.
- *Data minimisation on egress.* The read carries the issuer
  identifier the verify step resolves; no PID attribute is sent
  outbound to the registry.

**Leg C — Evidence store write (operator-bound durable store for
the emitted identity-verification audit-evidence artifact).**

- *Destination class.* Processor under GDPR Art. 28 — the
  operator's evidence store. No default endpoint ships with the
  framework.
- *Transfer mechanism.* **No transfer.** The default
  sovereign-stack posture pins the evidence store to an
  EU-region object store or sovereign archive. The technical
  control is the operator's compile-time region pin on the
  evidence-store binding.
- *EU-residency posture.* Default is an EU-resident store under
  an Art. 28 DPA. A non-EU binding MUST be re-scored under
  Art. 46 SCCs with supplementary measures (encryption-at-rest
  with operator-held keys, pseudonymisation of the PID
  attribute subset before egress) before the binding goes live.
- *Data minimisation on egress.* The artifact carries the
  principal reference, the LoA verdict, the access tier, the
  verification outcome, and the PID attribute subset the
  operator's declared scope required; the raw credential is not
  written.

**Leg D — Telemetry / SIEM store write (OCSF Account Change
records emitted during request, verify, assess, and evidence
emission).**

- *Destination class.* Processor under GDPR Art. 28 — the
  operator's telemetry / SIEM store. No default endpoint ships
  with the framework.
- *Transfer mechanism.* **No transfer.** The default
  sovereign-stack posture pins the telemetry store to an
  EU-region SIEM or sovereign log-archive. The technical
  control is the operator's compile-time region pin on the
  telemetry-store binding.
- *EU-residency posture.* Default is an EU-resident telemetry
  store under an Art. 28 DPA. A non-EU binding MUST be re-scored
  under Art. 46 SCCs with supplementary measures (encryption-at-
  rest with operator-held keys, pseudonymisation of the
  principal reference before egress) before the binding goes
  live.
- *Data minimisation on egress.* OCSF Account Change records
  carry the principal reference, the presentation-request
  identifier, the LoA verdict, the access tier, and the
  verification outcome as enumerated in §3; the raw PID
  credential and any wallet-side private key material are not
  written.

The §6 cross-border scoring as a whole is **no transfer** —
consistent with all four legs above scoring no-transfer under the
default sovereign-stack posture. Any operator re-scoring of a leg
here MUST be reflected in §6 in the same change so the two
sections do not disagree.
