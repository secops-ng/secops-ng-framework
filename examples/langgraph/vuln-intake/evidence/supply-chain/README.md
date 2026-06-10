# examples/langgraph/vuln-intake/evidence/supply-chain

Worked example: one supply-chain evidence artifact for a representative
execution of the `playbook.vuln_intake@v1` playbook compiled by the
LangGraph reference compiler. The vuln-intake workflow calls external
providers during triage (CVE/EPSS data feed, optional AI risk-summary
generator), so it is the canonical F-CP-03 worked path on the LangGraph
side.

## Source

The artifact is produced by the LangGraph-side node adapter at
`compilers/langgraph/evidence/supply_chain_node.py`, which wraps the
shared emitter under `compilers/_shared/evidence/supply_chain.py`.
A preceding node — the one that performs the provider tool-call and
walks the operator's Sovereign Provider KB — assembles the typed
`SupplyChainContext` and places it on the running state under the
`supply_chain_context` key together with an `evidence_output_dir`; the
node adapter then delegates record assembly, sovereignty-band rollup,
and the atomic write to the shared helper. The per-dependency
sovereignty classification is forwarded verbatim from the KB — not
re-implemented in the example.

## Layout

| Path                          | Source compiler                                       | Format        |
|-------------------------------|-------------------------------------------------------|---------------|
| `dependencies-snapshot.json`  | `compilers.langgraph.evidence.supply_chain_node`      | evidence JSON |
| `regenerate.py`               | (tooling)                                             | python script |

The committed snapshot is named with the human-friendly
`dependencies-snapshot.json` filename for diffing; the node writes it
to disk as `<artifact_id>.json` where `artifact_id` is
`SHA-256(<workflow_id>|<execution_id>|<captured_at>)`. The snapshot
validates against `schemas/evidence/supply-chain.schema.json` and
carries the `sovereignty_classification` block populated for every
declared dependency, per NIS2 Art. 21(2)(d) and Art. 22.

## Regenerate

From the repo root:

```sh
PYTHONPATH=. python examples/langgraph/vuln-intake/evidence/supply-chain/regenerate.py
```

Re-runs with the same `(workflow_id, execution_id, captured_at)` tuple
reproduce the same artifact byte-for-byte — the snapshot is
deterministic.
