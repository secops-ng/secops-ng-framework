# Reference visualisation — `kri.overdue_key_rotations@v1`

This is the committed reference-visualisation artifact for the
key-rotation KRI. It exists so the G-04 catalog definition-of-done
(a *committed* reference visualisation, not a narrated one) is
closed; downstream compile targets (n8n / Temporal / LangGraph) read
the same metric YAML and render the executable form in their own
dashboard surface. The artifact here is the contract for the chart
shape, not the executable chart.

## Chart kind

Two-panel composition. The headline panel is a single gauge-style
horizontal bar reading the count of distinct in-scope keys judged by
the check-key-rotation step within the evaluation window whose
finding carries a drift or gap verdict. The drill-down panel is a
horizontal bar chart, one bar per judged key, plotting key age
relative to its governing rotation interval (age ÷ declared interval,
so `1.0` is the rotation deadline), coloured by verdict: `drift`
(overdue against a declared interval clause) versus `gap` (no
rotation-interval clause governs the key's class). The drift/gap
split is the canonical drill-down dimension because the two verdicts
have different owners — drift is closed by rotating the key, gap is
closed by writing the clause — and the rotation primitive refuses to
collapse them.

- **Headline (count):** distinct key references with a drift or gap
  verdict in the window. `lower_is_better`; `0` is the floor
  (target) and any positive reading is rotation debt against NIS2
  Art. 21(2)(h).
- **Drill-down x-axis:** age as a multiple of the declared interval,
  with the `1.0` deadline line marked; gap-verdict keys plot age in
  days on a parallel unscaled lane (there is no interval to divide
  by — that absence is the finding).
- **Drill-down rows:** one per key reference, labelled by the
  reference and the clause_ref the finding names (or `no clause`).
  Per the playbook's sovereign-stack constraint the row carries
  references and observed dates only — never key material.
- **Thresholds:** `warn` band shading from 1, `high` from 5, drawn
  on the headline gauge per the YAML thresholds.

## Worked reference rendering

```
kri.overdue_key_rotations — window 2026-07-05 → 2026-08-04 (P30D)

headline  █ 2                                    warn ≥ 1 · breach ≥ 5

key_ref                        clause             age/interval  verdict
artifact-signing hsm key       rotate-180d               1.63   drift  ████▉
sso-token signing key          rotate-90d                1.12   drift  ███▍
db-at-rest master key          rotate-365d               0.71   ok
webhook hmac secret            (no clause)            412 days  gap    ─▶
```

Two drift findings past their declared intervals, one healthy key
below deadline (plotted for context, not counted), and one key aging
with no governing clause. The headline reads `3` — both drift
findings and the gap finding count; the healthy key does not. The
operator rotates two keys and writes one clause.
