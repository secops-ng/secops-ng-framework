# content/evidence/supply-chain/drift/

Supply-chain evidence stream — drift-detection layer (SKELETON).

This directory is the contributor home for the **drift-detection** layer
that sits on top of the supply-chain `dependencies-snapshot` artefact
shape declared in
[`../SCHEMA.md`](../SCHEMA.md) and pinned in
[`schemas/evidence/supply-chain.schema.json`](../../../../schemas/evidence/supply-chain.schema.json).

The shape here is **interface-only** in this card. No detector is
wired; no per-target compiler hook is added; no alerting or status
flip is performed. Those land in sibling cards — see § _Out of scope_
below.

## What "drift" means on this stream

Two `dependencies-snapshot.json` artefacts for the same workflow are
expected to be _stable across cadence walks_: the same workflow against
the same dependency surface, re-attested on schedule, produces a
deterministic shape. Drift is any meaningful difference between two
successive snapshots that an operator (and a regulator) needs to see.

For the supply-chain stream, the drift surface is:

- **Added dependency.** A `provider_id` appears in the current
  snapshot's `dependencies[]` that was not in the previous snapshot
  for the same `workflow_id`. New transitive providers are first-class
  drift — silently expanding the dependency surface is exactly what
  NIS2 Article 21(2)(d) periodic re-attestation is designed to surface.
- **Removed dependency.** A `provider_id` present in the previous
  snapshot is absent from the current one. Removed dependencies are
  drift too: they often mean a refactor or a provider de-listing and
  both need to be re-attested rather than disappear silently.
- **Version-bumped dependency.** Same `provider_id` is present in both
  snapshots but the `version` field changed (pinned-library bump, hosted
  API moving to a new major, AI provider model id rotated). Version
  bumps tend to come with new sub-processor chains and new data flows;
  they have to be re-attested even when the provider identity is stable.
- **Sovereignty-class change on a transitive provider.** Same
  `provider_id` and same `version`, but the
  `sovereignty_classification.sovereignty_band` rolled-up verdict moved
  between the two snapshots. A provider crossing from `sovereign` to
  `eu_hosted_non_sovereign` (or to/from `unknown`) is the signal the
  Article 22 Cooperation-Group overlay needs surfaced per-entity. The
  band vocabulary is pinned in
  [`schemas/sovereignty_band.json`](../../../../schemas/sovereignty_band.json);
  drift to or from `unknown` is treated as a first-class signal, not a
  free pass.

A drift record is the persistent, replayable summary of these deltas
between one `previous_snapshot_ref` and one `current_snapshot_ref`,
for one `workflow_id` series.

## Regulator hooks

| Regulation | Article | Why drift matters here |
|------------|---------|------------------------|
| NIS2 | Art. 21(2)(d) | Supply-chain risk management explicitly requires periodic re-attestation of suppliers and service providers, including the security characteristics of direct suppliers. Drift between cadence walks is what re-attestation is _for_. Mapping file: [`content/mappings/nis2/article-21-2-d.yaml`](../../../mappings/nis2/article-21-2-d.yaml). |
| NIS2 | Art. 22 | The Cooperation Group, in cooperation with the Commission and ENISA, may carry out coordinated security risk assessments of specific critical supply chains. Per-entity drift records make a sectoral aggregate feasible — the framework emits the per-entity signal; the Member-State aggregation envelope is out of scope here. Mapping file: [`content/mappings/nis2/article-22.yaml`](../../../mappings/nis2/article-22.yaml); companion narrative [`article-22-supply-chain.md`](../../../mappings/nis2/article-22-supply-chain.md). |

## Artefact shape — pointer

The drift-record shape is declared in
[`drift-record.schema.json`](drift-record.schema.json). A byte-stable
fixture exercising one **added** + one **removed** + one
**version-bumped** delta entry lives at
[`sample-drift-record.json`](sample-drift-record.json) for cross-stream
fixture wiring; a sovereignty-band-change fixture lands with the
CORE-FANOUT sibling that wires the detector.

