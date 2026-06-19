# examples/temporal/vuln_intake/evidence/supply-chain

Worked example: one supply-chain evidence artifact for a representative
execution of the `playbook.vuln_intake@v1` playbook compiled by the
Temporal reference compiler. The vuln_intake workflow calls external
providers during triage (CVE/EPSS data feed, optional AI risk-summary
generator), so it is the canonical F-CP-03 worked path on the Temporal
side.

## Source

The artifact is produced by the Temporal-side activity at
`compilers/temporal/evidence/supply_chain_activity.py`, which wraps
the shared emitter under `compilers/_shared/evidence/supply_chain.py`.
The activity is scheduled from a Temporal workflow with a typed
`SupplyChainContext` describing the dependency surface the execution
resolved against; the per-dependency sovereignty classification is
forwarded verbatim from the operator's Sovereign Provider KB (queried
upstream of the activity).

## Layout

| Path                          | Source compiler                                    | Format        |
|-------------------------------|----------------------------------------------------|---------------|
| `dependencies-snapshot.json`  | `compilers.temporal.evidence.supply_chain_activity`| evidence JSON |
| `regenerate.py`               | (tooling)                                          | python script |

The committed snapshot is named with the human-friendly
`dependencies-snapshot.json` filename for diffing; the activity writes
it to disk as `<artifact_id>.json` where `artifact_id` is
`SHA-256(<workflow_id>|<execution_id>|<captured_at>)`. The snapshot
validates against `schemas/evidence/supply-chain.schema.json` and
carries the `sovereignty_classification` block populated for every
declared dependency, per NIS2 Art. 21(2)(d) and Art. 22.

## Regenerate

From the repo root:

```sh
PYTHONPATH=. python examples/temporal/vuln_intake/evidence/supply-chain/regenerate.py
```

Re-runs with the same `(workflow_id, execution_id, captured_at)` tuple
reproduce the same artifact byte-for-byte — the snapshot is
deterministic.
