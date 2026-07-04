# Reference visualisation — `kri.gdpr_breach_supervisory_authority_notification_latency_hours@v1`

This is the committed reference-visualisation artifact for the GDPR
Article 33(1) 72-hour supervisory-authority breach-notification
dispatch-latency KRI. It exists so the G-04 catalog definition-of-
done (a *committed* reference visualisation, not a narrated one) is
closed; downstream compile targets (n8n / Temporal / LangGraph) read
the same metric YAML and render the executable form in their own
dashboard surface. The artifact here is the contract for the chart
shape, not the executable chart.

## Chart kind

Two-panel composition. The headline panel is a single gauge-style
horizontal bar reading the max dispatch latency (`hours`) across
GDPR Art. 33(1) supervisory-authority notifications dispatched in the
evaluation window, plotted against the catalog `warn` / `high` /
`breach` thresholds (48h / 60h / 72h) and the statutory 72-hour bound.
Direction is `lower_is_better`: a max reading beyond 72 hours is a
statutory overrun. The drill-down panel is a horizontal bar chart,
one bar per supervisory-authority notification dispatched in the
window, plotting `dispatch_latency_hours` — hours between the
awareness timestamp and the supervisory-authority submission.

- **Headline (max):** the worst-case latency across dispatches in the
  window. This is the figure the operator's risk surface reads
  first — the case that came closest to (or beyond) the statutory
  wall.
- **Drill-down x-axis:** `dispatch_latency_hours` — hours between
  controller awareness and Art. 33(1) dispatch. Positive values grow
  towards the 72-hour bound.
- **Drill-down y-axis:** one row per supervisory-authority
  notification dispatched in the window, labelled by the case
  `incident.uid`; sorted descending so the longest latencies (and
  any overruns) sit at the top — the cases that lift the max.
- **Threshold overlay (drill-down):** three vertical lines at 48h
  (warn), 60h (high), and 72h (breach / statutory bound). Bars right
  of the 72h line are statutory overruns and require a "reasons for
  the delay" record on the supervisory-authority submission.

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
title: "kri.gdpr_breach_supervisory_authority_notification_latency_hours@v1 — dispatch latency per GDPR Art. 33(1) supervisory-authority notification (P30D window)"
---
xychart-beta horizontal
    title "hours between awareness and GDPR Art. 33(1) supervisory-authority dispatch"
    x-axis "notification (dispatched in window)" ["case-G1", "case-G2", "case-G3", "case-G4", "case-G5"]
    y-axis "dispatch_latency_hours" 0 --> 80
    bar [10, 28, 52, 63, 74]
```

Reading the bars in this illustrative rendering:

| case    | dispatch_latency_hours | band     | reading                                                       |
|---------|------------------------|----------|---------------------------------------------------------------|
| case-G1 | 10                     | ok       | dispatched inside 48h — comfortable slack                     |
| case-G2 | 28                     | ok       | dispatched inside 48h — comfortable slack                     |
| case-G3 | 52                     | warn     | above 48h — leading signal, still inside statutory bound      |
| case-G4 | 63                     | high     | above 60h — approaching the 72-hour statutory wall            |
| case-G5 | 74                     | breach   | above 72h — statutory overrun, reasons-for-delay required     |

With one overrun in the window the max resolves to `74` hours —
inside the `breach` band (`> 72`). That value is what the catalog
aggregation `measurement.aggregation: max` resolves to for this
snapshot.

## Threshold band reference

| name   | comparator | value | severity |
|--------|------------|-------|----------|
| warn   | >          | 48    | warn     |
| high   | >          | 60    | high     |
| breach | >          | 72    | critical |

The bands match the `thresholds` array on
`gdpr_breach_supervisory_authority_notification_latency_hours.yaml`;
the catalog entry is the source of truth, this file is the
visualisation surface. The catalog `target` (`<= 72`) is the
statutory ceiling every dispatch is expected to clear.

## OCSF source-data shape

The chart's underlying observations are derived from the controller's
GDPR supervisory-authority notification chain. Each Art. 33(1)
notification dispatched in the evaluation window contributes one
`dispatch_latency_hours` sample computed from the two inputs declared
in
`gdpr_breach_supervisory_authority_notification_latency_hours.yaml`'s
`measurement.inputs`:

- `awareness_timestamp` — controller-awareness timestamp emitted when
  a candidate incident crosses the Art. 4(12) personal-data-breach
  classification threshold, used as the start of the 72-hour clock.
  Bound to `telemetry.ocsf.compliance_finding@v1` field `start_time`
  on the supervisory-authority notification submission event.
- `notification_dispatch` — the supervisory-authority notification
  chain step transition that dispatches the Art. 33(1) notification
  to the competent supervisory authority. Bound to
  `telemetry.ocsf.compliance_finding@v1` field `time` on the
  supervisory-authority notification submission event.

The latency samples that drive the max headline are
`notification_dispatch.time - awareness_timestamp.start_time`
converted to hours.

## Operator override

Operators are expected to render this metric in their own dashboard
idiom — the catalog reference rendering above is the contract for
the chart shape (max headline, per-dispatch horizontal bars, three
statutory-clock threshold overlays), not the visual style. The
compile target is the source of truth for the executable form.
