# alert-triage — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the alert-triage CACAO source playbook. It is aimed at an integrator
who already runs LangGraph and wants to adopt the portable SecOps-NG
alert-triage primitive without re-platforming: the example shows
exactly which artifacts the compiler produces, how they fit together,
and where the integrator owns the seams.

This worked example is **SKELETON** — the workflow graph, step ids,
join keys, and the start → ingest → enrich → if(suppress) → classify
→ switch(priority{p1,p2,p3,p4}) → end shape are committed; node bodies
are deliberately stubbed (`NotImplementedError`) so the example compiles
deterministically without any tool or model binding. Real bindings land
in follow-up CORE/EXTEND work against the source playbook.

## Files in this directory

| File | Role |
|------|------|
| `playbook.cacao.json` | Portable CACAO v2 playbook — byte-deterministic JSON mirror of `content/playbooks/alert-triage.cacao.yaml`, the canonical source. The mirror exists because the LangGraph emitter consumes JSON; the two formats round-trip through `yaml.safe_load` + `json.dumps`. |
| `graph_spec.json` | Target-neutral GraphSpec (nodes, edges, conditional edges) emitted by `compilers.langgraph.emit`. |
| `state_bindings.py` | Generated `TypedDict` state + `@tool`-decorated action wrappers + agentic-extension hook, emitted by `compilers.langgraph.state`. |
| `assemble.py` | Hand-written reference assembly that wires the GraphSpec + bindings into a `langgraph.graph.StateGraph`. |
| `regenerate.sh` | Re-mirrors the canonical YAML source to `playbook.cacao.json` and re-runs both emitters. |

## How to regenerate

After any change to the canonical YAML source or to `compilers/langgraph/*`,
refresh the committed artifacts from the repo root:

```bash
./examples/langgraph/alert-triage/regenerate.sh
```

The script mirrors the canonical CACAO YAML into the JSON form this
folder commits, then re-emits `graph_spec.json` and `state_bindings.py`
from it using `compilers.langgraph.emit` and `compilers.langgraph.state`.
A drift test in `tests/examples/alert_triage/` fails the suite if the
committed artifacts diverge from a fresh regeneration, so the worked
example stays honest as the compiler evolves.

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
