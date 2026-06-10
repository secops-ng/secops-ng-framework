# NIS2 Article 22 — Union-level coordinated supply-chain risk assessment

Companion narrative for the structural mapping atom `nis2:art-22` (the
YAML atom itself lands in the F-CP-03 EXTEND-NIS2-MAPPING sibling card;
this file is the contributor-facing prose).

This document explains how the **supply-chain evidence stream** under
[`content/evidence/supply-chain/`](../../evidence/supply-chain/SCHEMA.md)
discharges the operational half of the NIS2 Article 22 obligation —
making each in-scope entity's dependency surface visible enough that a
Union-level coordinated risk assessment of critical supply chains is
actually feasible — and how the schema is referenced (not duplicated)
here.

## Scope

- **In:** how the supply-chain evidence stream's artifact shape
  satisfies the Union-level coordinated-risk-assessment overlay in
  Article 22; pointers to the typed schema (under SKELETON narrative
  in [`SCHEMA.md`](../../evidence/supply-chain/SCHEMA.md), JSON Schema
  to land in CORE-FANOUT), to the per-target reference emitters (also
  in CORE-FANOUT), and to the existing Article 21(2)(d) atom this
  overlay leans against.
- **Out:** legal interpretation of Article 22; duplication of the
  schema body; the Article 21(2)(d) baseline supply-chain obligation —
  that is the companion narrative under
  [`article-21-2-d.yaml`](article-21-2-d.yaml); the EU-Cooperation-Group
  reporting envelope (the framework emits the per-entity artifact,
  it does not implement the Member-State aggregation pipeline).

## How Article 22 reads against Article 21(2)(d)

Article 21(2)(d) is the per-entity baseline: every essential and
important entity must address supply-chain security as part of its
risk-management measures, including the security characteristics of
direct suppliers and service providers and periodic re-attestation.
The supply-chain evidence stream's per-execution
`dependencies-snapshot.json` artifact discharges the operational half
of that baseline; the structural crosswalk lives in
[`article-21-2-d.yaml`](article-21-2-d.yaml).

Article 22 layers an additional Union-level overlay onto the baseline:
Article 22(1) places the **coordinated security risk assessment of
specific critical supply chains** with the **Cooperation Group**,
acting **in cooperation with the Commission and ENISA** — not with
Member States acting on their own initiative. Member States'
Article 22 role (Art. 22(2) onward) is to surface the per-entity
inputs that feed the Cooperation Group's assessment. For that
assessment to be feasible, each in-scope entity has to surface its
dependency inventory — by provider kind, residency, ownership, and
sub-processor chain — in a shape that aggregates across the sector.
The supply-chain stream's snapshot artifact is designed to be that
surface: `dependencies[]` enumerated per provider, every record
sovereignty-classified by the `sovereign-provider classification`
fields documented in [`../../evidence/supply-chain/SCHEMA.md`](../../evidence/supply-chain/SCHEMA.md),
and the `aggregates` block carrying pre-computed per-execution counts
so a sectoral rollup is one set-union away.

## Schema — pointer, not copy

The supply-chain evidence artifact shape is documented once, in the
contributor SCHEMA narrative under the stream root:

- **Contributor narrative (SKELETON, this card):**
  [`content/evidence/supply-chain/SCHEMA.md`](../../evidence/supply-chain/SCHEMA.md)
- **Authoritative JSON Schema (lands in F-CP-03 CORE-FANOUT):**
  `schemas/evidence/supply-chain.schema.json`

The stream narrative is the human-facing entry point; the JSON Schema
is the machine-checkable contract. **Do not duplicate the schema body
in this file.** If a field name, type, or constraint changes, the
schema file is the source of truth and the stream narrative's
at-a-glance summary is updated alongside it; this mapping document
only changes when the *mapping* between the stream and the regulatory
clause changes.

Shared vocabularies the schema will import once the CORE-FANOUT lands
(see [`SCHEMA.md`](../../evidence/supply-chain/SCHEMA.md) §"Promoted
enums"):

- `supply_chain_dependency_kind` enum — five dependency kinds
  (`software_dependency`, `hosted_api`, `data_feed`, `ai_provider`,
  `managed_runtime`).
- `sovereignty_residency` enum — five residency values (`eu`, `eea`,
  `eu_adequate_third_country`, `non_eu`, `unknown`).
- `sovereignty_band` enum — five rolled-up bands (`sovereign`,
  `eu_hosted_non_sovereign`, `eu_adequate`, `non_eu`, `unknown`).
- `provenance` shape — `{ source_url, captured_at, commit_sha }`,
  mirrored from `content/controls/`.

## Article 22 → schema-field overlay

For each `dependencies[]` record in the snapshot:

| Article 22 input the coordinated assessment needs | Schema field carrying it                                                  |
|---------------------------------------------------|---------------------------------------------------------------------------|
| Provider identity (opaque)                        | `dependencies[].provider_id`                                              |
| Kind of dependency                                | `dependencies[].kind`                                                     |
| Where the workload runs                           | `dependencies[].sovereignty_classification.residency`                     |
| Beneficial ownership of the provider              | `dependencies[].sovereignty_classification.ownership`                     |
| Declared sub-processor chain                      | `dependencies[].sovereignty_classification.sub_processor_chain`           |
| Rolled-up sectoral band                           | `dependencies[].sovereignty_classification.sovereignty_band`              |
| Re-attestation freshness                          | `dependencies[].attestation.last_reattested_at`, `next_due_at`            |

Per-execution aggregates (`aggregates.total_providers`,
`aggregates.sovereign_count`, `aggregates.eu_hosted_count`,
`aggregates.non_eu_count`, `aggregates.ai_provider_count`) carry the
five numbers a Member-State-level rollup needs without re-walking the
per-record array.

The framework is deliberately silent on the **aggregation pipeline**:
how an operator's snapshots reach the competent authority or feed the
Cooperation Group's coordinated assessment is a Member-State-specific
delivery path, out of scope for the per-entity artifact contract.

## Sovereign-provider classification

The classification fields read against an operator-supplied private
knowledge base; the framework repository never ingests KB contents —
see the existing note in [`article-21-2-d.yaml`](article-21-2-d.yaml).
The contract here is the *shape* the emitter writes when the KB is
consulted. Fixtures used in tests are synthetic; see
`tests/fixtures/supply_chain/` (lands in EXTEND-tests-goldens).

## Status

SCHEMA card landed: the authoritative JSON Schema
[`schemas/evidence/supply-chain.schema.json`](../../../schemas/evidence/supply-chain.schema.json),
the four promoted shared enums (`supply_chain_dependency_kind`,
`sovereignty_residency`, `sovereignty_ownership`, `sovereignty_band`),
the structural `nis2:art-22` atom in
[`article-22.yaml`](article-22.yaml) — with `evidence_stream_refs:
[supply-chain]`, control refs, and the `kri.suppliers_attestation_stale@v1`
metric ref — and the `evidence_stream_refs: [supply-chain]` wire on
the existing Art. 21(2)(d) atom. The shared emitter, the per-target
adapters, the byte-parity goldens, the drift hook, and the KPI / KRI
promotions land in their named sibling cards under F-CP-03.

## See also

- [`article-21-2-d.yaml`](article-21-2-d.yaml) — Art. 21(2)(d) baseline
  atom this overlay leans against.
- [`../../evidence/supply-chain/SCHEMA.md`](../../evidence/supply-chain/SCHEMA.md)
  — stream record-schema narrative.
- ROADMAP entry: F-CP-03 — Supply-chain stream.
