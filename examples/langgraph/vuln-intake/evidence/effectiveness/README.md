# examples/langgraph/vuln-intake/evidence/effectiveness

Worked example: one effectiveness evidence artifact for a
representative evaluation of the `playbook.vuln_intake@v1` playbook
compiled by the LangGraph reference compiler. Mirrors the F-CP-03
supply-chain and F-CP-05 crypto-attestation LangGraph worked examples
under `examples/langgraph/vuln-intake/evidence/supply-chain/` and
`examples/langgraph/vuln-intake/evidence/crypto/`.

## Source

The artifact is produced by the LangGraph-side node adapter at
`compilers/langgraph/evidence/effectiveness_node.py`, which wraps the
shared emitter under `compilers/_shared/evidence/effectiveness.py`.
An integrator wires the node into a `StateGraph` with
`graph.add_node("emit_effectiveness", emit_effectiveness_artifact_node)`;
no LangGraph or LangChain import is required at the compiler layer.
The node reads `effectiveness_context` and `evidence_output_dir` from
the running state and returns a partial state update with the
artifact's deterministic id and on-disk path.

The pre-computed `measurement.value` is the snapshot — the underlying
sample (which may carry personal data) is deliberately out of scope
at this layer per AGENTS.md §3; the `measurement.source_shape` pointer
is the public-bar-safe surface a reviewer needs.

## Layout

| Path                                  | Source compiler                                       | Format        |
|---------------------------------------|-------------------------------------------------------|---------------|
| `control-effectiveness-snapshot.json` | `compilers.langgraph.evidence.effectiveness_node`     | evidence JSON |
| `regenerate.py`                       | (tooling)                                             | python script |

The committed snapshot is named with the human-friendly
`control-effectiveness-snapshot.json` filename for diffing; the node
writes it to disk as `<artifact_id>.json` where `artifact_id` is
`SHA-256(<workflow_id>|<execution_id>|<compile_target>|<metric_ref>|<subject_version.value>)`.
`captured_at` is deliberately *not* part of `artifact_id`, so
re-emissions inside a single evaluation land on the same path with
byte-stable content. The snapshot validates against
`schemas/evidence/effectiveness.schema.json` and anchors on
NIS2 Article 21(2)(f) (effectiveness measurement of cyber-risk
management measures).

## Regenerate

From the repo root:

```sh
PYTHONPATH=. python examples/langgraph/vuln-intake/evidence/effectiveness/regenerate.py
```

Re-runs with the same `(workflow_id, execution_id, compile_target,
metric_ref, subject_version.value)` tuple reproduce the same artifact
byte-for-byte — the snapshot is deterministic.
