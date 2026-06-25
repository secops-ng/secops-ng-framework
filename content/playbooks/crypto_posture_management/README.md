# crypto_posture_management

CACAO v2 SKELETON playbook for the cryptography & encryption posture
surface required by NIS2 Art. 21(2)(h): inventory crypto policy →
probe cert posture → check key rotation → capture dated posture
attestation → notify the cryptography owner. Read-only and side-
effect-free against operator infrastructure; the probe and the
rotation check do not alter endpoint state or rotate keys.

## Status

SKELETON. The playbook artifact and the regulatory + control overlay
land here; CORE-layer cards add the detection bindings (expired-cert,
weak-cipher, missed-rotation upstream rule ids) and the per-target
compiler emissions (n8n / Temporal / LangGraph goldens); an EXTEND
card wires the cipher-suite-floor KPI and rotation-cadence KPI
emitters against the operator's evidence store.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.crypto_posture_management@v1`).
- `mappings.yaml` — outbound overlay (OSCAL controls, OCSF telemetry,
  NIS2 Art.21(2)(h)).

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. Emitted
artifacts and golden tests are owned by CORE-layer sibling cards; this
directory ships the portable content only.
