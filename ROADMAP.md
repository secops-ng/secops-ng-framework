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
  tests** under `tests/examples/` (see e.g. `executive_metrics`,
  `on_call_rotation`, `post_incident_review`) compile each portable
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
  - `content/playbooks/vuln_intake/` carries the CACAO playbook,
    primitives, and cookbook entry; compiled targets land under
    `examples/{n8n,temporal,langgraph}/vuln_intake/`.
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

- **Status:** Shipped
- **Priority:** P1
- **Acceptance criteria:**
  - Ingestion of typed alert payloads from at least two source shapes.
  - Deterministic prioritisation policy expressed as code; DSPy module
    only used for free-text fields.
  - Cookbook entry + replay test + walkthrough docs.
- **Sovereign-stack constraints:** Payload shapes must validate as
  GDPR data-flow `data-flow-alert_triage.md` (see `content/mappings/gdpr/`).
- **Depends on:** F-WF-01
- **Source:** NIS2 Art. 21(2)(b).

### F-WF-04 — Detection engineering

- **Status:** Shipped
- **Priority:** P1
- **Acceptance criteria:**
  - Rule lifecycle workflow: propose → review → ship → measure.
  - Effectiveness metric snapshot emitted per rule version.
- **Sovereign-stack constraints:** Metric storage operator-configured;
  no hosted SaaS default.
- **Depends on:** F-CR-03, F-CP-06
- **Source:** NIS2 Art. 21(2)(f).

### F-WF-05 — Incident management

- **Status:** Shipped
- **Priority:** P1
- **Acceptance criteria:**
  - `content/playbooks/incident_management/` carries the CACAO playbook
    and primitives; compiled targets land under
    `examples/{n8n,temporal,langgraph}/incident_management/`.
  - Workflow scaffolds the NIS2 Art. 23 three-stage timeline (24 h
    early warning → 72 h notification → 1 month final report); state
    transitions are deterministic and replay-tested across all three
    targets.
  - Outputs include a machine-readable timeline JSON consumable by
    F-CP-02.
  - Cookbook entry + cross-target happy-path and replay tests.
- **Sovereign-stack constraints:** Notification destinations are
  operator-configured; the framework ships no default endpoint.
- **Depends on:** F-CR-04, F-PT-02 (incident_timeline pattern)
- **Source:** NIS2 Art. 23.

### F-WF-06 — Infrastructure posture management

- **Status:** Shipped
- **Priority:** P2
- **Acceptance criteria:**
  - `content/playbooks/infra_posture_management/` carries the canonical
    CACAO playbook (`playbook.infra_posture_management@v1`) and
    deterministic primitives (`collect.collect_posture_state`,
    `controls.evaluate_controls`,
    `artifact.build_posture_artifact`) with zero placeholders across
    all three action bodies; compiled targets land under
    `examples/{n8n,temporal,langgraph}/infra_posture_management/`.
  - Continuous re-execution topology: `collect-posture` →
    `evaluate-controls` → `emit-posture-evidence`; transitions
    deterministic and replay-tested across all three targets. The
    continuous shape is the scheduled re-execution variant of the
    F-WF-02 per-request posture-audit lane — both share the
    posture-evidence schema, they differ in cadence (request-driven
    vs. scheduler-driven) and in the durability of the artifact
    series.
  - Per-execution posture-evidence-record emitted against
    `schemas/evidence/posture.schema.json` (stream: `posture`);
    `artifact_id` derives deterministically from
    `SHA-256(workflow_id|execution_id|compile_target|policy_version.value)`,
    so re-emissions inside the same execution under the same policy
    version are byte-identical at the path level. The record pins the
    posture-state snapshot hash, the per-control evaluation result
    set, the NIS2 Article 21(2)(a) `regulation_refs`, and the
    closed `control_refs` list. The `artifact_id` is **per-target**
    by construction — the same logical execution under each compile
    target re-derives a distinct id; byte-parity is asserted per
    target, not across targets.
  - Cookbook entry + per-target byte-parity goldens
    (`tests/examples/infra_posture_management/test_{n8n,temporal,langgraph}_workflow_golden.py`
    and `test_{n8n,temporal,langgraph}_posture_evidence.py`) pin both
    the per-target workflow artefact and the per-target
    posture-evidence record.
