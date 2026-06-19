# iam_auditor — cookbook walkthrough

Per-execution capability-inventory workflow. The
`playbook.iam_auditor@v1` CACAO playbook fires on every workflow
execution: it resolves the role-shaped caller identity that invoked
the compiled workflow, walks the closed verb.resource capability list
that identity held at execution time, and emits one access-evidence
artifact per execution that the F-CP-07 access evidence stream
consumes and the auditor bundle (F-WF-09) folds into a handover.

The regulatory anchor is NIS2 Article 21(2)(i) — human-resources
security, access-control policies, and asset management — pinned by
the `nis2:art-21-2-i` mapping entry in
[`content/mappings/nis2/article-21-2-i.yaml`](../../content/mappings/nis2/article-21-2-i.yaml).
The artifact shape is
[`schemas/evidence/access.schema.json`](../../schemas/evidence/access.schema.json)
(stream: `access`).

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the deterministic
primitives package, the shared access-evidence emitter, and the
per-target adapter live in each.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/iam_auditor/
├── README.md                    # workflow-local module tree
├── playbook.cacao.json          # canonical CACAO v2 source (playbook.iam_auditor@v1)
└── primitives/
    ├── identity.py              # resolve_caller_identity — enumerate-identities
    ├── capabilities.py          # build_capability_list — enumerate-capabilities
    └── artifact.py              # build_access_artifact — emit-access-evidence

schemas/evidence/access.schema.json
                                  # per-execution access-evidence artifact schema (stream: access)

compilers/_shared/evidence/access.py
                                  # framework-agnostic shared emitter (deterministic id, atomic write)
