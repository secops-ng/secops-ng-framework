# alert_triage — cookbook walkthrough

SOC alert triage. The `playbook.alert_triage@v1` CACAO playbook
ingests a typed alert payload from one of two source shapes (a push
from the detection pipeline or a pull from a shared alert store),
enriches the case with adjacent telemetry context, collapses repeat
fires inside a configurable suppression window, applies a
deterministic prioritisation policy across the detection, asset, and
suppression axes to land the case in one of four bands (`p1_severe`,
`p2_high`, `p3_routine`, `p4_informational`), and routes onto the
matching response branch (page-and-escalate, notify-on-call,
queue-for-review, or log-and-close).

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the deterministic
primitives package, the OpenTelemetry signal layer, and the
context-local `AuditTrail` mirror live in each.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/
├── alert_triage.cacao.yaml          # canonical CACAO v2 source
└── alert_triage/
    ├── README.md                    # workflow-local module tree
    ├── payloads/                    # Pydantic v2 alert envelope models (two source shapes)
    └── primitives/
        ├── payloads.py              # validate_alert_payload (push / pull dispatch)
        ├── suppression.py           # canonical_seen_key + SuppressionWindow
        ├── prioritisation.py        # prioritise(detection, asset, suppression) → PriorityVerdict
        ├── response.py              # escalation_route + notify_on_call + route_to_review_queue
        └── signatures.py            # DSPy signature schema for free-text fields only
