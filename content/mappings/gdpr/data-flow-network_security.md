# GDPR data flow — network_security

Per-workflow GDPR data-flow entry for the `network_security` cookbook
playbook (`playbook.network_security@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
eight sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/network_security/`](../../playbooks/network_security/).

---

## 1. Purpose

The workflow exists to operationalise the network-security and
segmentation posture-management capability against the operator's
own deployed estate: on a scheduled reconciliation cadence enumerate
the documented network segments (VLAN / VPC / subnet / zone
identifiers pulled from the operator's declarative network-inventory
sources), evaluate the segmentation policy against the observed
reachability posture, detect and classify policy violations against
the declared zone-transit matrix, engage remediation on the
operator's pre-bound remediation surface, and publish the dated
network-security-posture evidence artifact for the reconciliation
window. The purpose is bounded to that per-window boundary
reconciliation decision and the metric hooks it will later feed
(segmentation-drift cardinality, unauthorised-egress cardinality);
the workflow does not author the operator's segmentation
architecture, does not inspect the application-layer payloads the
segmented services carry during normal operation, and does not
introduce a new processing purpose against the subject data those
services may otherwise hold.

## 2. Lawful basis

**Out of scope: no personal data processed in this workflow.**

The workflow operates on segment identifiers, policy-snapshot
identifiers, violation-record identifiers, remediation-action
identifiers, and evidence-record identifiers. The fields it reads
and writes are: network-segment identifiers (VLAN identifiers, VPC
identifiers, subnet CIDRs, zone identifiers, boundary-control
identifiers, infrastructure-as-code resource addresses),
segmentation-policy snapshot identifiers, per-segment-pair allowance
enumerations (allowed / denied / conditional), observed-reachability
markers against the operator's documented telemetry sources,
per-violation records carrying segment-pair identifiers and
classification enumerations (undocumented-transit,
unauthorised-egress, boundary-control-drift), remediation-action
identifiers against the operator's pre-bound remediation surface
(per-segment ACL / firewall-rule change ticket, boundary-control
posture-change ticket, short-circuit isolation reference), and
posture-evidence record identifiers. None of these carry personal
data within the meaning of GDPR Art. 4(1): the workflow exercises
the network-boundary reconciliation discipline against the
operator's documented segmentation surfaces, it does not process
the personal-data payload those surfaces may carry during normal
operation.

The segmented services themselves may, depending on the operator's
documented inventory, carry personal data in their normal request /
response payloads — but the lawful basis for that underlying
processing (production-system processing of subject data) lives on
the operator's production-system data-flow entries, not on this
network-security posture playbook. This workflow is the per-window
boundary-reconciliation discipline that NIS2 Art. 21(2)(e) and
DORA Art. 9 require operators to run against their deployed estate;
it does not introduce a new processing purpose against the subject
data.

If a future revision of this workflow extends scope to inspect
per-flow payload contents (for example, to surface application-
layer attacker fingerprints from request bodies during boundary-
drift classification), this section MUST be revisited and a real
lawful basis declared before that extension ships.

## 3. Categories of data subjects and personal data

Not applicable — no personal data processed. The workflow operates
on network-segment identifiers, segmentation-policy snapshot
identifiers, per-segment-pair allowance enumerations, observed-
reachability markers, per-violation classification records,
remediation-action identifiers, and posture-evidence record
identifiers. No category of natural person is the subject of the
processing.

For completeness: the detect-policy-violations step reads
operator-bound network-telemetry sources documented for the
segmented estate. Where the operator's documented telemetry schema
includes source IP addresses in the per-segment reachability
observations, those addresses are read as segment-pair reachability
inputs to the violation-classification (deciding whether a cross-
segment path is undocumented-transit, unauthorised-egress, or
boundary-control-drift) and are not retained on the posture-evidence
record or the remediation payload. If the operator's documented
telemetry schema is amended to include subject-identifier fields the
workflow emits onto the posture-evidence record, this section MUST
be re-scored against the categories of subjects and personal data so
retained.

## 4. Recipients

Not applicable for personal data. For completeness, the recipients
of the non-personal evidence data the workflow emits are:

- the operator's **evidence store** — primary recipient of the
  dated network-security-posture evidence artifact (the audit-
  evident artifact NIS2 Art. 21(2)(e) / DORA Art. 9 reviewers read);
