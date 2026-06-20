# examples/n8n/it_security_support_agent

CORE-FANOUT-N8N-WIRE worked example. This directory pins the
operator-facing layout for the n8n worked example of the
`playbook.it_security_support_agent@v1` IT and security support-agent
workflow (F-WF-12; NIS2 Article 21(2)(b)). The canonical CACAO source
lives at
`../../../content/playbooks/it_security_support_agent/playbook.cacao.json`
and is mirrored here byte-identical so the diff against the emitted
artefact is easy to inspect.

## Maturity

`CORE-FANOUT-N8N-WIRE` — the n8n workflow emitter is bound and the
five action bodies carry deterministic `core_body` bindings into
`content.playbooks.it_security_support_agent.primitives.*`. The
byte-parity golden test that pins the emitted `workflow.n8n.json`
against the compiler lives under
`tests/examples/it_security_support_agent/`. The representative
per-execution interaction-evidence artefact wired against
`schemas/evidence/incidents.schema.json`, the immutable fixture, and
its byte-parity golden test land in the GOLDEN sibling that follows
this WIRE. CORE-FANOUT-TMP and CORE-FANOUT-LG follow in further
serial sibling cards.

## Layout

| Path                                       | Source compiler          | Status                                                                                |
|--------------------------------------------|--------------------------|---------------------------------------------------------------------------------------|
| `playbook.cacao.json`                      | (input mirror)           | Byte-identical mirror of the canonical playbook                                       |
| `regenerate.sh`                            | (tooling)                | Re-mirrors the canonical playbook and re-emits the worked workflow artefact           |
| `regenerate.py`                            | (tooling)                | Validates the CORE primitives binding for the GOLDEN sibling that follows this WIRE   |
| `workflow.n8n.json`                        | `compilers.n8n`          | Compiled n8n workflow JSON — Code-node bodies for the five CORE primitives            |
| `evidence/`                                | (placeholder)            | Interaction-evidence artefact materialised by the GOLDEN sibling (F-CP-02 shape)      |

## How to regenerate

From the repository root:

```sh
examples/n8n/it_security_support_agent/regenerate.sh
```

The script copies the canonical CACAO source over the local mirror
and re-emits `workflow.n8n.json` via the n8n compiler. The
per-execution interaction-evidence artefact under `evidence/` is
materialised by the GOLDEN sibling that follows this WIRE.

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

## Pending siblings

Queued serially after this WIRE merges:

- **CORE-FANOUT-N8N-GOLDEN** — interaction-evidence emitter wired
  against `schemas/evidence/incidents.schema.json`, byte-parity
  golden, and the immutable fixture.
- **CORE-FANOUT-TMP** — Temporal emitter and byte-parity golden under
  `examples/temporal/it_security_support_agent/`.
- **CORE-FANOUT-LG** — LangGraph emitter and byte-parity golden under
  `examples/langgraph/it_security_support_agent/`.
- **EXTEND-metrics** — handoff-rate / automated-resolution-rate
  KPI/KRI surface anchored against F-CP-02.
