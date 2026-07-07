# cryptographic_controls — cookbook walkthrough

Write-side cryptography-and-encryption lifecycle under NIS2 Article
21(2)(h), DORA Article 9(2)/(3) (with the JC RTS on ICT risk
management framework, Commission Delegated Regulation (EU) 2024/1774,
Art. 6 on encryption and cryptographic controls), and GDPR Article
32(1)(a) (the encryption limb). The
`playbook.cryptographic_controls@v1` CACAO playbook is the
operator-side write-side materialisation of the NIS2 Art. 21(2)(h)
cryptography-and-encryption obligation: on a declared lifecycle
trigger (a scheduled per-key-class rotation window, a compromise
signal, a certificate-approaching-expiry event, a policy-floor
change), it resolves the declared cryptography policy, discharges
the key-lifecycle branch (generate / rotate / revoke), evaluates the
encryption-enforcement gate against the at-rest and in-transit
conditions the policy names, discharges the certificate-lifecycle
branch (issue / renew / revoke), records a dated lifecycle
attestation to the operator's evidence store, and notifies the
cryptography owner.

The playbook is the write-side lifecycle sibling of the
[`crypto_posture_management`](crypto_posture_management.md) read-only
posture-attestation playbook: both overlays anchor `nis2:art-21-2-h`
and share `__crypto_scope__` / `__policy_inventory_id__` so the
read-side and write-side lifecycles read from the same declared
scope. The posture playbook produces the measurement stream — dated
cryptography-posture attestations plus per-deviation Compliance
Findings — that this playbook's write-side branches then act on;
this playbook produces the material (rotated keys, renewed
certificates, enforcement-gate outcomes, dated lifecycle
attestations) the posture playbook subsequently attests against.

Production state is untouched by the framework itself — every
operator-bound seam (policy store, KMS backend, storage-encryption
backend, TLS-endpoint backend, CA backend, evidence store,
cryptography-owner notification channel) is a runtime seam the
operator wires against their own infrastructure. The algorithm and
key-size floors, per-key-class rotation cadence, TLS-version floor,
declared CA / trust anchors, and expiry buffer the workflow reads
all live in the operator's documented cryptography policy, which the
framework references but does not author.

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the policy
resolution, the key-lifecycle branch outcome, the encryption-
enforcement gate decision, the certificate-lifecycle branch outcome,
the dated lifecycle attestation, and the cryptography-owner
notification land in each target. The operator scenario carried
through the walkthrough is a **scheduled per-key-class rotation
window** — the most common Art. 21(2)(h) discharge in practice —
with the compromise / expiry / policy-change branches noted where
they diverge.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/cryptographic_controls/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / GDPR overlay
└── playbook.cacao.json          # canonical CACAO v2 source (playbook.cryptographic_controls@v1)

content/mappings/nis2/article-21-2-h.yaml
                                  # NIS2 Art. 21(2)(h) inbound anchor — backlinks
                                  # playbook.cryptographic_controls@v1 on `playbook_refs`
                                  # alongside the sibling playbook.crypto_posture_management@v1
content/mappings/dora/article-9-crypto.yaml
                                  # DORA Art. 9(2)/(3) inbound anchor — ICT security policies
                                  # anchored to Commission Delegated Regulation (EU) 2024/1774
                                  # Art. 6 on encryption and cryptographic controls
content/mappings/gdpr/article-32-1-a-encryption-pseudonymisation.yaml
                                  # GDPR Art. 32(1)(a) inbound anchor — encryption limb
                                  # (pseudonymisation limb documented as an out-of-scope gap)
