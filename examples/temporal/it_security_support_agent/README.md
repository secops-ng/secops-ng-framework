# examples/temporal/it_security_support_agent

CORE-FANOUT-TEMPORAL worked example. This directory pins the
operator-facing layout for the Temporal worked example of the
`playbook.it_security_support_agent@v1` IT and security support-agent
workflow (F-WF-12; NIS2 Article 21(2)(b)). The canonical CACAO source
lives at
`../../../content/playbooks/it_security_support_agent/playbook.cacao.json`
and is mirrored here byte-identical so the diff against the emitted
artefact is easy to inspect.

## Maturity

`CORE-FANOUT-TEMPORAL` — the Temporal workflow emitter is bound, the
five action bodies carry deterministic `core_body` bindings into
`content.playbooks.it_security_support_agent.primitives.*` (the same
primitives the n8n sibling binds), and the per-execution
interaction-evidence artefact is materialised through the Temporal
activity at
`compilers.temporal.evidence.emit_interaction_evidence_artifact_activity`
against `schemas/evidence/incidents.schema.json` (reused F-CP-02
incidents stream). The byte-parity goldens that pin both the emitted
`workflow.temporal.py` stub and the interaction-evidence record live
under `tests/examples/it_security_support_agent/`; the immutable
fixture lives under `tests/fixtures/it_security_support_agent/`.
CORE-FANOUT-LG follows in a further serial sibling card.

The interaction-evidence record is target-agnostic on the wire (the
schema carries no `compile_target` field), so the Temporal and n8n
adapters emit byte-identical records for the same canonical payload.
This invariant is pinned by
`test_temporal_fixture_matches_n8n_fixture` under
`tests/examples/it_security_support_agent/`.

## Layout

| Path                                       | Source compiler                  | Status                                                                                  |
|--------------------------------------------|----------------------------------|-----------------------------------------------------------------------------------------|
| `playbook.cacao.json`                      | (input mirror)                   | Byte-identical mirror of the canonical playbook                                         |
| `regenerate.sh`                            | (tooling)                        | Re-mirrors the canonical playbook and re-emits the worked workflow stub + artefact      |
| `regenerate.py`                            | (tooling)                        | Drives the primitive chain and emits the interaction-evidence artefact (Temporal adapter) |
| `workflow.temporal.py`                     | `compilers.temporal`             | Compiled Temporal workflow stub — activity bodies bound to the five CORE primitives     |
| `evidence/interaction-evidence.json`       | `compilers.temporal.evidence`    | Representative interaction-evidence artefact (F-CP-02 incidents-stream shape)           |

## How to regenerate

From the repository root:

```sh
examples/temporal/it_security_support_agent/regenerate.sh
```

The script copies the canonical CACAO source over the local mirror,
re-emits `workflow.temporal.py` via the Temporal compiler, and
materialises the per-execution interaction-evidence artefact under
`evidence/`.

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
reference Temporal compile target ships activity bodies that import
from `content.playbooks.it_security_support_agent.primitives`; the
operator's Temporal worker is expected to make that package importable
alongside the worker process.

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

Queued serially after this CORE-FANOUT-TEMPORAL merges:

- **CORE-FANOUT-LG** — LangGraph emitter and byte-parity golden under
  `examples/langgraph/it_security_support_agent/`.
- **EXTEND-metrics** — handoff-rate / automated-resolution-rate
  KPI/KRI surface anchored against F-CP-02.
