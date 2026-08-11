# content/evidence/sovereignty/SCHEMA.md

Sovereignty evidence stream — record-schema narrative.

This document is the **contributor-facing description** of the artifact
shape the sovereignty evidence stream emits. The authoritative
machine-readable schema is
[`schemas/evidence/sovereignty.schema.json`](../../../schemas/evidence/sovereignty.schema.json)
(F-SV-04 SKELETON card); the reference emitters (n8n / Temporal /
LangGraph) land in the sibling CORE card against that stable target.

## Envelope

Standard evidence-stream envelope, byte-compatible in spirit with the
F-CP streams:

| Field | Contract |
|---|---|
| `schema_version` | `const "1.0.0"` — consumers may reject artifacts from older schema versions once breaking changes ship. |
| `artifact_id` | SHA-256 hex of `<workflow_id>\|<execution_id>\|<compile_target>` — deterministic, so a replay re-derives the same id. |
| `stream` | `const "sovereignty"`. |
| `workflow_id` / `execution_id` | Which compiled workflow, which run. |
| `compile_target` | `n8n` \| `temporal` \| `langgraph`. |
| `regulation_refs` | ≥ 1 mapping-entry pins (typically GDPR Chapter V transfer atoms and NIS2 Art. 21(2)(d)); the indicators' own `external_refs` are the authority on which apply. |
| `control_refs` | ≥ 1 control stable-ids, standard shape. |
| `captured_at` | When the artifact was composed. Not part of `artifact_id`. |
| `provenance` | `source_url` + `captured_at` (+ optional `commit_sha`), mirroring `content/controls/*.yaml`. |

## Payload

| Field | Contract |
|---|---|
| `assessment_window` | `{from, to}` ISO-8601 UTC. Observations sampled at different instants inside the window are legitimate; the window bounds are the honesty contract about how stale the oldest observation may be. |
| `observations` | Object keyed by indicator `stable_id`. **Every** sovereignty-cluster indicator (`foundation_property: sovereignty` under `content/metrics/`) is required; no other key validates. Each observation carries `observed_value` (number — the indicator's catalogue entry declares the unit), `threshold_band` (`on_target` \| `warn` \| `high` \| `breach`, against the indicator's own catalogue thresholds), and `observed_at` (inside the window). |
| `attestation_state` | `$ref` to [`schemas/attestation_state.json`](../../../schemas/attestation_state.json) — the shared four-state vocabulary, reused, never redeclared. Describes the attestation exercise (fresh/complete vs. gapped vs. overdue), not a sovereignty verdict. |

## What the schema refuses, and why

- **A record missing any indicator** — completeness is the point; a
  partial attestation reads as a full one unless the schema forbids it.
- **Any unknown key anywhere** (`additionalProperties: false`
  throughout) — including any attempt to add a `sovereignty_score` or
  similar aggregate. Per-indicator observations, never a score.
- **A parallel state vocabulary** — the attestation state is imported
  by `$ref`; `tests/content_model/test_sovereignty_evidence_schema.py`
  fails if this schema ever declares an enum overlapping the four
  canonical states.

## Drift guards

`test_sovereignty_evidence_schema.py` derives the sovereignty-tagged
indicator set from `content/metrics/*.yaml` on every run and asserts it
equals the schema's required observation keys — in both directions. A
new sovereignty-tagged metric therefore surfaces as a named test
failure pointing at the schema file, not as a silently unattested
indicator.
