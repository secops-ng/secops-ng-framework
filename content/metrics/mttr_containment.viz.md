# Reference visualisation — `kpi.mttr_containment@v1`

This is the committed reference-visualisation artifact for the
containment-scoped mean-time-to-respond KPI (all incidents). It
exists so the G-04 catalog definition-of-done (a *committed*
reference visualisation, not a narrated one) is closed; downstream
compile targets (n8n / Temporal / LangGraph) read the same metric
YAML and render the executable form in their own dashboard surface.
The artifact here is the contract for the chart shape, not the
executable chart.

## Chart kind

Horizontal bar chart, one bar per incident closed within the
evaluation window whose response playbook reached the canonical
containment step, sorted by `remediation_latency_minutes` descending
so the slowest containment sits at the top. The `p95` aggregate is
the headline figure operators read first; the per-incident bars are
the supporting drill-down that names *which* incidents pulled the
tail.

- **x-axis:** `remediation_latency_minutes` — minutes between
  `first_detection_fire_timestamp` and
  `first_response_action_timestamp` (containment step) for each
  closed in-scope incident in the window.
- **y-axis:** one row per closed in-scope incident, labelled by the
  case `incident.uid`; sorted by latency descending so the worst-case
  incidents sit at the top.
- **Threshold overlays:** the unscoped baseline catalog entry
  (`kpi.mttr_critical@v1`) carries the warn (60 min) and breach (240
  min) thresholds; this scoped variant inherits the threshold-band
  shape but does not redeclare numeric values — the reference
  rendering shows the inherited band positions so operators reading
  the chart see the same band geometry as the unscoped baseline.
- **Headline annotation:** the `p95` aggregate across closed in-scope
  incidents, annotated as the metric value.

## Reference rendering (Mermaid)

The mermaid block below is the canonical reference rendering — small
enough to live in-tree and renderable directly on the public repo
surface. The numeric values are illustrative; the compile target is
the source of truth for the executable form against operator data.

```mermaid
---
config:
    xyChart:
        showTitle: true
        chartOrientation: horizontal
title: "kpi.mttr_containment@v1 — remediation latency to containment per closed incident (P30D window)"
---
xychart-beta horizontal
    title "minutes from first detection fire to first containment action"
    x-axis "incident (closed in window)" ["case-K1", "case-K2", "case-K3", "case-K4", "case-K5"]
    y-axis "remediation_latency_minutes" 0 --> 360
    bar [295, 160, 85, 45, 20]
```

Reading the bars in this illustrative rendering, referencing the
unscoped baseline thresholds for context:

| case    | remediation_latency_minutes | band (vs. kpi.mttr_critical@v1) | reading                                          |
|---------|-----------------------------|---------------------------------|--------------------------------------------------|
| case-K1 | 295                         | breach                          | above 240-min breach floor                       |
| case-K2 | 160                         | warn                            | above 60-min warn floor, below breach            |
| case-K3 | 85                          | warn                            | inside warn band                                 |
| case-K4 | 45                          | on-target                       | under 60-min target floor                        |
| case-K5 | 20                          | on-target                       | well under target — containment caught early     |

The headline `p95` figure here is `≈ 295 min` — that value is what
the catalog aggregation `measurement.aggregation: p95` resolves to
for this snapshot.

## Threshold band reference

This scoped variant does not redeclare numeric thresholds; it inherits
the band shape from the unscoped baseline `kpi.mttr_critical@v1` and
operators typically tune containment-specific values in their own
scoped overrides. See `mttr.yaml` and `mttr.viz.md` for the inherited
numeric bands.

## OCSF source-data shape

The chart's underlying observations are derived from the operator's
response pipeline. Each closed in-scope incident contributes one
`remediation_latency_minutes` sample computed from the two inputs
declared in `mttr_containment.yaml`'s `measurement.inputs`:

- `first_detection_fire` — the first authoritative detection firing
  that opened the incident record at the scoped class. Catalog entry
  is detection-vendor-neutral.
- `first_response_action` — the first playbook step transition whose
  purpose matches the scoped response class (containment). Bound by
  `playbook_step: containment` on the catalog entry; the
  `playbook_refs[]` array anchors the canonical step against
  `playbook.data_exfil@v1` (`action--20000000-0000-4000-8000-000000000005`)
  and `playbook.ransomware_containment@v1` (steps
  `action--30000000-0000-4000-8000-000000000005`,
  `…000006`, `…000007`).

The unscoped baseline (`kpi.mttr_critical@v1`) is the place a CORE
follow-up will land an OCSF Detection Finding binding for the
detection input; this scoped variant inherits whatever binding lands
there. The reference rendering above remains shape-valid: it reads
two timestamps per incident and computes a duration, regardless of
which OCSF classes carry them.

## Operator override

Operators are expected to render this metric in their own dashboard
idiom — the catalog reference rendering above is the contract for
the chart shape (per-incident horizontal bars, p95 headline,
inherited-band geometry), not the visual style. The compile target
is the source of truth for the executable form.