- the operator's **pre-bound remediation surface** (per-segment
  ACL / firewall-rule change tickets, boundary-control posture-
  change tickets, short-circuit isolation dispatchers) — receives
  a write call from the enforce-remediation step against the
  operator's documented remediation channels; the payload carries
  the remediation directive against the offending segment pair,
  not any per-subject data.

No external processor is invoked for personal-data processing; the
remediation surfaces named above process operator-bound segment
identifiers and violation-classification enumerations.

## 5. Retention

Not applicable for personal data. For completeness, the dated
network-security-posture evidence artifact is retained as the
operator's NIS2 Art. 21(2)(e) / DORA Art. 9 evidence under the
operator's regulatory-retention overlay; the retention mechanism is
the evidence-bundle expiry rule shared with the other evidence
streams under `schemas/evidence/bundle.schema.json`. This workflow
does not maintain its own retention schedule.

The network-telemetry sources the workflow consults at the
detect-policy-violations step are governed by the operator's
network-telemetry retention policy, which lives outside this
playbook. The workflow reads them for the duration of the
per-window reconciliation; it does not extend or shorten their
retention and does not project per-record fields onto the
posture-evidence record.

## 6. Cross-border transfers

**No transfer.** The default configuration runs the
inventory-network-segments read, the evaluate-segmentation-policy
read, the detect-policy-violations observation, the enforce-
remediation write, and the generate-posture-evidence-artifact
emission entirely against operator-bound, EU-resident endpoints
(the operator's declarative IaC records, cloud-provider network
APIs pinned to EU regions, on-premise network-controller
inventories, pre-bound remediation channels, and evidence store).
No public-cloud-AI dependency is wired on the workflow's hot path.
Operators MAY swap in a non-EU-hosted network-inventory source or
non-EU-hosted remediation channel; doing so is visible on a fork of
this data-flow doc, but is not the default and is not the
configuration the framework ships.

Even where the segmented services carry personal data governed by
Chapter V on the production-side workflow, the per-window
boundary-reconciliation discipline this playbook operates does not
itself cross a Chapter V boundary — the workflow's remediation
dispatch and evidence emission land on operator-bound endpoints,
not on a third-country endpoint.

## 7. Data subject rights

Not applicable — no personal data processed, no data subject to
exercise a right against this workflow. Subject Access Requests,
rectification requests, erasure requests, and objections that bear
on traffic the segmented services may have carried during the
reconciliation window are answered against the operator's
production-side workflows that own the subject data; the
network_security playbook neither creates a new subject record nor
holds a copy of one that a subject could exercise rights against
independently.

The dated network-security-posture evidence artifact names the
reconciliation window, the segment-inventory snapshot identifier,
the policy-snapshot identifier, the violation-set identifier, and
the remediation-action identifier; it carries no subject-identifier
fields.

## 8. Outbound personal-data transfer

**No outbound personal-data transfer — N/A.** Per §3, the workflow
processes network-segment identifiers, segmentation-policy snapshot
identifiers, per-segment-pair allowance enumerations, observed-
reachability markers, per-violation classification records,
remediation-action identifiers, and posture-evidence record
identifiers; no category of natural person is the subject of the
processing, so no Chapter V outbound leg exists.

The non-personal-data outbound legs documented elsewhere (evidence-
store publication in §4, remediation-surface engagement in §4) do
not engage Chapter V because their payloads carry no personal data:
the posture-evidence artifact names the reconciliation window and
the reconciled snapshot / policy / violation / remediation
identifiers, and the remediation directive carries the offending
segment pair and the classification enumeration against the
operator's pre-bound remediation surface.

Cross-reference §6: the workflow-as-a-whole cross-border scoring is
**no transfer** and this §8 carries no contradicting leg.

If a future binding wires a non-EU-hosted network-inventory source,
a non-EU-hosted remediation channel, a posture-evidence field that
captures a subject-identifier excerpt from the observed telemetry,
or any other surface that introduces personal data into the
per-window reconciliation discipline, this section MUST be re-scored
against the canonical four-axis shape (destination class, transfer
mechanism, EU-residency posture, data minimisation) and §3 amended
in the same change.
