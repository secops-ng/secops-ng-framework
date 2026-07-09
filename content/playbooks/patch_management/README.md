# patch_management

CACAO v2 SKELETON playbook for the patch / update maintenance
capability against the operator's own deployed estate: detect a
security update available → classify against the operator's patch-
criticality taxonomy → stage rollout to the canary ring → validate
the canary against the documented health gates → fan out to the
remaining rings on a green canary → capture dated evidence → notify
the maintenance owner. Operates the per-update rollout against the
operator's pre-bound deployment-ring topology; it does not author the
operator's patch-distribution architecture.

## Status

Shipped (see ROADMAP.md → F-WF-PATCH). The trilogy has landed:

- **SKELETON** — the CACAO v2 artifact
  (`playbook.patch_management@v1`) and the NIS2 Art. 21(2)(e)
  outbound overlay in `mappings.yaml`.
- **CORE** — six primitives under `primitives/` (`detect`,
  `classify`, `stage`, `validate`, `fanout`, `artifact`) with
  `core_body` bindings across the action steps; three
  reference-target compile examples under
  `examples/{n8n,temporal,langgraph}/patch_management/` with
  byte-parity goldens under
  `tests/examples/{n8n,temporal,langgraph}/patch_management/test_golden.py`.
- **EXTEND** — practitioner walkthrough at
  `docs/cookbook/patch_management.md`.

DORA Art. 9 ICT-risk-management framework (operations and
maintenance) and CRA Annex I §2 security-updates inbound entries
remain audited-skip / deferred to separate inbound-closure cards
(see the gap notes in `mappings.yaml` and the audited skip entries
under `content/mappings/dora/_orphan_skip.yaml` and
`content/mappings/cra/_orphan_skip.yaml`). The GDPR data-flow entry
is deferred under the same gdpr-orphan_skip manifest convention.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.patch_management@v1`).
- `mappings.yaml` — outbound overlay (OSCAL controls, OCSF telemetry,
  NIS2 Art. 21(2)(e)).
- `primitives/` — six CORE primitives (`detect`, `classify`, `stage`,
  `validate`, `fanout`, `artifact`) bound to the action steps via
  `core_body`.

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`.
Reference emissions and byte-parity goldens ship under
`examples/{n8n,temporal,langgraph}/patch_management/` and
`tests/examples/{n8n,temporal,langgraph}/patch_management/`.
