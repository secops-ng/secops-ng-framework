# examples/n8n/vuln-intake/evidence/effectiveness

Worked example: one effectiveness evidence artifact for a
representative evaluation of the `playbook.vuln_intake@v1` playbook
compiled by the n8n reference compiler. The vuln-intake workflow
continuously evaluates one KRI — `kri.control_effectiveness` —
against the operator's pinned `risk_management_policy`
`policy_version`, so it is the canonical F-CP-06 worked path on the
n8n side and mirrors the F-CP-03 supply-chain and F-CP-05
crypto-attestation worked examples under
`examples/n8n/vuln-intake/evidence/supply-chain/` and
`examples/n8n/vuln-intake/evidence/crypto/`.

## Source

The artifact is produced by the n8n-side adapter at
`compilers/n8n/evidence/effectiveness_node.py`, which wraps the shared
emitter under `compilers/_shared/evidence/effectiveness.py`. The
adapter is invoked from an n8n workflow via an `executeCommand` or
`Code` node with a JSON-native payload describing one indicator
evaluation: the metric stable-id, the pinned subject version (policy
or prompt), the pre-computed indicator value, and the source-shape
pointer the value was derived from. The pre-computed
`measurement.value` is the snapshot — the underlying sample (which
may carry personal data) is deliberately out of scope at this layer
per AGENTS.md §3; the `measurement.source_shape` pointer is the
public-bar-safe surface a reviewer needs.

## Layout

| Path                                  | Source compiler                                  | Format        |
|---------------------------------------|--------------------------------------------------|---------------|
| `control-effectiveness-snapshot.json` | `compilers.n8n.evidence.effectiveness_node`      | evidence JSON |
| `regenerate.py`                       | (tooling)                                        | python script |

The committed snapshot is named with the human-friendly
`control-effectiveness-snapshot.json` filename for diffing; the
adapter writes it to disk as `<artifact_id>.json` where `artifact_id`
is `SHA-256(<workflow_id>|<execution_id>|<compile_target>|<metric_ref>|<subject_version.value>)`.
`captured_at` is deliberately *not* part of `artifact_id`, so
re-emissions inside a single evaluation land on the same path with
byte-stable content. The snapshot validates against
`schemas/evidence/effectiveness.schema.json` and anchors on
NIS2 Article 21(2)(f) (effectiveness measurement of cyber-risk
management measures).

## Regenerate

From the repo root:

```sh
PYTHONPATH=. python examples/n8n/vuln-intake/evidence/effectiveness/regenerate.py
```

Re-runs with the same `(workflow_id, execution_id, compile_target,
metric_ref, subject_version.value)` tuple reproduce the same artifact
byte-for-byte — the snapshot is deterministic.
