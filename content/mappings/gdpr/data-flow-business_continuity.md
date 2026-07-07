# GDPR data flow — business_continuity

Per-workflow GDPR data-flow entry for the `business_continuity`
plan-lifecycle playbook (`playbook.business_continuity@v1`). Filled
in against [`_data-flow-template.md`](./_data-flow-template.md).
Together the eight sections below form the Art. 30 Record of
Processing Activity entry for this workflow.

Workflow source of truth:
[`content/playbooks/business_continuity/`](../../playbooks/business_continuity/).

Sibling: the `backup_recovery` playbook operates the periodic
non-destructive restore-drill discipline against the same
NIS2 Art. 21(2)(c) surface; its data-flow entry lives at
[`./data-flow-backup_recovery.md`](./data-flow-backup_recovery.md).
This entry covers the event-driven plan-lifecycle side (declare →
activate → isolate → failover → notify → restore → PIR).

---

## 1. Purpose

The workflow exists to materialise the operator-side NIS2
Art. 21(2)(c) business-continuity plan-lifecycle on an event basis:
detect and declare a business-continuity event, activate the
documented BCM plan artifact, isolate affected systems where the
plan calls for it, failover the affected service to the documented
backup capacity, notify the competent authority on the NIS2 Art. 23
significant-incident path where the threshold is crossed, restore
the primary service and verify against the documented recovery
objectives, and persist the post-incident-review record. The
purpose is bounded to that plan-lifecycle envelope; the workflow
does not itself author the BCM plan, does not run against the
subject-data payload the affected service processes, and does not
introduce a new processing purpose against personal data.

## 2. Lawful basis

**Out of scope: no personal data processed in this workflow.**

The workflow operates on event metadata and infrastructure
identifiers, not on the personal-data payload the affected service
processes. The fields it reads and writes are: event identifiers,
event-declared timestamps (against the NIS2 Art. 23 clock),
BCM-plan artifact identifiers, isolation-scope identifiers,
failover-target identifiers, significance-threshold booleans,
NIS2 Art. 23 notification-artifact identifiers, recovery-result
records (observed RTO / RPO against documented objectives,
primary-service health signals), and post-incident-review record
identifiers. None of these carry personal data within the meaning
of GDPR Art. 4(1): the workflow exercises the plan-lifecycle of a
service, it does not process the personal-data payload that
service may hold.

The affected service may, depending on the operator's documented
processing register, process personal data — but the lawful basis
for the underlying processing (the service's own subject-data
processing, with availability as a security-of-processing
discipline under GDPR Art. 32(1)(b)/(c)) lives on the service's
own data-flow entries, not on this plan-lifecycle playbook. This
workflow is the availability-restoration discipline Art. 32(1)(c)
and NIS2 Art. 21(2)(c) require operators to run against those
services; it does not introduce a new processing purpose against
the subject data.

If a future revision extends scope to inspect subject-data payload
during restore-and-verify (for example, to validate per-record
fidelity of a personal-data table after cutback), this section
MUST be revisited and a real lawful basis declared before that
extension ships.

## 3. Categories of data subjects and personal data

Not applicable — no personal data processed. The workflow operates
on event metadata (identifiers, timestamps, significance booleans),
plan-artifact identifiers, isolation / failover / recovery
identifiers, and notification / PIR record identifiers. No
category of natural person is the subject of the processing.

For completeness: the competent-authority notification envelope
carries the operator entity's own reporting metadata (entity
identification, service scope, cross-border-effect indicator,
preliminary assessment) to the national cybersecurity authority
per NIS2 Art. 23. Where the underlying incident involved a
personal-data breach, the parallel GDPR Art. 33 supervisory-
authority notification is a separate workflow on the operator's
side and is not chained from this playbook — the Art. 33 lane
lives on the operator's incident-management / data_exfil surfaces
and any wiring between the two lanes is documented on those
overlays, not here.

## 4. Recipients

Not applicable for personal data. For completeness, the recipients
of the non-personal event-driven data the workflow emits are:

