# Worked example: `playbook.executive_metrics_rollup@v1`

SKELETON scope: portable CACAO v2 artifact for the **executive metrics
rollup** scenario, mirroring the shape of
`content-model/examples/data-exfil/` and
`content-model/examples/vuln-intake/`.

The rollup is a recurring monthly aggregation of the operator's KPI/KRI
catalog into a board-ready summary plus a control-effectiveness score.
It anchors NIS2 Article 21(2)(f) — effectiveness assessment — and DORA
Article 6 — ICT risk-management framework periodic review — without
prescribing a specific board-pack template.

## Files

| Layer       | File                  | Stable ID                                  |
|-------------|-----------------------|--------------------------------------------|
| Playbook    | `playbook.json`       | `playbook.executive_metrics_rollup@v1`     |

The portable CACAO v2 fixture the compilers consume is also published
at `tests/compilers/_shared/fixtures/executive_metrics_rollup.cacao.json`
so the shared parser and per-target compiler suites can pick it up
without reaching into `content/`.

## Workflow shape

5-step CACAO workflow:

1. `resolve KPI/KRI catalog` — load the operator's pinned catalog
   version; entries that fail `content-model/metrics.schema.json` are
   recorded for the catalog-staleness KRI and excluded.
2. `evaluate metrics over window` — compute each metric's
   `measurement.formula` against the operator's telemetry / workflow /
   control-attestation source for the requested ISO-8601 window.
3. `score control effectiveness` — group evaluations by `control_refs[]`
   and emit a programme-level score in `0.0..1.0`.
4. `if-condition: any breach band hit?` — branches into a board-attention
   annotation step on true; both branches converge on the emit step so
   the rollup is single-output.
5. `emit board summary` — hand the structured summary artifact off to
   the operator's board-pack pipeline. Content-only — distribution is
   out of scope.

## Stable-ID index

- `playbook.executive_metrics_rollup@v1` — this playbook
- `kpi.control_effectiveness_coverage@v1`
- `kri.overdue_effectiveness_tests@v1`
- `kri.metrics_catalog_staleness@v1`
- `control.metrics_catalog_governance@v1`
- `control.control_effectiveness_test@v1`
- `telemetry.ocsf.security_finding@v1`

The metric / control / telemetry bodies and their cross-reference graph
land with the CORE card; SKELETON only pins the playbook and the
identifier set it joins to.

## Sigma references

Intentionally empty. The executive metrics rollup is an aggregate
reporting workflow — it consumes KPI / KRI evaluations the lower layers
already produced and does not emit or consume detection signals. No
upstream SigmaHQ rule IDs cleanly apply, so the playbook's
`detection_refs` is `[]` rather than carrying invented identifiers. If
the operator's catalog later exposes a detection-coverage KPI sourced
from a specific Sigma rule, the CORE / EXTEND cards add the pointer
there — never here.

## Cross-reference graph (skeleton)

```
                  playbook.executive_metrics_rollup@v1
                  (CACAO v2 + x_secops_ng)
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
  control.metrics_     control.control_       telemetry.ocsf.
  catalog_governance@  effectiveness_         security_finding@v1
  v1                   test@v1                       │
                              │                     │
                              ▼                     ▼
                kpi.control_effectiveness_coverage@v1
                kri.overdue_effectiveness_tests@v1
                kri.metrics_catalog_staleness@v1
```

## How to validate locally

```
cd secops-ng-framework
pytest tests/ -q
```

The content-model test suite validates the playbook against
`content-model/playbook.schema.json`. The shared parser fixture suite
will pick up the new portable CACAO file via the standard
`tests/compilers/_shared/fixtures/` glob when CORE wires the parser
against it.

## Out of scope here

- Compiler outputs (`examples/{n8n,temporal,langgraph}/executive-metrics-rollup/`)
  and the golden-byte tests. Owned by the CORE card.
- Regulatory overlay / metrics-mapping wiring into NIS2 Art. 21(2)(f)
  and DORA Art. 6. Owned by the EXTEND card.
- Control / detection / telemetry / metric bodies and their bidirectional
  graph. Owned by CORE.
