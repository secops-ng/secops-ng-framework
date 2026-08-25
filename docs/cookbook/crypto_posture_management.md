# crypto_posture_management — cookbook walkthrough

Cryptography and encryption posture management under NIS2 Article
21(2)(h), DORA Article 9(2)/(3) (with the JC RTS on ICT risk
management framework, Commission Delegated Regulation (EU) 2024/1774,
Art. 6 on encryption and cryptographic controls), and CRA Annex I
§1(e). The `playbook.crypto_posture_management@v1` CACAO playbook
operates the per-window measurement discipline the operator's
declared cryptography policy owes: it inventories the declared
policy and the assets in its scope, probes the certificate posture
of declared TLS endpoints against the policy floor, checks the
key-rotation cadence of managed keys against the declared schedule,
publishes a dated cryptography-posture attestation to the operator's
evidence store, and notifies the cryptography owner.

The playbook is the **read-only posture-probe materialisation** of
the cryptography and encryption obligation. It operationalises a
cryptography policy that lives on the operator's governance surface —
which algorithms and key sizes are permitted, which TLS versions and
cipher suites are the floor, how often each key class rotates. This
playbook does **not** author that policy, does not rotate keys, does
not renew certificates, does not push a cipher-suite change, and
does not force a TLS-version upgrade; the standing posture that
determines those bindings belongs on the operator's cryptographic-
governance layer, and the remediation lane belongs on the operator's
change-management surface (drift routed into `infra_posture_management`
where certificate expiry or floor-violation triggers a remediation
ticket). The two lanes are complementary:

```
crypto_posture_management  (per-window posture-probe, read-only)
   └── inventory policy ─► probe cert posture ─► check key rotation
       ─► attest ─► notify crypto owner
                                 │
                                 ▼ Compliance Findings (drift signals)
infra_posture_management   (drift remediation lane)
   └── configuration-drift attestation ─► remediation dispatch
```

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the policy
inventory, the certificate-posture probe, the key-rotation check,
the posture-attestation emission, and the cryptography-owner
notification land in each target.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/crypto_posture_management/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / OCSF / D3FEND / NIS2 / DORA / CRA overlay
└── playbook.cacao.json          # canonical CACAO v2 source (playbook.crypto_posture_management@v1)

content/mappings/nis2/article-21-2-h.yaml
                                  # NIS2 Art. 21(2)(h) inbound anchor —
                                  # policies and procedures regarding
                                  # the use of cryptography and, where
                                  # appropriate, encryption; pins
                                  # control.crypto_policy_inventory@v1,
                                  # control.cert_posture_scan@v1,
                                  # control.key_rotation_evidence@v1,
                                  # kri.expiring_tls_certs@v1, and
                                  # kri.overdue_key_rotations@v1
content/mappings/dora/article-9-crypto.yaml
                                  # DORA Art. 9(2)/(3) inbound anchor —
                                  # ICT security policies anchored to
                                  # the JC RTS on ICT risk management
                                  # framework (Commission Delegated
                                  # Regulation (EU) 2024/1774, Art. 6
                                  # on encryption and cryptographic
                                  # controls)
content/mappings/cra/annex-i-1-e-confidentiality-crypto-posture.yaml
                                  # CRA Annex I §1(e) inbound anchor —
                                  # cryptographic-posture lane of the
                                  # confidentiality of stored,
                                  # transmitted or otherwise processed
                                  # data obligation
