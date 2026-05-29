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
