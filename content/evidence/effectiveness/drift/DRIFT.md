# content/evidence/effectiveness/drift/

Effectiveness evidence stream — drift-detection layer (SKELETON).

This directory is the contributor home for the **drift-detection** layer
that sits on top of the effectiveness snapshot artifact shape declared
in
[`../README.md`](../README.md) and pinned in
[`schemas/evidence/effectiveness.schema.json`](../../../../schemas/evidence/effectiveness.schema.json).

The shape here is **interface-only** in this card. No detector is
wired; no per-target compiler hook is added; no alerting or status
flip is performed. Those land in sibling cards — see § _Out of scope_
below.

## What "drift" means on this stream

The effectiveness evidence stream emits one snapshot per (metric,
policy-or-prompt-version, evaluation-window) — the numeric value an
effectiveness indicator took at evaluation time, pinned to the
specific policy version or prompt version in force then. Two
effectiveness snapshots for the same `workflow_id` series — successive
cadence walks of the periodic effectiveness assessment, against the
same `subject_version` — are expected to be _stable across walks_:
the same workflow, evaluated against the same policy or prompt
version, against the same metric set, produces a deterministic
shape. Drift is any meaningful difference between two successive
walks that an operator (and a regulator) needs to see.

For the effectiveness stream, the drift surface is:

- **Added metric.** A `metric_ref` (`kpi.<slug>@v<semver>` or
  `kri.<slug>@v<semver>`) appears in the current walk that was not
  measured in the previous walk for the same
  `(workflow_id, subject_version)` pair. A new indicator entering the
  cadence is first-class drift — silently broadening the metric set
  is exactly what NIS2 Article 21(2)(f) periodic effectiveness
  assessment is designed to surface.
- **Removed metric.** A `metric_ref` present in the previous walk is
  absent from the current one. Removed indicators are drift too: they
  often mean a metric was retired, a control was descoped, or a
  cadence walk dropped a check, and all three need to be re-attested
  rather than disappear silently.
- **Value regressed.** Same `metric_ref` on both sides, but the
  measured value moved in the wrong direction (per the indicator's
  `direction` — `lower_is_better` or `higher_is_better`) past an
  operator-defined regression band. The regression band is out of
  scope on this schema; it lives with the detector wiring. A
  regression is the signal `kri.control_effectiveness@v1` exists to
  catch.
- **Threshold crossed.** Same `metric_ref` on both sides, and the
  catalogue-defined threshold tier the measurement rolls into
  changed between walks (e.g. `none` → `warn`, `warn` → `breach`).
  Tier movement is drift independent of magnitude — moving from
  `none` to `warn` matters even when the absolute regression is
  small. The threshold vocabulary mirrors the catalogue's
  `thresholds[].name` plus the implicit `none` value used when no
  threshold was crossed.
- **Source-shape changed.** Same `metric_ref` on both sides, but the
  pointer to the source-data shape the indicator was derived from
  (`measurement.source_shape`) moved between the two walks — a
  different OCSF event class, a different telemetry URN, or a swap
  to or from `none`. A source-shape change without a metric-version
  bump is drift because the indicator is now reading against a
  different upstream contract; downstream consumers need to see
  that the formula's input shape changed even when the formula's
  stable-id did not.

A drift record is the persistent, replayable summary of these deltas
between one `previous_artifact_ref` and one `current_artifact_ref`,
for one `workflow_id` series, against one pinned `subject_version`.

## Regulator hooks

| Regulation | Article | Why drift matters here |
|------------|---------|------------------------|
| NIS2 | Art. 21(2)(f) | Policies and procedures to assess the effectiveness of cybersecurity risk-management measures, with results archived. Drift between cadence walks is what periodic effectiveness assessment is _for_ — a regression in `kri.control_effectiveness@v1`, a dropped check, or a swapped source shape is exactly the signal the operator (and a regulator) needs surfaced. Mapping file: [`content/mappings/nis2/article-21-2-f.yaml`](../../../mappings/nis2/article-21-2-f.yaml); companion narrative [`article-21-2-f-effectiveness.md`](../../../mappings/nis2/article-21-2-f-effectiveness.md). |

## Artifact shape — pointer

The drift-record shape is declared in
[`drift-record.schema.json`](drift-record.schema.json). A byte-stable
fixture exercising one **metric_added** + one **value_regressed** +
one **threshold_crossed** delta entry lives at
[`sample-drift-record.json`](sample-drift-record.json) for cross-stream
fixture wiring; a source-shape-change fixture lands with the
CORE-FANOUT sibling that wires the detector.

At a glance, each drift record carries:

