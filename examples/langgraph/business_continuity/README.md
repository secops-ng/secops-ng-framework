# business_continuity — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the `business_continuity` CACAO playbook (NIS2 Art. 21(2)(c);
Art. 23 significant-incident notification). It is aimed at an
integrator who already runs LangGraph and wants to adopt a portable
SecOps-NG playbook without re-platforming.

This worked example pins the LangGraph leg (target 3 of 3) of the
cross-target parity lane for the `business_continuity` playbook. The
n8n and Temporal siblings ship under `../../n8n/business_continuity/`
and `../../temporal/business_continuity/`.

The `business_continuity` playbook is the plan-lifecycle sibling of
the `backup_recovery` exercise-lifecycle playbook (both anchor NIS2
Art. 21(2)(c)).

## Files in this directory

| Path                    | Source                              | Format                 |
|-------------------------|-------------------------------------|------------------------|
| `playbook.cacao.json`   | (input mirror)                      | CACAO v2 JSON          |
| `graph_spec.json`       | `compilers.langgraph.emit`          | GraphSpec JSON         |
| `state_bindings.py`     | `compilers.langgraph.state`         | Generated Python module|
| `assemble.py`           | (hand-written)                      | Runnable assembly      |
| `_audit_mirror.py`      | `compilers._shared.audit_mirror_cli`| Dependency-free mirror |
| `regenerate.sh`         | (tooling)                           | bash script            |
| `README.md`             | —                                   | This file.             |

The canonical input is the CACAO v2 playbook at
`../../../content/playbooks/business_continuity/playbook.cacao.yaml`.
The emitter splits into two artifacts: a declarative `GraphSpec` JSON
(nodes, edges, conditional-edge routers) and a generated Python module
carrying the state schema and per-step tool stubs. `assemble.py` wires
the two into a `langgraph.graph.StateGraph`; integrators copy this
file into their runtime and replace each `NotImplementedError` stub in
`state_bindings.py` with their own tool implementations.

## How to regenerate

After any change to the canonical playbook or to
`compilers/langgraph/*`, refresh the committed artifacts from the repo
root:

```sh
./examples/langgraph/business_continuity/regenerate.sh
```

The byte-parity golden test under
`tests/examples/langgraph/business_continuity/test_golden.py` reruns
the same pipeline and fails if the committed artifact drifts.

## Sovereignty note

LangGraph is open source (MIT) and runs as a Python library inside the
operator's own process — no vendor endpoint, no telemetry, no
call-home. The framework compiles to a `StateGraph` the operator owns
end to end.
