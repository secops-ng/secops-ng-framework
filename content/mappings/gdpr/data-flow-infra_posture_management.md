# GDPR data flow — infra_posture_management

Per-workflow GDPR data-flow entry for the `infra_posture_management`
cookbook playbook (`playbook.infra_posture_management@v1`). Filled in
against [`_data-flow-template.md`](./_data-flow-template.md). Together
the seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/infra_posture_management/`](../../playbooks/infra_posture_management/).

---

## 1. Purpose

The workflow exists to evidence, on every scheduled re-execution, that
the operator's in-scope infrastructure remains in the posture its
declared control catalog requires. On each run it walks the in-scope
infrastructure manifest (cloud accounts, identity boundaries, network
baseline), collects a read-only posture-state snapshot from the
operator's cloud / identity / network read APIs, evaluates each
declared control against that snapshot, and emits one posture-evidence
artifact shaped against `schemas/evidence/posture.schema.json` feeding
the F-WF-06 posture evidence stream. The purpose is bounded to
producing that per-execution posture attestation so an operator can
satisfy continuous infrastructure-posture-management evidence under
NIS2 Art. 21(2)(a); the workflow does not retain configuration
telemetry for analytics, profiling, or model training.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(c) — legal obligation**. Where the operator
is a regulated entity under the **NIS2 Directive** and is obliged to
implement and evidence risk-management measures covering policies on
the security of network and information systems under **NIS2
Art. 21(2)(a)** as transposed nationally, the per-execution
posture-evidence artifact this workflow produces is processed to
discharge that obligation. Operators under sector-specific rules
(DORA ICT risk-management framework obligations for financial
entities) inherit the same primary basis.

Secondary: **GDPR Art. 6(1)(f) — legitimate interests**. An operator
not within scope of a statutory posture-evidence obligation still has
a legitimate interest in continuously evidencing that its
infrastructure configuration remains aligned with its declared
security baseline and detecting configuration drift before it is
exploited; the processing here — reading configuration state and
identity-boundary metadata from the operator's own infrastructure —
is necessary and proportionate to that interest.

The posture state this workflow collects is **resource-shaped by
design** — cloud account configuration, identity-boundary
configuration (role definitions, permission boundaries, group
memberships), and network-baseline configuration — and is never
content data, user behaviour data, or credential-shaped material
(see §3). For operators whose identity boundaries are populated
entirely by non-personal service / workload identities, no personal
data is processed and GDPR does not engage. The sections below score
the worst case: an operator whose identity boundary carries
attributable natural-person principals (named employee or contractor
identities visible inside the IdP / cloud IAM the workflow reads).

Special-category data (Art. 9) is not the target of the workflow and
is not read or persisted; configuration values and identity-boundary
metadata as enumerated in §3 do not carry Art. 9 attributes by design.

## 3. Categories of data subjects and personal data

Data subjects (only where the operator's identity boundary carries
attributable natural-person principals; non-personal service /
workload identities fall outside GDPR scope):

- **Identity-boundary principals** — the employees, contractors, or
  external-collaborator identities that the operator's IdP / cloud
  IAM exposes as members of roles, groups, or permission boundaries
  inside the in-scope infrastructure manifest at `__scope_ref__`.
  Where such a principal is attributable to a natural person, that
  person is the data subject for the workflow.

Categories of personal data:

- **Identifiers** — principal references carried inside the
  identity-boundary configuration the cloud-identity read API
  returns (role names, group memberships, permission-boundary
  attachments). Personal only to the extent the operator's identity
  store maps the referenced principal to a natural person.
- **Configuration metadata** — the per-resource configuration state
  carried by `__posture_state_ref__`: cloud-account configuration
  values, identity-boundary configuration values, and
  network-baseline configuration values read from the operator's
  posture sources. Personal data only when configuration entries
  carry an attributable principal reference (the configuration value
  itself — a CIDR block, a TLS minimum version, a bucket policy — is
  not personal data on its own).
- **Evaluation metadata** — the per-control evaluation result set
  carried by `__control_evaluation_ref__`: one entry per
  (control_ref, scoped-resource-id) pair, with the attestation state
  (effective / partially_effective / ineffective) and the deviation
  list. Personal only where the scoped-resource-id is an
  identity-boundary resource whose principal is attributable.
- **Execution metadata** — the per-execution identifier
  (`__execution_id__`) issued by the compile target's runtime
  (n8n execution id, Temporal workflow run id, LangGraph
  thread/checkpoint id) and the `captured_at` timestamp carried on
  the emitted posture-evidence artifact.

No credential material, factor secret, key plaintext, or session
token is read or persisted; the workflow processes references and
configuration values only, projected through
`telemetry.ocsf.api_activity@v1` for the read calls it issues against
the operator's posture sources.

## 4. Recipients

Internal recipients:

- The **risk-management / posture-governance function** owning the
  Art. 21(2)(a) attestation — the operator's infrastructure-security
  administrators, control owners, and auditors who consume the
  posture-evidence artifacts to evidence baseline alignment and
  detect configuration drift.
- The **metrics layer** consuming `kpi.cloud_posture_coverage@v1` and
  `kri.control_effectiveness@v1` — the recipient is the aggregated
  coverage and residual-exposure counter, not the per-principal or
  per-resource identifier.

External / processor recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **posture sources** the compile target reads at execution time
  (the n8n credential binding, the Temporal worker identity, the
  LangGraph runtime principal, and the operator's cloud-account read
  API / IdP read API / network-baseline read API behind them).
- The **posture-evidence store** receiving the emitted artifact
  (`content/evidence/infra_posture_management/` contributor home; the
  durable store is operator-configured). Destination is
  operator-wired — no default non-EU endpoint.
- The **telemetry / SIEM store** receiving the OCSF API Activity
  records emitted during posture collection.

Each operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production; the
framework does not ship the DPAs, but the data-flow record names the
dependency so a sovereignty review can verify it.

## 5. Retention

The workflow itself is stateless — the durable retention horizon is
the operator-owned posture-evidence store and telemetry store:

- The **posture-evidence artifact** (in-scope manifest reference +
  collected posture-state reference + per-control evaluation result
  set + execution metadata) is written to the operator's
  posture-evidence store and inherits that store's retention policy.
  For continuous-attestation use the operator typically retains the
  per-execution artifacts for the audit window required by the
  governing regulation (NIS2 / DORA evidence-retention obligations),
  enforced by the store's TTL or evidence-pack expiry.
- **OCSF activity records** emitted during posture collection follow
  the operator's telemetry retention policy on the underlying OCSF
  store.

No copy of the collected posture state, identity-boundary metadata,
or evaluation result set is retained by the workflow beyond the
emission span; the durable artifact is the posture-evidence record
above.

## 6. Cross-border transfers

**No transfer.** The workflow is designed to execute end-to-end on
the operator's sovereign-hosted runtime (one of the EU-hostable
reference targets — n8n self-host, Temporal self-host, or LangGraph
self-host on Nebul / OVHcloud / Scaleway / Hetzner) with EU-pinned
processor endpoints for the operator-bound cloud / identity /
network read APIs, the posture-evidence store, and the
telemetry-store dependencies.

The technical controls that hold this scoring (FOUNDATION property #3
— sovereignty):

- The reference compile targets are framework-agnostic and run on the
  operator's own sovereign-hosted runtime; no SecOps-NG-hosted egress
  path exists in the workflow. The orchestrator the operator already
  runs is the execution boundary.
- The posture-collection read paths are operator-bound at compile
  time and target the operator's EU-region cloud accounts, IdP /
  cloud IAM, and network-baseline source directly; the playbook does
  not call a hosted SecOps-NG posture service. No hosted-SaaS
  posture-collection dependency is permitted at the SKELETON layer
  by the sovereign-stack constraint.
- The posture-evidence artifact emits to the operator's
  EU-region-pinned posture-evidence store; no external aggregation
  is invoked.
- No public-cloud-AI endpoint is called during posture collection,
  control evaluation, or emission.

If an operator binds a non-EU cloud read API, a non-EU
posture-evidence store, or a non-EU telemetry processor at compile
time, this scoring breaks — the operator MUST re-score this section
under "transfer under SCCs / BCRs / derogation", name the third
country and the transfer instrument, and document the supplementary
measures (encryption-at-rest with operator-held keys,
pseudonymisation of any attributable principal references before
egress) before the binding goes live. Sovereignty review at compile
time is the gate.

## 7. Data subject rights

- **Access (Art. 15).** Where an identity-boundary principal in the
  collected posture state is attributable to a natural person, a
  Subject Access Request is answered by querying the operator's
  posture-evidence store on the principal reference from §3 and the
  operator's telemetry / OCSF store on the same reference across the
  API Activity records the workflow emitted during collection. The
  workflow introduces no storage location beyond those parents.
- **Rectification (Art. 16).** The workflow does not store
  subject-supplied attributes intended to be updated; the
  identity-boundary configuration and posture state are
  captured-as-observed at execution time, and rectification at the
  subject's request is not operationally meaningful for the
  point-in-time attestation record. A misattributed principal or
  misassigned permission is corrected upstream in the operator's
  identity store or cloud-account configuration, which the next
  execution reflects.
- **Erasure (Art. 17).** The retention hooks in §5 are the
  operational erasure pathway: ageing the posture-evidence
  artifacts and OCSF activity records on the operator's store TTLs
  erases the workflow's copy of the identity-boundary metadata. A
  standalone subject-initiated erasure request flows through the
  posture-evidence store's erasure procedure, which the workflow
  inherits. Where the lawful basis is **Art. 6(1)(c)** legal
  obligation, erasure may be lawfully refused for the statutory
  evidence-retention window.
- **Objection (Art. 21).** Where the lawful basis is **Art. 6(1)(f)**
  legitimate interests, a data subject can object on grounds relating
  to their particular situation; the operational handling is to
  record the objection and route attestation for any
  identity-boundary entries attributable to that principal through
  manual review (the operator's risk-management function reviews
  the relevant evaluation entries off the artifact). Where the basis
  is **Art. 6(1)(c)** legal obligation (most regulated operators),
  Art. 21 objection does not displace the obligation.
- **Automated decision-making (Art. 22).** The workflow produces
  evidence; it does not make a decision with legal or similarly
  significant effects on the subject. Posture collection, control
  evaluation, and artifact emission are observational. Art. 22
  therefore does not apply to the workflow as shipped. If an
  operator wires the emitted posture evidence into an automated
  remediation decision that revokes a principal's access or removes
  a configuration without human review, that downstream decision
  MUST be re-scored where it is defined, not here.

## 8. Outbound personal-data transfer

The workflow has no statutory outbound-notification leg of its own —
posture attestation is an internal Art. 21(2)(a) evidence chain, not
a regulator-submission chain. The outbound legs that carry personal
data outside the workflow's own boundary are all **operator-bound
processor egress under GDPR Art. 28**, scored below against Chapter V
(Art. 44–49). The EU-residency posture is sovereignty-first by
default per Directive 1; the operator's compile-time bindings are
the knobs that can break the scoring.

**Leg A — Posture-source read egress (cloud-account read API, IdP /
cloud IAM read API, network-baseline read API).**

- *Destination class.* Operator-bound processor under GDPR Art. 28 —
  the cloud provider's control plane (acting as both processor for
  the resource-state read and controller for the IAM principal
  records its identity store holds), the operator's IdP, and the
  network-baseline source. The read returns the identity-boundary
  configuration enumerated in §3, which carries attributable
  principal references where the operator's identity store maps a
  principal to a natural person.
- *Transfer mechanism.* **No transfer** under the default sovereign-
  stack posture: an EU-region cloud account, an EU-hosted IdP, an
  EU-hosted network-baseline source. A non-EU control-plane region
  (a US-region AWS / Azure account, an APAC-region GCP project) or
  a US-hosted IdP SaaS MUST be re-scored under **SCCs (Art. 46)**
  with the EU-US Data Privacy Framework cited where the recipient
  is a certified US processor; supplementary measures are
  customer-managed encryption keys held in the EU on the IAM /
  configuration store, pseudonymisation of principal references in
  the posture-evidence artifact before egress, and audit-log region
  pinning to the EU even where the resource sits elsewhere.
- *EU-residency posture (Directive 1).* Default is an EU-region
  control plane and an EU-hosted IdP. The operator's account-
  configuration binding is the boundary that holds the
  identity-boundary read within the EU; sovereignty review at
  compile time refuses non-EU regions on the SKELETON binding. No
  hosted-SaaS posture-collection dependency is permitted at the
  SKELETON layer.
- *Data minimisation on egress (Art. 5(1)(c)).* The read returns
  the identity-boundary configuration scoped to the in-scope
  manifest at `__scope_ref__` — role names, group memberships, and
  permission-boundary attachments that the per-control evaluation
  needs. No bulk export of the operator's full identity graph is
  performed by the workflow; reads are scoped to the controls
  enumerated in `__scope_ref__`.

**Leg B — Posture-evidence store egress (artifact emission).**

- *Destination class.* Operator-bound processor under GDPR Art. 28 —
  the operator's posture-evidence store receiving the emitted
  artifact (in-scope manifest reference, posture-state reference,
  per-control evaluation result set, execution metadata). The
  destination is operator-configured at compile time; the framework
  ships no default endpoint.
- *Transfer mechanism.* **No transfer** when the posture-evidence
  store is EU-region. A non-EU posture-evidence store binding MUST
  be re-scored under **SCCs (Art. 46)**, naming the third country
  and the transfer instrument; supplementary measures are
  encryption-at-rest with operator-held keys on the artifact and
  pseudonymisation of any attributable principal references in the
  evaluation result set before egress.
- *EU-residency posture (Directive 1).* Default is an EU-region
  posture-evidence store. The compile-time sovereignty review is
  the gate; the framework ships no default and the binding is
  operator-bound.
- *Data minimisation on egress (Art. 5(1)(c)).* The artifact
  carries the §3 record exactly: the in-scope manifest reference,
  the posture-state reference, the per-control evaluation result
  set (control_ref, scoped-resource-id, attestation state,
  deviation list), and the execution metadata. Principal
  references appear only where the evaluated scoped-resource-id is
  an identity-boundary resource; no telemetry, log excerpts, or
  configuration-value snapshots beyond the evaluated-control surface
  are emitted into the evidence record.

**Leg C — Telemetry / SIEM store egress (OCSF API Activity records).**

- *Destination class.* Operator-bound processor under GDPR Art. 28 —
  the operator's OCSF / SIEM store receiving the
  `telemetry.ocsf.api_activity@v1` records the workflow emits for
  each read call against the posture sources.
- *Transfer mechanism.* **No transfer** under the default sovereign-
  stack posture: an EU-region OCSF / SIEM endpoint. A non-EU SIEM
  SaaS host MUST be re-scored under **SCCs (Art. 46)** with the
  EU-US Data Privacy Framework cited where the recipient is a
  certified US processor; supplementary measures are
  encryption-at-rest with operator-held keys on the SIEM index and
  pseudonymisation of principal references inside the API Activity
  body before egress.
- *EU-residency posture (Directive 1).* Default is an EU-region
  SIEM endpoint; the compile-time binding is operator-bound and
  the sovereignty review is the gate.
- *Data minimisation on egress (Art. 5(1)(c)).* The API Activity
  record carries the workflow's read-call provenance (the
  compile target's runtime identity acting as the activity actor,
  the targeted posture source, the read scope from `__scope_ref__`,
  the `captured_at` timestamp). The activity actor is the workflow
  runtime principal, not a natural-person identifier; principal
  references appear in the record body only where the read scope
  itself names them and the API Activity event carries the read's
  request shape.

Cross-reference §6: the workflow-as-a-whole cross-border scoring is
**no transfer** under the default sovereign-stack posture, consistent
with all three legs above scoring no-transfer under operator-bound
EU-region endpoints. Any operator re-scoring of a leg here (non-EU
cloud region, non-EU IdP SaaS, non-EU posture-evidence store, non-EU
SIEM) MUST be reflected in §6 in the same change so the two sections
do not disagree.
