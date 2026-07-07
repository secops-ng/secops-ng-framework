# GDPR data flow — dora_tpr_management

Per-workflow GDPR data-flow entry for the `dora_tpr_management`
playbook (`playbook.dora_tpr_management@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
eight sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/dora_tpr_management/`](../../playbooks/dora_tpr_management/).

---

## 1. Purpose

The workflow exists to operate the DORA Chapter V ICT third-party
risk management contract-lifecycle discipline against every ICT
third-party service provider an EU financial entity contracts with,
producing on each run the audit-evident artifacts the DORA Article
28 register-of-information cadence and the Article 28(8) exit-
strategy discipline consume. On each run against a single provider
handle it composes a pre-contractual risk assessment against the
operator's declared rubric (function criticality, sub-outsourcing
chain, data-location, concentration exposure per Article 28(4)),
verifies the negotiated contract carries the Article 30(2) and 30(3)
closed clause set, emits the Article 28 register-of-information row,
re-scores criticality on the operator's documented periodic-review
cadence with a runtime supply-chain-evidence stream drift join, and
discharges the Article 28(8) exit-strategy attestation on a
documented exit trigger. The purpose is bounded to producing that
per-provider contract-lifecycle evidence so a financial entity can
discharge DORA Chapter V; the workflow does not retain provider or
contract telemetry for analytics, profiling, or model training.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(c) — legal obligation**. Where the operator
is a financial entity under **DORA (Regulation (EU) 2022/2554)** and
is obliged to maintain the Article 28 register of information, run
the Article 28(4) pre-contractual risk assessment, ensure the Article
30(2)/(3) contractual clause set is present, run the Article 28(1)(a)
monitoring cadence, and discharge the Article 28(8) exit-strategy
discipline, the per-execution contract-lifecycle evidence this
workflow produces is processed to discharge that obligation. Operators
also within scope of overlapping sector rules (NIS2 Directive Art.
21(2)(d) supply-chain security, Critical Entities Resilience Directive
(EU) 2022/2557 supply-chain obligations for critical entities) inherit
the same primary basis on the overlap.

Secondary: **GDPR Art. 6(1)(f) — legitimate interests**. An operator
outside statutory DORA scope but running similar ICT third-party
governance against its own supplier estate still has a legitimate
interest in maintaining a register of ICT third-party service
providers, verifying contractual clauses, and running periodic
reviews with a runtime supply-chain-evidence drift join; the
processing here — reading a provider handle, a supported function,
a contract reference, and a runtime supply-chain-evidence artifact
set, and composing the risk assessment, clause check, register row,
periodic review, and exit attestation — is necessary and proportionate
to that interest.

The provider identifiers this workflow resolves are **role-shaped by
design** — an opaque operator-side provider id in `provider.<id>@v<n>`
shape, a function-supported token, a contract-record reference, and
a register-row identifier — and are never an individual personal name
or a credential-shaped string (see §3). For executions invoked against
ICT third-party service providers that are legal entities (the
typical case for financial-entity ICT contracts), no personal data
is processed and GDPR does not engage. The sections below score the
worst case: a contract whose contracting party is a natural person
(a sole trader, an individual freelancer, a named contractor) or
whose named-contact / signatory fields the operator chooses to
ingest are attributable to natural persons.

Special-category data (Art. 9) is not the target of the workflow and
is not read or persisted; provider handles, criticality determinations,
clause statuses, and register-row identifiers as enumerated in §3 do
not carry Art. 9 attributes by design.

## 3. Categories of data subjects and personal data

Data subjects (only where the contracting party or named contact is
attributable to a natural person; ICT third-party contracts with
legal entities fall outside GDPR scope for the contracting-party
fields):

- **The ICT third-party service provider contracting party** — where
  the provider is a sole trader, an individual contractor, or a
  freelancer whose contracting identity is a natural person, the
  natural person on whose behalf the contract was signed. This is
  the central data subject where the provider is not a legal entity.
- **The named contract signatory / point-of-contact** — where the
  operator's contract record carries a signatory name or a named
  contractual contact attributable to a natural person on the
  provider side. Personal only where the operator's document store
  pins such fields and the operator chooses to ingest them; the
  framework processes whatever the operator's record contains.

Categories of personal data:

- **Identifiers** — the provider handle carried by
  `__provider_handle__`, the contract reference carried by
  `__contract_ref__`, the register-row identifier carried by
  `__register_row_id__`, and the exit-attestation identifier
  carried by `__exit_attestation_id__`. Personal only to the extent
  the operator's record maps these references to a natural person.
