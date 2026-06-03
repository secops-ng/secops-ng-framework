# Audit-trail mirror: co-location decision

Status: accepted
Scope: `compilers/_shared/observability.py`, `compilers/{langgraph,temporal}/*`,
`examples/{langgraph,temporal}/*`.

## Context

The four non-negotiable properties (`docs/FOUNDATION.md`) require that an
emitted workflow remain **auditable** even when the operator has not
configured an OpenTelemetry exporter — typical for disconnected,
sovereign, or air-gapped deployments where OTLP egress to an external
collector is unavailable.

Both reference compilers (LangGraph and Temporal) wrap their generated
units of work in an OpenTelemetry span and, in parallel, append an
`AuditRecord` to a context-local `AuditTrail`. The span carries
attributes for a live OTel consumer; the audit trail carries the same
information for the case where no consumer is wired up. The mirror is
therefore the **source of truth for audit**, and the span layer is a
transport on top of it — spans add propagation and aggregation, not
semantics.

This document covers three questions:

1. Where the mirror physically lives at rest in the repository and in
   any operator's checkout (the co-location decision).
2. Where the mirror logically hangs in each emitted graph (which
   node / activity owns each `AuditRecord`; how the mirror's lifecycle
   relates to the span's lifecycle).
3. How the mirror is consumed offline, without an OTLP collector
   (the replay shape and envelope reference).

## File-location alternatives considered

1. **Single source-of-truth module imported from a shared package.**
   Emitted code would `from compilers._shared._audit_mirror import ...`.
   Rejected: the compiler output is intended to be a self-contained
   integrator drop-in. Pinning a `compilers.*` import in the emitted
   artifact would couple every deployed copy back to this repository's
   package layout.

2. **Inline the mirror module at the top of every emitted artifact.**
   Rejected: doubles the line count of generated stubs, makes byte-level
   goldens fragile under churn of the mirror module itself, and breaks
   the rule that emitted code stays minimal and easy to review.

3. **Co-locate `_audit_mirror.py` as a sibling of each emitted
   artifact.** Accepted (see below).

## Decision

`_audit_mirror.py` is written **as a sibling of each emitted artifact**.
Emitted modules reach it via a package-relative import
(`from ._audit_mirror import AuditRecord, AuditTrail`) — the same import
shape regardless of compile target.

Concretely:

- The canonical source is `render_audit_mirror_module()` in
  `compilers/_shared/observability.py`. Its output is deterministic and
  has no external dependencies (stdlib only).
- A thin module CLI — `python -m compilers._shared.audit_mirror_cli` —
  prints that source. `regenerate.sh` in each worked example runs the
  CLI to materialise the file next to the artifacts it emits.
- The materialised `_audit_mirror.py` is **committed** alongside its
  sibling artifact so the example directory is runnable on a fresh
  clone without invoking the compiler.
- A test under `tests/examples/` asserts every committed
  `_audit_mirror.py` is byte-identical to `render_audit_mirror_module()`
  — drift fails CI the same way a stale golden does.

## Where the mirror hangs in each emitted graph

The mirror's life is **per-invocation, not per-span**. One `AuditTrail`
is created when an emitted workflow starts and is finalised when that
workflow ends; individual nodes / activities only `append()` to it.

### LangGraph emitter

Each emitted node body is wrapped in one tool span. Inside the wrapped
body, before the user-supplied work runs, an `AuditRecord` is
constructed from the span attributes and appended to
`AuditTrail.current()`. The trail itself is created at graph entry
(the compiler emits the initialiser in the graph header) and snapshot
at graph exit. Lifecycle ordering, per node:

1. Span starts (`tool` kind, with deterministic attribute set).
2. `AuditRecord` constructed from those attributes; appended to the
   active `AuditTrail`.
3. Node body executes.
4. Span closes (success or error status set by the wrapper).

The audit append happens **inside** the span, before the body, so a
mid-body exception still leaves a record of the node having been
entered. The record carries the same identifying keys the span carries
(workflow id, node name, run id) so cross-referencing a snapshot
against a span log is mechanical.

### Temporal emitter

Each emitted activity is wrapped in one activity span via the emitter
activity introduced in F-CR-04 CORE-B1. The wrapping is symmetric to
the LangGraph case: the activity span starts, an `AuditRecord` is
appended to the `AuditTrail` that the workflow established at start,
the activity body runs, the span closes.

The workflow itself wraps the orchestration in a workflow-level span;
that span's start is also the moment the `AuditTrail` is established
on the workflow execution context. Activity-level appends accumulate
into that same trail. On workflow completion (success, failure, or
cancellation), `AuditTrail.current().snapshot()` is the durable record
of the run.

### Lifecycle vs span lifecycle (summary)

| Layer | Lifecycle owner | Scope |
|------|----------------|-------|
| `AuditTrail` | Workflow / graph invocation | One per run, lives for the whole run, finalised at run end. |
| Workflow / graph span | OTel TracerProvider | Same scope as the trail; carries the run's top-level attributes. |
| Node / activity span | OTel TracerProvider | Per unit of work; nested under the workflow span. |
| `AuditRecord` | Mirror, appended in node/activity wrapper | One per node / activity entry; appended inside the unit-of-work span, before the user body runs. |

The mirror outlives any single span: even if a span is dropped by an
exporter on the wire, the corresponding `AuditRecord` remains in the
in-process trail and is available to the snapshot consumer.

## Relationship to OTel spans

OpenTelemetry is used at the **API** layer only — the emitted artifacts
never bind a vendor SDK or a hard-coded collector endpoint. The
operator configures a TracerProvider out-of-band; the artifact obtains
its tracer from the global provider and writes spans to whichever
exporter (if any) the provider is wired to. EU-hostable collectors are
the assumed target when one is wired at all.

The mirror is what makes the artifact useful **without** that wiring:

- **No exporter configured.** A no-op TracerProvider (or a provider
  with no exporter) drops the spans on the floor. The `AuditTrail`
  still accumulates one `AuditRecord` per node / activity entry, and
  `snapshot()` returns the full run. This is the disconnected /
  air-gapped baseline.
- **Local console / file exporter.** Spans hit a local sink. The
  mirror is redundant for the purpose of debugging but is still the
  durable audit record — span exporters are best-effort transport, not
  storage.
- **Remote OTLP exporter to an EU-hostable collector.** Spans
  propagate; the mirror still keeps the local snapshot so an audit
  remains valid even if a downstream collector loses data, restarts,
  or is unreachable at the moment of inspection.

In every case, attribute semantics are owned by
`compilers/_shared/observability.py` — the constants used to populate
the span and the constants used to populate the `AuditRecord` are the
same constants. Spans and records do not drift.

## Offline / air-gapped replay shape

A `snapshot()` of an `AuditTrail` is a list of `AuditRecord` instances
in append order. The intended persistence form for offline replay is a
**JSONL envelope** — one record per line, ordered as appended. The
envelope carries:

- A header line with the workflow / graph identifier, the run id, the
  compile target (`langgraph` or `temporal`), and the schema version of
  the record shape.
- One body line per `AuditRecord`, with the deterministic attribute
  set the mirror emits (workflow id, node / activity name, run id,
  attempt, timestamp, status, plus any compile-target-specific keys
  documented in `compilers/_shared/observability.py`).

A replayer reconstructing the run does not need an OTLP collector. It
reads the JSONL file in order and rebuilds the `AuditTrail` by calling
`append()` for each line. Because the record shape is the
attribute-key contract owned by the shared helper layer, the same
replayer works against both emitted targets.

The envelope is **not a span format**. It does not carry timing /
parent / context fields; the audit channel is for *what happened*, not
*how long it took*. Operators who want both can run with an OTLP
exporter pointed at an EU-hostable collector and persist the JSONL
mirror in parallel — neither channel depends on the other.

## Consequences

**Property: audit holds without OTel.** Because the import resolves
locally and the mirror module has no extra dependencies, an operator
running the emitted artifact under a TracerProvider with no exporter
configured still collects the `AuditTrail` rows. The downstream
`AuditTrail.current().snapshot()` is the durable evidence channel for
sovereign deployments.

**Property: determinism.** A second invocation of `regenerate.sh`
produces no diff: the CLI emits the same bytes; the committed file is
overwritten with identical content. Span attribute sets and audit
record fields are sourced from the same constant table, so they do not
drift relative to each other across regenerations.

**Property: vendor neutrality.** No vendor SDK is imported. The mirror
is stdlib-only; the emitted code imports the OpenTelemetry **API**
only and obtains its tracer through the global TracerProvider an
operator configures out-of-band. No collector endpoint is hard-coded.

**Property: operability.** Integrators copy the example directory into
their own runtime and the import surface keeps working without
rewriting imports. New compile targets follow the same pattern: emit
artifacts that import from a sibling `_audit_mirror`, and have
`regenerate.sh` materialise it.

## Cross-references

- `docs/FOUNDATION.md` — the four non-negotiable properties
  (auditability, determinism, sovereignty, operability).
- `compilers/_shared/observability.py` — the shared helpers,
  attribute-key constants, and `render_audit_mirror_module()`.
- `tests/compilers/_shared/test_observability.py` — assertions on the
  helper layer (parse, determinism, frozen records, snapshot copy).
- `tests/compilers/test_observability.py` — per-target assertions that
  every emitted action / activity wraps its body in one tool / activity
  span and records one `AuditRecord`.
