# supply_chain_security — cookbook walkthrough

Per-signal supplier-assessment and supply-chain-evidence workflow. The
`playbook.supply_chain_security@v1` CACAO playbook ingests one raw
supply-chain signal (SBOM diff, supplier attestation, upstream
advisory, threat-intel report, or operator report) the operator has
staged from their signal feed, canonicalises the assessment of the
implicated supplier into a closed `verdict / supplier handle /
affected components / signal class` block, and emits one
supply-chain-evidence artifact per execution that the F-CP-03
supply-chain evidence stream consumes alongside the per-execution
dependency snapshots the rest of the cookbook workflows produce.

The regulatory anchor is NIS2 Article 21(2)(d) — supply-chain
security, including the security characteristics of direct suppliers
and service providers, with periodic re-attestation — pinned by the
`nis2:art-21-2-d` mapping entry in
[`content/mappings/nis2/article-21-2-d.yaml`](../../content/mappings/nis2/article-21-2-d.yaml).
The artifact shape is
[`schemas/evidence/supply-chain.schema.json`](../../schemas/evidence/supply-chain.schema.json)
(stream: `supply-chain`).

This workflow is the **per-signal** counterpart to the rest of the
F-CP-03 supply-chain stream. The base F-CP-03 surface emits a
per-execution `dependencies-snapshot.json` from every workflow that
calls an external provider — that surface enumerates the dependency
graph the execution actually resolved. This workflow emits a sibling
supply-chain-evidence artifact keyed on an operator-side signal: it
documents the supplier-side disposition (no impact / watch / confirmed
compromise) and the implicated-component set the signal carried. The
two surfaces share the same `supply-chain.schema.json` and the same
shared emitter; the cross-stream join on `(workflow_id, execution_id)`
lines up the runtime dependency surface with the operator's signal
disposition for the same execution.

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the deterministic
primitives package, the shared supply-chain-evidence emitter, and the
per-target adapter live in each.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/supply_chain_security/
├── README.md                    # workflow-local module tree
├── mappings.yaml                # outbound playbook-mappings overlay
├── playbook.cacao.json          # canonical CACAO v2 source (playbook.supply_chain_security@v1)
└── primitives/
    ├── assess.py                # assess_supplier_signal — assess-supplier-signal
    └── artifact.py              # build_supply_chain_evidence_artifact — emit-supply-chain-evidence

schemas/evidence/supply-chain.schema.json
                                  # per-execution supply-chain-evidence artifact schema (stream: supply-chain)

compilers/_shared/evidence/supply_chain.py
                                  # framework-agnostic shared emitter (deterministic id, atomic write)
