# data_subject_rights — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference
compiler on the `data_subject_rights` CACAO playbook
(GDPR Art. 15–22). It is aimed at an integrator who already runs
LangGraph and wants to adopt a portable SecOps-NG playbook without
re-platforming: the example shows exactly which artifacts the
compiler produces, how they fit together, and where the integrator
owns the seams.

This worked example pins the LangGraph leg (target 3 of 3) of the
cross-target parity lane for the `data_subject_rights` playbook. The
n8n and Temporal siblings ship under `../../n8n/data_subject_rights/`
and `../../temporal/data_subject_rights/`; together the three folders
pin the full three-target contract for this playbook.

## Files in this directory

| File | Role |
|------|------|
| `playbook.cacao.json` | Portable CACAO v2 playbook — byte-deterministic JSON mirror of `content/playbooks/data_subject_rights/playbook.cacao.yaml`, the input to the compiler. |
| `graph_spec.json` | Target-neutral GraphSpec (nodes, edges, conditional edges) emitted by `compilers.langgraph.emit`. |
| `state_bindings.py` | Generated `TypedDict` state + `@tool`-decorated action wrappers + agentic-extension hook, emitted by `compilers.langgraph.state`. |
| `_audit_mirror.py` | Dependency-free audit-mirror sibling (see `docs/observability/audit-mirror.md`). |
| `regenerate.sh` | Re-runs both emitters from the canonical playbook and overwrites the mirrored CACAO + the two generated artifacts. |

## How to regenerate

After any change to the canonical playbook or to
`compilers/langgraph/*`, refresh the committed artifacts from the
repo root:

```sh
./examples/langgraph/data_subject_rights/regenerate.sh
```

## Response-window handling (G-03 restart-drift row)

The 30-day GDPR Article 12(3) response window is expressed in the
LangGraph nodes as a deadline derived from `request_received_ts`
threaded through state — never from `time.time()` or
`datetime.utcnow()`. See
`tests/patterns/data_subject_rights/test_timer_restart_drift.py` for
the invariant asserted across all three targets.
