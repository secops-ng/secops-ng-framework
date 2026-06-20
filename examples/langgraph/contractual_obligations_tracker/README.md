# examples/langgraph/contractual_obligations_tracker

Worked example for the LangGraph compilation of
`playbook.contractual_obligations_tracker@v1` — the supplier-contract
obligations tracker workflow (F-WF-10; NIS2 Article 21(2)(d)). The
canonical CACAO source lives at
`../../../content/playbooks/contractual_obligations_tracker/playbook.cacao.json`
and is mirrored here byte-identical so the diff against the emitted
artefacts is easy to inspect.

## Files in this directory

| Path                                            | Source compiler                                   | Notes                                                                                          |
|-------------------------------------------------|---------------------------------------------------|------------------------------------------------------------------------------------------------|
| `playbook.cacao.json`                           | (input mirror)                                    | Byte-identical mirror of the canonical playbook                                                |
| `graph_spec.json`                               | `compilers.langgraph.emit`                        | Target-neutral GraphSpec (nodes, edges, conditional edges) — byte-parity golden                |
| `state_bindings.py`                             | `compilers.langgraph.state`                       | Generated `TypedDict` state + `@tool`-decorated action wrappers — byte-parity golden           |
| `_audit_mirror.py`                              | `compilers._shared.audit_mirror_cli`              | Dependency-free `AuditTrail` / `AuditRecord` sibling materialised by the compiler              |
| `regenerate.sh`                                 | (tooling)                                         | Re-mirrors playbook + emits `graph_spec.json` + `state_bindings.py` + audit-mirror             |
| `regenerate.py`                                 | (tooling)                                         | Drives the LangGraph obligation-evidence node adapter end-to-end                               |
| `evidence/obligation-evidence-record.json`      | `compilers.langgraph.evidence.contractual_obligations_node` | Representative obligation-evidence artifact (byte-parity golden)                              |

## How to regenerate

After any change to the canonical playbook or to `compilers/langgraph/*`,
refresh the committed artifacts from the repository root:

```sh
./examples/langgraph/contractual_obligations_tracker/regenerate.sh
PYTHONPATH=. python examples/langgraph/contractual_obligations_tracker/regenerate.py
```

The shell script:

1. Mirrors the canonical CACAO source over `playbook.cacao.json`.
2. Emits `graph_spec.json` via `compilers.langgraph.emit`.
3. Emits `state_bindings.py` via `compilers.langgraph.state`.
4. Materialises `_audit_mirror.py` via `compilers._shared.audit_mirror_cli`.

The Python script drives the LangGraph obligation-evidence node adapter
against the representative context (re-used byte-identical from the
Temporal sibling at `examples/temporal/contractual_obligations_tracker/`)
to write one `obligation-evidence-record.json` under `evidence/`.

Regeneration is deterministic and idempotent — re-running on a clean
checkout produces byte-identical artefacts. The obligation-evidence
artifact is target-agnostic on the wire (the schema carries no
`compile_target` field), so the LangGraph, n8n, and Temporal worked
examples are byte-identical at the record level; a cross-target
byte-parity test under
`tests/examples/contractual_obligations_tracker/` pins this.

## Source

- Canonical playbook: [`content/playbooks/contractual_obligations_tracker/`](../../../content/playbooks/contractual_obligations_tracker/)
- Obligation-evidence schema: [`schemas/evidence/contractual-obligations.schema.json`](../../../schemas/evidence/contractual-obligations.schema.json)
- Contractual-obligations shared emitter: [`compilers/_shared/evidence/contractual_obligations.py`](../../../compilers/_shared/evidence/contractual_obligations.py)
- LangGraph contractual-obligations adapter: [`compilers/langgraph/evidence/contractual_obligations_node.py`](../../../compilers/langgraph/evidence/contractual_obligations_node.py)
- Regulatory anchor (NIS2 Article 21(2)(d)): [`content/mappings/nis2/article-21-2-d.yaml`](../../../content/mappings/nis2/article-21-2-d.yaml)

## Sovereign-stack default

The document-store endpoint for `ingest-contract` (the operator's
supplier-contract record store — a sovereign EU object store, an
on-prem document management system, or a Git-managed contract
repository), the operator review-policy that `schedule-review` reads,
and the artefact destination for `emit-obligation-evidence` are all
operator-configured at execution time. No default non-EU endpoint,
no hosted DMS dependency, no vendor SDK bundled. The reference
compile targets emit to whatever the operator wires; the playbook
commits to the artefact contract, not the destination.
