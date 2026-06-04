# vuln-intake — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the vulnerability intake CACAO playbook. It is aimed at an
integrator who already runs LangGraph and wants to adopt a portable
SecOps-NG playbook without re-platforming: the example shows exactly
which artifacts the compiler produces, how they fit together, and
where the integrator owns the seams.

## Files in this directory

| File | Role |
|------|------|
| `playbook.cacao.json` | Portable CACAO v2 playbook — the input to the compiler. |
| `graph_spec.json` | Target-neutral GraphSpec (nodes, edges, conditional edges) emitted by `compilers.langgraph.emit`. |
| `state_bindings.py` | Generated `TypedDict` state + `@tool`-decorated action wrappers + agentic-extension hook, emitted by `compilers.langgraph.state`. |
| `assemble.py` | Hand-written reference assembly that wires the GraphSpec + bindings into a `langgraph.graph.StateGraph`. |
| `regenerate.sh` | Re-runs both emitters from the playbook and overwrites the two generated artifacts. |

## How to regenerate

After any change to the playbook or to `compilers/langgraph/*`, refresh
the committed artifacts from the repo root:

```bash
./examples/langgraph/vuln-intake/regenerate.sh
```

The script re-emits `graph_spec.json` and `state_bindings.py` from
`playbook.cacao.json` using `compilers.langgraph.emit` and
`compilers.langgraph.state`. A drift test in
`tests/examples/langgraph/` fails the suite if the committed artifacts
diverge from a fresh regeneration, so the worked example stays
honest as the compiler evolves.

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
   `graph.add_conditional_edges(src, router, branches)`. The router
   reads `state["step_status"][src]` and maps the CACAO branch label
   (`success` / `failure` for `if-condition`, `case_<i>` for
   `switch-condition`) to the successor node; a missing or unknown
   status falls through to the conditional's `default` (or
   terminates).
7. `graph.compile()` — the runtime is now ready to invoke.

## What this example deliberately doesn't do

- It does not execute the graph. The `@tool` bodies raise
  `NotImplementedError`; integrators wire them to their own runtime.
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
| `secops_ng.playbook.id`      | CACAO playbook id (e.g. `playbook--…`).              |
| `secops_ng.step.id`          | CACAO step id (e.g. `action--…`).                    |
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
export OTEL_SERVICE_NAME="vuln-intake"
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
