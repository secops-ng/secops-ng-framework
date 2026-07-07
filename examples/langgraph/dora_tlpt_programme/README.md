# dora_tlpt_programme — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the `dora_tlpt_programme` CACAO playbook. This is the operator-side
lifecycle of the DORA Chapter IV digital operational resilience
testing programme — DORT-scope definition, TLPT-mandatory decision and
competent-authority notification, red-team scoping-approval binding,
and dated competent-authority remediation attestation, anchored on the
ECB TIBER-EU framework as the implementation reference.

This worked example closes the cross-target parity ring (target 3 of 3)
for the `dora_tlpt_programme` playbook. The Temporal and n8n siblings
already ship under `../../temporal/dora_tlpt_programme/` and
`../../n8n/dora_tlpt_programme/`; together the three folders pin the
full three-target contract for this playbook.

## Files in this directory

| File | Role |
|------|------|
| `playbook.cacao.json` | Portable CACAO v2 playbook — byte-identical mirror of `content/playbooks/dora_tlpt_programme/playbook.cacao.json`, the input to the compiler. |
| `graph_spec.json` | Target-neutral GraphSpec (nodes, edges, conditional edges) emitted by `compilers.langgraph.emit`. |
| `state_bindings.py` | Generated `TypedDict` state + `@tool`-decorated action wrappers + agentic-extension hook, emitted by `compilers.langgraph.state`. |
| `assemble.py` | Hand-written reference assembly that wires the GraphSpec + bindings into a `langgraph.graph.StateGraph`. |
| `_audit_mirror.py` | Dependency-free audit-mirror sibling; see docs/observability/audit-mirror.md. |
| `regenerate.sh` | Re-runs both emitters from the canonical playbook and overwrites the mirrored CACAO + the generated artifacts. |

## How to regenerate

After any change to the canonical playbook or to `compilers/langgraph/*`,
refresh the committed artifacts from the repo root:

```bash
./examples/langgraph/dora_tlpt_programme/regenerate.sh
```

The script mirrors the canonical CACAO source into this folder and
re-emits `graph_spec.json` and `state_bindings.py` from it using
`compilers.langgraph.emit` and `compilers.langgraph.state`. A drift
test in `tests/examples/langgraph/dora_tlpt_programme/` fails the
suite if the committed artifacts diverge from a fresh regeneration.

## Cross-target pointers

The same canonical playbook ships under the other two reference compile
targets so an integrator can compare lowerings side by side:

- [`examples/n8n/dora_tlpt_programme/`](../../n8n/dora_tlpt_programme/) — n8n no-code workflow.
- [`examples/temporal/dora_tlpt_programme/`](../../temporal/dora_tlpt_programme/) — Temporal durable workflow stub.

## Topology

The dora_tlpt_programme playbook is a linear four-step lifecycle with
no conditional branching at the workflow layer. Four GraphSpec action
nodes, one per CACAO action step:

1. `define DORT scope` — resolve the DORT-scope catalogue against the
   operator's business-service / ICT-asset / ICT third-party registers
   per DORA Art. 24.
2. `TLPT trigger and planning gate` — evaluate whether TLPT is
   mandatory in the current window against JC 2022 03 and the
   operator's declared significance tier per DORA Art. 26(1); emit
   the competent-authority notification and record the dated
   decision.
3. `red-team scoping approval` — package the scoping submission for
   competent-authority approval per DORA Art. 26(3); record the
   response outcome (approved / deferred / rejected).
4. `remediation tracking` — compose the findings register from the
   red-team engagement and emit the dated competent-authority
   remediation attestation per DORA Art. 26(8).

Because the playbook is linear, the emitted GraphSpec has no
`conditional_edges`; every edge is an unconditional `on_completion`
hand-off. The conditional-edge router pattern documented in
`assemble.py` is still imported and exercised for parity with the
other LangGraph worked examples — it is a no-op for this playbook but
makes the assembly file copy-paste-ready for playbooks that do branch.

## What this example deliberately doesn't do

- It does not execute the graph. The `@tool` bodies raise
  `NotImplementedError`; integrators wire them to their own runtime
  (business-service register, ICT-asset register, ICT third-party
  register, competent-authority notification channel, scoping-
  submission dispatcher, findings-register store, evidence-store
  publisher).
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
