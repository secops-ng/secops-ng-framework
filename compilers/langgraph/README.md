# compilers/langgraph/

Reference compiler #3 for SecOps-NG.

Emits a target-neutral **graph spec** (`GraphSpec`) from a parsed CACAO v2
playbook. CACAO action steps become nodes, transitions become edges,
conditional steps (`if-condition`, `switch-condition`, `while-condition`)
become conditional edges with a branch map.

This module does **not** depend on the `langgraph` runtime. It produces a
structure a consumer feeds into `langgraph.graph.StateGraph`, or serialises
to JSON for diagram tooling and golden tests. State schema generation and
`@tool` binding ship in a sibling module (see the LangGraph state-binding
card).

## Quick start

```python
from compilers.langgraph import emit_from_file

spec = emit_from_file("content/playbooks/vuln-intake/playbook.cacao.json")
print(spec.entry)            # first real node reached from workflow_start
for node in spec.nodes:      # NodeKind.ACTION / CONDITION / PARALLEL
    ...
for edge in spec.edges:      # unconditional transitions
    ...
for cond in spec.conditional_edges:
    # cond.branches: {"success": "...", "failure": "..."} for if/while
    # cond.branches: {"case_0": "...", ...} for switch-condition
    # cond.default:  CACAO on_completion fall-through, if any
    ...
```

The CLI `python -m compilers.langgraph.emit <playbook.json>` prints the
spec as JSON for inspection.

## Design notes

- **Pure**: same AST in → same spec out. No I/O, no mutation.
- **End collapsing**: CACAO `end` steps are not nodes; transitions to them
  surface as edges whose `dst` is the `GraphSpec.END` sentinel.
- **Edge provenance**: every plain edge records which CACAO field produced
  it (`on_completion`, `on_success`, `on_failure`, `next_steps[i]`) so
  reviewers can trace topology without re-reading the playbook.
- **Framework-agnostic**: the spec is JSON-serialisable and consumed by
  the LangGraph builder downstream — we ship the structure, not a runtime.
