# Reference visualisation — `kpi.attested_adoption_count@v1`

This is the committed reference-visualisation artifact for the
attested-adoption KPI. It exists so the G-04 catalog
definition-of-done (a *committed* reference visualisation, not a
narrated one) is closed; downstream compile targets (n8n / Temporal /
LangGraph) read the same metric YAML and render the executable form
in their own dashboard surface. The artifact here is the contract for
the chart shape, not the executable chart.

## Chart kind

Two-panel composition. The headline panel is a single gauge-style
horizontal bar reading the count of USED-BY.md registry rows whose
Evidence link passed the most recent completed scheduled reachability
run. The drill-down panel is a horizontal bar chart, one bar per
registry row, plotting a binary evidence-verified encoding (`1`
passed, `0` failed or not yet covered), sliced by deployment type
(`production` / `staging` / `evaluation` / `research`) — the
canonical drill-down dimension, because a production row carries a
different adoption signal than a course evaluation and the registry
deliberately treats both as first-class.

- **Headline (count):** rows with verified evidence.
  `higher_is_better`; the target line sits at `5` (the F-ADOPT-01
  Q4 2026 outreach goal), `warn` shading below `5`, `high` below `1`
  (an empty verified registry), per the YAML thresholds.
- **Drill-down rows:** one per registry row, labelled by
  organisation and deployment type. Rows at `0` do not count toward
  the headline and appear in the paired KRI's drill-down with the
  failure detail.
- **Pairing note:** the canonical dashboard placement is side by
  side with `kri.adoption_evidence_rot_count@v1` — a registry that
  grows while its evidence rots is the pattern the pair catches.

## Worked reference rendering

```
kpi.attested_adoption_count — run 2026-08-12T06:17Z

headline  ███ 3                        target ≥ 5 · warn < 5 · breach < 1

organisation                 type         verified
Example community SOC        evaluation          1  ██
North-region CSIRT lab       research            1  ██
Utility-sector pilot group   staging             1  ██
Legacy field-notes mirror    evaluation          0  ─  ◀ see paired KRI
```

Four registry rows, three with evidence a reader can open — the
headline reads `3`, warn band: the outreach goal of five verified
references is not yet met, and the one failing row is named in the
paired KRI's drill-down rather than silently subtracted.