```

The CACAO source is canonical. The five action steps and the one
`start` / one `end` wiring node are the deterministic policy the
playbook *means* — a linear inventory → probe → check → attest →
notify chain with no conditional branching at the workflow layer.
The three worked examples under
`examples/{n8n,temporal,langgraph}/crypto_posture_management/` are
the same playbook compiled into three orchestrator idioms.
Everything else — the policy store the inventory step reads, the TLS
endpoints the certificate-posture probe examines, the key-management
surface the rotation check walks, the evidence store the attestation
step publishes to, and the cryptography-owner channel the
notification step delivers on — is the operator's data plane.

## 2. CACAO topology and lifecycle binding

The playbook ships seven steps: one `start`, five `action`, and one
`end`. The topology is a linear inventory-probe-check-attest-notify
chain — no if-condition step at the workflow layer; the deviation
classification lives in the Compliance Finding (class_uid 2003)
records emitted by the probe-cert-posture and check-key-rotation
steps.

| Step suffix | Step                          | Discipline                                                                                                                                                                                                                                              | Status         |
|-------------|-------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | crypto_posture_management_start | edge wiring only — no body                                                                                                                                                                                                                            | n/a            |
| `…000002`   | inventory crypto policy        | resolve the operator's declared cryptography policy at the start of the posture window: algorithm floor, key-size floor, per-key-class rotation cadence, TLS-version floor, and the set of in-scope endpoints / key-management surfaces / datasets-at-rest enumerated in `__crypto_scope__` | operator-bound |
| `…000003`   | probe cert posture             | per-endpoint read-only examination of certificate validity and chain, days-to-expiry, negotiated TLS version, negotiated cipher suite, and presence of mandated extensions against the floors carried in the policy-inventory snapshot                    | operator-bound |
| `…000004`   | check key rotation             | per-key comparison of last-rotation timestamp against the declared per-key-class cadence carried in the policy-inventory snapshot; keys with no declared cadence are reported as policy gaps rather than overdue rotations                                | operator-bound |
| `…000005`   | evidence capture               | compose and publish the dated cryptography-posture attestation to the operator's evidence store: policy-inventory snapshot, certificate-posture probe, key-rotation status, per-deviation Compliance Findings, top-level gap summary                     | operator-bound |
| `…000006`   | notify crypto owner            | deliver the attestation reference and the gap summary to the cryptography owner along the operator's pre-bound channel; read-only posture-readiness dispatch — no policy mutation, no rotation, no certificate renewal                                    | operator-bound |
| `…000007`   | crypto_posture_management_end  | edge wiring only — no body (posture window closed)                                                                                                                                                                                                    | n/a            |

All five action steps carry the CACAO I/O contract (`in_args` /
`out_args`) plus `x_secops_ng` reference bundles (control,
telemetry). One execution runs the five-step chain (inventory →
probe → check → attest → notify) exactly once per declared posture
window. Per-window metric accounting into the
`kri.expiring_tls_certs@v1` and `kri.overdue_key_rotations@v1`
catalogue entries is unambiguous.

> The playbook maturity is `stable` at `content_version` 1.0.0,
> graduated under the Maturity ladder (all five action steps carry
> deterministic primitive bindings). The mappings overlay pins the control and
> telemetry surface (OSCAL SC-13 / SC-8, D3FEND D3-CA on the probe
> and rotation halves, OCSF API Activity and Compliance Finding);
> the n8n, Temporal, and LangGraph reference emitters ship
> deterministic emitter output under
> `examples/{n8n,temporal,langgraph}/crypto_posture_management/`.
> Cross-target byte-parity goldens live under
> `tests/examples/{n8n,temporal,langgraph}/crypto_posture_management/`.

## 3. Lifecycle contract — the five action states

The per-window payload — the policy-inventory snapshot (declared
algorithm floor, key-size floor, per-key-class rotation cadence,
TLS-version floor, in-scope endpoints and key-management surfaces),
the certificate-posture probe artifact (per-endpoint record of
certificate validity, days-to-expiry, negotiated TLS version,
negotiated cipher suite, mandated-extension presence — sorted by
`endpoint_id`), the key-rotation status artifact (per-key record of
last-rotation timestamp, declared cadence, overdue-by-days — sorted
by `key_id`), per-deviation Compliance Findings, and the dated
cryptography-posture attestation record — is cryptographic-governance
content. The personal-data surface on this playbook's own telemetry
is thin: endpoint identifiers and key identifiers are technical
resource references rather than subject identifiers. The GDPR Art. 30
Record of Processing Activity for the cryptography-owner notification
processing is filed alongside the sibling playbook overlays; the
notification recipient identifier is the only subject-identifier
adjacent field, and it is aggregated to the crypto-owner role rather
than the per-recipient level.

**inventory crypto policy** (`…000002`)
:   Read step. Resolves the operator's declared cryptography policy
    at the start of the posture window: algorithm floor (symmetric
    and asymmetric), minimum key sizes, declared per-key-class
    rotation cadence, TLS-version floor, and the set of in-scope
    endpoints / key-management surfaces / datasets-at-rest
    enumerated in `__crypto_scope__`. Anchored on OSCAL SC-13
    (Cryptographic Protection) — the per-window measurement of the
    declared cryptographic uses SC-13 requires the operator to
    determine. The step is deliberately **not** D3FEND-pinned:
    D3FEND v1.0.0 does not carry a defensive technique for
    governance-policy inventory distinct from the downstream
    configuration- or certificate-analysis surface it feeds; the
    policy snapshot is the *upstream* of the dated-examination
    discipline rather than the examination itself (mirrors the
    `infra_posture_management` collect-posture gap-note precedent).
    Binds against the operator's governance policy store; emits
    `__policy_inventory_id__` — the snapshot the subsequent steps
    measure against. The playbook does NOT author the policy; if
    no policy is declared for `__crypto_scope__`, the inventory
    artifact records the missing-policy condition explicitly and
    the downstream steps still run so the attestation preserves the
    policy-gap branch.

**probe cert posture** (`…000003`)
:   Read step. Probes the certificate posture of the TLS endpoints
    enumerated in `__crypto_scope__` against the floors carried in
    `__policy_inventory_id__`: certificate validity and chain,
    days-to-expiry, negotiated TLS version, negotiated cipher
    suite, and presence of mandated extensions. Anchored on OSCAL
    SC-8 (Transmission Confidentiality and Integrity) — the per-
    endpoint record is the per-window evidence that the
    transmission-protection capability matches the declared posture;
    the cryptographic-floor link to SC-13 satisfies SC-8(1)
    (Cryptographic Protection). D3FEND-pinned to D3-CA (Certificate
    Analysis): dated per-endpoint examination of certificate
    properties against the operator's declared cryptography policy
    — same technique as adversary-attribution Certificate Analysis,
    posture-readiness scope rather than attribution scope. Binds
    against the operator's certificate-endpoint surface; emits
    `__cert_posture_id__`. Read-only and side-effect-free: no
    connection coercion, no downgrade, no renewal. Feeds
    `kri.expiring_tls_certs@v1`.

**check key rotation** (`…000004`)
:   Read step. Walks the key-management surfaces enumerated in
    `__crypto_scope__` and, for each managed key, compares the
    last-rotation timestamp against the per-key-class cadence
    carried in `__policy_inventory_id__`. Emits per-key records
    (key id, key class, last rotation, declared cadence,
    overdue-by-days). Keys with no declared cadence in the policy
    snapshot are reported as **policy gaps** rather than overdue
    rotations; the distinction is preserved so the attestation
    surfaces the policy-side and operations-side gaps separately
    (atom-per-deviation shape). Anchored on OSCAL SC-13 alongside
    the policy-inventory step. D3FEND-pinned to D3-CA on the
    adjacent dated-examination of the same cryptographic-material
    inventory the probe-cert-posture step examines on the transport
    side (D3FEND v1.0.0 does not carry a distinct cryptographic-
    key-analysis technique separate from Certificate Analysis).
    Binds against the operator's key-management surface; emits
    `__rotation_status__`. Read-only: the playbook does NOT
    perform rotations. Feeds `kri.overdue_key_rotations@v1`.

**evidence capture** (`…000005`)
:   Attestation step. Composes and publishes the dated cryptography-
    posture attestation to the operator's evidence store, carrying
    the policy-inventory snapshot, the certificate-posture probe
    artifact, the key-rotation status artifact, the per-deviation
    Compliance Findings, and the top-level gap summary
    (missing-policy, expiring-certs, overdue-rotations counts).
    Anchored on OSCAL SC-13 — the audit-evident record a reviewer
    reads against the declared cryptographic uses. Deliberately NOT
    D3FEND-pinned: per-execution attestation emission is an
    evidence-stream discipline rather than a runtime countermeasure
    or detection step. Binds against the operator's evidence store;
    emits `__attestation_id__`. The attestation is always emitted,
    including the policy-gap branch (which records the missing-
    policy condition rather than skipping the attestation). The
    playbook does not decide the evidence-store technology (object
    store, GRC platform, evidence lake); the operator binds the
    seam.

**notify crypto owner** (`…000006`)
:   Notification step. Delivers the attestation reference and the
    gap summary to the cryptography owner along the operator's
    pre-bound channel (ticketing queue, chat channel, email alias,
    policy-owner mailbox). Read-only posture-readiness dispatch —
    the notification does not mutate policy state, does not rotate
    keys, does not renew certificates, and does not escalate the
    deviations into the incident-response lane; the cryptography
    owner receives the summary and drives remediation off the
    operator's own cadence. Deliberately NOT D3FEND-pinned:
    notification is a delivery discipline, not a defensive
    technique (mirrors the `on_call_rotation` handoff-brief
    gap-note precedent).

The five action steps are operator-bound runtime seams: the
framework ships neither the policy store, the certificate-endpoint
surface, the key-management surface, the evidence store, nor the
cryptography-owner notification channel. The playbook is the
portable description of *what* the operator's stack should do per
posture window; binding those seams to real endpoints is the
operator's job.

> **LM determinism.** Policy inventory, certificate-posture probing,
> key-rotation checking, attestation emission, and cryptography-
> owner notification are structured reads and writes against
> operator-owned surfaces, not free-text reasoning steps. The
> playbook binds no DSPy signature — there is no LM-driven step at
> this layer. See [`docs/FOUNDATION.md`](../FOUNDATION.md) § LLM
> determinism. If an operator wires an LM-driven enrichment on top
> of the notify-crypto-owner step (rendering the per-endpoint
> expiring-cert / weak-cipher / overdue-rotation Compliance Finding
> stream into a per-owner narrative, for instance) as a private
> extension, the framework-wide EU-resident LM endpoint guard
> re-applies the check at process startup — see
> [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 4. Regulatory anchors

**NIS2 Article 21(2)(h)** — policies and procedures regarding the
use of cryptography and, where appropriate, encryption. NIS2
enforcement crossed on 2 July 2026; the cryptography-and-encryption
obligation sits alongside authentication (Art. 21(2)(j)) and access
control on the operator's Art. 21 posture and is among the
audit-evident measures a supervisory authority reads first when
assessing the organisation's technical measures. The
crypto_posture_management playbook is the **per-window
materialisation of that obligation's measurement and attestation
surface**: the policy-inventory snapshot, the certificate-posture
probe, the key-rotation status check, and the dated posture-
attestation record are the audit-evident discharge of the clause.
Inbound anchor at
[`content/mappings/nis2/article-21-2-h.yaml`](../../content/mappings/nis2/article-21-2-h.yaml)
(`nis2:art-21-2-h`) backlinks `playbook.crypto_posture_management@v1`,
pins `control.crypto_policy_inventory@v1`,
`control.cert_posture_scan@v1`, and
`control.key_rotation_evidence@v1`, and pins
`kri.expiring_tls_certs@v1` and `kri.overdue_key_rotations@v1` as
the metrics that trip on cryptographic-posture regressions.

**DORA Article 9(2)/(3)** — ICT security policies for cryptography.
Regulation (EU) 2022/2554 Art. 9(2) (reinforced by Art. 9(3))
requires financial entities to implement ICT security policies,
procedures, protocols and tools that protect the confidentiality,
integrity, and authenticity of data at rest, in use, and in transit.
The Level 2 detail in the Joint Committee RTS on ICT risk management
framework (Commission Delegated Regulation (EU) 2024/1774) Article 6
on encryption and cryptographic controls prescribes a documented
cryptography and encryption policy, algorithm and key-size floors,
the key-management lifecycle, and a periodic review cadence. The
per-window discharge shape here is the same one NIS2 Art. 21(2)(h)
anchors on — the policy-inventory snapshot, the certificate-posture
probe, the key-rotation status check, and the dated posture-
attestation record. Inbound anchor at
[`content/mappings/dora/article-9-crypto.yaml`](../../content/mappings/dora/article-9-crypto.yaml)
(`dora:art-9-crypto`). This is the cryptography slice of the
broader Art. 9 protection-and-prevention surface; the vuln-
management, access-management, and authentication slices live on
their respective siblings (`dora:art-9-vuln-mgmt`,
`dora:art-9-access-mgmt`, `dora:art-9-authentication`) and are
mapped separately to preserve the atom-per-obligation shape.

**CRA Annex I §1(e)** — confidentiality (cryptographic-posture
lane). Regulation (EU) 2024/2847 Annex I §1(e) requires
manufacturers of products with digital elements to protect the
confidentiality of stored, transmitted or otherwise processed data,
including by encrypting relevant data at rest or in transit by
state-of-the-art mechanisms. The crypto_posture_management playbook
is the **cryptographic-posture lane** of the Annex I §1(e) surface:
continuous evidence that the deployed cryptographic surface — TLS
endpoints, cipher suites, key-rotation cadence — remains aligned
with the declared cryptography policy across the support period.
Inbound anchor at
[`content/mappings/cra/annex-i-1-e-confidentiality-crypto-posture.yaml`](../../content/mappings/cra/annex-i-1-e-confidentiality-crypto-posture.yaml)
(`cra:annex-i-1-e-confidentiality-crypto-posture`); companion to
`cra:annex-i-1-confidentiality` in
`annex-i-1-essential-cybersecurity.yaml`, which carries the §1(e)
clause itself.

**OSCAL controls** exercised by the workflow (from
[`content/playbooks/crypto_posture_management/mappings.yaml`](../../content/playbooks/crypto_posture_management/mappings.yaml)):
SC-13 (Cryptographic Protection — anchors the inventory-crypto-
policy, check-key-rotation, and evidence-capture steps; SC-13
requires the organisation to determine the cryptographic uses and
to implement the types of cryptography required for each use, which
is the discipline the policy snapshot and the per-window
measurement discharge) and SC-8 (Transmission Confidentiality and
Integrity — anchors the probe-cert-posture step; SC-8(1)
Cryptographic Protection is satisfied via the cryptographic-floor
link to SC-13, and the per-endpoint TLS-version / cipher-suite
record is the per-window evidence that the transmission-protection
capability matches the declared posture).

**Deliberate OSCAL omissions.** SC-12 (Cryptographic Key
Establishment and Management) is not pinned: SC-12 covers key
generation, distribution, storage, and destruction across the full
lifecycle. This playbook operates the periodic rotation-cadence and
posture-probe slice of that lifecycle only; the key-establishment-
and-management surface itself belongs to the operator's key-
management governance, not to this exercise playbook. SC-17 (Public
Key Infrastructure Certificates) is not pinned: the certificate-
posture probe is read-only and operates downstream of the PKI
surface; SC-17 anchors the PKI governance content, not the per-
window posture check. AU-2 (Event Logging) is not pinned: the
playbook emits OCSF records, but the operator's audit-event policy
is upstream of this playbook.

**MITRE D3FEND v1.0.0** — `D3-CA` (Certificate Analysis) anchors
the probe-cert-posture step as the dated per-endpoint examination
of certificate properties against the operator's declared
cryptography policy, and anchors the check-key-rotation step as the
adjacent dated-examination of the same cryptographic-material
inventory (D3FEND v1.0.0 does not carry a distinct cryptographic-
key-analysis technique separate from Certificate Analysis, so the
rotation check is anchored on D3-CA so the discipline is named
consistently across both halves of the cryptographic-posture
surface). The `d3fend` closure documented in the mappings overlay
records the per-step gap rationale for the other three steps:
inventory-crypto-policy is a governance-surface read against the
operator's declared cryptography policy (the upstream of the
configuration-inventory discipline rather than the inventory
itself); evidence-capture is an attestation-stream emission
discipline rather than a runtime countermeasure or detection step;
notify-crypto-owner is a delivery discipline rather than a
defensive technique. This closure mirrors the gap-note precedent on
`infra_posture_management`, `iam_auditor`, and `on_call_rotation`.

**OCSF v1.3.0** — two class bindings.
`API Activity` (class_uid 6003, category Application Activity),
direction `both`, is consumed at the inventory-crypto-policy step
(read calls against the operator's policy store and the
cryptography-scope catalogue to resolve the policy snapshot), at
the probe-cert-posture step (TLS handshake records against the
declared endpoints — modelled as read-only API activity), and at
the check-key-rotation step (read calls against the key-management
surface for last-rotation timestamps); emitted at the evidence-
capture step (write call publishing the dated posture-attestation
record to the operator's evidence store) and at the notify-crypto-
owner step (delivery dispatch to the cryptography owner's pre-bound
channel). The API Activity records carry the request metadata
`kri.expiring_tls_certs@v1` and `kri.overdue_key_rotations@v1`
read.
`Compliance Finding` (class_uid 2003, category Findings), direction
`emits`, is emitted by the probe-cert-posture and check-key-
rotation steps as the structured per-endpoint and per-key deviation
record the posture-management layer routes to the cryptography
owner and the SIEM queries against — one Compliance Finding per
deviation (expired or short-dated certificate, negotiated TLS
version below the declared floor, negotiated cipher suite below
the declared floor, mandated-extension absence, key past its
declared rotation cadence, key with no declared cadence on the
policy-gap branch). The Compliance Finding stream is the upstream
of any Sigma detection-binding a downstream consumer chooses to
author against expired-cert / weak-cipher / floor-violation /
overdue-rotation rule fingerprints; SecOps-NG does not pin stable
Sigma rule ids on this overlay (the operator's posture-management
layer owns those fingerprints).

## 5. Per-target hand-off

### 5.1 n8n — operator-edited Set rows over the posture-probe topology

`examples/n8n/crypto_posture_management/workflow.n8n.json` carries
the CACAO topology as seven n8n nodes (`manualTrigger`, five `set`
nodes, one `noOp` terminal), with node ids preserving the CACAO
step ids verbatim. The five action steps emit
`n8n-nodes-base.set` nodes carrying the CACAO I/O contract as
editable assignment rows plus the `x_secops_ng` reference bundles
(control, telemetry). The linear sequencing carries via
`on_completion` edges on the emitted `connections` block. The lossy
translations are recorded in `meta.secops_ng_notes` so the
integrator sees exactly which seams need attention.

Operators bind the Set rows to their connectors:

- `inventory crypto policy` → the operator's governance policy
  store (a policy-as-code repository, a GRC platform, a
  cryptography-policy document store) plus the cryptography-scope
  catalogue enumerating the in-scope TLS endpoints, key-management
  surfaces, and datasets-at-rest; writes `__policy_inventory_id__`.
- `probe cert posture` → the operator's certificate-endpoint
  surface (the TLS endpoints enumerated in `__crypto_scope__`) via
  a read-only TLS-handshake probe (an internal certificate-posture
  scanner, a managed certificate-monitoring product, or a scripted
  handshake collector); writes `__cert_posture_id__`.
- `check key rotation` → the operator's key-management surface (an
  HSM control plane, a cloud KMS, an internal key-management
  system) exposing per-key last-rotation timestamp reads; writes
  `__rotation_status__`.
- `evidence capture` → the operator's evidence store (object
  store, GRC platform, evidence lake, or a policy-as-code artifact
  store); writes `__attestation_id__`.
- `notify crypto owner` → the operator's cryptography-owner
  channel (a ticketing queue, a chat channel, an email alias, or a
  policy-owner mailbox).

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/crypto_posture_management/regenerate.sh
```

