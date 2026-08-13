# Reference visualisation — `kri.expiring_tls_certs@v1`

This is the committed reference-visualisation artifact for the
certificate-validity KRI. It exists so the G-04 catalog
definition-of-done (a *committed* reference visualisation, not a
narrated one) is closed; downstream compile targets (n8n / Temporal /
LangGraph) read the same metric YAML and render the executable form
in their own dashboard surface. The artifact here is the contract for
the chart shape, not the executable chart.

## Chart kind

Two-panel composition. The headline panel is a single gauge-style
horizontal bar reading the count of distinct certificates judged by
the probe-cert-posture step within the evaluation window whose
finding carries a drift or gap verdict on an expiry-related clause.
The drill-down panel is a horizontal bar chart, one bar per judged
certificate, plotting days of validity remaining as of the window
end (negative for already-expired), coloured by verdict: `drift`
(contradicts a declared clause) versus `gap` (no governing clause
declared). The drift/gap split is the canonical drill-down dimension
because the two verdicts have different owners — drift is closed in
the estate, gap is closed in the policy document — and the probe
primitive refuses to collapse them.

- **Headline (count):** distinct certificate_refs with a drift or
  gap verdict in the window. `lower_is_better`; `0` is the floor
  (target) and any positive reading is an open NIS2 Art. 21(2)(h)
  exposure.
- **Drill-down x-axis:** days of remaining validity, zero line
  marked; bars sorted ascending so expired and soonest-expiring
  certificates sit at the top.
- **Drill-down rows:** one per certificate_ref, labelled by the
  reference and the clause_ref the finding names (or `no clause` for
  gap verdicts). Per the playbook's sovereign-stack constraint the
  row carries references and observed parameters only — never a
  certificate body or key material.
- **Thresholds:** `warn` band shading from 1, `high` from 5, drawn
  on the headline gauge per the YAML thresholds.

## Worked reference rendering

```
kri.expiring_tls_certs — window 2026-07-05 → 2026-08-04 (P30D)

headline  ██ 3                                   warn ≥ 1 · breach ≥ 5

cert_ref                       clause             days-left  verdict
edge-proxy-fe cert             max-validity-397d       -12   drift  ████▌
payments-api mTLS client       renewal-lead-30d          9   drift  ██▊
build-signing leaf             (no clause)              41   gap    █▍
```

Three findings: one certificate already expired against the declared
maximum-validity clause, one inside the renewal-lead window, one
governed by no clause at all. The headline reads `3`; the operator
closes the first two in the estate and the third in the policy.