At a glance, each drift record carries:

- `schema_version` — pinned to the drift-record schema.
- `id` — deterministic SHA-256 of
  `<workflow_id>|<previous_snapshot_ref>|<current_snapshot_ref>`. Two
  detectors run against the same pair collide deliberately.
- `stream` — constant `supply-chain` (this directory's stream).
- `workflow_id` — the workflow whose two snapshots are being diffed.
  One of the stable workflow ids declared in
  `content/playbooks/<workflow-id>/`.
- `previous_snapshot_ref` — `artifact_id` of the prior
  `dependencies-snapshot.json` in this `workflow_id` series.
- `current_snapshot_ref` — `artifact_id` of the current snapshot. The
  pair `(previous_snapshot_ref, current_snapshot_ref)` is the
  re-replayable input the detector consumes.
- `deltas[]` — one entry per detected change. Each delta carries:
  - `kind` — one of `added`, `removed`, `version_bumped`,
    `sovereignty_band_changed`. Extending this set is a discussion,
    not a drive-by change — see § _Promoted enums_ below.
  - `provider_id` — the provider the delta is about. Opaque
    operator-side id; the framework never resolves it.
  - `previous` — minimal pre-change snapshot of the fields relevant
    to `kind` (e.g. `{ version }` for `version_bumped`,
    `{ sovereignty_band }` for `sovereignty_band_changed`). `null`
    for `added`.
  - `current` — minimal post-change snapshot of the same fields.
    `null` for `removed`.
  - `note` — short free-text rationale field. No individual contact
    names; provider identity only, mirroring the SCHEMA.md `risk_notes`
    discipline.
- `detected_at` — ISO-8601 UTC timestamp the detector resolved this
  pair.

## Promoted enums (lands with detector wiring)

A small shared vocabulary will be promoted alongside the detector:

- `schemas/supply_chain_drift_kind.json` — the four delta kinds above
  (`added`, `removed`, `version_bumped`, `sovereignty_band_changed`).

The four-element vocabulary is intentionally small; extending it is
a discussion, mirroring the F-CP-02 / F-CP-03 / F-CP-04
enum-promotion pattern already established for the supply-chain
stream.

## Out of scope for this SKELETON card

Out of scope here; each lands in a sibling card under F-CP-03
EXTEND-drift:

- The detector implementation that consumes two
  `dependencies-snapshot.json` artefacts and emits one drift record —
  EXTEND-drift CORE-FANOUT sibling.
- Per-target compiler hooks (Temporal activity, n8n adapter, LangGraph
  node) that thread an optional `drift_hook` callable through the
  shared emitter — EXTEND-drift CORE-FANOUT sibling. The risk-analysis
  hook surface at `compilers/_shared/evidence/drift_hook.py` is the
  reference pattern to mirror when that card opens.
- Alerting and status-flip work — separate siblings; not part of
  EXTEND-drift.
- Promotion of `schemas/supply_chain_drift_kind.json` — lands with
  the detector, not in this SKELETON.
- The F-CP-03 ROADMAP status flip — gated by EXTEND-drift,
  EXTEND-metrics, and EXTEND-NIS2-MAPPING all landing.

## Contributor checklist

1. The schema is the source of truth — change
   `drift-record.schema.json` first, then update this DRIFT.md's
   at-a-glance summary if a field is added or removed.
2. The `kind` vocabulary above is intentionally small; extending it is
   a discussion, not a drive-by change.
3. Drift records reference snapshot `artifact_id` values; the
   framework never resolves opaque operator-side ids carried inside.
4. Run the content-model tests:

   ```sh
   python -m pytest tests/content_model/
   ```

5. Run the forward-public hygiene linter:

   ```sh
   python -m tools.hygiene_linter --min-severity LOW
   ```

6. Follow the
   [`AGENTS.md` §3 public-bar rules](../../../../AGENTS.md): no
   commercial framing, no credentials, no internal infrastructure
   references, no individual lead names.
