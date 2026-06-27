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

SKELETON. The playbook artifact and the NIS2 Art. 21(2)(e)
maintenance overlay land here; CORE-layer cards add the detection
bindings (canary-health / rollback-readiness signals) together with
their D3FEND pins, and the per-target compiler emissions (n8n /
Temporal / LangGraph goldens); an EXTEND card wires the time-to-patch
and patch-coverage metric emitters against the operator's evidence
store. DORA Art. 9 ICT-risk-management framework (operations and
maintenance) and CRA Annex I §2 security-updates inbound entries are
deliberately deferred to separate inbound-closure cards (see the gap
notes in `mappings.yaml` and the audited skip entries under
`content/mappings/dora/_orphan_skip.yaml` and
`content/mappings/cra/_orphan_skip.yaml`). The GDPR data-flow entry is
deferred to the same CORE-layer scope under the gdpr-orphan_skip
manifest convention.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.patch_management@v1`).
- `mappings.yaml` — outbound overlay (OSCAL controls, OCSF telemetry,
  NIS2 Art. 21(2)(e)).

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. Emitted
artifacts and golden tests are owned by CORE-layer sibling cards; this
directory ships the portable content only.
