# Worked example: `playbook.ransomware_containment@v1`

Five-layer worked-example projection of the ransomware-containment
starter playbook. The CACAO source of truth lives at
`content/playbooks/ransomware-containment/playbook.cacao.json`; the
LangGraph reference compile output lives at
`examples/langgraph/ransomware-containment/`; n8n and Temporal compiler
goldens live under `tests/compilers/{n8n,temporal}/`. This directory ties
the playbook to the SecOps-NG detection / control / telemetry / metrics
layers so a reviewer can trace the containment loop from an EDR /
identity-protection signal through endpoint isolation, identity
revocation, and backup verification, into the regulator early-warning
notification, without leaving the example.

## Why ransomware-containment

Ransomware-containment is the canonical EU-regulated incident shape: a
detection signal drives endpoint isolation (EDR-primary, network-ACL
fallback), identity revocation, and a backup-integrity check, and the
workflow closes on a comms-plan step that pages the IR lead and drafts
the NIS2 Article 23 early-warning pre-notification within the 24-hour
statutory clock. Metrics report detect-latency, containment-latency,
backup-recoverability coverage, regulator notification-SLA compliance,
and notification-overrun residual risk over a rolling window.

## Files

| Layer        | File                                                       | Stable ID                                          |
|--------------|------------------------------------------------------------|----------------------------------------------------|
| Playbook     | `playbook.json`                                            | `playbook.ransomware_containment@v1`               |
| Detection    | `detection.json`                                           | `detection.sigma.shadow_copies_deletion@v1`        |
| Control      | `control.json`                                             | `control.endpoint_isolation@v1`                    |
| Telemetry    | `telemetry.json`                                           | `telemetry.ocsf.process_activity@v1`               |
| Telemetry sample | `telemetry.sample.json`                                | (OCSF Process Activity payload, `class_uid 1007`)  |
| Metric (KPI) | `metrics/kpi.mttd_ransomware.json`                         | `kpi.mttd_ransomware@v1`                           |
| Metric (KPI) | `metrics/kpi.mttr_containment.json`                        | `kpi.mttr_containment@v1`                          |
| Metric (KPI) | `metrics/kpi.backup_integrity_pass_rate.json`              | `kpi.backup_integrity_pass_rate@v1`                |
| Metric (KPI) | `metrics/kpi.notification_sla_compliance.json`             | `kpi.notification_sla_compliance@v1`               |
| Metric (KRI) | `metrics/kri.regulator_notification_overrun.json`          | `kri.regulator_notification_overrun@v1`            |

The detection layer is a pointer to the upstream SigmaHQ rule
`c947b146-0abc-4c87-9c64-b17e9d7274a2`
(`rules/windows/process_creation/proc_creation_win_susp_shadow_copies_deletion.yml`).
SecOps-NG does not re-author Sigma; the rule body lives upstream and the
pointer is republished here. Additional Sigma rule IDs referenced by
the playbook (`21ff4ca9`, `89f75308`, `e3f673b3`, `192a0330`) appear in
the playbook's `external_references` block.

## Cross-reference graph

```
                       playbook.ransomware_containment@v1
                       (CACAO v2 + x_secops_ng)
                                 │
       ┌─────────────────────────┼──────────────────────────┐
       │                         │                          │
  detection.sigma.          control.endpoint_         telemetry.ocsf.
  shadow_copies_            isolation@v1              process_activity@v1
  deletion@v1                                         (OCSF class_uid 1007)
                                 │
                                 ▼
              kpi.mttd_ransomware@v1
              kpi.mttr_containment@v1
              kpi.backup_integrity_pass_rate@v1
              kpi.notification_sla_compliance@v1
              kri.regulator_notification_overrun@v1
```

Every metric pins which CACAO step it measures via
`playbook_refs[].step_id` so a dashboard compiler can render the metric
beside the step it observes without inferring topology. The playbook
references additional control and telemetry artifacts that are *not*
materialised in this directory (network-egress filtering, identity
revocation, session-token revocation, backup-integrity verification,
incident notification; OCSF File System Activity, Network Activity,
Authentication, Incident Finding) — those bind into sibling worked
examples (`identity-compromise/`, `data-exfil/`) and stay there to
avoid duplicating mid-layer artifacts.

## OSCAL / D3FEND / OCSF references