```

The CACAO source is canonical. The primitives package is the
deterministic policy the playbook *means*. The three worked examples
are the same playbook compiled into three orchestrator idioms.
Everything else — runtime, signal-feed source, SBOM-correlation /
supplier-attestation lookup, evidence sink — is the operator's data
plane.

The CACAO source ships as JSON
(`content/playbooks/supply_chain_security/playbook.cacao.json`); the
three worked examples each carry a mirror copy at
`examples/{n8n,temporal,langgraph}/supply_chain_security/playbook.cacao.json`
that is byte-identical to the canonical and refreshed by the
per-target `regenerate.sh`.

## 2. CACAO topology and primitives binding

The playbook ships four steps: one `start`, two `action`, one `end`.
Both action steps declare an `x_secops_ng.core_body` reference into
the deterministic primitives package; there are **no absent-body
steps** in this workflow — the CORE wave landed the bindings up-front
in the canonical source rather than via a per-target overlay.

| Step suffix | Step                         | `core_body` binding                                                                              | Status |
|-------------|------------------------------|--------------------------------------------------------------------------------------------------|--------|
| `…000001`   | start                        | edge wiring only — no body                                                                       | n/a    |
| `…000002`   | assess-supplier-signal       | `primitives.assess.assess_supplier_signal`                                                       | bound  |
| `…000003`   | emit-supply-chain-evidence   | `primitives.artifact.build_supply_chain_evidence_artifact`                                       | bound  |
| `…000004`   | end                          | edge wiring only — no body                                                                       | n/a    |

Transitions are deterministic — each state has exactly one
`on_completion` successor, no conditional branching at this layer.
One execution against one raw signal emits exactly one
supply-chain-evidence artifact; the per-component set the signal
carries is folded into the artifact's `dependencies[]` /
`affected_component_set` blocks, not emitted as independent records.

## 3. Deterministic primitives — the contract

The signal-class enum, the verdict vocabulary, the
`provider.<id>@v<n>` supplier-handle regex, the PURL canonicalisation
of the affected component set, the closed `supply-chain-evidence`
shape the schema pins, and the `artifact_id` recipe are **code, not
configuration**. They live in
`content/playbooks/supply_chain_security/primitives/` and in the
shared emitter under `compilers/_shared/evidence/supply_chain.py`.
Operators who need to diverge fork the primitive module; they do not
override it via runtime config.

The two bindings exercised today:

`assess_supplier_signal(signal_class, verdict, affected_supplier_handle, received_at, affected_component_set, signal_id=None, scoring_notes=None) -> AssessmentBlock`
:   The `assess-supplier-signal` step normalises the operator-supplied
    raw supply-chain signal into a closed `assessment` block. The
    closed vocabulary on `signal_class` is `sbom_diff` /
    `supplier_attestation` / `upstream_advisory` / `threat_intel` /
    `operator_report`; the closed vocabulary on `verdict` is
    `no_impact` / `watch` / `confirmed_compromise` (an upstream feed
    may carry an `unknown` signal but the operator-side disposition is
    meant to be acted on). `affected_supplier_handle` is validated
    against the same `provider.<id>@v<n>` regex the F-CP-03 schema
    pins so the handle round-trips into the artifact downstream
    without re-canonicalisation; `affected_component_set` is sorted,
    deduplicated, and PURL-validated. The signal-feed source the
    workflow reads — SBOM-correlation against the operator's
    component inventory, supplier-attestation lookup, verdict
    scoring — is operator-side I/O. This primitive is the
    shape-and-discipline gate at the step boundary; the real policy
    lives in operator-side configuration, not in the framework.

`build_supply_chain_evidence_artifact(workflow_id, execution_id, regulation_refs, control_refs, assessment, dependencies, owner_role, owner_assigned_at, captured_at, source_url, aggregates) -> SupplyChainEvidenceArtifact`
:   The `emit-supply-chain-evidence` step shapes the JSON-native
    supply-chain-evidence record the shared emitter under
    [`compilers/_shared/evidence/supply_chain.py`](../../compilers/_shared/evidence/supply_chain.py)
    serialises. The emitter is the single source of truth for the
    `artifact_id` recipe — SHA-256 of
    `<workflow_id>|<execution_id>|<captured_at>` (UTF-8, no separators
    around the pipes) — per the schema's `artifact_id` contract. The
    primitive enforces the supplier-integrity invariant: the
    `affected_supplier_handle` produced upstream by
    `assess_supplier_signal` MUST reference a supplier whose
    `provider_id` also appears among the declared `dependencies[]` on
    this execution. A signal that points at a supplier the operator
    has never declared as a dependency fails loud here rather than
    producing a silently-orphaned artifact. The primitive
    re-validates `assessment`, `dependencies`, `aggregates`, and the
    owner block so a direct caller cannot bypass the per-step guards.

The `artifact_id` recipe does **not** key on `compile_target` — the
three reference targets re-derive byte-identical bytes from the same
execution context, and byte-parity is asserted across targets. An
operator running more than one target against the same signal emits
the same artifact bytes per target; downstream consumers can join on
`(workflow_id, execution_id)` without a per-target discriminator.

Determinism is the property a regulator can replay against. The
shared emitter is the byte-stable anchor the per-target byte-parity
goldens pin: the three per-target adapters are thin glue, and the
on-disk evidence record re-emits byte-identical bytes on every
regeneration from the same canonical CACAO source and the same
representative context.

> **LM determinism.** Signal-class canonicalisation, verdict
> validation, supplier-handle and PURL regex enforcement, dependency
> normalisation, and supply-chain-evidence shaping are code, not LM.
> The supply_chain_security playbook does not bind any DSPy
> signature — there is no free-text step at this layer. SBOM
> correlation and supplier-attestation lookup are mechanical walks of
> the operator's signal feed and component inventory, not free-text
> reasoning steps. See `docs/FOUNDATION.md` § LLM determinism.

## 4. Per-target hand-off

### 4.1 n8n — operator-edited Set rows + Code-node bindings

`examples/n8n/supply_chain_security/workflow.n8n.json` carries the
CACAO topology as n8n nodes (`manualTrigger`, `set`, `code`, `noOp`),
with node ids preserving the CACAO step ids verbatim. The two bound
CORE steps emit `n8n-nodes-base.code` nodes whose `pythonCode` is the
exact primitive call — e.g.
`from content.playbooks.supply_chain_security.primitives.assess import assess_supplier_signal ; __assessment_ref__ = assess_supplier_signal(...)`.
The Code-node body assumes `PYTHONPATH` on the n8n host resolves
`content.playbooks.supply_chain_security.primitives`; operators who
run n8n in a Python-free container drop a Python-runner Code node
between the Set node and the next step — see
[`examples/n8n/supply_chain_security/README.md`](../../examples/n8n/supply_chain_security/README.md)
under *Per-action wiring notes — CORE bodies*.

The `emit-supply-chain-evidence` step routes the typed context
through the shared evidence emitter; the n8n adapter at
`compilers.n8n.evidence.emit_supply_chain_artifact_n8n` calls
`compilers._shared.evidence.supply_chain.render_supply_chain_artifact`
with the typed context and the operator-supplied evidence directory,
and the emitter writes the deterministic `<artifact_id>.json` to
disk.

### 4.2 Temporal — `@activity.defn` bodies with retry policy

`examples/temporal/supply_chain_security/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action. The two bound activities
import the primitive (and the shared emitter for
`emit-supply-chain-evidence`) and produce the canonical assessment
block / supply-chain-evidence record. There are no absent-body
activities in this workflow.

