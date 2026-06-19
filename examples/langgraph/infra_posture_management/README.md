# examples/langgraph/infra_posture_management

SKELETON-FANOUT scaffold shell. This directory pins the operator-facing
layout for the LangGraph worked example of the
`playbook.infra_posture_management@v1` continuous posture-management
workflow (F-WF-06). The canonical CACAO source lives at
`../../../content/playbooks/infra_posture_management/playbook.cacao.json`
and is mirrored here byte-identical so the diff against the eventual
emitted artefact is easy to inspect.

## Maturity

`SKELETON-FANOUT` — scaffold only. No LangGraph workflow emitter binding,
no representative posture-evidence artifact, and no byte-parity golden
under `tests/examples/langgraph/infra_posture_management/` at this layer.
The compiler emitter, the per-execution evidence artifact, and the
byte-parity golden land in the F-WF-06 CORE-FANOUT-LG sibling card
queued serially after this SKELETON merges (to avoid concurrent
byte-parity golden churn across the three targets).

## Layout

| Path                       | Source compiler        | Status at SKELETON                                                    |
|----------------------------|------------------------|-----------------------------------------------------------------------|
| `playbook.cacao.json`      | (input mirror)         | Byte-identical mirror of the canonical SKELETON playbook              |
| `regenerate.sh`            | (tooling)              | Re-mirrors the canonical playbook into this directory                 |
| `regenerate.py`            | (tooling)              | Placeholder; no evidence emitter bound until CORE-FANOUT-LG          |
| `graph_spec.json`        | `compilers.langgraph`        | **Not present at SKELETON.** Emitted in CORE-FANOUT-LG.              |
| `evidence/`                | (per-execution output) | Placeholder; representative posture-evidence artifact lands in CORE-FANOUT-LG |

## How to regenerate (SKELETON)

From the repository root:

```sh
examples/langgraph/infra_posture_management/regenerate.sh
```

The script copies the canonical CACAO source over the local mirror so
this directory stays in sync with `content/playbooks/infra_posture_management/`.
It does **not** emit an LangGraph workflow artefact at this layer — the
canonical playbook ships with declarative placeholder step bodies
(`x_secops_ng.core_body.placeholder: true`), so there are no primitive
bindings for the LangGraph compiler emitter to translate yet. The emitter
and the worked-artefact emission land in F-WF-06 CORE-FANOUT-LG.

## Source

- Canonical playbook: [`content/playbooks/infra_posture_management/`](../../../content/playbooks/infra_posture_management/)
- Posture-evidence schema: [`schemas/evidence/posture.schema.json`](../../../schemas/evidence/posture.schema.json)
- Evidence stream contributor home: [`content/evidence/infra_posture_management/`](../../../content/evidence/infra_posture_management/)
- Regulatory anchor (NIS2 Article 21(2)(a)): [`content/mappings/nis2/article-21-2-a.yaml`](../../../content/mappings/nis2/article-21-2-a.yaml)

## Sovereign-stack default

Source endpoints for `collect-posture` (cloud-account read APIs,
identity-provider read APIs, network-baseline read APIs) and the
artefact destination for `emit-posture-evidence` are operator-configured
at execution time. No default non-EU endpoint, no hosted-SaaS dependency,
no vendor SDK bundled. The reference compile targets emit to whatever
the operator wires; the playbook commits to the artefact contract, not
the destination.

## Pending sibling

- **F-WF-06 CORE-FANOUT-LG** — bind the LangGraph compiler emitter against
  the canonical primitive set, regenerate `graph_spec.json`
  deterministically from the canonical playbook, materialise one
  representative posture-evidence artifact under `evidence/`, and pin
  both with a byte-parity golden under
  `tests/examples/langgraph/infra_posture_management/`.
