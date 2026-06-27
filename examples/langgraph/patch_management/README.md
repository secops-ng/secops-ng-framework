# patch_management — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the patch_management CACAO playbook. It is aimed at an integrator
who already runs LangGraph and wants to adopt a portable SecOps-NG
playbook without re-platforming: the example shows exactly which
artifacts the compiler produces, how they fit together, and where the
integrator owns the seams.

This worked example closes the cross-target parity ring (target 3 of 3)
for the `patch_management` playbook (NIS2 Art.21(2)(e)). The Temporal
and n8n siblings already ship under
`../../temporal/patch_management/` and
`../../n8n/patch_management/`; together the three folders pin the
full three-target contract for this playbook.

## Files in this directory

| File | Role |
|------|------|
| `playbook.cacao.json` | Portable CACAO v2 playbook — byte-identical mirror of `content/playbooks/patch_management/playbook.cacao.json`, the input to the compiler. |
| `graph_spec.json` | Target-neutral GraphSpec (nodes, edges, conditional edges) emitted by `compilers.langgraph.emit`. |
| `state_bindings.py` | Generated `TypedDict` state + `@tool`-decorated action wrappers + agentic-extension hook, emitted by `compilers.langgraph.state`. |
| `assemble.py` | Hand-written reference assembly that wires the GraphSpec + bindings into a `langgraph.graph.StateGraph`. |
| `regenerate.sh` | Re-runs both emitters from the canonical playbook and overwrites the mirrored CACAO + the two generated artifacts. |

## How to regenerate

After any change to the canonical playbook or to `compilers/langgraph/*`,
refresh the committed artifacts from the repo root:

```bash
./examples/langgraph/patch_management/regenerate.sh
```

The script mirrors the canonical CACAO source into this folder and
re-emits `graph_spec.json` and `state_bindings.py` from it using
`compilers.langgraph.emit` and `compilers.langgraph.state`. A drift
test in `tests/examples/langgraph/patch_management/` fails the suite
if the committed artifacts diverge from a fresh regeneration, so the
worked example stays honest as the compiler evolves.

## Cross-target pointers

The same canonical playbook ships under the other two reference compile
targets so an integrator can compare lowerings side by side:

- [`examples/n8n/patch_management/`](../../n8n/patch_management/) — n8n no-code workflow.
- [`examples/temporal/patch_management/`](../../temporal/patch_management/) — Temporal durable workflow stub.

## Topology

The patch_management playbook is a linear detect-classify-stage-validate-
fan-out-evidence-notify chain with no conditional branching at the
workflow layer. Nine GraphSpec nodes, one per CACAO step:

1. `patch_management_start` — entry point matching the CACAO `start`
   step. Carries the workflow-scope variables the operator's update
   channel or maintenance-window scheduler supplies.
2. `detect patch availability` — detect that a security update is
   available against a tracked package / image / firmware line on the
   operator's update channel.
3. `classify patch criticality` — classify the available update against
   the operator's documented patch-criticality taxonomy
   (security-critical, security-routine, feature-only).
4. `stage rollout to canary ring` — stage the rollout against the
   operator's documented deployment-ring topology (test → canary →
   broad), starting with the canary ring.
5. `validate canary` — validate the canary ring against the documented
   health gates (functional probes, error-rate / latency deviation,
   rollback readiness) before fan-out.
6. `fan out to broad rings` — on a green canary, fan the rollout out to
   the remaining deployment rings.
7. `evidence capture` — persist a dated patch-application evidence
   record covering the available update, the criticality classification,
   the canary validation result, and the broad-ring fan-out.
8. `notify maintenance owner` — surface the attestation and any open
   items to the maintenance owner via the operator's notification
   channel.
9. `patch_management_end` — end sentinel.

Because the playbook is linear, the emitted GraphSpec has no
`conditional_edges`; every edge is an unconditional `on_completion`
hand-off. The conditional-edge router pattern documented in
`assemble.py` is still imported and exercised for parity with the
other LangGraph worked examples — it is a no-op for this playbook but
makes the assembly file copy-paste-ready for playbooks that do branch.

## What this example deliberately doesn't do

- It does not execute the graph. The `@tool` bodies raise
  `NotImplementedError`; integrators wire them to their own runtime
  (patch-availability feed, patch-criticality classifier, canary-ring
  deployer, canary health-gate probe, fan-out deployer, dated-attestation
  evidence store, and the maintenance-owner notification channel).
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
