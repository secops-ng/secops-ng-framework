# SecOps-NG — Roadmap

This is the **source-of-truth roadmap** for the SecOps-NG framework. It is
hand-curated and reviewed by the community. It is **not** a status board —
the live, per-task status of public work is rendered separately to
[`docs/kanban-status.md`](docs/kanban-status.md) from the project kanban.

## How this document is used

Each entry below is a **feature definition**. Features are derived from:

- [`docs/FOUNDATION.md`](docs/FOUNDATION.md) — the four non-negotiable
  properties (auditability, determinism, sovereignty, operability).
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — the four-layer runtime.
- [`compliance/nis2/`](compliance/nis2/) — NIS2 Articles 20–23 mappings.
- [`compliance/gdpr/`](compliance/gdpr/) — GDPR data-flow templates.
- Community input (issues, PRs, contributor field notes).

A feature graduates from this document into shipped code via the public
kanban. The convention:

1. A feature here gets one or more kanban cards. Cards reference the
   feature id (e.g. `F-CR-03`) in their body so the link is explicit.
2. Card status is rendered to `docs/kanban-status.md` daily.
3. When every card for a feature reaches `done`, the **Status** line on
   the feature flips to `Shipped` in the next ROADMAP revision.

This document is revised:

- **After every market or regulatory brief** lands at
  `docs/research/*-market-brief.md`. The Coder lane re-reads the brief
  and updates affected features (priorities, acceptance criteria,
  sovereign-stack constraints).
- **On contributor request** via a PR that amends the feature table.

## Schema

Each feature has the following fields:

| Field | Meaning |
|-------|---------|
| **Id** | Stable identifier `F-<epic>-<NN>`. Never reused. |
| **Title** | One-line human-readable name. |
| **Status** | `Proposed`, `In Design`, `In Progress`, `Shipped`, or `Deferred`. |
| **Priority** | `P0` (next), `P1` (queued), `P2` (later), `P3` (someday). |
| **Acceptance criteria** | Bullet list. Each bullet is independently testable. |
| **Sovereign-stack constraints** | Hard constraints from FOUNDATION property #3 (sovereignty) and stack choices (LangGraph, Pydantic v2, DSPy, OpenTelemetry). |
| **Depends on** | Other feature ids that must be `Shipped` first. |
| **Source** | The originating document (FOUNDATION, ARCHITECTURE, NIS2 Art. N, GDPR Art. N, or a brief filename). |

Forward-public hygiene applies to every entry: community language,
no internal infrastructure detail, no contact names, no credentials.

---

## Epic CR — Core Runtime

The minimum viable LangGraph + Pydantic v2 + DSPy + OpenTelemetry surface
that every SecOps-NG workflow runs on.

### F-CR-01 — Frozen Pydantic v2 `ToolIO` contract

- **Status:** Shipped
- **Priority:** P0
- **Acceptance criteria:**
  - `secops_ng.tool_io.ToolIO` is a `pydantic.BaseModel` with
    `model_config = ConfigDict(extra="forbid", frozen=True)`.
  - Every workflow / activity / agent input and output subclasses
    `ToolIO`.
  - A test fails loudly if any boundary type drops `extra="forbid"`
    or `frozen=True`.
- **Sovereign-stack constraints:** Pydantic v2 only; no v1 compatibility
  shim that would silently downgrade strictness.
- **Depends on:** —
- **Source:** FOUNDATION (auditability), ARCHITECTURE (Contracts layer).

### F-CR-02 — LangGraph `StateGraph` baseline

- **Status:** Shipped
- **Priority:** P0
- **Acceptance criteria:**
  - Workflows are expressed as `langgraph.graph.StateGraph` instances.
  - State is a single frozen `ToolIO` subclass; transitions are
    `model_copy(update=...)` returns.
  - The framework runs without an external orchestrator cluster.
- **Sovereign-stack constraints:** No Temporal cluster required at the
  default operating point; durability is delegated to LangGraph's
  pluggable checkpointer when an operator opts in.
- **Depends on:** F-CR-01
- **Source:** ARCHITECTURE (Orchestration layer).

