# GDPR data flow — ddos_response

Per-workflow GDPR data-flow entry for the `ddos_response` cookbook
playbook (`playbook.ddos_response@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/ddos_response/`](../../playbooks/ddos_response/).

---

## 1. Purpose

The workflow exists to operationalise the incident-handling
capability against the availability/denial-of-service attack
dimension: on an availability anomaly against a monitored service,
classify the attack vector, engage the operator's pre-bound
mitigation surface (upstream scrubbing, rate-limit / WAF posture
change, or failover to a documented standby), validate that the
protected service has been restored against documented availability
objectives, capture the dated evidence record, and notify the
incident-management owner. The purpose is bounded to that per-event
response decision and the metric hooks it will later feed (time-to-
mitigation, availability-restoration cadence); the workflow does not
author the operator's anti-DDoS architecture, does not retain or
inspect the contents of the traffic it observes beyond the
aggregate-counter level needed for vector classification, and does
not introduce a new processing purpose against the subject data the
protected service may otherwise carry.

## 2. Lawful basis

**Out of scope: no personal data processed in this workflow.**

The workflow operates on network-anomaly metrics, service
identifiers, attack-vector classifications, and attestation records.
The fields it reads and writes are: service identifiers, ISO 8601
anomaly windows, classified-vector enumerations (volumetric,
protocol, application-layer), aggregate throughput / error-rate /
latency series against the protected service, mitigation-action
identifiers against the operator's pre-bound response surface
(upstream-scrubbing provider reference, rate-limit / WAF
posture-change ticket id, failover-exercise reference), restoration
booleans, evidence record identifiers, and the incident-management
owner's pre-bound channel identifier. None of these carry personal
data within the meaning of GDPR Art. 4(1): the workflow exercises
the availability-defence capability of a documented service surface,
it does not process the personal-data payload that surface may carry
during normal operation.

The protected service itself may, depending on the operator's
documented inventory, carry personal data in its normal request /
response payloads — but the lawful basis for that underlying
processing (production-system processing of subject data) lives on
the operator's production-system data-flow entries, not on this
incident-response playbook. This workflow is the per-event
availability-defence discipline that NIS2 Art. 21(2)(b) requires
operators to run against incidents on those services; it does not
introduce a new processing purpose against the subject data.

If a future revision of this workflow extends scope to inspect
per-request payload contents (for example, to surface
application-layer attacker fingerprints from request bodies), this
section MUST be revisited and a real lawful basis declared before
that extension ships.

## 3. Categories of data subjects and personal data

Not applicable — no personal data processed. The workflow operates
on network-anomaly metrics, service identifiers, classified-vector
enumerations, aggregate throughput / error-rate / latency series,
mitigation-action identifiers, and attestation records. No category
of natural person is the subject of the processing.

For completeness: the classify-attack-vector step reads
operator-bound packet-capture / flow-record sources documented for
the protected service. Where the operator's documented flow-record
schema includes source IP addresses, those addresses are read as
aggregate-counter inputs to the volumetric / protocol / application-
layer classification (deciding which mitigation discipline to
engage) and are not retained on the evidence record or the
notification payload. If the operator's documented flow-record
schema is amended to include subject-identifier fields the workflow
emits onto the evidence record, this section MUST be re-scored
against the categories of subjects and personal data so retained.

The incident-management owner's pre-bound channel identifier
(ticketing system, chat thread, page-out roster) is a contact
endpoint, not a data-subject record — the
notify-incident-management-owner step delivers an evidence reference
along that channel and does not introduce or retain a per-subject
record beyond what the operator's notification surface already holds
independently.

## 4. Recipients

Not applicable for personal data. For completeness, the recipients
of the non-personal evidence data the workflow emits are:

- the operator's **evidence store** — primary recipient of the
  dated availability-incident evidence record (the audit-evident
  artifact NIS2 Art. 21(2)(b) reviewers read);
- the operator's **incident-management owner** along their
  pre-bound channel — receives the evidence reference via the
  notify-incident-management-owner step;