```

The CACAO source is canonical. The primitives package is the
deterministic policy the playbook *means*. The three worked examples
are the same playbook compiled into three orchestrator idioms.
Everything else — runtime, connectors, credentials — is the
operator's data plane.

The canonical YAML is in `content/playbooks/alert_triage.cacao.yaml`
rather than nested under `content/playbooks/alert_triage/`. Whether
the YAML should move under the workflow directory is a separate
refactor and deliberately out of scope here; the workflow-local module
tree is what the per-target compilers depend on today.

## 2. CACAO topology and primitives binding

The playbook ships 12 steps: one `start`, eight `action`, one
`if-condition`, one `switch-condition`, one `end`. Seven of the eight
action steps declare an `x_secops_ng.core_body` reference into the
deterministic primitives package — all eight are bound; the playbook
is `stable` at `content_version` 1.0.0 under the Maturity ladder.

| Step suffix       | Step                                                | `core_body` binding                                            | Status   |
|-------------------|-----------------------------------------------------|----------------------------------------------------------------|----------|
| `…000002`         | ingest typed alert payload                          | `primitives.payloads.validate_alert_payload`                   | bound    |
| `…000003`         | enrich with telemetry context                       | `primitives.suppression.canonical_seen_key`                    | bound    |
| `…000004`         | benign or already-seen? (if-condition)              | edge wiring only — no body                                     | n/a      |
| `…000005`         | suppress and close                                  | `primitives.suppression.canonical_seen_key`                    | bound    |
| `…000006`         | classify and prioritise (deterministic policy)      | `primitives.prioritisation.prioritise`                         | bound    |
| `…000007`         | route on priority (switch-condition)                | edge wiring only — no body                                     | n/a      |
| `…000008`         | response: p1 severe — page and escalate             | `primitives.response.escalation_route`                         | bound    |
| `…000009`         | response: p2 high — notify on-call                  | `primitives.response.notify_on_call`                           | bound    |
| `…00000a`         | response: p3 routine — queue for review             | `primitives.response.route_to_review_queue`                    | bound    |
| `…00000b`         | response: p4 informational — log and close          | `primitives.response.log_and_close`                            | bound    |

The eight bindings are the byte-identical anchor the cross-target
replay property hangs off. The remaining `NotImplementedError` in the
emitted artifacts marks only operator-integration seams (connector
inputs the operator wires), which is emitter-standard across every
bound playbook — span + AuditTrail mirror prologue first, so the seam
is identifiable at a glance.

## 3. Deterministic primitives — the contract

The priority bands, the suppression-window length, the canonical
seen-key shape, the typed alert payload schema, and the DSPy signature
schema for free-text fields are **code, not configuration**. They live
in `content/playbooks/alert_triage/primitives/`. Operators who need to
diverge fork the primitive module; they do not override it via runtime
config.

The seven bindings exercised today:

`validate_alert_payload(raw, source_shape) -> AlertPayload`
:   The ingest step normalises the inbound alert into the SecOps-NG
    `AlertPayload` envelope. Two source shapes are accepted
    (`push_detection_pipeline`, `pull_alert_store`); the dispatcher
    routes on `source_shape`. Validation failures raise a typed
    `PayloadValidationError` so an operator's connector wiring sees
    the seam.

`canonical_seen_key(detection_rule_id, subject_ref, asset_ref, classification) -> str`
:   The enrich and suppress steps derive the same seen-key shape from
    the four canonical axes. The `SuppressionWindow` helper carries
    the sliding-window membership check; two re-fires of the same
    alert inside the window collapse onto one case. Operators who
    diverge on the seen-key shape fork `suppression.py`.

`prioritise(detection_class, detection_severity, context, correlates_open_case) -> PriorityVerdict`
:   The classify step produces a single normalised priority verdict
    across three axes (detection, asset, suppression) so the
    downstream switch picks one of the four response branches without
    re-deriving the call in three different target idioms. The
    verdict carries the final band, the unmodified detection severity,
    an ordered tuple of every reason that fired, and a digest of the
    canonical inputs so a replay-vs-original comparison is one
    string-equal check.

`escalation_route(priority, asset_criticality, internet_exposed, regulated_data) -> EscalationDirective`
:   The p1-severe response step produces the page + escalate directive
    (paging tier + escalation handoff to the incident_management
    playbook) deterministically from the priority verdict and the
    asset axis.

`notify_on_call(priority, asset_criticality, internet_exposed, regulated_data) -> NotificationDirective`
:   The p2-high response step produces the notify directive
    (notification cadence + on-call routing) deterministically from
    the same axes.

`route_to_review_queue(priority, asset_criticality, internet_exposed, regulated_data) -> ReviewQueueDirective`
:   The p3-routine response step produces the review-queue placement
    (review tier + cadence) deterministically from the same axes.

Determinism is the property a regulator can replay against. The
`PriorityVerdict.inputs_digest` is the same hex string on every target
because the policy is the same Python function; the digest is what
makes byte-parity meaningful at audit time.

> **LM determinism.** The priority decision is code, not LM. DSPy
> appears only in `primitives.signatures` and is reserved for
> free-text fields (analyst summary, narrative) where free-text-in /
> structured-out is the only sensible shape. See
> `docs/FOUNDATION.md` § LLM determinism.

## 4. Per-target hand-off

### 4.1 n8n — operator-edited Set rows + Code-node bindings

`examples/n8n/alert_triage/workflow.n8n.json` carries the CACAO
topology as n8n nodes (`manualTrigger`, `set`, `if`, `switch`, `noOp`),
with node ids preserving the CACAO step ids verbatim. The seven bound
CORE steps emit `n8n-nodes-base.code` nodes whose `pythonCode` is the
exact primitive call (e.g. `from alert_triage.primitives.prioritisation
import prioritise ; __priority_verdict__ = prioritise(...)`) — all
eight action steps, the p4 log-and-close step included, lower to code
nodes invoking their bound primitives.

Operators bind the Code-node inputs to their connectors:

- ingest → detection-pipeline push endpoint / shared alert store
- enrich → telemetry-context enrichment store
- suppression → operator's suppression / known-benign cache
- response branches → ticketing / paging / queueing connectors

The Code-node body for the seven bound steps assumes `PYTHONPATH` on
the n8n host resolves `alert_triage.primitives`. Operators who run
n8n in a Python-free container drop a single Python-runner Code node
between the Set node and the next step; the wiring is documented in
[`examples/n8n/alert_triage/README.md`](../../examples/n8n/alert_triage/README.md)
under *Per-action wiring notes — CORE bodies*.

### 4.2 Temporal — `@activity.defn` bodies with retry policy

`examples/temporal/alert_triage/workflow.temporal.py` is a standard
Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action. All eight activities
import their primitive and produce the canonical payload / seen key /
priority verdict / response directive; the only remaining
`NotImplementedError` marks the operator-integration seam (connector
wiring) so an integrator sees exactly which seam is theirs.

Operators drop `workflow.temporal.py` next to their worker, register
the activities, and run the worker against their Temporal cluster.
The sibling `_audit_mirror.py` carries the `AuditRecord` / `AuditTrail`
types — no `compilers.*` import in the emitted artifact, so the worker
module is a self-contained drop-in.

Per-activity retry policies are emitted alongside the activities
(`<ACTIVITY>_RETRY_POLICY`) so the operator can pin them on the
`workflow.execute_activity` call sites in their worker assembly.

### 4.3 LangGraph — `@tool` wrappers + agentic-extension hook

`examples/langgraph/alert_triage/state_bindings.py` carries the
`TypedDict` state, `@tool`-decorated action wrappers, and an
`AGENTIC_HOOK` slot for an LLM-driven node. `graph_spec.json` carries
the target-neutral topology (nodes, edges, conditional edges).
`assemble.py` is the canonical reference assembly that wires the spec
into a `StateGraph`.

All eight tools import their primitive and update the typed state;
the operator-integration seams stay marked with `NotImplementedError`
for the operator to wire, or any node can be swapped for an
LLM-driven callable that fills the agentic hook.

The agentic-extension slot is provider-neutral by construction: the
compiler never embeds an LLM SDK, so the operator wires the hook to
self-hosted open-weights inference or to an EU-hosted managed
endpoint without regenerating the artifact. The framework-wide
EU-resident LM endpoint guard re-applies the check at process startup
(`_lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 5. Observability — OTel + AuditTrail in every target

