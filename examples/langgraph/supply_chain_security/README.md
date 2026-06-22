# examples/langgraph/supply_chain_security

LangGraph worked example for the `playbook.supply_chain_security@v1`
supply-chain-security workflow (F-WF-SCS; NIS2 Article 21(2)(d)).

## Maturity

`CORE-FANOUT-LANGGRAPH` — the LangGraph compile-target binding for the
canonical CACAO playbook. The LangGraph compiler emits the target-
neutral GraphSpec and the typed state bindings deterministically from
the canonical playbook; the two CORE tool bodies bind to
`content.playbooks.supply_chain_security.primitives.assess.assess_supplier_signal`
and
`content.playbooks.supply_chain_security.primitives.artifact.build_supply_chain_evidence_artifact`.
The LangGraph node adapter at
`compilers.langgraph.evidence.emit_supply_chain_artifact_node`
delegates to the framework-agnostic F-CP-03 shared emitter under
`compilers._shared.evidence.supply_chain` so the per-execution
supply-chain-evidence artifact is byte-stable across replays.

This card closes G-03 three-target parity for this workflow alongside
the n8n sibling at `examples/n8n/supply_chain_security/` (PR #420) and
the Temporal sibling at `examples/temporal/supply_chain_security/`
(PR #421). The full cross-target byte-parity ring is closed across
all three reference compilers under F-WF-SCS (see ROADMAP.md
F-WF-SCS).

## Layout

| Path                                          | Source                          | Contents                                                                                  |
|-----------------------------------------------|---------------------------------|-------------------------------------------------------------------------------------------|
| `playbook.cacao.json`                         | (input mirror)                  | Byte-identical mirror of the canonical playbook                                           |
| `graph_spec.json`                             | `compilers.langgraph.emit`      | Target-neutral GraphSpec (nodes, edges, conditional edges) — byte-parity golden           |
| `state_bindings.py`                           | `compilers.langgraph.state`     | Generated `TypedDict` state + `@tool`-decorated action wrappers — byte-parity golden      |
| `_audit_mirror.py`                            | `compilers._shared.audit_mirror_cli` | Dependency-free `AuditTrail` / `AuditRecord` sibling materialised by the compiler   |
| `evidence/supply-chain-evidence.json`         | `compilers.langgraph.evidence`  | One representative supply-chain-evidence artifact (F-CP-03 supply-chain-stream shape)     |
| `regenerate.sh`                               | (tooling)                       | Re-mirrors the canonical playbook and re-emits the worked graph + state + artefact        |
| `regenerate.py`                               | (tooling)                       | Drives the F-WF-SCS primitive chain and emits the artefact via the LangGraph node adapter |

## How to regenerate

From the repository root:

```sh
./examples/langgraph/supply_chain_security/regenerate.sh
```

The script copies the canonical CACAO source over the local mirror,
re-emits `graph_spec.json` via `compilers.langgraph.emit`, re-emits
`state_bindings.py` via `compilers.langgraph.state`, materialises
`_audit_mirror.py` via `compilers._shared.audit_mirror_cli`, and
re-emits the per-execution supply-chain-evidence artefact under
`evidence/` through the F-CP-03 LangGraph node adapter.

The committed `supply-chain-evidence.json` is the node adapter's
output renamed for human-friendly diffing; the deterministic
`<artifact_id>.json` written by the node is dropped after the copy.

Regeneration is deterministic and idempotent — re-running on a clean
checkout produces byte-identical artefacts.

## Source

- Canonical playbook: [`content/playbooks/supply_chain_security/`](../../../content/playbooks/supply_chain_security/)
- Primitives: [`content/playbooks/supply_chain_security/primitives/`](../../../content/playbooks/supply_chain_security/primitives/)
- Supply-chain-evidence schema (F-CP-03): [`schemas/evidence/supply-chain.schema.json`](../../../schemas/evidence/supply-chain.schema.json)
- LangGraph supply-chain adapter: [`compilers/langgraph/evidence/supply_chain_node.py`](../../../compilers/langgraph/evidence/supply_chain_node.py)
- Regulatory anchor (NIS2 Article 21(2)(d)): [`content/mappings/nis2/article-21-2-d.yaml`](../../../content/mappings/nis2/article-21-2-d.yaml)
- Byte-parity fixture: [`tests/fixtures/supply_chain_security/langgraph.supply-chain-evidence-record.json`](../../../tests/fixtures/supply_chain_security/langgraph.supply-chain-evidence-record.json)
- n8n sibling: [`examples/n8n/supply_chain_security/`](../../n8n/supply_chain_security/)
- Temporal sibling: [`examples/temporal/supply_chain_security/`](../../temporal/supply_chain_security/)

## Sovereign-stack default

The signal-feed source the workflow reads, the SBOM-correlation /
supplier-attestation lookup logic the operator runs upstream of
`assess-supplier-signal`, and the evidence-store destination the
node adapter writes to are all operator-configured at execution time.
No default hosted feed, no SBOM-correlation SaaS dependency, no
default non-EU endpoint, no vendor SDK bundled. The reference
LangGraph compile target emits state bindings whose `@tool` bodies
import from `content.playbooks.supply_chain_security.primitives`; the
operator's LangGraph runtime is expected to make that package
importable on the worker's PYTHONPATH.

## Pending siblings

- **F-WF-SCS EXTEND** — OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA
  inbound + outbound mapping closure, `metric_refs` pinning the
  supplier-attestation-staleness KRI and the supply-chain coverage
  KPI, and the cross-target byte-parity goldens that close the n8n /
  Temporal / LangGraph parity ring.