- **Governance metadata** — the function supported
  (`__function_supported__`), the criticality determination
  (`__criticality_determination__`), the risk-assessment block
  (`__risk_assessment_ref__`), the clause-check block
  (`__clause_check_ref__`), the periodic-review block
  (`__periodic_review_ref__`), and the exit trigger
  (`__exit_trigger__`). This is contract-lifecycle governance
  metadata, not content; it is personal data only when joined to
  an attributable provider signatory.
- **Execution metadata** — the per-execution identifier issued by
  the compile target's runtime (n8n execution id, Temporal workflow
  run id, LangGraph thread/checkpoint id) and the `captured_at`
  timestamp carried on the emitted register row and exit
  attestation.

No credential material, secret, or token plaintext is read or
persisted; the workflow processes provider handles, contract
references, register rows, and OCSF API Activity records only,
projected through `telemetry.ocsf.api_activity@v1`.

## 4. Recipients

Internal recipients:

- The **third-party-risk / vendor-governance function** owning the
  DORA Chapter V discipline — the operator's third-party-risk
  administrators and auditors who consume the register-of-information
  rows, the periodic-review blocks, and the exit-strategy attestations
  to discharge Article 28.
- The **supply-chain-security function** — read-only consumer of the
  register row via the join to the runtime supply-chain-evidence
  stream emitted by `playbook.supply_chain_security@v1`.
- The **metrics layer** consuming forthcoming DORA-third-party KRIs
  (EXTEND-metrics sibling card: `kri.dora_tpr_criticality_drift`,
  `kri.dora_tpr_clause_incomplete`, `kpi.dora_tpr_register_freshness`)
  — the recipient is the aggregated per-criticality-bucket counter,
  not the per-provider identifier.

External / processor recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **contract repository** the compile target reads at execution
  time (a sovereign EU object store, an on-prem contract-management
  system, or a Git-managed contract repository the operator wires
  via `__contract_ref__`). The framework ships no default CLM
  dependency.
- The **register sink** — the operator's evidence store the Article
  28 register-of-information row is published to
  (`content/evidence/dora_tpr_management/` contributor home; the
  durable store is operator-configured). Destination is operator-
  wired — no default non-EU endpoint.
- The **exit-attestation sink** — the operator's evidence store the
  Article 28(8) exit-strategy attestation is published to. Typically
  the same evidence store as the register sink.
- The **runtime supply-chain-evidence store** — read-only for the
  periodic-review drift join; the store binding is operator-wired
  and shared with `playbook.supply_chain_security@v1`.
- The **telemetry / SIEM store** receiving the OCSF API Activity
  records emitted during onboarding assessment, clause check,
  register emission, periodic review, and exit-attestation emission.

Each operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production;
the framework does not ship the DPAs, but the data-flow record names
the dependency so a sovereignty review can verify it.

## 5. Retention

The workflow itself is stateless — the durable retention horizon is
the operator-owned register sink, exit-attestation sink, and
telemetry store:

- The **Article 28 register-of-information row** (provider handle +
  function supported + criticality determination + risk-assessment
  block + clause-check block + execution metadata) is written to the
  operator's register sink and inherits that store's retention
  policy. DORA's supervisory-authority reporting cadence and the
  operator's declared evidence-retention obligation set the floor;
  the operator typically retains per-window register rows for the
  audit window required by DORA Chapter V and any overlapping
  national supervisory-authority direction.
- The **Article 28(8) exit-strategy attestation** is written to the
  operator's exit-attestation sink and inherits that store's
  retention policy. The exit attestation is one of the audit-evident
  artifacts DORA supervisory-authority reviewers consume against a
  terminated ICT third-party service provider engagement; retention
  typically matches the register-row retention plus the operator's
  post-termination audit window.
- **OCSF activity records** emitted during onboarding, clause check,
  register emission, periodic review, and exit-attestation emission
  follow the operator's telemetry retention policy on the underlying
  OCSF store.

No copy of the ingested contract record, the composed risk-assessment
block, or the periodic-review block is retained by the workflow
beyond the emission span; the durable artifacts are the register row
and exit attestation above.

## 6. Cross-border transfers

**No transfer.** The workflow is designed to execute end-to-end on
the operator's sovereign-hosted runtime (one of the EU-hostable
reference targets — n8n self-host, Temporal self-host, or LangGraph
self-host on Nebul / OVHcloud / Scaleway / Hetzner) with EU-pinned
processor endpoints for the operator-bound contract repository,
register sink, exit-attestation sink, runtime supply-chain-evidence
store, and telemetry-store dependencies.

The technical controls that hold this scoring (FOUNDATION property #3
— sovereignty):

- The reference compile targets are framework-agnostic and run on
  the operator's own sovereign-hosted runtime; no SecOps-NG-hosted
  egress path exists in the workflow. The orchestrator the operator
  already runs is the execution boundary.
