# GDPR data flow — asset_management

Per-workflow GDPR data-flow entry for the `asset_management` cookbook
playbook (`playbook.asset_management@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
eight sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/asset_management/`](../../playbooks/asset_management/).

---

## 1. Purpose

The workflow exists to operationalise the asset and configuration
management capability against the operator's own deployed estate:
on a scheduled reconciliation cadence ingest the documented
inventory-source set (CMDB, declarative infrastructure-as-code
records, cloud-provider asset APIs, endpoint-management agents),
reconcile them into the operator-authoritative snapshot for the
current window, compute the per-asset delta against the previous
documented snapshot, classify each delta against the operator's
documented delta taxonomy (new-managed, unmanaged-discovered,
decommissioned, baseline-drift), capture the dated asset-inventory-
delta evidence record, and notify the inventory owner. The purpose
is bounded to that per-window reconciliation decision and the
metric hooks it will later feed (asset-inventory-drift, unmanaged-
asset cardinality); the workflow does not author the operator's
inventory-source architecture, does not inspect the application-
layer payloads the inventoried services carry during normal
operation, and does not introduce a new processing purpose against
the subject data those services may otherwise hold.

## 2. Lawful basis

**Out of scope: no personal data processed in this workflow.**

The workflow operates on asset identifiers, inventory-source
identifiers, snapshot identifiers, delta identifiers, configuration-
baseline observations, and attestation records. The fields it reads
and writes are: tracked asset identifiers (hostnames, instance ids,
container image digests, infrastructure-as-code resource addresses,
endpoint-agent identifiers), inventory-source identifiers (CMDB
reference, IaC declaration set reference, cloud-provider asset-API
binding reference, endpoint-management agent fleet reference),
reconciled-snapshot identifiers, per-asset delta identifiers and
their previous-state / current-state markers, classification
enumerations (new-managed, unmanaged-discovered, decommissioned,
baseline-drift) and the unclassified marker, configuration-baseline
observations (declared baseline vs. observed configuration, hashed
or normalised against the operator's documented baseline schema),
dated reconciliation-window identifiers, dated asset-inventory-delta
evidence record identifiers, and the inventory owner's pre-bound
channel identifier. None of these carry personal data within the
meaning of GDPR Art. 4(1): the workflow exercises the asset-
management capability of a documented deployed estate, it does not
process the personal-data payload that estate may carry during
normal operation.

The inventoried assets themselves may, depending on the operator's
documented inventory, host or process personal data in their normal
request / response payloads — but the lawful basis for that
underlying processing (production-system processing of subject data)
lives on the operator's production-system data-flow entries, not on
this asset-reconciliation playbook. This workflow is the per-window
asset-management discipline that NIS2 Art. 21(2)(i) requires
operators to run against their documented inventory sources; it does
not introduce a new processing purpose against the subject data
those assets may hold.

If a future revision of this workflow extends scope to inspect
per-asset payload contents at the baseline-drift classification step
(for example, to surface application-layer configuration excerpts
that may include subject-identifier fields), this section MUST be
revisited and a real lawful basis declared before that extension
ships.

## 3. Categories of data subjects and personal data

Not applicable — no personal data processed. The workflow operates
on asset identifiers, inventory-source identifiers, snapshot
identifiers, delta identifiers, configuration-baseline observations,
and attestation records. No category of natural person is the
subject of the processing.

For completeness: the endpoint-management agent ingest path may
surface device identifiers that the operator's documented inventory
correlates against a human owner outside this workflow (e.g. an
asset assigned to a named employee on a separate HR-side record).
Such correlation is not performed by this playbook — the workflow
reads the device identifier as an opaque inventory identifier and
records it on the delta set against the operator's documented delta
taxonomy. Where the operator's documented inventory-source schema
is amended to include subject-identifier fields the workflow emits
onto the evidence record, this section MUST be re-scored against
the categories of subjects and personal data so retained.

The inventory owner's pre-bound channel identifier (ticketing
system, chat thread, asset-management board) is a contact endpoint,
not a data-subject record — the notify-inventory-owner step
delivers an evidence reference along that channel and does not
introduce or retain a per-subject record beyond what the operator's
notification surface already holds independently.

## 4. Recipients

Not applicable for personal data. For completeness, the recipients
of the non-personal evidence data the workflow emits are:

