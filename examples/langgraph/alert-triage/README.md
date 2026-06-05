# alert-triage — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the alert-triage CACAO source playbook. It is aimed at an
integrator who already runs LangGraph and wants to adopt the portable
SecOps-NG alert-triage playbook without re-platforming: the example
shows exactly which artifacts the compiler produces, how they fit
together, and where the integrator owns the seams.

The seven CORE action steps with a primitives binding (ingest, enrich,
suppress, classify, p1 / p2 / p3 response) emit `@tool` wrappers that
import the deterministic primitive directly; the single absent-body
step (p4 informational — log and close) emits a `@tool` wrapper that
opens the span, appends the audit record, and raises
`NotImplementedError` so the seam is visible at a glance.

## Files in this directory

| File | Role |
|------|------|
| `playbook.cacao.json` | Portable CACAO v2 playbook — byte-deterministic JSON mirror of `content/playbooks/alert-triage.cacao.yaml`, the canonical source. The mirror exists because the LangGraph emitter consumes JSON; the two formats round-trip through `yaml.safe_load` + `json.dumps`. |
| `graph_spec.json` | Target-neutral GraphSpec (nodes, edges, conditional edges) emitted by `compilers.langgraph.emit`. |
| `state_bindings.py` | Generated `TypedDict` state + `@tool`-decorated action wrappers + agentic-extension hook, emitted by `compilers.langgraph.state`. |
| `_audit_mirror.py` | Dependency-free `AuditTrail` / `AuditRecord` sibling — materialised by the compiler so the worked example is a self-contained drop-in. |
| `assemble.py` | Hand-written reference assembly that wires the GraphSpec + bindings into a `langgraph.graph.StateGraph`. |
| `regenerate.sh` | Re-mirrors the canonical YAML source to `playbook.cacao.json` and re-runs both emitters plus the audit-mirror materialiser. |

## How to regenerate

After any change to the canonical YAML source or to `compilers/langgraph/*`,
refresh the committed artifacts from the repo root:

```bash
./examples/langgraph/alert-triage/regenerate.sh
```

The script mirrors the canonical CACAO YAML into the JSON form this
folder commits, then re-emits `graph_spec.json` and `state_bindings.py`
from it using `compilers.langgraph.emit` and `compilers.langgraph.state`,
and re-materialises `_audit_mirror.py` via
`compilers._shared.audit_mirror_cli`. A drift test in
`tests/examples/alert_triage/` fails the suite if the committed
artifacts diverge from a fresh regeneration, so the worked example
stays honest as the compiler evolves.

## Wiring it into your runtime

`assemble.py` is the canonical reference. The pattern in ~10 lines:

1. Load `graph_spec.json` with `load_graph_spec()` — pure JSON, no
   runtime dependency.
2. Pick the generated `TypedDict` off `state_bindings` and pass it to
   `StateGraph(state_cls)`.
3. For each `node` in `spec["nodes"]`, call `graph.add_node(step_id,
   tool_fn)`. The `@tool`-decorated wrappers on `state_bindings` are
   the default binding; an integrator can swap any node for an
   LLM-driven callable that uses the `AGENTIC_HOOK` slot instead.
4. `graph.set_entry_point(spec["entry"])`.
5. For each plain edge in `spec["edges"]`, call `graph.add_edge(src,
   dst)` (mapping the `__END__` sentinel to LangGraph's `END`).
6. For each entry in `spec["conditional_edges"]`, build a router with
   `make_router(cond)` and call
   `graph.add_conditional_edges(src, router, path_map)`.
7. `graph.compile()` — the runtime is now ready to invoke.

The router pattern is shared across every LangGraph worked example in
this repository: the preceding action writes a status into
`State['step_status'][step_id]`, and the router maps that status onto
the CACAO branch label. For alert-triage:

* the `if-condition` after `enrich` reads the suppression decision
  (`success` → suppress-and-close, `failure` → classify-and-prioritise);
* the `switch-condition` after classification reads the priority bucket
  (`p1_severe`, `p2_high`, `p3_routine`, `p4_informational`) and routes
  to the matching response action.

Unknown / missing status falls through to the spec's `default` (or
`__END__`), so a misbehaving classifier terminates the run rather than
dead-locking.

## What this example deliberately doesn't do

- It does not execute the absent-body p4 log-and-close tool. The
  body raises `NotImplementedError`; integrators wire it to their
  telemetry-coverage / false-positive accounting sink.
