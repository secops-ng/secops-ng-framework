# vuln-intake

Coordinated vulnerability disclosure (CVD) intake playbook for
CRA-aligned operators. Receives an inbound disclosure (researcher
report, vendor advisory, CVE feed hit, or internal scan finding),
acknowledges the reporter against the CRA single-point-of-contact
obligation, correlates the affected component against the operator's
SBOM and asset inventory, scores the case with CVSS and EPSS, assesses
whether the disclosure trips the CRA Article 14 actively-exploited or
severe-incident reporting clock, fires the CRA regulator-notification
chain when it does, and routes the case to a per-severity response
branch (patch + advisory dissemination, scheduled remediation, or
accept-risk).

## Maturity

`CORE` — full topology with per-severity switch routing, CRA Article 14
regulator-notification chain, OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA
cross-references inline, and bidirectional KPI / KRI hooks. EXTEND will
add the worked example under `content-model/examples/vuln-intake/`,
n8n / Temporal / LangGraph compiler emission goldens, and the
per-target binding tests.

## Files

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.vuln_intake@v1`). Control, telemetry, and metric refs are
  carried inline on `x_secops_ng.{control_refs,telemetry_refs,metric_refs}`
  at both the per-step and top-level scopes.

## End-to-end annotation

The table below pins every playbook step to the control, telemetry, and
metric layer artifacts it exercises. Schema for each reference is the
shared `stable_id` shape (`<layer>.<slug>@v<semver>`) used across the
SecOps-NG content model.

| Step | Control refs (OSCAL / CRA anchor) | Telemetry refs (OCSF) | Metric refs |
|---|---|---|---|
| `intake disclosure` | `control.vuln_disclosure_intake@v1` (CRA Annex I §2(5)) | `telemetry.ocsf.vulnerability_finding@v1` (class_uid 2002) | `kpi.vuln_disclosure_sla@v1`, `kri.cvd_intake_aging@v1` |
| `triage and asset correlation` | `control.sbom_capture@v1` (CRA Annex I §2(1)) | `telemetry.ocsf.vulnerability_finding@v1` | `kri.releases_without_sbom@v1` |
| `assess CRA reporting trigger` | `control.incident_timeline_signals@v1` | `telemetry.ocsf.vulnerability_finding@v1` | — |
| `regulator-notification chain (CRA Art. 14)` | `control.cra_submission_templates@v1`, `control.incident_timeline_signals@v1` | `telemetry.ocsf.vulnerability_finding@v1` | `kpi.cra_early_warning_on_time@v1`, `kpi.cra_notification_72h_on_time@v1`, `kpi.cra_final_report_on_time@v1`, `kpi.cra_severe_incident_on_time@v1` |
| `response: critical — patch and advisory` | `control.patch_evidence@v1`, `control.vuln_disclosure_intake@v1` | `telemetry.ocsf.vulnerability_finding@v1` | `kpi.patch_disseminated_on_time@v1`, `kpi.mttr_critical@v1` |
| `response: high — patch and advisory` | `control.patch_evidence@v1`, `control.vuln_disclosure_intake@v1` | `telemetry.ocsf.vulnerability_finding@v1` | `kpi.patch_disseminated_on_time@v1` |
| `response: scheduled remediation` | `control.patch_evidence@v1` | `telemetry.ocsf.vulnerability_finding@v1` | `kpi.patch_disseminated_on_time@v1` |
| `response: accept risk` | — | `telemetry.ocsf.vulnerability_finding@v1` | — |

## Upstream regulatory anchors

- **CRA (EU) 2024/2847, Annex I §2(1)** — SBOM obligation. Exercised at
  the triage step and tracked by `kri.releases_without_sbom@v1`.
- **CRA (EU) 2024/2847, Annex I §2(5)** — coordinated vulnerability
  disclosure policy, single point of contact. Exercised at the intake
  step and tracked by `kpi.vuln_disclosure_sla@v1` and
  `kri.cvd_intake_aging@v1`.
- **CRA (EU) 2024/2847, Annex I §2(7)** — security-update dissemination
  without undue delay. Exercised on every response branch and tracked
  by `kpi.patch_disseminated_on_time@v1`.
- **CRA (EU) 2024/2847, Article 14(1)** — 24h early-warning of an
  actively exploited vulnerability. Tracked by
  `kpi.cra_early_warning_on_time@v1`.
- **CRA (EU) 2024/2847, Article 14(2)** — 72h notification and 14-day
  final report. Tracked by `kpi.cra_notification_72h_on_time@v1` and
  `kpi.cra_final_report_on_time@v1`.
- **CRA (EU) 2024/2847, Article 14(3)** — severe-incident notification
  chain. Tracked by `kpi.cra_severe_incident_on_time@v1`.
- **NIS2 (EU) 2022/2555, Article 21(2)(e)** — vulnerability handling
  and disclosure. Cross-referenced from
  `content/mappings/nis2/article-21-and-23.yaml`.
- **DORA (EU) 2022/2554, Article 9** and **Commission Delegated
  Regulation (EU) 2024/1774, Article 10** — ICT risk management
  framework and JC RTS on vulnerability management. Cross-referenced
  from `content/mappings/dora/article-9-and-rts-vuln-mgmt.yaml`.
- **ISO/IEC 29147:2018** — Vulnerability disclosure.
- **ISO/IEC 30111:2019** — Vulnerability handling processes.

## OCSF binding

The playbook emits the **Vulnerability Finding** event class
(`class_uid 2002`, OCSF v1.3.0) at intake, triage, the CRA reporting
trigger assessment, and every response disposition. The case CVE id,
CVSS vector, EPSS score, and asset reference are carried on the event
payload so downstream consumers (metrics rollup, SIEM, ticketing) can
pick the case up off a single telemetry channel.

## Scoring inputs

- **CVSS** — operators bring their CVSS v3.1 / v4.0 scorer per the
  FIRST.org specification; the catalog entry is scorer-neutral.
- **EPSS** — operators bring their EPSS feed per the FIRST.org Exploit
  Prediction Scoring System. The triage step records the EPSS score
  at intake time alongside the CVSS vector.

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. Emitted
artifacts under `examples/{n8n,temporal,langgraph}/vuln-intake/` will
be authored by the sibling EXTEND card; this directory ships the
portable CACAO content only.

## Sources

- OASIS CACAO v2.0 specification
- Cyber Resilience Act (EU) 2024/2847, Annex I §2 and Article 14
- NIS2 Directive (EU) 2022/2555, Article 21(2)(e)
- DORA Regulation (EU) 2022/2554, Article 9; Commission Delegated
  Regulation (EU) 2024/1774, Article 10
- FIRST.org — CVSS v3.1 / v4.0 specification
- FIRST.org — EPSS Exploit Prediction Scoring System
- ISO/IEC 29147:2018 and ISO/IEC 30111:2019
- OCSF v1.3.0 — Vulnerability Finding (class_uid 2002)
