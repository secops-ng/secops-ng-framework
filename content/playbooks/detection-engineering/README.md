# detection-engineering — F-WF-04

Source playbook for the **detection-engineering rule lifecycle**: a
deterministic four-state machine moving each rule version through
`propose → review → ship → measure`. The playbook lives next to the
other workflow source artifacts in `content/playbooks/` and binds to
the per-rule-version **effectiveness-metric snapshot** schema at
[`schemas/evidence/rule-effectiveness-snapshot.schema.json`](../../../schemas/evidence/rule-effectiveness-snapshot.schema.json).
The NIS2 Article 21(2)(f) entry at
[`content/mappings/nis2/article-21-2-f.yaml`](../../mappings/nis2/article-21-2-f.yaml)
points back at this playbook through `playbook_refs`.

## Maturity

`experimental` — the lifecycle state machine, step ids, transitions,
and schema references are wired and the schema gate passes. The n8n
reference emitter is wired: see
[`examples/n8n/detection-engineering/`](../../../examples/n8n/detection-engineering/)
for the compiled workflow artifact and the worked rule-effectiveness
snapshot. Gating predicates on `review → ship` / `ship → measure`,
per-target byte-parity goldens, and the cookbook walkthrough land in
follow-up sibling cards.

## What ships in this directory

- `playbook.cacao.yaml` — CACAO v2 + SecOps-NG content-model superset,
  expressed as YAML so it can carry the inline narrative and provenance
  comments alongside the schema-valid document. Four deterministic
  actions: `propose-rule-version`, `review-rule-version`,
  `ship-rule-version`, `measure-rule-version`. Transitions are
  unconditional in this artifact; gating predicates (review verdict,
  shipped-status check) land in follow-up sibling cards.
- The per-rule-version effectiveness-metric snapshot schema lives at
  [`schemas/evidence/rule-effectiveness-snapshot.schema.json`](../../../schemas/evidence/rule-effectiveness-snapshot.schema.json).
  It captures `definition`, `unit`, `calc_method`, OCSF `source_data`
  shape, and a `ref_viz` field for the reference visualisation hint
  the F-CP-06 effectiveness stream can consume.
- The NIS2 Article 21(2)(f) mapping entry references this playbook.

## Sovereign-stack constraint

Metric storage is operator-configured; no hosted SaaS default. The
effectiveness-snapshot schema only describes the shape; sinking the
snapshot to a store is the operator's choice resolved at the compile
target's config layer.

## Pending sibling work

Remaining lifecycle work tracked in `ROADMAP.md` § F-WF-04:

- **CORE-TEMPORAL / CORE-LANGGRAPH** — per-target compiler emission
  for Temporal and LangGraph, mirroring the n8n reference emitter
  already wired here.
- **Gating predicates** — the deterministic switch on the
  `review → ship` and `ship → measure` transitions.
- **Per-example byte-parity goldens** — per-target emitter goldens
  covering the four lifecycle states under
  `tests/examples/detection_engineering/`.
- **Cookbook walkthrough** at `docs/cookbook/detection-engineering.md`
  pairing this playbook with the F-CP-06 effectiveness evidence stream.

## See also

- [`ROADMAP.md`](../../../ROADMAP.md) § F-WF-04.
- [`examples/n8n/detection-engineering/`](../../../examples/n8n/detection-engineering/)
  — the n8n worked example: importable workflow and the
  per-rule-version effectiveness-snapshot artifact.
- [`schemas/evidence/effectiveness.schema.json`](../../../schemas/evidence/effectiveness.schema.json)
  — the F-CP-06 effectiveness evidence stream artifact. The
  per-rule snapshot from this playbook feeds that stream's
  `measurement` block.
- [`content/metrics/detection_coverage.yaml`](../../metrics/detection_coverage.yaml)
  and [`content/metrics/false_positive_rate.yaml`](../../metrics/false_positive_rate.yaml)
  — the indicator catalog entries the `measure` state binds against.
