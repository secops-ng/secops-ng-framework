# DORA Article 19 report variant — worked example (Temporal)

This example shows the F-WF-05 `incident_management` workflow producing
the four DORA Article 19 reporting-chain artifacts for one
representative major ICT-related incident, persisted through the
Temporal-side activity adapter at
`compilers.temporal.evidence.emit_dora_art19_report_activity`.

Regulatory anchors:

- **Regulation (EU) 2022/2554 (DORA), Article 19(4)** — reporting
  milestones for major ICT-related incidents (initial / intermediate /
  final).
- **Regulation (EU) 2022/2554 (DORA), Article 19(2)** — voluntary
  notification of significant cyber threats.
- **Commission Delegated Regulation (EU) 2024/1772** — RTS on the
  classification of major ICT-related incidents (Article 18(1)
  classifier).
- **Commission Implementing Regulation (EU) 2024/2956** — ITS on
  standard forms, templates and procedures (out of scope at the CORE
  layer; the EXTEND sibling card pins the field-level vocabulary).

The four artifacts committed under `evidence/`:

| File | Variant | Article 19 milestone |
|------|---------|----------------------|
| `evidence/initial_4h.report.json` | `initial_4h` | 19(4)(a) — 4h initial notification |
| `evidence/intermediate_72h.report.json` | `intermediate_72h` | 19(4)(b) — 72h intermediate report |
| `evidence/final_1mo.report.json` | `final_1mo` | 19(4)(c) — one-month final report |
| `evidence/voluntary_cyber_threat.report.json` | `voluntary_cyber_threat` | 19(2) — voluntary cyber-threat notification (separate precursor) |

Each artifact conforms to
`schemas/evidence/dora-art19-technical-incident-report.schema.json`.
The `report_id` is deterministic on
`SHA-256(<incident_id>|<report_variant>|<submitted_at>)` per the
schema; a replay of the same submission is byte-identical and the
sibling Temporal / n8n / LangGraph adapters produce byte-identical
records for the same input.

## Regeneration

```sh
PYTHONPATH=. python examples/temporal/dora_art19_report/regenerate.py
```

The Temporal sibling owns the canonical typed contexts; the n8n and
LangGraph siblings import the same `CONTEXTS` and re-drive their
target's adapter so cross-target byte-parity holds at the
artifact-bytes level.

## Public-bar notes

- No individual personal names or operator branding on any free-text
  field.
- No internal infrastructure references on the `provenance.source_url`
  — the URL points at the worked-example's documented illustrative
  endpoint.
- The narrative belongs to the community / NGO voice — a reviewer
  re-derives every value from the canonical inputs pinned in
  `regenerate.py`.

## Out-of-scope siblings

- **CORE-CLASSIFIER** — the DORA Article 18(1) classifier rule pack
  and its integration into the F-WF-05 classification primitive.
- **EXTEND-SCHEMA** — shared vocabularies at
  `schemas/dora_data_impact.json` and
  `schemas/dora_mitigation_state.json`, plus the Commission ITS (EU)
  2024/2956 field-level tightening of `impact_indicators`.
- **EXTEND-METRICS** — per-milestone on-time KPI specs
  (`kpi.dora_initial_4h_on_time@v1`, etc.) that complement the
  existing NIS2 Art. 23 milestone KPIs.
