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

Stable, `content_version` 1.0.0. All six action steps bind a
deterministic primitive under `primitives/` through
`x_secops_ng.core_body` — source-set resolution, snapshot
reconciliation, delta computation, taxonomy classification, evidence
composition and owner notification — each executed directly by unit
coverage, and the three reference targets emit those calls rather than
operator-TODO bodies. The graduation checklist recomputes green:
tier A, 6 of 6 real bindings, zero placeholder bodies, zero blank
predicates, zero schema errors, three-target goldens, examples
regenerated in the same change.

What the wire does **not** claim: the compile targets emit primitive
calls, not a deployment. The per-source pull, the evidence-store write,
and the delivery of the owner notification are all adapter surfaces the
operator binds. The reconciliation stays read-only against the source
set — the playbook surfaces inventory drift and never writes back into
the operator's CMDB or IaC declarations; correcting drift is the
operator's downstream lever.

Two naming points were settled at the wire rather than carried
forward. `__delta_set_id__` was renamed `__delta_set__`: the primitive
emits the delta records themselves, and naming a record list an "id"
would have promised a digest no primitive computes. `__delta_classification__`
keeps its name but its description now records that it carries one
taxonomy entry per delta, not an identifier.

The deadline short-circuit stays inside the classify primitive rather
than becoming a CACAO branch. `__reconciliation_deadline_missed__` is
bound as a real boolean input and the primitive returns the single
sentinel `['unclassified']`; routing around the step instead would mean
the sentinel is never produced, and deciding the same thing in two
places is how the two decisions drift apart.

Still owed: EXTEND cards wire the asset-inventory-drift and
unmanaged-asset-cardinality metric emitters against the operator's
evidence store, and detection bindings for ingest-side and
reconciliation-side failures wait on upstream rule ids. DORA Art. 8
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
goldens under `tests/examples/`. All three are regenerated from the
canonical source and emit the bound primitive calls: n8n as Code nodes
carrying the import and the call, Temporal as activity bodies,
LangGraph as state-bound node functions. The evidence `artifact_id`
does not key on `compile_target`, so the three re-derive byte-identical
records — asserted across targets rather than assumed.
