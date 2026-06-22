# GDPR data flow — iam_auditor

Per-workflow GDPR data-flow entry for the `iam_auditor` cookbook
playbook (`playbook.iam_auditor@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/iam_auditor/`](../../playbooks/iam_auditor/).

---

## 1. Purpose

The workflow exists to demonstrate, on every execution of a compiled
workflow, that the running form was invoked by a known caller and
that the caller held only the capabilities it was supposed to
exercise on that run. On each run it resolves the caller identity
that invoked the workflow, walks the closed capability list
(verb.resource tokens) that identity held at execution time, and
emits one access-evidence artifact against
`schemas/evidence/access.schema.json` feeding the F-CP-07 access
evidence stream. The purpose is bounded to producing that
per-execution capability-inventory evidence so an operator can
satisfy continuous access-control attestation under NIS2
Art. 21(2)(i); the workflow does not retain identity telemetry for
analytics, profiling, or model training.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(c) — legal obligation**. Where the operator
is a regulated entity under the **NIS2 Directive** and is obliged to
implement and evidence access-control policies, asset management, and
human-resources security under **NIS2 Art. 21(2)(i)** as transposed
nationally, the per-execution capability-inventory evidence this
workflow produces is processed to discharge that obligation.
Operators under sector-specific rules (DORA Art. 9 ICT-protection and
access-management obligations for financial entities) inherit the
same primary basis.

Secondary: **GDPR Art. 6(1)(f) — legitimate interests**. An operator
not within scope of a statutory access-evidence obligation still has
a legitimate interest in continuously evidencing least-privilege and
detecting capability drift on the identities that invoke its
automated workflows; the processing here — resolving the caller
identity and enumerating its capability list — is necessary and
proportionate to that interest.

The caller identity this workflow resolves is **role-shaped by
design** — a service-account name, a workflow-runtime principal id,
or an automation role — and is never an individual personal name or a
credential-shaped string (see §3). For executions invoked by a
non-personal service or workload identity, no personal data is
processed and GDPR does not engage. The sections below score the
worst case: an operator whose runtime principal is attributable to a
natural person (an individual workload-identity owner, a named
automation account).

Special-category data (Art. 9) is not the target of the workflow and
is not read or persisted; capability tokens and identity references
as enumerated in §3 do not carry Art. 9 attributes by design.

## 3. Categories of data subjects and personal data

Data subjects (only where the runtime principal is attributable to a
natural person; non-personal service/workload identities fall outside
GDPR scope):

- **The caller-identity owner** — the employee, contractor, or
  workload-identity owner to whom the role-shaped caller principal
  resolved by `enumerate-identities` is attributable, where such
  attribution exists. This is the central data subject for the
  workflow.

Categories of personal data:

- **Identifiers** — the role-shaped caller principal reference
  carried by `__caller_identity_ref__` (service-account name,
  workflow-runtime principal id, automation role). Personal only to
  the extent the operator's identity store maps that principal to a
  natural person.
- **Capability metadata** — the closed capability list carried by
  `__capabilities_ref__`: verb.resource tokens the caller held at
  execution time. This is authorisation metadata, not content; it is
  personal data only when joined to an attributable principal.
- **Execution metadata** — the per-execution identifier
  (`__execution_id__`) issued by the compile target's runtime
  (n8n execution id, Temporal workflow run id, LangGraph
  thread/checkpoint id) and the `captured_at` timestamp carried on
  the emitted access-evidence artifact.

No credential material, factor secret, or token plaintext is read or
persisted; the workflow processes references and verb.resource tokens
only, projected through `telemetry.ocsf.authentication@v1`,
`telemetry.ocsf.account_change@v1`, and
`telemetry.ocsf.api_activity@v1`.

## 4. Recipients

Internal recipients:

- The **access-governance / IAM-review function** owning the
  capability-inventory attestation — the operator's IAM
  administrators and auditors who consume the access-evidence
  artifacts to evidence least-privilege and detect capability drift.
- The **metrics layer** consuming `kpi.cloud_posture_coverage@v1` —
  the recipient is the aggregated coverage counter, not the
  per-principal identifier.

External / processor recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **identity / capability source** the compile target reads at
  execution time (the n8n credential binding, the Temporal worker
  identity, the LangGraph runtime principal, and the operator's
  IdP / cloud IAM that owns the capability grants).