- the operator's **evidence store** — primary recipient of the
  post-incident-review record and the associated activation /
  failover / restore attestations (the audit-evident artifact
  NIS2 Art. 21(2)(c) and DORA Art. 11 reviewers read);
- the operator's **competent authority** (the national
  cybersecurity authority per the entity's establishment Member
  State) — recipient of the NIS2 Art. 23 24h early warning, 72h
  incident notification, and one-month final report where the
  event crosses the significant-incident threshold;
- the **catalogue metric pipeline** that reads the recovery-
  timeliness signal for programme-level rollup (handled by the
  sibling `executive_metrics` workflow).

No external processor is invoked by the default configuration; the
BCM-plan store, the isolation surface, the failover surface, and
the evidence store are all operator-bound infrastructure.

## 5. Retention

Not applicable for personal data. For completeness, the post-
incident-review record and the associated activation / failover /
restore attestations are retained as the operator's NIS2
Art. 21(2)(c) / DORA Art. 11 evidence under the operator's
regulatory-retention overlay; the retention mechanism is the
evidence-bundle expiry rule shared with the other evidence streams
under `schemas/evidence/bundle.schema.json`. This workflow does
not maintain its own retention schedule.

The NIS2 Art. 23 notification envelope is retained under the
operator's regulator-correspondence retention policy, which lives
outside this playbook. The workflow only resolves and reads the
BCM-plan artifact for the duration of the lifecycle; it does not
extend or shorten its retention.

## 6. Cross-border transfers

**No transfer.** The default configuration runs the activate,
isolate, failover, restore-and-verify, and PIR steps entirely
against operator-bound, EU-resident endpoints (the operator's
BCM-plan store, isolation surface, failover surface, and evidence
store). The competent-authority notification lands at the national
cybersecurity authority of the entity's establishment Member State,
which is an EU endpoint under EU public authority. No public-cloud-
AI dependency is wired on the workflow's hot path. Operators MAY
swap in a non-EU-hosted failover target; doing so is visible on a
fork of this data-flow doc, but is not the default and is not the
configuration the framework ships.

Even where the affected service processes personal data governed
by Chapter V on the service's own workflows, the plan-lifecycle
this playbook operates does not itself cross a Chapter V boundary
— the failover lands on the operator's documented EU-resident
backup capacity and the notification lands at an EU authority.

## 7. Data subject rights

Not applicable — no personal data processed, no data subject to
exercise a right against this workflow. Subject Access Requests,
rectification requests, erasure requests, and objections that bear
on the underlying subject data are answered against the affected
service's own workflows that own that data; the business_continuity
playbook neither creates a new subject record nor holds a copy of
one that a subject could exercise rights against independently.

The post-incident-review record and the Art. 23 notification
envelope name the affected service by identifier, not by subject
content.

## 8. Outbound personal-data transfer

**No outbound personal-data transfer — N/A.** Per §3, the workflow
processes event metadata, plan / isolation / failover / recovery
identifiers, and notification / PIR record identifiers; no
category of natural person is the subject of the processing, so
no Chapter V outbound leg exists.

The non-personal-data outbound legs documented elsewhere
(evidence-store publication in §4, competent-authority notification
in §4, the catalogue-metric pipeline rollup in §4) do not engage
Chapter V because their payloads carry no personal data: the
notification envelope carries the operator entity's reporting
metadata and the service-scope identifier to the national
cybersecurity authority (an EU endpoint), and the PIR record names
the affected service by identifier.

Cross-reference §6: the workflow-as-a-whole cross-border scoring
is **no transfer** and this §8 carries no contradicting leg.

If a future binding wires a non-EU-hosted failover target, a
notification field that captures a subject-identifier excerpt from
the affected service, or any other surface that introduces
personal data into the plan-lifecycle discipline, this section
MUST be re-scored against the canonical four-axis shape
(destination class, transfer mechanism, EU-residency posture, data
minimisation) and §3 amended in the same change.
