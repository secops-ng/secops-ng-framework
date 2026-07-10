# network_security — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the `network_security` CACAO playbook (NIS2 Art. 21(2)(e) security
in network and information systems; DORA Art. 9 protection and
prevention, network-security slice). It is aimed at an integrator who
already runs LangGraph and wants to adopt a portable SecOps-NG
playbook without re-platforming.

This worked example pins the LangGraph leg (target 3 of 3) of the
cross-target parity lane for the `network_security` playbook. The
n8n and Temporal siblings ship under `../../n8n/network_security/`
and `../../temporal/network_security/`.

The `network_security` playbook is the network-boundary limb of the
posture-management family; broader host / workload / IAM posture is
covered by the sibling `infra_posture_management` playbook.

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
`../../../content/playbooks/network_security/playbook.cacao.yaml`.
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
./examples/langgraph/network_security/regenerate.sh
```

The byte-parity golden test under
`tests/examples/langgraph/network_security/test_golden.py` reruns
the same pipeline and fails if the committed artifact drifts.

## Sovereignty note

LangGraph is open source (MIT) and runs as a Python library inside the
operator's own process — no vendor endpoint, no telemetry, no
call-home. The framework compiles to a `StateGraph` the operator owns
end to end.