```

The CACAO source is canonical. The primitives package is the
deterministic policy the playbook *means*. The three worked examples
are the same playbook compiled into three orchestrator idioms.
Everything else — runtime, identity-provider, capability source,
evidence sink — is the operator's data plane.

The CACAO source ships as JSON
(`content/playbooks/iam_auditor/playbook.cacao.json`); the three
worked examples each carry a mirror copy at
`examples/{n8n,temporal,langgraph}/iam_auditor/playbook.cacao.json`
that is byte-identical to the canonical and refreshed by the
per-target `regenerate.sh`.

## 2. CACAO topology and primitives binding

The playbook ships five steps: one `start`, three `action`, one `end`.
All three action steps declare an `x_secops_ng.core_body` reference
into the deterministic primitives package; there are **no absent-body
steps** in this workflow — the CORE wave landed the bindings up-front
in the canonical source rather than via a per-target overlay.

| Step suffix | Step                   | `core_body` binding                                                                       | Status |
|-------------|------------------------|-------------------------------------------------------------------------------------------|--------|
| `…000001`   | start                  | edge wiring only — no body                                                                | n/a    |
| `…000002`   | enumerate-identities   | `primitives.identity.resolve_caller_identity`                                             | bound  |
| `…000003`   | enumerate-capabilities | `primitives.capabilities.build_capability_list`                                           | bound  |
| `…000004`   | emit-access-evidence   | `primitives.artifact.build_access_artifact`                                               | bound  |
| `…000005`   | end                    | edge wiring only — no body                                                                | n/a    |

Transitions are deterministic — each state has exactly one
`on_completion` successor, no conditional branching at this layer.
One execution emits exactly one access-evidence artifact; there is no
per-finding fan-out at this layer (capabilities are a closed list
attached to a single caller identity, not a stream of independent
records).

## 3. Deterministic primitives — the contract

The role-shape regex on the caller principal, the closed verb.resource
canonicalisation of the capability list, the `artifact_id` recipe, and
the JSON-native shape of the access-evidence record are **code, not
configuration**. They live in
`content/playbooks/iam_auditor/primitives/` and in the shared emitter
under `compilers/_shared/evidence/access.py`. Operators who need to
diverge fork the primitive module; they do not override it via runtime
config.

The three bindings exercised today:

`resolve_caller_identity(principal_type, principal_id, identity_provider) -> CallerIdentity`
:   The `enumerate-identities` step canonicalises the role-shaped
    caller identity the compile target's runtime resolves. The
    identity is supplied by the runtime — n8n credential binding,
    Temporal worker identity, LangGraph runtime principal. The
    primitive validates `principal_type` against the schema enum
    (`service_account` / `workflow_runtime` / `automation_role`;
    personal-user principals rejected at the boundary), checks
    `principal_id` against the role-shape regex the schema pins
    (UPPER_SNAKE_CASE / lower-snake-case / hyphenated tokens — no
    personal localparts, no credential-shaped strings, no free text),
    and shape-checks the optional `identity_provider` short token. The
    public-bar enforcement is the linter, but failing here produces a
    cleaner error path than letting the schema reject the artifact
    downstream.

`build_capability_list(capabilities) -> Sequence[str]`
:   The `enumerate-capabilities` step canonicalises the closed
    verb.resource list the resolved caller held at execution time.
    Each entry is a single `verb.resource` token (lower-snake-case
    verb, single dot, lower-snake-case resource); free text,
    wildcards, and credential-shaped strings are rejected at the regex
    boundary. The output preserves the operator-supplied order *and*
    dedups exact-match repeats, NFKC-normalised and lower-cased, so
    two replays of the same identity walk against the same provider
    produce byte-identical bytes. There is no implicit grant
    expansion; the runtime-side assertion is paired with the F-PT-01
    platform-side guarantee that the caller actually held the listed
    capabilities at boot — that orthogonal check is out of scope here.

`build_access_artifact(workflow_id, execution_id, compile_target, regulation_refs, control_refs, caller_identity, capabilities, captured_at, source_url) -> AccessEvidenceArtifact`
:   The `emit-access-evidence` step shapes the JSON-native
    access-evidence record the shared emitter under
    [`compilers/_shared/evidence/access.py`](../../compilers/_shared/evidence/access.py)
    serialises. The emitter is the single source of truth for the
    `artifact_id` recipe — SHA-256 of
    `<workflow_id>|<execution_id>|<compile_target>` (UTF-8, no
    separators around the pipes) — per the schema's `artifact_id`
    contract. `captured_at` is deliberately *not* part of the id so
    a re-emission of the same execution at a different wall-clock
    instant still dedupes at the path level. The primitive
    re-validates `caller_identity` and `capabilities` shape so a
    direct caller cannot inject a personal-user principal or a
    wildcard token even when the upstream primitive is bypassed.

Determinism is the property a regulator can replay against. The shared
emitter is the byte-stable anchor the per-target byte-parity goldens
pin: the three per-target adapters are thin glue, and the on-disk
evidence record re-emits byte-identical bytes on every regeneration
from the same canonical CACAO source and the same representative
context.

> **LM determinism.** Identity resolution, capability canonicalisation,
> and access-evidence shaping are code, not LM. The iam_auditor
> playbook does not bind any DSPy signature — there is no free-text
> step at this layer. The runtime-side capability assertion is a
> mechanical walk of the operator's IAM provider, not an LM judgement.
> See `docs/FOUNDATION.md` § LLM determinism.

## 4. Per-target hand-off

### 4.1 n8n — operator-edited Set rows + Code-node bindings

`examples/n8n/iam_auditor/workflow.n8n.json` carries the CACAO
topology as n8n nodes (`manualTrigger`, `set`, `code`, `noOp`), with
node ids preserving the CACAO step ids verbatim. The three bound CORE
steps emit `n8n-nodes-base.code` nodes whose `pythonCode` is the
exact primitive call — e.g.
`from content.playbooks.iam_auditor.primitives.identity import resolve_caller_identity ; __caller_identity_ref__ = resolve_caller_identity(__principal_type__, __principal_id__, __identity_provider__)`.
The Code-node body assumes `PYTHONPATH` on the n8n host resolves
`content.playbooks.iam_auditor.primitives`; operators who run n8n in
a Python-free container drop a Python-runner Code node between the
Set node and the next step — see
[`examples/n8n/iam_auditor/README.md`](../../examples/n8n/iam_auditor/README.md)
under *Per-action wiring notes — CORE bodies*.

The `emit-access-evidence` step routes the typed context through the
shared evidence emitter; the n8n adapter calls
`compilers._shared.evidence.access.emit_access_artifact` with the
typed context and the operator-supplied evidence directory, and the
emitter writes the deterministic `<artifact_id>.json` to disk.

### 4.2 Temporal — `@activity.defn` bodies with retry policy

`examples/temporal/iam_auditor/workflow.temporal.py` is a standard
Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action. The three bound activities
import the primitive (and the shared emitter for
`emit-access-evidence`) and produce the canonical caller identity /
capability list / access-evidence record. There are no absent-body
activities in this workflow.

The committed `workflow.temporal.py` is a generated stub: CORE
primitive calls are inlined into the activity bodies under the
`@activity.defn` decorators, while the workflow lowering itself (the
`@workflow.run` method) still raises `NotImplementedError` pending the
workflow-translator slice — operators wire the activity scheduling in
their worker assembly. Per-activity retry policies are emitted
alongside the activities (`<ACTIVITY>_RETRY_POLICY`) so the operator
can pin them on the `workflow.execute_activity` call sites.

The sibling `_audit_mirror.py` carries the `AuditRecord` / `AuditTrail`
types — no `compilers.*` import in the emitted artifact, so the worker
module is a self-contained drop-in. The Temporal evidence adapter is
the durable surface that exercises the shared emitter under
deterministic execution; replay against the same Temporal event
history re-derives the same `artifact_id`.

### 4.3 LangGraph — `@tool` wrappers + agentic-extension hook

`examples/langgraph/iam_auditor/state_bindings.py` carries the
`TypedDict` state and the three `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (nodes, edges).
`assemble.py` is the canonical reference assembly that wires the spec
into a `StateGraph`. The three bound tools import the primitive (and
the shared emitter for `emit-access-evidence`) and update the typed
state; there are no absent-body tools.