- The **access-evidence store** receiving the emitted artifact
  (`content/evidence/access/` contributor home; the durable store is
  operator-configured). Destination is operator-wired — no default
  non-EU endpoint.
- The **telemetry / SIEM store** receiving the OCSF Authentication,
  Account Change, and API Activity records emitted during
  enumeration.

Each operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production; the
framework does not ship the DPAs, but the data-flow record names the
dependency so a sovereignty review can verify it.

## 5. Retention

The workflow itself is stateless — the durable retention horizon is
the operator-owned access-evidence store and telemetry store:

- The **access-evidence artifact** (caller-identity reference +
  capability list + execution metadata) is written to the operator's
  access evidence store and inherits that store's retention policy.
  For continuous-attestation use the operator typically retains the
  per-execution artifacts for the audit window required by the
  governing regulation (NIS2 / DORA evidence-retention obligations),
  enforced by the store's TTL or evidence-pack expiry.
- **OCSF activity records** emitted during enumeration follow the
  operator's telemetry retention policy on the underlying OCSF store.

No copy of the resolved identity reference or capability list is
retained by the workflow beyond the emission span; the durable
artifact is the access-evidence record above.

## 6. Cross-border transfers

**No transfer.** The workflow is designed to execute end-to-end on
the operator's sovereign-hosted runtime (one of the EU-hostable
reference targets — n8n self-host, Temporal self-host, or LangGraph
self-host on Nebul / OVHcloud / Scaleway / Hetzner) with EU-pinned
processor endpoints for the operator-bound identity/capability source,
access-evidence store, and telemetry-store dependencies.

The technical controls that hold this scoring (FOUNDATION property #3
— sovereignty):

- The reference compile targets are framework-agnostic and run on the
  operator's own sovereign-hosted runtime; no SecOps-NG-hosted egress
  path exists in the workflow. The orchestrator the operator already
  runs is the execution boundary.
- The caller-identity resolution and capability enumeration are
  operator-bound at compile time and target the operator's EU-region
  IdP / cloud IAM directly; the playbook does not call a hosted
  SecOps-NG identity service.
- The access-evidence artifact emits to the operator's
  EU-region-pinned access-evidence store; no external aggregation is
  invoked.
- No public-cloud-AI endpoint is called during enumeration or
  emission.

If an operator binds a non-EU identity source, a non-EU
access-evidence store, or a non-EU telemetry processor at compile
time, this scoring breaks — the operator MUST re-score this section
under "transfer under SCCs / BCRs / derogation", name the third
country and the transfer instrument, and document the supplementary
measures (encryption-at-rest with operator-held keys,
pseudonymisation of the principal reference before egress) before the
binding goes live. Sovereignty review at compile time is the gate.

## 7. Data subject rights

- **Access (Art. 15).** Where the caller principal is attributable to
  a natural person, a Subject Access Request is answered by querying
  the operator's access-evidence store on the principal reference
  from §3 and the operator's telemetry / OCSF store on the same
  reference across the activity records the workflow emitted. The
  workflow introduces no storage location beyond those parents.
- **Rectification (Art. 16).** The workflow does not store
  subject-supplied attributes intended to be updated; the caller
  reference and capability list are captured-as-observed at execution
  time, and rectification at the subject's request is not
  operationally meaningful for the point-in-time attestation record.
  A misattributed principal is corrected upstream in the operator's
  identity store, which the next execution reflects.
- **Erasure (Art. 17).** The retention hooks in §5 are the
  operational erasure pathway: ageing the access-evidence artifacts
  and OCSF activity records on the operator's store TTLs erases the
  workflow's copy of the metadata. A standalone subject-initiated
  erasure request flows through the access-evidence store's erasure
  procedure, which the workflow inherits. Where the lawful basis is
  **Art. 6(1)(c)** legal obligation, erasure may be lawfully refused
  for the statutory evidence-retention window.
- **Objection (Art. 21).** Where the lawful basis is **Art. 6(1)(f)**
  legitimate interests, a data subject can object on grounds relating
  to their particular situation; the operational handling is to
  record the objection and route attestation for that principal
  through manual review. Where the basis is **Art. 6(1)(c)** legal
  obligation (most regulated operators), Art. 21 objection does not
  displace the obligation.
