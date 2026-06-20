# examples/temporal/onboarding_offboarding_tracker

Worked example of the on-boarding / off-boarding tracker workflow
(F-WF-11; NIS2 Article 21(2)(i)) compiled for the Temporal target.
The canonical CACAO source lives at
`../../../content/playbooks/onboarding_offboarding_tracker/playbook.cacao.json`
and is mirrored here byte-identical so the diff against the emitted
artefact is easy to inspect.

## Maturity

`CORE-FANOUT-TEMPORAL` — Temporal compiler emitter bound to the
deterministic primitive set under
`content/playbooks/onboarding_offboarding_tracker/primitives/`, with
the representative per-execution access-evidence artifact under
`evidence/` and the byte-parity goldens under
`tests/examples/onboarding_offboarding_tracker/`. CORE-FANOUT-LG and
the EXTEND siblings (schema, metrics, docs-closeout) follow in
separate serial cards.

## Layout

| Path                       | Source compiler          | Status                                                                 |
|----------------------------|--------------------------|------------------------------------------------------------------------|
| `playbook.cacao.json`      | (input mirror)           | Byte-identical mirror of the canonical playbook                        |
| `regenerate.sh`            | (tooling)                | Re-mirrors the canonical playbook and re-emits the Temporal artefact   |
| `regenerate.py`            | (tooling)                | Re-drives the Temporal activity adapter for the access-evidence record |
| `workflow.temporal.py`     | `compilers.temporal`     | Emitted Temporal workflow stub                                         |
| `evidence/access-evidence.json` | `compilers.temporal.evidence` | Representative per-execution access-evidence artifact            |

## How to regenerate

From the repository root:

```sh
examples/temporal/onboarding_offboarding_tracker/regenerate.sh
```

The script copies the canonical CACAO source over the local mirror,
re-emits `workflow.temporal.py` via
`python -m tools.compile --target temporal`, and re-drives the
access-evidence record via the sibling `regenerate.py`. The on-disk
bytes are pinned by tests at
`tests/examples/onboarding_offboarding_tracker/`.

## Source

- Canonical playbook: [`content/playbooks/onboarding_offboarding_tracker/`](../../../content/playbooks/onboarding_offboarding_tracker/)
- Access-evidence schema (reused from F-CP-07): [`schemas/evidence/access.schema.json`](../../../schemas/evidence/access.schema.json)
- Access evidence stream contributor home: [`content/evidence/access/`](../../../content/evidence/access/)
- Regulatory anchor (NIS2 Article 21(2)(i)): [`content/mappings/nis2/article-21-2-i.yaml`](../../../content/mappings/nis2/article-21-2-i.yaml)
- Sibling n8n worked example: [`../../n8n/onboarding_offboarding_tracker/`](../../n8n/onboarding_offboarding_tracker/)

## Cross-target shape parity

The committed access-evidence record is shape-identical to the n8n
sibling on every field except the three the schema's `artifact_id`
derivation joins on (`workflow_id, execution_id, compile_target`).
That cross-target shape parity is pinned by
`tests/examples/onboarding_offboarding_tracker/test_temporal_access_evidence.py::test_temporal_and_n8n_fixtures_agree_on_target_agnostic_fields`.
Both adapters drive the same shared helper
(`compilers._shared.evidence.emit_access_artifact`) from the same
primitive chain
(`content.playbooks.onboarding_offboarding_tracker.primitives`); a
drift on the cross-target parity test means one adapter started
rewriting payload fields the shared helper does not.

## Sovereign-stack default

The identity source the workflow reads and writes, and the
access-evidence store the emitted artifact targets, are
operator-configured. No default hosted IdP, no HR-SaaS dependency, no
default non-EU endpoint, no vendor SDK bundled. Pending serial
siblings: CORE-FANOUT-LG, EXTEND-schema, EXTEND-metrics,
EXTEND-docs-closeout.
