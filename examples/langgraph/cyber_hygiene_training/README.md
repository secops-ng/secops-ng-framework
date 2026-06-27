# cyber_hygiene_training — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the cyber_hygiene_training CACAO playbook. It is aimed at an
integrator who already runs LangGraph and wants to adopt a portable
SecOps-NG playbook without re-platforming: the example shows exactly
which artifacts the compiler produces, how they fit together, and where
the integrator owns the seams.

This worked example closes the cross-target parity ring (target 3 of 3)
for the `cyber_hygiene_training` playbook (NIS2 Art.21(2)(g)). The
Temporal and n8n siblings already ship under
`../../temporal/cyber_hygiene_training/` and
`../../n8n/cyber_hygiene_training/`; together the three folders pin
the full three-target contract for this playbook.

## Files in this directory

| File | Role |
|------|------|
| `playbook.cacao.json` | Portable CACAO v2 playbook — byte-identical mirror of `content/playbooks/cyber_hygiene_training/playbook.cacao.json`, the input to the compiler. |
| `graph_spec.json` | Target-neutral GraphSpec (nodes, edges, conditional edges) emitted by `compilers.langgraph.emit`. |
| `state_bindings.py` | Generated `TypedDict` state + `@tool`-decorated action wrappers + agentic-extension hook, emitted by `compilers.langgraph.state`. |
| `assemble.py` | Hand-written reference assembly that wires the GraphSpec + bindings into a `langgraph.graph.StateGraph`. |
| `regenerate.sh` | Re-runs both emitters from the canonical playbook and overwrites the mirrored CACAO + the two generated artifacts. |

## How to regenerate

After any change to the canonical playbook or to `compilers/langgraph/*`,
refresh the committed artifacts from the repo root:

```bash
./examples/langgraph/cyber_hygiene_training/regenerate.sh
```

The script mirrors the canonical CACAO source into this folder and
re-emits `graph_spec.json` and `state_bindings.py` from it using
`compilers.langgraph.emit` and `compilers.langgraph.state`. A drift
test in `tests/examples/langgraph/cyber_hygiene_training/` fails the
suite if the committed artifacts diverge from a fresh regeneration, so
the worked example stays honest as the compiler evolves.

## Cross-target pointers

The same canonical playbook ships under the other two reference compile
targets so an integrator can compare lowerings side by side:

- [`examples/n8n/cyber_hygiene_training/`](../../n8n/cyber_hygiene_training/) — n8n no-code workflow.
- [`examples/temporal/cyber_hygiene_training/`](../../temporal/cyber_hygiene_training/) — Temporal durable workflow stub.

## Topology

The cyber_hygiene_training playbook is a linear inventory-schedule-
exercise-track-attest chain with no conditional branching at the
workflow layer. Eight GraphSpec nodes, one per CACAO step:

1. `cyber_hygiene_training_start` — entry point matching the CACAO
   `start` step. Carries the workflow-scope variables
   (`__training_window__`, `__training_scope__`, …) the operator's
   scheduler or operator-initiated trigger supplies.
2. `inventory training roster` — resolve the in-scope training roster
   from the operator's HR / identity source against the declared
   training scope.
3. `schedule training cycle` — schedule the per-cycle awareness and
   role-based training assignments against the roster snapshot.
4. `run phishing simulation` — run the cycle's phishing-simulation
   exercise; record per-recipient delivery, click, and report-rate
   data. The simulation is a documented exercise and does NOT trigger
   downstream incident response.
5. `track completion` — track completion of mandatory training and
   aggregate per-cohort completion-rate and click/report-rate against
   the declared targets.
6. `evidence capture` — persist a dated cyber-hygiene and
   security-training posture attestation covering the roster snapshot,
   the cycle assignments, the simulation results, and the completion
   tracking.
7. `notify gaps` — surface the attestation and any open gaps to the
   training owner via the operator's notification channel.
8. `cyber_hygiene_training_end` — end sentinel.

Because the playbook is linear, the emitted GraphSpec has no
`conditional_edges`; every edge is an unconditional `on_completion`
hand-off. The conditional-edge router pattern documented in
`assemble.py` is still imported and exercised for parity with the
other LangGraph worked examples — it is a no-op for this playbook but
makes the assembly file copy-paste-ready for playbooks that do branch.

## What this example deliberately doesn't do

- It does not execute the graph. The `@tool` bodies raise
  `NotImplementedError`; integrators wire them to their own runtime
  (training-roster inventory, training-cycle scheduler,
  phishing-simulation exercise runner, completion tracker, evidence
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
