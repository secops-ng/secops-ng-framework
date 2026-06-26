# cyber_hygiene_training

CACAO v2 SKELETON playbook for the basic cyber-hygiene and staff
cybersecurity-training posture surface required by NIS2 Art. 21(2)(g):
inventory training roster → schedule training cycle → run phishing
simulation → track completion → capture dated training attestation →
notify the training owner of any gaps. Read-only and side-effect-free
against operator infrastructure; the roster inventory and completion
tracking do not mutate LMS or HR state, and the phishing-simulation
step is a clearly-labelled exercise that does not trigger incident
response or alter production mailflow controls.

This playbook is the PROACTIVE training and hygiene companion to the
existing REACTIVE phishing_triage playbook under the same article:
phishing_triage handles a real phishing incident in progress;
cyber_hygiene_training operates the per-cycle awareness, role-based
training, and phishing-simulation programme that is the audit-evident
discharge of the policy NIS2 Art.21(2)(g) requires.

## Status

SKELETON. The playbook artifact and the regulatory + control overlay
land here; CORE-layer cards add the detection bindings (missed-training
and simulation-click upstream rule ids) and the per-target compiler
emissions (n8n / Temporal / LangGraph goldens); an EXTEND card wires
the per-cohort training-overdue KPI emitters against the operator's
evidence store.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.cyber_hygiene_training@v1`).
- `mappings.yaml` — outbound overlay (OSCAL controls, OCSF telemetry,
  NIS2 Art.21(2)(g)).

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`.
Emitted artifacts and golden tests are owned by CORE-layer sibling
cards; this directory ships the portable content only.