### F-CR-03 — DSPy-mediated LLM reasoning

- **Status:** Shipped
- **Priority:** P0
- **Acceptance criteria:**
  - All LLM-facing reasoning is expressed as a DSPy signature + module.
  - A `DummyLM` test double exists and is used by the test suite so
    LLM-using nodes are testable without a network call.
  - The LM backend is configured via `secops_ng.config.configure_default_lm`
    and is pluggable.
- **Sovereign-stack constraints:** Default configuration assumes the
  operator pins the LM to an EU-resident endpoint. The framework
  **must not** ship a default that calls a non-EU service.
- **Depends on:** F-CR-01
- **Source:** FOUNDATION (sovereignty), ARCHITECTURE (LLM reasoning layer),
  NIS2 Art. 21(2)(f).

### F-CR-04 — OpenTelemetry spans on every node and tool call

- **Status:** In Progress
- **Priority:** P0
- **Acceptance criteria:**
  - Every graph node emits an OTel span with structured attributes
    (workflow id, node name, input/output schema names, duration).
  - Every tool call emits a child span with finding id, severity, and
    recommended action where applicable.
  - Spans are exported via the operator's OTLP collector; no vendor
    SDK is bundled.
  - An in-band audit trail (e.g. `TriageState.audit_trail`) mirrors the
    OTel events so the trail survives an OTLP outage.
- **Sovereign-stack constraints:** OTLP endpoint is operator-configured;
  default points to localhost.
- **Depends on:** F-CR-02
- **Source:** ARCHITECTURE (Observability layer), NIS2 Art. 23.

### F-CR-05 — Deterministic replay test for every workflow

- **Status:** Shipped
- **Priority:** P0
- **Acceptance criteria:**
  - Each cookbook workflow ships a replay test that invokes the
    LangGraph replayer (or equivalent) and asserts identical state
    transitions on a fixed transcript.
  - A non-determinism negative case (mutating a node) is asserted to
    fail.
- **Sovereign-stack constraints:** —
- **Depends on:** F-CR-02
- **Source:** FOUNDATION (determinism).

---

## Epic WF — Workflow Cookbook

Reference workflows that exercise the Core Runtime and demonstrate a
named operator use-case. Each cookbook workflow lives under
`workflows/<name>/` with `README.md`, `PROMPT.md`, `config.yaml`,
`example.py`, and primitives directory.

### F-WF-01 — Vulnerability triage

- **Status:** In Progress
- **Priority:** P0
- **Acceptance criteria:**
  - `workflows/vulnerability_triage/` exists with library code,
    cookbook entry, primitives, example, and config.
  - DSPy signature for severity rating; deterministic dedup; OTel spans
    on every node.
  - Tests cover happy-path, dedup-collision, replay.
- **Sovereign-stack constraints:** Threat-intel feeds declared as
  Pydantic-typed supplier dependencies (F-CP-04).
- **Depends on:** F-CR-01, F-CR-02, F-CR-03, F-CR-04
- **Source:** NIS2 Art. 21(2)(e), Art. 21(2)(b).

### F-WF-02 — Posture audit

- **Status:** Shipped
- **Priority:** P0
- **Acceptance criteria:**
  - `workflows/posture_audit/` runnable end-to-end against a manifest
    fixture.
  - `submit_audit.py` CLI entrypoint.
  - Sample report fixture committed; walkthrough docs present.
- **Sovereign-stack constraints:** —
- **Depends on:** F-CR-01, F-CR-02, F-CR-05
- **Source:** NIS2 Art. 21(2)(a).

### F-WF-03 — Alert triage

- **Status:** Proposed
- **Priority:** P1
- **Acceptance criteria:**
  - Ingestion of typed alert payloads from at least two source shapes.
  - Deterministic prioritisation policy expressed as code; DSPy module
    only used for free-text fields.
  - Cookbook entry + replay test + walkthrough docs.
- **Sovereign-stack constraints:** Payload shapes must validate as
  GDPR data-flow `data-flow-alert-triage.md` (see `compliance/gdpr/`).