- **Sovereign-stack constraints:** Source endpoints for
  `collect-posture` (cloud-account read APIs, identity-provider read
  APIs, network-baseline read APIs) and the artifact destination for
  `emit-posture-evidence` are operator-configured; the framework
  ships no default endpoint and bundles no vendor SDK.
- **Depends on:** F-WF-02
- **Source:** NIS2 Art. 21(2)(a).

### F-WF-07 — Codebase vulnerability management

- **Status:** Shipped
- **Priority:** P2
- **Acceptance criteria:**
  - `content/playbooks/codebase_vuln_management/` carries the CACAO
    playbook and deterministic primitives (SBOM pin, finding
    normalisation, CVD disclosure-window resolution, timeline-record
    builder); compiled targets land under
    `examples/{n8n,temporal,langgraph}/codebase_vuln_management/`.
  - SBOM-driven dependency review workflow: `ingest-sbom` →
    `review-deps` → `assess-disclosure` → `track-timeline`; transitions
    deterministic and replay-tested across all three targets.
  - Per-finding disclosure-timeline-record emitted per workflow
    execution against
    `content/evidence/codebase_vuln_management/disclosure-timeline-record.schema.json`,
    deterministic on `(workflow_id, sbom_content_hash, component.purl,
    advisory_id)`.
  - Cookbook entry + cross-target byte-parity goldens
    (`tests/examples/codebase_vuln_management/`).
- **Sovereign-stack constraints:** Default scanner is a CLI installable
  from EU-hosted package index; no hosted scanner SaaS dependency.
- **Depends on:** F-WF-01
- **Source:** NIS2 Art. 21(2)(e).

### F-WF-08 — IAM auditor

- **Status:** Shipped
- **Priority:** P2
- **Acceptance criteria:**
  - `content/playbooks/iam_auditor/` carries the canonical CACAO
    playbook (`playbook.iam_auditor@v1`) and deterministic primitives
    (`identity.resolve_caller_identity`,
    `capabilities.build_capability_list`,
    `artifact.build_access_artifact`) with zero placeholders across
    all three action bodies; compiled targets land under
    `examples/{n8n,temporal,langgraph}/iam_auditor/`.
  - Capability-inventory workflow: `enumerate-identities` →
    `enumerate-capabilities` → `emit-access-evidence`; transitions
    deterministic and replay-tested across all three targets.
  - Per-execution caller-identity + closed capability-list bound onto
    the F-CP-07 access-evidence stream
    (`schemas/evidence/access.schema.json`); `artifact_id` derives
    deterministically from
    `SHA-256(workflow_id|execution_id|compile_target)`. Identity is
    role-shaped (service-account, workflow-runtime principal,
    automation role) — personal-user principals are rejected at the
    primitive boundary.
  - Cookbook entry + cross-target byte-parity goldens
    (`tests/examples/{n8n,temporal,langgraph}/iam_auditor/test_golden.py`)
    pin both the per-target workflow artefact and the per-target
    access-evidence record.
- **Sovereign-stack constraints:** —
- **Depends on:** F-CP-07
- **Source:** NIS2 Art. 21(2)(i).

### F-WF-09 — Compliance evidence collection

- **Status:** Shipped
- **Priority:** P1
- **Acceptance criteria:**
  - Workflow consumes the seven evidence streams (F-CP-01..F-CP-07)
    and emits a single bundle suitable for an auditor handover.
- **Sovereign-stack constraints:** Bundle format is a directory of
  plain files, not a proprietary archive.
- **Depends on:** all F-CP-*
- **Source:** NIS2 Art. 20, Art. 21(2)(f).

### F-WF-10 — Contractual-obligations tracker