LangGraph is the agentic target — the natural seam an operator extends
with an LLM-driven node is *out of band* for this workflow. Identity
resolution and capability enumeration are mechanical walks of the
operator's IAM provider, not free-text reasoning steps; adding an
agentic hook here would defeat the determinism the access-evidence
record relies on. The compiler never embeds an LLM SDK; the
framework-wide EU-resident LM endpoint guard re-applies the check at
process startup (`compilers/_shared/lm_endpoint_guard.py`), with the
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
  assembled in `assemble.py`; tool span (`tool.<step_id>`) inside the
  `@tool` wrapper.

The OTLP exporter endpoint is operator-supplied
(`OTEL_EXPORTER_OTLP_ENDPOINT`). The compiler never sets a default and
never imports a vendor SDK; pointing the exporter at a managed APM is
a downstream choice the operator owns end-to-end. The sovereignty
posture asks for an EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline.

## 6. Replay and audit story

Two replay properties are pinned for iam_auditor.

**Per-execution deterministic replay** — the shared emitter under
`compilers/_shared/evidence/access.py` produces a byte-identical
record on every re-emission against the same execution context. The
record `artifact_id` is
`SHA-256(workflow_id|execution_id|compile_target)`; `captured_at` is
deliberately excluded from the id so re-emission at a later
wall-clock instant still dedupes at the path level. A re-walk of the
same execution against the same IAM provider re-derives the same
caller-identity block, the same canonical capability list, and the
same artifact bytes.

**Per-target byte-stable goldens** — the three committed worked-
example records under
`examples/{n8n,temporal,langgraph}/iam_auditor/evidence/access-evidence.json`
are pinned byte-for-byte by the per-target byte-parity goldens at
`tests/examples/{n8n,temporal,langgraph}/iam_auditor/test_golden.py`.
Each test pins (a) the per-target workflow artefact
(`workflow.n8n.json` / `workflow.temporal.py` / `graph_spec.json` +
`state_bindings.py`), (b) the per-target access-evidence record, and
(c) the byte-equality of the co-located CACAO mirror against the
canonical source under `content/playbooks/iam_auditor/`. If the
compiler or the shared emitter changes, regenerate the worked example
via the per-target `regenerate.sh` and commit the diff intentionally;
the drift guard flips green again.

The access-evidence `artifact_id` keys on the `compile_target`
discriminator by design — the three reference targets have distinct
capability surfaces (n8n credential bindings, Temporal worker
identity, LangGraph runtime principal) and the artifact is honest
about which surface produced it. An operator running more than one
target against the same workflow emits one artifact per target per
execution; downstream consumers join on `(workflow_id, execution_id)`
and treat `compile_target` as a discriminator, not a noise dimension.

## 7. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys, no IAM
  provider endpoints, no IdP credentials, no service-account secrets.
  The identity provider, the capability source, and the storage
  backend for the access-evidence records are operator-bound at
  runtime against environment variables documented per target; the
  framework ships no default endpoint per the sovereign-stack posture.
- **Deployment topology.** Worker concurrency, retry policies beyond
  the per-activity defaults, persistence backends, n8n hosting,
  LangGraph host process model — those are runtime concerns the
  operator applies in their own assembly.
- **Platform-side capability enforcement.** This playbook captures the
  *assertion* that the caller held a specific capability list at
  execution time; the orthogonal F-PT-01 platform-side guarantee that
  the runtime actually withheld other capabilities at boot lives in
  the platform layer, not in this workflow.
- **Personal-user identities.** The `caller_identity` block is
  role-shaped by schema discipline (service-account, workflow-runtime
  principal, automation role). Operators auditing personal-user access
  attach a different workflow under the JML controls in
  `content/controls/`; this playbook is for the automation-runtime
  surface only.
- **Per-deployment YAML.** This playbook ships no separate
  operator-facing `config.yaml`; per-case inputs are the CACAO
  `playbook_variables` block bound at compile time via the standard
  `__double_underscore__` substitution.

## 8. References

- [`content/playbooks/iam_auditor/playbook.cacao.json`](../../content/playbooks/iam_auditor/playbook.cacao.json)
  — canonical CACAO source.
- [`content/playbooks/iam_auditor/README.md`](../../content/playbooks/iam_auditor/README.md)
  — workflow-local module tree.
- [`schemas/evidence/access.schema.json`](../../schemas/evidence/access.schema.json)
  — per-execution access-evidence artifact schema (stream: `access`).
- [`content/mappings/nis2/article-21-2-i.yaml`](../../content/mappings/nis2/article-21-2-i.yaml)
  — NIS2 Art. 21(2)(i) mapping; entry `nis2:art-21-2-i` is the
  human-resources-security / access-control / asset-management anchor.
- [`compilers/_shared/evidence/access.py`](../../compilers/_shared/evidence/access.py)
  — shared framework-agnostic evidence emitter.
- [`examples/n8n/iam_auditor/README.md`](../../examples/n8n/iam_auditor/README.md)
- [`examples/temporal/iam_auditor/README.md`](../../examples/temporal/iam_auditor/README.md)
- [`examples/langgraph/iam_auditor/README.md`](../../examples/langgraph/iam_auditor/README.md)
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
