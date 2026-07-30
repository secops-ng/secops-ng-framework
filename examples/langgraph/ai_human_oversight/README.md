# ai_human_oversight — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the ai_human_oversight CACAO playbook. It is aimed at an integrator
who already runs LangGraph and wants to adopt a portable SecOps-NG
playbook without re-platforming: the example shows exactly which
artifacts the compiler produces, how they fit together, and where the
integrator owns the seams.

This is the *exercise* half of EU AI Act human oversight — Art. 14. Its
sibling `eu_ai_act_deployer_obligations` covers the Art. 26(2)
**assignment**. A named overseer who never reviewed anything satisfies
the assignment and not this playbook, which is the whole point of
keeping them apart.

## Files in this directory

| File | Role |
|------|------|
| `playbook.cacao.json` | Portable CACAO v2 playbook — byte-identical mirror of `content/playbooks/ai_human_oversight/playbook.cacao.json`, the input to the compiler. |
| `graph_spec.json` | Target-neutral GraphSpec (nodes, edges, conditional edges) emitted by `compilers.langgraph.emit`. |
| `state_bindings.py` | Generated `TypedDict` state + `@tool`-decorated action wrappers + agentic-extension hook, emitted by `compilers.langgraph.state`. |
| `assemble.py` | Hand-written reference assembly that wires the GraphSpec + bindings into a `langgraph.graph.StateGraph`. |
| `_audit_mirror.py` | Dependency-free audit-mirror sibling — see `docs/observability/audit-mirror.md`. |
| `regenerate.sh` | Re-runs both emitters from the canonical playbook and overwrites the mirrored CACAO + the generated artifacts. |

## Graph shape

A **linear five-node chain** with no conditional edges:
`establish_oversight_roster` → `brief_oversight_personnel` →
`review_flagged_decisions` → `record_intervention` →
`emit_oversight_evidence`. The conditional-edge router machinery in
`assemble.py` is therefore inert here; it is retained so the file stays
consistent with the other LangGraph examples and so an integrator who
adds a branch does not have to reintroduce it.

The conditionality Art. 14 actually contains lives in **state**, not
topology, and it is worth understanding before binding:

- **`record_intervention` always runs.** Most windows produce reviews
  and no interventions, and the step emits a nil record in that case.
  Modelling "no intervention" as a skipped node would make a quiet
  window indistinguishable from an unmonitored one — the opposite of
  what the evidence is for.
- **`__intervention_type__` is a state value, not a branch.** The four
  Art. 14(4)(d)-(e) exercises — decline, disregard, override, halt —
  all flow into the same evidence step. What differs is the weight a
  reviewer gives them, so they are carried as a distinct value rather
  than collapsed into the intervention record.
- **Art. 14(5) is a conditional *field*, not a conditional edge.**
  `__biometric_two_person_verification__` is populated only on Annex III
  point 1(a) remote biometric identification deployments, and is empty
  everywhere else. It holds either the two **separate** natural persons
  who independently verified the identification — one overseer
  confirming twice does not satisfy the provision — or the Union or
  national legal basis relied on for the law-enforcement exemption.

## How to regenerate

After any change to the playbook or to `compilers/langgraph/*`, refresh
the committed artifacts from the repo root:

```bash
./examples/langgraph/ai_human_oversight/regenerate.sh
```

The script mirrors the canonical CACAO source into this folder and
re-emits `graph_spec.json` and `state_bindings.py` from it. The drift
guard is pinned by
`tests/examples/ai_human_oversight/test_golden.py`.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
LangGraph runtime should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
LangGraph is open source (MIT) and integrators are free to run it on EU
sovereign infrastructure (Nebul, OVHcloud, Scaleway, Hetzner). We ship
the structure, the operator owns the data plane.
