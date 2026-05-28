# LangGraph compiler

Compile a SecOps-NG CACAO v2 playbook into a LangGraph-shaped scaffold:
a target-neutral graph topology plus a typed Python module with the
`State` `TypedDict`, `@tool`-decorated action wrappers, and a documented
agentic-extension hook.

LangGraph is the **agentic** reference target — the right one to reach
for when at least one step in the playbook is best expressed as an LLM
choosing among tools rather than as a deterministic transition. It sits
next to n8n (no-code) and Temporal (durable code) as one of three
compile targets the framework ships. The framework itself remains
runtime-agnostic; this compiler is here so operators who already run
LangGraph can adopt SecOps-NG playbooks without re-platforming.

## Quickstart

The LangGraph compiler ships two surfaces — a topology emitter and a
state/tool-bindings emitter — both runnable as modules from the
framework repo root.

### Topology — graph spec JSON

```bash
PYTHONPATH=. python -m compilers.langgraph.emit \
    content/playbooks/vuln-intake/playbook.cacao.json
```

That prints a JSON document describing the LangGraph topology: entry
point, nodes (one per CACAO `action` / `playbook-action` /
`if-condition` / `switch-condition` / `while-condition` / `parallel`
step), unconditional edges, and conditional edges with their branch
maps. CACAO `start` and `end` steps are collapsed onto the special
`__END__` sentinel; the emitter never depends on the `langgraph`
runtime.

### State + tool bindings — Python module

```bash
PYTHONPATH=. python -m compilers.langgraph.state \
    content/playbooks/vuln-intake/playbook.cacao.json \
    > vuln_intake_state.py
```

The generated module exposes three registry symbols an integrator
imports directly:

- `STATE_SCHEMA` — the `TypedDict` describing the graph's state shape
  (one field per CACAO `playbook_variables` entry, plus the bookkeeping
  channels `step_status`, `errors`, `messages`).
- `TOOLS` — a tuple of `@tool`-decorated async functions, one per CACAO
  action step, signatures derived from `in_args` / `out_args`.
- `AGENTIC_HOOK` — a placeholder `async def llm_step(state)` showing
  where to plug in an LLM-driven node.

### Programmatic use

```python
from pathlib import Path

from compilers._shared.cacao_parser import parse_file
from compilers.langgraph import emit, render_module

playbook = parse_file("content/playbooks/vuln-intake/playbook.cacao.json")

spec = emit(playbook)                 # GraphSpec — topology, no runtime
module_source = render_module(playbook)  # Python source string

Path("vuln_intake_state.py").write_text(module_source, encoding="utf-8")
```

`emit_from_file` and `render_module_from_file` accept a path directly.

### Assembling the StateGraph

The compiler stops short of importing `langgraph` — the integrator
owns the runtime bootstrap. A minimal assembly looks like:

```python
from langgraph.graph import StateGraph, END

from compilers.langgraph import emit_from_file
from vuln_intake_state import STATE_SCHEMA, TOOLS, AGENTIC_HOOK

spec = emit_from_file("content/playbooks/vuln-intake/playbook.cacao.json")

graph = StateGraph(STATE_SCHEMA)
for node in spec.nodes:
    # Bind your runtime callable here — the @tool wrappers are the
    # default, an LLM-driven node calls AGENTIC_HOOK, etc.
    graph.add_node(node.name, ...)

graph.set_entry_point(spec.entry if spec.entry != spec.END else END)
for edge in spec.edges:
    graph.add_edge(edge.src, END if edge.dst == spec.END else edge.dst)
for cond in spec.conditional_edges:
    graph.add_conditional_edges(cond.src, router_for(cond.src), cond.branches)

app = graph.compile()
```

The conditional-edge `branches` keys are stable: `success` / `failure`
for `if-condition` and `while-condition`, `case_<i>` for
`switch-condition`. The integrator's router function returns whichever
key matches the current state.

## Agentic vs deterministic

Use this target when at least one step is genuinely a *choice*, not a
transition. Two heuristics:

1. **Pick LangGraph when the routing depends on free-form input.**
   If the next step depends on classifying a natural-language alert,
   summarising a finding, deciding which playbook to invoke, or
   reconciling conflicting signals — that's an LLM call, and LangGraph
   gives you the state container + tool calling loop to express it
   cleanly. Use the `AGENTIC_HOOK` slot, bind `TOOLS` to a `ToolNode`,
   and let the model pick.
2. **Pick n8n or Temporal when every routing decision is a rule.**
   If your conditional steps map to clean expressions (`severity ==
   "critical"`, `asset_owner in on_call_team`), the LLM adds nothing
   but latency, cost, and a class of failure modes you didn't have
   before. n8n is the right reach when you want a UI for the operator;
   Temporal when you want durable, restartable code.