```

The CACAO source is canonical. The six action steps are the
deterministic policy the playbook *means* — a linear chain through
policy resolution, key lifecycle, encryption enforcement, certificate
lifecycle, evidence emission, and owner notification, with the
per-branch outcome (generate / rotate / revoke for keys; issue /
renew / revoke for certificates; permit / deny for the enforcement
gate) recorded on the action's `out_args` rather than routed via a
CACAO `if-condition` node, so the workflow topology stays a single
audit lane regardless of branch. Every branch emits a record — the
key-lifecycle record on step 003, the enforcement-gate outcome on
step 004, the certificate-lifecycle record on step 005 — so
accountability is preserved across the full branch set.

The three worked examples under
`examples/{n8n,temporal,langgraph}/cryptographic_controls/` are the
same playbook compiled into three orchestrator idioms. Everything
else — the policy store, the KMS backend, the storage-encryption
backend, the TLS-endpoint backend, the CA backend, the evidence
store, the cryptography-owner channel — is the operator's data
plane.

## 2. CACAO topology and lifecycle binding

The playbook ships eight steps: one `start`, six `action`, one
`end`. The chain is linear on the workflow edges; the branch
selection on the key-lifecycle and certificate-lifecycle steps
(generate / rotate / revoke; issue / renew / revoke) and the
permit / deny outcome on the enforcement-gate step live *inside*
each action's body rather than on a CACAO `if-condition` node, so
the workflow topology stays a single audit lane regardless of
branch outcome.

| Step suffix | Step                          | Discipline                                                                                                                                                                                                                                                        | Status         |
|-------------|-------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | start (`cryptographic_controls_start`) | edge wiring only — no body                                                                                                                                                                                                                              | n/a            |
| `…000002`   | resolve policy inventory      | resolve the operator's declared cryptography policy for the trigger scope: algorithm floor, key-size floor, per-key-class rotation cadence, TLS-version floor, declared CA / trust anchors, expiry buffer (`__policy_inventory_id__`)                             | operator-bound |
| `…000003`   | key lifecycle                 | dispatch the generate / rotate / revoke branch against the operator's KMS backend for the target key material (`__key_lifecycle_record__`)                                                                                                                        | operator-bound |
| `…000004`   | enforce encryption            | per-workload measurement of the at-rest and in-transit conditions against the declared floors (permit / deny outcome carried on `__enforcement_decision__`); the actual admission or blocking is operator-owned on the provisioning control plane                 | operator-bound |
| `…000005`   | certificate lifecycle         | dispatch the issue / renew / revoke branch against the operator's CA backend for the target certificate material (`__cert_lifecycle_record__`)                                                                                                                    | operator-bound |
| `…000006`   | record lifecycle evidence     | compose and publish the dated cryptographic-controls lifecycle attestation to the operator's evidence store: policy snapshot, key-lifecycle record, enforcement-gate outcome, certificate-lifecycle record (`__attestation_id__`)                                 | operator-bound |
| `…000007`   | notify crypto owner           | deliver the attestation reference to the cryptography owner along the operator's pre-bound channel; write-side lifecycle dispatch — the notification carries the lifecycle record, not a remediation demand                                                       | operator-bound |
| `…000008`   | end (`cryptographic_controls_end`) | edge wiring only — no body                                                                                                                                                                                                                                 | n/a            |

All six action steps carry the CACAO I/O contract (`in_args` /
`out_args`) plus `x_secops_ng` reference bundles (control,
telemetry). One per-trigger execution emits exactly one lifecycle
attestation; the per-branch outcomes on the key-lifecycle,
enforcement-gate, and certificate-lifecycle steps never create a
parallel evidence lane — one trigger, one attestation, one record
per lifecycle branch decided.

> The playbook maturity is CORE on the workflow-local README (this
> EXTEND card lands with the cookbook walkthrough). All three
> reference emitters ship committed artifacts under
> `examples/{n8n,temporal,langgraph}/cryptographic_controls/` with
> deterministic stubs for the operator-bound seams; a sibling
> EXTEND card lands the adapter Protocols under
> `patterns.cryptographic_controls` (KMS backend, CA backend,
> storage-encryption backend, TLS-endpoint backend) and the
> advanced features (HSM-backed key ceremonies, post-quantum
> rollover choreography, per-Member-State CA-trust posture).

## 3. Lifecycle contract — the six action states

The per-trigger payload — the policy snapshot (declared algorithm
floor, key-size floor, per-key-class rotation cadence, TLS-version
floor, declared CA / trust anchors, expiry buffer), the
key-lifecycle record (generate / rotate / revoke branch, target key
class, key material handle, previous-key backreference on the
rotation branch), the enforcement-gate decision (per-workload
at-rest and in-transit condition against the declared floor with a
permit / deny outcome), the certificate-lifecycle record (issue /
renew / revoke branch, target certificate subject, issuer trust
anchor), and the dated lifecycle attestation — is
cryptographic-governance content. Where the affected workload
processes personal data, GDPR Art. 32(1)(a) attaches as a parallel
obligation surface on the encryption limb (see § 4). The framework
treats `__policy_inventory_id__`, `__key_lifecycle_record__`,
`__enforcement_decision__`, `__cert_lifecycle_record__`, and
`__attestation_id__` as opaque operator-assigned identifiers.

**resolve policy inventory** (`…000002`)
:   Read step. Resolves the operator's declared cryptography policy
    for the trigger scope from the operator's governance policy
    store: algorithm floor (symmetric and asymmetric), minimum key
    sizes, declared per-key-class rotation cadence, TLS-version
    floor, declared CA / trust anchors, and the expiry buffer the
    certificate-lifecycle branch reads. Anchored on OSCAL SC-13
    (Cryptographic Protection) — SC-13 requires the organisation to
    determine the cryptographic uses and to implement the types of
    cryptography required for each use, which is the discipline
    the policy snapshot discharges at the head of the lifecycle.
    Deliberately not D3FEND-pinned: D3FEND v1.0.0 does not carry a
    defensive technique for governance-policy inventory distinct
    from the downstream cryptographic-module or key-takeout
    surface it feeds; the policy snapshot is the upstream of the
    cryptographic-operation discipline rather than the operation
    itself. Missing-policy branch is explicitly modelled — if no
    policy is declared for `__crypto_scope__`, the inventory
    artifact records the missing-policy condition and the
    downstream steps still run so the attestation preserves the
    policy-gap branch (mirrors the read-side sibling
    crypto_posture_management overlay's policy-gap treatment).

**key lifecycle** (`…000003`)
:   Write step. Dispatches the generate / rotate / revoke branch
    against the operator's KMS backend for the target key material.
    Generation instantiates a new key against the algorithm and
    key-size floor carried in `__policy_inventory_id__`; rotation
    replaces an existing key against the per-key-class cadence with
    a backreference to the previous key so the material chain is
    audit-evident; revocation retires a key on compromise, on scope
    exit, or on decommissioning under the operator's key-management
    discipline. Records `__key_lifecycle_record__` — the
    audit-evident output of the key-takeout pass and the write-side
    counterpart the read-side sibling crypto_posture_management
    overlay's rotation-status check reads against. Anchored on
    OSCAL SC-12 (Cryptographic Key Establishment and Management) —
    SC-12 requires the organisation to establish and manage
    cryptographic keys in accordance with organisation-defined
    requirements for key generation, distribution, storage, access,
    rotation, and destruction. D3FEND-pinned to `D3-SKT` (Software
    Key Takeout, Harden tactic): controlled generation, rotation,
    and revocation of cryptographic keys under operator custody is
    exactly the software-key-takeout discipline D3-SKT names. The
    adapter Protocol against the KMS backend is the seam where the
    takeout is actually dispatched; landed on the sibling EXTEND
    adapter-Protocols card under `patterns.cryptographic_controls`.

**enforce encryption** (`…000004`)
:   Gate step. Evaluates the at-rest and in-transit encryption
    conditions on the target workload against the declared floors
    carried in `__policy_inventory_id__`: the at-rest half measures
    the operator's storage-encryption backend engagement on the
    persistent-storage surface, and the in-transit half measures
    the operator's TLS-endpoint backend for negotiated version and
    cipher suite against the declared floor. Records
    `__enforcement_decision__` with the permit / deny outcome and
    the per-condition rationale. Anchored on **two** OSCAL
    controls: SC-28 (Protection of Information at Rest) on the
    at-rest half, and SC-8 (Transmission Confidentiality and
    Integrity) on the in-transit half; SC-8(1) (Cryptographic
    Protection) is satisfied via the cryptographic-floor link to
    SC-13 the policy step resolved. D3FEND-pinned to `D3-CM`
    (Cryptographic Module, Harden / Isolate tactics): the
    enforcement-gate decision measures whether the operator's
    cryptographic module — the storage-encryption backend on the
    at-rest side and the TLS-endpoint backend on the in-transit
    side — is engaged on the pair of conditions the policy names.
    Read-and-decide by contract: the actual admission or blocking
    of the workload is discharged by the operator's provisioning
    control plane against the emitted decision, so the gate
    records the measurement, not the enforcement action itself.
    Compliance Finding (2003) records on the deny branch land on
    the sibling CORE-tier OCSF binding follow-on (currently
    API Activity 6003 is the only OCSF class pinned; the finding
    binding lands on an EXTEND revisit).

**certificate lifecycle** (`…000005`)
:   Write step. Dispatches the issue / renew / revoke branch
    against the operator's CA backend for the target certificate
    material. Issuance produces a new certificate against the
    declared CA / trust anchors in `__policy_inventory_id__`;
    renewal replaces an existing certificate ahead of the declared
    expiry buffer; revocation retires a certificate on compromise
    or scope exit. Records `__cert_lifecycle_record__` — the
    audit-evident output of the certificate-lifecycle pass and the
    write-side counterpart the read-side sibling
    crypto_posture_management overlay's cert-posture probe reads
    against. Anchored on OSCAL SC-17 (Public Key Infrastructure
    Certificates) — SC-17 requires the organisation to issue
    certificates under an organisation-defined certificate policy
    or obtain them from an approved service provider, which is the
    obligation the issue / renew / revoke branches discharge on
    the certificate side of the cryptographic-material inventory.
    Deliberately not D3FEND-pinned: D3FEND v1.0.0 carries
    Certificate Analysis (D3-CA) on the Detect tactic (dated
    examination of certificate properties) but not a distinct
    certificate-issuance / renewal / revocation technique — the
    read-side lane pins D3-CA, and cross-pinning it here would
    misrepresent the write-side as a read-side analysis lane. The
    SC-17 OSCAL anchor carries the discipline instead. Mirrors the
    read-side sibling overlay's per-step pin-where-it-fits /
    document-the-gap pattern.

**record lifecycle evidence** (`…000006`)
:   Attestation step. Composes and publishes the dated
    cryptographic-controls lifecycle attestation to the operator's
    evidence store, carrying the policy snapshot, the key-lifecycle
    record, the enforcement-gate decision, and the
    certificate-lifecycle record. Records `__attestation_id__` on
    the operator's evidence store keyed to `__crypto_scope__` and
    `__policy_inventory_id__`. The attestation is always emitted,
    including the policy-gap branch (missing-policy condition
    recorded rather than skipping the attestation) and including
    the deny branch on the enforcement gate (the deny outcome is
    the audit-evident record). Anchored on OSCAL SC-13 as the
    audit-evident record a reviewer reads against the declared
    cryptographic uses. Deliberately not D3FEND-pinned:
    per-execution attestation emission is an evidence-stream
    discipline rather than a runtime countermeasure or detection
    step — mirrors the `backup_recovery`, `business_continuity`,
    `crypto_posture_management`, `iam_auditor`, and
    `on_call_rotation` evidence-capture gap-note precedents.

**notify crypto owner** (`…000007`)
:   Notification step. Delivers the attestation reference to the
    cryptography owner along the operator's pre-bound channel
    (ticketing queue, chat channel, email alias, policy-owner
    mailbox). Write-side lifecycle dispatch — the notification
    carries the lifecycle record for the cryptography owner's
    accountability posture; it does not itself mutate policy
    state, does not trigger a follow-on rotation, and does not
    escalate the deny branch into the incident-response lane
    (those are downstream disciplines on the operator's own
    surfaces). Deliberately not D3FEND-pinned: notification is a
    delivery discipline, not a defensive technique (mirrors the
    read-side sibling overlay's notify-crypto-owner gap note and
    the `on_call_rotation` handoff-brief gap-note precedent).

The six action steps are operator-bound runtime seams: the
framework ships neither the governance policy store, the KMS
backend, the storage-encryption backend, the TLS-endpoint backend,
the CA backend, the evidence store, nor the cryptography-owner
notification channel. The playbook is the portable description of
*what* the operator's stack should do on each declared lifecycle
trigger; binding those seams to real endpoints is the operator's
job.

> **LM determinism.** Policy resolution, key-lifecycle dispatch,
> encryption-enforcement measurement, certificate-lifecycle
> dispatch, attestation emission, and cryptography-owner
> notification are structured reads and writes against
> operator-owned surfaces, not free-text reasoning steps. The
> playbook binds no DSPy signature — there is no LM-driven step at
> this layer. See [`docs/FOUNDATION.md`](../FOUNDATION.md) § LLM
> determinism. If an operator wires an LM-driven summariser on top
> of the notify-crypto-owner step (rendering the per-branch
> lifecycle record into a per-owner narrative, for instance) as a
> private extension, the framework-wide EU-resident LM endpoint
> guard re-applies the check at process startup — see
> [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 4. Regulatory anchors

**NIS2 Article 21(2)(h)** — policies and procedures regarding the
use of cryptography and, where appropriate, encryption. NIS2
enforcement crossed on 2 July 2026; the cryptography-and-encryption
obligation sits alongside authentication (Art. 21(2)(j)) and access
control on the operator's Art. 21 posture and is among the
audit-evident measures a supervisory authority reads first when
assessing the organisation's technical measures. The
`cryptographic_controls` playbook is the **write-side lifecycle
materialisation of that obligation**: the policy resolution, the
key-lifecycle branch (generate / rotate / revoke), the
encryption-enforcement gate against the declared at-rest and
in-transit floors, the certificate-lifecycle branch (issue / renew
/ revoke), and the dated lifecycle attestation are the audit-evident
discharge of the write-side lane of the clause. The read-side
posture-attestation lane is discharged by the sibling
`crypto_posture_management` playbook. Inbound anchor at
[`content/mappings/nis2/article-21-2-h.yaml`](../../content/mappings/nis2/article-21-2-h.yaml)
(`nis2:art-21-2-h`) backlinks `playbook.cryptographic_controls@v1`
on `playbook_refs` alongside `playbook.crypto_posture_management@v1`.

**DORA Article 9(2)/(3)** — ICT security policies for cryptography.
Regulation (EU) 2022/2554 Art. 9(2) (reinforced by Art. 9(3))
requires financial entities to implement ICT security policies,
procedures, protocols and tools that protect the confidentiality,
integrity and authenticity of data at rest, in use, and in transit.
The Level 2 detail in the Joint Committee RTS on ICT risk management
framework (Commission Delegated Regulation (EU) 2024/1774) Article 6
on encryption and cryptographic controls prescribes a documented
cryptography and encryption policy, algorithm and key-size floors,
the key-management lifecycle, and a periodic review cadence. The
`cryptographic_controls` playbook is the write-side
key-management-lifecycle materialisation of Art. 6: the key-lifecycle
branch discharges the generation / rotation / destruction slice, the
enforcement-gate step discharges the algorithm-and-floor slice on
the deployed workload, and the certificate-lifecycle branch
discharges the PKI-material slice. The periodic-review slice is
discharged on the read side by the sibling
`crypto_posture_management` playbook. Inbound anchor at
[`content/mappings/dora/article-9-crypto.yaml`](../../content/mappings/dora/article-9-crypto.yaml)
(`dora:art-9-crypto`) closes the graph. The vuln-management,
access-management, and authentication slices of the broader Art. 9
protection-and-prevention surface live on their respective siblings
(`dora:art-9-vuln-mgmt`, `dora:art-9-access-mgmt`,
`dora:art-9-authentication`) and are mapped separately to preserve
the atom-per-obligation shape.

**GDPR Article 32(1)(a)** — pseudonymisation and encryption of
personal data as one of the technical-and-organisational measures
the operator implements under Art. 32(1) appropriate to the risk.
Where the affected workload under this lifecycle processes personal
data, the key-lifecycle branch produces the key material against
the declared algorithm and key-size floor, the encryption-
enforcement gate measures the operator's cryptographic module
against the declared at-rest and in-transit floors on personal-data
workloads, the certificate-lifecycle branch produces the certificate
material the TLS floor relies on, and the dated lifecycle
attestation is the audit-evident artifact that makes the encryption
capability evidenced rather than asserted. This playbook is the
**write-side lifecycle anchor for the encryption limb**; the
sibling `crypto_posture_management` overlay pins the read-side
posture-attestation lane on the same clause. Together the two
overlays discharge the encryption limb of Art. 32(1)(a). The
pseudonymisation limb is NOT anchored by this playbook —
cryptographic_controls operates encryption-key and certificate
lifecycle disciplines, not a pseudonymisation transform against
subject data; the pseudonymisation gap is documented in the
inbound anchor's notes section. Inbound anchor at
[`content/mappings/gdpr/article-32-1-a-encryption-pseudonymisation.yaml`](../../content/mappings/gdpr/article-32-1-a-encryption-pseudonymisation.yaml)
(`gdpr:art-32-1-a-encryption`).

**CRA Annex I §1(e) (deferred)** — write-side lifecycle-lane
companion anchor. Regulation (EU) 2024/2847 Annex I §1(e) requires
manufacturers of products with digital elements to protect the
confidentiality of stored, transmitted or otherwise processed data,
including by encrypting relevant data at rest or in transit by
state-of-the-art mechanisms. The read-side posture-attestation lane
is already pinned on
`cra:annex-i-1-e-confidentiality-crypto-posture` via the sibling
`crypto_posture_management` playbook; the write-side lifecycle-lane
companion anchor
`cra:annex-i-1-e-confidentiality-crypto-lifecycle` plus the matching
inbound entry that pins `playbook.cryptographic_controls@v1` into
`content/mappings/cra/` land together on a sibling CRA mapping card
(F-WF-CRYPTOMGMT-CRA-EDGE) so both anchors ship in one PR — see the
`cra:` slot on
[`content/playbooks/cryptographic_controls/mappings.yaml`](../../content/playbooks/cryptographic_controls/mappings.yaml).
§1(d) access control (which includes the key-material and
certificate-lifecycle keys the access-control surface relies on)
and the umbrella §1 essential-cybersecurity anchor remain candidate
secondary anchors on the same CRA card if the reviewer selects them.

**OSCAL controls** exercised by the workflow (from
[`content/playbooks/cryptographic_controls/mappings.yaml`](../../content/playbooks/cryptographic_controls/mappings.yaml)):
SC-12 (Cryptographic Key Establishment and Management — anchors
`key lifecycle`), SC-13 (Cryptographic Protection — anchors
`resolve policy inventory`, the enforcement-gate cryptographic-floor
link, and `record lifecycle evidence`), SC-17 (Public Key
Infrastructure Certificates — anchors `certificate lifecycle`),
SC-28 (Protection of Information at Rest — anchors the at-rest half
of `enforce encryption`), SC-8 (Transmission Confidentiality and
Integrity — anchors the in-transit half of `enforce encryption`;
SC-8(1) Cryptographic Protection is satisfied via the
cryptographic-floor link to SC-13). This SC-family (SC-8, SC-12,
SC-13, SC-17, SC-28) is the standard OSCAL closure the NIST SP
800-53 Rev. 5 catalogue names for a write-side cryptography-and-
encryption lifecycle; the sibling read-side overlay pins the
subset (SC-8, SC-13) applicable to the per-window posture-
attestation lane. A sibling EXTEND card revisits step-level pinning
once the adapter Protocols under `patterns.cryptographic_controls`
are landed.

**MITRE D3FEND v1.0.0** — `D3-SKT` (Software Key Takeout) at
`key lifecycle` and `D3-CM` (Cryptographic Module) at
`enforce encryption`. The Harden and Isolate tactics in D3FEND
v1.0.0 carry the two write-side disciplines this playbook
operates: D3-SKT names the controlled generation, rotation, and
revocation of cryptographic keys under operator custody (the
software-key-takeout discipline the key-lifecycle branch
discharges), and D3-CM names the hardware- or software-backed
cryptographic operations on protected material (the module
engagement the enforcement-gate step measures on the at-rest and
in-transit conditions). The read-side sibling
`crypto_posture_management` lane pins D3-CA (Certificate Analysis)
because its discipline is the dated examination of certificate
properties; the write-side lane here pins D3-CM / D3-SKT because
the discipline is the controlled operation on cryptographic
material rather than the analysis of the result. The
`resolve policy inventory`, `certificate lifecycle`,
`record lifecycle evidence`, and `notify crypto owner` steps are
deliberately NOT D3FEND-pinned, with per-step gap notes in
`mappings.yaml` (governance-policy inventory, PKI-material
lifecycle, attestation-stream emission, and notification-delivery
disciplines respectively). This closure mirrors the read-side
sibling overlay's pin-where-it-fits / document-the-gap pattern.

**OCSF v1.3.0** — `API Activity` (class_uid 6003, category 6
Application Activity), direction `both`, consumed at
`resolve policy inventory` (read calls against the operator's
policy store), at `key lifecycle` (KMS backend calls for the
generate / rotate / revoke branch), at `enforce encryption` (read
calls against the storage-encryption backend for the at-rest
condition and against the TLS-endpoint backend for the in-transit
condition), and at `certificate lifecycle` (CA backend calls for
the issue / renew / revoke branch); emitted at
`record lifecycle evidence` (write call publishing the dated
lifecycle-attestation record to the operator's evidence store) and
at `notify crypto owner` (delivery dispatch to the cryptography
owner's pre-bound channel). The class_uid 6003 binding is
intentional at CORE tier — API Activity is the OCSF v1.3.0
consistent class across the write-side and evidence-side surfaces
this playbook interacts with; a sibling EXTEND card revisits the
class selection (and adds Compliance Finding 2003 on the
enforcement-gate deny branch) once the adapter surfaces are pinned.

## 5. Per-target hand-off

### 5.1 n8n — operator-edited Set rows over the lifecycle topology

`examples/n8n/cryptographic_controls/workflow.n8n.json` carries the
CACAO topology as eight n8n nodes (one `manualTrigger`, six `set`
nodes, one `noOp`), with node ids preserving the CACAO step ids
verbatim. The six action steps emit `n8n-nodes-base.set` nodes
carrying the CACAO I/O contract as editable assignment rows plus the
`x_secops_ng` reference bundles. The per-branch selection on the
key-lifecycle, enforcement-gate, and certificate-lifecycle steps
lives inside each Set row's assignments rather than fanning out as
downstream `n8n-nodes-base.if` nodes — the row carries every
branch's `out_args` shape so the operator wires whichever branch
the trigger scope names against `__key_lifecycle_record__`,
`__enforcement_decision__`, and `__cert_lifecycle_record__`. The
lossy translation is recorded in `meta.secops_ng_notes` so the
integrator sees exactly which seams need attention.

Operators bind the Set rows to their connectors — worked against
the scheduled per-key-class rotation scenario carried through this
walkthrough:

- `resolve policy inventory` → the operator's governance policy
  store (a policy-as-code repository, a GRC platform, a
  cryptography-policy document store); the Set row records
  `__policy_inventory_id__` — the snapshot the subsequent steps
  measure against, including the per-key-class rotation cadence
  the key-lifecycle step reads.
- `key lifecycle` → the operator's KMS backend (an HSM control
  plane, a cloud KMS, an internal key-management system); for the
  scheduled-rotation trigger, the Set row records
  `__key_lifecycle_record__` with the `rotate` branch, the target
  key class, the new key material handle, and the previous-key
  backreference. The compromise-trigger scenario diverges here:
  the Set row records the `revoke` branch instead; the new-
  workload trigger records the `generate` branch.
- `enforce encryption` → the operator's storage-encryption backend
  (per-workload at-rest condition) and TLS-endpoint backend
  (per-workload in-transit condition); the Set row records
  `__enforcement_decision__` — a permit outcome when both
  conditions meet the declared floor, a deny outcome with the
  per-condition rationale otherwise. The operator's provisioning
  control plane consumes the decision and enforces admission /
  blocking downstream.
- `certificate lifecycle` → the operator's CA backend (an internal
  CA, an ACME endpoint, a managed PKI); the Set row records
  `__cert_lifecycle_record__` with the branch (`issue` for new
  subjects, `renew` for expiry-buffer-crossing certificates,
  `revoke` for compromise or scope exit) and the certificate
  material reference.
- `record lifecycle evidence` → the operator's evidence store
  (object store, GRC platform, evidence lake); the Set row records
  `__attestation_id__` carrying the policy snapshot, the
  key-lifecycle record, the enforcement-gate outcome, and the
  certificate-lifecycle record.
- `notify crypto owner` → the operator's cryptography-owner
  channel (ticketing queue, chat channel, email alias,
  policy-owner mailbox).

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/cryptographic_controls/regenerate.sh
```

