# Reference visualisation — `kri.cra_early_warning_latency_hours@v1`

This is the committed reference-visualisation artifact for the CRA
Article 14(1) 24-hour early-warning dispatch-latency KRI. It exists so
the G-04 catalog definition-of-done (a *committed* reference
visualisation, not a narrated one) is closed; downstream compile
targets (n8n / Temporal / LangGraph) read the same metric YAML and
render the executable form in their own dashboard surface. The
artifact here is the contract for the chart shape, not the executable
chart.

## Chart kind

Two-panel composition. The headline panel is a single gauge-style
horizontal bar reading the max dispatch latency (`hours`) across CRA
Article 14(1) early-warning notifications dispatched in the evaluation
window, plotted against the catalog `warn` / `high` / `breach`
thresholds (12h / 20h / 24h) and the statutory 24-hour bound.
Direction is `lower_is_better`: a max reading beyond 24 hours is a
statutory overrun. The drill-down panel is a horizontal bar chart,
one bar per early-warning notification dispatched in the window,
plotting `dispatch_latency_hours` — hours between the awareness
timestamp and the SRP submission.

- **Headline (max):** the worst-case latency across dispatches in the
  window. This is the figure the operator's risk surface reads
  first — the case that came closest to (or beyond) the statutory
  wall.
- **Drill-down x-axis:** `dispatch_latency_hours` — hours between
  operator awareness and SRP dispatch. Positive values grow towards
  the 24-hour bound.
- **Drill-down y-axis:** one row per early-warning dispatched in the
  window, labelled by the case `incident.uid`; sorted descending so
  the longest latencies (and any overruns) sit at the top — the
  cases that lift the max.
- **Threshold overlay (drill-down):** three vertical lines at 12h
  (warn), 20h (high), and 24h (breach / statutory bound). Bars right
  of the 24h line are statutory overruns and require a "reasons for
  the delay" record on the SRP submission.

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
title: "kri.cra_early_warning_latency_hours@v1 — dispatch latency per CRA Art. 14(1) early warning (P30D window)"
---
xychart-beta horizontal
    title "hours between awareness and SRP early-warning dispatch"
    x-axis "notification (dispatched in window)" ["case-E1", "case-E2", "case-E3", "case-E4", "case-E5"]
    y-axis "dispatch_latency_hours" 0 --> 30
    bar [3, 8, 14, 22, 26]
```

Reading the bars in this illustrative rendering:

| case    | dispatch_latency_hours | band     | reading                                                       |
|---------|------------------------|----------|---------------------------------------------------------------|
| case-E1 | 3                      | ok       | dispatched inside 12h — comfortable slack                     |
| case-E2 | 8                      | ok       | dispatched inside 12h — comfortable slack                     |
| case-E3 | 14                     | warn     | above 12h — leading signal, still inside statutory bound      |
| case-E4 | 22                     | high     | above 20h — approaching the 24-hour statutory wall            |
| case-E5 | 26                     | breach   | above 24h — statutory overrun, reasons-for-delay required     |

With one overrun in the window the max resolves to `26` hours — inside
the `breach` band (`> 24`). That value is what the catalog aggregation
`measurement.aggregation: max` resolves to for this snapshot.

## Threshold band reference

| name   | comparator | value | severity |
|--------|------------|-------|----------|
| warn   | >          | 12    | warn     |
| high   | >          | 20    | high     |
| breach | >          | 24    | critical |

The bands match the `thresholds` array on
`cra_early_warning_latency_hours.yaml`; the catalog entry is the
source of truth, this file is the visualisation surface. The catalog
`target` (`<= 24`) is the statutory ceiling every dispatch is
expected to clear.

## OCSF source-data shape

The chart's underlying observations are derived from the operator's
CRA SRP notification chain. Each early-warning dispatched in the
evaluation window contributes one `dispatch_latency_hours` sample
computed from the two inputs declared in
`cra_early_warning_latency_hours.yaml`'s `measurement.inputs`:

- `awareness_timestamp` — operator-awareness timestamp handed to the
  CRA SRP notification chain by the upstream classifier as the
  `__awareness_ts__` playbook variable, used as the start of the
  24-hour clock. Bound to `telemetry.ocsf.compliance_finding@v1`
  field `start_time` on the early-warning submission event.
- `notification_dispatch` — the regulator-notification chain step
  transition that dispatches the early warning through the SRP.
  Bound to `telemetry.ocsf.compliance_finding@v1` field `time` on
  the early-warning submission event.

The latency samples that drive the max headline are
`notification_dispatch.time - awareness_timestamp.start_time`
converted to hours.

## Operator override

Operators are expected to render this metric in their own dashboard
idiom — the catalog reference rendering above is the contract for
the chart shape (max headline, per-dispatch horizontal bars, three
statutory-clock threshold overlays), not the visual style. The
compile target is the source of truth for the executable form.