Every emitted action opens an OpenTelemetry
span and appends an `AuditRecord` to a context-local `AuditTrail`
*before* the primitive call or the `NotImplementedError`. The mirror
runs unconditionally, ahead of any OTLP exporter, so the audit
property holds even when the operator has not configured a collector
— typical for disconnected, sovereign, or air-gapped deployments.

Span attributes use the shared `secops_ng.*` keyspace and are stable
across the three targets:

| Attribute key                | Carries                                              |
|------------------------------|------------------------------------------------------|
| `secops_ng.playbook.id`      | CACAO playbook id (`playbook--…`).                   |
| `secops_ng.playbook.version` | Content version pinned in the playbook.              |
| `secops_ng.step.id`          | CACAO step id (`action--…`).                         |
| `secops_ng.step.name`        | Human-readable step label.                           |
| `secops_ng.step.type`        | CACAO step type (`action`, `if-condition`, …).       |
| `secops_ng.tool.name`        | Emitted tool / activity / Code-node function name.   |
| `secops_ng.compile.target`   | `n8n` / `temporal` / `langgraph` discriminator.      |

Span boundaries per target:

- **n8n** — the compiled workflow is a snapshot of intent; OTel
  instrumentation is a per-node operator concern, documented per
  node-id, not a runtime guarantee of the emitted JSON.
- **Temporal** — workflow span (`workflow.<stable_id>`) at workflow
  entry; activity span (`activity.<step_id>`) on every activity body,
  with retries opening a fresh child span per Temporal attempt.
- **LangGraph** — node span (`node.<step_id>`) wrapping every node
  assembled in `assemble.py`; tool span (`tool.<step_id>`) inside the
  `@tool` wrapper. The node span is the parent of the tool span so a
  trace shows one `node.*` per step with the matching `tool.*` child.

The OTLP exporter endpoint is operator-supplied (`OTEL_EXPORTER_OTLP_ENDPOINT`).
The compiler never sets a default endpoint and never imports a vendor
SDK; pointing the exporter at a managed APM is a downstream choice
the operator owns end-to-end. The sovereignty posture asks for an
EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline.

## 6. Replay and audit story

The byte-parity drift guards under `tests/examples/alert_triage/` pin
each committed worked example to a fresh emitter run from the
canonical CACAO source. If the compiler or the playbook changes,
regenerate via the per-target `regenerate.sh` and commit the diff
intentionally; the drift guard flips green again.

The cross-target replay property is the harder one: the same alert,
fed through n8n / Temporal / LangGraph, produces a byte-identical
case because the bound CORE bodies are the same Python functions
called through three different idioms. The
`PriorityVerdict.inputs_digest` is the single string a regulator can
diff to confirm the property held.

## 7. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys.
  Connectors are operator-bound at runtime against environment
  variables documented per target.
- **Deployment topology.** Worker concurrency, retry policies beyond
  the per-activity defaults, persistence backends, n8n hosting,
  LangGraph host process model — those are runtime concerns the
  operator applies in their own assembly.
- **Detection rules.** Detection-rule references are pinned upstream
  in the canonical CACAO source via `x_secops_ng.detection_refs`; no
  detection rules are authored in this repository.
- **Suppression-window length, prioritisation policy values.** Those
  are pinned in `primitives.suppression` and
  `primitives.prioritisation` so the policy is the same across
  targets. Operators who diverge fork the primitive module rather
  than overriding at runtime.
- **Per-deployment YAML.** This playbook ships no separate
  operator-facing `config.yaml`; per-case inputs are the CACAO
  `playbook_variables` block bound at compile time via the standard
  `__double_underscore__` substitution.

## 8. References

- [`content/playbooks/alert_triage.cacao.yaml`](../../content/playbooks/alert_triage.cacao.yaml)
  — canonical CACAO source.
- [`content/playbooks/alert_triage/README.md`](../../content/playbooks/alert_triage/README.md)
  — workflow-local module tree.
- [`examples/n8n/alert_triage/README.md`](../../examples/n8n/alert_triage/README.md)
- [`examples/temporal/alert_triage/README.md`](../../examples/temporal/alert_triage/README.md)
- [`examples/langgraph/alert_triage/README.md`](../../examples/langgraph/alert_triage/README.md)
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
