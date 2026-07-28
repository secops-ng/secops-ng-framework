# GDPR data flow — eu_ai_act_deployer_obligations

Per-workflow GDPR data-flow entry for the `eu_ai_act_deployer_obligations`
playbook (`playbook.eu_ai_act_deployer_obligations@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/eu_ai_act_deployer_obligations/`](../../playbooks/eu_ai_act_deployer_obligations/).

---

## 1. Purpose

Discharge and evidence the EU AI Act Article 26 obligations of a
deployer running a third-party high-risk AI system in production, and
the Article 27 fundamental-rights impact assessment that gates first
use. Concretely: record who has been assigned competent human oversight
of a named deployment and on what evidence; record that workers subject
to a workplace deployment were informed before it went into service;
record each monitoring window's observation and any escalation to
suspension or authority notification; record the assessment of impact on
the fundamental rights of the categories of people the deployment
affects; and record the retention disposition applied to the logs the
system generates automatically.

The personal data processed here is incidental to a compliance record —
the workflow exists to prove obligations were met, not to profile
anyone. It makes no decision about any data subject.

## 2. Lawful basis

Primary: **Art. 6(1)(c) — compliance with a legal obligation to which
the controller is subject.** This is unusually clean for a
security-operations workflow. Every record the playbook emits exists
because Regulation (EU) 2024/1689 compels it: Art. 26(2) compels the
oversight assignment, Art. 26(6) compels the log retention, Art. 26(7)
compels the worker notice, and Art. 27 compels the assessment and its
notification. The operator has no discretion over whether to hold these
records.

Secondary: **Art. 6(1)(f) — legitimate interests**, available for the
narrow margin where an operator retains detail beyond the statutory
minimum for its own assurance purposes. Where the operator relies on
6(1)(f) for that margin, the Art. 21 objection right in §7 applies to
it.

**Special-category data (Art. 9):** not processed by this workflow.
Note the boundary carefully — the *deployed AI system* may process
special-category data, and the Art. 27 assessment may have to describe
that risk. Describing a risk category in an assessment is not the same
as this workflow processing the underlying data, and the assessment
record must be written to keep it that way: name categories of affected
persons, not identified individuals.

## 3. Categories of data subjects and personal data

| Data subject category | Personal data in this workflow |
|---|---|
| **Oversight assignees** — the operator's own staff assigned under Art. 26(2) | Name or role identifier, competence evidence, training-completion attestation, the scope of delegated authority, and the dated assignment record |
| **Workers subject to a workplace deployment** — Art. 26(7) | The dated notice record and the representative body or worker group notified. Individual workers are normally recorded as a group, not enumerated |
| **Persons affected by the deployment** — assessed under Art. 27(1)(c) | **Categories and groups only.** The assessment names affected categories (for example "applicants for a public benefit", "insurance policyholders") and the risks of harm to them. It does not enumerate individuals |
| **Data subjects appearing in automatically generated logs** — Art. 26(6) | Whatever the deployed system writes, which the operator does not choose. This workflow records the *retention disposition* over those logs; it does not read their contents |

The distinction in the last two rows is the one to preserve on
implementation: the workflow's own records are about the deployment and
its overseers, and reach affected individuals only at category level.

## 4. Recipients

- **The provider of the high-risk AI system** — receives the Art. 26(5)
  routine monitoring information feeding its Art. 72 post-market loop,
  and is the first recipient in the serious-incident notification
  sequence.
- **The importer or distributor** — second in the Art. 26(5)
  serious-incident sequence, where one exists in the chain.
- **The market-surveillance authority of the relevant Member State** —
  receives the Art. 26(5) risk notification and the Art. 27(4)
  notification of the assessment result. A public authority acting under
  statutory powers, not a processor.
- **Internal recipients** — the operator's governance function
  (assignment and approval records) and, for the Art. 26(7) notice, the
  works council or equivalent worker-representative body.

No external processor is invoked by the workflow itself. Where the
operator's deployment register, evidence store or log store is a
third-party service, that provider is a processor under Art. 28 and the
dependency is the operator's to record — the framework declares the
contract for those surfaces and ships none of them.

## 5. Retention

The Art. 26(6) statutory rule governs and is a **floor, not a target**:
logs automatically generated by the system, to the extent under the
deployer's control, are retained for a period appropriate to the
intended purpose of the system and **at least six months**, unless Union
or national law provides otherwise. Sector law frequently provides
otherwise and longer.

The workflow's own compliance records — the intended-use determination,
the oversight assignment, the monitoring observations, the assessment,
and the retention disposition itself — are retained for as long as the
deployment is in service plus the operator's evidentiary tail, because
they are the evidence that the obligations were met while it ran.

Enforcement is operator-side: the retention period is applied by the
operator's evidence store and log store, and the workflow's contribution
is the dated record stating which period was applied and on what basis.
The framework ships no store and therefore enforces no TTL.

## 6. Cross-border transfers

**No transfer**, by default and by construction.

Every recipient in §4 is EU-resident: the market-surveillance authority
is a Member State body, and the provider, importer and distributor of a
high-risk AI system placed on the Union market are addressable within
the Union. The EU-resident inference-endpoint guard in the shared
compiler layer holds the posture for any compiled target, and the
workflow makes no public-cloud-AI call.

The dependency that would break this scoring is the operator's own
choice of evidence store or log store. If either is hosted outside the
EU/EEA, the retention records in §5 and the assessment record in §3
leave the Union and the leg must be re-scored under Art. 46 with
supplementary measures. That is an operator binding, not a framework
default, and it is the swap to watch in review.

## 7. Data subject rights

- **Access (Art. 15)** — an oversight assignee's data is located in the
  assignment record keyed on the deployment identifier; a worker's is in
  the Art. 26(7) notice record. Both are indexed by deployment, so a
  Subject Access Request is answered by resolving the deployments the
  subject was assigned to or subject to.
- **Rectification (Art. 16)** — applies to the assignment record, where
  competence, training or authority attributes may be recorded wrongly
  or go stale. Correcting them is a re-assignment, and the superseded
  record is retained because it evidences who held oversight at the
  time.
- **Erasure (Art. 17)** — substantially restricted while the deployment
  is in service. The records exist under Art. 6(1)(c) to satisfy a legal
  obligation, so Art. 17(3)(b) applies; the retention hook in §5 is the
  operative mechanism rather than on-request deletion.
- **Objection (Art. 21)** — not available against the Art. 6(1)(c)
  records. It is available against any margin the operator retains under
  6(1)(f) per §2, and is handled by dropping that margin for the
  objecting subject while the statutory record stands.
- **Automated decision-making (Art. 22)** — **this workflow makes no
  automated decision about any data subject.** It records determinations
  about a *deployment*. The deployed AI system it oversees may well make
  Art. 22 decisions, and where it does, that is precisely what the
  Art. 27 assessment must examine and what the Art. 26(2) human
  oversight exists to interrupt. The distinction matters: this playbook
  is part of the safeguard, not part of the decision.