- **Depends on:** F-WF-01
- **Source:** NIS2 Art. 21(2)(b).

### F-WF-04 — Detection engineering

- **Status:** Proposed
- **Priority:** P1
- **Acceptance criteria:**
  - Rule lifecycle workflow: propose → review → ship → measure.
  - Effectiveness metric snapshot emitted per rule version.
- **Sovereign-stack constraints:** Metric storage operator-configured;
  no hosted SaaS default.
- **Depends on:** F-CR-03, F-CP-06
- **Source:** NIS2 Art. 21(2)(f).

### F-WF-05 — Incident management

- **Status:** Proposed
- **Priority:** P1
- **Acceptance criteria:**
  - Workflow scaffolds the NIS2 Art. 23 three-stage timeline (24 h
    early warning → 72 h notification → 1 month final report).
  - State transitions are deterministic and replay-tested.
  - Outputs include a machine-readable timeline JSON consumable by
    F-CP-02.
- **Sovereign-stack constraints:** Notification destinations are
  operator-configured; the framework ships no default endpoint.
- **Depends on:** F-CR-04, F-PT-02 (incident_timeline pattern)
- **Source:** NIS2 Art. 23.

### F-WF-06 — Infrastructure posture management

- **Status:** Proposed
- **Priority:** P2
- **Acceptance criteria:**
  - Continuous variant of F-WF-02 driven by scheduled re-execution.
- **Sovereign-stack constraints:** —
- **Depends on:** F-WF-02
- **Source:** NIS2 Art. 21(2)(a).

### F-WF-07 — Codebase vulnerability management

- **Status:** Proposed
- **Priority:** P2
- **Acceptance criteria:**
  - SBOM-driven dependency review workflow with disclosure timeline
    capture.
- **Sovereign-stack constraints:** Default scanner is a CLI installable
  from EU-hosted package index; no hosted scanner SaaS dependency.
- **Depends on:** F-WF-01
- **Source:** NIS2 Art. 21(2)(e).

### F-WF-08 — IAM auditor

- **Status:** Proposed
- **Priority:** P2
- **Acceptance criteria:**
  - Capability inventory workflow that produces a per-execution caller
    identity + capability list (the F-CP-07 evidence stream).
- **Sovereign-stack constraints:** —
- **Depends on:** F-CP-07
- **Source:** NIS2 Art. 21(2)(i).

### F-WF-09 — Compliance evidence collection

- **Status:** Proposed
- **Priority:** P1
- **Acceptance criteria:**
  - Workflow consumes the seven evidence streams (F-CP-01..F-CP-07)
    and emits a single bundle suitable for an auditor handover.
- **Sovereign-stack constraints:** Bundle format is a directory of
  plain files, not a proprietary archive.
- **Depends on:** all F-CP-*
- **Source:** NIS2 Art. 20, Art. 21(2)(f).

### F-WF-10 — Contractual-obligations tracker

- **Status:** Proposed
- **Priority:** P3
- **Acceptance criteria:**
  - Supplier-contract obligation extraction and review-date workflow.
- **Sovereign-stack constraints:** Operator-supplied document store;
  no hosted DMS dependency.
- **Depends on:** F-CP-03 (supply-chain stream)
- **Source:** NIS2 Art. 21(2)(d).

### F-WF-11 — On-boarding / off-boarding

- **Status:** Proposed
- **Priority:** P3
- **Acceptance criteria:**
  - Identity lifecycle workflow with capability grant/revoke
    confirmation.
- **Sovereign-stack constraints:** —
- **Depends on:** F-WF-08
- **Source:** NIS2 Art. 21(2)(i).

### F-WF-12 — IT and security support agent

- **Status:** Proposed
- **Priority:** P3
- **Acceptance criteria:**
  - Ticket-shaped interaction workflow with explicit handoff to a
    human responder.
- **Sovereign-stack constraints:** —
- **Depends on:** F-WF-03
- **Source:** community input.

---

## Epic PT — Pattern Library

Reusable graph fragments and Pydantic types shared across cookbook
workflows. Each pattern lives under `patterns/<name>/`.

