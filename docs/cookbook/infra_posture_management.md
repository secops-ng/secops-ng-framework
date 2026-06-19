# infra_posture_management — cookbook walkthrough

Continuous infrastructure-posture-management workflow. The
`playbook.infra_posture_management@v1` CACAO playbook fires on a
scheduled cadence: it walks the operator's in-scope infrastructure
manifest, evaluates each declared control against the resulting
posture-state snapshot under the policy version in force at the tick,
and emits one posture-evidence artifact per execution that the
posture evidence stream consumes and the auditor bundle (F-WF-09)
folds into a handover.

The regulatory anchor is NIS2 Article 21(2)(a) — risk-analysis and
information-system-security policies, including periodic
re-assessment with dated ownership — pinned by the `nis2:art-21-2-a`
mapping entry in
[`content/mappings/nis2/article-21-2-a.yaml`](../../content/mappings/nis2/article-21-2-a.yaml).
The artifact shape is
[`schemas/evidence/posture.schema.json`](../../schemas/evidence/posture.schema.json)
(stream: `posture`).

This workflow is the **continuous** variant of the Shipped
[F-WF-02 posture-audit](../../ROADMAP.md#f-wf-02--posture-audit) lane.
F-WF-02 is the per-request audit shape (an operator or auditor
submits a manifest, the workflow walks it once, the report is
returned). This workflow is the scheduled re-execution shape: the
same audit logic feeds a durable evidence series rather than a
one-shot report. The two lanes share the posture-evidence schema;
they differ in cadence (request-driven vs. scheduler-driven) and in
the durability of the artifact series.

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the deterministic
primitives package, the shared posture-evidence emitter, and the
per-target adapter live in each.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/infra_posture_management/
├── README.md                    # workflow-local module tree
├── playbook.cacao.json          # canonical CACAO v2 source (playbook.infra_posture_management@v1)
└── primitives/
    ├── collect.py               # collect_posture_state — collect-posture
    ├── controls.py              # evaluate_controls — evaluate-controls
    └── artifact.py              # build_posture_artifact — emit-posture-evidence

schemas/evidence/posture.schema.json
                                  # per-execution posture-evidence artifact schema (stream: posture)

compilers/_shared/evidence/posture.py
                                  # framework-agnostic shared emitter (deterministic id, atomic write)
```

The CACAO source is canonical. The primitives package is the
deterministic policy the playbook *means*. The three worked examples
are the same playbook compiled into three orchestrator idioms.
Everything else — runtime, cloud-account read endpoint,
identity-provider read endpoint, network-baseline read endpoint, and
the artifact destination — is the operator's data plane.

The CACAO source ships as JSON
(`content/playbooks/infra_posture_management/playbook.cacao.json`);
the three worked examples each carry a mirror copy at
`examples/{n8n,temporal,langgraph}/infra_posture_management/playbook.cacao.json`
that is byte-identical to the canonical and refreshed by the
per-target `regenerate.sh`.

## 2. CACAO topology and primitives binding

The playbook ships five steps: one `start`, three `action`, one `end`.
All three action steps declare an `x_secops_ng.core_body` reference
into the deterministic primitives package; there are **no absent-body
steps** in this workflow — the CORE wave landed the bindings up-front
in the canonical source rather than via a per-target overlay.

| Step suffix | Step                    | `core_body` binding                                                           | Status |
|-------------|-------------------------|-------------------------------------------------------------------------------|--------|
| `…000001`   | start                   | edge wiring only — no body                                                    | n/a    |
| `…000002`   | collect-posture         | `primitives.collect.collect_posture_state`                                    | bound  |
| `…000003`   | evaluate-controls       | `primitives.controls.evaluate_controls`                                       | bound  |
| `…000004`   | emit-posture-evidence   | `primitives.artifact.build_posture_artifact`                                  | bound  |
| `…000005`   | end                     | edge wiring only — no body                                                    | n/a    |

Transitions are deterministic — each state has exactly one
`on_completion` successor, no conditional branching at this layer.
One scheduled execution emits exactly one posture-evidence artifact;
there is no per-resource fan-out at this layer (per-resource
deviation entries are folded into the per-control aggregation that
`evaluate-controls` returns, not emitted as independent records).

## 3. Deterministic primitives — the contract

The posture-snapshot canonicalisation and hash, the per-control
attestation classifier, the closed `posture_state` / `control_evaluation`
shapes the schema pins, and the `artifact_id` recipe are **code, not
configuration**. They live in
`content/playbooks/infra_posture_management/primitives/` and in the
shared emitter under `compilers/_shared/evidence/posture.py`.
Operators who need to diverge fork the primitive module; they do not
override it via runtime config.

The three bindings exercised today:

`collect_posture_state(raw_posture, scope_ref) -> PostureState`
:   The `collect-posture` step canonicalises the operator-supplied raw
    posture-collection snapshot (a JSON-native list of
    `{resource_id, configuration}` entries the operator's collector
    produced over `scope_ref`) into the closed `posture_state` block
    the schema pins. Resources are NFKC-normalised, sorted on
    `resource_id`, exact-match duplicates collapse, and the canonical
    list is SHA-256-hashed into `snapshot_hash` so two replays of the
    same collection walk produce byte-identical bytes. The compile
    target's runtime walks the operator's read APIs upstream — this
    primitive only normalises and hashes the resulting list. No
    network, no clock, no vendor SDK; `scope_ref` is operator-side and
    the framework does not interpret it.

`evaluate_controls(posture_state, controls_policy) -> Sequence[ControlEvaluation]`
:   The `evaluate-controls` step classifies each declared control
    against the collected snapshot under the operator-supplied policy
    (a JSON-native `{controls: {control.<id>@v<n>: {required: {...}}}}`).
    Resources whose configuration matches the baseline exactly
    contribute zero deviations; resources missing any required key or
    carrying a non-matching value contribute one deviation each, and
    the `partially_effective` band falls out of the aggregation when
    *some* in-scope resources match and some do not. Output is sorted
    by `control_ref` so two replays of the same inputs collapse to
    byte-identical bytes. The classifier is intentionally minimal at
    this layer — it returns the SKELETON enum (`effective` /
    `partially_effective` / `ineffective`); the EXTEND-evaluator
    sibling will tighten this against `schemas/attestation_state.json`
    and pin a richer deviation list shape.

`build_posture_artifact(workflow_id, execution_id, compile_target, regulation_refs, control_refs, policy_version, posture_state, control_evaluation, captured_at, evaluated_at, source_url) -> PostureEvidenceArtifact`
:   The `emit-posture-evidence` step shapes the JSON-native
    posture-evidence record the shared emitter under
    [`compilers/_shared/evidence/posture.py`](../../compilers/_shared/evidence/posture.py)
    serialises. The emitter is the single source of truth for the
    `artifact_id` recipe — SHA-256 of
    `<workflow_id>|<execution_id>|<compile_target>|<policy_version.value>`
    (UTF-8, no separators around the pipes) — per the schema's
    `artifact_id` contract. `captured_at` and `evaluated_at` are
    deliberately *not* part of the id so a re-emission of the same
    execution under the same policy version at a different wall-clock
    instant still dedupes at the path level. The primitive re-validates
    `posture_state` and `control_evaluation` shape so a direct caller
    cannot bypass the per-step guards.

The `artifact_id` keys on the `compile_target` discriminator by
design — the three reference targets each produce their own artifact
under their own id, and the byte-parity guarantee applies **per
target** (a regeneration of the same target re-derives byte-identical
bytes), **not across targets**. An operator running more than one
target against the same workflow emits one artifact per target per
execution; downstream consumers join on `(workflow_id, execution_id)`
and treat `compile_target` as a discriminator, not a noise dimension.

> **LM determinism.** Posture canonicalisation, per-control
> classification, and posture-evidence shaping are code, not LM. The
> infra_posture_management playbook does not bind any DSPy signature
> — there is no free-text step at this layer. The cloud-account /
> identity-provider / network-baseline reads are mechanical walks of
> the operator's manifest, not LM judgements. See
> `docs/FOUNDATION.md` § LLM determinism.

## 4. Per-target hand-off

### 4.1 n8n — operator-edited Set rows + Code-node bindings

`examples/n8n/infra_posture_management/workflow.n8n.json` carries the
CACAO topology as n8n nodes (`manualTrigger`, `set`, `code`, `noOp`),
with node ids preserving the CACAO step ids verbatim. The three bound
CORE steps emit `n8n-nodes-base.code` nodes whose `pythonCode` is the
exact primitive call — e.g.
`from content.playbooks.infra_posture_management.primitives.collect import collect_posture_state ; __posture_state_ref__ = collect_posture_state(__raw_posture__, __scope_ref__)`.
The Code-node body assumes `PYTHONPATH` on the n8n host resolves
`content.playbooks.infra_posture_management.primitives`; operators
who run n8n in a Python-free container drop a Python-runner Code node
between the Set node and the next step — see
[`examples/n8n/infra_posture_management/README.md`](../../examples/n8n/infra_posture_management/README.md)
under *Per-action wiring notes — CORE bodies*.

The `emit-posture-evidence` step routes the typed context through the
shared evidence emitter; the n8n adapter calls
`compilers._shared.evidence.posture.emit_posture_artifact` with the
typed context and the operator-supplied evidence directory, and the
emitter writes the deterministic `<artifact_id>.json` to disk.

n8n is the **no-code** target; the continuous re-execution cadence
the workflow expects is the operator's cron / schedule trigger at the
front of the imported workflow. The compiled artefact is a snapshot of
intent — the operator wires the schedule, the credential bindings on
the read APIs, and the evidence directory in their own n8n instance.

### 4.2 Temporal — `@activity.defn` bodies with retry policy

`examples/temporal/infra_posture_management/workflow.temporal.py` is
a standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action. The three bound
activities import the primitive (and the shared emitter for
`emit-posture-evidence`) and produce the canonical posture-state
snapshot / per-control evaluation / posture-evidence record. There
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
Temporal event history re-derives the same `artifact_id`. Temporal is
the natural fit for the continuous shape: the scheduled re-execution
cadence becomes a Temporal Schedule, and the per-tick workflow is
the unit a regulator-facing reviewer reads the artifact series back
against.

### 4.3 LangGraph — `@tool` wrappers + agentic-extension hook

`examples/langgraph/infra_posture_management/state_bindings.py`
carries the `TypedDict` state and the three `@tool`-decorated action
wrappers. `graph_spec.json` carries the target-neutral topology
(nodes, edges). The bound tools import the primitive (and the shared
emitter for `emit-posture-evidence`) and update the typed state; there
are no absent-body tools.

LangGraph is the agentic target — the natural seam an operator
extends with an LLM-driven node is *out of band* for this workflow.
Posture collection, per-control classification, and evidence shaping
are mechanical walks of the operator's manifest and policy, not
free-text reasoning steps; adding an agentic hook here would defeat
the determinism the posture-evidence record relies on. The compiler
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

Two replay properties are pinned for infra_posture_management.

**Per-execution deterministic replay** — the shared emitter under
`compilers/_shared/evidence/posture.py` produces a byte-identical
record on every re-emission against the same execution context. The
record `artifact_id` is
`SHA-256(workflow_id|execution_id|compile_target|policy_version.value)`;
`captured_at` and `evaluated_at` are deliberately excluded from the
id so re-emission at a later wall-clock instant still dedupes at the
path level. A re-walk of the same posture sources under the same
policy version re-derives the same `snapshot_hash`, the same
per-control evaluation result set, and the same artifact bytes.

**Per-target byte-stable goldens** — the three committed worked-
example records under
`examples/{n8n,temporal,langgraph}/infra_posture_management/evidence/posture-evidence-record.json`
are pinned byte-for-byte by the per-target byte-parity goldens at
`tests/examples/infra_posture_management/test_{n8n,temporal,langgraph}_workflow_golden.py`
and
`tests/examples/infra_posture_management/test_{n8n,temporal,langgraph}_posture_evidence.py`.
Each test pins (a) the per-target workflow artefact
(`workflow.n8n.json` / `workflow.temporal.py` / `graph_spec.json` +
`state_bindings.py`), (b) the per-target posture-evidence record, and
(c) the byte-equality of the co-located CACAO mirror against the
canonical source under `content/playbooks/infra_posture_management/`.
If the compiler or the shared emitter changes, regenerate the worked
example via the per-target `regenerate.sh` and commit the diff
intentionally; the drift guard flips green again.

The `artifact_id` derivation pins `policy_version.value` into the id
on purpose: a posture re-evaluation under a *new* policy version
deliberately produces a *new* `artifact_id`, even when the workflow
execution context is otherwise identical. That is the audit
property — a regulator reading the artifact series back can tell
exactly which policy version each posture artifact was evaluated
against, and a deduplicator never collapses two artifacts that were
evaluated under different policy versions.

## 7. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys, no
  cloud-account credentials, no identity-provider credentials, no
  network-baseline read endpoints. The cloud-account read APIs, the
  identity-provider read APIs, the network-baseline read APIs, and
  the storage backend for the posture-evidence records are
  operator-bound at runtime against environment variables documented
  per target; the framework ships no default endpoint per the
  sovereign-stack posture.
- **Deployment topology.** Worker concurrency, retry policies beyond
  the per-activity defaults, persistence backends, n8n hosting, the
  scheduler driving the continuous re-execution cadence, LangGraph
  host process model — those are runtime concerns the operator
  applies in their own assembly.
- **Posture-source collection.** This playbook consumes a posture
  snapshot the operator's collector has already produced over the
  in-scope manifest; the upstream collector (cloud-account read, IdP
  read, network-baseline read) is operator-owned and out of scope
  for this workflow. The framework commits to the artifact contract,
  not the collection topology.
- **Personal data in resource configurations.** Operator-side
  configurations may carry resource ids, account labels, owner
  tags, and tenancy markers; per AGENTS.md §3 they MUST stay
  role-shaped or opaque. Personal localparts, credential-shaped
  strings, and raw cloud-account secret material are out of scope
  and rejected at the schema boundary.
- **Per-deployment YAML.** This playbook ships no separate
  operator-facing `config.yaml`; per-case inputs are the CACAO
  `playbook_variables` block bound at compile time via the standard
  `__double_underscore__` substitution.

## 8. References

- [`content/playbooks/infra_posture_management/playbook.cacao.json`](../../content/playbooks/infra_posture_management/playbook.cacao.json)
  — canonical CACAO source.
- [`content/playbooks/infra_posture_management/README.md`](../../content/playbooks/infra_posture_management/README.md)
  — workflow-local module tree.
- [`schemas/evidence/posture.schema.json`](../../schemas/evidence/posture.schema.json)
  — per-execution posture-evidence artifact schema (stream:
  `posture`).
- [`content/mappings/nis2/article-21-2-a.yaml`](../../content/mappings/nis2/article-21-2-a.yaml)
  — NIS2 Art. 21(2)(a) mapping; entry `nis2:art-21-2-a` is the
  risk-analysis / information-system-security-policies anchor.
- [`compilers/_shared/evidence/posture.py`](../../compilers/_shared/evidence/posture.py)
  — shared framework-agnostic evidence emitter.
- [`examples/n8n/infra_posture_management/README.md`](../../examples/n8n/infra_posture_management/README.md)
- [`examples/temporal/infra_posture_management/README.md`](../../examples/temporal/infra_posture_management/README.md)
- [`examples/langgraph/infra_posture_management/README.md`](../../examples/langgraph/infra_posture_management/README.md)
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
