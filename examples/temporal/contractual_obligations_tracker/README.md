# examples/temporal/contractual_obligations_tracker

Temporal worked example for the
`playbook.contractual_obligations_tracker@v1` supplier-contract
obligations tracker workflow (F-WF-10; NIS2 Article 21(2)(d)).

## Maturity

`CORE-FANOUT-TEMPORAL` — the Temporal compile target binding for the
canonical CACAO playbook. The Temporal compiler emits the workflow
stub deterministically from the canonical playbook; the Temporal
activity adapter at
`compilers.temporal.evidence.emit_contractual_obligations_artifact_activity`
delegates to the framework-agnostic emitter under
`compilers._shared.evidence.contractual_obligations` so the
per-execution obligation-evidence artifact is byte-stable.
Cross-target byte parity against the n8n sibling is pinned at the
artifact-bytes level by
`tests/examples/contractual_obligations_tracker/test_temporal_obligation_evidence.py`.
The LG sibling lands in a separate F-WF-10 CORE-FANOUT-LG card.

## Layout

| Path | Source | Contents |
|------|--------|----------|
| `playbook.cacao.json` | (input mirror) | Byte-identical mirror of the canonical playbook |
| `workflow.temporal.py` | `compilers.temporal` | Temporal workflow stub emitted from the canonical playbook |
| `evidence/obligation-evidence-record.json` | Temporal activity adapter | One representative obligation-evidence artifact (shape: `schemas/evidence/contractual-obligations.schema.json`) |
| `regenerate.sh` | (tooling) | Regenerates the workflow + evidence record from the canonical playbook |
| `regenerate.py` | (tooling) | Drives the Temporal contractual-obligations activity adapter against the pinned context |

## How to regenerate

From the repository root:

```sh
./examples/temporal/contractual_obligations_tracker/regenerate.sh
```

The script copies the canonical CACAO source over the local mirror,
re-emits `workflow.temporal.py` via the unified `python -m tools.compile`
CLI, and re-runs the per-execution adapter against the pinned context
in `regenerate.py`. Run after any change to the canonical playbook,
the Temporal compiler, or the Temporal contractual-obligations
activity adapter; commit the resulting bytes alongside the change.

The committed `obligation-evidence-record.json` is the adapter's
output renamed for human-friendly diffing; the deterministic
`<artifact_id>.json` written by the adapter is the SHA-256-named
sibling of the same bytes.

## Source

- Canonical playbook: [`content/playbooks/contractual_obligations_tracker/`](../../../content/playbooks/contractual_obligations_tracker/)
- Obligation-evidence schema: [`schemas/evidence/contractual-obligations.schema.json`](../../../schemas/evidence/contractual-obligations.schema.json)
- Regulatory anchor (NIS2 Article 21(2)(d)): [`content/mappings/nis2/article-21-2-d.yaml`](../../../content/mappings/nis2/article-21-2-d.yaml)
- Byte-parity fixture: [`tests/fixtures/contractual_obligations_tracker/temporal.obligation-evidence-record.json`](../../../tests/fixtures/contractual_obligations_tracker/temporal.obligation-evidence-record.json)
- n8n sibling: [`examples/n8n/contractual_obligations_tracker/`](../../n8n/contractual_obligations_tracker/)

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

## Pending siblings

- **F-WF-10 CORE-FANOUT-LG** — LangGraph adapter + cross-target
  byte-parity test against the n8n / Temporal fixtures.
- **F-WF-10 EXTEND-metrics** — pin the supplier-attestation-staleness
  KRI and supplier-obligation-coverage KPI; bind via `metric_refs` on
  the canonical playbook.
- **F-WF-10 EXTEND-schema** — tighten the inner envelopes of
  `obligation_kind`, `clause_ref`, and the waiver / deferral surface;
  lift `schema_version` to 1.0.0.
