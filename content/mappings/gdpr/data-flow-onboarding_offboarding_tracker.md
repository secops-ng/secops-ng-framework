# GDPR data flow — onboarding_offboarding_tracker

Per-workflow GDPR data-flow entry for the
`onboarding_offboarding_tracker` cookbook playbook
(`playbook.onboarding_offboarding_tracker@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/onboarding_offboarding_tracker/`](../../playbooks/onboarding_offboarding_tracker/).

---

## 1. Purpose

The workflow exists to demonstrate, on every joiner / mover / leaver
lifecycle event against a role-shaped runtime principal, that the
declared capability delta was applied to the operator's identity
source and confirmed on the principal's downstream capability
surface. On each run it ingests one operator-supplied lifecycle event
from the operator's identity source, resolves the principal handle,
applies the declared capability delta (grant on join, adjust on move,
revoke on leave), confirms by re-reading the closed capability list
that the delta landed, and emits one access-evidence artifact against
`schemas/evidence/access.schema.json` feeding the F-CP-07 access
evidence stream. The purpose is bounded to producing that
per-lifecycle-event grant/revoke-confirmation evidence so an operator
can satisfy joiner-mover-leaver attestation under NIS2 Art. 21(2)(i);
the workflow does not retain identity telemetry for analytics,
profiling, or model training.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(c) — legal obligation**. Where the operator
is a regulated entity under the **NIS2 Directive** and is obliged to
implement and evidence human-resources security, access-control
policies, and asset management — including joiner-mover-leaver
evidence and privileged-access review cadence — under **NIS2
Art. 21(2)(i)** as transposed nationally, the per-lifecycle-event
grant/revoke-confirmation evidence this workflow produces is
processed to discharge that obligation. Operators under
sector-specific rules (DORA Art. 9 ICT-protection and
access-management obligations for financial entities) inherit the
same primary basis.

Secondary: **GDPR Art. 6(1)(f) — legitimate interests**. An operator
not within scope of a statutory joiner-mover-leaver evidence
obligation still has a legitimate interest in continuously evidencing
that capability grants and revocations against runtime principals
land as declared and that no grant or revocation drifts silently
between intent and effect; the processing here — ingesting one
lifecycle event, resolving the principal, applying the delta, and
confirming the closed capability list — is necessary and
proportionate to that interest.

The principal handle this workflow resolves is **role-shaped by
design** — a service-account name, a workflow-runtime principal id,
or an automation role — and is never an individual personal name or a
credential-shaped string (see §3). For executions invoked against a
non-personal service or workload identity, no personal data is
processed and GDPR does not engage. The sections below score the
worst case: a lifecycle event whose principal is attributable to a
natural person (an individual workload-identity owner, a named
automation account, a sole-trader operator).

Special-category data (Art. 9) is not the target of the workflow and
is not read or persisted; the lifecycle-event record, the principal
reference, the declared capability delta, and the confirmed capability
list as enumerated in §3 do not carry Art. 9 attributes by design.

## 3. Categories of data subjects and personal data

Data subjects (only where the runtime principal is attributable to a
natural person; non-personal service/workload identities fall outside
GDPR scope):

- **The principal owner** — the employee, freelancer, contractor, or
  workload-identity owner to whom the role-shaped principal resolved
  by `resolve-identity` is attributable, where such attribution
  exists. This is the central data subject for the workflow.

Categories of personal data:

- **Identifiers** — the role-shaped principal reference carried by
  `__resolved_identity_ref__` (service-account name, workflow-runtime
  principal id, automation role). Personal only to the extent the
  operator's identity store maps that principal to a natural person.
- **Lifecycle-event metadata** — the `event_kind`
  (joiner / mover / leaver), the declared capability delta
  (`add_set` and `remove_set` of `verb.resource` tokens), and the
  `effective_at` timestamp carried by `__lifecycle_event_record_ref__`.
  This is access-control metadata, not content; it is personal data
  only when joined to an attributable principal.
- **Capability metadata** — the closed capability list carried by
  `__confirmation_ref__`: `verb.resource` tokens the principal holds
  after the delta was applied. Authorisation metadata, not content;
  personal only via the attributable-principal join.
- **Execution metadata** — the per-execution identifier
  (`__execution_id__`) issued by the compile target's runtime (n8n
  execution id, Temporal workflow run id, LangGraph thread/checkpoint
  id) and the `captured_at` timestamp carried on the emitted
  access-evidence artifact.

No credential material, factor secret, or token plaintext is read or
persisted; the workflow processes references and `verb.resource`
tokens only, projected through `telemetry.ocsf.account_change@v1`,
`telemetry.ocsf.authentication@v1`, and
`telemetry.ocsf.api_activity@v1`.

## 4. Recipients

Internal recipients:

- The **access-governance / IAM-review function** owning the
  joiner-mover-leaver attestation — the operator's IAM administrators
  and auditors who consume the access-evidence artifacts to evidence
  that grants and revocations land as declared and that no lifecycle
  delta drifts between intent and effect.
- The **metrics layer** consuming the joiner-mover-leaver KRI
  surface — once the EXTEND-metrics sibling lands (no metric_refs are
  pinned at the SKELETON layer). The recipient is the aggregated KRI
  counter, not the per-principal identifier.

External / processor recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **identity source** the compile target reads (ingest) and writes
  (apply-capability-delta) at execution time — the operator's IdP,
  cloud IAM, sovereign directory, or Git-managed role-and-capability
  repository. No hosted IdP / HR-SaaS default; no vendor SDK bundling;
  no default non-EU endpoint.
