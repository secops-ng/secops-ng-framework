# examples/n8n/it_security_support_agent

CORE-FANOUT-N8N worked example. This directory pins the
operator-facing layout for the n8n worked example of the
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

`Shipped` — the n8n workflow emitter is bound, the five action
bodies carry deterministic `core_body` bindings into
`content.playbooks.it_security_support_agent.primitives.*`, and the
per-execution interaction-evidence artefact is materialised through
the n8n adapter at
`compilers.n8n.evidence.emit_interaction_evidence_artifact_n8n`
against `schemas/evidence/incidents.schema.json` (reused F-CP-02
incidents stream). The byte-parity goldens that pin both the emitted
`workflow.n8n.json` and the interaction-evidence record live under
`tests/examples/it_security_support_agent/`; the immutable fixture
lives under `tests/fixtures/it_security_support_agent/`.

The Temporal and LangGraph siblings ship the same primitives against
the same incidents-stream schema; the three-target byte-parity ring
is closed by `test_n8n_fixture_matches_temporal_fixture` and
`test_langgraph_fixture_matches_n8n_fixture` under
`tests/examples/it_security_support_agent/`.

## Layout

| Path                                       | Source compiler          | Status                                                                                |
|--------------------------------------------|--------------------------|---------------------------------------------------------------------------------------|
| `playbook.cacao.json`                      | (input mirror)           | Byte-identical mirror of the canonical playbook                                       |
| `regenerate.sh`                            | (tooling)                | Re-mirrors the canonical playbook and re-emits the worked workflow + artefact         |
| `regenerate.py`                            | (tooling)                | Drives the primitive chain and emits the interaction-evidence artefact (n8n adapter)  |
| `workflow.n8n.json`                        | `compilers.n8n`          | Compiled n8n workflow JSON — Code-node bodies for the five CORE primitives            |
| `evidence/interaction-evidence.json`       | `compilers.n8n.evidence` | Representative interaction-evidence artefact (F-CP-02 incidents-stream shape)         |

## How to regenerate

From the repository root:

```sh
examples/n8n/it_security_support_agent/regenerate.sh
```

The script copies the canonical CACAO source over the local mirror,
re-emits `workflow.n8n.json` via the n8n compiler, and materialises
the per-execution interaction-evidence artefact under `evidence/`.

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
reference n8n compile target ships Code-node bodies that import from
`content.playbooks.it_security_support_agent.primitives`; the
operator's runtime is expected to make that package importable
alongside the n8n instance.

## Relation to F-WF-05 incident_management

The F-WF-05 incident-management workflow produces one incidents-stream
artifact per incident-case execution (NIS2 Article 21(2)(b) +
Article 23 lifecycle + notification timeline). This workflow produces
one incidents-stream artifact per support interaction — on an
incident-shaped classification or a `handoff_fired=true` path the
artifact lands with `classification.significant=true` on the same
F-CP-02 KPI surface, on the automated-resolution closure path the
artifact lands with `classification.significant=false` (the schema's
intake-only audit-close branch) so the KPI surface does not
overcount. Both workflows anchor onto
`schemas/evidence/incidents.schema.json` and the same NIS2 Article
21(2)(b) anchor.
