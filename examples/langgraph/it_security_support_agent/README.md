# examples/langgraph/it_security_support_agent

CORE-FANOUT-LANGGRAPH worked example. This directory pins the
operator-facing layout for the LangGraph worked example of the
`playbook.it_security_support_agent@v1` IT and security support-agent
workflow (F-WF-12; NIS2 Article 21(2)(b)). The workflow ingests a
ticket-shaped interaction, runs deterministic triage, and either
emits an automated-resolution close or an explicit hand-off to a
human responder; the per-execution interaction-evidence artefact
records both branches against the reused F-CP-02 incidents stream. The canonical CACAO source
lives at
`../../../content/playbooks/it_security_support_agent/playbook.cacao.json`
and is mirrored here byte-identical so the diff against the emitted
artefact is easy to inspect.

## Maturity

`Shipped` — the LangGraph emitter is bound, the five action bodies on
the generated `state_bindings.py` carry deterministic
`core_body` bindings into
`content.playbooks.it_security_support_agent.primitives.*` (the same
primitives the n8n and Temporal siblings bind), and the per-execution
interaction-evidence artefact is materialised through the LangGraph
node adapter at
`compilers.langgraph.evidence.emit_interaction_evidence_artifact_node`
against `schemas/evidence/incidents.schema.json` (reused F-CP-02
incidents stream). The byte-parity goldens that pin both the emitted
LangGraph artefacts (GraphSpec + state bindings) and the
interaction-evidence record live under
`tests/examples/it_security_support_agent/`; the immutable fixture
lives under `tests/fixtures/it_security_support_agent/`.

The interaction-evidence record is target-agnostic on the wire (the
schema carries no `compile_target` field), so the LangGraph, n8n, and
Temporal adapters emit byte-identical records for the same canonical
payload. This invariant is pinned by
`test_langgraph_fixture_matches_n8n_fixture` and
`test_langgraph_fixture_matches_temporal_fixture` under
`tests/examples/it_security_support_agent/`.

## Layout

| Path                                       | Source compiler                       | Status                                                                                  |
|--------------------------------------------|---------------------------------------|-----------------------------------------------------------------------------------------|
| `playbook.cacao.json`                      | (input mirror)                        | Byte-identical mirror of the canonical playbook                                         |
| `regenerate.sh`                            | (tooling)                             | Re-mirrors the canonical playbook and re-emits the worked LG artefacts + interaction artefact |
| `regenerate.py`                            | (tooling)                             | Drives the primitive chain and emits the interaction-evidence artefact (LangGraph node) |
| `graph_spec.json`                          | `compilers.langgraph.emit`            | Compiled LangGraph topology (nodes + edges) for the playbook                            |
| `state_bindings.py`                        | `compilers.langgraph.state`           | Compiled state TypedDict + `@tool`-decorated action bodies bound to the five CORE primitives |
| `_audit_mirror.py`                         | `compilers._shared.audit_mirror_cli`  | Dependency-free audit-mirror sibling (co-located observability glue)                    |
| `evidence/interaction-evidence.json`       | `compilers.langgraph.evidence`        | Representative interaction-evidence artefact (F-CP-02 incidents-stream shape)           |

## How to regenerate

From the repository root:

```sh
examples/langgraph/it_security_support_agent/regenerate.sh
```

The script copies the canonical CACAO source over the local mirror,
re-emits the GraphSpec + state-bindings + audit-mirror sibling via the
LangGraph compiler, and materialises the per-execution
interaction-evidence artefact under `evidence/`.

## Source

- Canonical playbook: [`content/playbooks/it_security_support_agent/`](../../../content/playbooks/it_security_support_agent/)
- Primitives: [`content/playbooks/it_security_support_agent/primitives/`](../../../content/playbooks/it_security_support_agent/primitives/)
- Incidents-evidence schema (reused from F-CP-02): [`schemas/evidence/incidents.schema.json`](../../../schemas/evidence/incidents.schema.json)
- Regulatory anchor (NIS2 Article 21(2)(b)): [`content/mappings/nis2/article-21-2-b.yaml`](../../../content/mappings/nis2/article-21-2-b.yaml)

## Sovereign-stack default

The ticketing source the workflow reads, the self-service surface it
walks, the responder queue it confirms acknowledgement against, and
the evidence store the emitted artifact targets are all
operator-configured. No default hosted helpdesk, no ITSM-SaaS
dependency, no default non-EU endpoint, no vendor SDK bundled. The
reference LangGraph compile target ships action-step tool bodies that
import from `content.playbooks.it_security_support_agent.primitives`;
the operator's LangGraph runtime is expected to make that package
importable alongside the graph process.

## Relation to F-WF-05 incident_management

The F-WF-05 incident-management workflow produces one incidents-stream
artifact per incident-case execution; this support-agent workflow
produces one interaction-evidence artifact per support interaction on
the same reused F-CP-02 incidents stream. A support→incident handoff
keeps `classification.significant=true` so the NIS2 Article 21(2)(b)
KPI surface counts it once on the same anchor F-WF-05 discharges; an
automated-resolution closure emits with `classification.significant=false`
on the schema's intake-only audit-close branch so the interaction is
still durable evidence without overcounting the incident KPI.
