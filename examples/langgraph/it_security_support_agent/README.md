# examples/langgraph/it_security_support_agent

SKELETON-FANOUT scaffold shell. This directory pins the operator-facing
layout for the LangGraph worked example of the
`playbook.it_security_support_agent@v1` IT and security support-agent
workflow (F-WF-12; NIS2 Article 21(2)(b)). The canonical CACAO source
lives at
`../../../content/playbooks/it_security_support_agent/playbook.cacao.json`
and is mirrored here byte-identical so the diff against the eventual
emitted artefact is easy to inspect.

## Maturity

`SKELETON-FANOUT` — scaffold only for the workflow-emitter side. No
representative interaction-evidence artifact and no byte-parity
golden under `tests/examples/langgraph/it_security_support_agent/` at
this layer. The per-execution evidence artifact and the byte-parity
golden land in the CORE-FANOUT-LG sibling that follows this
SKELETON (queued serially after this SKELETON merges, to avoid
concurrent byte-parity golden churn across the three targets).

## SKELETON-layer emitter wire-up (LangGraph only)

Following the established LangGraph shell pattern, `regenerate.sh`
also drives the LangGraph emitter at the SKELETON layer to keep the
idempotency-test contract green: it mirrors the canonical CACAO
source, calls `compilers.langgraph.emit` to materialise
`graph_spec.json`, calls `compilers.langgraph.state` to materialise
`state_bindings.py`, and calls `compilers._shared.audit_mirror_cli`
to materialise the dependency-free `_audit_mirror.py` sibling. The
step-body tool stubs raise `NotImplementedError` until the
CORE-FANOUT-LG sibling that follows this SKELETON binds the
primitive set.

## Layout

| Path                       | Source compiler                       | Status at SKELETON                                                                  |
|----------------------------|---------------------------------------|-------------------------------------------------------------------------------------|
| `playbook.cacao.json`      | (input mirror)                        | Byte-identical mirror of the canonical SKELETON playbook                            |
| `regenerate.sh`            | (tooling)                             | Re-mirrors the canonical playbook and re-emits LG artefacts                         |
| `regenerate.py`            | (tooling)                             | Placeholder; no evidence emitter bound until CORE-FANOUT-LG                         |
| `graph_spec.json`          | `compilers.langgraph.emit`            | Emitted at SKELETON (topology-only — declarative placeholder step bodies)           |
| `state_bindings.py`        | `compilers.langgraph.state`           | Emitted at SKELETON (tool stubs raise NotImplementedError until CORE-FANOUT-LG)     |
| `_audit_mirror.py`         | `compilers._shared.audit_mirror_cli`  | Emitted at SKELETON (dependency-free; co-located audit-mirror sibling)              |
| `evidence/`                | (per-execution output)                | Placeholder; representative interaction-evidence artifact lands in CORE-FANOUT-LG   |

## How to regenerate (SKELETON)

From the repository root:

```sh
examples/langgraph/it_security_support_agent/regenerate.sh
```

The script copies the canonical CACAO source over the local mirror,
re-emits the GraphSpec + state-bindings stub + audit-mirror sibling
from the mirrored playbook, and is otherwise a no-op pending the
CORE-FANOUT-LG sibling. The emitted artefacts carry topology and
state-channel shape only; primitive bindings and the representative
access-evidence artifact land in CORE-FANOUT-LG.

## Source

- Canonical playbook: [`content/playbooks/it_security_support_agent/`](../../../content/playbooks/it_security_support_agent/)
- Interaction-evidence schema (reused from F-CP-02): [`schemas/evidence/incidents.schema.json`](../../../schemas/evidence/incidents.schema.json)
- Incidents evidence stream contributor home: [`content/evidence/incidents/`](../../../content/evidence/incidents/)
- Regulatory anchor (NIS2 Article 21(2)(b)): [`content/mappings/nis2/article-21-2-b.yaml`](../../../content/mappings/nis2/article-21-2-b.yaml)

## Sovereign-stack default

The ticketing source the workflow reads, the self-service surface the
workflow calls against, the responder-queue surface the human handoff
acknowledges against, and the interaction-evidence store the emitted
artifact targets are all operator-configured. No default hosted
helpdesk, no ITSM-SaaS dependency, no default non-EU endpoint, no
vendor SDK bundled. The reference LangGraph compile-target binding
lands in CORE-FANOUT-LG.
