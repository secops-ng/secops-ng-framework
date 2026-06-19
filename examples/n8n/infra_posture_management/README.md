# examples/n8n/infra_posture_management

Worked example for the n8n compilation of
`playbook.infra_posture_management@v1` — the continuous
infrastructure-posture-management workflow (F-WF-06; NIS2 Article
21(2)(a)). The canonical CACAO source lives at
`../../../content/playbooks/infra_posture_management/playbook.cacao.json`
and is mirrored here byte-identical so the diff against the emitted
artefacts is easy to inspect.

## Layout

| Path                              | Source compiler        | Notes                                                                 |
|-----------------------------------|------------------------|-----------------------------------------------------------------------|
| `playbook.cacao.json`             | (input mirror)         | Byte-identical mirror of the canonical playbook                       |
| `regenerate.sh`                   | (tooling)              | Re-mirrors playbook + emits workflow + emits posture artefact         |
| `regenerate.py`                   | (tooling)              | Drives the n8n posture adapter against a representative payload      |
| `workflow.n8n.json`               | `compilers.n8n`        | Emitted n8n workflow JSON (byte-parity golden)                       |
| `evidence/posture-evidence-record.json` | `compilers.n8n.evidence.posture_node` | Representative posture-evidence artefact (byte-parity golden) |

## How to regenerate

From the repository root:

```sh
examples/n8n/infra_posture_management/regenerate.sh
```

The script:

1. Mirrors the canonical CACAO source over `playbook.cacao.json`.
2. Emits `workflow.n8n.json` via `python -m tools.compile --target n8n`.
3. Drives the n8n posture adapter against the representative payload
   pinned in `regenerate.py` to write one
   `posture-evidence-record.json` under `evidence/`.

Regeneration is deterministic and idempotent — re-running the script
on a clean checkout produces byte-identical artefacts.

## Source

- Canonical playbook: [`content/playbooks/infra_posture_management/`](../../../content/playbooks/infra_posture_management/)
- Posture-evidence schema: [`schemas/evidence/posture.schema.json`](../../../schemas/evidence/posture.schema.json)
- Posture shared emitter: [`compilers/_shared/evidence/posture.py`](../../../compilers/_shared/evidence/posture.py)
- n8n posture adapter: [`compilers/n8n/evidence/posture_node.py`](../../../compilers/n8n/evidence/posture_node.py)
- Regulatory anchor (NIS2 Article 21(2)(a)): [`content/mappings/nis2/article-21-2-a.yaml`](../../../content/mappings/nis2/article-21-2-a.yaml)

## Sovereign-stack default

Source endpoints for `collect-posture` (cloud-account read APIs,
identity-provider read APIs, network-baseline read APIs) and the
artefact destination for `emit-posture-evidence` are operator-configured
at execution time. No default non-EU endpoint, no hosted-SaaS dependency,
no vendor SDK bundled. The reference compile targets emit to whatever
the operator wires; the playbook commits to the artefact contract, not
the destination.
