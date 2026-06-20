# onboarding_offboarding_tracker — cookbook walkthrough

Per-lifecycle-event grant/revoke-confirmation workflow. The
`playbook.onboarding_offboarding_tracker@v1` CACAO playbook fires on
every joiner / mover / leaver event against a role-shaped runtime
principal: it resolves the principal handle the event names, applies
the declared capability delta against the operator's identity source,
re-reads the closed capability list to confirm the delta landed, and
emits one access-evidence artifact per lifecycle event that the
F-CP-07 access evidence stream consumes alongside the per-execution
inventory the F-WF-08 IAM auditor produces.

The regulatory anchor is NIS2 Article 21(2)(i) — human-resources
security, access-control policies, and asset management — pinned by
the `nis2:art-21-2-i` mapping entry in
[`content/mappings/nis2/article-21-2-i.yaml`](../../content/mappings/nis2/article-21-2-i.yaml).
The artifact shape is
[`schemas/evidence/access.schema.json`](../../schemas/evidence/access.schema.json)
(stream: `access`). The same mapping entry references
`playbook.iam_auditor@v1` — the two workflows discharge the read-side
and write-side halves of the same obligation surface and reuse the
same evidence schema.

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
content/playbooks/onboarding_offboarding_tracker/
├── README.md                    # workflow-local module tree
├── playbook.cacao.json          # canonical CACAO v2 source (playbook.onboarding_offboarding_tracker@v1)
└── primitives/
    ├── ingest.py                # ingest_lifecycle_event — ingest-lifecycle-event
    ├── identity.py              # resolve_identity — resolve-identity
    ├── delta.py                 # apply_capability_delta — apply-capability-delta
    ├── confirmation.py          # confirm_grant_revoke — confirm-grant-revoke
    └── artifact.py              # build_access_artifact — emit-access-evidence

schemas/evidence/access.schema.json
                                  # per-lifecycle-event access-evidence artifact schema (stream: access; reused)

compilers/_shared/evidence/access.py
                                  # framework-agnostic shared emitter (deterministic id, atomic write)
