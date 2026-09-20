# asset_management

CACAO v2 playbook for the asset and configuration management
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

Experimental, CORE-PRIM complete. All six action steps now have a
deterministic primitive behind them under `primitives/` — source-set
resolution, snapshot reconciliation, delta computation, taxonomy
classification, evidence composition and owner notification — each
executed directly by unit coverage. The three worked examples under
`examples/{n8n,temporal,langgraph}/asset_management/` and the
cookbook at `docs/cookbook/asset_management.md` ship alongside.

**Owed: the wire.** The CACAO steps do not yet carry
`x_secops_ng.core_body` bindings, so `catalog.py` reports 0 of 6
bound and the playbook stays `experimental`: the primitives exist but
the compile targets still emit operator-TODO bodies rather than
calling them. Binding the six steps, regenerating the examples and
recomputing the Maturity ladder is the CORE-WIRE card. EXTEND cards
wire the asset-inventory-drift and unmanaged-asset-cardinality metric
emitters against the operator's evidence store. DORA Art. 8
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
- `primitives/` — the six deterministic primitives the action steps
  bind at CORE-WIRE: pure, offline, LLM-free. Reconciliation is
  read-only against the source set — the playbook surfaces inventory
  drift and never writes back into the operator's CMDB or IaC
  declarations; correcting drift is the operator's downstream lever.
  Two derivations are shared rather than duplicated: the source-set
  id is computed once in `reconcile` and reused by `ingest`, and the
  `unmanaged-discovered` cardinality the notification pages on is
  counted from the same classification list the evidence record
  counts, with both equalities pinned by test.
- `docs/cookbook/asset_management.md` — the practitioner walkthrough.

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. The
emitted artifacts ship under
`examples/{n8n,temporal,langgraph}/asset_management/` with byte-parity
goldens under `tests/examples/`. They are regenerated from the
canonical source, which is not yet bound — so the emitted bodies are
still operator-TODO placeholders rather than primitive calls. The
CORE-WIRE card changes that and regenerates them in the same change.
