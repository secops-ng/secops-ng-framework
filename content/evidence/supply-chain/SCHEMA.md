# content/evidence/supply-chain/SCHEMA.md

Supply-chain evidence stream — record-schema narrative.

This document is the **contributor-facing description** of the artifact
shape the supply-chain evidence stream emits. The authoritative
machine-readable schema landed alongside this narrative at
[`schemas/evidence/supply-chain.schema.json`](../../../schemas/evidence/supply-chain.schema.json)
(F-CP-03 SCHEMA card); the reference emitters (n8n / Temporal /
LangGraph) land in the CORE-FANOUT sibling card against that stable
target.

## What this stream is

An operator running workflows that call external providers — software
dependencies, hosted APIs, third-party data feeds, AI providers,
managed runtimes — has to demonstrate, per execution, that the
dependency surface is enumerated, classified for sovereignty, and
re-attested on cadence. NIS2 Article 21(2)(d) makes that a baseline
risk-management obligation; Article 22 layers on a Union-level
coordinated-risk-assessment overlay for critical supply chains. The
stream discharges the operational half of those obligations by
emitting one `dependencies-snapshot.json` artifact every time a
workflow execution that calls an external provider closes.

Upstream workflow: any workflow whose definition declares one or more
external-provider calls. The anchor for this SKELETON is the
`vulnerability_triage` workflow (F-WF-01, Shipped) — its triage
primitives already enumerate the dependency surface they read against
and it depends on the F-PT-03 supplier-attestation primitive set.

Indicators fed (lands in CORE-FANOUT):
`kri.suppliers_attestation_stale@v1` (already declared in
`content/mappings/nis2/article-21-2-d.yaml`) plus the new
`kpi.sovereign_provider_share@v1` and `kri.non_sovereign_call_surge@v1`
once they land in `content/metrics/` in the EXTEND-metrics sibling.

## Regulator hooks

| Regulation | Article          | Obligation paraphrase                                                                                                            | Mapping file                                                                       |
|------------|------------------|----------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| NIS2       | Art. 21(2)(d)    | Address supply-chain security including the security characteristics of direct suppliers and service providers, with periodic re-attestation. | [`content/mappings/nis2/article-21-2-d.yaml`](../../mappings/nis2/article-21-2-d.yaml) |
| NIS2       | Art. 22(1)       | The Cooperation Group, acting in cooperation with the Commission and ENISA, may carry out coordinated security risk assessments of specific critical supply chains; entities surface their dependency surface so a sectoral aggregate is feasible. | [`content/mappings/nis2/article-22.yaml`](../../mappings/nis2/article-22.yaml), companion narrative [`article-22-supply-chain.md`](../../mappings/nis2/article-22-supply-chain.md) |

## Artifact shape — field inventory

Each `dependencies-snapshot.json` artifact carries:

- `artifact_id` — deterministic SHA-256 of
  `<workflow_id>|<execution_id>|<captured_at>`. Two executions of the
  same workflow at the same instant against the same dependency set
  collide deliberately; same execution re-emitted does not.
- `workflow_id` — the workflow whose run produced the snapshot
  (`vulnerability_triage`, `incident-management`, …). One of the stable
  workflow ids declared in `content/playbooks/<workflow-id>/`.
- `execution_id` — per-execution id issued by the compile target's
  runtime. Re-runs of the same workflow_id produce distinct executions.
- `regulation_refs[]` — pin to every regulatory obligation the artifact
  satisfies (typically `nis2:art-21-2-d` plus, where applicable, the
  `nis2:art-22` aggregation atom once it lands).
- `control_refs[]` — control stable-ids attested by this artifact
  (typically `control.supplier_inventory@v1` and
  `control.provider_attestation@v1`).
- `dependencies[]` — one record per external dependency the execution
  resolved against. Each record carries:
  - `provider_id` — stable internal id for the provider (e.g.
    `provider.cve_feed_eu@v1`). Provider catalogue is operator-supplied;
    the framework ships the schema, not the catalogue.
  - `kind` — one of `software_dependency` (pinned library / SBOM line),
    `hosted_api` (external HTTP API), `data_feed` (subscription /
    threat-intel feed), `ai_provider` (LLM / embedding / inference
    endpoint), `managed_runtime` (PaaS / FaaS host).
  - `version` — version pin or commit SHA where applicable; `null` for
    moving-tag hosted services.
  - `call_count` — integer count of calls this execution issued
    against the provider (0 for "linked but not called this run").
  - `sovereignty_classification` — see the dedicated section below.
  - `attestation` — `{ state, last_reattested_at, next_due_at,
    attestation_ref }` mirror of the cadence vocabulary in
    [`schemas/attestation_state.json`](../../../schemas/attestation_state.json).
    `kri.suppliers_attestation_stale@v1` reads `next_due_at` against
    `captured_at`.
  - `risk_notes` — free-text rationale field. No individual contact
    names; provider identity only.
- `aggregates` — pre-computed counts the emitter may carry so
  downstream rollups skip re-derivation: `{ total_providers,
  sovereign_count, eu_hosted_count, non_eu_count, ai_provider_count }`.