- **Status:** Shipped
- **Priority:** P3
- **Acceptance criteria:**
  - `content/playbooks/contractual_obligations_tracker/` carries the
    canonical CACAO playbook
    (`playbook.contractual_obligations_tracker@v1`) and deterministic
    primitives (`ingest.ingest_contract`,
    `obligations.extract_obligations`,
    `schedule.schedule_reviews`,
    `artifact.build_obligation_artifact`) with zero placeholders
    across all four action bodies; compiled targets land under
    `examples/{n8n,temporal,langgraph}/contractual_obligations_tracker/`.
  - Per-contract obligation-tracking topology: `ingest-contract` →
    `extract-obligations` → `schedule-review` →
    `emit-obligation-evidence`; transitions deterministic and
    replay-tested across all three targets. This stream is the
    contract-time counterpart to the F-CP-03 supply-chain
    execution-time stream; both pin the operator's supply-chain
    posture along complementary axes (per-contract obligation surface
    vs. per-execution dependency surface).
  - Per-execution obligation-evidence-record emitted against
    `schemas/evidence/contractual-obligations.schema.json` (stream:
    `contractual_obligations`); `artifact_id` derives deterministically
    from
    `SHA-256(workflow_id|execution_id|contract_id|captured_at)`, so
    re-emissions inside the same execution against the same contract
    record at the same `captured_at` instant are byte-identical at
    the path level. The record pins the canonical `contract` block,
    the sorted `obligations[]` set, the paired `review_schedule[]`
    with `unknown` / `current` / `due_soon` / `overdue` / `waived`
    state classification, the NIS2 Article 21(2)(d)
    `regulation_refs`, and the closed `control_refs` list. The
    `artifact_id` does **not** key on `compile_target` — the three
    reference targets re-derive byte-identical bytes from the same
    execution context; byte-parity is asserted across targets.
  - Cookbook entry
    ([`docs/cookbook/contractual_obligations_tracker.md`](docs/cookbook/contractual_obligations_tracker.md))
    + per-target byte-parity goldens
    (`tests/examples/contractual_obligations_tracker/test_{n8n,temporal,langgraph}_workflow_golden.py`
    and `test_{n8n,temporal,langgraph}_obligation_evidence.py`) pin
    both the per-target workflow artefact and the per-target
    obligation-evidence record.
- **Sovereign-stack constraints:** Operator-supplied document store;
  no hosted DMS dependency, no vendor SDK bundled. The document-store
  read endpoint that `ingest-contract` reads, the review-policy
  source, and the artifact destination that
  `emit-obligation-evidence` writes are operator-configured; the
  framework ships no default endpoint.
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

- **Status:** Shipped
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

- **Status:** Shipped
- **Priority:** P1
- **Acceptance criteria:**
  - `content/evidence/incidents/<workflow-id>/` populated by the
    incident_management workflow.
- **Sovereign-stack constraints:** —
- **Depends on:** F-PT-02, F-WF-05
- **Source:** NIS2 Art. 21(2)(b), Art. 23.

### F-CP-03 — Supply-chain stream

- **Status:** Shipped
- **Priority:** P1
- **Acceptance criteria:**
  - `content/evidence/supply-chain/dependencies-snapshot.json`
    emitted per workflow execution that calls an external provider.
- **Sovereign-stack constraints:** Snapshot includes provider
  sovereignty classification.
- **Depends on:** F-PT-03
- **Source:** NIS2 Art. 21(2)(d), Art. 22.
- **Shipped via:**
  - SCHEMA — #286 (record-schema narrative at
    `content/evidence/supply-chain/SCHEMA.md`, the
    `vulnerability_triage` stream-root placeholder, and the Article 22
    mapping stub at
    `content/mappings/nis2/article-22-supply-chain.md`; JSON Schema at
    `schemas/evidence/dependencies-snapshot.schema.json` with provider
    sovereignty classification pinned).
  - CORE-FANOUT shared helper — #287 (framework-agnostic emitter at
    `compilers/_shared/evidence/supply_chain.py`).
  - CORE-FANOUT-N8N — #288 (n8n adapter at
    `compilers/n8n/evidence/supply_chain_node.py` wired into the
    `vulnerability_triage` workflow path, with a byte-stable sample
    emission under `examples/n8n/vuln_intake/evidence/supply-chain/`).
  - CORE-FANOUT-TEMPORAL — #289 (Temporal activity at
    `compilers/temporal/evidence/supply_chain_activity.py` wrapping
    the same shared helper, with a byte-stable sample emission under
    `examples/temporal/vuln_intake/evidence/supply-chain/`).
  - CORE-FANOUT-LG SKELETON — #290 (LangGraph node adapter at
    `compilers/langgraph/evidence/supply_chain_node.py` wrapping the
    same shared helper).
  - CORE-FANOUT-LG EXAMPLE — #291 (LangGraph worked example under
    `examples/langgraph/vuln_intake/evidence/supply-chain/`).
  - EXTEND-tests-goldens per-target byte-parity — #303 (n8n +
    Temporal + LangGraph; 21 replay tests).
  - EXTEND-drift SKELETON — #304 (drift-detection scaffolding for
    `dependencies-snapshot.json` across all three targets).
