# examples/temporal/it_security_support_agent

SKELETON-FANOUT scaffold shell. This directory pins the operator-facing
layout for the Temporal worked example of the
`playbook.it_security_support_agent@v1` IT and security support-agent
workflow (F-WF-12; NIS2 Article 21(2)(b)). The canonical CACAO source
lives at
`../../../content/playbooks/it_security_support_agent/playbook.cacao.json`
and is mirrored here byte-identical so the diff against the eventual
emitted artefact is easy to inspect.

## Maturity

`SKELETON-FANOUT` — scaffold only. No Temporal workflow emitter
binding, no representative interaction-evidence artifact, and no
byte-parity golden under `tests/examples/temporal/it_security_support_agent/`
at this layer. The compiler emitter, the per-execution evidence
artifact, and the byte-parity golden land in the CORE-FANOUT-TMP
sibling that follows this SKELETON (queued serially after this
SKELETON merges, to avoid concurrent byte-parity golden churn across
the three targets).

## Layout

| Path                       | Source compiler          | Status at SKELETON                                                                |
|----------------------------|--------------------------|-----------------------------------------------------------------------------------|
| `playbook.cacao.json`      | (input mirror)           | Byte-identical mirror of the canonical SKELETON playbook                          |
| `regenerate.sh`            | (tooling)                | Re-mirrors the canonical playbook into this directory                             |
| `regenerate.py`            | (tooling)                | Placeholder; no evidence emitter bound until CORE-FANOUT-TMP                      |
| `workflow.temporal.py`     | `compilers.temporal`     | **Not present at SKELETON.** Emitted in CORE-FANOUT-TMP.                          |
| `evidence/`                | (per-execution output)   | Placeholder; representative interaction-evidence artifact lands in CORE-FANOUT-TMP |

## How to regenerate (SKELETON)

From the repository root:

```sh
examples/temporal/it_security_support_agent/regenerate.sh
```

The script copies the canonical CACAO source over the local mirror so
this directory stays in sync with
`content/playbooks/it_security_support_agent/`. It does **not**
emit a Temporal workflow artefact at this layer — the canonical
playbook ships with declarative placeholder step bodies (no
`core_body` bindings), so there are no primitive bindings for the
Temporal compiler emitter to translate yet. The emitter and the
worked-artefact emission land in CORE-FANOUT-TMP.

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
vendor SDK bundled. The reference Temporal compile-target binding
lands in CORE-FANOUT-TMP.