- **Automated decision-making (Art. 22).** The workflow produces
  evidence; it does not make a decision with legal or similarly
  significant effects on the subject. Capability inventory and
  artifact emission are observational. Art. 22 therefore does not
  apply to the workflow as shipped. If an operator wires the
  emitted access evidence into an automated access-revocation
  decision that locks the principal out without human review, that
  downstream decision MUST be re-scored where it is defined, not
  here.

## 8. Outbound personal-data transfer

The workflow has three classes of outbound leg that carry personal
data outside the runtime's own process boundary into operator-bound
processors. Each is scored below against GDPR Chapter V
(Art. 44–49); the EU-residency posture is sovereignty-first by
default per Directive 1, and the operator's compile-time bindings
are the knobs that can break the scoring.

**Leg A — Identity / capability source (operator-bound IdP, cloud
IAM, or sovereign directory) read.**

- *Destination class.* Processor under GDPR Art. 28 — the
  operator's IdP, cloud IAM, or sovereign directory whose caller
  identity and capability surface the workflow enumerates. The
  framework ships no default endpoint; the binding is
  operator-supplied through compile-time variables.
- *Transfer mechanism.* **No transfer.** The default sovereign-stack
  posture pins the identity source to an EU-region tenant
  (Entra EU geo, AWS IAM Identity Center in an EU region, an
  on-premises sovereign directory). The technical control that
  holds this is the operator's compile-time region pin on the
  identity-source binding; sovereignty review at compile time
  refuses any non-EU endpoint.
- *EU-residency posture.* Default is an EU-resident identity
  source under an Art. 28 DPA. A non-EU binding (a US-region
  IdP tenant where the operator's directory is hosted) MUST be
  re-scored under Art. 46 SCCs with supplementary measures
  (encryption-at-rest with operator-held keys, pseudonymisation
  of the principal reference before egress) before the binding
  goes live; a derogation under Art. 49 is not a default
  posture for a recurring attestation workflow.
- *Data minimisation on egress.* The enumeration carries only the
  caller-identity reference and the capability scope the
  attestation requires; authentication factor secrets, session
  tokens, and refresh-token plaintext are never read into the
  workflow. The capability list is captured-as-observed without
  enriching with HR-record fields.

**Leg B — Access-evidence store write (operator-bound durable
store for the emitted attestation artifact).**

- *Destination class.* Processor under GDPR Art. 28 — the
  operator's access-evidence store
  (`content/evidence/access/` contributor home; the durable
  store is operator-configured). No default endpoint ships with
  the framework.
- *Transfer mechanism.* **No transfer.** The default
  sovereign-stack posture pins the access-evidence store to an
  EU-region object store or sovereign archive. The technical
  control is the operator's compile-time region pin on the
  access-evidence-store binding.
- *EU-residency posture.* Default is an EU-resident store under
  an Art. 28 DPA. A non-EU binding MUST be re-scored under
  Art. 46 SCCs with supplementary measures (encryption-at-rest
  with operator-held keys, pseudonymisation of the principal
  reference before egress) before the binding goes live.
- *Data minimisation on egress.* The artifact carries the
  caller-identity reference, the capability list, and the
  execution metadata enumerated in §3; no analytics-only
  projection is emitted to a separate store independent of the
  evidence artifact.

**Leg C — Telemetry / SIEM store write (OCSF Authentication,
Account Change, and API Activity records emitted during
enumeration).**

- *Destination class.* Processor under GDPR Art. 28 — the
  operator's telemetry / SIEM store. No default endpoint ships
  with the framework.
- *Transfer mechanism.* **No transfer.** The default
  sovereign-stack posture pins the telemetry store to an
  EU-region SIEM or sovereign log-archive. The technical control
  is the operator's compile-time region pin on the
  telemetry-store binding.
- *EU-residency posture.* Default is an EU-resident telemetry
  store under an Art. 28 DPA. A non-EU binding MUST be re-scored
  under Art. 46 SCCs with supplementary measures (encryption-at-
  rest with operator-held keys, pseudonymisation of the
  principal reference before egress) before the binding goes
  live.
- *Data minimisation on egress.* OCSF activity records carry the
  principal reference and the action metadata as enumerated in
  §3; authentication factor secrets and token plaintext are
  never written.

The §6 cross-border scoring as a whole is **no transfer** —
consistent with all three legs above scoring no-transfer under the
default sovereign-stack posture. Any operator re-scoring of a leg
here MUST be reflected in §6 in the same change so the two
sections do not disagree.
