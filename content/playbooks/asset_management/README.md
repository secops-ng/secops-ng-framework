# asset_management

CACAO v2 SKELETON playbook for the asset and configuration management
capability against the operator's own deployed estate: ingest the
documented inventory-source set on a scheduled cadence → reconcile
into the operator-authoritative snapshot → compute the per-asset
delta against the previous documented snapshot → classify each delta
against the operator's documented delta taxonomy → capture the dated
asset-inventory-delta evidence record → notify the inventory owner.
Operates the per-window reconciliation against the operator's
documented inventory sources; it does not author the operator's
inventory-source architecture.

## Status

SKELETON. The playbook artifact and the NIS2 Art. 21(2)(i)
asset-management overlay land here; CORE-layer cards add the
deterministic primitives (ingest-source reconciliation, snapshot-id
derivation, delta normalisation, taxonomy classification, evidence
emission) together with their D3FEND pins, and the per-target
compiler emissions (n8n / Temporal / LangGraph goldens); EXTEND
cards wire the asset-inventory-drift and unmanaged-asset-cardinality
metric emitters against the operator's evidence store. DORA Art. 8
(identification function — asset / configuration register) and CRA
Annex I §1(c) / §1(e) inbound entries are deliberately deferred to
separate inbound-closure cards (see the gap notes in `mappings.yaml`
and the audited skip entries under
`content/mappings/dora/_orphan_skip.yaml` and
`content/mappings/cra/_orphan_skip.yaml`). The GDPR data-flow entry
follows the same no-personal-data pattern as patch_management and
ddos_response.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.asset_management@v1`).
- `mappings.yaml` — outbound overlay (OSCAL controls, OCSF telemetry,
  NIS2 Art. 21(2)(i)).

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. Emitted
artifacts and golden tests are owned by CORE-layer sibling cards; this
directory ships the portable content only.