- `schema_version` — pinned to the drift-record schema.
- `id` — deterministic SHA-256 of
  `<workflow_id>|<subject_version.value>|<previous_artifact_ref>|<current_artifact_ref>`.
  Two detectors run against the same pair collide deliberately.
- `stream` — constant `effectiveness` (this directory's stream).
- `workflow_id` — the workflow whose two effectiveness walks are
  being diffed. One of the stable workflow ids declared in
  `content/playbooks/<workflow-id>/`.
- `subject_version` — `{ kind: policy_version | prompt_version,
  value }`. The thing the two walks evaluated against; the pair
  shares one subject version by construction. Mixed-subject diffs are
  intentionally out of scope at this layer — they would conflate a
  version bump with an indicator movement.
- `previous_artifact_ref` — `artifact_id` of the prior effectiveness
  snapshot anchoring the previous cadence walk in this
  `(workflow_id, subject_version)` series.
- `current_artifact_ref` — `artifact_id` of the current effectiveness
  snapshot anchoring the current walk. The pair
  `(previous_artifact_ref, current_artifact_ref)` is the
  re-replayable input the detector consumes. The operator-side
  resolution from these anchor refs to the full metric set of the
  walk is out of scope on this schema; it lives with the detector
  wiring.
- `deltas[]` — one entry per detected change. Each delta carries:
  - `kind` — one of `metric_added`, `metric_removed`,
    `value_regressed`, `threshold_crossed`, `source_shape_changed`.
    Extending this set is a discussion, not a drive-by change — see §
    _Promoted enums_ below.
  - `metric_ref` — the `kpi.<slug>@v<semver>` /
    `kri.<slug>@v<semver>` indicator the delta is about. Mirror of
    `metric_ref` on the effectiveness schema.
  - `previous` — minimal pre-change snapshot of the fields relevant
    to `kind` (e.g. `{ value, unit, direction }` for
    `value_regressed`, `{ threshold }` for `threshold_crossed`,
    `{ source_shape }` for `source_shape_changed`). `null` for
    `metric_added`.
  - `current` — minimal post-change snapshot of the same fields.
    `null` for `metric_removed`.
  - `note` — short free-text rationale field. No individual contact
    names; role-shaped owner identifiers only, mirroring the
    effectiveness SCHEMA `owner.role` discipline.
- `detected_at` — ISO-8601 UTC timestamp the detector resolved this
  pair.

## Promoted enums (lands with detector wiring)

A small shared vocabulary will be promoted alongside the detector:

- `schemas/effectiveness_drift_kind.json` — the five delta kinds
  above (`metric_added`, `metric_removed`, `value_regressed`,
  `threshold_crossed`, `source_shape_changed`).

The five-element vocabulary is intentionally small; extending it is a
discussion, mirroring the F-CP-02 / F-CP-03 / F-CP-04 / F-CP-07
enum-promotion pattern already established on the sibling streams.

## Out of scope for this SKELETON card

Out of scope here; each lands in a sibling card under F-CP-06
EXTEND-drift:

- The detector implementation that consumes two effectiveness
  snapshots (and the operator-side resolution to the full metric
  set of each cadence walk) and emits one drift record —
  EXTEND-drift CORE-FANOUT sibling.
- The operator-side regression-band table that resolves whether a
  same-`metric_ref`, same-`direction` value move counts as a
  regression — lives with the detector wiring, not with this
  interface-only schema.
- The catalogue-side mapping from raw measurement values to
  threshold tiers (`none` / `warn` / `breach` / `critical`) — the
  tier vocabulary is pinned here; the resolution table lives with
  the detector wiring.
- Per-target compiler hooks (Temporal activity, n8n adapter,
  LangGraph node) that thread an optional `drift_hook` callable
  through the shared emitter — EXTEND-drift CORE-FANOUT sibling. The
  risk-analysis hook surface at
  `compilers/_shared/evidence/drift_hook.py` is the reference pattern
  to mirror when that card opens.
- Alerting and status-flip work — separate siblings; not part of
  EXTEND-drift.
- Promotion of `schemas/effectiveness_drift_kind.json` — lands with
  the detector, not in this SKELETON.
- The F-CP-06 ROADMAP status flip — gated by EXTEND-drift,
  EXTEND-metrics, and EXTEND-NIS2-MAPPING all landing.

## Contributor checklist

1. The schema is the source of truth — change
   `drift-record.schema.json` first, then update this DRIFT.md's
   at-a-glance summary if a field is added or removed.
2. The `kind` vocabulary above is intentionally small; extending it is
   a discussion, not a drive-by change.
3. Drift records reference effectiveness `artifact_id` values; the
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