You can mix the two: a deterministic playbook can still benefit from
LangGraph if one specific step (e.g. *classify* this alert) is the
agentic part. The `@tool`-decorated wrappers this compiler emits are
usable from any LangGraph node, deterministic or LLM-driven — that's
the point of compiling to *content*, not to a runtime opinion.

What this compiler explicitly does **not** do:

- It does not assemble the `StateGraph`. That's runtime code the
  integrator owns.
- It does not bind an LLM provider. The `llm_step` stub is
  provider-neutral by design — see "Sovereignty" below.
- It does not choose between an LLM and a deterministic node for any
  given step. That's a content / authoring decision, not a compile
  decision.

## Sovereignty

LangGraph is open source (MIT) and ships as a Python library — running
it is a hosting decision, not a vendor lock-in. Two paths fit the EU
sovereign-cloud posture this project favours
(see [docs/sovereignty/](../sovereignty/)):

- **Self-hosted LangGraph on a sovereign EU runtime.** Run the graph
  inside a Python process on EU sovereign infrastructure (Nebul,
  OVHcloud, Scaleway, Hetzner). This is the default posture for
  operators with strict residency or processor-chain constraints
  (GDPR Art. 28, NIS2 Art. 21, DORA Ch. V).
- **LangGraph Platform, EU region.** LangChain's managed offering with
  an EU region is suitable for teams that want a managed control plane
  and accept the standard managed-SaaS trade-offs (data residency
  follows the region you provision in; control-plane telemetry follows
  the provider's terms).

### Run with EU-hosted LLMs

The agentic hook is provider-neutral on purpose. The compiler emits a
documented `llm_step` placeholder; the integrator wires it to whichever
provider their sovereignty posture allows. Sovereignty-compatible
options today include:

- **Self-hosted open-weights models on EU sovereign GPU infrastructure**
  (e.g. Mistral / Llama / Qwen families served via vLLM, TGI, or
  llama.cpp on Nebul, OVHcloud, Scaleway, Hetzner).
- **Managed EU-hosted inference endpoints** from providers with an
  EU residency commitment for both data and control plane.

Avoid binding the agentic hook to a US-hosted LLM provider in
deployments that need EU data residency — even if the rest of your
stack is sovereign, every model call leaks the prompt (and any state
data interpolated into it) into a non-sovereign processing context.

The compile-time output never embeds a provider SDK; the choice is the
operator's, made at integration time, and revisable without
regenerating the playbook.

## Determinism

Same AST in → byte-identical output, for both halves of the compiler.
Two golden tests under `tests/compilers/langgraph/` pin the
`vuln_intake` worked example:

- `golden/vuln_intake.graph_spec.json` — the topology JSON.
- `golden/vuln_intake.expected.py` — the state + tool-bindings module.

Any change to either emitter that alters the output for this fixture
must update the golden in the same commit, surfacing the diff in code
review.

Regenerate after an intentional emitter change:

```bash
PYTHONPATH=. python -m compilers.langgraph.emit \
    tests/compilers/_shared/fixtures/vuln_intake.cacao.json \
    > tests/compilers/langgraph/golden/vuln_intake.graph_spec.json

PYTHONPATH=. python -m compilers.langgraph.state \
    tests/compilers/_shared/fixtures/vuln_intake.cacao.json \
    > tests/compilers/langgraph/golden/vuln_intake.expected.py
```

Commit the new goldens alongside the emitter change so reviewers see
both diffs in the same PR.

## Limits of this release

- The compiler emits a *scaffold*, not a runnable graph. State reducers
  and tool bodies are intentionally `raise NotImplementedError` — the
  integrator wires them to the operator's runtime.
- `while-condition` is surfaced as a conditional edge with `success`
  (loop body) and `failure` (exit) keys; the integrator owns the
  iteration shape and any loop bookkeeping in state.
- `parallel` is recorded as a node of kind `parallel`; the fan-out /
  fan-in shape on the LangGraph side is the integrator's call (typical
  pattern: a fan-out node feeding multiple branches that converge on a
  shared join node).
- Retry policy, timeout, and concurrency limits are not surfaced into
  the emitted module — these are runtime concerns the integrator
  applies in their own assembly code.

## See also

- `compilers/langgraph/README.md` — module-level engineering notes
  (translation tables, design rationale, internals).
- `tests/compilers/langgraph/` — golden tests and regeneration recipe.
- `docs/compilers/README.md` — index of all reference compilers.
- `docs/sovereignty/` — sovereignty posture for the framework.
