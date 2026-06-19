# Worked example: `playbook.identity_compromise@v1`

This directory is the third end-to-end worked example for the SecOps-NG
content model, after `examples/vuln_intake/` and `examples/data_exfil/`.
It ties together all five layers around the identity_compromise starter
playbook so a reviewer can trace the workflow from an inbound
identity-protection signal to the residual-persistence audit step
without leaving the example.

## Why identity_compromise

Identity compromise is the smallest realistic workflow that exercises
the IAM-containment half of the content model. An identity-protection
signal (telemetry → detection) drives a triage decision, a confirmed
compromise routes through MFA reset + session revocation (control), and
the workflow closes on a lateral-movement hunt + IAM audit step. The
metrics layer reports detect-latency, containment-latency, lateral-hunt
coverage, and MFA-control effectiveness over a rolling window.

## Files

| Layer       | File                                                         | Stable ID                                                       |
|-------------|--------------------------------------------------------------|-----------------------------------------------------------------|
| Playbook    | `playbook.json`                                              | `playbook.identity_compromise@v1`                               |
| Detection   | `detection.json`                                             | `detection.sigma.azure_identity_protection_impossible_travel@v1`|
| Control     | `control.json`                                               | `control.iam.mfa_enforcement@v1`                                |
| Telemetry   | `telemetry.json`                                             | `telemetry.ocsf.authentication@v1`                              |
| Telemetry sample | `telemetry.sample.json`                                 | (OCSF Authentication payload, class_uid 3002)                   |
| Metric (KPI)| `metrics/kpi.mttd_identity_compromise.json`                  | `kpi.mttd_identity_compromise@v1`                               |
| Metric (KPI)| `metrics/kpi.mttr_session_revocation.json`                   | `kpi.mttr_session_revocation@v1`                                |
| Metric (KPI)| `metrics/kpi.coverage_lateral_hunt.json`                     | `kpi.coverage_lateral_hunt@v1`                                  |
| Metric (KRI)| `metrics/kri.mfa_control_effectiveness.json`                 | `kri.mfa_control_effectiveness@v1`                              |

The detection layer references the upstream SigmaHQ rule by `rule_id`
+ repo. SecOps-NG does not re-author Sigma; the rule body lives upstream
and the pointer is republished here.

## Cross-reference graph

```
                       playbook.identity_compromise@v1
                       (CACAO v2 + x_secops_ng)
                                 │
       ┌─────────────────────────┼──────────────────────────┐
       │                         │                          │
  detection.sigma.          control.iam.              telemetry.ocsf.
  azure_identity_           mfa_enforcement@v1        authentication@v1
  protection_impossible                               (OCSF class_uid 3002)
  _travel@v1
                                 │
                                 ▼
                    kpi.mttd_identity_compromise@v1
                    kpi.mttr_session_revocation@v1
                    kpi.coverage_lateral_hunt@v1
                    kri.mfa_control_effectiveness@v1
```

Every metric pins which CACAO step it measures via `playbook_refs[].step_id`
so a dashboard compiler can render the metric beside the step it observes
without inferring topology.

## OSCAL / D3FEND / OCSF references

* **OSCAL control catalog** — `control.json` carries NIST SP 800-53 Rev. 5
  control identifiers (`ia-2`, `ia-5`, `ac-2`, `ac-7`) inside an OSCAL
  component-definition fragment. The `source` URI pins the catalog.
* **MITRE D3FEND** — `control.json` references the `D3-MFA` defensive
  technique (Multi-factor Authentication). The session-revocation
  capability is captured operationally by the playbook step and the
  `kpi.mttr_session_revocation@v1` metric; future iterations may layer
  an additional credential-hardening binding once a second control
  artifact is added for credential rotation.
* **MITRE ATT&CK counters** — `T1078.004` (Valid Accounts: Cloud
  Accounts), `T1110.003` (Brute Force: Password Spraying), `T1556.006`
  (Modify Authentication Process: MFA).
* **OCSF** — `telemetry.json` binds the workflow to OCSF v1.3.0 class
  `Authentication` (`class_uid 3002`, category `Identity & Access
  Management`). The bundled `telemetry.sample.json` is a conformant
  payload.

## Regulatory cross-references

| Regulation | Article | Relevance                                                                                               |
|------------|---------|---------------------------------------------------------------------------------------------------------|
| NIS2 Directive (EU) 2022/2555 | Article 21 (risk-management measures) | Identity-management and authentication appear explicitly in Art. 21(2)(d). |
| NIS2 Directive (EU) 2022/2555 | Article 23 (incident reporting)        | An identity_compromise that meets the "significant incident" threshold triggers the 24h early-warning and 72h initial-notification windows. |
| DORA Regulation (EU) 2022/2554 | Article 17 (ICT-related incident management) | Identity-compromise containment falls inside the ICT-related incident_management process financial entities maintain. |
| DORA Regulation (EU) 2022/2554 | Article 19 (reporting of major incidents) | A "major" identity_compromise (classified per RTS) triggers the 4h initial-report window after classification. |

Canonical sources:

* NIS2 (Directive (EU) 2022/2555): https://eur-lex.europa.eu/eli/dir/2022/2555/oj
* DORA (Regulation (EU) 2022/2554): https://eur-lex.europa.eu/eli/reg/2022/2554/oj

## Sovereignty note

The control artifact intentionally references the IdP as an abstract
`service` component. The accompanying mapping packs (see
`content/mappings/`) bind sovereignty-relevant IdP choices (EU-hosted
identity providers, data-residency boundaries) to the operator's
deployment, so this worked example stays portable across sovereign and
non-sovereign IdP stacks. The lateral-hunt and IAM-audit step's
telemetry window length is also configurable per regulatory regime
(e.g. shorter under DORA Art. 19 reporting pressure).

## How to validate locally

```
cd secops-ng-framework
pytest tests/ -q
```

The content-model test suite parametrises against every JSON file under
`content-model/examples/` and asserts each artifact validates against
its layer schema.

## What this example is NOT

- Not a runnable playbook — the CACAO source of truth lives at
  `content/playbooks/identity_compromise/playbook.cacao.json`, and the
  CORE-layer compiler outputs (`examples/{n8n,temporal,langgraph}/identity_compromise/`)
  are the executable artifacts.
- Not authoritative for upstream rule IDs (Sigma), control catalog
  control-ids (NIST 800-53 / ISO 27001), event class UIDs (OCSF), or
  D3FEND technique IDs. Upstream sources are pinned by URL; the example
  follows upstream renames by republishing the pointer.

## Sibling worked examples

- `../vuln_intake/` — vulnerability intake (host process-creation telemetry).
- `../data_exfil/` — data exfiltration with regulator notification gate (NIS2 Art. 23 / DORA Art. 19).
- `../phishing_triage/` — phishing triage.
