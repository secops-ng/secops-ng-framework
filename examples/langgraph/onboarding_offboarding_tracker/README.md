# examples/langgraph/onboarding_offboarding_tracker

Worked example of the on-boarding / off-boarding tracker workflow
(F-WF-11; NIS2 Article 21(2)(i)) compiled for the LangGraph target.
The canonical CACAO source lives at
`../../../content/playbooks/onboarding_offboarding_tracker/playbook.cacao.json`
and is mirrored here byte-identical so the diff against the emitted
artefacts is easy to inspect.

## Maturity

`CORE-FANOUT-LANGGRAPH` — LangGraph compiler emitter bound to the
deterministic primitive set under
`content/playbooks/onboarding_offboarding_tracker/primitives/`, with
the representative per-execution access-evidence artifact under
`evidence/` and the byte-parity goldens under
`tests/examples/onboarding_offboarding_tracker/`. The closeout
sibling (ROADMAP flip, EXTEND-metrics, cookbook docs) follows in a
separate card once all three CORE-FANOUT targets are merged.

## Files in this directory

| Path                              | Source compiler                                  | Notes                                                                                          |
|-----------------------------------|--------------------------------------------------|------------------------------------------------------------------------------------------------|
| `playbook.cacao.json`             | (input mirror)                                   | Byte-identical mirror of the canonical playbook                                                |
| `graph_spec.json`                 | `compilers.langgraph.emit`                       | Target-neutral GraphSpec (nodes, edges, conditional edges) — byte-parity golden                |
| `state_bindings.py`               | `compilers.langgraph.state`                      | Generated `TypedDict` state + `@tool`-decorated action wrappers — byte-parity golden           |
| `_audit_mirror.py`                | `compilers._shared.audit_mirror_cli`             | Dependency-free `AuditTrail` / `AuditRecord` sibling materialised by the compiler              |
| `regenerate.sh`                   | (tooling)                                        | Re-mirrors the canonical playbook and re-emits the LangGraph artefacts                         |
| `regenerate.py`                   | (tooling)                                        | Drives the LangGraph access-evidence node adapter for the representative joiner execution     |
| `evidence/access-evidence.json`   | `compilers.langgraph.evidence.access_node`       | Representative per-execution access-evidence artifact (byte-parity golden)                     |

## How to regenerate

After any change to the canonical playbook or to `compilers/langgraph/*`,
refresh the committed artifacts from the repository root:

```sh
./examples/langgraph/onboarding_offboarding_tracker/regenerate.sh
PYTHONPATH=. python examples/langgraph/onboarding_offboarding_tracker/regenerate.py
```

The shell script:

1. Mirrors the canonical CACAO source over `playbook.cacao.json`.
2. Emits `graph_spec.json` via `compilers.langgraph.emit`.
3. Emits `state_bindings.py` via `compilers.langgraph.state`.
4. Materialises `_audit_mirror.py` via `compilers._shared.audit_mirror_cli`.

The Python script drives the LangGraph access-evidence node adapter
against the representative joiner context — same primitive chain
(`ingest_lifecycle_event` → `resolve_identity` → `apply_capability_delta`
→ `confirm_grant_revoke`) the n8n and Temporal siblings exercise — to
write one `access-evidence.json` under `evidence/`.

Regeneration is deterministic and idempotent — re-running on a clean
checkout produces byte-identical artefacts. The on-disk bytes are
pinned by tests at `tests/examples/onboarding_offboarding_tracker/`.

## Source

- Canonical playbook: [`content/playbooks/onboarding_offboarding_tracker/`](../../../content/playbooks/onboarding_offboarding_tracker/)
- Access-evidence schema (reused from F-CP-07): [`schemas/evidence/access.schema.json`](../../../schemas/evidence/access.schema.json)
- Access evidence stream contributor home: [`content/evidence/access/`](../../../content/evidence/access/)
- Shared access-evidence emitter: [`compilers/_shared/evidence/access.py`](../../../compilers/_shared/evidence/access.py)
- LangGraph access-evidence node adapter: [`compilers/langgraph/evidence/access_node.py`](../../../compilers/langgraph/evidence/access_node.py)
- Regulatory anchor (NIS2 Article 21(2)(i)): [`content/mappings/nis2/article-21-2-i.yaml`](../../../content/mappings/nis2/article-21-2-i.yaml)
- Sibling n8n worked example: [`../../n8n/onboarding_offboarding_tracker/`](../../n8n/onboarding_offboarding_tracker/)
- Sibling Temporal worked example: [`../../temporal/onboarding_offboarding_tracker/`](../../temporal/onboarding_offboarding_tracker/)

## Cross-target shape parity

The committed access-evidence record is shape-identical to the n8n
and Temporal siblings on every field except the three the schema's
`artifact_id` derivation joins on (`workflow_id, execution_id,
compile_target`). That cross-target shape parity is pinned by
`tests/examples/onboarding_offboarding_tracker/test_langgraph_access_evidence.py::test_langgraph_fixture_matches_n8n_fixture`.
All three adapters drive the same shared helper
(`compilers._shared.evidence.emit_access_artifact`) from the same
primitive chain
(`content.playbooks.onboarding_offboarding_tracker.primitives`); a
drift on the cross-target parity test means one adapter started
rewriting payload fields the shared helper does not.

## Sovereign-stack default

The identity source the workflow reads and writes, and the
access-evidence store the emitted artifact targets, are
operator-configured. No default hosted IdP, no HR-SaaS dependency, no
default non-EU endpoint, no vendor SDK bundled. Pending closeout
sibling: ROADMAP flip + EXTEND-metrics + cookbook docs once all three
CORE-FANOUT targets are merged.
