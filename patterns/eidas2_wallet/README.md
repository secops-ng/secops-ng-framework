# patterns/eidas2_wallet/ — eIDAS 2.0 EUDIW attestation as workflow input

ROADMAP feature: **F-SV-02** — Shipped with three-target parity
(SKELETON #377, CORE-FANOUT-N8N #378, CORE-FANOUT-TEMPORAL #379,
CORE-FANOUT-LANGGRAPH #380). The CORE fan-out (compile-target
emitters) and EXTEND (worked examples) have landed under
`examples/{n8n,temporal,langgraph}/eidas2_wallet/` with byte-identical
cross-target goldens.

## What this pattern is

A minimal **typed-input shape** a workflow accepts when its caller has
already resolved an EU Digital Identity Wallet (EUDIW) attestation
into a verified, normalised record. The pattern hands the workflow a
strict Pydantic v2 model so downstream activities run against a
validated bundle, not a raw wire artifact.

The model is at `patterns/eidas2_wallet/input.py` and re-exported from
the package root as `WalletAttestationInput`.

## What this pattern is **not**

* **Not an OpenID4VP relying-party adapter.** The wire-protocol
  exchange (presentation request → wallet → Verifiable Presentation →
  issuer-chain verification → holder-binding check → status check →
  wallet trust-mark check) happens outside the workflow, in a
  verifier the operator already runs. The workflow consumes the
  result of that verifier, not the raw artifact.
* **Not the wallet-attestation evidence variant** under
  `schemas/evidence/`. The evidence variant is the durable record a
  workflow *emits*; this is the durable input it *accepts*. Field
  names overlap where the trust surface coincides; the two shapes
  remain distinct so input-side validation and emission-side
  attestation each have a single source of truth.
* **Not a complete pattern.** This SKELETON ships only the input
  model + this README + a sanity test. CORE wiring into compile
  targets and EXTEND worked examples are deliberately deferred.

## Pattern shape

```
patterns/eidas2_wallet/
├── README.md             — this file
├── __init__.py           — re-exports the typed input surface
├── input.py              — WalletAttestationInput + building blocks
└── tests/
    └── test_input.py     — sanity tests for the typed input model
```

The input model composes from three building blocks:

* `IssuerRef` — resolved reference to the attestation's issuer, joined
  to the entry in a Member-State Trusted List (per Commission
  Implementing Decision (EU) 2015/1505) or its aggregator (LOTL).
* `HolderBinding` — verifier-confirmed cryptographic binding between
  the holder and the proof-of-possession key (`cnf` claim for SD-JWT
  VC, device binding for mDoc).
* `StatusAssertion` — resolved revocation / suspension status from the
  upstream verifier (Token Status List for SD-JWT VC, OCSP-style for
  mDoc per ARF v2). The workflow applies its own freshness policy
  against `checked_at`.

## Wire-format coverage

ARF v2.x mandates both credential formats; `attestation_format`
enumerates them:

| Code         | Format                                            |
|--------------|---------------------------------------------------|
| `sd_jwt_vc`  | SD-JWT VC (IETF draft, JSON, salted-disclosure)   |
| `mso_mdoc`   | ISO/IEC 18013-5 mDoc (CBOR/COSE, namespace-signed) |

Both are first-class at the input layer. The pattern is wire-form
agnostic above the verifier — the caller has already parsed the wire
form and reduced it to claims.

## Regulatory anchors

* **Regulation (EU) 2024/1183** of the European Parliament and of the
  Council of 11 April 2024 amending Regulation (EU) No 910/2014 as
  regards establishing the European Digital Identity Framework.
  CELEX `32024R1183`. Articles 5a–5g (EUDIW), 5b(2) (relying-party
  register), 5c (wallet trust mark), 45f-bis (QEAA presumption of
  accuracy).
* **Regulation (EU) No 910/2014** as amended. CELEX `32014R0910`.
  Articles 25 (QES legal effect), Chapter III (trust services).
* **Commission Implementing Decision (EU) 2015/1505** establishing the
  Trusted List format. The LOTL / per-MS TSL fetch is referenced by
  the input model via the `trust_list_uri` field but lives outside
  this pattern; the framework keeps a single LOTL source of truth.

## Wire-protocol anchors (ARF v2.x line; see source brief §3)

* **OpenID for Verifiable Presentations (OpenID4VP)** — RP ↔ wallet
  presentation protocol (mandated by ARF v2).
* **SD-JWT VC** (`draft-ietf-oauth-sd-jwt-vc`) — JSON credential
  format with salted selective disclosure.
* **ISO/IEC 18013-5** — mDoc data model and proximity flows.
* **IETF Token Status List** (`draft-ietf-oauth-status-list`) —
  status surface for SD-JWT VC; mDoc uses an OCSP-style mechanism
  per ARF v2.

The framework references the ARF v2.x line rather than pinning a
point release, because the v2 surface has been stable on cadence
since v2.4 (July 2025) and pinning monthly drifts docs.

## Public-bar hygiene

* No specific QTSP, wallet vendor, or Member-State relying-party
  register names appear in this pattern or its fixtures. Operational
  deployment guidance (which MS to register an RP in, which QTSP a
  given operator has chosen) belongs in `secops-ng-deployment`
  (private), not here.
* The trust topology fields (`issuer_country`, `trust_list_uri`,
  `issuer_identifier`) are structural — they pin the **shape** of the
  trust join, not a specific anchor.
* The verifier — not this pattern — owns the wallet trust-mark check
  per Art. 5c. ARF certification implementing acts are still in
  flight at the SKELETON cut; the verifier ships its own fail-closed
  policy on trust marks and surfaces a resolved boolean if needed
  (out of SKELETON scope; CORE may add a `wallet_trust_mark_verified`
  field if downstream activities need it).

## Contribution checklist (for the CORE / EXTEND cards)

CORE (compile-target fan-out) lands when:

* `compilers/_shared/eidas2_wallet/` exposes a deterministic adapter
  that lifts a `WalletAttestationInput` into the input surface each
  compile target needs (n8n credentials node payload, Temporal
  workflow input dataclass, LangGraph state schema entry).
* Per-target byte-parity goldens exist under
  `examples/{n8n,temporal,langgraph}/eidas2_wallet/` (placeholder
  workflow; the meaningful workflow is on the EXTEND card).

EXTEND (worked examples) lands when:

* A representative regulator-flavoured workflow consumes a
  `WalletAttestationInput` end-to-end (proposed shape:
  qualified-attestation-as-evidence into a posture-audit run; the
  source brief §6.2 is the strongest signal here).
* Cookbook entry under `docs/cookbook/eidas2_wallet.md` documents
  the operator workflow.

## Out of scope (permanently, for this pattern)

* RP registration per Member State (legal/operational lift, not a
  code problem).
* Cross-border attribute resolution beyond what OpenID4VP gives
  free.
* mDoc proximity (BLE / NFC) flows — not a security-operations
  workflow shape.
