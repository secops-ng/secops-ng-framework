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
| `cyber_hygiene_training` | [`cyber_hygiene_training.md`](cyber_hygiene_training.md) | `content/playbooks/cyber_hygiene_training/`     |
| `cra_srp_notify`      | [`cra_srp_notify.md`](cra_srp_notify.md)           | `content/playbooks/cra_srp_notify/`                   |
| `cra_cvd`             | [`cra_cvd.md`](cra_cvd.md)                         | `content/playbooks/cra_cvd/`                          |
| `mfa_secured_comms`   | [`mfa_secured_comms.md`](mfa_secured_comms.md)     | `content/playbooks/mfa_secured_comms/`                |
| `data_subject_rights` | [`data_subject_rights.md`](data_subject_rights.md) | `content/playbooks/data_subject_rights/`              |

Additional entries land alongside their content sources as workflows
flip from In Progress to Shipped on
[`ROADMAP.md`](../../ROADMAP.md).

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
