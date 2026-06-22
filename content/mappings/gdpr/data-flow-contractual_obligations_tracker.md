# GDPR data flow — contractual_obligations_tracker

Per-workflow GDPR data-flow entry for the
`contractual_obligations_tracker` playbook
(`playbook.contractual_obligations_tracker@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/contractual_obligations_tracker/`](../../playbooks/contractual_obligations_tracker/).

---

## 1. Purpose

The workflow exists to demonstrate, on every execution against a
single supplier-contract reference, that the security obligations the
operator has accepted from that supplier are inventoried, scheduled
for review against the operator's review-cadence policy, and emitted
as a durable per-contract evidence artifact. On each run it ingests
the supplier contract from the operator's document store, extracts
the per-clause obligation set the operator has accepted (security
control commitments, audit-right windows, attestation cadence,
sub-processor disclosure, breach-notification cadence), derives the
per-obligation next-review-due schedule deterministically from the
contractual cadence and the operator's review-policy, and emits one
obligation-evidence artifact against
`schemas/evidence/contractual-obligations.schema.json` feeding the
F-WF-10 contractual-obligations evidence stream. The purpose is
bounded to producing that per-contract obligation-inventory evidence
so an operator can satisfy continuous supplier-attestation under
NIS2 Art. 21(2)(d); the workflow does not retain supplier or
contract telemetry for analytics, profiling, or model training.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(c) — legal obligation**. Where the operator
is a regulated entity under the **NIS2 Directive** and is obliged to
implement and evidence supply-chain security measures —
security-characteristics review of direct suppliers and service
providers, periodic re-attestation — under **NIS2 Art. 21(2)(d)** as
transposed nationally, the per-execution obligation-inventory
evidence this workflow produces is processed to discharge that
obligation. Operators under sector-specific rules (DORA
Art. 28–30 ICT third-party risk management for financial entities,
Critical Entities Resilience Directive (EU) 2022/2557 supply-chain
obligations for critical entities) inherit the same primary basis.

Secondary: **GDPR Art. 6(1)(f) — legitimate interests**. An operator
not within scope of a statutory supply-chain evidence obligation
still has a legitimate interest in continuously evidencing the
security obligations it has accepted from its suppliers and detecting
review-cadence drift on those obligations; the processing here —
reading a supplier-contract record, extracting the obligation set,
and deriving the per-obligation review schedule — is necessary and
proportionate to that interest.

The supplier identifiers this workflow resolves are **role-shaped by
design** — an opaque operator-side supplier id, a supplier-record
URN, or a contract-id token — and are never an individual personal
name or a credential-shaped string (see §3). For executions invoked
against contracts whose contracting party is a legal entity (the
typical case for supplier contracts), no personal data is processed
and GDPR does not engage. The sections below score the worst case:
a contract whose contracting party is a natural person (a sole
trader, an individual freelancer, a named contractor) or whose
named-contact / signatory fields the operator chooses to ingest are
attributable to natural persons.

Special-category data (Art. 9) is not the target of the workflow and
is not read or persisted; supplier-side identifiers, clause
references, and obligation kinds as enumerated in §3 do not carry
Art. 9 attributes by design.

## 3. Categories of data subjects and personal data

Data subjects (only where the contracting party or named contact is
attributable to a natural person; supplier contracts with legal
entities fall outside GDPR scope for the contracting-party fields):

- **The supplier contracting party** — where the supplier is a
  sole trader, an individual contractor, or a freelancer whose
  contracting identity is a natural person, the natural person on
  whose behalf the contract was signed. This is the central data
  subject where the supplier is not a legal entity.
- **The named contract signatory / point-of-contact** — where the
  operator's contract record carries a signatory name or a
  named contractual contact attributable to a natural person on the
  supplier side. Personal only where the operator's document store
  pins such fields and the operator chooses to ingest them; the
  framework processes whatever the operator's record contains.

Categories of personal data:

- **Identifiers** — the contract record reference carried by
  `__contract_record_ref__`, the supplier reference field on the
  ingested contract record, and the contract-id field on the emitted
  obligation-evidence artifact. Personal only to the extent the
  operator's record maps these references to a natural person.
- **Contractual metadata** — the per-clause obligation set carried
  by `__obligation_set_ref__` (clause reference, obligation text,
  obligation kind, contractual cadence) and the per-obligation
  review schedule carried by `__review_schedule_ref__`. This is
  contractual-commitment metadata, not content; it is personal data
  only when joined to an attributable supplier signatory.
- **Execution metadata** — the per-execution identifier
  (`__execution_id__`) issued by the compile target's runtime
  (n8n execution id, Temporal workflow run id, LangGraph
  thread/checkpoint id) and the `captured_at` timestamp carried on
  the emitted obligation-evidence artifact.

No credential material, secret, or token plaintext is read or
persisted; the workflow processes contract records, obligation
references, and OCSF API Activity records only, projected through
`telemetry.ocsf.api_activity@v1`.

## 4. Recipients

Internal recipients:

