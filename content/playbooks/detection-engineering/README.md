# detection-engineering — F-WF-04 SKELETON

Source playbook for the **detection-engineering rule lifecycle**: a
deterministic four-state machine moving each rule version through
`propose → review → ship → measure`. The playbook lives next to the
other workflow source artifacts in `content/playbooks/` and binds to
the per-rule-version **effectiveness-metric snapshot** schema stub at
[`schemas/evidence/rule-effectiveness-snapshot.schema.json`](../../../schemas/evidence/rule-effectiveness-snapshot.schema.json).
The NIS2 Article 21(2)(f) entry at
[`content/mappings/nis2/article-21-2-f.yaml`](../../mappings/nis2/article-21-2-f.yaml)
points back at this playbook through `playbook_refs`.

## Maturity

`SKELETON` — the lifecycle state machine, step ids, transitions, and
schema references are wired so downstream compilers can be primed and
the schema gate passes. Action bodies are placeholders. No compiler
fan-out yet (no n8n / Temporal / LangGraph emitter goldens).

## What ships in this card

- `playbook.cacao.yaml` — CACAO v2 + SecOps-NG content-model superset,
  expressed as YAML. Four deterministic actions: `propose-rule-version`,
  `review-rule-version`, `ship-rule-version`, `measure-rule-version`.
  Transitions are unconditional in the SKELETON; gating predicates
  (review verdict, shipped-status check) land in CORE-FANOUT.
- `schemas/evidence/rule-effectiveness-snapshot.schema.json`
  (under `schemas/`, not this directory) — per-rule-version
  effectiveness-metric snapshot stub. Captures `definition`,
  `unit`, `calc_method`, OCSF `source_data` shape, and a `ref_viz`
  field for the reference visualisation hint the F-CP-06
  effectiveness stream can consume.
- NIS2 Article 21(2)(f) mapping entry updated to reference this
  playbook.

## Sovereign-stack constraint

Metric storage is operator-configured; no hosted SaaS default. The
effectiveness-snapshot schema only describes the shape; sinking the
snapshot to a store is the operator's choice resolved at the compile
target's config layer.

## Pending sibling cards (named, not yet opened)

The remaining work decomposes into three siblings that land after this
SKELETON merges:

- **F-WF-04 CORE-FANOUT** — per-target compiler emission for n8n /
  Temporal / LangGraph, plus the deterministic gating predicates on the
  `review → ship` and `ship → measure` transitions. Includes the
  per-target reference emitters for the per-rule-version
  effectiveness-snapshot artifact.
- **F-WF-04 EXTEND-tests-goldens** — per-example byte-parity goldens
  under `tests/examples/detection_engineering/` and per-target
  emitter goldens covering the four lifecycle states.
- **F-WF-04 EXTEND-docs** — cookbook walkthrough at
  `docs/cookbook/detection-engineering.md`, plus the contributor
  narrative that pairs this playbook with the F-CP-06 effectiveness
  evidence stream.

## See also

- [`ROADMAP.md`](../../../ROADMAP.md) § F-WF-04.
- [`schemas/evidence/effectiveness.schema.json`](../../../schemas/evidence/effectiveness.schema.json)
  — the F-CP-06 effectiveness evidence stream artifact. The per-rule
  snapshot stub in this card feeds that stream's `measurement` block.
- [`content/metrics/detection_coverage.yaml`](../../metrics/detection_coverage.yaml)
  and [`content/metrics/false_positive_rate.yaml`](../../metrics/false_positive_rate.yaml)
  — the indicator catalog entries the `measure` state will bind
  against once CORE-FANOUT lands.
