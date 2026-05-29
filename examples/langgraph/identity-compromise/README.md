# identity-compromise — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the identity-compromise CACAO playbook. It is aimed at an integrator
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
./examples/langgraph/identity-compromise/regenerate.sh
```

The script re-emits `graph_spec.json` and `state_bindings.py` from
`playbook.cacao.json` using `compilers.langgraph.emit` and
`compilers.langgraph.state`. A drift test in `tests/examples/` fails
the suite if the committed artifacts diverge from a fresh regeneration,
so the worked example stays honest as the compiler evolves.

## Topology

The identity-compromise playbook branches on the triage outcome:

1. `triage identity signal` — collect signals from the IdP, EDR, and
   any anomaly-detection feed the operator already runs.
2. `compromise confirmed?` — an `if-condition` step. The triage step
   writes a status into `state["step_status"][src]`; the router maps
   `success` (compromise confirmed) to the containment branch and
   `failure` (false positive) to the false-positive end sentinel.
3. Containment branch — `reset MFA factors`, `revoke active sessions`,
   `lateral-movement hunt`, `IAM audit and persistence removal` chain
   in sequence, then terminate at the main end sentinel.

The conditional-edge router pattern is identical to vuln-intake; see
`assemble.py` for the ~10-line wiring.

## What this example deliberately doesn't do

- It does not execute the graph. The `@tool` bodies raise
  `NotImplementedError`; integrators wire them to their own runtime
  (IdP, EDR, ticketing, SIEM).
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
