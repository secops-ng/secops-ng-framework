# cryptographic_controls — NIS2 Art. 21(2)(h) lifecycle

Write-side lifecycle playbook of the F-WF-CRYPTOMGMT trilogy —
`stable` under the Maturity ladder (`content_version` 1.0.0), with the
cookbook walkthrough at
[`docs/cookbook/cryptographic_controls.md`](../../../docs/cookbook/cryptographic_controls.md).
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

- `playbook.cacao.json` — the CACAO v2 workflow: resolve-policy-inventory
  → a `switch-condition` on `__lifecycle_event__` → the branch the event
  names (key-lifecycle for the three key events, certificate-lifecycle
  for the three certificate events, enforce-encryption for
  `enforcement-gate`) → record-lifecycle-evidence → notify-crypto-owner.
  Every action step binds a deterministic primitive under `primitives/`
  through `x_secops_ng.core_body`.
- `primitives/` — the six deterministic primitives: pure, offline,
  LLM-free. The policy is input, not content (no default cipher
  baseline is ever injected — a shipped baseline would become a
  de-facto standard the framework has no authority to set); every
  policy check lands on the satisfied / violated / undocumented ladder
  with `compliant` reserved for documented-and-satisfied; key material
  is actively refused at the boundary; the enforcement gate denies only
  on a documented violation. The KMS backend, CA backend,
  storage-encryption and TLS-endpoint surfaces, the evidence store and
  the owner channel stay adapter-bound operator surfaces.
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
`tests/examples/{n8n,temporal,langgraph}/cryptographic_controls/`,
regenerated from the bound source: n8n emits six Code nodes and one
Switch node; the Temporal activities and LangGraph tools import their
primitives, with `NotImplementedError` marking only the
operator-integration seams.

## Trilogy

- **SKELETON:** scaffold + mappings + compile-target declaration.
- **CORE:** three-target compiled examples + byte-parity goldens and
  the mappings closure (D3-SKT / D3-CM D3FEND selection, GDPR
  Art. 32(1)(a) inbound edge, NIS2 + DORA inbound edges); then the six
  deterministic primitives (CORE-PRIM) bound to the action steps with
  the lifecycle switch and the playbook graduated to `stable`
  (CORE-WIRE).
- **EXTEND:** the cookbook walkthrough at
  [`docs/cookbook/cryptographic_controls.md`](../../../docs/cookbook/cryptographic_controls.md).
  Advanced features — HSM-backed key ceremonies, post-quantum rollover
  choreography, per-Member-State CA-trust posture — remain
  operator-side and are recorded as not covered in the cookbook.

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
