# Reference visualisation — `kri.tlpt_remediation_overdue@v1`

This is the committed reference-visualisation artifact for the
remediation-aging KRI. It exists so the G-04 catalog
definition-of-done (a *committed* reference visualisation, not a
narrated one) is closed; downstream compile targets (n8n / Temporal /
LangGraph) read the same metric YAML and render the executable form
in their own dashboard surface. The artifact here is the contract for
the chart shape, not the executable chart.

## Chart kind

Two-panel composition. The headline panel is a single gauge-style
horizontal bar reading the count of findings in the composed
resilience-testing findings register whose committed remediation date
has passed with no dated remediation attestation bound. The
drill-down panel is a horizontal bar chart, one bar per overdue
finding, plotting days overdue as of the window end, with attested
and not-yet-due findings plotted in a muted lane for context (they do
not count). Sorting is by days overdue descending, so the
longest-aging finding sits at the top.

- **Headline (count):** distinct overdue finding references in the
  window. `lower_is_better`; `0` is the floor (target), `warn`
  shading from 1, `high` from 5, per the YAML thresholds.
- **Drill-down x-axis:** days past the committed remediation date.
- **Drill-down rows:** one per finding reference from the register,
  labelled by reference, committed date, and the attestation
  reference (or `none`). Per the playbook's sovereign-stack
  constraint the row carries references and dates only — finding
  bodies stay in the operator's own store.
- **Pairing note:** the canonical dashboard placement is side by
  side with `kpi.dora_resilience_test_coverage@v1` — this KRI is
  the aging side of that pair.

## Worked reference rendering

```
kri.tlpt_remediation_overdue — window 2026-05-06 → 2026-08-04 (P90D)

headline  ██ 2                                  warn ≥ 1 · breach ≥ 5

finding_ref        committed     attestation   days-over
tlpt-2025-002/F3   2026-06-15    none                 50  ████████▌
test-2026-018/F1   2026-07-20    none                 15  ██▌
tlpt-2025-002/F1   2026-07-01    att-2026-090          —  (attested)
test-2026-031/F2   2026-09-01    none                  —  (not yet due)
```

Two findings past their committed dates with no attestation — the
headline reads `2`. The attested and not-yet-due rows are plotted
for context and count nothing; the 50-day row at the top is the one
the next remediation review starts with.