To import into an n8n instance: open the workflows list, choose
**Import from File**, and select
`examples/n8n/crypto_posture_management/workflow.n8n.json`. The
workflow is inactive by default — review and bind the Set rows to
your own connectors before activating. The emitted workflow is a
*snapshot of intent*, not a runnable playbook.

### 5.2 Temporal — `@activity.defn` bodies

`examples/temporal/crypto_posture_management/workflow.temporal.py`
is a standard Temporal worker module: one `@workflow.defn` class
and one `@activity.defn` function per CACAO action, with the five
action activities documenting their operator-bound seam (inventory /
probe / check / attest / notify). Each activity documents the
canonicalisation and validation contract; the operator wires the
surrounding data-plane call (policy-store read, TLS-handshake
probe, key-management read, evidence-store write, notification
dispatch) inside the activity body.

Temporal is a natural fit for the posture-probe discipline: each
declared posture window becomes one workflow run; retries against
transient failures on the policy store, the certificate-endpoint
surface, the key-management surface, or the evidence store get
first-class Temporal semantics (activity retry policy per seam);
replay against the same Temporal event history re-derives the same
policy-inventory snapshot, the same certificate-posture record, the
same key-rotation status, and the same posture-attestation record.
Schedules (Temporal `Schedule`) give the operator a durable per-
window trigger without a bespoke cron surface.

