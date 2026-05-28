# compilers/langgraph/

Reference compiler #3 for SecOps-NG. CACAO v2 playbook → LangGraph-shaped
artifacts an integrator can drop into `langgraph.graph.StateGraph`.

The compiler ships in two halves so each surface stays focused and
runtime-free. Neither module imports `langgraph` or `langchain_core` —
the **generated** code does.

## 1. Topology — `compilers.langgraph.emit`

Emits a target-neutral `GraphSpec` from a parsed CACAO playbook:

- CACAO `action` / `playbook-action` steps → graph nodes.
- CACAO `start` → graph `entry` pointer.
- CACAO `end` → the `GraphSpec.END` sentinel (no node).
- Unconditional transitions → plain edges with provenance
  (`on_completion` / `on_success` / `on_failure` / `next_steps[i]`).
- `if-condition` / `while-condition` / `switch-condition` →
  conditional edges with a branch map and (where the playbook declares
  one) a default fall-through.

```python
from compilers.langgraph import emit_from_file

spec = emit_from_file("content/playbooks/vuln-intake/playbook.cacao.json")
print(spec.entry)            # first real node reached from workflow_start
for node in spec.nodes: ...
for edge in spec.edges: ...  # unconditional transitions
for cond in spec.conditional_edges:
    # cond.branches: {"success": ..., "failure": ...} for if/while
    # cond.branches: {"case_0": ..., ...} for switch-condition
    # cond.default:  CACAO on_completion fall-through, if any
    ...
```

CLI: `python -m compilers.langgraph.emit <playbook.json>` prints the spec
as JSON.

## 2. State + tool bindings — `compilers.langgraph.state`

Emits the typed state container the graph runs over and `@tool`
wrappers for every action step, plus the documented agentic-extension
hook.

```python
from compilers.langgraph import (
    state_schema, tool_bindings, render_module_from_file,
)

spec     = state_schema(playbook)            # StateSchemaSpec
bindings = tool_bindings(playbook)           # ToolBindingsSpec
source   = render_module_from_file("…/playbook.cacao.json")
```

Or from the shell:

```
python -m compilers.langgraph.state <playbook.json> [--spec-only]
```

### State schema shape

`render_state_schema(spec)` emits a `TypedDict` whose fields come from
three sources, in this order:

1. **`playbook_variables`** — one field per declared variable, named by
   stripping the `__double_underscore__` decoration and typed via the
   CACAO `type` field (`string`/`uri`/`uuid`/… → `str`, `integer`/`long`
   → `int`, `boolean` → `bool`, `dictionary` → `dict[str, object]`).
2. **Step-local variables** (CACAO §3.4) that aren't already covered by
   a playbook-level entry — surfaced so the integrator never loses
   access to a value the playbook references but didn't declare at top
   level.
3. **Bookkeeping channels** added by the compiler:
   - `step_status: dict[str, str]` — per-step status map, keyed by
     CACAO `step_id`. Conventional values: `pending`, `running`, `ok`,
     `failed`, `awaiting-human`.
   - `errors: list[str]` — accumulated error messages.
   - `messages: Annotated[list[AnyMessage], add_messages]` — the
     LangChain message channel for the agentic extension surface (see
     §4).

`StateSchemaSpec.to_dict()` is JSON-serialisable for golden tests and
diagram tooling.

### Tool bindings shape

`render_tool_bindings(bindings)` emits one `@tool`-decorated async
function per CACAO `action` / `playbook-action` step. The signature is
derived from the step's `in_args` / `out_args` via the shared
activity-signature resolver (the same code path the Temporal compiler
uses — CACAO variable typing is identical across reference compilers).

Each function body raises `NotImplementedError` carrying the source
`step_id` — the integrator fills it in. CACAO step IDs are preserved in
the docstring so reviewers can trace tools back to the playbook without
re-reading the JSON.

## 3. Generated module — `render_module`

`render_module(playbook)` ties §2 together into a single, deterministic
Python source file that compiles without modification:

```
# AUTO-GENERATED — do not edit by hand.
…
from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

class <StableId>State(TypedDict, total=False): …
@tool async def <step_name>(…) -> …: …       # one per action step
async def llm_step(state: <…>State) -> dict: …  # agentic hook

STATE_SCHEMA = <…>State
TOOLS = (…)
AGENTIC_HOOK = llm_step
```

The trailing `STATE_SCHEMA` / `TOOLS` / `AGENTIC_HOOK` registry is what
a LangGraph builder imports — no pattern-matching on identifier names.

Output is byte-identical across runs for the same input.

## 4. Agentic extension surface

LangGraph is the agentic compile target, so the generated module always
includes an `llm_step(state)` placeholder. This is the documented hook
where an integrator plugs in an LLM-driven node — typically wired into
the graph next to a `ToolNode` bound against `TOOLS`.

Contract (also documented in the generated docstring):

- Read CACAO variables off the typed state (`state["finding_id"]`,
  not `state["__finding_id__"]`).
- Call an LLM with `llm.bind_tools([...])` or route through a
  LangGraph `ToolNode` over `TOOLS`.
- Return a dict of state updates. LangGraph merges into the typed
  state via the reducers the integrator picks.
- Append assistant / tool messages to `state["messages"]`. The
  channel uses `add_messages`, so returning a `list` under that key
  concatenates rather than replaces.

The stub intentionally does not import a specific LLM SDK. Sovereignty
and provider-neutrality mean the operator picks (Ollama on Nebul,
Mistral hosted on Scaleway, a gateway in front of OpenAI, …) at
integration time — the playbook never mentions a vendor.

## Design notes

- **Pure**: same AST in → same source out. No I/O, no mutation, no
  network. The compilers depend only on the standard library and the
  shared parser AST.
- **Runtime-free**: this module never imports `langgraph` /
  `langchain_core`. Generated code does.
- **Deterministic**: identifier choices, field order, and iteration
  order are all stable so generated files diff cleanly under git.
- **Framework-agnostic**: the spec types (`GraphSpec`,
  `StateSchemaSpec`, `ToolBindingsSpec`) are JSON-serialisable and
  consumable by any LangGraph builder — we ship the structure, not a
  runtime.
