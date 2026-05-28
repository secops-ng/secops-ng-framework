# threat-intel-ingest — LangGraph worked example

Emitted from `content/playbooks/threat-intel-ingest/playbook.cacao.json`
via `compilers.langgraph.emit.emit_from_file` (CLI:
`python -m compilers.langgraph.emit`).

- `playbook.cacao.json` — source CACAO playbook (copy of the canonical
  authored file under `content/`).
- `graph_spec.json` — intermediate `GraphSpec`: target-neutral,
  immutable description of LangGraph nodes, edges, and conditional
  edges (one per CACAO `if-condition` / `switch-condition` /
  `while-condition`).

State schema generation and `@tool` bindings ship in the sibling
`compilers.langgraph.state` module — invoke it on the same source
playbook to produce a TypedDict + tool-binding scaffold for the
operator's runtime. The emitter neither imports nor depends on the
`langgraph` runtime; the spec is a portable view of topology only.

The emitter is deterministic: regenerating produces byte-identical
output (stable ordering, no embedded timestamps).