- `owner` — role-shaped ownership pointer with `assigned_at` date. No
  individual personal names.
- `captured_at` — ISO-8601 UTC timestamp.
- `provenance` — `{ source_url, captured_at, commit_sha }` mirror of
  the pattern used in `content/controls/`.
- `retention` — optional ISO-8601 duration retention pointer; the
  community-default value is an open question to be settled in the
  EXTEND-retention sibling card, mirroring the equivalent F-CP-02 /
  F-CP-04 deferrals.

## Sovereign-provider classification (per F-CP-03 sovereign-stack constraint)

Each dependency record carries a `sovereignty_classification` object
with the following fields. The classification source-of-truth is an
operator-supplied private knowledge base; the framework repository
never ingests KB contents — see the existing note in
[`article-21-2-d.yaml`](../../mappings/nis2/article-21-2-d.yaml).
The contract here is the **shape** the emitter writes into the
artifact when the KB is consulted; a stub KB fixture lives under
`tests/fixtures/supply_chain/` (lands in EXTEND-tests-goldens).

Fields:

- `residency` — one of `eu`, `eea`, `eu_adequate_third_country`,
  `non_eu`, `unknown`. Where the provider runs the workload that
  produces the data the framework reads.
- `ownership` — one of `eu_owned`, `eu_majority_owned`,
  `non_eu_owned`, `unknown`. Beneficial-ownership pointer, NOT
  registered-office.
- `sub_processor_chain` — array of strings; opaque provider ids of
  declared sub-processors. Empty array if the provider declares none.
  `null` if the operator's KB has not captured the chain yet (distinct
  from "no sub-processors").
- `sovereignty_band` — single rolled-up verdict derived deterministically
  from `residency`, `ownership`, and `sub_processor_chain`. One of:
  - `sovereign` — `residency` ∈ {eu, eea} AND `ownership` ∈
    {eu_owned, eu_majority_owned} AND every sub-processor in the chain
    is itself `sovereign`.
  - `eu_hosted_non_sovereign` — `residency` ∈ {eu, eea} but the
    ownership or sub-processor-chain test fails.
  - `eu_adequate` — `residency` = `eu_adequate_third_country` under a
    standing adequacy decision; ownership and chain not load-bearing.
  - `non_eu` — `residency` = `non_eu`.
  - `unknown` — any of the three inputs is `unknown` or `null`.
- `band_rationale` — short free-text explanation pinning the band to
  the input triple. Read by reviewers; not parsed downstream.
- `kb_ref` — opaque pointer into the operator's private supplier-KB
  (e.g. `supplier-kb://provider-<id>/2026-Q2`). Framework never
  resolves this; it only carries the pointer for audit reproducibility.

The `sovereignty_band` rollup is a pure function of the three input
fields; the helper that computes it lands on the shared emitter in
CORE-FANOUT. Drift on the band between successive snapshots feeds the
drift-detection sibling.

## Promoted enums (lands in CORE-FANOUT)

Three small shared vocabularies will be promoted alongside this stream
when the JSON schema lands:

- `schemas/supply_chain_dependency_kind.json` — the five dependency
  kinds (`software_dependency`, `hosted_api`, `data_feed`,
  `ai_provider`, `managed_runtime`).
- `schemas/sovereignty_residency.json` — the five residency values.
- `schemas/sovereignty_band.json` — the five rolled-up bands.

These are intentionally small. Extending any of them is a discussion,
not a drive-by change, mirroring the F-CP-02 / F-CP-04 enum-promotion
pattern.

## What this SCHEMA card deliberately does **not** include

Out of scope for the SCHEMA card; each lands in a sibling:

- The shared emitter (`compilers/_shared/evidence/supply_chain.py`)
  and the three target adapters (Temporal, n8n, LangGraph) — CORE-FANOUT.
- Per-target byte-parity goldens — EXTEND-tests-goldens.
- Drift-detection hook for `sovereignty_band` transitions —
  EXTEND-drift sibling.
- KPI / KRI catalogue entries (`kpi.sovereign_provider_share@v1`,
  `kri.non_sovereign_call_surge@v1`) — EXTEND-metrics sibling.

## Contributor checklist (when the JSON schema lands)

1. The JSON Schema will become the source of truth — change
   `schemas/evidence/supply-chain.schema.json` first, then update this
   SCHEMA.md's at-a-glance summary if a field is added or removed.
2. The promoted enums above are intentionally small; extending any of
   them is a discussion, not a drive-by change.
3. The sovereign-provider classification fields read against an
   operator-supplied private KB; the framework repo never ingests KB
   contents. Fixtures used in tests are synthetic.
4. Run the content-model tests:

   ```sh
   python -m pytest tests/content_model/
   ```

5. Run the forward-public hygiene linter:

   ```sh
   python -m tools.hygiene_linter --min-severity LOW
   ```

6. Follow the
   [`AGENTS.md` §3 public-bar rules](../../../AGENTS.md): no commercial
   framing, no credentials, no internal infrastructure references, no
   individual lead names.
