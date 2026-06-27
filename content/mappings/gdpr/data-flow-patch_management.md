# GDPR data flow — patch_management

Per-workflow GDPR data-flow entry for the `patch_management` cookbook
playbook (`playbook.patch_management@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/patch_management/`](../../playbooks/patch_management/).

---

## 1. Purpose

The workflow exists to operationalise the maintenance capability
against the operator's own deployed estate: on a security update
becoming available against a tracked package / image / firmware
line, classify the update against the operator's documented
patch-criticality taxonomy (security-critical, security-routine,
feature-only), stage the rollout against the operator's documented
deployment-ring topology (test → canary → broad), validate the
canary ring against documented health gates, fan out to the
remaining rings on a green canary, capture the dated patch-
application evidence record, and notify the maintenance owner.
The purpose is bounded to that per-update rollout decision and the
metric hooks it will later feed (time-to-patch, patch-coverage);
the workflow does not author the operator's patch-distribution
architecture, does not retain or inspect the contents of the
deployed artifacts beyond the inventory and ring-cohort counters
needed for rollout staging, and does not introduce a new processing
purpose against the subject data the deployed services may
otherwise carry.

## 2. Lawful basis

**Out of scope: no personal data processed in this workflow.**

The workflow operates on deployment-inventory identifiers, advisory
references, ring-cohort identifiers, and attestation records. The
fields it reads and writes are: tracked package / image / firmware
identifiers, advisory references (CVE-style identifiers, vendor
advisory ids, severity / exploit-status enumerations), classified-
criticality enumerations (security-critical, security-routine,
feature-only), deployment-ring identifiers and ring-cohort
identifiers against the operator's documented ring topology,
canary-health gate observations (functional-probe pass / fail,
aggregate error-rate / latency deviation against documented
thresholds), rollout-action identifiers against the operator's
pre-bound distribution-channel push endpoints and change-management
ticketing, broad-rollout identifiers, dated patch-application
evidence record identifiers, and the maintenance owner's pre-bound
channel identifier. None of these carry personal data within the
meaning of GDPR Art. 4(1): the workflow exercises the maintenance
capability of a documented deployed estate, it does not process the
personal-data payload that estate may carry during normal
operation.

The deployed services themselves may, depending on the operator's
documented inventory, carry personal data in their normal request /
response payloads — but the lawful basis for that underlying
processing (production-system processing of subject data) lives on
the operator's production-system data-flow entries, not on this
maintenance-rollout playbook. This workflow is the per-update
rollout discipline that NIS2 Art. 21(2)(e) requires operators to
run against security updates on those services; it does not
introduce a new processing purpose against the subject data.

If a future revision of this workflow extends scope to inspect
per-request payload contents at the canary-health gate (for example,
to surface application-layer regression fingerprints from request
bodies), this section MUST be revisited and a real lawful basis
declared before that extension ships.

## 3. Categories of data subjects and personal data

Not applicable — no personal data processed. The workflow operates
on deployment-inventory identifiers, advisory references, ring-
cohort identifiers, canary-health gate observations, rollout-action
identifiers, and attestation records. No category of natural person
is the subject of the processing.

For completeness: the validate-canary step reads operator-bound
canary-health endpoints documented for the deployed services
participating in the canary cohort. Where the operator's documented
health-endpoint schema includes source IP addresses or request
identifiers, those values are read as aggregate-counter inputs to
the functional-probe and error-rate / latency deviation
classification (deciding whether to fan out or hold the rollout) and
are not retained on the evidence record or the notification payload.
If the operator's documented health-endpoint schema is amended to
include subject-identifier fields the workflow emits onto the
evidence record, this section MUST be re-scored against the
categories of subjects and personal data so retained.

The maintenance owner's pre-bound channel identifier (ticketing
system, chat thread, page-out roster) is a contact endpoint, not a
data-subject record — the notify-maintenance-owner step delivers an
evidence reference along that channel and does not introduce or
retain a per-subject record beyond what the operator's notification
surface already holds independently.

## 4. Recipients

Not applicable for personal data. For completeness, the recipients
of the non-personal evidence data the workflow emits are:

- the operator's **evidence store** — primary recipient of the
  dated patch-application evidence record (the audit-evident
  artifact NIS2 Art. 21(2)(e) reviewers read);
