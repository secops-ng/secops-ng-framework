# NIS2 Article 21(2)(f) — Effectiveness evidence schema

Companion narrative to the structural mapping in
[`article-21-2-f.yaml`](./article-21-2-f.yaml). This document
explains how the **effectiveness evidence stream** under
[`content/evidence/effectiveness/`](../../evidence/effectiveness/README.md)
discharges the NIS2 Article 21(2)(f) obligation — *policies and
procedures to assess the effectiveness of cybersecurity
risk-management measures, with results archived* — how the schema is
referenced (not duplicated) here, and how the per-execution snapshot
shape pins each indicator value to a specific policy version or
prompt version.

This file is contributor-facing prose. The structural crosswalk
(`obligation`, `control_refs`, `metric_refs`, `evidence_stream_refs`)
remains the single source of truth in
[`article-21-2-f.yaml`](./article-21-2-f.yaml); change that file when
the mapping itself changes.

## Scope

- **In:** how the effectiveness evidence stream's per-snapshot
  artifact shape satisfies the assessment-and-archival obligation in
  NIS2 Article 21(2)(f); pointers to the typed schema, to the
  reference metric in the catalogue, and to the per-target reference
  emitters once the CORE-FANOUT sibling lands.
- **Out:** legal interpretation of Article 21(2)(f); duplication of
  the schema body (the JSON Schema is canonical and must not be
  mirrored here); duplication of the metric catalogue body (the
  catalogue's `unit`, `direction`, `thresholds`, and `formula` remain
  the source of truth and are not re-declared on the snapshot); the
  drift-detection surface for this stream — that ships in the
  EXTEND-drift sibling card; KPI/KRI emission wiring — that is the
  CORE-FANOUT sibling.

## How the snapshot discharges the obligation

Article 21(2)(f) reads against two operator-side responsibilities:

1. **Assessment.** The operator runs an indicator against the
   risk-management measures the organisation has adopted, on a
   declared cadence, and surfaces the value the indicator took.
2. **Archival.** The operator retains the results, pinned to the
   specific version of the policy or prompt that was in force when
   the indicator was measured, so a regulator can re-derive whether
   the indicator was moving against the *current* risk-management
   surface or a stale one.

The framework's contribution is the per-snapshot artifact shape that
makes both responsibilities reviewable at the per-execution layer:

- `metric_ref` pins the indicator (a `kpi.<slug>@v<semver>` or
  `kri.<slug>@v<semver>` stable-id from `content/metrics/`).
- `subject_version` pins what the indicator was measured against,
  with a mechanical `kind` of `policy_version` or `prompt_version`
  and a semver-shaped or 64-hex content-hash `value`. The two kinds
  are kept distinct because policy text and prompt-anchored agentic
  surfaces re-version on different cadences, and a reviewer needs to
  see which surface a movement in the indicator is attributable to.
- `measurement.value` carries the value the indicator took;
  `measurement.unit`, `measurement.direction`, and
  `measurement.threshold_crossed` mirror the catalogue declaration so
  a downstream consumer can render the snapshot without re-walking
  the catalogue.
- `measurement.source_shape` carries a pointer to the source-data
  shape the indicator was derived from — typically an OCSF event
  class (`class_uid` and `class_name`) — *not* the underlying sample
  payload. The underlying sample may carry personal data; the
  source-shape pointer is the public-bar-safe surface a reviewer
  needs to confirm the indicator is reading from the right shape.
- `captured_at` and `retention` discharge the archival half: the
  snapshot is timestamped and carries the operator's retention
  pointer. The upstream control's `review_cadence` (declared on
  `control.control_effectiveness_test@v1`) tells a reviewer whether
  the most recent snapshot is in cadence.

## Schema — pointer, not copy

The effectiveness-evidence artifact shape is documented once, in the
authoritative JSON Schema:

- **Stream root (this card):**
  [`content/evidence/effectiveness/README.md`](../../evidence/effectiveness/README.md)
- **Authoritative JSON Schema (this card):**
  [`schemas/evidence/effectiveness.schema.json`](../../../schemas/evidence/effectiveness.schema.json)

The stream README is the human-facing entry point; the JSON Schema is
the machine-checkable contract. **Do not duplicate the schema body in
this file.** If a field name, type, or constraint changes, the schema
file is the source of truth and the stream README's at-a-glance
summary is updated alongside it; this mapping document only changes
when the *mapping* between the stream and the regulatory clause
changes.

## Reference indicator

The reference indicator the F-CP-06 stream reads against is the
catalogue's
[`kri.control_effectiveness@v1`](../../../metrics/control_effectiveness.yaml).
The catalogue entry is the source of truth for the indicator's unit,
direction, thresholds, and measurement formula; the snapshot artifact
carries the per-evaluation value and pins it to a specific policy or
prompt version. The schema deliberately accepts any
`kpi.<slug>@v<semver>` or `kri.<slug>@v<semver>` stable-id so the
catalogue can grow without a schema bump.

Two KPI/KRI siblings feed against the same stream:

- `kpi.control_effectiveness_coverage@v1` — coverage of the in-scope
  control set by an in-cadence effectiveness test.
- `kri.overdue_effectiveness_tests@v1` — count of controls whose most
  recent effectiveness test predates the declared review cadence.

The catalogue-side promotions and the closed declaration of the
F-CP-06 stream's consumers are decided in the EXTEND-metrics sibling
card; the SKELETON here just pins the per-snapshot artifact shape.

## Status

SKELETON card landed: the authoritative JSON Schema at
[`schemas/evidence/effectiveness.schema.json`](../../../schemas/evidence/effectiveness.schema.json),
the stream-root README at
[`content/evidence/effectiveness/README.md`](../../evidence/effectiveness/README.md),
and this Article 21(2)(f) companion narrative. The structural
`nis2:art-21-2-f` atom in [`article-21-2-f.yaml`](./article-21-2-f.yaml)
declares `evidence_stream_refs: [effectiveness]`. The shared emitter,
the per-target adapters, the worked example, the byte-parity goldens,
the drift hook, the metric-catalogue promotions, and the F-WF-09
auditor-bundle slot land in their named sibling cards under F-CP-06.

## See also

- [`article-21-2-f.yaml`](./article-21-2-f.yaml) — structural atom
  this overlay reads against.
- [`../../evidence/effectiveness/README.md`](../../evidence/effectiveness/README.md)
  — stream record-schema narrative.
- [`../../metrics/control_effectiveness.yaml`](../../metrics/control_effectiveness.yaml)
  — reference indicator.
- ROADMAP entry: F-CP-06 — Effectiveness stream.
