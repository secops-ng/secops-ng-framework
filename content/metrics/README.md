# content/metrics/ — KPI / KRI catalog

The metrics catalog is a curated set of operational and risk indicators
that playbooks, detections, and controls in this framework reference by
stable identifier. It is intentionally a thin overlay: SecOps-NG does
not define a new metrics standard. Each entry names a common operator
metric (MTTD, MTTR, coverage, false-positive rate, control
effectiveness, …) and binds it to the lower content layers through the
shared `stable_id` shape used everywhere else in the content model.

## Scope

The catalog answers, for every metric a playbook author wants to emit
or affect:

- What does this metric mean, in one paragraph an operator can read?
- What inputs does it consume — which telemetry classes, detections,
  controls, or playbook step transitions?
- How is it aggregated (p95 latency, ratio, count, …) and over what
  window?
- Is lower or higher better, and what target / threshold bands does the
  community recommend?
- Which upstream regulatory references (NIS2, DORA, ENISA guidance,
  ISO 27004, CIS measures) motivate it?

The catalog is **not** an executable runtime. It is the contract.
Compile targets (n8n / Temporal / LangGraph references in this repo,
plus any community-contributed compiler) are the source of truth for
the executable form.

## ID convention

Stable identifier shape is shared with every other content layer:

```
<namespace>.<slug>@v<major>[.<minor>[.<patch>]]
```

For the metrics catalog the namespace MUST be one of:

- `kpi.*` — performance indicator (how well operations are running),
- `kri.*` — risk indicator (how much residual exposure remains).

The namespace prefix and the `kind` field must agree. The full lexical
shape and the kpi/kri agreement constraint are enforced by the schema.

Examples:

- `kpi.mttd_critical@v1` — mean time to detect, critical-severity
  scope, content version 1.
- `kri.control_effectiveness@v1` — residual exposure indicator from
  control attestation state.

## KPI vs KRI — when to pick which

| Question                                                | Answer is a |
|---------------------------------------------------------|-------------|
| "How fast / well / completely did we run an operation?" | KPI         |
| "How much residual risk remains after our controls?"    | KRI         |

A latency or completion rate is almost always a KPI. A coverage gap, a
suppression rate, an overdue-effectiveness ratio, or a regulator
notification overrun is almost always a KRI. When in doubt, ask
whether the value rising is bad news for the operator (KRI) or for the
ops team's running scorecard (KPI).

## Link policy — how playbooks reference catalog entries

A shipped playbook MUST reference a metric by its catalog `stable_id`,
not by inlining its definition. The two link directions are:

1. **Playbook → metric.** Playbook KPI/KRI hooks list catalog
   `stable_id`s in their `metric_ref` (or equivalent) field.
2. **Metric → playbook.** Catalog entries MAY list `playbook_refs`,
   each pointing to a playbook `stable_id` and optionally pinning a
   specific step. This is documentation; the linter checks target
   existence.

The same shape applies to `detection_refs`, `control_refs`, and
`telemetry_refs` on catalog entries — they bind to the corresponding
layers' `stable_id`s.

OSCAL/D3FEND control mappings under `content/mappings/` may also
reference catalog metrics when a control's effectiveness is defined in
terms of a KPI or KRI; the link direction is the same — by
`stable_id`, never by inlined definition.

## Schema location

The canonical schema for catalog entries lives at:

- `content-model/metrics.schema.json` — JSON Schema Draft 2020-12.

The `content/metrics/_schema/metric.schema.json` file in this
directory is a thin pointer that re-exports the canonical schema, so
catalog authors and validators inside `content/metrics/` can resolve
the schema with a local relative path.

## File layout

```
content/metrics/
├── README.md                   # this file
├── _schema/
│   └── metric.schema.json      # pointer to content-model/metrics.schema.json
├── mttd.yaml                   # seed KPI entry (SKELETON exemplar)
├── mttr.yaml                   # KPI: mean time to respond (critical)
├── detection_coverage.yaml     # KPI: ATT&CK technique coverage
├── false_positive_rate.yaml    # KPI: FP/(FP+TP) per detection class
├── control_effectiveness.yaml  # KRI: residual exposure from attestations
└── …                           # one YAML per catalog entry
```

One catalog entry per YAML file. The filename SHOULD be the slug
portion of the `stable_id` (e.g. `mttd_critical.yaml` for
`kpi.mttd_critical@v1`); the seed entry uses the short form
`mttd.yaml` as a deliberately minimal exemplar.

## Forward-public hygiene reminder

Per the project directive on forward-public hygiene, every catalog
entry — fields, prose, `maintainer`, `external_refs` — must already
pass the public-release bar: community-neutral language, no commercial
framing, no individual contact names (generic role mailboxes only), no
internal infra references, no credentials.

## Current state (v0 SKELETON)

This is the SKELETON layer. It scaffolds the directory, the schema
pointer, the validation test harness, and one canonical seed entry
(`mttd.yaml`). CORE and EXTEND follow-on tasks populate the rest of
the catalog (MTTR, coverage %, false-positive %, dwell-time,
control-effectiveness, risk metrics) and cross-link every shipped
playbook's KPI hooks to a catalog entry.
