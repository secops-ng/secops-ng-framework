# GDPR Data-Flow Templates

This directory holds **data-flow templates** aligned to Regulation (EU)
2016/679 (the General Data Protection Regulation). The templates exist so
that an operator running SecOps-NG can describe, in a uniform shape, every
flow of personal data that touches the framework — and so that two
operators in two different jurisdictions can hand each other a document
that means the same thing.

## Why this matters for a security framework

Security telemetry frequently contains personal data: usernames in logs,
source IP addresses, email addresses in alert payloads, identifiers in
case-management traffic. Treating that data with the same care as any
other personal-data processing is both a legal obligation under GDPR and a
**community-protective** practice: the people whose data flows through a
SecOps-NG workflow are usually the same people the workflow is trying to
protect.

## Files

- [`data-flow-template.md`](data-flow-template.md) — the canonical template,
  with seven required sections. Copy and fill in per flow.
- [`example-vulnerability-triage.md`](example-vulnerability-triage.md) —
  worked example for the reference `vulnerability_triage` workflow.
- [`lawful-basis-notes.md`](lawful-basis-notes.md) — guidance on choosing
  the correct lawful basis under Article 6(1).

## Articles most directly relevant

| Article | Subject |
|---------|---------|
| 5       | Principles relating to processing of personal data |
| 6       | Lawfulness of processing |
| 9       | Processing of special categories of personal data |
| 13–14   | Information to be provided to data subjects |
| 25      | Data protection by design and by default |
| 28      | Processor obligations |
| 30      | Records of processing activities |
| 32      | Security of processing |
| 33–34   | Personal data breach notification |
| 35      | Data protection impact assessment |
| 44–49   | Transfers of personal data to third countries |

## How the template relates to Article 30 records

The seven-section template is designed so that, when populated, it directly
satisfies the **record-of-processing-activities** obligation under
Article 30(1) for controllers and Article 30(2) for processors. The
field-to-article mapping is in `data-flow-template.md`.

## Status

**Scaffold only.** Coder will wire automated emission of partial
data-flow documents from workflow contracts in a subsequent commit.
Markers labelled `<!-- coder:wire -->` indicate the integration points.

<!-- coder:wire — `secops_ng.compliance.gdpr.data_flow_from_contract`
     should generate a partial data-flow document from a workflow's
     Pydantic input/output contracts. Operators fill in the
     human-judgement fields (lawful basis, retention rationale, transfer
     safeguards). -->