- the operator's **upstream-scrubbing provider**, **edge / WAF
  surface**, or **failover orchestration surface** as the
  mitigation-engagement recipient depending on the classified
  vector — receives a write call from the engage-mitigation step
  against the operator's pre-bound API surface; the payload carries
  the mitigation directive against the protected service, not any
  per-subject data.

No external processor is invoked for personal-data processing; the
mitigation surfaces named above process operator-bound service
identifiers and aggregate-counter inputs.

## 5. Retention

Not applicable for personal data. For completeness, the dated
availability-incident evidence record is retained as the operator's
NIS2 Art. 21(2)(b) evidence under the operator's
regulatory-retention overlay; the retention mechanism is the
evidence-bundle expiry rule shared with the other evidence streams
under `schemas/evidence/bundle.schema.json`. This workflow does not
maintain its own retention schedule.

The packet-capture / flow-record sources the workflow consults at
the classify-attack-vector step are governed by the operator's
network-telemetry retention policy, which lives outside this
playbook. The workflow reads them in aggregate for the duration of
the classification; it does not extend or shorten their retention
and does not project per-record fields onto the evidence record.

## 6. Cross-border transfers

**No transfer.** The default configuration runs the
detect-availability-anomaly observation, the classify-attack-vector
read, the engage-mitigation write, the validate-service-restoration
observation, the evidence-capture emission, and the notify dispatch
entirely against operator-bound, EU-resident endpoints (the
operator's monitoring surface, network-telemetry sources, pre-bound
mitigation surface, evidence store, and incident-management
channel). No public-cloud-AI dependency is wired on the workflow's
hot path. Operators MAY swap in a non-EU-hosted upstream-scrubbing
provider or non-EU-hosted edge surface; doing so is visible on a
fork of this data-flow doc, but is not the default and is not the
configuration the framework ships.

Even where the protected service carries personal data governed by
Chapter V on the production-side workflow, the per-event
availability-response discipline this playbook operates does not
itself cross a Chapter V boundary — the workflow's mitigation
engagement and evidence emission land on operator-bound endpoints,
not on a third-country endpoint.

## 7. Data subject rights

Not applicable — no personal data processed, no data subject to
exercise a right against this workflow. Subject Access Requests,
rectification requests, erasure requests, and objections that bear
on traffic the protected service may have carried during the
incident window are answered against the operator's production-side
workflows that own the subject data; the ddos_response playbook
neither creates a new subject record nor holds a copy of one that a
subject could exercise rights against independently.

The dated availability-incident evidence record names the protected
service by identifier, the attack vector by classification
enumeration, and the engaged mitigation by action identifier; it
carries no subject-identifier fields.

## 8. Outbound personal-data transfer

**No outbound personal-data transfer — N/A.** Per §3, the workflow
processes network-anomaly metrics, service identifiers,
classified-vector enumerations, mitigation-action identifiers, and
attestation records; no category of natural person is the subject
of the processing, so no Chapter V outbound leg exists.

The non-personal-data outbound legs documented elsewhere (evidence-
store publication in §4, incident-management-owner notification in
§4, mitigation-surface engagement in §4) do not engage Chapter V
because their payloads carry no personal data: the evidence record
names the protected service and the engaged mitigation by
identifier, the notification carries the evidence reference along
an operator-bound channel, and the mitigation directive carries the
service identifier and the vector classification against the
operator's pre-bound API surface.

Cross-reference §6: the workflow-as-a-whole cross-border scoring is
**no transfer** and this §8 carries no contradicting leg.

If a future binding wires a non-EU-hosted upstream-scrubbing
provider, a non-EU-hosted edge / WAF surface, an evidence-record
field that captures a subject-identifier excerpt from the
observed traffic, or any other surface that introduces personal
data into the per-event response discipline, this section MUST be
re-scored against the canonical four-axis shape (destination class,
transfer mechanism, EU-residency posture, data minimisation) and §3
amended in the same change.