- the operator's **evidence store** — primary recipient of the
  dated asset-inventory-delta evidence record (the audit-evident
  artifact NIS2 Art. 21(2)(i) reviewers read);
- the operator's **inventory owner** along their pre-bound
  channel — receives the evidence reference via the
  notify-inventory-owner step;
- the operator's **inventory-source set** (CMDB endpoint, IaC
  state backend, cloud-provider asset APIs, endpoint-management
  agent control plane) as the ingest-side surfaces — receive read
  calls from the ingest-inventory-sources step against the
  operator's pre-bound API surfaces; the read payloads carry the
  reconciliation-window directive against the inventory-source
  set, not any per-subject data.

No external processor is invoked for personal-data processing; the
inventory surfaces named above process operator-bound asset
identifiers, source identifiers, and reconciliation-window
identifiers.

## 5. Retention

Not applicable for personal data. For completeness, the dated
asset-inventory-delta evidence record is retained as the operator's
NIS2 Art. 21(2)(i) evidence under the operator's
regulatory-retention overlay; the retention mechanism is the
evidence-bundle expiry rule shared with the other evidence streams
under `schemas/evidence/bundle.schema.json`. This workflow does not
maintain its own retention schedule.

The inventory-source endpoints the workflow consults at the
ingest-inventory-sources step are governed by the operator's
inventory-source and operational-telemetry retention policies,
which live outside this playbook. The workflow reads them for the
duration of the reconciliation window; it does not extend or
shorten their retention and does not project per-record fields onto
the evidence record.

## 6. Cross-border transfers

**No transfer.** The default configuration runs the
ingest-inventory-sources reads, the reconcile-authoritative-
inventory composition, the compute-delta diff, the classify-delta
taxonomy resolution, the evidence-capture emission, and the
notify dispatch entirely against operator-bound, EU-resident
endpoints (the operator's CMDB, IaC state backend, cloud-provider
asset APIs, endpoint-management agent control plane, evidence
store, and inventory-owner channel). No public-cloud-AI dependency
is wired on the workflow's hot path. Operators MAY swap in a
non-EU-hosted CMDB provider or a non-EU-hosted endpoint-management
agent control plane; doing so is visible on a fork of this
data-flow doc, but is not the default and is not the configuration
the framework ships.

Even where the inventoried services carry personal data governed
by Chapter V on the production-side workflow, the per-window
asset-management discipline this playbook operates does not itself
cross a Chapter V boundary — the workflow's reconciliation and
evidence emission land on operator-bound endpoints, not on a
third-country endpoint.

## 7. Data subject rights

Not applicable — no personal data processed, no data subject to
exercise a right against this workflow. Subject Access Requests,
rectification requests, erasure requests, and objections that bear
on data the inventoried services may have carried during the
reconciliation window are answered against the operator's
production-side workflows that own the subject data; the
asset_management playbook neither creates a new subject record nor
holds a copy of one that a subject could exercise rights against
independently.

The dated asset-inventory-delta evidence record names the
reconciled snapshot by identifier, the delta set by identifier,
the per-delta classification by enumeration, and the inventory
source set by identifier; it carries no subject-identifier fields.

## 8. Outbound personal-data transfer

**No outbound personal-data transfer — N/A.** Per §3, the workflow
processes asset identifiers, inventory-source identifiers, snapshot
identifiers, delta identifiers, configuration-baseline observations,
and attestation records; no category of natural person is the
subject of the processing, so no Chapter V outbound leg exists.

The non-personal-data outbound legs documented elsewhere (evidence-
store publication in §4, inventory-owner notification in §4,
inventory-source read engagement in §4) do not engage Chapter V
because their payloads carry no personal data: the evidence record
names the reconciled snapshot and the per-delta set by identifier,
the notification carries the evidence reference along an
operator-bound channel, and the inventory-source reads carry the
reconciliation-window directive against the operator's pre-bound
API surface.

Cross-reference §6: the workflow-as-a-whole cross-border scoring is
**no transfer** and this §8 carries no contradicting leg.

If a future binding wires a non-EU-hosted CMDB provider, a non-EU-
hosted endpoint-management agent control plane, an evidence-record
field that captures a subject-identifier excerpt from the inventory-
source read, or any other surface that introduces personal data
into the per-window reconciliation discipline, this section MUST be
re-scored against the canonical four-axis shape (destination class,
transfer mechanism, EU-residency posture, data minimisation) and §3
amended in the same change.
