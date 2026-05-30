# vuln-intake

Coordinated vulnerability disclosure (CVD) intake playbook for
CRA-aligned operators. Receives an inbound disclosure (researcher
report, vendor advisory, CVE feed hit, or internal scan finding),
performs initial triage against the operator's asset inventory and
severity policy, routes the case to the appropriate response track,
and closes.

## Maturity

`SKELETON` — minimal CACAO v2 topology only. CORE will add CVSS / EPSS
scoring, SBOM PURL correlation, per-severity switch routing, KPI
metric_refs, and the full OSCAL / D3FEND / OCSF cross-reference set.
EXTEND will add the n8n / Temporal / LangGraph compiler emission
goldens.

## Files

- `playbook.cacao.json` — the CACAO v2 artifact (SKELETON tier).
  Control cross-references are carried inline on `x_secops_ng.control_refs`
  (`control.vuln_disclosure_intake@v1`, `control.sbom_capture@v1`); a
  full `mappings.yaml` covering OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA
  lands with the CORE tier.

## Upstream obligations the full playbook helps operationalise

- CRA (EU) 2024/2847, Annex I §2 — coordinated vulnerability disclosure
  policy.
- CRA (EU) 2024/2847, Article 14 — reporting obligations for actively
  exploited vulnerabilities.
- NIS2 (EU) 2022/2555, Article 21(2)(e) — vulnerability handling and
  disclosure.
- ISO/IEC 29147:2018 and ISO/IEC 30111:2019 — vulnerability disclosure
  and handling process baselines.
