# executive_metrics — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the executive_metrics CACAO playbook. It is aimed at an integrator
who already runs LangGraph and wants to adopt a portable SecOps-NG
playbook without re-platforming: the example shows exactly which
artifacts the compiler produces, how they fit together, and where the
integrator owns the seams.

## Files in this directory

| File | Role |
|------|------|
| `playbook.cacao.json` | Portable CACAO v2 playbook — byte-identical mirror of `content/playbooks/executive_metrics/playbook.cacao.json`, the input to the compiler. |
| `graph_spec.json` | Target-neutral GraphSpec (nodes, edges, conditional edges) emitted by `compilers.langgraph.emit`. |
| `state_bindings.py` | Generated `TypedDict` state + `@tool`-decorated action wrappers + agentic-extension hook, emitted by `compilers.langgraph.state`. |
| `assemble.py` | Hand-written reference assembly that wires the GraphSpec + bindings into a `langgraph.graph.StateGraph`. |
| `regenerate.sh` | Re-runs both emitters from the canonical playbook and overwrites the mirrored CACAO + the two generated artifacts. |

## How to regenerate

After any change to the canonical playbook or to `compilers/langgraph/*`,
refresh the committed artifacts from the repo root:

```bash
./examples/langgraph/executive_metrics/regenerate.sh
```

The script mirrors the canonical CACAO source into this folder and
re-emits `graph_spec.json` and `state_bindings.py` from it using
`compilers.langgraph.emit` and `compilers.langgraph.state`. A drift
test in `tests/examples/executive_metrics/test_langgraph_workflow.py`
fails the suite if the committed artifacts diverge from a fresh
regeneration, so the worked example stays honest as the compiler
evolves.

## Cross-target pointers

The same canonical playbook ships under the other two reference compile
targets so an integrator can compare lowerings side by side:

- [`examples/n8n/executive_metrics/`](../../n8n/executive_metrics/) — n8n no-code workflow.
- [`examples/temporal/executive_metrics/`](../../temporal/executive_metrics/) — Temporal durable workflow stub.

## Topology

The executive_metrics playbook is a periodic KPI/KRI rollup that
branches once on whether any breach band was hit:

1. `resolve KPI/KRI catalog` — load the catalogue of executive metrics
   the operator publishes to their board.
2. `evaluate metrics over window` — compute the configured metrics over
   the reporting window from whichever upstream data lake / SIEM the
   operator already runs.
3. `score control effectiveness` — derive control-effectiveness scores
   from the evaluated metrics.
4. `any breach band hit?` — an `if-condition` step. The scoring step
   writes a status into `state["step_status"][src]`; the router maps
   `success` (at least one breach band hit) to `raise board-attention
   flag` and `failure` (all bands green) straight to `emit board
   summary`.
5. Both branches converge on `emit board summary` and then the end
   sentinel.

The conditional-edge router pattern is identical to vuln_intake and
identity_compromise; see `assemble.py` for the ~10-line wiring.

## What this example deliberately doesn't do

- It does not execute the graph. The `@tool` bodies raise
  `NotImplementedError`; integrators wire them to their own runtime
  (data lake, SIEM, metrics store, board-reporting channel).
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
