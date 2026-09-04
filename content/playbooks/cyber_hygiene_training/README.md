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

Shipped (see ROADMAP.md → F-WF-CYBERHYG). The trilogy has landed:

- **SKELETON** — the CACAO v2 artifact
  (`playbook.cyber_hygiene_training@v1`) and the NIS2
  Art. 21(2)(g) outbound overlay in `mappings.yaml`.
- **CORE** — three reference-target compile examples under
  `examples/{n8n,temporal,langgraph}/cyber_hygiene_training/`
  with byte-parity goldens under
  `tests/examples/{n8n,temporal,langgraph}/cyber_hygiene_training/test_golden.py`.
- **EXTEND** — practitioner walkthrough at
  `docs/cookbook/cyber_hygiene_training.md`.

The per-cohort training-overdue KPI emitters against the operator's
evidence store remain a separate metrics-layer card.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.cyber_hygiene_training@v1`).
- `mappings.yaml` — outbound overlay (OSCAL controls, OCSF telemetry,
  NIS2 Art.21(2)(g)).

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`.
Reference emissions and byte-parity goldens ship under
`examples/{n8n,temporal,langgraph}/cyber_hygiene_training/` and
`tests/examples/{n8n,temporal,langgraph}/cyber_hygiene_training/`.

## Binding status

Deliberately unbound. The 6 action steps compile with operator-TODO
bodies on all three targets and the playbook carries no `core_body`
primitive bindings; `catalog.py` reports it that way and the playbook
stays `experimental` under the Maturity ladder. This is a recorded
decision (#921 — PARK bucket, Director 2026-09-04), not neglect:
it overlaps `security_awareness_training` almost entirely, and binding either playbook twice would entrench the duplication — the pair is parked together pending a merge decision (park-both). Reopening the park is a roadmap decision, not a bug — the
trigger would be that the merge decision is taken, after which the surviving playbook is bound once.
