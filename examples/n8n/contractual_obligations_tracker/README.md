# examples/n8n/contractual_obligations_tracker

SKELETON-FANOUT scaffold shell. This directory pins the operator-facing
layout for the n8n worked example of the
`playbook.contractual_obligations_tracker@v1` supplier-contract
obligations tracker workflow (F-WF-10; NIS2 Article 21(2)(d)). The
canonical CACAO source lives at
`../../../content/playbooks/contractual_obligations_tracker/playbook.cacao.json`
and is mirrored here byte-identical so the diff against the eventual
emitted artefact is easy to inspect.

## Maturity

`SKELETON-FANOUT` — scaffold only. No n8n workflow emitter
binding, no representative obligation-evidence artifact, and no
byte-parity golden under
`tests/examples/n8n/contractual_obligations_tracker/` at
this layer. The compiler emitter, the per-execution evidence
artifact, and the byte-parity golden land in the F-WF-10
CORE-FANOUT-N8N sibling card Aurora queues serially after
this SKELETON merges (to avoid concurrent byte-parity golden churn
across the three targets).

## Layout

| Path                       | Source compiler          | Status at SKELETON                                                          |
|----------------------------|--------------------------|-----------------------------------------------------------------------------|
| `playbook.cacao.json`      | (input mirror)           | Byte-identical mirror of the canonical SKELETON playbook                    |
| `regenerate.sh`            | (tooling)                | Re-mirrors the canonical playbook into this directory                       |
| `regenerate.py`            | (tooling)                | Placeholder; no evidence emitter bound until CORE-FANOUT-N8N            |
| `workflow.n8n.json`          | `compilers.n8n`             | **Not present at SKELETON.** Emitted in CORE-FANOUT-N8N.                |
| `evidence/`                | (per-execution output)   | Placeholder; representative obligation-evidence artifact lands in CORE-FANOUT-N8N |

## How to regenerate (SKELETON)

From the repository root:

```sh
examples/n8n/contractual_obligations_tracker/regenerate.sh
```

The script copies the canonical CACAO source over the local mirror so
this directory stays in sync with
`content/playbooks/contractual_obligations_tracker/`. It does **not**
emit a n8n workflow artefact at this layer — the canonical
playbook ships with declarative placeholder step bodies
(`x_secops_ng.core_body.placeholder: true`), so there are no primitive
bindings for the n8n compiler emitter to translate yet. The
emitter and the worked-artefact emission land in F-WF-10
CORE-FANOUT-N8N.

## Source

- Canonical playbook: [`content/playbooks/contractual_obligations_tracker/`](../../../content/playbooks/contractual_obligations_tracker/)
- Obligation-evidence schema: [`schemas/evidence/contractual-obligations.schema.json`](../../../schemas/evidence/contractual-obligations.schema.json)
- Evidence stream contributor home: [`content/evidence/contractual_obligations_tracker/`](../../../content/evidence/contractual_obligations_tracker/)
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

## Pending sibling

- **F-WF-10 CORE-FANOUT-N8N** — bind the n8n compiler
  emitter against the canonical primitive set, regenerate
  `workflow.n8n.json` deterministically from the canonical playbook,
  materialise one representative obligation-evidence artifact under
  `evidence/`, and pin both with a byte-parity golden under
  `tests/examples/n8n/contractual_obligations_tracker/`.
