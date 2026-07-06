# eu_ai_act_risk_management — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the eu_ai_act_risk_management CACAO playbook. It is aimed at an
integrator who already runs LangGraph and wants to adopt a portable
SecOps-NG playbook without re-platforming: the example shows exactly
which artifacts the compiler produces, how they fit together, and where
the integrator owns the seams.

## Files in this directory

| File | Role |
|------|------|
| `playbook.cacao.json` | Portable CACAO v2 playbook — byte-identical mirror of `content/playbooks/eu_ai_act_risk_management/playbook.cacao.json`, the input to the compiler. |
| `graph_spec.json` | Target-neutral GraphSpec (nodes, edges, conditional edges) emitted by `compilers.langgraph.emit`. |
| `state_bindings.py` | Generated `TypedDict` state + `@tool`-decorated action wrappers + agentic-extension hook, emitted by `compilers.langgraph.state`. |
| `assemble.py` | Hand-written reference assembly that wires the GraphSpec + bindings into a `langgraph.graph.StateGraph`. |
| `_audit_mirror.py` | Dependency-free audit-mirror sibling — see `docs/observability/audit-mirror.md`. |
| `regenerate.sh` | Re-runs both emitters from the canonical playbook and overwrites the mirrored CACAO + the generated artifacts. |

## How to regenerate

After any change to the playbook or to `compilers/langgraph/*`, refresh
the committed artifacts from the repo root:

```bash
./examples/langgraph/eu_ai_act_risk_management/regenerate.sh
```

The script mirrors the canonical CACAO source into this folder and
re-emits `graph_spec.json` and `state_bindings.py` from it. The drift
guard is pinned by
`tests/examples/eu_ai_act_risk_management/test_golden.py`.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
LangGraph runtime should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
LangGraph is open source (MIT) and integrators are free to run it on EU
sovereign infrastructure (Nebul, OVHcloud, Scaleway, Hetzner). We ship
the structure, the operator owns the data plane.