The committed `workflow.temporal.py` is a generated stub: CORE
primitive calls are inlined into the activity bodies under the
`@activity.defn` decorators, while the workflow lowering itself (the
`@workflow.run` method) still raises `NotImplementedError` pending
the workflow-translator slice — operators wire the activity
scheduling in their worker assembly. Per-activity retry policies are
emitted alongside the activities (`<ACTIVITY>_RETRY_POLICY`) so the
operator can pin them on the `workflow.execute_activity` call sites.

The Temporal evidence adapter at
`compilers.temporal.evidence.emit_supply_chain_artifact_activity` is
the durable surface that exercises the shared emitter under
deterministic execution; replay against the same Temporal event
history re-derives the same `artifact_id`.

### 4.3 LangGraph — `@tool` wrappers + agentic-extension hook

`examples/langgraph/supply_chain_security/state_bindings.py` carries
the `TypedDict` state and the two `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (nodes, edges).
`regenerate.py` is the canonical reference assembly that wires the
spec into a `StateGraph`. The bound tools import the primitive (and
the shared emitter for `emit-supply-chain-evidence`) and update the
typed state; there are no absent-body tools.

LangGraph is the agentic target — the natural seam an operator
extends with an LLM-driven node is *out of band* for this workflow.
Signal canonicalisation, supplier-handle validation, PURL
normalisation, and supply-chain-evidence shaping are mechanical walks
of the operator's signal feed and dependency inventory, not free-text
reasoning steps; adding an agentic hook here would defeat the
determinism the supply-chain-evidence record relies on. The compiler
never embeds an LLM SDK; the framework-wide EU-resident LM endpoint
guard re-applies the check at process startup
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

Span boundaries per target match the rest of the cookbook (workflow
+ activity in Temporal; node + tool in LangGraph; per-node operator
concern in n8n).

The OTLP exporter endpoint is operator-supplied
(`OTEL_EXPORTER_OTLP_ENDPOINT`). The compiler never sets a default
and never imports a vendor SDK; the sovereignty posture asks for an
EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline.

## 6. Replay and audit story

Two replay properties are pinned for supply_chain_security.

**Per-execution deterministic replay** — the shared emitter under
`compilers/_shared/evidence/supply_chain.py` produces a byte-identical
record on every re-emission against the same execution context. The
record `artifact_id` is
`SHA-256(workflow_id|execution_id|captured_at)`. A re-walk of the
same raw signal under the same supplier inventory at the same
`captured_at` anchor re-derives the same assessment block, the same
canonical dependency set, and the same artifact bytes.

**Cross-target byte-parity goldens** — the three committed
worked-example records under
`examples/{n8n,temporal,langgraph}/supply_chain_security/evidence/supply-chain-evidence.json`
are pinned byte-for-byte by the per-target byte-parity goldens at
`tests/examples/supply_chain_security/test_{n8n,temporal,langgraph}_workflow_golden.py`
and
`tests/examples/supply_chain_security/test_{n8n,temporal,langgraph}_supply_chain_evidence.py`.
Each test pins (a) the per-target workflow artefact
(`workflow.n8n.json` / `workflow.temporal.py` / `graph_spec.json` +
`state_bindings.py`), (b) the per-target supply-chain-evidence
record, and (c) the byte-equality of the co-located CACAO mirror
against the canonical source under
`content/playbooks/supply_chain_security/`. Because the `artifact_id`
recipe does not key on `compile_target`, the three per-target
evidence records are byte-identical across targets; if the shared
emitter changes, regenerate the worked examples via the per-target
`regenerate.sh` and commit the diff intentionally; the drift guard
flips green again.

The `captured_at` anchor is part of the `artifact_id` on purpose: a
re-ingest of the same signal at a different wall-clock instant
deliberately produces a *new* artifact, even when the signal is
otherwise identical. That is the audit property — a regulator
reading the artifact series back can see, per supplier, the sequence
of verdict snapshots over time, and a deduplicator never collapses
two snapshots taken at different instants.

## 7. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys, no
  signal-feed credentials, no SBOM-tool credentials, no
  supplier-portal credentials. The signal-feed read endpoints that
  `assess-supplier-signal` reads, the supplier inventory and
  attestation source, and the storage backend for the
  supply-chain-evidence records are operator-bound at runtime against
  environment variables documented per target; the framework ships
  no default endpoint per the sovereign-stack posture.
- **Hosted SBOM or threat-intel dependency.** This playbook
  deliberately ships no default SBOM-correlation integration, no
  default threat-intel feed binding, and no vendor SDK. The signal
  source is operator-supplied — a filesystem-backed signal staging
  area, an EU-hosted intel feed, or whatever signal surface the
  operator already runs. The framework commits to the artifact
  contract, not the upstream signal-feed topology.
- **Deployment topology.** Worker concurrency, retry policies beyond
  the per-activity defaults, persistence backends, n8n hosting, the
  scheduler driving re-execution cadence, LangGraph host process
  model — those are runtime concerns the operator applies in their
  own assembly.
- **Upstream signal generation.** This playbook consumes an
  already-assessed raw signal envelope; it does not run an SBOM
  diff, score a supplier attestation, or fetch an upstream advisory.
  The upstream signal-generation activity is operator-owned and out
  of scope for this workflow.
- **Personal data in signal records.** Operator-side signal records
  may carry supplier handles, component PURLs, and short scoring
  notes; per AGENTS.md §3 supplier handles MUST stay role-shaped
  (`provider.<id>@v<n>`) and scoring notes MUST NOT carry personal
  localparts, contact-shaped supplier references, or
  credential-shaped strings. Personal localparts and
  credential-shaped material are rejected at the schema boundary.
- **Per-deployment YAML.** This playbook ships no separate
  operator-facing `config.yaml`; per-case inputs are the CACAO
  `playbook_variables` block bound at compile time via the standard
  `__double_underscore__` substitution.

## 8. References

- [`content/playbooks/supply_chain_security/playbook.cacao.json`](../../content/playbooks/supply_chain_security/playbook.cacao.json)
  — canonical CACAO source.
- [`content/playbooks/supply_chain_security/README.md`](../../content/playbooks/supply_chain_security/README.md)
  — workflow-local module tree.
- [`schemas/evidence/supply-chain.schema.json`](../../schemas/evidence/supply-chain.schema.json)
  — per-execution supply-chain-evidence artifact schema (stream:
  `supply-chain`).
- [`content/mappings/nis2/article-21-2-d.yaml`](../../content/mappings/nis2/article-21-2-d.yaml)
  — NIS2 Art. 21(2)(d) mapping; entry `nis2:art-21-2-d` is the
  supply-chain-security anchor.
- [`compilers/_shared/evidence/supply_chain.py`](../../compilers/_shared/evidence/supply_chain.py)
  — shared framework-agnostic evidence emitter.
- [`docs/cookbook/contractual_obligations_tracker.md`](contractual_obligations_tracker.md)
  — contract-time counterpart on the same NIS2 Art. 21(2)(d) anchor.
- [`examples/n8n/supply_chain_security/README.md`](../../examples/n8n/supply_chain_security/README.md)
- [`examples/temporal/supply_chain_security/README.md`](../../examples/temporal/supply_chain_security/README.md)
- [`examples/langgraph/supply_chain_security/README.md`](../../examples/langgraph/supply_chain_security/README.md)
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
