# eu_ai_act_deployer_obligations — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the eu_ai_act_deployer_obligations CACAO playbook. It is aimed at an
integrator who already runs LangGraph and wants to adopt a portable
SecOps-NG playbook without re-platforming: the example shows exactly
which artifacts the compiler produces, how they fit together, and where
the integrator owns the seams.

This is the deployer-side counterpart to the provider-side
`eu_ai_act_risk_management` example — the operator running a
third-party high-risk AI system in production, rather than the one
placing a system on the market.

## Files in this directory

| File | Role |
|------|------|
| `playbook.cacao.json` | Portable CACAO v2 playbook — byte-identical mirror of `content/playbooks/eu_ai_act_deployer_obligations/playbook.cacao.json`, the input to the compiler. |
| `graph_spec.json` | Target-neutral GraphSpec (nodes, edges, conditional edges) emitted by `compilers.langgraph.emit`. |
| `state_bindings.py` | Generated `TypedDict` state + `@tool`-decorated action wrappers + agentic-extension hook, emitted by `compilers.langgraph.state`. |
| `assemble.py` | Hand-written reference assembly that wires the GraphSpec + bindings into a `langgraph.graph.StateGraph`. |
| `_audit_mirror.py` | Dependency-free audit-mirror sibling — see `docs/observability/audit-mirror.md`. |
| `regenerate.sh` | Re-runs both emitters from the canonical playbook and overwrites the mirrored CACAO + the generated artifacts. |

## Graph shape

The lifecycle is a **linear five-node chain** with no conditional
edges: confirm-intended-use → assign-human-oversight →
monitor-operation → assess-fundamental-rights-impact →
retain-logs-and-evidence. The conditional-edge router machinery in
`assemble.py` is therefore inert here; it is retained so the file stays
consistent with the other LangGraph examples and so an integrator who
adds a branch does not have to reintroduce it.

The branching that the *regulation* contains is carried in state rather
than in topology, which is a deliberate modelling choice worth
understanding before you bind it:

- **`__escalation_trigger_class__`** holds the Art. 26(5) trigger —
  routine Art. 72 feedback, an Art. 79(1) risk determination compelling
  notification *and* suspension of use, or a serious incident
  compelling immediate sequenced notification into the provider-side
  Art. 73 chain. These are not alternate graph paths because all three
  still flow into the retention step; what differs is the obligation
  each fires externally.
- **In-scope / out-of-scope determinations are values, not skipped
  nodes.** The Art. 27 step always runs and always emits a
  `__fria_determination_id__`; an out-of-scope deployer emits a dated
  out-of-scope record. Modelling that as a skipped node would produce
  an absence of evidence where the obligation requires a record.

## How to regenerate

After any change to the playbook or to `compilers/langgraph/*`, refresh
the committed artifacts from the repo root:

```bash
./examples/langgraph/eu_ai_act_deployer_obligations/regenerate.sh
```

The script mirrors the canonical CACAO source into this folder and
re-emits `graph_spec.json` and `state_bindings.py` from it. The drift
guard is pinned by
`tests/examples/eu_ai_act_deployer_obligations/test_golden.py`.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
LangGraph runtime should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
LangGraph is open source (MIT) and integrators are free to run it on EU
sovereign infrastructure (Nebul, OVHcloud, Scaleway, Hetzner). We ship
the structure, the operator owns the data plane.
