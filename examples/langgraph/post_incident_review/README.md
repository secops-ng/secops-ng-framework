# post_incident_review — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the post_incident_review CACAO playbook. It is aimed at an
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
./examples/langgraph/post_incident_review/regenerate.sh
```

The script re-emits `graph_spec.json` and `state_bindings.py` from
`playbook.cacao.json` using `compilers.langgraph.emit` and
`compilers.langgraph.state`. A drift test in `tests/examples/` fails
the suite if the committed artifacts diverge from a fresh regeneration,
so the worked example stays honest as the compiler evolves.

## Topology

The post_incident_review playbook is a linear three-step chain run
after an incident has been closed or contained:

1. `timeline collation` — collate the timeline from the artifacts the
   responders left behind (tickets, chat transcripts, runbook output,
   SIEM exports). Anti-forensics / audit-tampering signals surfaced
   by the upstream Sigma references are flagged here as gaps in the
   log record rather than silently glossed.
2. `blameless review template` — walk a blameless review template
   that separates contributing factors from individual error, so
   downstream reading of the record cannot retroactively reframe
   contributing factors as fault.
3. `corrective action tracking` — emit a corrective-action register
   that downstream tracking (ticketing, governance, audit) can
   consume as durable, restartable state.

There are no conditional branches: the playbook does not re-litigate
the incident, so every run walks the full three-step chain.

## What this example deliberately doesn't do

- It does not execute the graph. The `@tool` bodies raise
  `NotImplementedError`; integrators wire them to their own runtime
  (ticketing, knowledge base, governance register).
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
