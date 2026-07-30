# Cookbook

End-to-end walkthroughs of SecOps-NG content artifacts as a shipped
operator would encounter them: the CACAO playbook, the deterministic
primitives package the CACAO `core_body` refs bind into, the three
reference-compiled worked examples, and the operator runtime hand-off
contract per target.

Cookbook entries are reading material for an operator who already has
the framework checked out and wants to understand how one playbook
lands in one orchestrator end-to-end. They are not a substitute for the
canonical CACAO sources under `content/playbooks/<workflow>/` or the
emitted worked examples under `examples/{n8n,temporal,langgraph}/<workflow>/`
— those are the source of truth; the cookbook is the connective
narrative.

## Entries

| Workflow       | Cookbook walkthrough                            | Canonical CACAO                                       |
|----------------|-------------------------------------------------|-------------------------------------------------------|
| `vuln_intake`         | [`vuln_intake.md`](vuln_intake.md)                 | `content/playbooks/vuln_intake/`                      |
| `alert_triage`        | [`alert_triage.md`](alert_triage.md)               | `content/playbooks/alert_triage.cacao.yaml` + `content/playbooks/alert_triage/` |
| `incident_management` | [`incident_management.md`](incident_management.md) | `content/playbooks/incident_management/`              |
| `codebase_vuln_management` | [`codebase_vuln_management.md`](codebase_vuln_management.md) | `content/playbooks/codebase_vuln_management/`    |
| `iam_auditor`         | [`iam_auditor.md`](iam_auditor.md)                 | `content/playbooks/iam_auditor/`                      |
| `infra_posture_management` | [`infra_posture_management.md`](infra_posture_management.md) | `content/playbooks/infra_posture_management/`    |
| `contractual_obligations_tracker` | [`contractual_obligations_tracker.md`](contractual_obligations_tracker.md) | `content/playbooks/contractual_obligations_tracker/` |
| `detection_engineering` | [`detection_engineering.md`](detection_engineering.md) | `content/playbooks/detection_engineering/`            |
| `backup_recovery`     | [`backup_recovery.md`](backup_recovery.md)         | `content/playbooks/backup_recovery/`                  |
| `business_continuity` | [`business_continuity.md`](business_continuity.md) | `content/playbooks/business_continuity/`              |
| `cyber_hygiene_training` | [`cyber_hygiene_training.md`](cyber_hygiene_training.md) | `content/playbooks/cyber_hygiene_training/`     |
| `security_awareness_training` | [`security_awareness_training.md`](security_awareness_training.md) | `content/playbooks/security_awareness_training/` |
| `dora_major_incident_reporting` | [`dora_major_incident_reporting.md`](dora_major_incident_reporting.md) | `content/playbooks/dora_major_incident_reporting/` |
| `cra_srp_notify`      | [`cra_srp_notify.md`](cra_srp_notify.md)           | `content/playbooks/cra_srp_notify/`                   |
| `cra_cvd`             | [`cra_cvd.md`](cra_cvd.md)                         | `content/playbooks/cra_cvd/`                          |
| `mfa_secured_comms`   | [`mfa_secured_comms.md`](mfa_secured_comms.md)     | `content/playbooks/mfa_secured_comms/`                |
| `data_subject_rights` | [`data_subject_rights.md`](data_subject_rights.md) | `content/playbooks/data_subject_rights/`              |
| `data_protection_impact_assessment` | [`data_protection_impact_assessment.md`](data_protection_impact_assessment.md) | `content/playbooks/data_protection_impact_assessment/` |
| `nis2_self_assessment` | [`nis2_self_assessment.md`](nis2_self_assessment.md) | `content/playbooks/nis2_self_assessment/`             |
| `nis2_art20_governance` | [`nis2_art20_governance.md`](nis2_art20_governance.md) | `content/playbooks/nis2_art20_governance/`         |
| `dora_ict_risk_selfassess` | [`dora_ict_risk_selfassess.md`](dora_ict_risk_selfassess.md) | `content/playbooks/dora_ict_risk_selfassess/`   |
| `eu_ai_act_risk_management` | [`eu_ai_act_risk_management.md`](eu_ai_act_risk_management.md) | `content/playbooks/eu_ai_act_risk_management/` |
| `eu_ai_act_deployer_obligations` | [`eu_ai_act_deployer_obligations.md`](eu_ai_act_deployer_obligations.md) | `content/playbooks/eu_ai_act_deployer_obligations/` |
| `asset_management`    | [`asset_management.md`](asset_management.md)       | `content/playbooks/asset_management/`                 |
| `agentic_threat_response` | [`agentic_threat_response.md`](agentic_threat_response.md) | `content/playbooks/agentic_threat_response/`     |
| `vulnerability_management` | [`vulnerability_management.md`](vulnerability_management.md) | `content/playbooks/vulnerability_management/`   |
| `identity_access_management_metrics` | [`identity_access_management_metrics.md`](identity_access_management_metrics.md) | `content/metrics/identity_mfa_enforcement_rate.yaml` + `content/metrics/access_review_completion_rate.yaml` |
| `threat_intel_operations_metrics` | [`threat_intel_operations_metrics.md`](threat_intel_operations_metrics.md) | `content/metrics/coverage_threat_intel_feed.yaml` + `content/metrics/mttd_threat_intel_indicator.yaml` + `content/metrics/threat_intel_indicator_ingestion_rate.yaml` + `content/metrics/threat_intel_stale_ioc_ratio.yaml` |
| `vulnerability_management_metrics` | [`vulnerability_management_metrics.md`](vulnerability_management_metrics.md) | `content/metrics/vuln_remediation_sla_compliance.yaml` + `content/metrics/vuln_critical_open_age_p99.yaml` + `content/metrics/unpatched_critical_cve_age_days.yaml` |
| `eidas2_identity_verification` | [`eidas2_identity_verification.md`](eidas2_identity_verification.md) | `content/playbooks/eidas2_identity_verification/` |
| `network_security` | [`network_security.md`](network_security.md) | `content/playbooks/network_security/` |