- The contract read reads from the operator's EU-region contract
  repository directly; the playbook does not call a hosted SecOps-NG
  contract service. Pre-contractual risk assessment, clause-presence
  check, register-row composition, and exit-attestation emission
  are computed in-band on the ingested record.
- The register row emits to the operator's EU-region-pinned register
  sink; the exit attestation emits to the operator's EU-region-pinned
  exit-attestation sink; no external aggregation is invoked.
- No public-cloud-AI endpoint is called during onboarding, clause
  check, register emission, periodic review, or exit-attestation
  emission.

If an operator binds a non-EU contract repository, a non-EU register
sink, a non-EU exit-attestation sink, or a non-EU telemetry
processor at compile time, this scoring breaks — the operator MUST
re-score this section under "transfer under SCCs / BCRs /
derogation", name the third country and the transfer instrument, and
document the supplementary measures (encryption-at-rest with
operator-held keys, pseudonymisation of the provider reference and
any natural-person signatory handle before egress) before the
binding goes live. Sovereignty review at compile time is the gate.

## 7. Data subject rights

- **Access (Art. 15).** Where the provider contracting party or
  named signatory is attributable to a natural person, a Subject
  Access Request is answered by querying the operator's register
  sink on the provider handle from §3, the exit-attestation sink on
  the same handle, and the operator's telemetry / OCSF store on the
  same handle across the activity records the workflow emitted. The
  workflow introduces no storage location beyond those parents.
- **Rectification (Art. 16).** The workflow does not store
  subject-supplied attributes intended to be updated; the contract
  record is captured-as-observed at ingest time, and rectification
  at the subject's request is not operationally meaningful for the
  point-in-time register-row or exit-attestation record. A
  misattributed provider handle is corrected upstream in the
  operator's contract repository, which the next execution reflects.
- **Erasure (Art. 17).** The retention hooks in §5 are the
  operational erasure pathway: ageing the register rows,
  exit-attestation records, and OCSF activity records on the
  operator's store TTLs erases the workflow's copy of the metadata.
  A standalone subject-initiated erasure request flows through the
  register-sink and exit-attestation-sink erasure procedures, which
  the workflow inherits. Where the lawful basis is **Art. 6(1)(c)**
  legal obligation (DORA Chapter V evidence-retention), erasure may
  be lawfully refused for the statutory evidence-retention window.
- **Objection (Art. 21).** Where the lawful basis is **Art. 6(1)(f)**
  legitimate interests, a data subject can object on grounds
  relating to their particular situation; the operational handling
  is to record the objection and route the periodic review and
  register-row emission for that provider through manual review.
  Where the basis is **Art. 6(1)(c)** legal obligation (financial
  entities under DORA), Art. 21 objection does not displace the
  obligation.
- **Automated decision-making (Art. 22).** The workflow produces
  evidence and re-scored criticality; it does not make a decision
  with legal or similarly significant effects on the subject.
  Onboarding assessment, clause check, register emission, periodic
  review, and exit-attestation emission are observational. Exit is
  never auto-invoked: the exit_assessment step fires only on a
  documented operator-invoked exit trigger, with the human decision
  upstream of the workflow. Art. 22 therefore does not apply to the
  workflow as shipped. If an operator wires the emitted register
  row or the criticality re-score into an automated
  supplier-termination decision that ends a contracting relationship
  without human review, that downstream decision MUST be re-scored
  where it is defined, not here.

## 8. Outbound personal-data transfer

The workflow has three classes of outbound leg that carry personal
data outside the operator's contract-record source. Each is scored
below against GDPR Chapter V (Art. 44–49); the EU-residency posture
is sovereignty-first by default per Directive 1, and the operator's
compile-time bindings are the knobs that can break the scoring. The
contract repository named in §4 is an inbound read — the workflow
reads contract records from it, not pushes to it — and is not scored
here. The §6 cross-border scoring as a whole is `no transfer` under
the default sovereign-stack posture — consistent with all three legs
below — and any operator re-scoring of a leg here MUST be reflected
in §6 in the same change so the two sections do not disagree.

**Leg A — Article 28 register-of-information row emission to the
operator-bound register sink.**

- *Destination class.* Operator-bound processor under GDPR Art. 28
  — the register sink the operator wires at compile time (a
  sovereign EU object store, an on-prem evidence-pack archive, or
  a Git-managed evidence repository the operator's third-party-risk
  function consumes). The provider itself is not a recipient of the
  register row; the row lands inside the operator's audit-evidence
  surface only.
