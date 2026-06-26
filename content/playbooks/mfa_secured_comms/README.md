# mfa_secured_comms

CACAO v2 SKELETON playbook for the multi-factor / continuous-
authentication and secured-communications posture surface required
by NIS2 Art. 21(2)(j): probe MFA coverage → assess continuous
authentication → verify out-of-band emergency channels → capture
dated posture attestation → notify the authentication owner.
Read-only and side-effect-free against operator infrastructure; the
MFA probe and the continuous-authentication assessment do not alter
identity-provider state, and the OOB-channel verification is a
documented test transaction rather than a real emergency
notification.

## Status

SKELETON. The playbook artifact and the regulatory + control overlay
land here; CORE-layer cards add the detection bindings (missing-MFA,
stale-session, unreachable-OOB upstream rule ids) and the per-target
compiler emissions (n8n / Temporal / LangGraph goldens); an EXTEND
card wires the session-staleness KPI and OOB-reachability KPI
emitters against the operator's evidence store.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.mfa_secured_comms@v1`).
- `mappings.yaml` — outbound overlay (OSCAL controls, OCSF telemetry,
  NIS2 Art.21(2)(j)).

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`.
Emitted artifacts and golden tests are owned by CORE-layer sibling
cards; this directory ships the portable content only.
