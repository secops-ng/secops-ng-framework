# Compile-target tradeoffs

Read this when the interview reaches the target recommendation. Every row was
checked against an emitted artifact in `examples/`, not inferred from prose —
where a doc and an artifact disagree, the artifact wins and the disagreement is
noted.

The three launch targets, per `docs/FOUNDATION.md` §4 ("each one of three, not
the engine"): **n8n** (visual, self-hostable), **Temporal** (durable,
replayable), **LangGraph** (graph-shaped, agentic).

## The matrix

| | n8n | Temporal | LangGraph |
|---|---|---|---|
| **control flow in output** | **full** — `if` / `switch` nodes + edges | **none** — activities only; the workflow body raises | **full** — `graph_spec.json` carries `conditional_edges` |
| **artifacts you must produce** | 1 file | 3 — `workflow.temporal.py`, `_audit_mirror.py`, `__init__.py` | 4 — `graph_spec.json`, `state_bindings.py`, `_audit_mirror.py`, `__init__.py` |
| **plus hand-written** | none | the workflow body (ordering, branching, parallel) | `assemble.py` — the `StateGraph` wiring |
| **an unbound action becomes** | a `set` node carrying the CACAO I/O contract, editable in the UI | `raise NotImplementedError(step_id)` | `raise NotImplementedError(step_id)` |
| **a bound action becomes** | a `code` node with the primitive call — **but see the Pyodide caveat** | an activity body calling the primitive | a `@tool` body calling the primitive |
| **needs Python to change a threshold** | no | yes, plus a redeploy | yes, plus a redeploy |
| **machine-readable TODO list** | **yes** — `meta.secops_ng_notes`, per step, in operator language | no — count `NotImplementedError` | no — count `NotImplementedError` |
| **where credentials live** | n8n credential records, attached after import | operator runtime | operator runtime |

## Evidence for each claim

**Control flow.** `examples/n8n/vuln_intake/workflow.n8n.json` node types:
`{manualTrigger: 1, code: 2, set: 6, if: 1, switch: 1, noOp: 1}` — the branch
steps survive as real nodes. `examples/langgraph/vuln_intake/graph_spec.json`
carries `nodes: 10, edges: 8, conditional_edges: 2`. By contrast
`examples/temporal/vuln_intake/workflow.temporal.py` contains **8
`NotImplementedError`**, one of which is the workflow lowering itself:

```
raise NotImplementedError(
    f"CACAO workflow lowering not implemented: stable_id='playbook.vuln_intake@v1'"
)
```

`compilers/temporal/README.md` states control-flow lowering is "intentionally
deferred". **Note the doc conflict:** `docs/cookbook/vuln_intake.md` §4.2
describes the Temporal output as a worker module you "register the activities and
run" — that overstates it. Trust the artifact.

**Bound vs unbound.** `vuln_intake` has 2 real `core_body` bindings and its n8n
emit has exactly 2 `code` nodes; `data_exfil` has 0 bindings and 0 `code` nodes
(`{manualTrigger: 1, set: 5, if: 2, noOp: 1}`). The mapping is one-to-one.

**Hand-written assembly.** `examples/langgraph/vuln_intake/assemble.py` is **184
lines** and is referenced by **zero** `regenerate.sh` scripts — no compiler emits
it. `docs/compilers/langgraph.md` is explicit: the compiler emits "a *scaffold*,
not a runnable graph" and "does not assemble the `StateGraph`". That file is the
honest measure of what LangGraph adoption costs.

**The Temporal import gap.** All 12 emitted Temporal modules do
`from ._audit_mirror import AuditRecord, AuditTrail`, but no
`examples/temporal/*/` directory contains `_audit_mirror.py` or `__init__.py`,
and their `regenerate.sh` never calls `audit_mirror_cli`. So the committed
Temporal examples do not import as-is. Every LangGraph example *does* ship
`_audit_mirror.py`. Generated `regenerate.sh` must add the missing calls for
Temporal — see SKILL.md.

## Two caveats that change recommendations

**Pyodide (n8n + bindings).** The `code` node runs `language: python` under
Pyodide. It cannot import `content/playbooks/…`, and it reads inputs via `$json`,
not the bare `__var__` names the emitter writes. So on n8n, **more bindings means
more rewriting**, not less — either flatten to a `set` node plus an external
call, or run the primitive outside n8n behind HTTP.

**Bound bodies are intent, not working code.** A bound step's body references
playbook variables that are frequently absent from `playbook_variables`, so it
raises `NameError` before it does anything. Treat a binding as *a precise
statement of the intended call*, which is genuinely useful, and not as a step
that runs. This is why binding coverage is a poor readiness ranking.

## Choosing when nothing is decisive

Default to **n8n**, and justify it as a property of the compilers rather than a
judgement about the team: it is the only target whose emitted artifact preserves
control flow *and* is importable without writing Python, and the only one that
publishes its own remaining-work list.

Temporal is the target where the compiler currently does least. Recommend it when
a step must survive process death against a named regulator clock — NIS2 Art. 23
(`incident_management`, which ships `primitives/stage_clock.py`) or CRA Art. 14
(`vuln_intake`) — and say the topology gap out loud before the operator commits,
not after.

LangGraph earns its cost only when a model must **choose what happens next**. If
the model is only writing text inside a step whose path is fixed, all three
targets can do that, and the framework's own position (`examples/*/
incident_management/core_body.overlay.json` `_meta`) is that model reach stays
scoped to free-text fields while regulated decisions stay deterministic code.

## Offer the second compile

Compiling the same playbook to a second target is free — same canonical source,
byte-deterministic output, and cross-target parity is one of the four
non-negotiables (`docs/FOUNDATION.md` §2). Suggest **n8n as the reading artifact**
even when a Python target is the running one: it is the reviewable picture of the
playbook to put in front of an auditor or a new analyst.
