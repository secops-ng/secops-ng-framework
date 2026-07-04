# nis2_self_assessment — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the nis2_self_assessment CACAO playbook (NIS2 Art. 21(2)
whole-Article operator self-assessment roll-up). It is aimed at an
integrator who already runs LangGraph and wants to adopt a portable
SecOps-NG playbook without re-platforming: the example shows exactly
which artifacts the compiler produces, how they fit together, and
where the integrator owns the seams.

This worked example pins the LangGraph leg (target 3 of 3) of the
cross-target parity lane for the `nis2_self_assessment` playbook. The
n8n and Temporal siblings ship under
`../../n8n/nis2_self_assessment/` and
`../../temporal/nis2_self_assessment/`; together the three folders
pin the full three-target contract for this playbook.

## Files in this directory

| File | Role |
|------|------|
| `playbook.cacao.json` | Portable CACAO v2 playbook — byte-identical mirror of `content/playbooks/nis2_self_assessment/playbook.cacao.json`, the input to the compiler. |
| `graph_spec.json` | Target-neutral GraphSpec (nodes, edges, conditional edges) emitted by `compilers.langgraph.emit`. |
| `state_bindings.py` | Generated `TypedDict` state + `@tool`-decorated action wrappers + agentic-extension hook, emitted by `compilers.langgraph.state`. |
| `_audit_mirror.py` | Dependency-free audit-mirror sibling emitted by `compilers._shared.audit_mirror_cli`. |
| `assemble.py` | Hand-written reference assembly that wires the GraphSpec + bindings into a `langgraph.graph.StateGraph`. |
| `regenerate.sh` | Re-runs both emitters from the canonical playbook and overwrites the mirrored CACAO + the two generated artifacts. |

## How to regenerate

After any change to the canonical playbook or to
`compilers/langgraph/*`, refresh the committed artifacts from the
repo root:

```bash
./examples/langgraph/nis2_self_assessment/regenerate.sh
```

The script mirrors the canonical CACAO source into this folder and
re-emits `graph_spec.json` and `state_bindings.py` from it using
`compilers.langgraph.emit` and `compilers.langgraph.state`. A drift
test in `tests/examples/langgraph/nis2_self_assessment/` fails the
suite if the committed artifacts diverge from a fresh regeneration,
so the worked example stays honest as the compiler evolves.

## Cross-target pointers

The same canonical playbook ships under the other two reference
compile targets so an integrator can compare lowerings side by side:

- [`examples/n8n/nis2_self_assessment/`](../../n8n/nis2_self_assessment/) — n8n no-code workflow.
- [`examples/temporal/nis2_self_assessment/`](../../temporal/nis2_self_assessment/) — Temporal durable workflow stub.

## Topology

The nis2_self_assessment playbook is a linear collect-map-score-attest
chain with no conditional branching at the workflow layer. Six
GraphSpec nodes, one per CACAO step:

1. `nis2_self_assessment_start` — entry point matching the CACAO
   `start` step. Carries the workflow-scope variable
   (`__assessment_window__`) the operator's scheduler, on-demand
   attestation trigger, or supervisory-authority request supplies.
2. `collect clause evidence` — collect evidence from the operator's
   evidence store keyed on the ten Article 21(2)(a–j) sub-clause
   atoms.
3. `map evidence to clauses` — bind each collected evidence record
   to the sub-clause it discharges plus the originating playbook slug
   under the SecOps-NG content-model overlay.
4. `score per-clause coverage` — score each of the ten sub-clauses
   against the operator's documented coverage rubric.
5. `report attestation` — assemble the durable per-clause attestation
   artifact plus the whole-Article roll-up verdict.
6. `nis2_self_assessment_end` — end sentinel.

Because the playbook is linear, the emitted GraphSpec has no
`conditional_edges`; every edge is an unconditional `on_completion`
hand-off. The conditional-edge router pattern documented in
`assemble.py` is still imported and exercised for parity with the
other LangGraph worked examples — it is a no-op for this playbook but
makes the assembly file copy-paste-ready for playbooks that do
branch.

## What this example deliberately doesn't do

- It does not execute the graph. The `@tool` bodies raise
  `NotImplementedError`; integrators wire them to their own runtime
  (evidence-store adapter, coverage rubric, attestation artifact
  template).
- It does not ship operator credentials, endpoints, or environment.
  Secrets stay with the operator.
- It does not pick an LLM provider for the agentic-extension hook.
  `AGENTIC_HOOK` is a documented placeholder; the operator chooses a
  provider that matches their sovereignty posture at integration
  time.
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
