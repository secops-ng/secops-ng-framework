# examples/n8n/vuln-intake/evidence/supply-chain

Worked example: one supply-chain evidence artifact for a representative
execution of the `playbook.vuln_intake@v1` playbook compiled by the
n8n reference compiler. The vuln-intake workflow calls external
providers during triage (CVE/EPSS data feed, optional AI risk-summary
generator), so it is the canonical F-CP-03 worked path on the n8n
side.

## Source

The artifact is produced by the n8n-side adapter at
`compilers/n8n/evidence/supply_chain_node.py`, which wraps the shared
emitter under `compilers/_shared/evidence/supply_chain.py`. The
adapter is invoked from an n8n workflow via an `executeCommand` or
`Code` node with a JSON-native payload describing the dependency
surface the execution resolved against; the per-dependency
sovereignty classification is forwarded verbatim from the operator's
Sovereign Provider KB (queried upstream of the node).

## Layout

| Path                          | Source compiler                              | Format        |
|-------------------------------|----------------------------------------------|---------------|
| `dependencies-snapshot.json`  | `compilers.n8n.evidence.supply_chain_node`   | evidence JSON |
| `regenerate.py`               | (tooling)                                    | python script |

The committed snapshot is named with the human-friendly
`dependencies-snapshot.json` filename for diffing; the adapter writes
it to disk as `<artifact_id>.json` where `artifact_id` is
`SHA-256(<workflow_id>|<execution_id>|<captured_at>)`. The snapshot
validates against `schemas/evidence/supply-chain.schema.json` and
carries the `sovereignty_classification` block populated for every
declared dependency, per NIS2 Art. 21(2)(d) and Art. 22.

## Regenerate

From the repo root:

```sh
PYTHONPATH=. python examples/n8n/vuln-intake/evidence/supply-chain/regenerate.py
```

Re-runs with the same `(workflow_id, execution_id, captured_at)` tuple
reproduce the same artifact byte-for-byte — the snapshot is
deterministic.
