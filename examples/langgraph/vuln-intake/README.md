# vuln-intake — LangGraph worked example

Demonstrates the LangGraph reference compiler end-to-end on the
vulnerability intake CACAO playbook.

## Flow

1. `playbook.cacao.json` — the portable CACAO playbook (input).
2. `graph_spec.json` — the intermediate GraphSpec produced by the
   compiler. Captures nodes, edges, and routing in a target-agnostic
   shape.
3. `state_bindings.py` — generated state TypedDict and `@tool`
   bindings derived from the playbook's variables and commands.
4. `assemble.py` — runnable assembly that wires the GraphSpec and
   state bindings into a `langgraph.graph.StateGraph` ready to invoke.

## Input fixture

`playbook.cacao.json` is sourced from the parser test fixture at
`tests/compilers/_shared/fixtures/vuln_intake.cacao.json`. A canonical
authored copy under `content/playbooks/vuln-intake/` will replace it
once that directory lands; for now the example reuses the parser
fixture so the worked example has a real, validated input.

## Status

Scaffolding only. The GraphSpec, state bindings, and assembly are
stubs marked TBD; the compiler-driven content lands in a follow-up.