- *Transfer mechanism.* **No transfer** under the default binding:
  the framework ships no default non-EU endpoint and no
  vendor-bundled register-sink dependency, and the reference
  compile targets (n8n / Temporal / LangGraph self-host on Nebul /
  OVHcloud / Scaleway / Hetzner) terminate the emission inside the
  EU/EEA on the operator's EU-region-pinned register sink. Where
  the operator binds a non-EU register sink, the leg MUST be
  re-scored under Art. 46 SCCs with supplementary measures
  (encryption-at-rest with operator-held keys on the register row
  at rest, pseudonymisation of any natural-person signatory or
  contact handle attached to the row before egress) before the
  binding goes live.
- *EU-residency posture.* Default is EU-region register sink only;
  the operator-bound knob is the compile-time register-sink
  binding. The technical control that holds the posture is that
  the framework ships no default register-sink endpoint and no
  fallback that could route the emission outside the EU; the
  operator's DPA inventory (GDPR Art. 28) is the durable record of
  the processor binding the register emission depends on.
- *Data minimisation on egress.* The register row carries the
  provider handle (`__provider_handle__`), the function supported
  (`__function_supported__`), the criticality determination
  (`__criticality_determination__`), the risk-assessment block
  reference, the clause-check block reference, the per-execution
  identifier, and the `captured_at` timestamp. Where the
  contracting party or named signatory is attributable to a
  natural person (the §3 worst-case path), that handle rides on
  the provider reference field as captured-as-observed; no
  signatory profile, no contract-body free text, and no
  credential material is enriched onto the row.

**Leg B — Article 28(8) exit-strategy attestation emission to the
operator-bound exit-attestation sink.**

- *Destination class.* Operator-bound processor under GDPR Art. 28
  — the exit-attestation sink the operator wires at compile time
  (typically the same evidence store as the register sink but
  bindable independently). The provider is not a recipient of the
  attestation; the record lands inside the operator's audit-evidence
  surface only.
- *Transfer mechanism.* **No transfer** under the default binding:
  the framework ships no default non-EU endpoint. Where the
  operator binds a non-EU exit-attestation sink, the leg MUST be
  re-scored under Art. 46 SCCs with supplementary measures
  (encryption-at-rest with operator-held keys on the attestation
  at rest, pseudonymisation of any natural-person signatory or
  contact handle before egress) before the binding goes live.
- *EU-residency posture.* Default is EU-region exit-attestation
  sink only; the operator-bound knob is the compile-time
  exit-attestation-sink binding. The technical control that holds
  the posture is that the framework ships no default sink endpoint
  and no fallback that could route the emission outside the EU.
- *Data minimisation on egress.* The attestation carries the
  provider handle, the register-row identifier, the risk-assessment
  block reference, the clause-check block reference, the
  periodic-review block reference, the exit trigger
  (`__exit_trigger__`), the per-execution identifier, and the
  `captured_at` timestamp. No signatory profile, no contract-body
  free text, and no credential material is enriched onto the
  attestation.

**Leg C — OCSF API Activity emission to the operator-bound telemetry
/ SIEM store.**

- *Destination class.* Operator-bound processor under GDPR Art. 28
  — the operator's SIEM / OCSF telemetry store. The workflow
  emits `telemetry.ocsf.api_activity@v1` records covering the
  onboarding, clause-check, register-emission, periodic-review,
  and exit-attestation steps; the store binding the operator
  wires at compile time receives the events.
- *Transfer mechanism.* **No transfer** under the default binding:
  the operator's EU-region-pinned SIEM / OCSF store is EU-resident
  and the emission terminates inside the EU/EEA. Where the
  operator binds a non-EU SIEM / telemetry processor, the leg
  MUST be re-scored under Art. 46 SCCs with supplementary
  measures (encryption-at-rest with operator-held keys on the
  OCSF payload at rest, pseudonymisation of the provider handle
  and any natural-person signatory handle on the API Activity
  record before egress) before the binding goes live.
- *EU-residency posture.* Default is EU-region telemetry store
  only; the operator-bound knob is the compile-time SIEM / OCSF
  processor binding. The technical control that holds the posture
  is that the framework ships no default telemetry processor and
  no fallback that could route OCSF emissions outside the EU.
- *Data minimisation on egress.* The API Activity record carries
  the contract-repository endpoint, the provider handle, the
  per-execution identifier, the actor (the workflow's runtime
  identity), and the activity outcome (onboarding succeeded /
  failed, clause check present / present_with_deviation / absent,
  register emission succeeded / failed, periodic review succeeded
  / failed, exit attestation succeeded / failed). The
  risk-assessment block itself, the per-clause deviation notes,
  and the periodic-review re-score deltas are not enriched onto
  the OCSF record; the durable copies of those live on the
  register row and exit attestation in Legs A and B, not on the
  telemetry record.