### F-PT-01 — Evidence collector

- **Status:** Shipped
- **Priority:** P0
- **Acceptance criteria:**
  - `patterns/evidence_collector/` exists with usage docs and a test.
  - Pattern emits to a configurable `compliance/evidence/<stream>/`
    location.
- **Sovereign-stack constraints:** —
- **Depends on:** F-CR-01
- **Source:** NIS2 Art. 21(2)(f).

### F-PT-02 — Incident timeline

- **Status:** Shipped
- **Priority:** P0
- **Acceptance criteria:**
  - `patterns/incident_timeline/` builds a NIS2-Art-23-shaped timeline
    artefact from workflow events.
- **Sovereign-stack constraints:** Timeline is plain JSON, not a
  proprietary export.
- **Depends on:** F-PT-01
- **Source:** NIS2 Art. 23.

### F-PT-03 — Provider attestation

- **Status:** Shipped
- **Priority:** P1
- **Acceptance criteria:**
  - `patterns/provider_attestation/` produces a verifiable claim
    record for an external provider invocation.
- **Sovereign-stack constraints:** Claim records reference EU
  certification schemes where available.
- **Depends on:** F-PT-01
- **Source:** NIS2 Art. 21(2)(d), Art. 22.

### F-PT-04 — Patterns index

- **Status:** Shipped
- **Priority:** P1
- **Acceptance criteria:**
  - `patterns/README.md` indexes every pattern with a one-line summary
    and contribution checklist.
- **Sovereign-stack constraints:** —
- **Depends on:** —
- **Source:** community input.

---

## Epic CP — Compliance Evidence Pipeline

Wire each `<!-- coder:wire -->` marker in `compliance/nis2/` to a real
evidence stream emitted by framework workflows. Each stream is a
directory under `compliance/evidence/<stream>/` whose schema is
documented in the corresponding NIS2 article file.

### F-CP-01 — Risk-analysis stream

- **Status:** Proposed
- **Priority:** P1
- **Acceptance criteria:**
  - `compliance/evidence/risk-analysis/` populated by at least one
    workflow with policy versions and risk-analysis outputs.
  - Schema documented in `compliance/nis2/article-21-risk-management.md`
    §21(2)(a).
- **Sovereign-stack constraints:** —
- **Depends on:** F-PT-01
- **Source:** NIS2 Art. 21(2)(a).

### F-CP-02 — Incidents stream

- **Status:** Proposed
- **Priority:** P1
- **Acceptance criteria:**
  - `compliance/evidence/incidents/<workflow-id>/` populated by the
    incident-management workflow.
- **Sovereign-stack constraints:** —
- **Depends on:** F-PT-02, F-WF-05
- **Source:** NIS2 Art. 21(2)(b), Art. 23.

### F-CP-03 — Supply-chain stream

- **Status:** Proposed
- **Priority:** P1
- **Acceptance criteria:**
  - `compliance/evidence/supply-chain/dependencies-snapshot.json`
    emitted per workflow execution that calls an external provider.
- **Sovereign-stack constraints:** Snapshot includes provider
  sovereignty classification.
- **Depends on:** F-PT-03
- **Source:** NIS2 Art. 21(2)(d), Art. 22.

### F-CP-04 — Vulnerabilities stream

- **Status:** Proposed
- **Priority:** P1
- **Acceptance criteria:**
  - `compliance/evidence/vulns/` populated by `vulnerability_triage`
    with triage decisions and disclosure timelines.
- **Sovereign-stack constraints:** —
- **Depends on:** F-WF-01, F-PT-01
- **Source:** NIS2 Art. 21(2)(e).

### F-CP-05 — Crypto attestation stream

- **Status:** Proposed
- **Priority:** P2
- **Acceptance criteria:**
  - `compliance/evidence/crypto/secret-handling-attestation.json`
    emitted per workflow execution, asserting no secret was baked into
    workflow code (env-only injection).
- **Sovereign-stack constraints:** Hard rule: any workflow that fails
  the env-only check is refused at boot.
- **Depends on:** F-PT-01
- **Source:** NIS2 Art. 21(2)(h), Core Directive #6.

