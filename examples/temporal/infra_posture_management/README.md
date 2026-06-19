# examples/temporal/infra_posture_management

Worked example for the Temporal compilation of
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
| `regenerate.py`                   | (tooling)              | Drives the Temporal posture activity adapter                          |
| `workflow.temporal.py`            | `compilers.temporal`   | Emitted Temporal workflow stub (byte-parity golden)                  |
| `evidence/posture-evidence-record.json` | `compilers.temporal.evidence.posture_activity` | Representative posture-evidence artefact (byte-parity golden) |

## How to regenerate

From the repository root:

```sh
examples/temporal/infra_posture_management/regenerate.sh
```

The script:

1. Mirrors the canonical CACAO source over `playbook.cacao.json`.
2. Emits `workflow.temporal.py` via `python -m tools.compile --target temporal`.
3. Drives the Temporal posture activity adapter against the
   representative context pinned in `regenerate.py` to write one
   `posture-evidence-record.json` under `evidence/`.

Regeneration is deterministic and idempotent — re-running the script
on a clean checkout produces byte-identical artefacts.

Per the posture-schema's `artifact_id` contract the artifact id derives
from
`SHA-256(<workflow_id>|<execution_id>|<compile_target>|<policy_version.value>)`,
so the Temporal artifact and the n8n / LangGraph siblings carry
distinct `artifact_id`s and distinct `compile_target` fields by design;
the per-target byte-parity goldens pin each target independently
against its own adapter output.

## Source

- Canonical playbook: [`content/playbooks/infra_posture_management/`](../../../content/playbooks/infra_posture_management/)
- Posture-evidence schema: [`schemas/evidence/posture.schema.json`](../../../schemas/evidence/posture.schema.json)
- Posture shared emitter: [`compilers/_shared/evidence/posture.py`](../../../compilers/_shared/evidence/posture.py)
- Temporal posture adapter: [`compilers/temporal/evidence/posture_activity.py`](../../../compilers/temporal/evidence/posture_activity.py)
- Regulatory anchor (NIS2 Article 21(2)(a)): [`content/mappings/nis2/article-21-2-a.yaml`](../../../content/mappings/nis2/article-21-2-a.yaml)

## Sovereign-stack default

Source endpoints for `collect-posture` and the artefact destination for
`emit-posture-evidence` are operator-configured at execution time. No
default non-EU endpoint, no hosted-SaaS dependency, no vendor SDK
bundled. The reference compile targets emit to whatever the operator
wires; the playbook commits to the artefact contract, not the
destination.