To import into an n8n instance: open the workflows list, choose
**Import from File**, and select
`examples/n8n/cryptographic_controls/workflow.n8n.json`. The
workflow is inactive by default — review and bind the Set rows to
your own connectors before activating. The emitted workflow is a
*snapshot of intent*, not a runnable playbook.

### 5.2 Temporal — `@activity.defn` bodies

`examples/temporal/cryptographic_controls/workflow.temporal.py` is
a standard Temporal worker module: one `@workflow.defn` class and
one `@activity.defn` function per CACAO action, with the six
action activities documenting their operator-bound seam (policy
inventory, KMS dispatch, at-rest / in-transit gate measurement, CA
dispatch, evidence-store write, notification dispatch). Each
activity documents the canonicalisation and validation contract;
the operator wires the surrounding data-plane call inside the
activity body.

Temporal is the natural fit for the write-side lifecycle
discipline against the scheduled per-key-class rotation scenario:
each declared lifecycle trigger becomes one workflow run; the
per-key-class rotation cadence carried in the policy snapshot can
be realised as a Temporal `Schedule` that fires the workflow on
the operator's declared cadence without a bespoke cron surface;
retries against transient failures on the KMS backend, the CA
backend, or the evidence store get first-class Temporal semantics
(activity retry policy per seam); replay against the same Temporal
event history re-derives the same policy snapshot, the same
key-lifecycle record, the same enforcement-gate decision, the same
certificate-lifecycle record, and the same lifecycle attestation
once the activity bodies are wired against deterministic seams.
The compromise-trigger scenario is a separate schedule (or an
event-signal into a long-running parent workflow); the workflow
code the compiler emits stays pure — every non-deterministic
boundary lives on the activity side of the `@activity.defn` line,
so replay determinism survives the operator's own activity
implementations.

