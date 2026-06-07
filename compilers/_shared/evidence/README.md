# compilers/\_shared/evidence/

Framework-agnostic emitter helpers for the SecOps-NG **evidence** layer.
Each module in this package is the source of truth for one evidence
stream's artifact assembly and on-disk write. The three reference
compile targets (n8n, Temporal, LangGraph) wrap the same helper in a
thin adapter under `compilers/<target>/evidence/` — record shape and
deterministic `artifact_id` derivation never fork per target.

## Streams

| Stream | Module | Schema |
|--------|--------|--------|
| `risk-analysis` (F-CP-01) | [`risk_analysis.py`](risk_analysis.py) | [`schemas/evidence/risk-analysis.schema.json`](../../../schemas/evidence/risk-analysis.schema.json) |

Additional streams (F-CP-02..F-CP-07) land alongside as each stream's
EMITTER card ships.

## Contract

Each emitter exposes three callables:

- `<Stream>Context` — frozen dataclass; one cadence walk over one
  control. Validated before any JSON is written.
- `render_<stream>_artifact(ctx) -> dict` — pure context → record.
  Used by goldens, dry-runs, and compile targets that route the record
  through their own audit channel before persisting.
- `emit_<stream>_artifact(ctx, output_dir) -> Path` — render, then
  write `<artifact_id>.json` atomically under `output_dir`. The
  `artifact_id` is the SHA-256 of `<control_ref>|<captured_at>` (UTF-8)
  per the stream's schema.

Emitters do no network I/O and import nothing from a runtime SDK.
Compile-target adapters under `compilers/<target>/evidence/` are
responsible for the activity / node / workflow-step wiring.