Additional entries land alongside their content sources as workflows
flip from In Progress to Shipped on
[`ROADMAP.md`](../../ROADMAP.md).

## Crosswalks

Cookbook entries that walk a **regulatory / framework crosswalk**
under `content/mappings/<axis>/` rather than a workflow under
`content/playbooks/<workflow>/`:

| Crosswalk | Cookbook walkthrough | Canonical mapping |
|-----------|----------------------|-------------------|
| NIST CSF 2.0 | [`nist_csf_crosswalk.md`](nist_csf_crosswalk.md) | `content/mappings/nist_csf/` |
| SOC 2 (TSC) | [`soc2_crosswalk.md`](soc2_crosswalk.md) | `content/mappings/soc2/` |
| EU AI Act Art. 73 (serious-incident reporting) | [`eu_ai_act_art73_serious_incident_reporting.md`](eu_ai_act_art73_serious_incident_reporting.md) | `content/mappings/eu_ai_act/article-73-serious-incident-reporting.yaml` |

## Structure of an entry

Each entry follows the same outline so a reader can scan across
playbooks without re-learning the layout:

1. **What the playbook does** — one paragraph naming the regulatory
   anchors and the operator-facing outcome.
2. **CACAO topology** — the step list at a glance, with the per-step
   primitives binding (`x_secops_ng.core_body`) called out where it
   exists and the absent-body steps flagged so an operator knows which
   stubs they still have to wire.
3. **Deterministic primitives** — the helper functions under
   `content/playbooks/<workflow>/primitives/` that the CACAO
   `core_body` refs resolve to. Severity bands, idempotency keys,
   freshness windows, and any other replay-determining policy lives
   here.
4. **Per-target hand-off** — what the n8n, Temporal, and LangGraph
   reference compilers emit, what they bind by default, what they
   leave for the operator, and what the OTel + AuditTrail observability
   contract looks like in each runtime.
5. **Replay and audit story** — how the same disclosure is byte-
   identical across targets, what `AuditTrail` carries when there is
   no OTLP collector, and which tests pin the property.
6. **What the cookbook deliberately does not cover** — credentials,
   per-deployment topology, and any operator decision the framework
   refuses to centralise.