### 5.3 LangGraph — `@tool` wrappers + agentic-extension hook

`examples/langgraph/cryptographic_controls/state_bindings.py`
carries the `TypedDict` state and the `@tool`-decorated action
wrappers. `graph_spec.json` carries the target-neutral topology
(nodes and the linear on-completion edges from resolve-policy-
inventory through notify-crypto-owner to the terminal end, with
the internal per-branch selection on the key-lifecycle,
enforcement-gate, and certificate-lifecycle steps recorded as
state fields rather than conditional edges); `assemble.py` is the
hand-written reference assembly that wires the GraphSpec +
bindings into a `langgraph.graph.StateGraph`. `_audit_mirror.py`
is the dependency-free audit-mirror sibling (see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)).

LangGraph is the agentic target — an operator who wants to layer
an LM-driven enrichment on top of the notify-crypto-owner step
(rendering the per-branch lifecycle record into a per-owner
narrative, for instance) fills that as a private extension. The
framework-wide EU-resident LM endpoint guard re-applies the check
at process startup (`compilers/_shared/lm_endpoint_guard.py`),
with the `SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
The compiler never embeds an LLM SDK.

### 5.4 Cross-target parity

All three reference targets are present in the tree today
(`examples/n8n/cryptographic_controls/`,
`examples/temporal/cryptographic_controls/`,
`examples/langgraph/cryptographic_controls/`). Each ships a
committed emitter artifact (n8n workflow JSON, Temporal worker
module, LangGraph GraphSpec + bindings) with the action bodies
documenting the operator-bound seam and the CACAO I/O contract.
The per-target byte-parity goldens under
`tests/examples/{n8n,temporal,langgraph}/cryptographic_controls/`
pin each per-target artifact against a fresh emitter run from the
canonical CACAO source — the cross-target byte-parity property the
framework relies on.

## 6. Observability — OTel + AuditTrail in every target

Every emitted action opens an OpenTelemetry span and appends an
`AuditRecord` to a context-local `AuditTrail` *before* the
operator-bound seam call or the primitive body. The mirror runs
unconditionally, ahead of any OTLP exporter, so the audit property
holds even when the operator has not configured a collector —
typical for disconnected, sovereign, or air-gapped deployments.

Span attributes use the shared `secops_ng.*` keyspace and are
stable across the three targets:

| Attribute key                | Carries                                              |
|------------------------------|------------------------------------------------------|
| `secops_ng.playbook.id`      | CACAO playbook id (`playbook--7c9d0e1f-…`).          |
| `secops_ng.playbook.version` | Content version pinned in the playbook.              |
| `secops_ng.step.id`          | CACAO step id (`action--52000000-…`).                |
| `secops_ng.step.name`        | Human-readable step label.                           |
| `secops_ng.step.type`        | CACAO step type (`action`, `start`, `end`).          |
| `secops_ng.tool.name`        | Emitted tool / activity / Code-node function name.   |
| `secops_ng.compile.target`   | `n8n` / `temporal` / `langgraph` discriminator.      |

Span boundaries per target:

- **n8n** — the compiled workflow is a snapshot of intent; OTel
  instrumentation is a per-node operator concern documented per
  node-id, not a runtime guarantee of the emitted JSON.
- **Temporal** — workflow span (`workflow.<stable_id>`) at
  workflow entry; activity span (`activity.<step_id>`) on every
  activity body, with retries opening a fresh child span per
  Temporal attempt.
- **LangGraph** — node span (`node.<step_id>`) wrapping every node
  assembled from `graph_spec.json`; tool span (`tool.<step_id>`)
  inside the `@tool` wrapper.

The audit envelope carried per action step names the six operator-
bound seams explicitly: the policy snapshot on step 002, the
key-lifecycle branch outcome on step 003, the enforcement-gate
decision on step 004, the certificate-lifecycle branch outcome on
step 005, the lifecycle attestation reference on step 006, and the
notification reference on step 007. The `__policy_inventory_id__`
correlation key threads through every record so a reviewer can
join the full write-side lifecycle into a single reportable-trigger
ledger.

The OTLP exporter endpoint is operator-supplied
(`OTEL_EXPORTER_OTLP_ENDPOINT`). The compiler never sets a default
and never imports a vendor SDK; pointing the exporter at a managed
APM is a downstream choice the operator owns end-to-end. The
sovereignty posture asks for an EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline.

## 7. Operator customisation points

The playbook is a write-side lifecycle machine; the *policy* it
discharges is the operator's. The customisation seams:

- **Cryptography policy document location.** The
  `resolve policy inventory` step reads the operator's declared
  cryptography policy from wherever it lives (a policy-as-code
  repository, a GRC platform, a policy document store, a wiki
  page rendered to structured content). The framework binds no
  policy source; the operator's governance topology decides where
  the policy lives and how the resolution step reads it.
- **KMS backend.** The `key lifecycle` step dispatches the
  generate / rotate / revoke branch against the operator's KMS
  backend (an HSM control plane, a cloud KMS, an internal key-
  management system). The framework binds the seam via the
  adapter Protocol landed on the sibling EXTEND card under
  `patterns.cryptographic_controls`, not the KMS itself. The
  per-key-class rotation cadence read from the policy snapshot is
  the operator's declared number, bounded by the ENISA
  algorithm-and-key-parameters guidance and by the JC RTS on ICT
  risk management framework Art. 6 cadence discipline.
- **Storage-encryption backend and TLS-endpoint backend.** The
  `enforce encryption` step reads the operator's storage-
  encryption backend on the at-rest half and the operator's
  TLS-endpoint backend on the in-transit half; the framework
  binds neither the surface shape nor the per-workload
  measurement contract (per-workload = per-datastore on the
  at-rest side, per-endpoint on the in-transit side is a common
  default, but the operator's cryptographic-scope catalogue
  decides).
- **CA backend.** The `certificate lifecycle` step dispatches the
  issue / renew / revoke branch against the operator's CA backend
  (an internal CA, an ACME endpoint, a managed PKI). The declared
  CA / trust anchors and the expiry buffer live on the policy
  snapshot; the CA-backend adapter Protocol lands on the sibling
  EXTEND card. Per-Member-State CA-trust posture (which national
  trust anchors are recognised for cross-border service delivery)
  is a candidate advanced feature the same EXTEND card names.
- **Evidence-store retention.** The `record lifecycle evidence`
  step publishes the dated attestation to the operator's evidence
  store; the retention discipline (per-record TTL, immutability
  posture, regulator-query response SLA) is operator-defined and
  documented in the operator's governance surface upstream of
  this workflow. Bounded by NIS2 Art. 21 audit-retention practice
  and by the DORA Art. 12 backup-and-retention discipline where
  transposition applies.
- **Cryptography-owner routing.** The channel the
  `notify crypto owner` step dispatches on (ticketing queue, chat
  channel, email alias, policy-owner mailbox) is the operator's
  decision. The framework binds the notification seam but not the
  channel.

## 8. Replay and audit story

The byte-parity drift guards land under
`tests/examples/{n8n,temporal,langgraph}/cryptographic_controls/`.
Each per-target golden pins the committed worked-example artifact
to a fresh emitter run from the canonical CACAO source; if the
compiler or the playbook changes, regenerate via the per-target
`regenerate.sh` and commit the diff intentionally.

The cross-target replay property is the harder one: the same
declared lifecycle trigger, fed through n8n / Temporal /
LangGraph, produces a byte-identical lifecycle attestation and a
byte-identical set of key-lifecycle / enforcement / certificate-
lifecycle records once each target's activity / tool bodies are
wired against the same operator seams and the same OSCAL / OCSF /
D3FEND reference bundles. The `(__policy_inventory_id__,
__key_lifecycle_record__, __enforcement_decision__,
__cert_lifecycle_record__, __attestation_id__)` tuple is the
string a regulator can diff to confirm the property holds across
targets, and the `__policy_inventory_id__` correlation key is the
join column that threads through every audit record from policy
resolution to notification.

## 9. Playbook chain — where cryptographic_controls sits

The cryptography-and-encryption chain expresses itself as one
write-side lifecycle playbook (this one) that sits alongside the
read-side posture-attestation sibling and hands drift signals into
the infrastructure-posture remediation lane:

```
cryptographic_controls  (write-side lifecycle — generate / rotate / revoke keys,
                          issue / renew / revoke certs, enforce at-rest and
                          in-transit floors, record lifecycle attestation)
    └── lifecycle attestation ─► operator's evidence store
    └── notify crypto owner ─► write-side lifecycle dispatch
                                  ▲
                                  │ measured against
                                  │