- the operator's **maintenance owner** along their pre-bound
  channel — receives the evidence reference via the
  notify-maintenance-owner step;
- the operator's **distribution-channel push endpoint** (update
  channel against the deployed estate) and **change-management
  ticketing surface** as the rollout-engagement recipients —
  receive write calls from the stage-rollout-to-canary-ring and
  fan-out-to-broad-rings steps against the operator's pre-bound
  API surfaces; the payloads carry the rollout directive against
  the deployment-ring topology, not any per-subject data.

No external processor is invoked for personal-data processing; the
rollout surfaces named above process operator-bound deployment-
inventory identifiers, advisory references, and ring-cohort
identifiers.

## 5. Retention

Not applicable for personal data. For completeness, the dated
patch-application evidence record is retained as the operator's
NIS2 Art. 21(2)(e) evidence under the operator's
regulatory-retention overlay; the retention mechanism is the
evidence-bundle expiry rule shared with the other evidence streams
under `schemas/evidence/bundle.schema.json`. This workflow does not
maintain its own retention schedule.

The advisory-intake feeds and canary-health endpoints the workflow
consults at the detect-patch-availability, classify-patch-
criticality, and validate-canary steps are governed by the
operator's advisory-source and operational-telemetry retention
policies, which live outside this playbook. The workflow reads them
for the duration of the rollout window; it does not extend or
shorten their retention and does not project per-record fields onto
the evidence record.

## 6. Cross-border transfers

**No transfer.** The default configuration runs the
detect-patch-availability read, the classify-patch-criticality
read, the stage-rollout-to-canary-ring write, the validate-canary
observation, the fan-out-to-broad-rings write, the evidence-capture
emission, and the notify dispatch entirely against operator-bound,
EU-resident endpoints (the operator's advisory-intake surface,
distribution-channel push endpoints, change-management ticketing,
canary-health endpoints, evidence store, and maintenance-owner
channel). No public-cloud-AI dependency is wired on the workflow's
hot path. Operators MAY swap in a non-EU-hosted advisory-intake
provider or a non-EU-hosted distribution channel; doing so is
visible on a fork of this data-flow doc, but is not the default and
is not the configuration the framework ships.

Even where the deployed services carry personal data governed by
Chapter V on the production-side workflow, the per-update rollout
discipline this playbook operates does not itself cross a Chapter V
boundary — the workflow's rollout engagement and evidence emission
land on operator-bound endpoints, not on a third-country endpoint.

## 7. Data subject rights

Not applicable — no personal data processed, no data subject to
exercise a right against this workflow. Subject Access Requests,
rectification requests, erasure requests, and objections that bear
on traffic the deployed services may have carried during the
rollout window are answered against the operator's production-side
workflows that own the subject data; the patch_management playbook
neither creates a new subject record nor holds a copy of one that a
subject could exercise rights against independently.

The dated patch-application evidence record names the tracked
artifact by identifier, the criticality by classification
enumeration, the engaged ring-cohort by identifier, and the
broad-rollout by action identifier; it carries no subject-identifier
fields.

## 8. Outbound personal-data transfer

**No outbound personal-data transfer — N/A.** Per §3, the workflow
processes deployment-inventory identifiers, advisory references,
ring-cohort identifiers, canary-health gate observations,
rollout-action identifiers, and attestation records; no category of
natural person is the subject of the processing, so no Chapter V
outbound leg exists.

The non-personal-data outbound legs documented elsewhere (evidence-
store publication in §4, maintenance-owner notification in §4,
distribution-channel and change-management engagement in §4) do not
engage Chapter V because their payloads carry no personal data: the
evidence record names the tracked artifact and the engaged ring
cohort by identifier, the notification carries the evidence
reference along an operator-bound channel, and the rollout directive
carries the deployment-ring identifier and the criticality
classification against the operator's pre-bound API surface.

Cross-reference §6: the workflow-as-a-whole cross-border scoring is
**no transfer** and this §8 carries no contradicting leg.

If a future binding wires a non-EU-hosted advisory-intake provider,
a non-EU-hosted distribution channel, an evidence-record field that
captures a subject-identifier excerpt from the canary-health
observation, or any other surface that introduces personal data
into the per-update rollout discipline, this section MUST be
re-scored against the canonical four-axis shape (destination class,
transfer mechanism, EU-residency posture, data minimisation) and §3
amended in the same change.
