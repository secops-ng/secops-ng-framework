# data_exfil — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the data_exfil CACAO playbook. It is aimed at an integrator who
already runs LangGraph and wants to adopt a portable SecOps-NG playbook
without re-platforming: the example shows exactly which artifacts the
compiler produces, how they fit together, and where the integrator owns
the seams.

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
./examples/langgraph/data_exfil/regenerate.sh
```

The script re-emits `graph_spec.json` and `state_bindings.py` from
`playbook.cacao.json` using `compilers.langgraph.emit` and
`compilers.langgraph.state`. A byte-pinned golden test in
`tests/compilers/langgraph/` fails the suite if the emitter output drifts
from the committed artifacts, so the worked example stays honest as the
compiler evolves.

## Entry point

The compiler walks the CACAO `workflow_start` reference. For this
playbook that points at the first action — `triage signal` — so the
emitted `graph_spec.entry` is the `triage signal` node id, not the
synthetic CACAO `start` step (start/end are not materialised as
LangGraph nodes; they collapse into the entry point and `__END__`
sentinel respectively).

## Topology

The data_exfil playbook branches twice:

1. `triage signal` — initial collection from EDR, DLP, and any
   anomaly-detection feed the operator already runs.
2. `scope assessment` — quantify blast radius (records, systems, data
   classes affected) before deciding on containment.
3. `exfil confirmed?` — an `if-condition` step. The preceding action
   writes a status into `state["step_status"][src]`; the router maps
   `success` (exfil confirmed) to the containment branch and `failure`
   (false positive) to the end sentinel.
4. `containment` — isolate affected systems / revoke leaked credentials
   / block egress.
5. `regulator notification threshold met?` — a second `if-condition`
   step gating the regulatory-notification path. `success` chains
   through `notify regulator` then `notify affected party`; `failure`
   skips regulator notification and goes straight to
   `notify affected party`.

The conditional-edge router pattern is identical to vuln_intake and
identity_compromise; see `assemble.py` for the ~10-line wiring.

## What this example deliberately doesn't do

- It does not execute the graph. The `@tool` bodies raise
  `NotImplementedError`; integrators wire them to their own runtime
  (EDR, DLP, ticketing, SIEM, regulatory-notification channel).
- It does not ship operator credentials, endpoints, or environment.
  Secrets stay with the operator.
- It does not pick an LLM provider for the agentic-extension hook.
  `AGENTIC_HOOK` is a documented placeholder; the operator chooses a
  provider that matches their sovereignty posture at integration time.
- It does not encode a specific regulatory regime. The
  `regulator notification threshold met?` condition is intentionally
  abstract — the integrator wires the threshold to whichever
  jurisdiction-specific obligation applies (NIS2 Art. 23, GDPR Art. 33,
  DORA Art. 19, sector-specific, etc.).
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