- It does not ship operator credentials, endpoints, or environment.
  Secrets stay with the operator.
- It does not pick an LLM provider for the agentic-extension hook.
  `AGENTIC_HOOK` is a documented placeholder; the operator chooses a
  provider that matches their sovereignty posture at integration time.
- It does not bind a specific runtime topology (retry policy,
  concurrency, persistence backend). Those are runtime concerns the
  integrator applies in their own assembly.

## Observability — OTel spans emitted by default

The LangGraph reference compiler emits this worked example already
wrapped in OpenTelemetry instrumentation; an operator who runs the
compiled artifact gets traces without writing any glue.

Two span layers are emitted for every action step:

- **Tool span — `tool.<step_id>`.** Each `@tool`-decorated wrapper in
  `state_bindings.py` opens
  `tracer.start_as_current_span("tool.<step_id>", attributes={...})`
  around its body. The wrapper is what runs whether the integrator
  binds the tool directly or routes through an LLM-driven `ToolNode`,
  so the span is opened regardless of the upstream caller.
- **Node span — `node.<step_id>`.** Every node assembled in
  `assemble.py` is wrapped in `node.<step_id>` via the local
  `_wrap_node_span` helper before being handed to
  `StateGraph.add_node`. The node span is the parent of the tool span
  inside it, so a trace shows one `node.*` per LangGraph step with the
  matching `tool.*` child.

Span attributes use the shared `secops_ng.*` keyspace and are stable
across reference compilers (LangGraph, Temporal, n8n):

| Attribute key                | Carries                                              |
|------------------------------|------------------------------------------------------|
| `secops_ng.playbook.id`      | CACAO playbook id (`playbook--…`).                   |
| `secops_ng.step.id`          | CACAO step id (`action--…`).                         |
| `secops_ng.step.name`        | Human-readable step label from the playbook.         |
| `secops_ng.tool.name`        | Emitted tool / activity function name.               |
| `secops_ng.workflow.run_id`  | Run-id placeholder; empty string until the host runtime binds one. |

### Audit-trail mirror — offline / air-gapped

Each span the compiled module opens also appends an `AuditRecord` to a
context-local `AuditTrail` in the sibling `_audit_mirror.py`. The mirror
runs unconditionally, *before* any OTLP exporter is involved, so the
audit property holds even when the operator has not configured a
collector — typical for disconnected, sovereign, or air-gapped
deployments where OTLP egress is unavailable. See
[../../../docs/observability/audit-mirror.md](../../../docs/observability/audit-mirror.md)
for the co-location decision, the JSONL replay envelope, and the
snapshot API used to drain a trail offline.

### Operator configuration

The compiled artifact reads the standard OpenTelemetry environment
variables; nothing is hard-coded. The minimum the operator wires:

```sh
# OTLP collector — operator-provided. No default endpoint is set by
# the compiled artifact; if unset, spans are dropped and the audit
# mirror is the sole audit record.
export OTEL_EXPORTER_OTLP_ENDPOINT="https://otel.collector.example.eu:4317"
export OTEL_SERVICE_NAME="alert-triage"
```

Sovereign-stack note: the collector should be EU-resident. Reference
choices include Grafana Alloy on Hetzner, OTLP → Tempo on Scaleway, or
an OVHcloud / Nebul-hosted collector — anything in operator-controlled
EU infrastructure works; `us-*` regional endpoints do not meet the
project's sovereignty posture.

The compiled artifact also stays provider-neutral by construction: the
emitter never imports a vendor SDK and never sets a default endpoint
that routes outside the operator's control. Pointing the OTLP exporter
at a managed APM is a downstream configuration choice the operator
owns end-to-end.

## Per-tool wiring notes — CORE bodies

The eight CORE action steps split into two emission shapes depending
on whether the canonical CACAO step declares an `x_secops_ng.core_body`
reference into the deterministic primitives package under
`content/playbooks/alert-triage/primitives/`:

- **`core_body` set (ingest, enrich, suppress, classify, p1 / p2 / p3
  response).** The `@tool`-decorated wrapper in `state_bindings.py`
  imports the primitive and produces the canonical alert payload /
  seen key / priority verdict / response directive (e.g.
  `validate_alert_payload(raw=..., source_shape=...)`,
  `canonical_seen_key(...)`,
  `prioritise(detection_class=..., detection_severity=...,
  context=..., correlates_open_case=...)`,
  `escalation_route(...) / notify_on_call(...) /
  route_to_review_queue(...)`). Same Python functions called from n8n
  and Temporal; same `PriorityVerdict.inputs_digest` on every target.
