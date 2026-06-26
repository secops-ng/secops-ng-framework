# mfa_secured_comms — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the mfa_secured_comms CACAO playbook. It is aimed at an
integrator who already runs LangGraph and wants to adopt a portable
SecOps-NG playbook without re-platforming: the example shows exactly
which artifacts the compiler produces, how they fit together, and where
the integrator owns the seams.

This worked example pins the LangGraph leg (target 3 of 3) of the
cross-target parity lane for the `mfa_secured_comms` playbook
(NIS2 Art.21(2)(j)). The Temporal and n8n siblings already ship under
`../../temporal/mfa_secured_comms/` and `../../n8n/mfa_secured_comms/`;
together the three folders pin the full three-target contract for this
playbook.

## Files in this directory

| File | Role |
|------|------|
| `playbook.cacao.json` | Portable CACAO v2 playbook — byte-identical mirror of `content/playbooks/mfa_secured_comms/playbook.cacao.json`, the input to the compiler. |
| `graph_spec.json` | Target-neutral GraphSpec (nodes, edges, conditional edges) emitted by `compilers.langgraph.emit`. |
| `state_bindings.py` | Generated `TypedDict` state + `@tool`-decorated action wrappers + agentic-extension hook, emitted by `compilers.langgraph.state`. |
| `assemble.py` | Hand-written reference assembly that wires the GraphSpec + bindings into a `langgraph.graph.StateGraph`. |
| `regenerate.sh` | Re-runs both emitters from the canonical playbook and overwrites the mirrored CACAO + the two generated artifacts. |

## How to regenerate

After any change to the canonical playbook or to `compilers/langgraph/*`,
refresh the committed artifacts from the repo root:

```bash
./examples/langgraph/mfa_secured_comms/regenerate.sh
```

The script mirrors the canonical CACAO source into this folder and
re-emits `graph_spec.json` and `state_bindings.py` from it using
`compilers.langgraph.emit` and `compilers.langgraph.state`. A drift
test in `tests/examples/langgraph/mfa_secured_comms/` fails the suite
if the committed artifacts diverge from a fresh regeneration, so the
worked example stays honest as the compiler evolves.

## Cross-target pointers

The same canonical playbook ships under the other two reference compile
targets so an integrator can compare lowerings side by side:

- [`examples/n8n/mfa_secured_comms/`](../../n8n/mfa_secured_comms/) — n8n no-code workflow.
- [`examples/temporal/mfa_secured_comms/`](../../temporal/mfa_secured_comms/) — Temporal durable workflow stub.

## Topology

The mfa_secured_comms playbook is a linear evaluate-and-attest chain
with no conditional branching at the workflow layer: probe, assess,
verify, attest, notify. Seven GraphSpec nodes, one per CACAO step:

1. `mfa_secured_comms_start` — entry point matching the CACAO `start`
   step. Carries the workflow-scope variables (`__posture_window__`,
   `__auth_scope__`, …) the operator's scheduler or operator-initiated
   trigger supplies.
2. `probe mfa coverage` — probe the identity-provider surface to
   confirm MFA coverage across in-scope principals.
3. `assess continuous auth` — assess whether continuous-authentication
   signals are observed on long-lived sessions.
4. `verify oob channels` — verify the out-of-band emergency
   communications channel is reachable independently of the primary
   information-system path.
5. `evidence capture` — persist a dated posture-attestation record
   covering MFA coverage, continuous-auth, and OOB reachability.
6. `notify authentication owner` — surface the attestation to the
   authentication owner via the operator's notification channel.
7. `mfa_secured_comms_end` — end sentinel.

Because the playbook is linear, the emitted GraphSpec has no
`conditional_edges`; every edge is an unconditional `on_completion`
hand-off. The conditional-edge router pattern documented in
`assemble.py` is still imported and exercised for parity with the
other LangGraph worked examples — it is a no-op for this playbook but
makes the assembly file copy-paste-ready for playbooks that do branch.

## What this example deliberately doesn't do

- It does not execute the graph. The `@tool` bodies raise
  `NotImplementedError`; integrators wire them to their own runtime
  (identity-provider probe, continuous-auth assessor, OOB-channel
  verifier, evidence store, notification channel).
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
