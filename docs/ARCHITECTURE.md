# SecOps-NG — Architecture

This document describes the four layers of the SecOps-NG runtime. Each layer
is independently swappable, but the combination below is the supported
default and the one used by the cookbook examples in `workflows/`.

## Orchestration — LangGraph

Workflows are LangGraph `StateGraph` instances. State is a single Pydantic
model (a `ToolIO` subclass); nodes are plain Python callables that take and
return the state. Because the state model is frozen, every node returns a
*new* state object via `model_copy(update=...)`, which keeps transitions
explicit and replay-friendly. We deliberately do **not** run an external
orchestrator (no Temporal cluster, no Airflow scheduler) — a SecOps-NG
workflow is a Python process. Durability, when required, is delegated to
LangGraph's pluggable checkpointer (e.g. SQLite or Postgres) rather than to a
separate orchestration stack.

## Contracts — Pydantic v2

Every value that crosses a node / tool / agent boundary is a subclass of
`secops_ng.tool_io.ToolIO`, a `pydantic.BaseModel` configured with
`extra="forbid"` and `frozen=True`. `extra="forbid"` means an unknown field
fails loudly at the boundary instead of silently corrupting downstream state —
this is the property that lets us claim NIS2-grade auditability for the data
plane. `frozen=True` makes models hashable and immutable, which removes a
whole class of aliasing bugs from graph state transitions. The contract
boundary is the same in tests, dev, and production; there is no "loose mode."

## LLM reasoning — DSPy

LLM-facing steps live inside graph nodes as DSPy modules. A DSPy signature
declares the input fields, output fields, and an instruction docstring; the
DSPy adapter constrains the LM response to that schema and emits structured
JSON which we map back onto Pydantic types. The point of going through DSPy
(rather than calling an LM client directly) is that the *prompt is code*:
versioned, diff-reviewable, and testable with a `DummyLM` stub. Under NIS2
Article 21, that is the artefact an auditor can read. The LM backend itself
is pluggable; the default configuration assumes the operator pins it to an
EU-resident endpoint via `configure_default_lm` and `secops_ng.config`.

## Observability — OpenTelemetry

Observability is unchanged from the pre-pivot design: every node and every
tool call emits an OpenTelemetry span with structured attributes (finding id,
severity, recommended action, etc.). Spans are exported via the operator's
OTLP collector — SecOps-NG does not bundle a vendor. The audit trail kept
inside `TriageState.audit_trail` is the *in-band* version of the same data,
captured in workflow state so it survives even if the OTLP exporter is
unavailable. The combination — out-of-band telemetry plus in-band audit
trail — is what supports the NIS2 Article 23 incident-reporting timeline.
