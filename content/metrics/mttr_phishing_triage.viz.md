# Reference visualisation — `kpi.mttr_phishing_triage@v1`

This is the committed reference-visualisation artifact for the
phishing-triage-scoped mean-time-to-respond KPI. It exists so the
G-04 catalog definition-of-done (a *committed* reference
visualisation, not a narrated one) is closed; downstream compile
targets (n8n / Temporal / LangGraph) read the same metric YAML and
render the executable form in their own dashboard surface. The
artifact here is the contract for the chart shape, not the executable
chart.

## Chart kind

Horizontal bar chart, one bar per phishing-rooted incident closed
within the evaluation window whose response playbook reached the
canonical triage step, sorted by `remediation_latency_minutes`
descending so the slowest triage decision sits at the top. The `p95`
aggregate is the headline figure operators read first; the
per-incident bars are the supporting drill-down that names *which*
phishing incidents pulled the tail.

- **x-axis:** `remediation_latency_minutes` — minutes between
  `first_detection_fire_timestamp` and
  `first_response_action_timestamp` (triage step) for each closed
  phishing incident in the window.
- **y-axis:** one row per closed phishing incident, labelled by the
  case `incident.uid`; sorted by latency descending so the worst-case
  incidents sit at the top.
- **Threshold overlays:** the unscoped baseline catalog entry
  (`kpi.mttr_critical@v1`) carries the warn (60 min) and breach (240
  min) thresholds; this scoped variant inherits the threshold-band
  shape but does not redeclare numeric values — the reference
  rendering shows the inherited band positions so operators reading
  the chart see the same band geometry as the unscoped baseline.
  Phishing-triage targets are typically tightened in operator scoped
  overrides given the volume profile of the inbox.
- **Headline annotation:** the `p95` aggregate across closed phishing
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
title: "kpi.mttr_phishing_triage@v1 — remediation latency to triage per closed phishing incident (P30D window)"
---
xychart-beta horizontal
    title "minutes from first detection fire to first triage action (phishing-rooted)"
    x-axis "incident (closed in window)" ["case-T1", "case-T2", "case-T3", "case-T4", "case-T5"]
    y-axis "remediation_latency_minutes" 0 --> 300
    bar [255, 130, 65, 30, 10]
```

Reading the bars in this illustrative rendering, referencing the
unscoped baseline thresholds for context:

| case    | remediation_latency_minutes | band (vs. kpi.mttr_critical@v1) | reading                                          |
|---------|-----------------------------|---------------------------------|--------------------------------------------------|
| case-T1 | 255                         | breach                          | above 240-min breach floor                       |
| case-T2 | 130                         | warn                            | above 60-min warn floor, below breach            |
| case-T3 | 65                          | warn                            | just above warn floor                            |
| case-T4 | 30                          | on-target                       | under 60-min target floor                        |
| case-T5 | 10                          | on-target                       | well under target — triage decision caught early |

The headline `p95` figure here is `≈ 255 min` — that value is what
the catalog aggregation `measurement.aggregation: p95` resolves to
for this snapshot.

## Threshold band reference

This scoped variant does not redeclare numeric thresholds; it inherits
the band shape from the unscoped baseline `kpi.mttr_critical@v1` and
operators typically tighten phishing-triage-specific values in their
own scoped overrides. See `mttr.yaml` and `mttr.viz.md` for the
inherited numeric bands.

## OCSF source-data shape

The chart's underlying observations are derived from the operator's
response pipeline for phishing-rooted incidents. Each closed phishing
incident contributes one `remediation_latency_minutes` sample
computed from the two inputs declared in
`mttr_phishing_triage.yaml`'s `measurement.inputs`:

- `first_detection_fire` — the first authoritative detection firing
  that opened the phishing incident record. Catalog entry is
  detection-vendor-neutral.
- `first_response_action` — the first playbook step transition whose
  purpose matches the scoped response class (triage). Bound by
  `playbook_step: triage` on the catalog entry; the `playbook_refs[]`
  array anchors the canonical step against `playbook.phishing_triage@v1`
  (steps `action--c0a17a01-0000-4000-8000-000000000008` through
  `…00000000000c`).

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
