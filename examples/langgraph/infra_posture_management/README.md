# examples/langgraph/infra_posture_management

Worked example for the LangGraph compilation of
`playbook.infra_posture_management@v1` — the continuous
infrastructure-posture-management workflow (F-WF-06; NIS2 Article
21(2)(a)). The canonical CACAO source lives at
`../../../content/playbooks/infra_posture_management/playbook.cacao.json`
and is mirrored here byte-identical so the diff against the emitted
artefacts is easy to inspect.

## Files in this directory

| Path                              | Source compiler                                   | Notes                                                                  |
|-----------------------------------|---------------------------------------------------|------------------------------------------------------------------------|
| `playbook.cacao.json`             | (input mirror)                                    | Byte-identical mirror of the canonical playbook                        |
| `graph_spec.json`                 | `compilers.langgraph.emit`                        | Target-neutral GraphSpec (nodes, edges, conditional edges) — byte-parity golden |
| `state_bindings.py`               | `compilers.langgraph.state`                       | Generated `TypedDict` state + `@tool`-decorated action wrappers; tool bodies call the deterministic primitives in `content.playbooks.infra_posture_management.primitives` — byte-parity golden |
| `_audit_mirror.py`                | `compilers._shared.audit_mirror_cli`              | Dependency-free `AuditTrail` / `AuditRecord` sibling materialised by the compiler |
| `regenerate.sh`                   | (tooling)                                         | Re-mirrors playbook + emits `graph_spec.json` + `state_bindings.py` + audit-mirror |
| `regenerate.py`                   | (tooling)                                         | Drives the LangGraph posture-evidence node adapter end-to-end          |
| `evidence/posture-evidence-record.json` | `compilers.langgraph.evidence.posture_node`  | Representative posture-evidence artifact (byte-parity golden)         |

## How to regenerate

After any change to the canonical playbook or to
`compilers/langgraph/*`, refresh the committed artifacts from the
repository root:

```sh
./examples/langgraph/infra_posture_management/regenerate.sh
PYTHONPATH=. python examples/langgraph/infra_posture_management/regenerate.py
```

The shell script:

1. Mirrors the canonical CACAO source over `playbook.cacao.json`.
2. Emits `graph_spec.json` via `compilers.langgraph.emit`.
3. Emits `state_bindings.py` via `compilers.langgraph.state`.
4. Materialises `_audit_mirror.py` via `compilers._shared.audit_mirror_cli`.

The Python script drives the LangGraph posture-evidence node adapter
against the representative context pinned in `regenerate.py` to write
one `posture-evidence-record.json` under `evidence/`.

Regeneration is deterministic and idempotent — re-running on a clean
checkout produces byte-identical artefacts.

Per the posture-schema's `artifact_id` contract the artifact id
derives from
`SHA-256(<workflow_id>|<execution_id>|<compile_target>|<policy_version.value>)`,
so the LangGraph artifact and the n8n / Temporal siblings carry
distinct `artifact_id`s and distinct `compile_target` fields by
design; the per-target byte-parity goldens pin each target
independently against its own adapter output.

## Source

- Canonical playbook: [`content/playbooks/infra_posture_management/`](../../../content/playbooks/infra_posture_management/)
- Posture-evidence schema: [`schemas/evidence/posture.schema.json`](../../../schemas/evidence/posture.schema.json)
- Posture shared emitter: [`compilers/_shared/evidence/posture.py`](../../../compilers/_shared/evidence/posture.py)
- LangGraph posture adapter: [`compilers/langgraph/evidence/posture_node.py`](../../../compilers/langgraph/evidence/posture_node.py)
- Regulatory anchor (NIS2 Article 21(2)(a)): [`content/mappings/nis2/article-21-2-a.yaml`](../../../content/mappings/nis2/article-21-2-a.yaml)

## Sovereign-stack default

Source endpoints for `collect-posture` (cloud-account read APIs,
identity-provider read APIs, network-baseline read APIs) and the
artefact destination for `emit-posture-evidence` are operator-configured
at execution time. No default non-EU endpoint, no hosted-SaaS
dependency, no vendor SDK bundled. The reference compile targets emit
to whatever the operator wires; the playbook commits to the artefact
contract, not the destination.
