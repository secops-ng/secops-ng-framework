# examples/temporal/supply_chain_security

Temporal worked example for the `playbook.supply_chain_security@v1`
supply-chain-security workflow (F-WF-SCS; NIS2 Article 21(2)(d)).

## Maturity

`CORE-FANOUT-TMP` — the Temporal compile target binding for the
canonical CACAO playbook. The Temporal compiler emits the workflow
stub deterministically from the canonical playbook; the two CORE
activity bodies bind to
`content.playbooks.supply_chain_security.primitives.assess.assess_supplier_signal`
and
`content.playbooks.supply_chain_security.primitives.artifact.build_supply_chain_evidence_artifact`.
The Temporal activity adapter at
`compilers.temporal.evidence.emit_supply_chain_artifact_activity`
delegates to the framework-agnostic F-CP-03 shared emitter under
`compilers._shared.evidence.supply_chain` so the per-execution
supply-chain-evidence artifact is byte-stable across replays.

The n8n sibling lands at `examples/n8n/supply_chain_security/` and
the LangGraph sibling at `examples/langgraph/supply_chain_security/`;
the cross-target byte-parity ring is closed across all three reference
compilers under F-WF-SCS (see ROADMAP.md F-WF-SCS).

## Layout

| Path                                          | Source                        | Contents                                                                                  |
|-----------------------------------------------|-------------------------------|-------------------------------------------------------------------------------------------|
| `playbook.cacao.json`                         | (input mirror)                | Byte-identical mirror of the canonical playbook                                           |
| `workflow.temporal.py`                        | `compilers.temporal`          | Temporal workflow stub emitted from the canonical playbook                                |
| `evidence/supply-chain-evidence.json`         | `compilers.temporal.evidence` | One representative supply-chain-evidence artifact (F-CP-03 supply-chain-stream shape)     |
| `regenerate.sh`                               | (tooling)                     | Re-mirrors the canonical playbook and re-emits the worked workflow + artefact             |
| `regenerate.py`                               | (tooling)                     | Drives the F-WF-SCS primitive chain and emits the artefact via the Temporal activity      |

## How to regenerate

From the repository root:

```sh
./examples/temporal/supply_chain_security/regenerate.sh
```

The script copies the canonical CACAO source over the local mirror,
re-emits `workflow.temporal.py` via the Temporal compiler, and
materialises the per-execution supply-chain-evidence artefact under
`evidence/` through the F-CP-03 Temporal activity adapter.

The committed `supply-chain-evidence.json` is the activity's output
renamed for human-friendly diffing; the deterministic
`<artifact_id>.json` written by the activity is dropped after the
copy.

## Source

- Canonical playbook: [`content/playbooks/supply_chain_security/`](../../../content/playbooks/supply_chain_security/)
- Primitives: [`content/playbooks/supply_chain_security/primitives/`](../../../content/playbooks/supply_chain_security/primitives/)
- Supply-chain-evidence schema (F-CP-03): [`schemas/evidence/supply-chain.schema.json`](../../../schemas/evidence/supply-chain.schema.json)
- Regulatory anchor (NIS2 Article 21(2)(d)): [`content/mappings/nis2/article-21-2-d.yaml`](../../../content/mappings/nis2/article-21-2-d.yaml)
- Byte-parity fixture: [`tests/fixtures/supply_chain_security/temporal.supply-chain-evidence-record.json`](../../../tests/fixtures/supply_chain_security/temporal.supply-chain-evidence-record.json)
- n8n sibling: [`examples/n8n/supply_chain_security/`](../../n8n/supply_chain_security/)

## Sovereign-stack default

The signal-feed source the workflow reads, the SBOM-correlation /
supplier-attestation lookup logic the operator runs upstream of
`assess-supplier-signal`, and the evidence-store destination the
activity writes to are all operator-configured at execution time. No
default hosted feed, no SBOM-correlation SaaS dependency, no default
non-EU endpoint, no vendor SDK bundled. The reference Temporal
compile target ships an activity stub that imports from
`content.playbooks.supply_chain_security.primitives`; the operator's
Temporal worker is expected to make that package importable on the
worker's PYTHONPATH.

## Sibling targets

- **LangGraph sibling:** [`examples/langgraph/supply_chain_security/`](../../langgraph/supply_chain_security/)
  closes the third compile-target binding for the same primitive chain.

## Pending siblings

- **F-WF-SCS EXTEND** — OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA
  inbound + outbound mapping closure, `metric_refs` pinning the
  supplier-attestation-staleness KRI and the supply-chain coverage
  KPI, and the cross-target byte-parity goldens that close the n8n /
  Temporal / LangGraph parity ring.