* **OSCAL control catalog** — `control.json` carries NIST SP 800-53
  Rev. 5 control identifiers (`ir-4`, `ir-4(1)`, `sc-7`, `ac-4`) inside
  an OSCAL component-definition fragment. The `source` URI pins the
  catalog (https://doi.org/10.6028/NIST.SP.800-53r5).
* **MITRE D3FEND** — `control.json` references the `D3-NTF` defensive
  technique (Network Traffic Filtering,
  https://d3fend.mitre.org/technique/d3f:NetworkTrafficFiltering/),
  which covers both the EDR-isolate primary path (host-level kernel
  network gate) and the network-ACL deny fallback path at the access
  boundary.
* **MITRE ATT&CK counters** — `T1486` (Data Encrypted for Impact),
  `T1490` (Inhibit System Recovery, the shadow-copy / backup-deletion
  precursor), `T1021` (Remote Services, the lateral-spread path that
  isolation cuts).
* **OCSF** — `telemetry.json` binds the workflow to OCSF v1.4.0 class
  `Process Activity` (`class_uid 1007`, category `System Activity`,
  `category_uid 1`). The bundled `telemetry.sample.json` is a conformant
  payload showing the shadow-copy-deletion precursor (`wmic` /
  `powershell` command-line patterns) used by the playbook's triage
  step.

## Regulatory cross-references

| Regulation | Article | Relevance                                                                                               |
|------------|---------|---------------------------------------------------------------------------------------------------------|
| NIS2 Directive (EU) 2022/2555 | Article 21 (cybersecurity risk-management measures) | The containment, identity-management, backup, and incident-handling capabilities the playbook exercises are explicit Article 21(2) baselines (incident handling, business continuity & backup management, basic cyber-hygiene, identity & access). |
| NIS2 Directive (EU) 2022/2555 | Article 23 (incident reporting)                        | A confirmed ransomware event meeting the "significant incident" threshold triggers the 24h early-warning and 72h initial-notification windows. The playbook's comms-plan step drafts the Article 23 pre-notification within the 24h clock. |
| DORA Regulation (EU) 2022/2554 | Article 17 (ICT-related incident management)          | Ransomware containment falls inside the ICT-related incident-management process financial entities maintain. The MTTR / backup-integrity KPIs are the operational counterparts to the Article 17 process controls. |
| DORA Regulation (EU) 2022/2554 | Article 19 (reporting of major ICT-related incidents)  | A "major" ransomware event (classified per the supporting RTS) triggers the 4h initial-report window after classification. The `kri.regulator_notification_overrun@v1` artifact is the residual-risk gauge on this window. |

Canonical sources:

* NIS2 (Directive (EU) 2022/2555): https://eur-lex.europa.eu/eli/dir/2022/2555/oj
* DORA (Regulation (EU) 2022/2554): https://eur-lex.europa.eu/eli/reg/2022/2554/oj

## Sovereignty note

The control artifact intentionally references the EDR and network
chokepoint as abstract `service` components. The accompanying mapping
packs (see `content/mappings/`) bind sovereignty-relevant choices
(EU-hosted EDR control planes, sovereign-cloud egress filtering, EU
data-residency for the backup catalogue) to the operator's deployment,
so this worked example stays portable across sovereign and
non-sovereign endpoint stacks. The comms-plan step's 24h NIS2 / 4h DORA
notification windows are jurisdiction-anchored: operators serving
multiple regulators bind the tighter of the applicable windows via the
mapping pack rather than re-authoring the playbook.

## How to validate locally

```
cd secops-ng-framework
pytest tests/ -q
```

The content-model test suite parametrises against the worked-example
artifacts in this directory and asserts each artifact validates against
its layer schema, the metric inputs resolve to siblings (where the
example materialises the referenced layer), and the namespace / kind /
sample-class-uid consistency invariants hold.

## What this example is NOT

- Not a runnable playbook — the CACAO source of truth lives at
  `content/playbooks/ransomware-containment/playbook.cacao.json`, and
  the compiler outputs (`examples/langgraph/ransomware-containment/`
  plus the n8n / Temporal compiler goldens under
  `tests/compilers/{n8n,temporal}/`) are the executable artifacts.
- Not authoritative for upstream rule IDs (Sigma), control catalog
  control-ids (NIST 800-53 / ISO 27001), event class UIDs (OCSF), or
  D3FEND technique IDs. Upstream sources are pinned by URL; the
  example follows upstream renames by republishing the pointer.

## Sibling worked examples

- `../vuln-intake/` — vulnerability intake (host process-creation telemetry).
- `../data-exfil/` — data exfiltration with regulator notification gate (NIS2 Art. 23 / DORA Art. 19).
- `../identity-compromise/` — identity compromise + IAM containment (OCSF Authentication, D3-MFA).
- `../cloud-misconfiguration/` — cloud-misconfiguration drift detection.
- `../on-call-rotation/` — on-call rotation with handoff briefs.
- `../phishing-triage/` — phishing triage.
- `../post-incident-review/` — post-incident review and learning loop.
