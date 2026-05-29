# threat-intel-ingest — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the threat-intel-ingest CACAO playbook. It is aimed at an integrator
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
./examples/langgraph/threat-intel-ingest/regenerate.sh
```

The script re-emits `graph_spec.json` and `state_bindings.py` from
`playbook.cacao.json` using `compilers.langgraph.emit` and
`compilers.langgraph.state`. A drift test in `tests/examples/` fails
the suite if the committed artifacts diverge from a fresh regeneration,
so the worked example stays honest as the compiler evolves.

## Topology

The threat-intel-ingest playbook branches on indicator confidence:

1. `pull upstream feed` — poll the upstream TAXII collection or STIX
   bundle endpoint (sovereign / community feed of the operator's
   choosing — an ENISA CSIRTs-network feed, a national CSIRT
   bulletin, a community MISP instance).
2. `normalise STIX to OCSF` — flatten the bundle into the OCSF shape
   the rest of the framework already speaks.
3. `above confidence threshold?` — an `if-condition` step. The
   normalisation step writes a status into `state["step_status"][src]`;
   the router maps `success` (high-confidence indicators present) to
   the propagation branch and `failure` (detection-only) to the
   detection-rule activation.
4. Propagation branch — `propagate to blocklist` then chains into
   `activate detection rule`; the false-branch goes straight to
   `activate detection rule`. Both branches converge so detections are
   always armed.

The conditional-edge router pattern is identical to vuln-intake and
identity-compromise; see `assemble.py` for the ~10-line wiring.

## What this example deliberately doesn't do

- It does not execute the graph. The `@tool` bodies raise
  `NotImplementedError`; integrators wire them to their own runtime
  (TAXII client, OCSF pipeline, SIEM, detection-rule manager).
- It does not ship operator credentials, feed endpoints, or
  environment. Secrets stay with the operator.
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
