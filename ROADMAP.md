# SecOps-NG — Roadmap

This is the **source-of-truth roadmap** for the SecOps-NG framework. It is
hand-curated and reviewed by the community. Each entry is a feature
definition; live shipping work shows up in repository activity (merged
PRs, release notes) rather than a separate status mirror.

## How this document is used

Each entry below is a **feature definition**. Features are derived from:

- [`docs/FOUNDATION.md`](docs/FOUNDATION.md) — the four non-negotiable
  properties (auditability, determinism, sovereignty, operability).
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — the four-layer runtime.
- [`content/mappings/nis2/`](content/mappings/nis2/) — NIS2 Articles
  20–23 mappings.
- [`content/mappings/gdpr/`](content/mappings/gdpr/) — GDPR data-flow
  templates.
- Community input (issues, PRs, contributor field notes).

A feature graduates from this document into shipped code via contributor
PRs. The convention:

1. A feature here gets one or more PRs against the affected surface.
   PRs reference the feature id (e.g. `F-CR-03`) in their description
   so the link is explicit.
2. When every PR for a feature has merged, the **Status** line on the
   feature flips to `Shipped` in the next ROADMAP revision.

This document is revised on contributor request, via a PR that amends
the feature table.

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

> **Note (content-first refactor, PR #34, `a78ea7f`):** The original
> F-CR-* features described a single in-repo Python runtime
> (`src/secops_ng/{tool_io,config,workflows}/`) that bundled a
> Pydantic v2 contract layer, a LangGraph `StateGraph` baseline, a
> DSPy reasoning layer, and a deterministic replayer. That runtime
> tree was deliberately removed when the repository pivoted to a
> framework-agnostic, content-first layout: portable artifacts under
> `content/`, reference compilers under `compilers/{n8n,temporal,langgraph,community}/`,
> and per-target example projects under `examples/<target>/<workflow>/`.
> The contract, orchestration, reasoning, and replay concerns now
> belong to the compile target the operator already runs (n8n,
> Temporal, LangGraph), not to a runtime we ship. F-CR-01, F-CR-02,
> F-CR-03, and F-CR-05 are therefore marked **Removed (superseded
> by content-first refactor)** below; their acceptance criteria are
> preserved for historical reference but no longer track in-repo
> work. F-CR-04 (OpenTelemetry) is **Shipped** under a compiler-emitted
> scope: each reference compiler emits artifacts already wrapped in OTel
> instrumentation, governed by a shared attribute-schema helper — see
> the F-CR-04 entry below.

### F-CR-01 — Frozen Pydantic v2 `ToolIO` contract

- **Status:** Removed (superseded by content-first refactor)
- **Priority:** P0
- **Rationale:** PR #34 (`a78ea7f`) dropped the `src/secops_ng/`
  runtime tree, including `secops_ng.tool_io.ToolIO`. Boundary
  contracts are now expressed in portable artifacts under `content/`
  and `schemas/`, and each compile target enforces them in its own
  idiom (Pydantic models in the LangGraph reference compiler, JSON
  Schema for n8n, dataclasses for Temporal). A single in-repo
  `ToolIO` base class no longer fits the framework-agnostic posture.
- **Acceptance criteria (historical):**
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

- **Status:** Removed (superseded by content-first refactor)
- **Priority:** P0
- **Rationale:** PR #34 (`a78ea7f`) removed the in-repo LangGraph
  baseline (`src/secops_ng/workflows/`, `TriageState`, etc.). The
  LangGraph surface is now one of three reference compile targets
  under `compilers/langgraph/`, with per-workflow examples at
  `examples/langgraph/<workflow>/`. Operators who want a LangGraph
  baseline compile content into it; the framework no longer
  privileges LangGraph as *the* orchestrator.
- **Acceptance criteria (historical):**
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

- **Status:** Removed (superseded by content-first refactor)
- **Priority:** P0
- **Rationale:** PR #34 (`a78ea7f`) removed `src/secops_ng/config/`
  and the shared DSPy reasoning layer. Reasoning is now expressed in
  the portable PROMPT artifacts under `content/` and realised by each
  compile target (the LangGraph reference compiler can still use DSPy;
  n8n and Temporal targets do not). A single in-repo DSPy layer is
  not framework-agnostic and so cannot remain a Core Runtime feature.
- **Acceptance criteria (historical):**
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

### F-CR-04 — OpenTelemetry instrumentation emitted by every reference compiler

- **Status:** Shipped
- **Priority:** P0
- **Note (M0):** shipped in M0 as compiler-emitted OTel — each reference
  compiler (n8n, Temporal, LangGraph) wraps its emitted workflow steps
  in OpenTelemetry spans, with the audit-trail mirror co-located
  alongside the emitted artifact; the operator-config envelope is
  documented in each worked example's `Observability` section, and the
  shared attribute schema lives at `compilers/_shared/observability/`.
- **Rationale:** After the content-first refactor (PR #34), SecOps-NG
  ships portable content and reference compilers, not an in-repo
  runtime. Observability therefore lives in the compile targets: each
  reference compiler (`compilers/n8n/`, `compilers/temporal/`,
  `compilers/langgraph/`) emits artifacts that are already wrapped in
  OpenTelemetry instrumentation, and a shared helper module defines the
  common attribute schema so the three targets stay span-compatible.
  The previous acceptance criteria (which assumed a single in-repo
  `StateGraph` and a `TriageState.audit_trail` field) are obsolete and
  are replaced by the compiler-emitted criteria below.
- **Acceptance criteria:**
  - Each reference compiler under `compilers/{n8n,temporal,langgraph}/`
    emits artifacts whose every workflow step (n8n node, Temporal
    activity, LangGraph node) opens an OpenTelemetry span with
    structured attributes: workflow id, step name, input and output
    content-artifact ids, and step duration.
  - Each emitted tool or sub-workflow call opens a child span carrying
    finding id, severity, and recommended-action attributes when the
    underlying content artifact declares them.
  - A shared helper module (e.g. `compilers/_shared/observability/`)
    documents the span and attribute schema and is referenced — not
    duplicated — by each per-target emitter.
  - Emitted artifacts target the operator's OTLP collector via
    environment-variable configuration; no vendor SDK (Datadog,
    Honeycomb, New Relic, etc.) is bundled, and no default endpoint
    outside the operator's control is set.
  - Emitted artifacts also record an in-band audit-trail entry per
    step — mirroring the span's structured attributes — in a
    target-appropriate location (workflow state object on LangGraph,
    activity heartbeat / search attributes on Temporal, execution
    metadata on n8n) so the audit property holds when OTLP is offline.
  - Per-target byte-parity golden tests under `tests/examples/` cover
    the emitted instrumentation, so any regression in the OTel wrapping
    flips a test red.
- **Sovereign-stack constraints:** OTLP endpoint is operator-configured
  via environment variable; no default points outside the operator's
  collector. The shared helper imports only upstream OpenTelemetry SDK
  packages.
- **Depends on:** —
- **Source:** ARCHITECTURE (Observability layer), NIS2 Art. 23.

### F-CR-05 — Deterministic replay test for every workflow

- **Status:** Removed (superseded by content-first refactor)
- **Priority:** P0
- **Rationale:** PR #34 (`a78ea7f`) removed the in-repo workflow tree
  the LangGraph replayer was wired against. Determinism is now
  asserted per compile target: the per-example **byte-parity golden
  tests** under `tests/examples/` (see e.g. `executive-metrics`,
  `on-call-rotation`, `post-incident-review`) compile each portable
  artifact into n8n, Temporal, and LangGraph and assert the rendered
  output is byte-identical across runs. That assertion does the work
  the LangGraph replayer used to do, but at the content layer where
  it is framework-agnostic.
- **Acceptance criteria (historical):**
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

- **Status:** Shipped
- **Priority:** P0
- **Acceptance criteria:**
  - `content/playbooks/vuln-intake/` carries the CACAO playbook,
    primitives, and cookbook entry; compiled targets land under
    `examples/{n8n,temporal,langgraph}/vuln-intake/`.
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

- **Status:** In Progress
- **Status note:** SKELETON worked examples landed across all three
  reference targets (n8n / Temporal / LangGraph) with byte-parity
  golden drift guards in place; CORE action bodies, shared primitives
  (deterministic prioritisation policy, suppression-window helper,
  DSPy signature for free-text fields), the GDPR data-flow doc, and
  the replay / cookbook tests remain. Gap inventory:
  [`docs/internal/f-wf-03-gap-inventory.md`](docs/internal/f-wf-03-gap-inventory.md).
- **Priority:** P1
- **Acceptance criteria:**
  - Ingestion of typed alert payloads from at least two source shapes.
  - Deterministic prioritisation policy expressed as code; DSPy module
    only used for free-text fields.
  - Cookbook entry + replay test + walkthrough docs.
- **Sovereign-stack constraints:** Payload shapes must validate as
  GDPR data-flow `data-flow-alert-triage.md` (see `content/mappings/gdpr/`).
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

- **Status:** In Progress
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
  - Pattern emits to a configurable `content/evidence/<stream>/`
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

Wire each `<!-- coder:wire -->` marker in `content/mappings/nis2/` to a real
evidence stream emitted by framework workflows. Each stream is a
directory under `content/evidence/<stream>/` whose schema is
documented in the corresponding NIS2 article file.

### F-CP-01 — Risk-analysis stream

- **Status:** Proposed
- **Priority:** P1
- **Acceptance criteria:**
  - `content/evidence/risk-analysis/` populated by at least one
    workflow with policy versions and risk-analysis outputs.
  - Schema documented in `content/mappings/nis2/article-21-risk-management.md`
    §21(2)(a).
- **Sovereign-stack constraints:** —
- **Depends on:** F-PT-01
- **Source:** NIS2 Art. 21(2)(a).

### F-CP-02 — Incidents stream

- **Status:** Proposed
- **Priority:** P1
- **Acceptance criteria:**
  - `content/evidence/incidents/<workflow-id>/` populated by the
    incident-management workflow.
- **Sovereign-stack constraints:** —
- **Depends on:** F-PT-02, F-WF-05
- **Source:** NIS2 Art. 21(2)(b), Art. 23.

### F-CP-03 — Supply-chain stream

- **Status:** Proposed
- **Priority:** P1
- **Acceptance criteria:**
  - `content/evidence/supply-chain/dependencies-snapshot.json`
    emitted per workflow execution that calls an external provider.
- **Sovereign-stack constraints:** Snapshot includes provider
  sovereignty classification.
- **Depends on:** F-PT-03
- **Source:** NIS2 Art. 21(2)(d), Art. 22.

### F-CP-04 — Vulnerabilities stream

- **Status:** Proposed
- **Priority:** P1
- **Acceptance criteria:**
  - `content/evidence/vulns/` populated by `vulnerability_triage`
    with triage decisions and disclosure timelines.
- **Sovereign-stack constraints:** —
- **Depends on:** F-WF-01, F-PT-01
- **Source:** NIS2 Art. 21(2)(e).

### F-CP-05 — Crypto attestation stream

- **Status:** Proposed
- **Priority:** P2
- **Acceptance criteria:**
  - `content/evidence/crypto/secret-handling-attestation.json`
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
  - `content/evidence/effectiveness/` populated with metric
    snapshots per policy / prompt version.
- **Sovereign-stack constraints:** Metrics are DSPy-evaluatable.
- **Depends on:** F-CR-03, F-PT-01
- **Source:** NIS2 Art. 21(2)(f).

### F-CP-07 — Access stream

- **Status:** Proposed
- **Priority:** P2
- **Acceptance criteria:**
  - `content/evidence/access/` populated with per-execution caller
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
    `content/mappings/gdpr/data-flow-<workflow>.md` derived from the
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
- **Source:** GDPR Art. 6(1), `content/mappings/gdpr/lawful-basis-notes.md`.

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
- **Source:** Research `2026-05-16-eidas2-wallet-patterns.md` (private; available on request).

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
  (private; available on request).

---

## Revision history

- **v0 (2026-05-21).** Initial seed from FOUNDATION.md, ARCHITECTURE.md,
  and the NIS2 / GDPR mappings under `content/mappings/`. Subsequent
  revisions land via contributor PRs.