- The **supply-chain governance / vendor-risk function** owning the
  supplier-attestation programme — the operator's third-party-risk
  administrators and auditors who consume the obligation-evidence
  artifacts to evidence supply-chain security obligations and
  detect review-cadence drift.
- The **metrics layer** consuming forthcoming supplier-attestation
  KRIs (EXTEND-metrics sibling card) — the recipient is the
  aggregated supplier-attestation-staleness counter, not the
  per-supplier identifier.

External / processor recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **supplier-contract document store** the compile target reads
  at execution time (a sovereign EU object store, an on-prem
  document management system, or a Git-managed contract repository
  the operator wires in via the `__contract_ref__` pointer). The
  framework ships no default DMS dependency.
- The **obligation-evidence store** receiving the emitted artifact
  (`content/evidence/contractual_obligations_tracker/` contributor
  home; the durable store is operator-configured). Destination is
  operator-wired — no default non-EU endpoint.
- The **telemetry / SIEM store** receiving the OCSF API Activity
  records emitted during contract ingest and obligation extraction.

Each operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production; the
framework does not ship the DPAs, but the data-flow record names the
dependency so a sovereignty review can verify it.

## 5. Retention

The workflow itself is stateless — the durable retention horizon is
the operator-owned obligation-evidence store and telemetry store:

- The **obligation-evidence artifact** (contract record reference +
  obligation set + per-obligation review schedule + execution
  metadata) is written to the operator's obligation-evidence store
  and inherits that store's retention policy. For continuous
  supplier-attestation use the operator typically retains the
  per-execution artifacts for the audit window required by the
  governing regulation (NIS2 / DORA / CER evidence-retention
  obligations), enforced by the store's TTL or evidence-pack
  expiry.
- **OCSF activity records** emitted during contract ingest follow
  the operator's telemetry retention policy on the underlying OCSF
  store.

No copy of the ingested contract record, the extracted obligation
set, or the review schedule is retained by the workflow beyond the
emission span; the durable artifact is the obligation-evidence
record above.

## 6. Cross-border transfers

**No transfer.** The workflow is designed to execute end-to-end on
the operator's sovereign-hosted runtime (one of the EU-hostable
reference targets — n8n self-host, Temporal self-host, or LangGraph
self-host on Nebul / OVHcloud / Scaleway / Hetzner) with EU-pinned
processor endpoints for the operator-bound document store,
obligation-evidence store, and telemetry-store dependencies.

The technical controls that hold this scoring (FOUNDATION property #3
— sovereignty):

- The reference compile targets are framework-agnostic and run on the
  operator's own sovereign-hosted runtime; no SecOps-NG-hosted egress
  path exists in the workflow. The orchestrator the operator already
  runs is the execution boundary.
- The contract ingest reads from the operator's EU-region document
  store directly; the playbook does not call a hosted SecOps-NG
  document service. Obligation extraction is computed in-band on
  the ingested record — the workflow MUST NOT contact the supplier
  on the extract or schedule steps.
- The obligation-evidence artifact emits to the operator's
  EU-region-pinned obligation-evidence store; no external
  aggregation is invoked.
- No public-cloud-AI endpoint is called during ingest, extraction,
  scheduling, or emission.

If an operator binds a non-EU document store, a non-EU
obligation-evidence store, or a non-EU telemetry processor at
compile time, this scoring breaks — the operator MUST re-score this
section under "transfer under SCCs / BCRs / derogation", name the
third country and the transfer instrument, and document the
supplementary measures (encryption-at-rest with operator-held keys,
pseudonymisation of the supplier reference before egress) before the
binding goes live. Sovereignty review at compile time is the gate.

## 7. Data subject rights

- **Access (Art. 15).** Where the supplier contracting party or named
  signatory is attributable to a natural person, a Subject Access
  Request is answered by querying the operator's obligation-evidence
  store on the supplier reference from §3 and the operator's
  telemetry / OCSF store on the same reference across the activity
  records the workflow emitted. The workflow introduces no storage
  location beyond those parents.
- **Rectification (Art. 16).** The workflow does not store
  subject-supplied attributes intended to be updated; the contract
  record is captured-as-observed at ingest time, and rectification
  at the subject's request is not operationally meaningful for the
  point-in-time obligation-inventory record. A misattributed
  supplier reference is corrected upstream in the operator's
  document store, which the next execution reflects.
- **Erasure (Art. 17).** The retention hooks in §5 are the
  operational erasure pathway: ageing the obligation-evidence
  artifacts and OCSF activity records on the operator's store TTLs
  erases the workflow's copy of the metadata. A standalone
  subject-initiated erasure request flows through the
  obligation-evidence store's erasure procedure, which the workflow
  inherits. Where the lawful basis is **Art. 6(1)(c)** legal
  obligation, erasure may be lawfully refused for the statutory
  evidence-retention window.
- **Objection (Art. 21).** Where the lawful basis is **Art. 6(1)(f)**
  legitimate interests, a data subject can object on grounds relating
  to their particular situation; the operational handling is to
  record the objection and route attestation for that supplier
  through manual review. Where the basis is **Art. 6(1)(c)** legal
  obligation (most regulated operators), Art. 21 objection does not
  displace the obligation.
