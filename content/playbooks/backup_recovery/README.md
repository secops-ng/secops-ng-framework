# backup_recovery

CACAO v2 SKELETON playbook for the business-continuity / backup &
disaster-recovery surface: detect restore-drill trigger → validate
backup integrity → execute non-destructive restore drill → capture
dated attestation + drill evidence → notify continuity owner. Reentrant
and side-effect-free against production state; the drill executes
against the operator's documented isolated drill target.

## Status

SKELETON. The playbook artifact and the regulatory + control overlay
land here; CORE-layer cards add the detection bindings (restore-target
misconfiguration signals) and the per-target compiler emissions
(n8n / Temporal / LangGraph goldens); an EXTEND card wires the
attestation-cadence and integrity-failure metric emitters against
the operator's evidence store.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.backup_recovery@v1`).
- `mappings.yaml` — outbound overlay (OSCAL controls, OCSF telemetry,
  NIS2 Art.21(2)(c), DORA Art.12).

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. Emitted
artifacts and golden tests are owned by CORE-layer sibling cards; this
directory ships the portable content only.