- The **access-evidence store** receiving the emitted artifact
  (`content/evidence/access/` contributor home; the durable store is
  operator-configured). Destination is operator-wired — no default
  non-EU endpoint.
- The **telemetry / SIEM store** receiving the OCSF Account Change,
  Authentication, and API Activity records emitted during ingest,
  resolution, application, and confirmation.

Each operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production;
the framework does not ship the DPAs, but the data-flow record names
the dependency so a sovereignty review can verify it.

## 5. Retention

The workflow itself is stateless — the durable retention horizon is
the operator-owned identity source, access-evidence store, and
telemetry store:

- The **access-evidence artifact** (resolved-identity reference +
  confirmed capability list + execution metadata) is written to the
  operator's access evidence store and inherits that store's
  retention policy. For continuous-attestation use the operator
  typically retains the per-event artifacts for the audit window
  required by the governing regulation (NIS2 / DORA
  evidence-retention obligations), enforced by the store's TTL or
  evidence-pack expiry.
- **OCSF activity records** emitted during ingest, resolution,
  application, and confirmation follow the operator's telemetry
  retention policy on the underlying OCSF store.
- The **identity-source mutation** (the actual capability grants and
  revocations applied by `apply-capability-delta`) is durable on the
  operator's IdP / cloud IAM and follows that system's retention,
  not the workflow's.

No copy of the lifecycle-event record, the resolved principal, or the
applied capability delta is retained by the workflow beyond the
emission span; the durable artifact is the access-evidence record
above.

## 6. Cross-border transfers

**No transfer.** The workflow is designed to execute end-to-end on
the operator's sovereign-hosted runtime (one of the EU-hostable
reference targets — n8n self-host, Temporal self-host, or LangGraph
self-host on Nebul / OVHcloud / Scaleway / Hetzner) with EU-pinned
processor endpoints for the operator-bound identity source,
access-evidence store, and telemetry-store dependencies.

The technical controls that hold this scoring (FOUNDATION property #3
— sovereignty):

- The reference compile targets are framework-agnostic and run on the
  operator's own sovereign-hosted runtime; no SecOps-NG-hosted egress
  path exists in the workflow. The orchestrator the operator already
  runs is the execution boundary.
- The lifecycle-event ingest, principal resolution, capability-delta
  application, and confirmation read are operator-bound at compile
  time and target the operator's EU-region identity source directly;
  the playbook does not call a hosted SecOps-NG identity service or a
  hosted HR-SaaS.
- The access-evidence artifact emits to the operator's
  EU-region-pinned access-evidence store; no external aggregation is
  invoked.
- No public-cloud-AI endpoint is called during ingest, resolution,
  application, confirmation, or emission.

If an operator binds a non-EU identity source, a non-EU HR-SaaS, a
non-EU access-evidence store, or a non-EU telemetry processor at
compile time, this scoring breaks — the operator MUST re-score this
section under "transfer under SCCs / BCRs / derogation", name the
third country and the transfer instrument, and document the
supplementary measures (encryption-at-rest with operator-held keys,
pseudonymisation of the principal reference before egress) before the
binding goes live. Sovereignty review at compile time is the gate.

## 7. Data subject rights

- **Access (Art. 15).** Where the resolved principal is attributable
  to a natural person, a Subject Access Request is answered by
  querying the operator's access-evidence store on the principal
  reference from §3 and the operator's telemetry / OCSF store on the
  same reference across the activity records the workflow emitted.
  The workflow introduces no storage location beyond those parents.
- **Rectification (Art. 16).** The workflow does not store
  subject-supplied attributes intended to be updated; the
  lifecycle-event record, the principal reference, and the capability
  delta are captured-as-declared by the upstream identity source.
  Rectification at the subject's request is operationally meaningful
  only against the upstream identity source — the next lifecycle
  event reflects the corrected attribution.
- **Erasure (Art. 17).** The retention hooks in §5 are the
  operational erasure pathway: ageing the access-evidence artifacts
  and OCSF activity records on the operator's store TTLs erases the
  workflow's copy of the metadata. A standalone subject-initiated
  erasure request flows through the access-evidence store's erasure
  procedure, which the workflow inherits. Where the lawful basis is
  **Art. 6(1)(c)** legal obligation, erasure may be lawfully refused
  for the statutory evidence-retention window. A leaver lifecycle
  event itself drains the principal's capability surface upstream;
  erasure of the downstream attestation record is a separate flow.
- **Objection (Art. 21).** Where the lawful basis is **Art. 6(1)(f)**
  legitimate interests, a data subject can object on grounds relating
  to their particular situation; the operational handling is to
  record the objection and route lifecycle-event handling for that
  principal through manual review. Where the basis is
  **Art. 6(1)(c)** legal obligation (most regulated operators),
  Art. 21 objection does not displace the obligation.
- **Automated decision-making (Art. 22).** The workflow applies a
  capability delta declared upstream by the operator's identity
  source — it does not autonomously decide what the delta should be.
  The decision lawfulness sits on the upstream lifecycle-event
  authoring path (the operator's HR / access-governance process),
  not on this workflow. Art. 22 therefore does not apply to the
  workflow as shipped. If an operator wires the emitted access
  evidence into an automated downstream decision that locks the
  principal out without human review, that downstream decision MUST
  be re-scored where it is defined, not here.