```

The CACAO source is canonical. The primitives package is the
deterministic policy the playbook *means*. The three worked examples
are the same playbook compiled into three orchestrator idioms.
Everything else — runtime, identity-provider, capability source,
evidence sink — is the operator's data plane.

The CACAO source ships as JSON
(`content/playbooks/onboarding_offboarding_tracker/playbook.cacao.json`);
the three worked examples each carry a mirror copy at
`examples/{n8n,temporal,langgraph}/onboarding_offboarding_tracker/playbook.cacao.json`
that is byte-identical to the canonical and refreshed by the
per-target `regenerate.sh`.

## 2. CACAO topology and primitives binding

The playbook ships seven steps: one `start`, five `action`, one `end`.
All five action steps declare an `x_secops_ng.core_body` reference
into the deterministic primitives package; there are **no absent-body
steps** in this workflow — the CORE wave landed the bindings up-front
in the canonical source rather than via a per-target overlay.

| Step suffix | Step                     | `core_body` binding                                                                          | Status |
|-------------|--------------------------|----------------------------------------------------------------------------------------------|--------|
| `…000001`   | start                    | edge wiring only — no body                                                                   | n/a    |
| `…000002`   | ingest-lifecycle-event   | `primitives.ingest.ingest_lifecycle_event`                                                   | bound  |
| `…000003`   | resolve-identity         | `primitives.identity.resolve_identity`                                                       | bound  |
| `…000004`   | apply-capability-delta   | `primitives.delta.apply_capability_delta`                                                    | bound  |
| `…000005`   | confirm-grant-revoke     | `primitives.confirmation.confirm_grant_revoke`                                               | bound  |
| `…000006`   | emit-access-evidence     | `primitives.artifact.build_access_artifact`                                                  | bound  |
| `…000007`   | end                      | edge wiring only — no body                                                                   | n/a    |

Transitions are deterministic — each state has exactly one
`on_completion` successor, no conditional branching at this layer.
One lifecycle event emits exactly one access-evidence artifact; there
is no per-finding fan-out at this layer (the declared delta and the
observed confirmation collapse into a single envelope on the
emitter's input).

## 3. Deterministic primitives — the contract

The role-shape regex on the principal handle, the closed
verb.resource canonicalisation of the declared delta and the observed
capability list, the joiner / mover / leaver event-kind discipline,
the `artifact_id` recipe, and the JSON-native shape of the
access-evidence record are **code, not configuration**. They live in
`content/playbooks/onboarding_offboarding_tracker/primitives/` and in
the shared emitter under `compilers/_shared/evidence/access.py`.
Operators who need to diverge fork the primitive module; they do not
override it via runtime config.

The five bindings exercised today:

`ingest_lifecycle_event(raw_event, lifecycle_event_ref) -> LifecycleEventRecord`
:   The `ingest-lifecycle-event` step normalises the operator-supplied
    lifecycle event into a closed in-workflow record (`event_kind` in
    `{joiner, mover, leaver}`, role-shaped `principal_handle`,
    closed `declared_capability_delta` add-set / remove-set,
    `effective_at`). Read-only by contract: the workflow MUST NOT
    mutate the source event on this step. The identity source the
    `lifecycle_event_ref` points at is operator-configured — no
    default hosted IdP, no HR-SaaS dependency, no non-EU default
    endpoint.

`resolve_identity(lifecycle_event_record) -> ResolvedIdentity`
:   The `resolve-identity` step canonicalises the role-shaped caller
    identity the ingested event names. The primitive validates
    `principal_type` against the schema enum
    (`service_account` / `workflow_runtime` / `automation_role`;
    personal-user principals rejected at the boundary), checks
    `principal_id` against the role-shape regex the schema pins
    (UPPER_SNAKE_CASE / lower-snake-case / hyphenated tokens — no
    personal localparts, no credential-shaped strings, no free text),
    and shape-checks the optional `identity_provider` short token.
    The F-WF-08 IAM auditor enforces the same shape on the read side
    so the two workflows produce envelope-compatible artifacts.

`apply_capability_delta(lifecycle_event_record, resolved_identity) -> CapabilityDelta`
:   The `apply-capability-delta` step pins the closed delta the event
    declares — grant the add-set on a joiner, adjust both sets on a
    mover, drain the remove-set on a leaver. Each entry is a single
    `verb.resource` token (lower-snake-case verb, single dot,
    lower-snake-case resource); free text, wildcards, and
    credential-shaped strings are rejected at the regex boundary. The
    delta is closed (no implicit grants, no implicit revocations
    beyond what the event declares) and deterministic on the same
    event record + same resolved principal — re-runs collapse to
    byte-identical bytes at the delta layer. The actual mutation on
    the operator's identity source is delegated to the compile
    target in its native idiom; the primitive only pins the
    closed-delta shape that the confirmation step re-walks against.

`confirm_grant_revoke(capability_delta, observed_capabilities) -> Confirmation`
:   The `confirm-grant-revoke` step closes the loop between intent
    (the closed delta) and observed effect (the post-mutation
    closed capability list re-read from the same identity source).
    The observed list is canonicalised through the same
    verb.resource regex; divergence between declared add-set and
    observed presence surfaces as `missing_grants`, divergence
    between declared remove-set and observed presence surfaces as
    `lingering_revokes`. Read-only on this step. The confirmation
    block IS the lifecycle counterpart of the IAM auditor's
    capability inventory — same canonical shape, different anchor
    point on the lifecycle.

`build_access_artifact(workflow_id, execution_id, compile_target, regulation_refs, control_refs, resolved_identity, confirmation, captured_at, source_url, owner_role, owner_assigned_at) -> AccessEvidenceArtifact`
:   The `emit-access-evidence` step shapes the JSON-native
    access-evidence record the shared emitter under
    [`compilers/_shared/evidence/access.py`](../../compilers/_shared/evidence/access.py)
    serialises. The emitter is the single source of truth for the
    `artifact_id` recipe — SHA-256 of
    `<workflow_id>|<execution_id>|<compile_target>` (UTF-8, no
    separators around the pipes) — per the schema's `artifact_id`
    contract. `captured_at` is deliberately *not* part of the id so
    a re-emission of the same lifecycle event at a different
    wall-clock instant still dedupes at the path level. The
    primitive re-validates `resolved_identity` and the confirmed
    capability list shape so a direct caller cannot inject a
    personal-user principal or a wildcard token even when the
    upstream primitives are bypassed.

Determinism is the property a regulator can replay against. The
shared emitter is the byte-stable anchor the per-target byte-parity
goldens pin: the three per-target adapters are thin glue, and the
on-disk evidence record re-emits byte-identical bytes on every
regeneration from the same canonical CACAO source and the same
representative context.

> **LM determinism.** Lifecycle-event ingestion, identity resolution,
> capability-delta application, grant/revoke confirmation, and
> access-evidence shaping are code, not LM. The
> onboarding_offboarding_tracker playbook does not bind any DSPy
> signature — there is no free-text step at this layer. The
> identity-source walk is a mechanical re-read of the operator's IAM
> provider, not an LM judgement. See `docs/FOUNDATION.md` § LLM
> determinism.

## 4. Per-target hand-off

### 4.1 n8n — operator-edited Set rows + Code-node bindings

`examples/n8n/onboarding_offboarding_tracker/workflow.n8n.json`
carries the CACAO topology as n8n nodes (`manualTrigger`, `set`,
`code`, `noOp`), with node ids preserving the CACAO step ids
verbatim. The five bound CORE steps emit `n8n-nodes-base.code` nodes
whose `pythonCode` is the exact primitive call — e.g.
`from content.playbooks.onboarding_offboarding_tracker.primitives.identity import resolve_identity ; __resolved_identity_ref__ = resolve_identity(__lifecycle_event_record_ref__)`.
The Code-node body assumes `PYTHONPATH` on the n8n host resolves
`content.playbooks.onboarding_offboarding_tracker.primitives`;
operators who run n8n in a Python-free container drop a Python-runner
Code node between the Set node and the next step — see
[`examples/n8n/onboarding_offboarding_tracker/README.md`](../../examples/n8n/onboarding_offboarding_tracker/README.md)
under *Per-action wiring notes — CORE bodies*.

The `emit-access-evidence` step routes the typed context through the
shared evidence emitter; the n8n adapter calls
`compilers._shared.evidence.access.emit_access_artifact` with the
typed context and the operator-supplied evidence directory, and the
emitter writes the deterministic `<artifact_id>.json` to disk.

### 4.2 Temporal — `@activity.defn` bodies with retry policy

`examples/temporal/onboarding_offboarding_tracker/workflow.temporal.py`
is a standard Temporal worker module: one `@workflow.defn` class and
one `@activity.defn` function per CACAO action. The five bound
activities import the primitive (and the shared emitter for
`emit-access-evidence`) and produce the canonical lifecycle event
record / resolved identity / capability delta / confirmation /
access-evidence record. There are no absent-body activities in this
workflow.

The committed `workflow.temporal.py` is a generated stub: CORE
primitive calls are inlined into the activity bodies under the
`@activity.defn` decorators, while the workflow lowering itself (the
`@workflow.run` method) still raises `NotImplementedError` pending
the workflow-translator slice — operators wire the activity
scheduling in their worker assembly. Per-activity retry policies are
emitted alongside the activities (`<ACTIVITY>_RETRY_POLICY`) so the
operator can pin them on the `workflow.execute_activity` call sites.

The Temporal evidence adapter is the durable surface that exercises
the shared emitter under deterministic execution; replay against the
same Temporal event history re-derives the same `artifact_id`.

### 4.3 LangGraph — `@tool` wrappers + agentic-extension hook

`examples/langgraph/onboarding_offboarding_tracker/state_bindings.py`
carries the `TypedDict` state and the five `@tool`-decorated action
wrappers. `graph_spec.json` carries the target-neutral topology
(nodes, edges). `assemble.py`/`regenerate.py` is the canonical
reference assembly that wires the spec into a `StateGraph`. The five
bound tools import the primitive (and the shared emitter for
`emit-access-evidence`) and update the typed state; there are no
absent-body tools.

LangGraph is the agentic target — the natural seam an operator
extends with an LLM-driven node is *out of band* for this workflow.
Lifecycle-event ingestion, identity resolution, delta application,
and grant/revoke confirmation are mechanical walks of the operator's
identity source, not free-text reasoning steps; adding an agentic
hook here would defeat the determinism the access-evidence record
relies on. The compiler never embeds an LLM SDK; the framework-wide
EU-resident LM endpoint guard re-applies the check at process startup
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

Span boundaries per target match the iam_auditor convention (workflow
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

Two replay properties are pinned for onboarding_offboarding_tracker.

**Per-lifecycle-event deterministic replay** — the shared emitter
under `compilers/_shared/evidence/access.py` produces a byte-identical
record on every re-emission against the same lifecycle-event context.
The record `artifact_id` is
`SHA-256(workflow_id|execution_id|compile_target)`; `captured_at` is
deliberately excluded from the id so re-emission at a later
wall-clock instant still dedupes at the path level. A re-walk of the
same lifecycle event against the same identity source re-derives the
same resolved-identity block, the same canonical declared delta, the
same observed capability list, the same confirmation diff, and the
same artifact bytes.

**Per-target byte-stable goldens** — the three committed
worked-example records under
`examples/{n8n,temporal,langgraph}/onboarding_offboarding_tracker/evidence/access-evidence.json`
are pinned byte-for-byte by the per-target byte-parity goldens at
`tests/examples/onboarding_offboarding_tracker/test_{n8n,temporal,langgraph}_workflow_golden.py`
and
`tests/examples/onboarding_offboarding_tracker/test_{n8n,temporal,langgraph}_access_evidence.py`.
Each test pins (a) the per-target workflow artefact
(`workflow.n8n.json` / `workflow.temporal.py` / `graph_spec.json` +
`state_bindings.py`), (b) the per-target access-evidence record, and
(c) the byte-equality of the co-located CACAO mirror against the
canonical source under
`content/playbooks/onboarding_offboarding_tracker/`. If the compiler
or the shared emitter changes, regenerate the worked example via the
per-target `regenerate.sh` and commit the diff intentionally; the
drift guard flips green again.

The access-evidence `artifact_id` keys on the `compile_target`
discriminator by design — the three reference targets have distinct
capability surfaces (n8n credential bindings, Temporal worker
identity, LangGraph runtime principal) and the artifact is honest
about which surface produced it. An operator running more than one
target against the same lifecycle event emits one artifact per target
per event; downstream consumers join on `(workflow_id, execution_id)`
and treat `compile_target` as a discriminator, not a noise dimension.

## 7. KRIs — joiner/leaver lifecycle latency

The EXTEND-metrics wave pinned two KRI entries under `content/metrics/`:

- [`kri.joiner_to_provisioned_time@v1`](../../content/metrics/joiner_to_provisioned_time.yaml)
  — wall-clock latency from a joiner lifecycle event's
  `effective_at` to the confirmed presence of every declared add-set
  capability on the principal's downstream surface.
- [`kri.leaver_to_revoked_time@v1`](../../content/metrics/leaver_to_revoked_time.yaml)
  — wall-clock latency from a leaver lifecycle event's
  `effective_at` to the confirmed absence of every declared
  remove-set capability.

Both KRIs are referenced by the `confirm-grant-revoke` and
`emit-access-evidence` steps via the `metric_refs` block; the metrics
read directly off the confirmation envelope and the artifact
`captured_at` and produce no additional collector surface.

## 8. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys, no IAM
  provider endpoints, no IdP credentials, no service-account secrets.
  The identity source, the capability source, and the storage backend
  for the access-evidence records are operator-bound at runtime
  against environment variables documented per target; the framework
  ships no default endpoint per the sovereign-stack posture.
- **Deployment topology.** Worker concurrency, retry policies beyond
  the per-activity defaults, persistence backends, n8n hosting,
  LangGraph host process model — those are runtime concerns the
  operator applies in their own assembly.
- **Platform-side capability enforcement.** This playbook captures
  the *assertion* that the declared delta landed on the principal's
  downstream surface at lifecycle-event time; the orthogonal F-PT-01
  platform-side guarantee that the runtime actually withheld other
  capabilities at boot lives in the platform layer, not in this
  workflow.
- **Personal-user identities.** The `principal_handle` is
  role-shaped by schema discipline (service-account,
  workflow-runtime principal, automation role). Operators auditing
  personal-user joiner-mover-leaver attach a different workflow
  under the JML controls in `content/controls/`; this playbook is
  for the automation-runtime surface only.
- **HR-SaaS or IdP integration code.** The framework ships no
  connector, no SDK, no default lifecycle-event feed shape. The
  ingest primitive's `lifecycle_event_ref` is a string pointer the
  operator's adapter resolves against their own identity source.

## 9. References

- [`content/playbooks/onboarding_offboarding_tracker/playbook.cacao.json`](../../content/playbooks/onboarding_offboarding_tracker/playbook.cacao.json)
  — canonical CACAO source.
- [`content/playbooks/onboarding_offboarding_tracker/README.md`](../../content/playbooks/onboarding_offboarding_tracker/README.md)
  — workflow-local module tree.
- [`schemas/evidence/access.schema.json`](../../schemas/evidence/access.schema.json)
  — per-execution / per-lifecycle-event access-evidence artifact
  schema (stream: `access`; reused with the F-WF-08 IAM auditor).
- [`content/mappings/nis2/article-21-2-i.yaml`](../../content/mappings/nis2/article-21-2-i.yaml)
  — NIS2 Art. 21(2)(i) mapping; entry `nis2:art-21-2-i` is the
  human-resources-security / access-control / asset-management
  anchor; references both this playbook and `playbook.iam_auditor@v1`.
- [`compilers/_shared/evidence/access.py`](../../compilers/_shared/evidence/access.py)
  — shared framework-agnostic evidence emitter.
- [`docs/cookbook/iam_auditor.md`](iam_auditor.md) — read-side
  counterpart on the same NIS2 Art. 21(2)(i) anchor.
- [`content/metrics/joiner_to_provisioned_time.yaml`](../../content/metrics/joiner_to_provisioned_time.yaml)
- [`content/metrics/leaver_to_revoked_time.yaml`](../../content/metrics/leaver_to_revoked_time.yaml)
- [`examples/n8n/onboarding_offboarding_tracker/README.md`](../../examples/n8n/onboarding_offboarding_tracker/README.md)
- [`examples/temporal/onboarding_offboarding_tracker/README.md`](../../examples/temporal/onboarding_offboarding_tracker/README.md)
- [`examples/langgraph/onboarding_offboarding_tracker/README.md`](../../examples/langgraph/onboarding_offboarding_tracker/README.md)
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
