# SecOps-NG — Foundation

SecOps-NG is an opinionated, EU-sovereignty-aware Python framework for building
agentic Security Operations workflows. The framework is designed around four
non-negotiable properties:

- **Auditability.** Every step in every workflow is reviewable as plain code,
  and every value crossing a boundary is a typed, validated artefact. This is
  the foundation of our alignment with NIS2 Article 21 (risk management) and
  Article 23 (incident reporting), and with the GDPR Article 30 record of
  processing activities.
- **Determinism where it matters.** Routing, policy, and state transitions are
  deterministic Python. Only the explicitly LLM-facing reasoning steps are
  non-deterministic, and those are isolated behind DSPy signatures so their
  inputs, outputs, and prompts are themselves versioned code.
- **Sovereignty.** No hidden calls to non-EU services. Inference endpoints are
  pluggable; the default configuration assumes an operator will pin the
  framework to an EU-resident LM.
- **Operability.** The runtime cost of a SecOps-NG workflow is a Python
  process. No external orchestrator cluster is required.

## The stack at a glance

| Layer | Technology | Why |
|-------|------------|-----|
| Orchestration | LangGraph `StateGraph` | Python-native, low operational cost, good ergonomics for branching reasoning. |
| Contracts | Pydantic v2 `BaseModel` (`extra="forbid"`, `frozen=True`) | Strict, immutable I/O contracts at every boundary. |
| LLM reasoning | DSPy signatures + modules | Prompts as versioned code; auditable under NIS2. |
| Observability | OpenTelemetry | Spans on every node and every tool call, exported to the operator's collector. |

## Architecture pivot (2026-05)

The pre-0.1 prototype used Temporal + dataclasses. That stack was correct in
spirit (durability, typed boundaries) but wrong in cost-to-value: running a
Temporal cluster is a non-trivial operational ask for a security team that
just wants reviewable agents. We pivoted to LangGraph for orchestration,
Pydantic v2 for contracts, and DSPy for LLM-facing reasoning. See
[`ARCHITECTURE.md`](./ARCHITECTURE.md) for the per-layer detail.

## Where to read next

- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — the per-layer breakdown.
- [`../compliance/nis2/`](../compliance/nis2/) — how each NIS2 article maps
  to framework features.
- [`../compliance/gdpr/`](../compliance/gdpr/) — data-flow templates and
  lawful-basis notes.
- [`../workflows/`](../workflows/) — runnable cookbook examples.
