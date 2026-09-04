# contractual_obligations_tracker — cookbook walkthrough

Supplier-contract obligation-extraction and review-date workflow. The
`playbook.contractual_obligations_tracker@v1` CACAO playbook reads a
supplier-contract record the operator has staged in their document
store, walks the per-clause obligations the operator has accepted
(security-control commitments, audit-right windows, attestation
cadences, sub-processor-disclosure clauses, breach-notification
cadences), derives a per-obligation review schedule from the
contractual cadence + the operator's review-cadence policy, and emits
one obligation-evidence artifact per execution that the obligation
evidence stream consumes and the auditor bundle (F-WF-09) folds into a
handover.

The regulatory anchor is NIS2 Article 21(2)(d) — supply-chain security,
including the security characteristics of direct suppliers and service
providers, with periodic re-attestation — pinned by the
`nis2:art-21-2-d` mapping entry in
[`content/mappings/nis2/article-21-2-d.yaml`](../../content/mappings/nis2/article-21-2-d.yaml).
The artifact shape is
[`schemas/evidence/contractual-obligations.schema.json`](../../schemas/evidence/contractual-obligations.schema.json)
(stream: `contractual_obligations`).

This workflow is the **contract-time** counterpart to the
[F-CP-03 supply-chain evidence stream](../../ROADMAP.md#f-cp-03--supply-chain-stream),
which is the **execution-time** surface — one artifact per workflow
execution enumerating the external-provider dependencies that
execution resolved against. This workflow emits one artifact per
supplier contract enumerating the obligations the operator has
accepted from that supplier and the per-obligation review schedule.
Together the two streams pin the operator's supply-chain posture
along both axes — what is being called at runtime, and what was
contractually committed at procurement time. The shapes are
intentionally distinct (F-CP-03 keys on `(workflow_id, execution_id)`
and enumerates `provider_id` records; this stream keys on
`contract_id` and enumerates `obligation` records); the cross-stream
join on `provider_id` ↔ `supplier_ref` is pinned in a downstream
sibling card.

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the deterministic
primitives package, the shared obligation-evidence emitter, and the
per-target adapter live in each.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/contractual_obligations_tracker/
├── README.md                    # workflow-local module tree
├── playbook.cacao.json          # canonical CACAO v2 source (playbook.contractual_obligations_tracker@v1)
└── primitives/
    ├── ingest.py                # ingest_contract — ingest-contract
    ├── obligations.py           # extract_obligations — extract-obligations
    ├── schedule.py              # schedule_reviews — schedule-review
    └── artifact.py              # build_obligation_artifact — emit-obligation-evidence

schemas/evidence/contractual-obligations.schema.json
                                  # per-execution obligation-evidence artifact schema (stream: contractual_obligations)

compilers/_shared/evidence/contractual_obligations.py
                                  # framework-agnostic shared emitter (deterministic id, atomic write)
```

The CACAO source is canonical. The primitives package is the
deterministic policy the playbook *means*. The three worked examples
are the same playbook compiled into three orchestrator idioms.
Everything else — runtime, document-store read endpoint, review-policy
source, and the artifact destination — is the operator's data plane.

The CACAO source ships as JSON
(`content/playbooks/contractual_obligations_tracker/playbook.cacao.json`);
the three worked examples each carry a mirror copy at
`examples/{n8n,temporal,langgraph}/contractual_obligations_tracker/playbook.cacao.json`
that is byte-identical to the canonical and refreshed by the
per-target `regenerate.sh`.

## 2. CACAO topology and primitives binding

The playbook ships six steps: one `start`, four `action`, one `end`.
All four action steps declare an `x_secops_ng.core_body` reference
into the deterministic primitives package; there are **no absent-body
steps** in this workflow — the CORE wave landed the bindings up-front
in the canonical source rather than via a per-target overlay.

| Step suffix | Step                       | `core_body` binding                                                            | Status |
|-------------|----------------------------|--------------------------------------------------------------------------------|--------|
| `…000001`   | start                      | edge wiring only — no body                                                     | n/a    |
| `…000002`   | ingest-contract            | `primitives.ingest.ingest_contract`                                            | bound  |
| `…000003`   | extract-obligations        | `primitives.obligations.extract_obligations`                                   | bound  |
| `…000004`   | schedule-review            | `primitives.schedule.schedule_reviews`                                         | bound  |
| `…000005`   | emit-obligation-evidence   | `primitives.artifact.build_obligation_artifact`                                | bound  |
| `…000006`   | end                        | edge wiring only — no body                                                     | n/a    |

Transitions are deterministic — each state has exactly one
`on_completion` successor, no conditional branching at this layer.
One execution against one supplier-contract record emits exactly one
obligation-evidence artifact; the per-clause obligation set is folded
into the artifact's `obligations[]` block, not emitted as independent
records.

## 3. Deterministic primitives — the contract

The contract-record canonicalisation, the per-clause obligation
extraction, the review-state classifier, the closed `contract` /
`obligation` / `review_schedule` shapes the schema pins, and the
`artifact_id` recipe are **code, not configuration**. They live in
`content/playbooks/contractual_obligations_tracker/primitives/` and
in the shared emitter under
`compilers/_shared/evidence/contractual_obligations.py`. Operators who
need to diverge fork the primitive module; they do not override it
via runtime config.

The four bindings exercised today:

`ingest_contract(raw_contract, contract_ref) -> ContractBlock`
:   The `ingest-contract` step canonicalises the operator-supplied raw
    contract record (a JSON-native `{contract_id, supplier_ref,
    effective_at, expires_at?, jurisdiction?}` envelope the operator's
    document-store adapter produced for `contract_ref`) into the
    closed `contract` block the schema pins. Fields are
    NFKC-normalised, dates are validated against the schema's date
    shapes, and the resulting block is the same on every replay. The
    compile target's runtime reads the operator's document store
    upstream — this primitive only normalises the resulting record.
    No network, no clock, no vendor SDK; `contract_ref` is
    operator-side and the framework does not interpret it.

`extract_obligations(raw_obligations) -> Sequence[ObligationEntry]`
:   The `extract-obligations` step canonicalises the operator-supplied
    obligation list (one `{obligation_id, clause_ref, obligation_kind,
    text, cadence}` entry per accepted clause). Entries are
    NFKC-normalised, sorted on `obligation_id`, exact-match duplicates
    collapse, and the cadence is validated against the ISO-8601
    duration grammar. The classifier is intentionally minimal at this
    layer — it returns the closed obligation-kind enum
    (`security_control_commitment` / `audit_right` /
    `attestation_cadence` / `sub_processor_disclosure` /
    `breach_notification_cadence` / `data_localisation` / `other`);
    an EXTEND-schema sibling tightens
    the inner envelopes and lifts `schema_version` to 1.0.0.

`schedule_reviews(obligations, review_policy, captured_at) -> Sequence[ReviewScheduleEntry]`
:   The `schedule-review` step derives one `review_schedule[]` entry
    per obligation, paired one-to-one with the sorted obligation set.
    `next_review_due_at` is computed deterministically from
    `(last_reviewed_at, cadence, operator-policy fallback cadence)`.
    The state classifier reads the relationship between `captured_at`
    and `next_review_due_at`: `current` when the next review is
    outside the `due_soon` window, `due_soon` inside the window,
    `overdue` past the deadline, and `unknown` when no
    `last_reviewed_at` is on file. The `waived` state is
    operator-driven and arrives via the policy's
    `waived_obligation_ids` list. Cadence arithmetic is
    contractual-coarse (months → 30 days, years → 365 days) to avoid
    operator-locale ambiguity; the EXTEND-schema sibling pins a
    richer cadence envelope. No network, no clock — `captured_at` is
    the only time anchor and the operator's review-policy is the
    only fallback source.

`build_obligation_artifact(workflow_id, execution_id, regulation_refs, control_refs, owner, contract, obligations, review_schedule, captured_at, source_url) -> ObligationEvidenceArtifact`
:   The `emit-obligation-evidence` step shapes the JSON-native
    obligation-evidence record the shared emitter under
    [`compilers/_shared/evidence/contractual_obligations.py`](../../compilers/_shared/evidence/contractual_obligations.py)
    serialises. The emitter is the single source of truth for the
    `artifact_id` recipe — SHA-256 of
    `<workflow_id>|<execution_id>|<contract_id>|<captured_at>` (UTF-8,
    no separators around the pipes) — per the schema's `artifact_id`
    contract. The `contract_id` is part of the id by design: this
    stream's natural axis is per-contract (one artifact per supplier
    contract per execution), and a re-ingest of the same contract
    inside the same execution at the same `captured_at` instant
    dedupes at the path level. The primitive re-validates `contract`,
    `obligations`, and `review_schedule` shape so a direct caller
    cannot bypass the per-step guards.

The `artifact_id` recipe keys on `contract_id` (not `compile_target`)
on purpose — this stream's natural unit is the supplier-contract
record, not the compile target. The three reference targets re-derive
the same `artifact_id` from the same `(workflow_id, execution_id,
contract_id, captured_at)` tuple and write byte-identical bytes; the
byte-parity guarantee applies **across targets** at this layer. An
operator running more than one target against the same contract emits
the same artifact bytes per target; downstream consumers can join on
`(contract_id, captured_at)` without a per-target discriminator.

> **LM determinism.** Contract ingestion, per-clause obligation
> extraction, review-schedule derivation, and obligation-evidence
> shaping are code, not LM. The contractual_obligations_tracker
> playbook does not bind any DSPy signature — there is no free-text
> step at this layer. The contract record arrives normalised at the
> ingest boundary; the operator's document-store adapter is
> responsible for any upstream extraction, not this workflow. See
> `docs/FOUNDATION.md` § LLM determinism.

## 4. Per-target hand-off

### 4.1 n8n — operator-edited Set rows + Code-node bindings

`examples/n8n/contractual_obligations_tracker/workflow.n8n.json`
carries the CACAO topology as n8n nodes (`manualTrigger`, `set`,
`code`, `noOp`), with node ids preserving the CACAO step ids
verbatim. The four bound CORE steps emit `n8n-nodes-base.code` nodes
whose `pythonCode` is the exact primitive call — e.g.
`from content.playbooks.contractual_obligations_tracker.primitives.ingest import ingest_contract ; __contract_ref__ = ingest_contract(__raw_contract__, __contract_ref_id__)`.
The Code-node body assumes `PYTHONPATH` on the n8n host resolves
`content.playbooks.contractual_obligations_tracker.primitives`;
operators who run n8n in a Python-free container drop a Python-runner
Code node between the Set node and the next step — see
[`examples/n8n/contractual_obligations_tracker/README.md`](../../examples/n8n/contractual_obligations_tracker/README.md)
under *Per-action wiring notes — CORE bodies*.

The `emit-obligation-evidence` step routes the typed context through
the shared evidence emitter; the n8n adapter calls
`compilers._shared.evidence.contractual_obligations.emit_obligation_artifact`
with the typed context and the operator-supplied evidence directory,
and the emitter writes the deterministic `<artifact_id>.json` to
disk.

n8n is the **no-code** target; the cadence the workflow expects is
the operator's cron / schedule trigger at the front of the imported
workflow. The compiled artefact is a snapshot of intent — the
operator wires the schedule, the document-store credential bindings,
and the evidence directory in their own n8n instance.

### 4.2 Temporal — `@activity.defn` bodies with retry policy

`examples/temporal/contractual_obligations_tracker/workflow.temporal.py`
is a standard Temporal worker module: one `@workflow.defn` class and
one `@activity.defn` function per CACAO action. The four bound
activities import the primitive (and the shared emitter for
`emit-obligation-evidence`) and produce the canonical contract block /
obligation list / review schedule / obligation-evidence record. There
are no absent-body activities in this workflow.

The committed `workflow.temporal.py` is a generated stub: CORE
primitive calls are inlined into the activity bodies under the
`@activity.defn` decorators, while the workflow lowering itself (the
`@workflow.run` method) still raises `NotImplementedError` pending
the workflow-translator slice — operators wire the activity
scheduling in their worker assembly. Per-activity retry policies are
emitted alongside the activities (`<ACTIVITY>_RETRY_POLICY`) so the
operator can pin them on the `workflow.execute_activity` call sites.

The sibling `_audit_mirror.py` carries the `AuditRecord` /
`AuditTrail` types — no `compilers.*` import in the emitted artifact,
so the worker module is a self-contained drop-in. The Temporal
evidence adapter is the durable surface that exercises the shared
emitter under deterministic execution; replay against the same
Temporal event history re-derives the same `artifact_id`.

### 4.3 LangGraph — `@tool` wrappers + agentic-extension hook

`examples/langgraph/contractual_obligations_tracker/state_bindings.py`
carries the `TypedDict` state and the four `@tool`-decorated action
wrappers. `graph_spec.json` carries the target-neutral topology
(nodes, edges). The bound tools import the primitive (and the shared
emitter for `emit-obligation-evidence`) and update the typed state;
there are no absent-body tools.

LangGraph is the agentic target — the natural seam an operator
extends with an LLM-driven node is *out of band* for this workflow.
Contract ingestion, per-clause obligation extraction, review-schedule
derivation, and evidence shaping are mechanical walks of the
operator's contract record and policy, not free-text reasoning steps;
adding an agentic hook here would defeat the determinism the
obligation-evidence record relies on. The compiler never embeds an
LLM SDK; the framework-wide EU-resident LM endpoint guard re-applies
the check at process startup
(`compilers/_shared/lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 5. Observability — OTel + AuditTrail in every target

Every emitted action opens an OpenTelemetry span and appends an
`AuditRecord` to a context-local `AuditTrail` *before* the primitive
call. The mirror runs unconditionally, ahead of any OTLP exporter, so
the audit property holds even when the operator has not configured a
collector — typical for disconnected, sovereign, or air-gapped
deployments.

Span attributes use the shared `secops_ng.*` keyspace and are stable
across the three targets:

| Attribute key                | Carries                                              |
|------------------------------|------------------------------------------------------|
| `secops_ng.playbook.id`      | CACAO playbook id (`playbook--…`).                   |
| `secops_ng.playbook.version` | Content version pinned in the playbook.              |
| `secops_ng.step.id`          | CACAO step id (`action--…`).                         |
| `secops_ng.step.name`        | Human-readable step label.                           |
| `secops_ng.step.type`        | CACAO step type (`action`, `start`, `end`).          |
| `secops_ng.tool.name`        | Emitted tool / activity / Code-node function name.   |
| `secops_ng.compile.target`   | `n8n` / `temporal` / `langgraph` discriminator.      |

Span boundaries per target:

- **n8n** — the compiled workflow is a snapshot of intent; OTel
  instrumentation is a per-node operator concern documented per
  node-id, not a runtime guarantee of the emitted JSON.
- **Temporal** — workflow span (`workflow.<stable_id>`) at workflow
  entry; activity span (`activity.<step_id>`) on every activity body,
  with retries opening a fresh child span per Temporal attempt.
- **LangGraph** — node span (`node.<step_id>`) wrapping every node
  assembled from `graph_spec.json`; tool span (`tool.<step_id>`)
  inside the `@tool` wrapper.

The OTLP exporter endpoint is operator-supplied
(`OTEL_EXPORTER_OTLP_ENDPOINT`). The compiler never sets a default
and never imports a vendor SDK; pointing the exporter at a managed
APM is a downstream choice the operator owns end-to-end. The
sovereignty posture asks for an EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline.

## 6. Replay and audit story

Two replay properties are pinned for contractual_obligations_tracker.

**Per-execution deterministic replay** — the shared emitter under
`compilers/_shared/evidence/contractual_obligations.py` produces a
byte-identical record on every re-emission against the same execution
context. The record `artifact_id` is
`SHA-256(workflow_id|execution_id|contract_id|captured_at)`. A
re-walk of the same contract record under the same review-cadence
policy at the same `captured_at` anchor re-derives the same
`contract` block, the same sorted `obligations[]` set, the same
paired `review_schedule[]`, and the same artifact bytes.

**Cross-target byte-parity goldens** — the three committed worked-
example records under
`examples/{n8n,temporal,langgraph}/contractual_obligations_tracker/evidence/obligation-evidence-record.json`
are pinned byte-for-byte by the per-target byte-parity goldens at
`tests/examples/contractual_obligations_tracker/test_{n8n,temporal,langgraph}_workflow_golden.py`
and
`tests/examples/contractual_obligations_tracker/test_{n8n,temporal,langgraph}_obligation_evidence.py`.
Each test pins (a) the per-target workflow artefact
(`workflow.n8n.json` / `workflow.temporal.py` / `graph_spec.json` +
`state_bindings.py`), (b) the per-target obligation-evidence record,
and (c) the byte-equality of the co-located CACAO mirror against the
canonical source under
`content/playbooks/contractual_obligations_tracker/`. Because the
`artifact_id` recipe does not key on `compile_target`, the three
per-target evidence records are byte-identical across targets; if the
shared emitter changes, regenerate the worked examples via the
per-target `regenerate.sh` and commit the diff intentionally; the
drift guard flips green again.

The `captured_at` anchor is part of the `artifact_id` on purpose: a
re-ingest of the same contract at a different wall-clock instant
deliberately produces a *new* artifact, even when the contract record
is otherwise identical. That is the audit property — a regulator
reading the artifact series back can see, per contract, the sequence
of obligation snapshots and the per-obligation review-state
transitions over time, and a deduplicator never collapses two
snapshots taken at different instants.

## 7. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys, no
  document-store credentials, no supplier-portal credentials. The
  document-store read APIs that `ingest-contract` reads, the
  review-policy source, and the storage backend for the
  obligation-evidence records are operator-bound at runtime against
  environment variables documented per target; the framework ships
  no default endpoint per the sovereign-stack posture.
- **Hosted DMS dependency.** This playbook deliberately ships no
  default document-management-system integration and no vendor SDK.
  The document store is operator-supplied — a filesystem-backed
  contract repository, an EU-hosted document store, or whatever
  reading surface the operator already runs. The framework commits
  to the artifact contract, not the document-store topology.
- **Deployment topology.** Worker concurrency, retry policies beyond
  the per-activity defaults, persistence backends, n8n hosting, the
  scheduler driving the re-execution cadence, LangGraph host process
  model — those are runtime concerns the operator applies in their
  own assembly.
- **Contract drafting and negotiation.** This playbook consumes a
  contract record the operator has already signed and staged in
  their document store; it does not advise on contract terms,
  generate redlines, or evaluate supplier proposals. The upstream
  contract-management activity is operator-owned and out of scope
  for this workflow.
- **Personal data in contract records.** Operator-side contract
  records may carry counterparty entity names, contract ids, and
  jurisdiction codes; per AGENTS.md §3 personal localparts attached
  to individuals on either side MUST stay role-shaped (e.g.
  `supplier-governance@example.org`) or opaque. Personal
  localparts, credential-shaped strings, and raw contract-handling
  secret material are out of scope and rejected at the schema
  boundary.
- **Per-deployment YAML.** This playbook ships no separate
  operator-facing `config.yaml`; per-case inputs are the CACAO
  `playbook_variables` block bound at compile time via the standard
  `__double_underscore__` substitution.

## 8. References

- [`content/playbooks/contractual_obligations_tracker/playbook.cacao.json`](../../content/playbooks/contractual_obligations_tracker/playbook.cacao.json)
  — canonical CACAO source.
- [`content/playbooks/contractual_obligations_tracker/README.md`](../../content/playbooks/contractual_obligations_tracker/README.md)
  — workflow-local module tree.
- [`schemas/evidence/contractual-obligations.schema.json`](../../schemas/evidence/contractual-obligations.schema.json)
  — per-execution obligation-evidence artifact schema (stream:
  `contractual_obligations`).
- [`content/mappings/nis2/article-21-2-d.yaml`](../../content/mappings/nis2/article-21-2-d.yaml)
  — NIS2 Art. 21(2)(d) mapping; entry `nis2:art-21-2-d` is the
  supply-chain-security anchor.
- [`compilers/_shared/evidence/contractual_obligations.py`](../../compilers/_shared/evidence/contractual_obligations.py)
  — shared framework-agnostic evidence emitter.
- [`examples/n8n/contractual_obligations_tracker/README.md`](../../examples/n8n/contractual_obligations_tracker/README.md)
- [`examples/temporal/contractual_obligations_tracker/README.md`](../../examples/temporal/contractual_obligations_tracker/README.md)
- [`examples/langgraph/contractual_obligations_tracker/README.md`](../../examples/langgraph/contractual_obligations_tracker/README.md)
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