- **`core_body` absent (p4 informational — log and close).** The
  `@tool` body opens the tool span, appends the `AuditRecord`, and
  then `raise NotImplementedError`. Integrator fills the body in
  against their telemetry-coverage / false-positive accounting sink
  — the seam is visible at a glance.

Operators can swap any node for an LLM-driven callable that fills the
`AGENTIC_HOOK` slot instead of using the `@tool` wrapper directly;
the wrapper is what runs whether the integrator binds the tool or
routes through a `ToolNode`, so the span is opened regardless of the
upstream caller.

## Primitives contract

The priority bands, the suppression-window length, the canonical
seen-key shape, the typed alert payload schema, and the DSPy signature
schema for free-text fields are **code, not configuration**. They live
under `content/playbooks/alert-triage/primitives/`:

| Module             | What it pins                                                                       |
|--------------------|------------------------------------------------------------------------------------|
| `payloads.py`      | `validate_alert_payload(raw, source_shape) → AlertPayload`; two source shapes.     |
| `suppression.py`   | `canonical_seen_key(...)` + `SuppressionWindow` sliding-window membership.         |
| `prioritisation.py`| `prioritise(detection_class, detection_severity, context, correlates_open_case) → PriorityVerdict`. |
| `response.py`      | `escalation_route` + `notify_on_call` + `route_to_review_queue` deterministic directives. |
| `signatures.py`    | DSPy signature for free-text fields only — never the priority decision.            |

Operators who need to diverge fork the primitive module; they do not
override it via runtime config.

## Operator runtime hand-off contract

The LangGraph reference compiler emits a target-neutral GraphSpec,
the generated `TypedDict` state + `@tool` wrappers, and a hand-written
reference `assemble.py`. The hand-off boundary:

| The framework ships                          | The operator owns                                            |
|----------------------------------------------|--------------------------------------------------------------|
| `graph_spec.json` topology (nodes, edges, conditional edges) | LangGraph host process (self-hosted, EU-resident). |
| `TypedDict` state and `@tool` wrappers       | Connector credentials and endpoints.                         |
| `core_body` bodies for ingest, enrich, suppress, classify, p1 / p2 / p3 response | Telemetry-coverage / false-positive accounting sink (for p4 log-and-close). |
| `NotImplementedError` stub for absent-body p4 log-and-close | LLM provider choice for the `AGENTIC_HOOK` slot (EU-resident or open-weights). |
| Generated `_lm_endpoint_guard.py` runtime check | Acknowledged non-EU opt-out (`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK=1`) if applicable. |
| `_audit_mirror.py` co-located AuditTrail     | OTel exporter endpoint (EU-resident collector).              |
| Cross-target replay determinism via shared primitives | Suppression window length, prioritisation thresholds — forked in `primitives/` rather than overridden at runtime. |

The walkthrough in
[`../../../docs/cookbook/alert-triage.md`](../../../docs/cookbook/alert-triage.md)
reads this end-to-end alongside the n8n and Temporal targets.

## Sovereignty note

LangGraph is open source (MIT) and runs as a Python process: hosting
it on EU sovereign infrastructure (Nebul, OVHcloud, Scaleway, Hetzner)
is a deployment choice, not a vendor decision. The agentic-extension
hook is provider-neutral by design — the compiler never embeds an LLM
SDK, so the operator can wire it to self-hosted open-weights inference
or to an EU-hosted managed endpoint without regenerating the artifact.
See [docs/compilers/langgraph.md](../../../docs/compilers/langgraph.md)
and [docs/sovereignty/](../../../docs/sovereignty/) for the full
posture.

## EU-resident LM endpoint guard

This worked example inherits the framework-wide default that any LM
endpoint reachable from the compiled artifact lives in the European
Union. The check runs both at compile time (the reference compiler
fails fast on a non-EU endpoint when emitting this example) and at
runtime (a generated `_lm_endpoint_guard.py` sibling re-applies the
check at process startup). An operator who deliberately wires a non-EU
endpoint must set `SECOPS_NG_LM_ENDPOINT_NON_EU_ACK=1` in the
environment to acknowledge the trade-off; the workflow then loses its
EU-residency posture and should document that fact in the operator's
own deployment notes. See
[docs/sovereignty/eu-resident-lm-guard.md](../../../docs/sovereignty/eu-resident-lm-guard.md)
for the heuristic, the override, and the EU allowlist.
