# Reference visualisation — `kri.hardcoded_non_eu_endpoint_reference_count@v1`

This is the committed reference-visualisation artifact for the
hardcoded non-EU endpoint reference count across content and compilers KRI. It exists so the G-04 catalog
definition-of-done (a *committed* reference visualisation, not a
narrated one) is closed; downstream compile targets (n8n / Temporal /
LangGraph) read the same metric YAML and render the executable form
in their own dashboard surface. The artifact here is the contract for
the chart shape, not the executable chart.

## Chart kind

Bar chart of per-observation outcomes contributing to the headline
`count` aggregate for `kri.hardcoded_non_eu_endpoint_reference_count@v1`. Each bar plots one observation
of the shape declared under `measurement.inputs` on the catalog YAML;
the headline aggregate is the `count` roll-up across the bars per the
catalog `measurement.aggregation`. Direction `lower_is_better` fixes the
colour convention — lower bars are better.

## Reference rendering (Mermaid)

The mermaid block below is the canonical reference rendering — small
enough to live in-tree and renderable directly on the public repo
surface. The numeric values are illustrative; the compile target is
the source of truth for the executable form against the artifacts
declared in `measurement.inputs`.

```mermaid
---
config:
    xyChart:
        showTitle: true
        chartOrientation: horizontal
title: "kri.hardcoded_non_eu_endpoint_reference_count@v1 — hardcoded non-EU endpoint reference count across content and compilers (illustrative snapshot)"
---
xychart-beta horizontal
    title "count of distinct non-EU hardcoded literals"
    x-axis "observation" ["sample_a", "sample_b", "sample_c", "sample_d", "sample_e", "sample_f"]
    y-axis "outcome" 0 --> 3
    bar [0, 0, 1, 2, 0, 1]
```

## Threshold band reference

| name | comparator | value | severity |
|------|------------|-------|----------|
| warn | > | 0 | warn |
| breach | >= | 5 | high |

The bands match the `thresholds` array on `hardcoded_non_eu_endpoint_reference_count.yaml`; the catalog
entry is the source of truth, this file is the visualisation surface.

## Source-data shape

The chart's underlying observations are derived from the inputs
declared under `measurement.inputs` on `hardcoded_non_eu_endpoint_reference_count.yaml`. Each observation
contributes one bar to the drill-down; the headline aggregate is
computed per the catalog `measurement.aggregation`. The catalog
window is the tumbling / sliding window declared under
`measurement.window`, so operators can compare readings across
comparable windows without re-litigating the shape.

## Operator override

Operators are expected to render this metric in their own dashboard
idiom — the catalog reference rendering above is the contract for
the chart shape, not the visual style. The compile target is the
source of truth for the executable form against the artifacts the
catalog entry binds to.
