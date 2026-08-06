# crypto_posture_management

CACAO v2 playbook for the cryptography & encryption posture
surface required by NIS2 Art. 21(2)(h): inventory crypto policy →
probe cert posture → check key rotation → capture dated posture
attestation → notify the cryptography owner. Read-only and side-
effect-free against operator infrastructure; the probe and the
rotation check do not alter endpoint state or rotate keys.

## Status

CORE. The playbook artifact, the regulatory + control overlay, and the
five deterministic primitives under `primitives/` bound to the five
action steps. The three finding kinds this card names — expired-cert,
weak-cipher, missed-rotation — are produced by the two probe steps and
classified against the operator's own policy as either a **drift** (the
posture contradicts a clause the policy states) or a **gap** (the policy
is silent on the concern). An EXTEND card wires the cipher-suite-floor
KPI and rotation-cadence KPI emitters against the operator's evidence
store, and binds the notification channel the notify step currently only
plans against.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.crypto_posture_management@v1`).
- `primitives/` — the five deterministic bodies the action steps bind to.
  Pure, offline, replay-safe: no clock reads, no network, no LLM. Nothing
  rotates a key, reissues a certificate, changes a cipher suite or sends
  a message.
- `mappings.yaml` — outbound overlay (OSCAL controls, OCSF telemetry,
  NIS2 Art.21(2)(h)).

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. Emitted
artifacts and golden tests are owned by CORE-layer sibling cards; this
directory ships the portable content only.
