# Worked example: `playbook.data_exfil@v1`

This directory is a second end-to-end worked example for the SecOps-NG
content model, following the same shape as `examples/vuln-intake/`. It
ties together all five layers around the data-exfiltration starter
playbook so a reviewer can trace the workflow from an inbound DLP /
egress signal to the regulator-notification gate without leaving the
example.

## Why data-exfil

Data exfiltration is the smallest realistic workflow that exercises the
regulator-notification half of the content model. A DLP / egress signal
(telemetry) is triaged and scope-assessed (detection + control
attestation), a confirmed exfiltration branches into containment, and a
second branch gates regulator / customer notification on the
affected-subjects threshold (NIS2 Article 23, DORA Article 19). The
metrics layer then reports detect-to-contain latency, notification SLA
compliance, and the regulator-overrun risk indicator over a rolling
window.

## Files

| Layer       | File                                                  | Stable ID                                          |
|-------------|-------------------------------------------------------|----------------------------------------------------|
| Playbook    | `../../../content/playbooks/data-exfil/playbook.cacao.json` | `playbook.data_exfil@v1`                     |
| Detection   | `detection.json`                                      | `detection.sigma.dlp_egress_alert@v1`              |
| Detection   | `detection.data_staging.json`                         | `detection.sigma.data_staging_archive_created@v1`  |
| Control     | `control.json`                                        | `control.dlp_enforcement@v1`                       |
| Control     | `control.data_classification.json`                    | `control.data_classification_baseline@v1`          |
| Control     | `control.network_egress_filtering.json`               | `control.network_egress_filtering@v1`              |
| Telemetry   | `telemetry.json`                                      | `telemetry.ocsf.dlp_alert@v1`                      |
| Telemetry   | `telemetry.incident_finding.json`                     | `telemetry.ocsf.incident_finding@v1`               |
| Metric (KPI)| `metrics/kpi.mttd_exfil.json`                         | `kpi.mttd_exfil@v1`                                |
| Metric (KPI)| `metrics/kpi.mttr_containment.json`                   | `kpi.mttr_containment@v1`                          |
| Metric (KPI)| `metrics/kpi.notification_sla_compliance.json`        | `kpi.notification_sla_compliance@v1`               |
| Metric (KRI)| `metrics/kri.regulator_notification_overrun.json`     | `kri.regulator_notification_overrun@v1`            |

The detection layer references upstream Sigma rules by `rule_id` + repo
+ commit pin. SecOps-NG does not re-author Sigma; the rule bodies live
upstream and the pointer is republished here.

## Cross-reference graph

```
                       playbook.data_exfil@v1
                       (CACAO v2 + x_secops_ng)
                                 │
       ┌─────────────────────────┼──────────────────────────┐
       │                         │                          │
  detection.sigma.          control.dlp_              telemetry.ocsf.
  dlp_egress_alert@v1       enforcement@v1            dlp_alert@v1
  detection.sigma.          control.data_             telemetry.ocsf.
  data_staging_             classification_           incident_finding@v1
  archive_created@v1        baseline@v1
                            control.network_
                            egress_filtering@v1
                                 │
                                 ▼
                    kpi.mttd_exfil@v1
                    kpi.mttr_containment@v1
                    kpi.notification_sla_compliance@v1
                    kri.regulator_notification_overrun@v1
                    (measurement.inputs[].{telemetry,detection,playbook}_ref)
```

Every metric pins which CACAO step it measures (`playbook_refs[].step_id`)
so a dashboard compiler can render the metric beside the step it observes
without inferring topology.

## How to validate locally

```
cd secops-ng-framework
pytest tests/ -q
```

The existing content-model test suite parametrises against every JSON
file under `content-model/examples/` and asserts each artifact validates
against its layer schema. The data-exfil playbook also parses cleanly
via `compilers._shared.cacao_parser.parse_file()` — exercised by the
parser fixture suite when CORE wires the compilers against this skeleton.

## What this example is NOT

- Not a runnable playbook. Compile targets (n8n / Temporal / LangGraph)
  are the SKELETON's downstream consumers; runnable artifacts are
  authored by the CORE card (`t_41811424`).
- Not authoritative for upstream rule IDs (Sigma), control catalog
  control-ids (OSCAL / NIST 800-53 / ISO 27001), event class UIDs (OCSF),
  or D3FEND technique IDs. Upstream sources are pinned by URL plus a
  commit / version where one exists; the example follows upstream
  renames by republishing the pointer, never by vendoring rule or
  catalog bodies.
- Not the place where regulator-notification thresholds are encoded.
  The `__regulator_required__` variable is evaluated against the
  operator's regulator-routing policy — itself bound at compile time by
  the mapping pack the operator selects (NIS2 Art. 23 / DORA Art. 19 /
  GDPR Art. 33). The EXTEND card (`t_9635932c`) cross-references those
  mapping packs against this playbook.

## Out of scope here

- Compiler outputs (`examples/{n8n,temporal,langgraph}/data-exfil/`) and
  their golden tests. Owned by the CORE card.
- Mapping-pack cross-reference updates (NIS2 Art. 23, DORA Art. 19).
  Owned by the EXTEND card.
- False-positive close-out logging on the `exfil_confirmed=false`
  branch — explicitly out of scope per the playbook description.
