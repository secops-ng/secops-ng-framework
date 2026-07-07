# cryptographic_controls — NIS2 Art. 21(2)(h) lifecycle

EXTEND tier of the F-WF-CRYPTOMGMT trilogy (cookbook walkthrough shipped
at [`docs/cookbook/cryptographic_controls.md`](../../../docs/cookbook/cryptographic_controls.md)).
This playbook is the
operator-side lifecycle materialisation of the NIS2 Art. 21(2)(h)
cryptography-and-encryption obligation: resolve the declared
cryptography policy, discharge the key-lifecycle branch (generate /
rotate / revoke), evaluate the encryption-enforcement gate against
the at-rest and in-transit conditions the policy names, discharge
the certificate-lifecycle branch (issue / renew / revoke), record
a dated lifecycle attestation to the operator's evidence store, and
notify the cryptography owner.

Deliberately paired with the sibling `crypto_posture_management`
playbook. That surface is the read-only posture-attestation lane
(inventory the policy, probe the certificate posture, check
rotation-cadence, publish a dated posture-attestation record). This
playbook is the write-side lane that produces the material the
posture surface then attests against. Both overlays anchor
`nis2:art-21-2-h` and share `__crypto_scope__` / `__policy_inventory_id__`
so the write-side and read-side lifecycles read from the same
declared scope.

## Files

- `playbook.cacao.json` — CACAO v2 workflow scaffold (six action
  steps: resolve-policy-inventory → key-lifecycle → enforce-encryption
  → certificate-lifecycle → record-lifecycle-evidence →
  notify-crypto-owner). SKELETON: adapter bindings under
  `patterns.cryptographic_controls` (KMS backend, CA backend,
  storage-encryption backend, TLS-endpoint backend) are TODO markers
  a sibling CORE card lands.
- `mappings.yaml` — outbound view of the content model: OSCAL
  (SC-12 key management, SC-13 cryptographic protection, SC-17
  PKI certificates, SC-28 protection of information at rest, SC-8
  transmission confidentiality and integrity), D3FEND (D3-SKT
  Software Key Takeout on the key-lifecycle branch, D3-CM
  Cryptographic Module on the enforcement-gate branch), OCSF (API
  Activity 6003), and the inbound regulatory anchors (NIS2 Art.
  21(2)(h), DORA Art. 9, GDPR Art. 32(1)(a)). The CRA §1(e)
  write-side companion anchor is deliberately deferred to a
  sibling CRA mapping card so the read-side and write-side lane
  entries land together — see the header note on the CRA anchor.

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`.
Byte-parity compiled examples ship under
`examples/{n8n,temporal,langgraph}/cryptographic_controls/` with
drift guards under
`tests/examples/{n8n,temporal,langgraph}/cryptographic_controls/`.

## Trilogy

- **SKELETON:** scaffold + mappings + compile-target declaration.
- **CORE:** three-target compiled examples + byte-parity
  goldens, full mappings closure (D3-SKT / D3-CM D3FEND selection,
  GDPR Art. 32(1)(a) inbound edge, NIS2 + DORA inbound edges).
- **EXTEND (this card):** cookbook walkthrough at
  [`docs/cookbook/cryptographic_controls.md`](../../../docs/cookbook/cryptographic_controls.md).
  Adapter Protocols under `patterns.cryptographic_controls` and
  advanced features (HSM-backed key ceremonies, post-quantum
  rollover choreography, per-Member-State CA-trust posture) land
  on a sibling EXTEND card.

## Prerequisites

Operator inputs the CORE-layer bindings will read:

- A documented cryptography policy resolvable against
  `__crypto_scope__` (algorithm floor, key-size floor, per-key-class
  rotation cadence, TLS-version floor, declared CA / trust anchors,
  expiry buffer). Missing-policy branch is explicitly modelled — the
  playbook records the gap, it does not fail.
- Read/write access to the operator's KMS backend (for the
  key-lifecycle branch) and CA backend (for the certificate-lifecycle
  branch).
- A pre-bound notification channel for the cryptography owner.