crypto_posture_management  (read-side posture-probe, per-window)
    └── posture attestation ─► operator's evidence store
    └── Compliance Finding stream ─► operator's posture-management layer
                                          │
                                          ▼
infra_posture_management (drift remediation)
    └── certificate-drift / floor-violation ─► remediation ticket
```

- **Sibling: `crypto_posture_management`.** The read-side posture-
  attestation lane. The read-side playbook operates a per-window
  measurement of the deployed cryptographic surface (policy
  inventory, cert-posture probe, key-rotation status check); this
  playbook operates the write-side lifecycle branches that
  produce the material the read-side lane attests against. Both
  overlays anchor `nis2:art-21-2-h`, `dora:art-9-crypto`, and
  `gdpr:art-32-1-a-encryption`, and share `__crypto_scope__` /
  `__policy_inventory_id__` so the two lanes read from the same
  declared scope. See
  [`docs/cookbook/crypto_posture_management.md`](./crypto_posture_management.md).
- **Adjacent: `infra_posture_management`.** The configuration-
  drift remediation lane. When the sibling
  `crypto_posture_management` overlay surfaces drift signals
  (expiring certs, TLS-version drift, cipher-suite-below-floor),
  they route to `infra_posture_management` where the operator's
  remediation discipline picks them up. This playbook is the
  write-side counterpart: it operates the lifecycle branches
  under the operator's declared cadence or on a compromise
  trigger, rather than on a drift-remediation ticket. See
  [`docs/cookbook/infra_posture_management.md`](./infra_posture_management.md).

The chain is not code-coupled — each playbook is a standalone
CACAO artifact that can be run in isolation — but the audit
trail's coherence across the workflows is the sovereign-security
property the framework guarantees.

## 10. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys for the
  policy store, the KMS backend, the storage-encryption backend,
  the TLS-endpoint backend, the CA backend, the evidence store, or
  the cryptography-owner channel. Connectors are operator-bound at
  runtime against environment variables documented per target.
- **Policy authorship.** The playbook operates the write-side
  lifecycle discipline; it does not author the algorithm floor,
  the key-size floor, the per-key-class rotation cadence, the
  TLS-version floor, the declared CA / trust anchors, or the
  expiry buffer. Authorship is the operator's governance concern,
  bounded by the ENISA algorithm-and-key-parameters guidance and
  by the JC RTS on ICT risk management framework Art. 6
  discipline.
- **Adapter Protocols under `patterns.cryptographic_controls`.**
  KMS backend, CA backend, storage-encryption backend, and
  TLS-endpoint backend adapter Protocols land on a sibling EXTEND
  card. The CORE tier ships deterministic emitter output with
  documented seams; the adapter binding lands next.
- **HSM-backed key ceremonies.** The scheduled per-key-class
  rotation scenario carried through this walkthrough is the most
  common Art. 21(2)(h) discharge; HSM-backed key ceremonies (with
  quorum sign-off, offline root ceremonies, tamper-evident
  transport) land on the same sibling EXTEND card as an advanced-
  feature slice.
- **Post-quantum rollover choreography.** The multi-cycle
  choreography for algorithm migration (rollout, dual-signing
  windows, deprecation of legacy material) is a candidate advanced
  feature on the same EXTEND card.
- **Per-Member-State CA-trust posture.** Cross-border service
  delivery under the eIDAS trust-list posture (which national
  trust anchors are recognised for which service classes) lands
  on the same EXTEND card once the per-authority trust-list
  surfaces stabilise.
- **CRA write-side companion anchor.** The write-side lifecycle-
  lane companion anchor
  `cra:annex-i-1-e-confidentiality-crypto-lifecycle` (paired with
  the already-pinned read-side
  `cra:annex-i-1-e-confidentiality-crypto-posture` anchor) lands
  on a sibling CRA mapping card (F-WF-CRYPTOMGMT-CRA-EDGE), so the
  read-side and write-side companion anchors ship together.
- **Pseudonymisation limb of GDPR Art. 32(1)(a).** This playbook
  operates the encryption limb of Art. 32(1)(a); the
  pseudonymisation limb is not anchored by any finalized playbook
  in the current framework and is documented as an out-of-scope
  gap in
  [`content/mappings/gdpr/article-32-1-a-encryption-pseudonymisation.yaml`](../../content/mappings/gdpr/article-32-1-a-encryption-pseudonymisation.yaml).
- **Sigma rule ids on the enforcement-gate deny branch.** The
  enforcement-gate deny branch is the upstream of any Sigma
  detection rule an operator's posture-management layer chooses
  to author against at-rest / in-transit floor violations; the
  framework does not pin stable Sigma rule ids on this overlay.

## 11. References

- [`content/playbooks/cryptographic_controls/README.md`](../../content/playbooks/cryptographic_controls/README.md)
  — canonical CACAO source overview and status.
- [`content/playbooks/cryptographic_controls/mappings.yaml`](../../content/playbooks/cryptographic_controls/mappings.yaml)
  — outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / GDPR overlay
  with per-step control anchors and the in-line closure notes for
  the deliberate OSCAL / D3FEND / CRA omissions.
- [`content/mappings/nis2/article-21-2-h.yaml`](../../content/mappings/nis2/article-21-2-h.yaml)
  — NIS2 Article 21(2)(h) inbound anchor (co-anchored with the
  sibling `crypto_posture_management` playbook).
- [`content/mappings/dora/article-9-crypto.yaml`](../../content/mappings/dora/article-9-crypto.yaml)
  — DORA Article 9(2)/(3) inbound anchor (ICT security policies,
  cryptography slice; JC RTS on ICT risk management framework,
  Commission Delegated Regulation (EU) 2024/1774, Art. 6 on
  encryption and cryptographic controls).
- [`content/mappings/gdpr/article-32-1-a-encryption-pseudonymisation.yaml`](../../content/mappings/gdpr/article-32-1-a-encryption-pseudonymisation.yaml)
  — GDPR Article 32(1)(a) inbound anchor (encryption limb;
  pseudonymisation limb documented as an out-of-scope gap).
- [`docs/cookbook/crypto_posture_management.md`](crypto_posture_management.md)
  — sibling read-side posture-attestation cookbook (per-window
  measurement lane; both anchor NIS2 Art. 21(2)(h), DORA
  Art. 9(2)/(3), and GDPR Art. 32(1)(a) encryption limb).
- [`docs/cookbook/infra_posture_management.md`](infra_posture_management.md)
  — adjacent cookbook (configuration-drift remediation lane;
  consumes drift signals from the sibling read-side overlay).
- [`examples/n8n/cryptographic_controls/README.md`](../../examples/n8n/cryptographic_controls/README.md)
  — n8n worked-example walkthrough and import instructions.
- [`examples/temporal/cryptographic_controls/README.md`](../../examples/temporal/cryptographic_controls/README.md)
  — Temporal worked-example walkthrough.
- [`examples/langgraph/cryptographic_controls/README.md`](../../examples/langgraph/cryptographic_controls/README.md)
  — LangGraph worked-example walkthrough.
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay
  shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer
  runtime.