- **Automated decision-making (Art. 22).** The workflow produces
  evidence; it does not make a decision with legal or similarly
  significant effects on the subject. Obligation inventory, review
  scheduling, and artifact emission are observational. Art. 22
  therefore does not apply to the workflow as shipped. If an operator
  wires the emitted obligation evidence into an automated
  supplier-termination decision that ends a contracting relationship
  without human review, that downstream decision MUST be re-scored
  where it is defined, not here.

## 8. Outbound personal-data transfer

The workflow has two classes of outbound leg that carry personal
data outside the operator's contract-record source. Each is scored
below against GDPR Chapter V (Art. 44–49); the EU-residency posture
is sovereignty-first by default per Directive 1, and the operator's
compile-time bindings are the knobs that can break the scoring. The
supplier-contract document store named in §4 is an inbound read —
the workflow reads contract records from it, not pushes to it — and
is not scored here. The §6 cross-border scoring as a whole is
`no transfer` under the default sovereign-stack posture —
consistent with both legs below — and any operator re-scoring of a
leg here MUST be reflected in §6 in the same change so the two
sections do not disagree.

**Leg A — Obligation-evidence artifact emission to the
operator-bound F-WF-10 contractual-obligations evidence store.**

- *Destination class.* Operator-bound processor under GDPR
  Art. 28 — the obligation-evidence store the operator wires at
  compile time (a sovereign EU object store, an on-prem
  evidence-pack archive, or a Git-managed evidence repository
  the operator's vendor-risk function consumes). The supplier
  itself is not a recipient of the artifact; the artifact lands
  inside the operator's audit-evidence surface only.
- *Transfer mechanism.* **No transfer** under the default
  binding: the framework ships no default non-EU endpoint and
  no vendor-bundled evidence-store dependency, and the
  reference compile targets (n8n / Temporal / LangGraph
  self-host on Nebul / OVHcloud / Scaleway / Hetzner) terminate
  the emission inside the EU/EEA on the operator's
  EU-region-pinned evidence store. Where the operator binds a
  non-EU obligation-evidence store, the leg MUST be re-scored
  under Art. 46 SCCs with supplementary measures
  (encryption-at-rest with operator-held keys on the
  evidence-pack at rest, pseudonymisation of any natural-person
  signatory or contact handle attached to the artifact before
  egress) before the binding goes live.
- *EU-residency posture.* Default is EU-region evidence store
  only; the operator-bound knob is the compile-time F-WF-10
  evidence-store binding. The technical control that holds the
  posture is that the framework ships no default
  evidence-store endpoint and no fallback that could route the
  emission outside the EU; the operator's DPA inventory
  (GDPR Art. 28) is the durable record of the processor
  binding the evidence emission depends on.
- *Data minimisation on egress.* The artifact carries the
  contract record reference (`__contract_record_ref__`), the
  supplier reference, the per-clause obligation set
  (`__obligation_set_ref__`), the per-obligation review schedule
  (`__review_schedule_ref__`), the per-execution identifier
  (`__execution_id__`), and the `captured_at` timestamp. Where
  the contracting party or named signatory is attributable to a
  natural person (the §3 worst-case path), that handle rides on
  the supplier reference field as captured-as-observed; no
  signatory profile, no contract-body free text, and no
  credential material is enriched onto the artifact.

**Leg B — OCSF API Activity emission to the operator-bound
telemetry / SIEM store.**

- *Destination class.* Operator-bound processor under GDPR
  Art. 28 — the operator's SIEM / OCSF telemetry store. The
  workflow emits `telemetry.ocsf.api_activity@v1` records
  covering the contract-record ingest and obligation-extraction
  steps; the store binding the operator wires at compile time
  receives the events.
- *Transfer mechanism.* **No transfer** under the default
  binding: the operator's EU-region-pinned SIEM / OCSF store is
  EU-resident and the emission terminates inside the EU/EEA.
  Where the operator binds a non-EU SIEM / telemetry processor,
  the leg MUST be re-scored under Art. 46 SCCs with
  supplementary measures (encryption-at-rest with operator-held
  keys on the OCSF payload at rest, pseudonymisation of the
  supplier reference and any natural-person signatory handle on
  the API Activity record before egress) before the binding
  goes live.
- *EU-residency posture.* Default is EU-region telemetry store
  only; the operator-bound knob is the compile-time SIEM /
  OCSF processor binding. The technical control that holds the
  posture is that the framework ships no default telemetry
  processor and no fallback that could route OCSF emissions
  outside the EU.
- *Data minimisation on egress.* The API Activity record
  carries the document-store endpoint, the contract record
  reference, the per-execution identifier, the actor (the
  workflow's runtime identity), and the activity outcome
  (ingest succeeded / failed, extract succeeded / failed). The
  obligation set itself, the per-clause obligation text, and
  the review schedule are not enriched onto the OCSF record;
  the durable copy of those lives on the evidence artifact in
  Leg A, not on the telemetry record.