### F-CP-06 — Effectiveness stream

- **Status:** Proposed
- **Priority:** P2
- **Acceptance criteria:**
  - `compliance/evidence/effectiveness/` populated with metric
    snapshots per policy / prompt version.
- **Sovereign-stack constraints:** Metrics are DSPy-evaluatable.
- **Depends on:** F-CR-03, F-PT-01
- **Source:** NIS2 Art. 21(2)(f).

### F-CP-07 — Access stream

- **Status:** Proposed
- **Priority:** P2
- **Acceptance criteria:**
  - `compliance/evidence/access/` populated with per-execution caller
    identity and capability list.
- **Sovereign-stack constraints:** —
- **Depends on:** F-PT-01
- **Source:** NIS2 Art. 21(2)(i).

---

## Epic GD — GDPR Data-Flow Adoption

Make GDPR data-flow templates a first-class citizen of every workflow,
not a separate documentation chore.

### F-GD-01 — Data-flow template adoption per cookbook workflow

- **Status:** In Progress
- **Priority:** P1
- **Acceptance criteria:**
  - Every cookbook workflow under `workflows/` ships a populated
    `compliance/gdpr/data-flow-<workflow>.md` derived from the
    canonical template.
  - The seven required sections (purpose, lawful basis, categories,
    recipients, retention, cross-border, rights) are non-empty.
- **Sovereign-stack constraints:** Cross-border section explicitly
  evaluates non-EU recipient endpoints; default workflows must score
  "no transfer".
- **Depends on:** —
- **Source:** GDPR Art. 5(1)(b), Art. 6(1), Art. 30.

### F-GD-02 — Lawful-basis check in CI

- **Status:** Proposed
- **Priority:** P2
- **Acceptance criteria:**
  - CI fails if a workflow ships without a corresponding data-flow
    document, or if the lawful-basis section is empty.
- **Sovereign-stack constraints:** —
- **Depends on:** F-GD-01
- **Source:** GDPR Art. 6(1), `compliance/gdpr/lawful-basis-notes.md`.

---

## Epic SV — Sovereign Defaults

Operator-facing defaults that enforce FOUNDATION property #3 without
manual configuration.

### F-SV-01 — EU-resident LM default refusal

- **Status:** Proposed
- **Priority:** P1
- **Acceptance criteria:**
  - `configure_default_lm` refuses an unconfigured (no endpoint pinned)
    boot with an explicit error pointing to the sovereignty docs.
  - A documented opt-out exists for community contributors testing
    against non-EU endpoints in development only.
- **Sovereign-stack constraints:** Hard refusal in production mode.
- **Depends on:** F-CR-03
- **Source:** FOUNDATION (sovereignty), Core Directive #1.

### F-SV-02 — eIDAS 2.0 wallet integration pattern

- **Status:** Proposed
- **Priority:** P2
- **Acceptance criteria:**
  - Pattern (under `patterns/eidas2_wallet/`) shows how to consume an
    EU Digital Identity Wallet attestation as a Pydantic-typed
    workflow input.
- **Sovereign-stack constraints:** Uses Regulation (EU) 2024/1183
  reference schemas only.
- **Depends on:** F-PT-03
- **Source:** Research `2026-05-16-eidas2-wallet-patterns.md` (private;
  surface to public when scoped).

### F-SV-03 — DORA technical-incident reporting alignment

- **Status:** Proposed
- **Priority:** P2
- **Acceptance criteria:**
  - Incident-management workflow (F-WF-05) emits a variant timeline
    consumable as a DORA Art. 19 technical incident report for
    in-scope operators.
- **Sovereign-stack constraints:** —
- **Depends on:** F-WF-05
- **Source:** Research `2026-05-15-dora-incident-reporting.md`
  (private; surface to public when scoped).

---

## Revision history

- **v0 (2026-05-21).** Initial seed from FOUNDATION.md, ARCHITECTURE.md,
  and the NIS2 / GDPR compliance scaffolds. No market brief yet
  consumed; subsequent revisions will follow the standing cadence
  ("after each new market brief").
