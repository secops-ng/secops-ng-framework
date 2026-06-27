# ddos_response — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the ddos_response CACAO playbook. It is aimed at an integrator who
already runs LangGraph and wants to adopt a portable SecOps-NG playbook
without re-platforming: the example shows exactly which artifacts the
compiler produces, how they fit together, and where the integrator owns
the seams.

This worked example closes the cross-target parity ring (target 3 of 3)
for the `ddos_response` playbook (NIS2 Art.21(2)(b)). The Temporal and
n8n siblings ship under `../../temporal/ddos_response/` and
`../../n8n/ddos_response/`; together the three folders pin the full
three-target contract for this playbook.

## Files in this directory

| File | Role |
|------|------|
| `playbook.cacao.json` | Portable CACAO v2 playbook — byte-identical mirror of `content/playbooks/ddos_response/playbook.cacao.json`, the input to the compiler. |
| `graph_spec.json` | Target-neutral GraphSpec (nodes, edges, conditional edges) emitted by `compilers.langgraph.emit`. |
| `state_bindings.py` | Generated `TypedDict` state + `@tool`-decorated action wrappers + agentic-extension hook, emitted by `compilers.langgraph.state`. |
| `assemble.py` | Hand-written reference assembly that wires the GraphSpec + bindings into a `langgraph.graph.StateGraph`. |
| `regenerate.sh` | Re-runs both emitters from the canonical playbook and overwrites the mirrored CACAO + the two generated artifacts. |

## How to regenerate

After any change to the canonical playbook or to `compilers/langgraph/*`,
refresh the committed artifacts from the repo root:

```bash
./examples/langgraph/ddos_response/regenerate.sh
```

The script mirrors the canonical CACAO source into this folder and
re-emits `graph_spec.json` and `state_bindings.py` from it using
`compilers.langgraph.emit` and `compilers.langgraph.state`. A drift
test in `tests/examples/langgraph/ddos_response/` fails the suite if
the committed artifacts diverge from a fresh regeneration, so the
worked example stays honest as the compiler evolves.

## Cross-target pointers

The same canonical playbook ships under the other two reference compile
targets so an integrator can compare lowerings side by side:

- [`examples/n8n/ddos_response/`](../../n8n/ddos_response/) — n8n no-code workflow.
- [`examples/temporal/ddos_response/`](../../temporal/ddos_response/) — Temporal durable workflow stub.

## Topology

The ddos_response playbook is a linear detect-classify-mitigate-validate
chain with no conditional branching at the workflow layer. Six
GraphSpec action nodes, one per CACAO action step:

1. `detect availability anomaly` — entry point. Detect an availability
   anomaly on a monitored service from the operator's availability
   telemetry feed.
2. `classify attack vector` — classify the attack dimension
   (volumetric, protocol, application-layer) so the mitigation step can
   engage the right discipline.
3. `engage mitigation` — engage the operator's pre-bound response
   surface (upstream scrubbing, rate-limit / WAF posture change,
   failover to a documented standby).
4. `validate service restoration` — validate the protected service has
   been restored against documented availability objectives.
5. `evidence capture` — persist a dated incident-attestation record
   covering anomaly signal, classified vector, mitigation engaged, and
   restoration outcome.
6. `notify incident-management owner` — surface the attestation to the
   incident-management owner via the operator's notification channel.

Because the playbook is linear, the emitted GraphSpec has no
`conditional_edges`; every edge is an unconditional `on_completion`
hand-off. The conditional-edge router pattern documented in
`assemble.py` is still imported and exercised for parity with the
other LangGraph worked examples — it is a no-op for this playbook but
makes the assembly file copy-paste-ready for playbooks that do branch.

## What this example deliberately doesn't do

- It does not execute the graph. The `@tool` bodies raise
  `NotImplementedError`; integrators wire them to their own runtime
  (availability-anomaly detector, attack-vector classifier,
  mitigation-engagement surface, service-restoration probe, evidence
  store, notification channel).
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