### 5.3 LangGraph — `@tool` wrappers + agentic-extension hook

`examples/langgraph/crypto_posture_management/state_bindings.py`
carries the `TypedDict` state and the `@tool`-decorated action
wrappers. `graph_spec.json` carries the target-neutral topology
(nodes and the linear on-completion edges from inventory-crypto-
policy through notify-crypto-owner to the terminal end);
`assemble.py` is the hand-written reference assembly that wires the
GraphSpec + bindings into a `langgraph.graph.StateGraph`.

LangGraph is the agentic target — an operator who wants to layer an
LM-driven enrichment on top of the `notify crypto owner` step
(rendering the per-endpoint expiring-cert / weak-cipher / overdue-
rotation Compliance Finding stream into a per-owner narrative, for
instance) fills that as a private extension. The framework-wide
EU-resident LM endpoint guard re-applies the check at process
startup (`compilers/_shared/lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
The compiler never embeds an LLM SDK.

### 5.4 Cross-target parity

All three reference targets are present in the tree today
(`examples/n8n/crypto_posture_management/`,
`examples/temporal/crypto_posture_management/`,
`examples/langgraph/crypto_posture_management/`). Each ships a
committed emitter artifact (n8n workflow JSON, Temporal worker
module, LangGraph GraphSpec + bindings) with the action bodies
documenting the operator-bound seam and the CACAO I/O contract.
Cross-target byte-parity goldens live under
`tests/examples/{n8n,temporal,langgraph}/crypto_posture_management/`.

## 6. Observability — OTel + AuditTrail in every target

Every emitted action opens an OpenTelemetry span and appends an
`AuditRecord` to a context-local `AuditTrail` *before* the operator-
bound seam call or the primitive body. The mirror runs
unconditionally, ahead of any OTLP exporter, so the audit property
holds even when the operator has not configured a collector —
typical for disconnected, sovereign, or air-gapped deployments.

Span attributes use the shared `secops_ng.*` keyspace and are
stable across the three targets:

| Attribute key                | Carries                                              |
|------------------------------|------------------------------------------------------|
| `secops_ng.playbook.id`      | CACAO playbook id (`playbook--…`).                   |
| `secops_ng.playbook.version` | Content version pinned in the playbook.              |
| `secops_ng.step.id`          | CACAO step id (`action--…`).                         |
| `secops_ng.step.name`        | Human-readable step label.                           |
| `secops_ng.step.type`        | CACAO step type (`action`, `start`, `end`).          |
| `secops_ng.tool.name`        | Emitted tool / activity / Code-node function name.   |
| `secops_ng.compile.target`   | `n8n` / `temporal` / `langgraph` discriminator.      |

The OTLP exporter endpoint is operator-supplied
(`OTEL_EXPORTER_OTLP_ENDPOINT`). The compiler never sets a default
and never imports a vendor SDK; pointing the exporter at a managed
APM is a downstream choice the operator owns end-to-end. The
sovereignty posture asks for an EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline.

## 7. Metrics — what the posture-probe discipline exposes

Two KRIs are pinned on the NIS2 Art. 21(2)(h) inbound anchor and
fed by this playbook:

- **`kri.expiring_tls_certs@v1`** — per-window count of TLS
  endpoints in `__crypto_scope__` whose certificate is expired,
  within the operator-declared expiry-warning window, or whose
  negotiated TLS version / cipher suite falls below the declared
  floor. Stamped by the probe-cert-posture step. Rising values
  indicate the certificate posture is drifting behind the declared
  policy; each deviation is captured as a Compliance Finding on
  the emit side.
- **`kri.overdue_key_rotations@v1`** — per-window count of managed
  keys in `__crypto_scope__` whose last-rotation timestamp is past
  the declared per-key-class cadence, plus a separate count of
  keys with no declared cadence (policy gaps reported separately
  from overdue rotations to preserve the atom-per-deviation shape).
  Stamped by the check-key-rotation step. Rising values indicate
  the key-rotation cadence is drifting behind the declared policy.

The catalogue entries pin the field-level read contract; the
framework does not ship a hosted dashboard. Operators dashboard the
KRI series against their own metrics backend. An `EXTEND` sibling
card lands the cipher-suite-floor KPI and rotation-cadence KPI
emitters against the operator's evidence store as the two per-
window observation series a reviewer reads alongside the gap-count
KRIs.

## 8. Detection references — the upstream signal shapes

The playbook does not re-author detection rules. The Compliance
Finding stream emitted by the probe-cert-posture and check-key-
rotation steps is the **upstream of any Sigma rule** a downstream
consumer chooses to author against expired-cert / weak-cipher /
floor-violation / overdue-rotation deviations. Rule fingerprints
are the operator's posture-management-layer concern; SecOps-NG
does not pin stable Sigma rule ids on this overlay.

The rule shapes an operator typically authors against the finding
stream:

- **Expired or short-dated certificate** — a Compliance Finding
  with the certificate-probe key and the expiry-branch; the
  fingerprint is stable per (`__cert_posture_id__`, endpoint-id).
- **Negotiated TLS version below the declared floor** — a
  Compliance Finding with the certificate-probe key and the
  tls-version-below-policy branch; the fingerprint is stable per
  (`__cert_posture_id__`, endpoint-id).
- **Negotiated cipher suite below the declared floor** — a
  Compliance Finding with the certificate-probe key and the
  cipher-suite-below-policy branch; the fingerprint is stable per
  (`__cert_posture_id__`, endpoint-id).
- **Mandated extension absent** — a Compliance Finding on the
  same endpoint granularity with the missing-extension branch.
- **Key past declared rotation cadence** — a Compliance Finding
  stamped at the check-key-rotation step with the overdue branch;
  the fingerprint is stable per
  (`__rotation_status__`, key-id).
- **Key with no declared rotation cadence** — the policy-gap
  branch, reported separately from overdue rotations; the
  fingerprint is stable per (`__rotation_status__`, key-id).

## 9. Operator customisation points

The playbook is a per-window cryptography-posture machine; the
*policy* it exercises is the operator's. The customisation seams:

- **Cryptography policy document location.** The
  `inventory crypto policy` step reads the operator's declared
  cryptography policy from wherever it lives (a policy-as-code
  repository, a GRC platform, a policy document store, a wiki
  page rendered to structured content). The framework binds no
  policy source; the operator's governance topology decides where
  the policy lives and how the inventory step reads it.
- **TLS endpoint list.** The `__crypto_scope__` variable declares
  the TLS endpoints in scope for the probe. The framework binds
  no endpoint list; the operator's cryptography-scope catalogue
  decides the perimeter (which public endpoints, which internal
  service endpoints, which mTLS-mesh endpoints are in scope).
- **Key-rotation schedule source.** The declared per-key-class
  cadence carried in the policy snapshot is the operator's number,
  bounded by the ENISA algorithm-and-key-parameters guidance and
  by the JC RTS on ICT risk management framework Art. 6 cadence
  discipline. The framework never hard-codes a cadence; the
  rotation check trips against whatever the policy declares.
- **Posture-attestation retention.** The `evidence capture` step
  publishes the dated attestation to the operator's evidence
  store; the retention window against that record is the
  operator's declared policy (bounded by NIS2 Art. 21 audit-
  retention practice and by the DORA Art. 12 backup-and-retention
  discipline where transposition applies). The framework binds
  the seam, not the retention.
- **Cryptography-owner routing.** The channel the `notify crypto
  owner` step dispatches on (ticketing queue, chat channel, email
  alias, policy-owner mailbox) is the operator's decision. The
  framework binds the notification seam but not the channel.

## 10. Replay and audit story

The byte-parity drift guards under
`tests/examples/{n8n,temporal,langgraph}/crypto_posture_management/`
each pin the committed worked-example artifact to a fresh emitter
run from the canonical CACAO source; if the compiler or the
playbook changes, regenerate via the per-target `regenerate.sh` and
commit the diff intentionally.

The cross-target replay property is the harder one: the same
policy-store observation, the same certificate-endpoint observation
set, and the same key-management observation set, fed through n8n /
Temporal / LangGraph, produce byte-identical policy-inventory
snapshots, certificate-posture records, key-rotation status
records, Compliance Finding records, *and* byte-identical posture-
attestation records — because the deterministic canonicalisation /
validation / sort contract is stable across the targets. The
`(__policy_inventory_id__, __cert_posture_id__, __rotation_status__,
 __attestation_id__)` tuple is the string an operator can diff to
confirm the property holds across targets.

## 11. Playbook chain — where crypto_posture_management sits

The cryptography-and-encryption chain expresses itself as one
proactive per-window posture probe that sits alongside the sibling
posture-probe playbook (authentication-side) and hands drift signals
into the infrastructure-posture remediation lane:

```
crypto_posture_management  (proactive, per-window posture-probe, read-only)
    └── attestation ─► operator's evidence store
    └── notify crypto owner ─► posture-readiness dispatch
    └── Compliance Finding stream ─► operator's posture-management layer
                                          │
                                          ▼
infra_posture_management (drift remediation)
    └── certificate-drift / floor-violation ─► remediation ticket
```

- **Adjacent: `infra_posture_management`.** The configuration-drift
  attestation lane. When the certificate-posture probe surfaces
  expiring certificates, TLS-version drift, or cipher-suite-below-
  floor deviations, the drift signal feeds
  `infra_posture_management` where the operator's remediation
  discipline picks it up and routes a change-management ticket.
  The two are complementary: crypto_posture_management is the
  read-only *measurement* against the declared cryptography
  policy; infra_posture_management is the *remediation dispatch*
  against configuration drift. See
  [`docs/cookbook/infra_posture_management.md`](./infra_posture_management.md).
- **Adjacent: `mfa_secured_comms`.** The DORA Art. 9 companion —
  the authentication slice (`dora:art-9-authentication`) is
  operated by `mfa_secured_comms`; crypto_posture_management
  operates the cryptography slice (`dora:art-9-crypto`). Both are
  per-window read-only posture-probes that emit a dated
  attestation and per-deviation Compliance Findings against the
  operator's evidence store; the two slices discharge independent
  operational disciplines and are mapped separately to preserve
  the atom-per-obligation shape. See
  [`docs/cookbook/mfa_secured_comms.md`](./mfa_secured_comms.md).

The chain lets crypto_posture_management stay narrowly focused on
the per-window cryptographic-posture measurement discipline while
infra_posture_management handles remediation dispatch on drift
signals and mfa_secured_comms handles the authentication-surface
half of the DORA Art. 9 protection-and-prevention obligation. The
chain is not code-coupled — each playbook is a standalone CACAO
artifact that can be run in isolation — but the audit trail's
coherence across the workflows is the sovereign-security property
the framework guarantees.

## 12. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys for the
  policy store, the certificate-endpoint surface, the key-
  management surface, the evidence store, or the cryptography-
  owner channel. Connectors are operator-bound at runtime against
  environment variables documented per target.
- **Policy authorship.** The playbook operates the per-window
  measurement discipline; it does not author the algorithm floor,
  the key-size floor, the per-key-class rotation cadence, or the
  TLS-version floor. Authorship is the operator's governance
  concern, bounded by the ENISA algorithm-and-key-parameters
  guidance and by the JC RTS on ICT risk management framework
  Art. 6 discipline.
- **Certificate renewal.** The playbook is read-only-by-contract:
  no certificate is issued, no renewal is triggered, no
  short-dated certificate is auto-replaced. Renewal lives on the
  operator's certificate-management surface (an ACME client, a
  PKI control plane, a certificate-management platform); this
  playbook records the days-to-expiry deviation and lets the
  operator's remediation lane pick it up.
- **Key rotation.** The playbook records overdue-rotation
  deviations and policy-gap deviations; it does not rotate keys.
  Rotation lives on the operator's key-management surface (an HSM
  control plane, a cloud KMS, an internal KMS) under the
  operator's change-management discipline.
- **Cipher-suite / TLS-version push.** The playbook records
  cipher-suite-below-floor and TLS-version-below-floor deviations;
  it does not push a cipher-suite change to the endpoint. The
  cipher-suite binding lives on the operator's edge surface (an
  in-house edge, a load-balancer control plane, a service-mesh
  control plane) and is remediated on the operator's change-
  management cadence.
- **Sigma rule ids.** The Compliance Finding stream is the
  upstream of any expired-cert / weak-cipher / floor-violation /
  overdue-rotation rule the operator's posture-management layer
  chooses to author; SecOps-NG does not pin stable Sigma rule
  ids on this overlay.

## 13. References

- [`content/playbooks/crypto_posture_management/README.md`](../../content/playbooks/crypto_posture_management/README.md)
  — canonical CACAO source overview and status.
- [`content/playbooks/crypto_posture_management/mappings.yaml`](../../content/playbooks/crypto_posture_management/mappings.yaml)
  — outbound OSCAL / OCSF / D3FEND / NIS2 / DORA / CRA overlay
  with per-step control anchors.
- [`content/mappings/nis2/article-21-2-h.yaml`](../../content/mappings/nis2/article-21-2-h.yaml)
  — NIS2 Article 21(2)(h) inbound anchor (cryptography and
  encryption policies and procedures).
- [`content/mappings/dora/article-9-crypto.yaml`](../../content/mappings/dora/article-9-crypto.yaml)
  — DORA Article 9(2)/(3) inbound anchor (ICT security policies,
  cryptography slice; JC RTS on ICT risk management framework
  Art. 6 on encryption and cryptographic controls).
- [`content/mappings/cra/annex-i-1-e-confidentiality-crypto-posture.yaml`](../../content/mappings/cra/annex-i-1-e-confidentiality-crypto-posture.yaml)
  — CRA Annex I §1(e) inbound anchor (cryptographic-posture lane
  of the confidentiality obligation).
- [`examples/n8n/crypto_posture_management/README.md`](../../examples/n8n/crypto_posture_management/README.md)
  — n8n worked-example walkthrough and import instructions.
- [`examples/temporal/crypto_posture_management/README.md`](../../examples/temporal/crypto_posture_management/README.md)
  — Temporal worked-example walkthrough.
- [`examples/langgraph/crypto_posture_management/README.md`](../../examples/langgraph/crypto_posture_management/README.md)
  — LangGraph worked-example walkthrough.
- [`docs/cookbook/mfa_secured_comms.md`](./mfa_secured_comms.md)
  — adjacent cookbook (DORA Art. 9 authentication slice
  companion).
- [`docs/cookbook/infra_posture_management.md`](./infra_posture_management.md)
  — adjacent cookbook (configuration-drift remediation lane;
  consumes drift signals from this playbook).
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay
  shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer
  runtime.
