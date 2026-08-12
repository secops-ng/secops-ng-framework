# Reference visualisation — `kpi.dora_resilience_test_coverage@v1`

This is the committed reference-visualisation artifact for the
resilience-testing coverage KPI. It exists so the G-04 catalog
definition-of-done (a *committed* reference visualisation, not a
narrated one) is closed; downstream compile targets (n8n / Temporal /
LangGraph) read the same metric YAML and render the executable form
in their own dashboard surface. The artifact here is the contract for
the chart shape, not the executable chart.

## Chart kind

Two-panel composition. The headline panel is a single gauge-style
horizontal bar reading the ratio of critical-or-important functions
in the DORT scope catalogue that hold composed testing evidence
completed inside the cadence window their class requires. The
drill-down panel is a horizontal bar chart, one bar per in-scope
function, plotting evidence age as a share of the allowed cadence
(`age ÷ cadence`, so `1.0` is the deadline), coloured by cadence
class: `art-24-annual` versus `art-26-tlpt-3y`. Functions with no
in-cadence evidence plot as full bars past the deadline line — they
are the uncovered slice the headline ratio subtracts.

- **Headline (ratio):** covered functions ÷ in-scope functions.
  `higher_is_better`; `1.0` is the target, `warn` shading below
  `1.0`, `high` below `0.8`, per the YAML thresholds.
- **Drill-down x-axis:** evidence age as a multiple of the class
  cadence, the `1.0` deadline line marked.
- **Drill-down rows:** one per function reference from the scope
  catalogue, labelled by reference and cadence class, with the
  test-record reference of its newest evidence (or `no evidence`).
  Per the playbook's sovereign-stack constraint the row carries
  references and dates only — never finding bodies.
- **Pairing note:** the canonical dashboard placement is side by
  side with `kri.tlpt_remediation_overdue@v1` — coverage rising
  while remediation debt ages is the false-comfort pattern the pair
  exists to catch.

## Worked reference rendering

```
kpi.dora_resilience_test_coverage — window 2026-05-06 → 2026-08-04 (P90D)

headline  ███████████████████▌ 0.83            target ≥ 1.0 · warn < 1.0 · breach < 0.8

function_ref                 cadence          age/cadence  evidence
payments-clearing core       art-24-annual           0.44  test-2026-031
customer-auth gateway        art-24-annual           0.71  test-2026-018
trade-settlement engine      art-26-tlpt-3y          0.29  tlpt-2025-002
ledger reconciliation        art-24-annual           0.58  test-2026-027
client-portal frontend       art-24-annual           0.90  test-2025-061
market-data ingestion        art-24-annual           1.18  test-2025-044  ◀ stale
```

Six in-scope functions: five covered inside their cadence, one whose
newest evidence has aged past the annual window and therefore does
not count. The headline reads `5/6 ≈ 0.83` — warn band, and the
stale row at the top of the sorted drill-down names exactly which
test to schedule next.
