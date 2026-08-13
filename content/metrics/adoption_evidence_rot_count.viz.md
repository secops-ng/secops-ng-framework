# Reference visualisation — `kri.adoption_evidence_rot_count@v1`

This is the committed reference-visualisation artifact for the
evidence-rot KRI. It exists so the G-04 catalog definition-of-done
(a *committed* reference visualisation, not a narrated one) is
closed; downstream compile targets (n8n / Temporal / LangGraph) read
the same metric YAML and render the executable form in their own
dashboard surface. The artifact here is the contract for the chart
shape, not the executable chart.

## Chart kind

Two-panel composition. The headline panel is a single gauge-style
horizontal bar reading the count of USED-BY.md registry rows whose
Evidence link failed the most recent completed scheduled reachability
run. The drill-down panel is a horizontal bar chart, one bar per
failing row, plotting consecutive failing runs (how many daily runs
the link has now failed), coloured by failure class: `http-error`
(non-2xx), `login-wall` (redirect to an authentication surface),
`timeout`. Consecutive-failure age is the canonical drill-down
dimension because it separates a transient host hiccup (one failing
run) from genuine rot (a week of them) — the remediation contact is
worth making for the second, not the first.

- **Headline (count):** distinct failing rows in the latest run.
  `lower_is_better`; `0` is the floor (target), `warn` shading from
  `1`, `high` from `3`, per the YAML thresholds.
- **Drill-down rows:** one per failing row, labelled by organisation
  and the failure class of the latest run.
- **Pairing note:** the canonical dashboard placement is side by
  side with `kpi.attested_adoption_count@v1` — this KRI is the rot
  side of that pair, and every row here is absent from the KPI's
  headline by construction.

## Worked reference rendering

```
kri.adoption_evidence_rot_count — run 2026-08-12T06:17Z

headline  █ 1                                   warn ≥ 1 · breach ≥ 3

organisation                 class        consecutive-failing-runs
Legacy field-notes mirror    http-error                         6  █████▊
```

One registry row failing for six consecutive daily runs — past the
transient-hiccup range, so the next step the registry contract names
is contacting the attesting organisation or opening the one-line
removal PR. The headline reads `1`, warn band.
