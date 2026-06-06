# incident-management — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the incident-management CACAO playbook (the NIS2 Article 23
three-stage regulator timeline: 24-hour early warning, 72-hour
notification, one-month final report). It is aimed at an integrator who
already runs LangGraph and wants to adopt the portable SecOps-NG
incident-management playbook without re-platforming: the example shows
exactly which artifacts the compiler produces, how they fit together,
and where the integrator owns the seams.

This is the **SKELETON** card of the F-WF-05 wave. Action bodies are
stub placeholders that raise `NotImplementedError` and carry only the
CACAO I/O contract; no primitives binding is in place yet — that lands
in the CORE-PRIM card (card 5 of the F-WF-05 wave).

## Files in this directory

| File | Role |
|------|------|
| `playbook.cacao.json` | Portable CACAO v2 playbook — byte-identical mirror of `content/playbooks/incident-management/playbook.cacao.json`, the input to the compiler. |
| `graph_spec.json` | Target-neutral GraphSpec (nodes, edges, conditional edges) emitted by `compilers.langgraph.emit`. |
| `state_bindings.py` | Generated `TypedDict` state + `@tool`-decorated action wrappers + agentic-extension hook, emitted by `compilers.langgraph.state`. |
| `_audit_mirror.py` | Dependency-free `AuditTrail` / `AuditRecord` sibling — materialised by the compiler so the worked example is a self-contained drop-in. |
| `assemble.py` | Hand-written reference assembly that wires the GraphSpec + bindings into a `langgraph.graph.StateGraph`. |
| `regenerate.sh` | Re-runs both emitters from the canonical playbook and overwrites the mirrored CACAO + the two generated artifacts plus the audit-mirror sibling. |

## How to regenerate

After any change to the canonical playbook or to `compilers/langgraph/*`,
refresh the committed artifacts from the repo root:

```bash
./examples/langgraph/incident-management/regenerate.sh
```

The script mirrors the canonical CACAO source into this folder and
re-emits `graph_spec.json` and `state_bindings.py` from it using
`compilers.langgraph.emit` and `compilers.langgraph.state`, and
re-materialises `_audit_mirror.py` via
`compilers._shared.audit_mirror_cli`. A drift test in
`tests/examples/incident_management/` fails the suite if the committed
artifacts diverge from a fresh regeneration, so the worked example
stays honest as the compiler evolves.

## Wiring it into your runtime

`assemble.py` is the canonical reference. The pattern in ~10 lines:

1. Load `graph_spec.json` with `load_graph_spec()` — pure JSON, no
   runtime dependency.
2. Pick the generated `TypedDict` off `state_bindings` and pass it to
   `StateGraph(state_cls)`.
3. For each `node` in `spec["nodes"]`, call `graph.add_node(step_id,
   tool_fn)`. The `@tool`-decorated wrappers on `state_bindings` are
   the default binding; an integrator can swap any node for an
   LLM-driven callable that uses the `AGENTIC_HOOK` slot instead.
4. `graph.set_entry_point(spec["entry"])`.
5. For each plain edge in `spec["edges"]`, call `graph.add_edge(src,
   dst)` (mapping the `__END__` sentinel to LangGraph's `END`).
6. For each entry in `spec["conditional_edges"]`, build a router with
   `make_router(cond)` and call
   `graph.add_conditional_edges(src, router, branches)`. The router
   reads `state["step_status"][src]` and maps the CACAO branch label
   (`success` / `failure` for `if-condition`) to the successor node; a
   missing or unknown status falls through to the conditional's
   `default` (or terminates).
7. `graph.compile()` — the runtime is now ready to invoke.

The two `if-condition` branches in this playbook are:

* `significant?` — true paths into the regulator-timeline three-stage
  submission flow; false routes directly to the end step.
* `final-report material complete?` — true paths into the one-month
  final-report submission; false closes the timeline with a
  deferred-final-report marker so the timeline JSON stays well-formed.

## What this example deliberately doesn't do

- It does not execute the graph. The `@tool` bodies raise
  `NotImplementedError`; integrators wire them to their own runtime
  (incident signal intake, deterministic significance / cross-border
  classification, the F-PT-02 incident-timeline pattern handle store,
  regulator-submission destinations for the three NIS2 stages,
  timeline JSON persistence backend).
- It does not ship operator credentials, endpoints, or environment.
  Secrets stay with the operator — the sovereign-stack constraint
  applies, so regulator destinations come from the operator's own
  config layer (no default endpoint is shipped).
- It does not pick an LLM provider for the agentic-extension hook.
  `AGENTIC_HOOK` is a documented placeholder; the single DSPy reach in
  this playbook is the free-text narrative / root-cause / mitigations
  fields on the one-month final report, and the operator chooses a
  provider that matches their sovereignty posture at integration time.
- It does not bind a specific runtime topology (retry policy,
  concurrency, persistence backend, stage-clock arithmetic). Those are
  runtime concerns the integrator applies in their own assembly; the
  stage-clock primitive itself lands in CORE-PRIM.
- It does not implement the deterministic significance / cross-border
  classification policy or the typed early-warning / 72h notification /
  final-report payload shapes. Those land in CORE-PRIM.

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

## EU-resident LM endpoint guard

This worked example inherits the framework-wide default that any LM
endpoint reachable from the compiled artifact lives in the European
Union. The check runs both at compile time (the reference compiler
fails fast on a non-EU endpoint when emitting this example) and at
runtime (a generated `_lm_endpoint_guard.py` sibling re-applies the
check at process startup). An operator who deliberately wires a non-EU
endpoint must set `SECOPS_NG_LM_ENDPOINT_NON_EU_ACK=1` in the
environment to acknowledge the trade-off; the workflow then loses its
EU-residency posture and should document that fact in the operator's
own deployment notes. See
[docs/sovereignty/eu-resident-lm-guard.md](../../../docs/sovereignty/eu-resident-lm-guard.md)
for the heuristic, the override, and the EU allowlist.
