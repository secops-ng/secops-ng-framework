# backup_recovery

CACAO v2 SKELETON playbook for the business-continuity / backup &
disaster-recovery surface: detect restore-drill trigger → validate
backup integrity → execute non-destructive restore drill → capture
dated attestation + drill evidence → notify continuity owner. Reentrant
and side-effect-free against production state; the drill executes
against the operator's documented isolated drill target.

## Status

CORE. All five action steps carry `core_body` bindings onto the pure
primitives under `primitives/` (drill-trigger resolution, integrity
evaluation, restore-drill evaluation, attestation build, notification
composition); the `__integrity_ok__` branch predicate is filled; the
three worked examples and their byte-parity goldens ship refreshed
against the bound playbook. Operator observations (backup inventory,
integrity checks, drill results, owner channel binding) arrive as
external playbook variables so the primitives stay replay-safe and
offline. An EXTEND card owns the cookbook walkthrough and wires the
attestation-cadence and integrity-failure metric emitters against the
operator's evidence store.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.backup_recovery@v1`).
- `mappings.yaml` — outbound overlay (OSCAL controls, OCSF telemetry,
  NIS2 Art.21(2)(c), DORA Art.12).

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. Emitted
artifacts and golden tests are owned by CORE-layer sibling cards; this
directory ships the portable content only.