- EXTEND-metrics and EXTEND-NIS2-MAPPING (Art. 22 narrative) fan out
  into sibling cards tracked separately.

### F-CP-04 — Vulnerabilities stream

- **Status:** Shipped
- **Priority:** P1
- **Acceptance criteria:**
  - `content/evidence/vulns/` populated by `vulnerability_triage`
    with triage decisions and disclosure timelines.
- **Sovereign-stack constraints:** —
- **Depends on:** F-WF-01, F-PT-01
- **Source:** NIS2 Art. 21(2)(e).

### F-CP-05 — Crypto attestation stream

- **Status:** Shipped
- **Priority:** P2
- **Acceptance criteria:**
  - `content/evidence/crypto/secret-handling-attestation.json`
    emitted per workflow execution, asserting no secret was baked into
    workflow code (env-only injection).
- **Sovereign-stack constraints:** Hard rule: any workflow that fails
  the env-only check is refused at boot.
- **Depends on:** F-PT-01
- **Source:** NIS2 Art. 21(2)(h), Core Directive #6.
- **Shipped via:**
  - SCHEMA — #292 (typed record shape at
    `schemas/evidence/crypto-attestation.schema.json`; the three
    mechanical assertions — `secrets_baked_in: false`,
    `injection_mode: env`, UPPER_SNAKE_CASE `env_var_refs` only — are
    const-pinned at the schema).
  - EMITTER SKELETON — #293 (shared framework-agnostic helper at
    `compilers/_shared/evidence/crypto_attestation.py` and the
    Temporal-side activity wrapper at
    `compilers/temporal/evidence/crypto_attestation_activity.py`).
  - CORE-FANOUT-N8N — #296 (n8n adapter at
    `compilers/n8n/evidence/crypto_attestation_node.py` wired into the
    `vulnerability_triage` workflow path, with a byte-stable sample
    emission under `examples/n8n/vuln_intake/evidence/crypto/`).
  - CORE-FANOUT-LG — #297 (LangGraph node adapter at
    `compilers/langgraph/evidence/crypto_attestation_node.py` wrapping
    the same shared helper, with a byte-stable sample emission under
    `examples/langgraph/vuln_intake/evidence/crypto/`).
  - CORE-FANOUT-TEMPORAL-EXAMPLE — #300 (Temporal worked example
    under `examples/temporal/vuln_intake/evidence/crypto/`).
  - EXTEND-tests-goldens per-target byte-parity — #298 (n8n), #299
    (LangGraph), #301 (Temporal).
- EXTEND-drift, EXTEND-NIS2-MAPPING (Art. 21(2)(h) narrative), and
  the F-PT-01 refuse-at-boot enforcement fan out into sibling cards
  tracked separately.

### F-CP-06 — Effectiveness stream

- **Status:** Shipped
- **Priority:** P2
- **Acceptance criteria:**
  - `content/evidence/effectiveness/` populated with metric
    snapshots per policy / prompt version.
- **Sovereign-stack constraints:** Metrics are DSPy-evaluatable.
- **Depends on:** F-CR-03 (Removed — superseded by content-first;
  dependency satisfied), F-PT-01 (Shipped).
- **Source:** NIS2 Art. 21(2)(f).

### F-CP-07 — Access stream

- **Status:** Shipped
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

- **Status:** Shipped
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
- **Shipped via:** populated per-workflow data-flow documents under
  `content/mappings/gdpr/`, derived from
  `content/mappings/gdpr/_data-flow-template.md`:
  - `data-flow-alert_triage.md`
  - `data-flow-cloud_misconfiguration.md`
  - `data-flow-data_exfil.md`
  - `data-flow-executive_metrics.md`
  - `data-flow-identity_compromise.md`
  - `data-flow-incident_management.md`
  - `data-flow-on_call_rotation.md`
  - `data-flow-phishing_triage.md`
  - `data-flow-post_incident_review.md`
  - `data-flow-ransomware_containment.md`
  - `data-flow-threat_intel_ingest.md`
  - `data-flow-vuln_intake.md`

  Each document fills the seven required sections (purpose, lawful
  basis, categories, recipients, retention, cross-border, rights) and
  scores the cross-border section as "No transfer" as the
  sovereign-stack default, with the technical controls that hold the
  scoring named inline.

### F-GD-02 — Lawful-basis check in CI

- **Status:** Shipped
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

- **Status:** Shipped
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

- **Status:** Shipped
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
