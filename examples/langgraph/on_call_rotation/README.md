# on_call_rotation — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the on_call_rotation CACAO playbook. It is aimed at an integrator
who already runs LangGraph and wants to adopt a portable SecOps-NG
playbook without re-platforming: the example shows exactly which
artifacts the compiler produces, how they fit together, and where the
integrator owns the seams.

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
./examples/langgraph/on_call_rotation/regenerate.sh
```

The script re-emits `graph_spec.json` and `state_bindings.py` from
`playbook.cacao.json` using `compilers.langgraph.emit` and
`compilers.langgraph.state`. A drift test in `tests/examples/` fails
the suite if the committed artifacts diverge from a fresh regeneration,
so the worked example stays honest as the compiler evolves.

## Topology

The on_call_rotation playbook is reentrant and only emits a handoff
brief when a shift-handoff window is active:

1. `load rotation roster` — read the current rotation from the roster
   the operator already maintains (PagerDuty / Opsgenie / spreadsheet
   / wiki — the playbook is source-agnostic).
2. `bind escalation tiers` — bind the primary / secondary / manager
   escalation chain the operator's paging system will fan out through.
   This is the only durable state change in steady state.
3. `shift handoff window?` — an `if-condition` step. A prior step
   writes a status into `state["step_status"][src]`; the router maps
   `success` (inside a handoff window) to the handoff branch and
   `failure` (mid-shift, no handoff due) to the end sentinel.
4. Handoff branch — `generate handoff brief` then
   `notify incoming on-call` chain in sequence, then terminate at the
   end sentinel.

The conditional-edge router pattern is identical to vuln_intake and
identity_compromise; see `assemble.py` for the ~10-line wiring.

## What this example deliberately doesn't do

- It does not execute the graph. The `@tool` bodies raise
  `NotImplementedError`; integrators wire them to their own runtime
  (roster source, paging system, ticketing, notifier).
- It does not ship operator credentials, endpoints, or environment.
  Secrets stay with the operator.
- It does not pick an LLM provider for the agentic-extension hook.
  `AGENTIC_HOOK` is a documented placeholder; the operator chooses a
  provider that matches their sovereignty posture at integration time.
- It does not bind a specific runtime topology (retry policy,
  concurrency, persistence backend, schedule). Those are runtime
  concerns the integrator applies in their own assembly.

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
