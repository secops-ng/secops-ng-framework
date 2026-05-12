# NIS2 Article 23 — Reporting Obligations

**Directive (EU) 2022/2555, Article 23 — Reporting obligations**

## Obligation

Article 23 imposes a **three-stage reporting timeline** on essential and
important entities for significant incidents:

| Stage | Deadline | Content |
|-------|----------|---------|
| Early warning (Article 23(4)(a)) | **Without undue delay and in any event within 24 hours** of becoming aware of the significant incident | Indication of whether the incident is suspected of being caused by unlawful or malicious acts or could have a cross-border impact |
| Incident notification (Article 23(4)(b)) | **Without undue delay and in any event within 72 hours** of becoming aware of the significant incident | Update of the early-warning information; initial assessment of the incident, including its severity and impact, and, where available, the indicators of compromise |
| Final report (Article 23(4)(d)) | **Not later than one month** after submission of the incident notification | Detailed description, type of threat, applied mitigation, and, where applicable, cross-border impact |

An **intermediate report** (Article 23(4)(c)) may be required by the CSIRT
or competent authority at any time before the final report, summarising
relevant status updates.

Article 23(1) defines a "significant incident" as one which has caused or is
capable of causing severe operational disruption of the services or
financial loss for the entity concerned; or has affected or is capable of
affecting other natural or legal persons by causing considerable material
or non-material damage.

Article 23(3) requires entities to **notify recipients of their services**,
without undue delay, of significant incidents that are likely to adversely
affect the provision of those services.

## SecOps-NG mapping

Reporting timelines are the single hardest operational requirement in NIS2
for under-staffed teams: the 24-hour clock starts ticking on *awareness*,
not on confirmation. SecOps-NG can help with **awareness, evidence assembly,
and submission rehearsal**.

| Article 23 element | SecOps-NG contribution |
|--------------------|------------------------|
| Awareness timestamp (Article 23(4)(a)) | Workflow ingestion timestamps are durable and unforgeable — they establish the moment the system became aware, which the operator can use to anchor the 24-hour clock. |
| Early warning content (Article 23(4)(a)) | The `vulnerability_triage` and forthcoming `incident_enrichment` workflows produce structured outputs that contain the malicious-act suspicion field and the cross-border indicators required by 23(4)(a). |
| Incident notification (Article 23(4)(b)) | Workflow outputs at this stage include initial severity, impact, and IoCs in Pydantic-validated form, suitable for direct submission to the CSIRT's intake schema. |
| Intermediate report (Article 23(4)(c)) | Workflow replay state at any point yields the same content as the original notification updated to current time. |
| Final report (Article 23(4)(d)) | The complete workflow timeline plus operator-authored mitigation narrative form the final report's evidentiary basis. |
| Recipient notification (Article 23(3)) | Out of direct framework scope; the framework can trigger but does not own the comms channel. |

## Evidence stream

- `../evidence/incidents/<workflow-id>/awareness.json` — timestamped record
  of the moment the workflow became aware of the incident. The single most
  important artefact for the 24-hour clock.
- `../evidence/incidents/<workflow-id>/early-warning.json` — content for
  Article 23(4)(a) submission.
- `../evidence/incidents/<workflow-id>/notification.json` — content for
  Article 23(4)(b) submission.
- `../evidence/incidents/<workflow-id>/final-report.json` — content for
  Article 23(4)(d) submission.

<!-- coder:wire — incident-evidence emitters not yet implemented. The
     `secops_ng.evidence.incidents` module will own these. Schemas live
     in `src/secops_ng/contracts.py`. -->

## Gaps

- **Submission transport** is out of scope. Each Member State has a
  different CSIRT intake mechanism (web portal, email, API). Operators
  must wire the last mile themselves.
- **Severity classification** under each Member State's transposition law
  may differ from the framework's default thresholds. The thresholds are
  configurable; the default is conservative (i.e. errs on the side of
  reporting).

## References

- Directive (EU) 2022/2555, Article 23(1)–(11).
- Implementing Regulation (EU) 2024/2690 (where applicable, for digital
  infrastructure entities) for further specification of significance
  thresholds.
