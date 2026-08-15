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

## Maturity ladder

`playbook.schema.json` gives every playbook a `maturity` field
(`draft | experimental | stable | deprecated`) and defers its meaning
here. The ladder:

| Tier | Meaning |
|------|---------|
| `draft` | Scaffold exists; content is not yet trustworthy. |
| `experimental` | Complete enough to study and compile, not yet held to the stable bar. The default for new content. |
| `stable` | Deployment-ready: every criterion below holds. Deployers can adopt it without reading the source first. |
| `deprecated` | Kept for compatibility; do not adopt. Entry names its replacement. |

**Graduation to `stable` requires all of the following, and every
criterion is computed by `catalog.py` or enforced by CI — graduation is
a checklist, not a judgement call:**

1. Tier A in the catalogue: cookbook entry **and** deterministic
   primitives **and** every action step carries a real `core_body`
   binding (`real_bindings == action_steps`, zero placeholder bodies).
2. Zero blank predicates and zero schema errors.
3. Compiles to all three reference targets, with committed worked
   examples and byte-parity goldens for each.
4. Primitives have unit coverage; the playbook's scoped test suite and
   the hygiene linter pass at `LOW`.
5. `content_version` reaches `1.0.0` at graduation (semver: first
   stable interface), and the three worked examples are regenerated in
   the same change so their embedded metadata stays byte-true.

Demotion (`stable → deprecated`, or back to `experimental` when a
regression breaks a criterion) follows the same PR + Shipped-via
bookkeeping as graduation.

Enforcement status, stated honestly: the schema note that non-stable
content is "not compiled by default in production targets" is a
**deployer-side contract** — the reference compilers compile whatever
they are pointed at and carry `maturity` through as metadata for the
deployer's gate. Nothing in this repository silently skips content.

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

**Twelve entries in this epic were backfilled** — from
`F-WF-AGENTIC-RESPONSE` onward — for playbooks that shipped before they
carried a feature id. Until then this document under-reported the
catalogue by roughly a quarter: 48 playbooks on disk against 36 with an
entry, which is part of why the roadmap read as more finished than the
work was.

Their `Status` was determined from the artifacts rather than from
recollection, using the compile-playbooks catalogue: ten are
`In Progress` because they ship a CACAO scaffold, mappings, a cookbook
and three-target examples but **no `primitives/` directory**, so CORE is
genuinely outstanding on each; two are `Shipped` because they carry bound
primitives and their EXTEND artifacts. Acceptance criteria describe what
the finished feature requires, and the `Shipped via` lines record which
stage each PR actually landed — cross-cutting sweeps that touched many
playbooks at once (#862, #874, #877) are deliberately not cited as any
one playbook's provenance.

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

- **Status:** Shipped
- **Priority:** P3
- **Acceptance criteria:**
  - Identity lifecycle workflow with capability grant/revoke
    confirmation.
- **Sovereign-stack constraints:** —
- **Depends on:** F-WF-08 (Shipped)
- **Source:** NIS2 Art. 21(2)(i).
- **Shipped via:**
  - SKELETON — #364
    (`content/playbooks/onboarding_offboarding_tracker/` CACAO
    scaffold + lifecycle-event state machine + `nis2:art-21-2-i`
    mapping anchor reusing the F-CP-07 access evidence stream).
  - CORE-FANOUT-N8N — #366 (n8n emitter + worked example under
    `examples/n8n/onboarding_offboarding_tracker/` + byte-parity
    golden).
  - CORE-FANOUT-TEMPORAL — #367 (Temporal activity adapter + worked
    example under `examples/temporal/onboarding_offboarding_tracker/`
    + cross-target byte-parity golden).
  - CORE-FANOUT-LANGGRAPH — #368 (LangGraph node adapter + worked
    example under `examples/langgraph/onboarding_offboarding_tracker/`
    closing the three-target byte-parity ring).
  - EXTEND-metrics — #369 (joiner-to-provisioned-time and
    leaver-to-revoked-time KRI entries under `content/metrics/` with
    playbook pin).

### F-WF-12 — IT and security support agent

- **Status:** Shipped
- **Priority:** P3
- **Acceptance criteria:**
  - Ticket-shaped interaction workflow with explicit handoff to a
    human responder.
- **Sovereign-stack constraints:** —
- **Depends on:** F-WF-03 (Shipped)
- **Source:** NIS2 Art. 21(2)(b); community input.
- **Shipped via:**
  - SKELETON — #365 (`content/playbooks/it_security_support_agent/`
    CACAO scaffold + cookbook entry).
  - CORE-FANOUT-N8N-PRIM — #370 (five deterministic primitives under
    `content/playbooks/it_security_support_agent/primitives/` with
    unit coverage).
  - CORE-FANOUT-N8N-WIRE — #371 (playbook `core_body` binds + n8n
    worked example emission under
    `examples/n8n/it_security_support_agent/`).
  - CORE-FANOUT-N8N-GOLDEN — #372 (interaction-evidence emitter
    `compilers/n8n/evidence/` + byte-parity golden + immutable
    fixture under
    `tests/fixtures/it_security_support_agent/`).
  - CORE-FANOUT-TEMPORAL — #373 (Temporal activity adapter under
    `compilers/temporal/evidence/` + worked example under
    `examples/temporal/it_security_support_agent/` + cross-target
    byte-parity golden).
  - CORE-FANOUT-LANGGRAPH — #374 (LangGraph node adapter under
    `compilers/langgraph/evidence/` + worked example under
    `examples/langgraph/it_security_support_agent/` closing the
    three-target byte-parity ring).
  - GRADUATE — #935 (first maturity graduation: `experimental` →
    `stable`, `content_version` 1.0.0, per the Maturity ladder; all
    three worked examples regenerated with the new metadata).

### F-WF-SCS — Supply-chain security

- **Status:** Shipped
- **Priority:** P2
- **Acceptance criteria:**
  - `content/playbooks/supply_chain_security/` carries the canonical
    CACAO playbook (`playbook.supply_chain_security@v1`) and
    deterministic primitives (`assess.assess_supplier_signal`,
    `artifact.build_supply_chain_evidence_artifact`) with zero
    placeholders across both action bodies; compiled targets land
    under `examples/{n8n,temporal,langgraph}/supply_chain_security/`.
  - Per-signal supplier-assessment topology: `assess-supplier-signal`
    → `emit-supply-chain-evidence`; transitions deterministic and
    replay-tested across all three targets. This per-signal surface
    is the operator-side disposition counterpart to the F-CP-03
    per-execution `dependencies-snapshot.json` stream; both share
    `schemas/evidence/supply-chain.schema.json` and the shared
    emitter under `compilers/_shared/evidence/supply_chain.py`, and
    join on `(workflow_id, execution_id)`.
  - Per-execution supply-chain-evidence record emitted against
    `schemas/evidence/supply-chain.schema.json` (stream:
    `supply-chain`); `artifact_id` derives deterministically from
    `SHA-256(workflow_id|execution_id|captured_at)`, so re-emissions
    inside the same execution at the same `captured_at` instant are
    byte-identical at the path level. The record pins the canonical
    `assessment` block (closed `verdict` / `signal_class` /
    `affected_supplier_handle` / sorted PURL
    `affected_component_set`), the sorted `dependencies[]` set, the
    NIS2 Article 21(2)(d) `regulation_refs`, and the closed
    `control_refs` list. The `artifact_id` does **not** key on
    `compile_target` — the three reference targets re-derive
    byte-identical bytes from the same execution context; byte-parity
    is asserted across targets.
  - Cookbook entry
    ([`docs/cookbook/supply_chain_security.md`](docs/cookbook/supply_chain_security.md))
    + per-target byte-parity goldens
    (`tests/examples/supply_chain_security/test_{n8n,temporal,langgraph}_workflow_golden.py`
    and `test_{n8n,temporal,langgraph}_supply_chain_evidence.py`)
    pin both the per-target workflow artefact and the per-target
    supply-chain-evidence record.
- **Sovereign-stack constraints:** Operator-supplied signal feed and
  evidence sink; no hosted SBOM-correlation SaaS dependency, no
  default threat-intel feed binding, no vendor SDK bundled. The
  signal-feed source, the supplier-attestation lookup, and the
  artifact destination are operator-configured; the framework ships
  no default endpoint.
- **Depends on:** F-CP-03 (supply-chain stream)
- **Source:** NIS2 Art. 21(2)(d).
- **Shipped via:**
  - SKELETON — #418
    (`content/playbooks/supply_chain_security/` CACAO scaffold + G-01
    finalized-playbook coverage with `nis2:art-21-2-d` anchor).
  - CORE-PRIM — #419 (canonical `assess_supplier_signal` and
    `build_supply_chain_evidence_artifact` action logic under
    `content/playbooks/supply_chain_security/primitives/` with unit
    coverage and supplier-integrity invariant).
  - CORE-FANOUT-N8N — #420 (n8n emitter + worked example under
    `examples/n8n/supply_chain_security/` + byte-parity golden).
  - CORE-FANOUT-TEMPORAL — #421 (Temporal activity adapter + worked
    example under `examples/temporal/supply_chain_security/` +
    cross-target byte-parity golden).
  - CORE-FANOUT-LANGGRAPH — #422 (LangGraph node adapter + worked
    example under `examples/langgraph/supply_chain_security/`
    closing the three-target byte-parity ring).
- EXTEND-mappings (OSCAL / D3FEND / OCSF outbound closure on the
  supply_chain_security overlay, NIS2 / DORA / CRA inbound already
  landed via #431 / #438 / #440) and EXTEND-metrics
  (`kri.supplier_attestation_staleness@v1` and
  `kpi.supply_chain_coverage@v1` catalog entries pinning the emit
  step of the runtime supply-chain signal spine) shipped in the
  supply-chain EXTEND card.

---

### F-WF-VULN-MGMT — Vulnerability and patch management

- **Status:** Shipped
- **Priority:** P1
- **Goal:** G-01 (≥25 canonical CACAO v2 playbooks by Q4 2026 —
  vulnerability management closes a top-5 NIS2 Art. 21(2) control-
  family bar); G-02 (100% mapping coverage by Q3 2026 — the inbound
  anchor at `content/mappings/nis2/article-21-2-e.yaml` lands with
  the sibling EXTEND card so the outbound edge pinned in the
  playbook overlay closes the regulatory graph on the NIS2 axis).
- **Acceptance criteria (SKELETON):**
  - `content/playbooks/vulnerability_management/` carries the CACAO
    v2 scaffold (`playbook.vulnerability_management@v1`) with five
    action steps covering the discovery-to-audit lifecycle
    (`trigger_vulnerability_scan`, `triage_severity`,
    `decide_remediation`, `verify_remediation`,
    `emit_audit_evidence`) plus the outbound mappings overlay
    (`mappings.yaml`) pinning the NIS2 Art. 21(2)(e) anchor and the
    OSCAL RA-5 / SI-2 control + OCSF Vulnerability Finding /
    Compliance Finding surface.
  - Schema-validity test at
    `tests/content/test_vulnerability_management_playbook_schema.py`
    pins the CACAO artifact against `content-model/playbook.schema.json`,
    the mappings overlay against
    `schemas/playbook-mappings.schema.json`, and asserts the
    workflow-shape and primary NIS2 anchor.
- **Sovereign-stack constraints:** Operator-supplied scan surface
  (network / host / container / cloud-config scanner adapter),
  advisory-feed source (CVSS / EPSS / exploit-status enrichment),
  and evidence sink; no hosted vulnerability-management SaaS
  dependency, no default vendor SDK bundled. The scan adapter, the
  triage-signal source, and the evidence-record destination are
  operator-configured; the framework ships no default endpoint.
- **Depends on:** —
- **Source:** NIS2 Art. 21(2)(e). Overlaps CRA Art. 13(4)–13(5)
  (product vulnerability handling and security-updates
  distribution) and DORA Art. 25 (ICT vulnerability management);
  the EXTEND card closes the CRA / DORA overlap graph.

---

### F-WF-ASSET — Asset and configuration management

- **Status:** Shipped
- **Priority:** P2
- **Goal:** G-01 (content coverage — 25th canonical cookbook
  playbook, closing the top-5 NIS2 Art. 21 family bar); the
  inbound mapping at `content/mappings/nis2/article-21-2-i.yaml`
  citing `playbook.asset_management@v1` also defends G-02 (orphan-
  free regulatory graph) on the NIS2 axis.
- **Acceptance criteria:**
  - `content/playbooks/asset_management/` carries the canonical
    CACAO SKELETON (`playbook.asset_management@v1`) and the
    deterministic primitives (`reconcile.reconcile_inventory_snapshot`,
    `classify.classify_inventory_delta`,
    `artifact.build_asset_inventory_delta_evidence_artifact`) with
    zero placeholders across all action bodies; compiled targets
    land under `examples/{n8n,temporal,langgraph}/asset_management/`.
  - Per-window reconciliation topology:
    `ingest-inventory-sources` → `reconcile-authoritative-inventory`
    → `compute-delta-against-previous-snapshot` → `classify-delta`
    → `capture-evidence` → `notify-inventory-owner`; transitions
    deterministic and replay-tested across all three targets.
  - Per-window asset-inventory-delta evidence record emitted against
    a stable evidence-stream schema (candidate: extend the access
    stream `schemas/evidence/access.schema.json` for the
    capability-inventory companion shape, or stand up a dedicated
    `schemas/evidence/inventory.schema.json` envelope at the
    CORE-PRIM card). The record pins the canonical reconciliation
    block (sorted, normalised asset set, source-attribution carry,
    closed per-delta classification enumeration), the NIS2
    Article 21(2)(i) `regulation_refs`, and the closed
    `control_refs` list. The `artifact_id` derives deterministically
    from `SHA-256(workflow_id|execution_id|captured_at)`, so
    re-emissions inside the same execution at the same `captured_at`
    instant are byte-identical at the path level. The `artifact_id`
    does **not** key on `compile_target` — the three reference
    targets re-derive byte-identical bytes from the same execution
    context; byte-parity is asserted across targets.
  - Cookbook entry (`docs/cookbook/asset_management.md`) + per-
    target byte-parity goldens
    (`tests/examples/asset_management/test_{n8n,temporal,langgraph}_workflow_golden.py`
    and `test_{n8n,temporal,langgraph}_asset_inventory_delta_evidence.py`)
    pin both the per-target workflow artefact and the per-target
    asset-inventory-delta evidence record.
- **Sovereign-stack constraints:** Operator-supplied inventory
  sources (CMDB, IaC state backend, cloud-provider asset APIs,
  endpoint-management agent control plane) and evidence sink; no
  hosted CMDB-correlation SaaS dependency, no default endpoint-
  management SDK bundled. The inventory-source set and the
  artifact destination are operator-configured; the framework
  ships no default endpoint.
- **Depends on:** F-CP-07 (access stream — companion capability-
  inventory artifact shape, candidate envelope for the per-window
  inventory record), F-CR-01 (`ToolIO` contract for the primitives).
- **Source:** NIS2 Art. 21(2)(i) — human resources security,
  access-control policies, and asset management.
- **SKELETON → CORE → EXTEND decomposition plan:**
  - SKELETON (this card) —
    `content/playbooks/asset_management/` CACAO topology + IDs +
    schema refs, `mappings.yaml` outbound (OSCAL CM-8 / CM-8(2),
    OCSF API Activity, NIS2 Art. 21(2)(i) inbound closure with
    `article-21-2-i.yaml` `playbook_refs:` update), DORA / CRA
    gap-note `_orphan_skip` entries (Art. 8 / Annex I §1 inbound
    deferred), GDPR per-workflow RoPA entry (no-personal-data
    pattern, mirrors patch_management).
  - CORE-PRIM — Deterministic per-step primitives under
    `content/playbooks/asset_management/primitives/`:
    `reconcile.reconcile_inventory_snapshot` (sorted, normalised
    asset-set hash → snapshot id), `classify.classify_inventory_delta`
    (per-delta taxonomy resolver), and the canonical evidence
    artifact builder, with unit coverage and a normalisation
    invariant test asserting source-precedence ordering.
  - CORE-FANOUT-N8N — n8n emitter under
    `compilers/n8n/asset_management/` + worked example under
    `examples/n8n/asset_management/` + byte-parity golden.
  - CORE-FANOUT-TEMPORAL — Temporal activity adapter under
    `compilers/temporal/asset_management/` + worked example under
    `examples/temporal/asset_management/` + cross-target byte-
    parity golden.
  - CORE-FANOUT-LANGGRAPH — LangGraph node adapter under
    `compilers/langgraph/asset_management/` + worked example
    under `examples/langgraph/asset_management/` closing the
    three-target byte-parity ring.
  - EXTEND-mappings — D3FEND per-step lift (D3-AI Asset Inventory,
    D3-SWI Software Inventory, baseline-drift slice pin), DORA
    Art. 8 inbound-closure card under
    `content/mappings/dora/` removing the
    `_orphan_skip` entry, CRA Annex I scope-mapping review card
    (manufacturer-vs-operator clarification) ahead of any CRA
    inbound.
  - EXTEND-metrics — `kri.asset_inventory_drift@v1` and a new
    `kpi.unmanaged_asset_cardinality@v1` emitter against the
    operator's evidence store with the per-window observation
    series and threshold-band pinning.
- **Shipped via:**
  - SKELETON — #515
    (`content/playbooks/asset_management/` CACAO scaffold + G-01
    finalized-playbook coverage with `nis2:art-21-2-i` anchor closing
    the top-5 NIS2 Art. 21 family bar as the 25th canonical cookbook
    playbook).
  - CORE-PRIM — #516 (canonical
    `reconcile.reconcile_inventory_snapshot`,
    `classify.classify_inventory_delta`, and
    `artifact.build_asset_inventory_delta_evidence_artifact` action
    logic under `content/playbooks/asset_management/primitives/`
    with unit coverage and the source-precedence normalisation
    invariant).
  - CORE-FANOUT-N8N — #517 (n8n emitter + worked example under
    `examples/n8n/asset_management/` + byte-parity golden).
  - CORE-FANOUT-TEMPORAL — #518 (Temporal activity adapter + worked
    example under `examples/temporal/asset_management/` +
    cross-target byte-parity golden).
  - CORE-FANOUT-LANGGRAPH — #518 (LangGraph node adapter + worked
    example under `examples/langgraph/asset_management/` closing
    the three-target byte-parity ring).
  - EXTEND-mappings-DORA — #519 (DORA Art. 8 inbound closure under
    `content/mappings/dora/` removing the prior `_orphan_skip`
    entry).
  - EXTEND-DOCS — #520 (`docs/cookbook/asset_management.md`
    cookbook entry).
  - EXTEND-metrics — #521 (`kri.asset_inventory_drift@v1` and
    `kpi.unmanaged_asset_cardinality@v1` emitters under
    `content/metrics/` with per-window observation series and
    threshold-band pinning).
  - EXTEND-mappings-D3FEND — #522 (per-step D3FEND defensive-
    technique lift covering D3-AI Asset Inventory, D3-SWI Software
    Inventory, and the baseline-drift slice pin).
  - EXTEND-mappings-CRA — #523 (CRA Annex I scope-mapping review,
    shipped as a documented manufacturer-vs-operator scope
    deferral; the CRA axis is recorded as a documented
    `_orphan_skip` rather than an inbound closure).

---

### F-WF-DPIA — GDPR Art. 35 Data Protection Impact Assessment lifecycle

- **Status:** Shipped
- **Priority:** P1
- **Goal:** G-01 (content coverage — canonical DPIA cookbook
  playbook covering the Article 35 lifecycle from screening through
  DPO consultation and, where required, Article 36 prior consultation
  with the supervisory authority), G-02 (regulatory-graph closure —
  GDPR Art. 35 is the primary inbound anchor, with Art. 36 covering
  the prior-consultation branch).
- **Acceptance criteria:**
  - `content/playbooks/data_protection_impact_assessment/` carries
    the canonical CACAO v2 playbook
    (`playbook.data_protection_impact_assessment@v1`) and the
    deterministic primitives with zero placeholders across all
    action bodies; compiled targets land under
    `examples/{n8n,temporal,langgraph}/data_protection_impact_assessment/`.
  - Per-assessment DPIA topology covering the Article 35 lifecycle:
    screening → threshold decision → assessment (necessity,
    proportionality, risks to rights and freedoms, mitigations) →
    DPO consultation → residual-risk gate → optional Article 36
    prior consultation with the supervisory authority → decision
    record → evidence emission; transitions deterministic and
    replay-tested across all three targets.
  - Per-assessment DPIA evidence record emitted against a stable
    evidence-stream schema (candidate:
    `schemas/evidence/dpia.schema.json`) pinning the closed
    screening outcome, the residual-risk verdict, the DPO
    consultation record, the Article 35 `regulation_refs` (plus
    Article 36 when the prior-consultation branch fires), and the
    closed `control_refs` list. `artifact_id` derives
    deterministically from
    `SHA-256(workflow_id|execution_id|captured_at)`; the field
    does **not** key on `compile_target` so the three reference
    targets re-derive byte-identical bytes from the same execution
    context, and byte-parity is asserted across targets.
  - Cookbook entry
    (`docs/cookbook/data_protection_impact_assessment.md`) + per-
    target byte-parity goldens
    (`tests/examples/data_protection_impact_assessment/test_{n8n,temporal,langgraph}_workflow_golden.py`
    and per-target DPIA-evidence goldens) pin both the workflow
    artefact and the DPIA-evidence record.
  - OSCAL / D3FEND regulatory-graph closure on the GDPR axis
    (Art. 35 inbound, Art. 36 covering the prior-consultation
    branch); the D3FEND lift covers the risk-assessment and
    consultation slices.
- **Sovereign-stack constraints:** CACAO v2 content only, no
  proprietary schema. GDPR Art. 35 / Art. 36 are the regulatory
  anchors; operator-supplied processing-activity register, DPO
  consultation surface, and evidence sink — the framework ships no
  hosted DPIA-workflow SaaS binding and no default non-EU endpoint.
- **Depends on:** F-WF-05 (incident management — reused DPO
  consultation evidence pattern and consultation-record shape).
- **Source:** GDPR Art. 35 (DPIA obligation), GDPR Art. 36 (prior
  consultation with the supervisory authority).
- **Shipped via:**
  - SKELETON — #625
    (`content/playbooks/data_protection_impact_assessment/` CACAO v2
    playbook + GDPR Art. 35 inbound anchor + Art. 36 prior-consultation
    branch topology + outbound overlay).
  - CORE — #627 (three-target compile-target emitters: n8n, Temporal,
    LangGraph + evidence schema `schemas/evidence/dpia.schema.json` +
    byte-parity goldens + per-target DPIA-evidence goldens).
  - EXTEND — #628
    (`docs/cookbook/data_protection_impact_assessment.md` walkthrough).

---

### F-WF-NIS2-SELF-ASSESS — NIS2 Art. 21 operator self-assessment report template

- **Status:** Shipped
- **Priority:** P1
- **Goal:** G-01 (content coverage — a whole-Article roll-up
  playbook that lets an operator walk the ten NIS2 Art. 21(2)(a-j)
  measure families in a single deterministic workflow and emit a
  self-assessment report against the existing per-measure playbook
  family), G-06 (contributor adoption — an operator-facing
  self-assessment template lowers the barrier for a new contributor
  verifying their own deployment against the framework before
  proposing a change).
- **Acceptance criteria:**
  - `content/playbooks/nis2_self_assessment/` carries the canonical
    CACAO v2 scaffold (`playbook.nis2_self_assessment@v1`) with the
    ten Art. 21(2)(a-j) measure-family sections wired as
    deterministic steps, a `mappings.yaml` pinning inbound anchors
    for each of the ten sub-paragraphs, and a README walking the
    operator through the roll-up structure.
  - Inbound backlinks land on all ten per-measure Art. 21(2)(a-j)
    map files so the roll-up is discoverable from the existing
    NIS2 measure playbook family.
  - Three reference-target compile examples land under
    `examples/{n8n,temporal,langgraph}/nis2_self_assessment/` with
    byte-parity goldens across all three targets.
  - Cookbook entry `docs/cookbook/nis2_self_assessment.md`
    walks an operator through running the self-assessment
    end-to-end against a reference deployment.
- **Sovereign-stack constraints:** CACAO v2 content only, no
  proprietary schema. NIS2 Art. 21(2)(a-j) are the regulatory
  anchors; operator-supplied evidence sink and no default non-EU
  endpoint.
- **Depends on:** — (standalone roll-up referencing the existing
  Art. 21(2)(a-j) per-measure playbook family)
- **Source:** NIS2 Directive (EU) 2022/2555 Art. 21(2)(a-j);
  enforcement active July 2026.
- **Shipped via:**
  - SKELETON — #630
    (`content/playbooks/nis2_self_assessment/` CACAO v2 scaffold +
    `mappings.yaml` + README + inbound backlinks on all ten
    Art. 21(2)(a-j) map files).
  - CORE — #631 (three-target compile examples under
    `examples/{n8n,temporal,langgraph}/nis2_self_assessment/`
    + byte-parity goldens across targets).
  - EXTEND — #632
    (`docs/cookbook/nis2_self_assessment.md` walkthrough).

---

### F-WF-DORA-SELFASSESS — DORA Chapter II ICT risk management operator self-assessment roll-up

- **Status:** Shipped
- **Priority:** P1
- **Goal:** G-01 (content coverage — a whole-Chapter roll-up
  playbook that lets a DORA-in-scope financial entity walk the five
  Chapter II ICT risk management section atoms (Articles 6, 7, 8,
  10, 11) in a single deterministic workflow and emit a dated
  self-assessment attestation on the Article 6(5) annual review
  cadence plus the post-major-incident review trigger the same
  paragraph names).
- **Acceptance criteria:**
  - `content/playbooks/dora_ict_risk_selfassess/` carries the
    canonical CACAO v2 scaffold
    (`playbook.dora_ict_risk_selfassess@v1`) with the five Chapter
    II section atoms wired as deterministic steps, a `mappings.yaml`
    pinning inbound anchors for each of the five sections, and a
    README walking the operator through the roll-up structure.
  - Inbound backlinks land on all five per-section DORA Chapter II
    map files (`article-6.yaml`, `article-7.yaml`, `article-8.yaml`,
    `article-10.yaml`, `article-11.yaml`) so the roll-up is
    discoverable from the existing per-section anchor set.
  - Three reference-target compile examples land under
    `examples/{n8n,temporal,langgraph}/dora_ict_risk_selfassess/`
    with byte-parity goldens across all three targets.
  - Cookbook entry `docs/cookbook/dora_ict_risk_selfassess.md`
    walks an operator through running the self-assessment
    end-to-end against a reference deployment.
- **Sovereign-stack constraints:** CACAO v2 content only, no
  proprietary schema. DORA Chapter II (Articles 6, 7, 8, 10, 11) are
  the regulatory anchors; operator-supplied evidence sink and no
  default non-EU endpoint.
- **Depends on:** — (standalone roll-up referencing the existing
  per-section playbook family).
- **Source:** DORA — Regulation (EU) 2022/2554 Chapter II
  (Articles 6 to 14) ICT risk management; Article 6(5) annual
  review of the ICT risk-management framework and the post-major-
  incident review trigger; Commission Delegated Regulation (EU)
  2024/1774 (JC RTS on the ICT risk-management framework).
- **Shipped via:**
  - SKELETON — #648
    (`content/playbooks/dora_ict_risk_selfassess/` CACAO v2 scaffold
    + `mappings.yaml` + README + inbound backlinks on all five
    Chapter II section map files).
  - CORE — #649 (three-target compile examples under
    `examples/{n8n,temporal,langgraph}/dora_ict_risk_selfassess/`
    + byte-parity goldens across targets).

---

### F-CACAO-NIS2-ART20 — NIS2 Art. 20 management-body cyber-governance playbook

- **Status:** Shipped
- **Priority:** P1
- **Goal:** G-01 (content coverage — a portable CACAO v2 playbook that
  lets an operator discharge the NIS2 Art. 20 management-body approval,
  oversight, and cyber-security training obligations against a
  deterministic workflow with dated approval and training-completion
  evidence), G-03 (compile-target parity — the same playbook emits
  byte-identical artifacts across n8n, Temporal, and LangGraph).
- **Acceptance criteria:**
  - `content/playbooks/nis2_art20_governance/` carries the canonical
    CACAO v2 scaffold (`playbook.nis2_art20_governance@v1`) with the
    four management-body governance action steps wired as deterministic
    primitives (management-body approval, oversight review,
    training-completion, evidence emission), a `mappings.yaml` pinning
    the NIS2 Art. 20 inbound anchor and the OSCAL AT-family training
    outbound anchors, and a README walking the operator through the
    workflow.
  - Three reference-target compile examples land under
    `examples/{n8n,temporal,langgraph}/nis2_art20_governance/` with
    byte-parity goldens across all three targets and shared
    `regenerate.sh` recipes.
  - Per-target unit coverage on the four governance primitives plus
    per-example byte-parity golden tests under
    `tests/examples/nis2_art20_governance/`.
- **Sovereign-stack constraints:** CACAO v2 content only, no proprietary
  schema. NIS2 Art. 20 is the regulatory anchor; operator-supplied
  training-completion source, management-body approval sink, and
  evidence destination — the framework ships no default non-EU
  endpoint.
- **Depends on:** — (standalone Art. 20 governance atom; complements
  the existing Art. 21(2)(a-j) per-measure playbook family).
- **Source:** NIS2 Directive (EU) 2022/2555 Art. 20 (management bodies
  — approval of cyber-security risk-management measures, oversight of
  their implementation, and mandatory management-body training);
  enforcement active July 2026.
- **Shipped via:**
  - SKELETON — #762
    (`content/playbooks/nis2_art20_governance/` CACAO v2 scaffold +
    `mappings.yaml` + README + NIS2 Art. 20 inbound anchor).
  - CORE-PRIMITIVES — #764 (four deterministic primitives under
    `content/playbooks/nis2_art20_governance/primitives/` with unit
    coverage).
  - CORE-FANOUT — #765 (three-target compile examples under
    `examples/{n8n,temporal,langgraph}/nis2_art20_governance/`).
  - CORE-GOLDENS — #776 (byte-parity golden tests under
    `tests/examples/nis2_art20_governance/` closing the three-target
    parity ring).
  - EXTEND — practitioner cookbook walkthrough at
    `docs/cookbook/nis2_art20_governance.md` and cookbook index
    entry under `docs/cookbook/README.md`.

---

### F-WF-DORA-TPR — DORA Chapter V ICT third-party risk management contract-lifecycle spine

- **Status:** Shipped
- **Priority:** P1
- **Goal:** G-01 (content coverage — a portable contract-lifecycle
  workflow that lets a DORA-in-scope financial entity discharge the
  Article 28 / Article 30 obligation set against every ICT third-party
  service provider, from pre-contractual risk assessment through
  register-of-information maintenance and periodic re-scoring to a
  dated Article 28(8) exit-strategy attestation) and G-02 (regulatory
  mapping — inbound anchors on the DORA Article 28 register atom and
  a new Article 30 clause-set atom).
- **Acceptance criteria:**
  - `content/playbooks/dora_tpr_management/` carries the canonical
    CACAO v2 scaffold (`playbook.dora_tpr_management@v1`) with the
    five DORA Chapter V lifecycle atoms wired as deterministic steps
    (onboarding_risk_assessment → contractual_provisions_check →
    register_entry → periodic_review → exit_assessment), a
    `mappings.yaml` pinning outbound OSCAL SR-3 / SR-6 anchors and
    the OCSF API-Activity binding, and a README walking the operator
    through the lifecycle structure.
  - Inbound backlinks land on the DORA Article 28 register atom in
    `content/mappings/dora/article-19-and-28.yaml` and on a new
    `content/mappings/dora/article-30.yaml` entry for the Article 30
    closed clause set.
  - Three reference-target compile examples land under
    `examples/{n8n,temporal,langgraph}/dora_tpr_management/` with
    byte-parity goldens across all three targets.
  - Cookbook entry `docs/cookbook/dora_tpr_management.md` walks an
    operator through running the lifecycle end-to-end against a
    reference deployment, including the runtime supply-chain-evidence
    join into the periodic-review step and the target-agnostic
    `artifact_id` derivation for the register row and the exit
    attestation.
- **Sovereign-stack constraints:** CACAO v2 content only, no
  proprietary schema. DORA Chapter V (Articles 28 and 30) are the
  regulatory anchors; operator-supplied evidence sink and no default
  non-EU endpoint. Register-row shape follows Commission Implementing
  Regulation (EU) 2024/2956 (ITS on the standard templates for the
  register of information).
- **Depends on:** F-WF-SCS (runtime supply-chain-signal spine — the
  periodic-review step joins against its per-execution supply-chain-
  evidence stream on the shared `provider.<id>@v<n>` handle).
- **Source:** DORA — Regulation (EU) 2022/2554 Chapter V, Articles
  28 (general principles for the use of ICT third-party service
  providers) and 30 (key contractual provisions); Commission
  Implementing Regulation (EU) 2024/2956 (ITS on the register of
  information).
- **Shipped via:**
  - SKELETON — #721
    (`content/playbooks/dora_tpr_management/` CACAO v2 scaffold
    + `mappings.yaml` + README).
  - CORE — #722 (three-target compile examples under
    `examples/{n8n,temporal,langgraph}/dora_tpr_management/`
    + byte-parity goldens across targets + inbound DORA anchor
    wiring).
  - EXTEND — PR #723 (practitioner cookbook walkthrough and
    ROADMAP `Shipped` flip).

---

### F-WF-CRA-CVD — CRA Article 14 coordinated vulnerability disclosure lifecycle

- **Status:** Shipped
- **Priority:** P1
- **Goal:** G-01 (content coverage — a portable operator-side
  coordinated vulnerability disclosure lifecycle discharging CRA
  Article 14 §1 (CVD policy operation) and §6 (acknowledgement to the
  reporter), from reporter intake through public advisory publication;
  advances the Q4 2026 target of ≥ 25 CACAO v2 playbooks) and G-02
  (regulatory-graph closure — CRA Article 14 primary anchor, Annex I
  §2(2) / §2(5) inbound anchors, GDPR Art. 32(1)(b) channel-security
  overlay, GDPR Art. 30 ROPA entry).
- **Acceptance criteria:**
  - `content/playbooks/cra_cvd/` carries the canonical CACAO v2
    scaffold (`playbook.cra_cvd@v1`) — seven action steps (intake →
    ack_to_reporter → triage → develop_fix → validate_fix →
    coordinate_disclosure → publish_advisory) plus start / end edge
    wiring, deterministic transitions, eight workflow-scope variables
    (`__case_id__`, `__reporter_contact__`, `__reporter_ack_ts__`,
    `__triage_verdict__`, `__actively_exploited__`, `__fix_ref__`,
    `__disclosure_target_date__`, `__advisory_id__`), a
    `mappings.yaml` pinning outbound OSCAL SI-5 / RA-5, OCSF
    Vulnerability Finding + Compliance Finding, and CRA Annex I §2
    overlay entries, plus a workflow-local README.
  - Two CORE primitives land under
    `content/playbooks/cra_cvd/primitives/`
    (`reporter.send_acknowledgement`,
    `disclosure.build_advisory_artifact`) with `core_body` bindings on
    the `ack_to_reporter` and `publish_advisory` action steps;
    `coordinate_disclosure` binding is CORE-DEFERRED pending the
    two-variable `out_args` collapse (revisited in EXTEND).
  - Three Jinja2 templates under
    `content/playbooks/cra_cvd/templates/`: `ack_letter.j2`,
    `advisory.md.j2` (human-readable), and `advisory.csaf2.json.j2`
    (machine-readable CSAF 2.0). Templates are reference forms;
    per-operator forking is expected.
  - Three reference-target compile examples land under
    `examples/{n8n,temporal,langgraph}/cra_cvd/` with byte-parity
    goldens under `tests/examples/cra_cvd/test_golden.py` guarding
    the ring across all three targets on every PR.
  - Inbound anchors land on `cra:annex-i-2-vuln-handling` and
    `cra:annex-i-2-cvd-policy` in
    `content/mappings/cra/article-14-and-annex-i.yaml`. Overlap with
    `codebase_vuln_management` is anchored at
    `cra:annex-i-2-codebase-vuln-mgmt`.
  - GDPR Art. 32(1)(b) channel-security anchor lands on
    `content/mappings/gdpr/article-32-security-of-processing.yaml`;
    per-workflow ROPA entry at
    `content/mappings/gdpr/data-flow-cra_cvd.md`. NIS2 Art. 23 and
    GDPR Art. 33 overlaps are recorded as audited exclusions in the
    respective `_orphan_skip.yaml` files (the parallel-notification
    chains belong to `incident_management` / a GDPR-scoped breach
    playbook).
  - Cookbook entry `docs/cookbook/cra_cvd.md` walks an operator
    through the CVD lifecycle end-to-end against a compiled example
    (n8n / Temporal / LangGraph), including the prerequisites the
    operator wires (SMTP endpoint handle, CSIRT endpoint handle,
    advisory-publishing hook), the step-by-step operator playbook,
    the evidence-record shape (CSAF 2.0 envelope, acknowledgement
    envelope, per-step OCSF records), and the sovereign-stack note
    on operator-supplied endpoints.
- **Sovereign-stack constraints:** CACAO v2 content only, no
  proprietary schema. CRA Article 14 is the regulatory anchor. No
  hardcoded SMTP / CSIRT / advisory-publishing endpoint — the
  operator wires each at the compile-target config layer. CSAF 2.0
  is the machine-readable advisory shape.
- **Depends on:** F-WF-01 (vulnerability triage — shared operator-
  side vulnerability-management surface anchored on OSCAL RA-5),
  F-WF-07 (codebase vulnerability management — adjacent
  outbound-scan leg of the shared vulnerability discipline).
- **Source:** Cyber Resilience Act (Regulation (EU) 2024/2847)
  Article 14 §1 (CVD policy obligation) and §6 (acknowledgement-to-
  reporter obligation); CRA Annex I §2(2) (vulnerability-handling
  requirements) and §2(5) (CVD policy with single point of contact);
  CSAF 2.0 (Common Security Advisory Framework, OASIS); ISO/IEC
  29147:2018 (vulnerability disclosure guidance); RFC 9116
  (`security.txt`).
- **Shipped via:**
  - SKELETON — #591 / #592 (CACAO v2 scaffold + outbound overlay +
    cookbook narrative + regulatory-anchor sidebar).
  - CORE-A — #595 / #596 (D3-IRA + IR-6/SI-2 + Art.14§6
    acknowledgement-SLA KPI wiring + three-target compiled examples).
  - CORE-B-PRIM — #741 (three primitives at
    `content/playbooks/cra_cvd/primitives/` + `core_body` bindings on
    `ack_to_reporter` and `publish_advisory`).
  - CORE-B-EXAMPLES — #743 (three-target examples/goldens regenerated
    from the CORE-B-PRIM source + cookbook status flipped to CORE +
    GDPR data-flow ROPA entry lifted to CORE).
  - EXTEND — PR #744 (operator-facing cookbook walkthrough:
    prerequisites, step-by-step, worked example, evidence-record
    shape, sovereign-stack note; ROADMAP `Shipped` flip).

---

### F-WF-PATCH — Patch management lifecycle

- **Status:** Shipped
- **Priority:** P1
- **Goal:** G-01 (content coverage — a portable operator-side
  patch / update maintenance workflow discharging NIS2
  Art. 21(2)(e), from update detection through canary-ring
  validation, fan-out, evidence capture and owner notification;
  advances the Q4 2026 target of ≥ 25 CACAO v2 playbooks), G-02
  (regulatory-graph closure — NIS2 Art. 21(2)(e) primary anchor;
  DORA Art. 9 ICT-risk-management (operations and maintenance)
  and CRA Annex I §2 security-updates inbound anchors are
  audited-skip / deferred to separate inbound-closure cards),
  G-03 (compile-target parity — n8n / Temporal / LangGraph
  goldens carry the ring across every PR).
- **Acceptance criteria:**
  - `content/playbooks/patch_management/` carries the canonical
    CACAO v2 scaffold (`playbook.patch_management@v1`) — the
    detect → classify → stage → validate → fan-out →
    evidence-capture → notify chain against the operator's
    pre-bound deployment-ring topology, plus `mappings.yaml`
    pinning outbound OSCAL (SI-2 / CM-3), OCSF telemetry, and
    the NIS2 Art. 21(2)(e) overlay, plus a workflow-local
    README.
  - Six CORE primitives under
    `content/playbooks/patch_management/primitives/`
    (`detect`, `classify`, `stage`, `validate`, `fanout`,
    `artifact`) with `core_body` bindings across the action
    steps.
  - Three reference-target compile examples land under
    `examples/{n8n,temporal,langgraph}/patch_management/` with
    byte-parity goldens under
    `tests/examples/{n8n,temporal,langgraph}/patch_management/test_golden.py`
    guarding the ring across all three targets on every PR.
  - Cookbook entry `docs/cookbook/patch_management.md` walks an
    operator through the maintenance lifecycle end-to-end
    against a compiled example (n8n / Temporal / LangGraph).
- **Sovereign-stack constraints:** CACAO v2 content only, no
  proprietary schema. NIS2 Art. 21(2)(e) is the regulatory
  anchor. No hardcoded patch-distribution endpoint — the
  operator wires the deployment-ring topology and health-gate
  signals at the compile-target config layer.
- **Depends on:** —
- **Source:** NIS2 (Directive (EU) 2022/2555) Art. 21(2)(e);
  NIST SP 800-53 SI-2, CM-3.
- **Shipped via:**
  - SKELETON + CORE + EXTEND landed prior to formal ROADMAP
    entry: `content/playbooks/patch_management/` scaffold +
    six primitives, three-target compile examples with
    byte-parity goldens, and the operator cookbook
    (`docs/cookbook/patch_management.md`).
  - ROADMAP `Shipped` flip — PR #746 (formal ROADMAP entry
    for the already-landed trilogy; README Status flip to
    reflect actual delivery state).

---

### F-WF-CYBERHYG — Security-awareness and cyber-hygiene training

- **Status:** Shipped
- **Priority:** P1
- **Goal:** G-01 (content coverage — a portable operator-side
  proactive security-awareness and cyber-hygiene training
  workflow discharging NIS2 Art. 21(2)(g), companion to the
  reactive `phishing_triage` playbook under the same article;
  advances the Q4 2026 target of ≥ 25 CACAO v2 playbooks), G-02
  (regulatory-graph closure — NIS2 Art. 21(2)(g) primary anchor
  covering the training / awareness leg of the article; the
  reactive `phishing_triage` playbook covers the incident-
  response leg), G-03 (compile-target parity — n8n / Temporal /
  LangGraph goldens carry the ring across every PR).
- **Acceptance criteria:**
  - `content/playbooks/cyber_hygiene_training/` carries the
    canonical CACAO v2 scaffold
    (`playbook.cyber_hygiene_training@v1`) — the roster-
    inventory → schedule → phishing-simulation → completion-
    tracking → attestation → notify chain, plus
    `mappings.yaml` pinning outbound OSCAL controls, OCSF
    telemetry, and the NIS2 Art. 21(2)(g) overlay, plus a
    workflow-local README. Read-only and side-effect-free
    against operator infrastructure; the simulation step is a
    clearly-labelled exercise that does not trigger incident
    response.
  - Three reference-target compile examples land under
    `examples/{n8n,temporal,langgraph}/cyber_hygiene_training/`
    with byte-parity goldens under
    `tests/examples/{n8n,temporal,langgraph}/cyber_hygiene_training/test_golden.py`
    guarding the ring across all three targets on every PR.
  - Cookbook entry `docs/cookbook/cyber_hygiene_training.md`
    walks an operator through the training programme end-to-end
    against a compiled example (n8n / Temporal / LangGraph).
- **Sovereign-stack constraints:** CACAO v2 content only, no
  proprietary schema. NIS2 Art. 21(2)(g) is the regulatory
  anchor. No hardcoded LMS / HR / mailflow endpoint — the
  operator wires each at the compile-target config layer. The
  phishing-simulation step is a labelled exercise and does not
  mutate production mailflow controls.
- **Depends on:** F-WF-04 (phishing_triage — the reactive
  incident-response leg of NIS2 Art. 21(2)(g); this workflow is
  the proactive training / awareness companion).
- **Source:** NIS2 (Directive (EU) 2022/2555) Art. 21(2)(g)
  (basic cyber-hygiene practices and cybersecurity training).
- **Shipped via:**
  - SKELETON + CORE + EXTEND landed prior to formal ROADMAP
    entry: `content/playbooks/cyber_hygiene_training/`
    scaffold, three-target compile examples with byte-parity
    goldens, and the operator cookbook
    (`docs/cookbook/cyber_hygiene_training.md`).
  - ROADMAP `Shipped` flip — PR #746 (formal ROADMAP entry
    for the already-landed trilogy; README Status flip to
    reflect actual delivery state).

---

### F-WF-SECAWARENESS — Security-awareness training programme lifecycle

- **Status:** Shipped
- **Priority:** P1
- **Goal:** G-01 (content coverage — a portable operator-side
  programme-lifecycle workflow for the structured security-
  awareness training programme required by NIS2 Art. 21(2)(g);
  companion to the operational `cyber_hygiene_training` playbook
  and the reactive `phishing_triage` playbook under the same
  clause; advances the Q4 2026 target of ≥ 25 CACAO v2 playbooks),
  G-02 (regulatory-graph closure — NIS2 Art. 21(2)(g) primary
  anchor for the programme-governance surface, with sibling
  references to GDPR Art. 32(1)(b) staff-training organisational
  measures and ISO/IEC 27001 Annex A.6.3).
- **Acceptance criteria:**
  - `content/playbooks/security_awareness_training/` carries the
    canonical CACAO v2 scaffold
    (`playbook.security_awareness_training@v1`) — the schedule-
    assessment → design-content → deliver-training → record-
    completion → report-gaps → review-cycle chain, plus
    `mappings.yaml` pinning outbound OSCAL controls, an OCSF
    telemetry stub, the NIS2 Art. 21(2)(g) overlay, and the GDPR
    Art. 32(1)(b) sibling reference, plus a workflow-local README.
    Read-only and side-effect-free against operator
    infrastructure; the delivery step writes delivery-intent
    records to the learning-management surface, and the LMS owns
    final scheduling and per-staff dispatch.
  - Three reference-target compile examples land under
    `examples/{n8n,temporal,langgraph}/security_awareness_training/`
    with byte-parity goldens under
    `tests/examples/{n8n,temporal,langgraph}/security_awareness_training/test_golden.py`
    guarding the ring across all three targets on every PR.
  - Cookbook entry
    `docs/cookbook/security_awareness_training.md` walks an
    operator through the programme-lifecycle cycle end-to-end
    against a compiled example (n8n / Temporal / LangGraph).
- **Sovereign-stack constraints:** CACAO v2 content only, no
  proprietary schema. NIS2 Art. 21(2)(g) is the primary regulatory
  anchor. No hardcoded LMS / HR endpoint — the operator wires each
  at the compile-target config layer.
- **Depends on:** F-WF-CYBERHYG (the operational per-cycle
  materialisation this programme-lifecycle workflow feeds).
- **Source:** NIS2 (Directive (EU) 2022/2555) Art. 21(2)(g); GDPR
  (Regulation (EU) 2016/679) Art. 32(1)(b); ISO/IEC 27001:2022
  Annex A.6.3.
- **Shipped via:**
  - SKELETON — #767
    (`content/playbooks/security_awareness_training/` CACAO v2
    scaffold + `mappings.yaml` pinning outbound OSCAL AT-2 / AT-3 /
    AT-4 and ISO/IEC 27001 A.6.3 controls, the NIS2 Art. 21(2)(g)
    overlay, and the GDPR Art. 32(1)(b) sibling reference, plus the
    workflow-local README).
  - CORE — no-op retirement: the operational-delivery scope
    (`playbook.cyber_hygiene_training@v1`) already carries the
    per-cohort compile-target examples and byte-parity goldens under
    `examples/{n8n,temporal,langgraph}/cyber_hygiene_training/` and
    `tests/examples/{n8n,temporal,langgraph}/cyber_hygiene_training/`;
    the programme-governance layer and the operational layer share
    the compile ring rather than forking the NIS2 Art. 21(2)(g)
    surface into two synonymous rings.
  - EXTEND — #768
    (`docs/cookbook/security_awareness_training.md` operator
    walkthrough covering programme-governance vs operational-
    delivery scoping, step-by-step CACAO walkthrough with OSCAL /
    NIS2 / GDPR / ISO 27001 mapping, and the wiring contract to the
    per-cohort operational compile examples under
    `cyber_hygiene_training`; ROADMAP F-WF-SECAWARENESS status flip
    from In Progress to Shipped).

---

### F-DORA-ART19 — DORA Art. 19 major-ICT-related incident reporting lifecycle

- **Status:** Shipped
- **Priority:** P1
- **Goal:** G-01 (content coverage — dedicated DORA-flavoured major-
  ICT-related-incident reporting playbook closing the Chapter III
  reporting surface upstream of the existing NIS2 Art. 23-flavoured
  `incident_management` playbook; advances the Q4 2026 target of ≥
  25 CACAO v2 playbooks), G-02 (regulatory-graph closure — DORA
  Art. 19(4)(a)/(b)/(c) and Art. 18(1) primary anchors for the
  three-milestone reporting cycle, with sibling references to NIS2
  Art. 23 and GDPR Art. 33-34 for the cross-regime parallel-
  notification relationship; target Q3 2026 for full DORA-axis
  playbook coverage).
- **Acceptance criteria:**
  - `content/playbooks/dora_major_incident_reporting/` carries the
    canonical CACAO v2 scaffold
    (`playbook.dora_major_incident_reporting@v1`) — the
    detect-and-classify → notify-authority-initial (4h/24h) →
    notify-authority-intermediate (72h) → notify-authority-final
    (one month) → close-and-archive chain, plus `mappings.yaml`
    pinning outbound OSCAL IR-8 / IR-6 / IR-5 controls, an OCSF
    telemetry stub, the DORA Art. 19(4)(a)/(b)/(c) and Art. 18(1)
    overlays, the NIS2 Art. 23(4)(b) cross-regime sibling, and the
    GDPR Art. 33 cross-regime sibling, plus a workflow-local README.
    Read-only against the operator incident register upstream; each
    notification step writes a submission-intent record and captures
    the competent-authority acknowledgement.
  - Three reference-target compile examples land under
    `examples/{n8n,temporal,langgraph}/dora_major_incident_reporting/`
    with byte-parity goldens under
    `tests/examples/{n8n,temporal,langgraph}/dora_major_incident_reporting/test_golden.py`
    guarding the ring across all three targets on every PR.
- **Sovereign-stack constraints:** CACAO v2 content only, no
  proprietary schema. DORA Art. 19 is the primary regulatory
  anchor; content shape follows Commission Implementing Regulation
  (EU) 2024/2956 (ITS). No hardcoded competent-authority endpoint
  — the operator wires the ESA / NCA channel at the compile-target
  config layer. Distinct from the NIS2 Art. 23-flavoured
  `incident_management` lane; the two are cross-regime siblings
  that run in parallel on the same underlying incident against
  different authority chains.
- **Depends on:** F-WF-INCIDENT-MANAGEMENT (the NIS2-flavoured
  sibling this DORA-flavoured lane cross-references), and the
  existing `content.dora_major_classifier@v1` deterministic
  Art. 18 classifier primitive.
- **Source:** DORA (Regulation (EU) 2022/2554) Art. 18-19;
  Commission Delegated Regulation (EU) 2024/1772 (RTS on
  incident classification); Commission Implementing Regulation
  (EU) 2024/2956 (ITS on incident-reporting templates); NIS2
  (Directive (EU) 2022/2555) Art. 23; GDPR (Regulation (EU)
  2016/679) Art. 33-34.
- **Shipped via:**
  - SKELETON — #769
    (`content/playbooks/dora_major_incident_reporting/` CACAO v2
    scaffold + `mappings.yaml` pinning outbound OSCAL IR-8 / IR-6
    / IR-5 controls, the DORA Art. 19 and Art. 18 overlays, the
    NIS2 Art. 23 and GDPR Art. 33 cross-regime sibling anchors,
    plus the workflow-local README).
  - CORE — #770
    (`examples/{n8n,temporal,langgraph}/dora_major_incident_reporting/`
    three-target compile examples plus byte-parity goldens under
    `tests/examples/{n8n,temporal,langgraph}/dora_major_incident_reporting/`
    guarding the per-milestone submission ring across all three
    targets on every PR).
  - EXTEND — PR #771
    (`docs/cookbook/dora_major_incident_reporting.md` operator
    walkthrough covering the Art. 18 classification gate and the
    Art. 19 three-milestone reporting cycle with the three-target
    hand-off and the cross-target `artifact_id` invariant; cookbook
    index entry; ROADMAP F-DORA-ART19 status flip from In Progress
    to Shipped).

---

### F-WF-NETWORK-SECURITY — Network-boundary and segmentation posture reconciliation lifecycle

- **Status:** Shipped
- **Priority:** P1
- **Goal:** G-01 (content coverage — portable operator-side per-window
  reconciliation playbook for the network-boundary / segmentation limb
  of NIS2 Art. 21(2)(e); co-anchored with the existing vulnerability-
  handling and codebase dependency-review limbs of the same clause;
  advances the Q4 2026 target of ≥ 25 CACAO v2 playbooks), G-02
  (regulatory-graph closure — NIS2 Art. 21(2)(e) network-boundary
  primary anchor and DORA Art. 9 network-security sibling closure,
  target Q3 2026 for full NIS2 / DORA network-layer axis coverage),
  G-03 (compile-target parity — byte-parity goldens across the three
  reference targets pinning the reconciliation ring on every PR).
- **Acceptance criteria:**
  - `content/playbooks/network_security/` carries the canonical
    CACAO v2 scaffold (`playbook.network_security@v1`) — the
    inventory-network-segments → evaluate-segmentation-policy →
    detect-policy-violations → enforce-remediation →
    generate-posture-evidence-artifact chain, plus `mappings.yaml`
    pinning outbound OSCAL SC-7 / SC-3 / CA-9 controls, a D3FEND
    D3-NTA + D3-ISVA binding on the detect step (per-step gap notes
    on the other four), an OCSF Network Activity (4001) telemetry
    stub, the NIS2 Art. 21(2)(e) network-boundary overlay, the DORA
    Art. 9 sibling reference, and the CRA / GDPR orphan-skip
    entries (asset_management precedent), plus a workflow-local
    README. Read-only against the operator's declared inventory
    and policy sources; the remediation step dispatches against
    pre-bound operator remediation surfaces (ACL / firewall-rule
    change, boundary-control posture-change ticket, or short-circuit
    isolation).
  - Three reference-target compile examples land under
    `examples/{n8n,temporal,langgraph}/network_security/` with
    byte-parity goldens under
    `tests/examples/{n8n,temporal,langgraph}/network_security/test_golden.py`
    guarding the ring across all three targets on every PR.
  - Cookbook entry `docs/cookbook/network_security.md` walks an
    operator through the reconciliation cycle end-to-end against a
    compiled example (n8n / Temporal / LangGraph).
- **Sovereign-stack constraints:** CACAO v2 content only, no
  proprietary schema. NIS2 Art. 21(2)(e) is the primary regulatory
  anchor; DORA Art. 9 is the financial-sector sibling. No hardcoded
  IaC / cloud-provider / flow-log / ticketing endpoint — the operator
  wires each adapter surface at the compile-target config layer. The
  reconciliation operates on segment identifiers, policy-snapshot
  identifiers, and evidence-record identifiers only; no personal data
  is processed.
- **Depends on:** `control.network_boundary_protection@v1`
  placeholder control (SC-7 / SC-3 / CA-9 catalog rows resolve via
  the mappings overlay).
- **Source:** NIS2 (Directive (EU) 2022/2555) Art. 21(2)(e); DORA
  (Regulation (EU) 2022/2554) Art. 9; Commission Delegated
  Regulation (EU) 2024/1774 (JC RTS on ICT risk management
  framework) Art. 12; NIST SP 800-53 Rev. 5 SC-7 / SC-3 / CA-9;
  OCSF v1.3.0 Network Activity (4001); MITRE D3FEND D3-NTA /
  D3-ISVA.
- **Shipped via:**
  - SKELETON — #798
    (`content/playbooks/network_security/` CACAO v2 five-step
    scaffold + `mappings.yaml` pinning outbound OSCAL SC-7 / SC-3 /
    CA-9 controls, the NIS2 Art. 21(2)(e) network-boundary overlay,
    the DORA Art. 9 sibling reference, and the CRA / GDPR
    orphan-skip entries, plus the workflow-local README).
  - CORE — #799
    (deterministic per-step action bodies plus three-target
    compile examples under
    `examples/{n8n,temporal,langgraph}/network_security/` closing
    the CACAO source → n8n / Temporal / LangGraph emission ring).
  - MAPPINGS-INBOUND — #800
    (`content/mappings/{nis2,dora,cra,gdpr}/` inbound wires —
    NIS2 Art. 21(2)(e) network-boundary limb, DORA Art. 9
    network-security atom, CRA orphan-skip clause-by-clause review,
    GDPR no-personal-data data-flow doc — closing the four-regime
    inbound-lane coverage for `playbook.network_security@v1`).
  - EXTEND-GOLDENS — #801
    (`tests/examples/{n8n,temporal,langgraph}/network_security/test_golden.py`
    byte-parity goldens guarding the reconciliation ring across
    all three targets on every PR).
  - EXTEND-COOKBOOK — PR #802
    (`docs/cookbook/network_security.md` operator walkthrough
    covering the five-step reconciliation cycle, the three-target
    hand-off, the OSCAL SC-7 / SC-3 anchors, the D3-NTA detect-step
    binding, the OCSF Network Activity 4001 emission surface, and
    the operator-wired adapter contract; cookbook index entry;
    ROADMAP F-WF-NETWORK-SECURITY status flip from In Progress to
    Shipped).

### F-WF-EUAIACT-DEPLOYER — EU AI Act Art. 26 deployer-obligation lifecycle with Art. 27 fundamental-rights impact assessment

- **Status:** Shipped
- **Priority:** P1
- **Goal:** G-01 (content coverage — the shipped EU AI Act surface is
  provider-side end to end; an operator running a third-party high-risk
  AI system in production is a *deployer*, and that population currently
  has no portable playbook), G-02 (regulatory-graph closure — Art. 26
  and Art. 27 are unmapped, the largest remaining gap on the EU AI Act
  axis alongside the GPAI chapter), G-05 (sovereignty — deployer-side
  monitoring and logging must be discharged on EU-resident surfaces).
- **Acceptance criteria:**
  - `content/mappings/eu_ai_act/article-26-deployer-obligations.yaml`
    carries the Art. 26 atoms: use in accordance with the instructions
    for use (26(1)), assignment of competent human oversight (26(2)),
    input-data relevance where the deployer controls it (26(4)),
    monitoring plus suspension-and-notification on a risk indication
    (26(5)), retention of automatically generated logs (26(6)),
    worker-representative information duty (26(7)), and the
    Art. 26(5) provider/authority notification edge that hands off to
    the shipped `eu_ai_act:art-73-serious-incident-reporting` entry.
  - `content/mappings/eu_ai_act/article-27-fria.yaml` carries the
    Art. 27(1)(a)–(f) fundamental-rights-impact-assessment elements and
    the Art. 27(4) notification of the market-surveillance authority,
    with the DPIA relationship recorded (Art. 27(4) allows the FRIA to
    complement an existing GDPR Art. 35 DPIA rather than duplicate it —
    the cross-reference must name `playbook.data_protection_impact_assessment@v1`).
  - `content/playbooks/eu_ai_act_deployer_obligations/` ships the
    canonical CACAO v2 scaffold: confirm-intended-use →
    assign-human-oversight → monitor-operation →
    assess-fundamental-rights-impact → retain-logs-and-evidence, with
    `mappings.yaml` pinning outbound OSCAL, D3FEND (D3-OAM on the
    evidence-retention step per the committed record-composition
    precedent), and an OCSF binding, plus a workflow-local README.
  - Three-target compile examples and byte-parity goldens (G-03), and a
    cookbook walkthrough indexed in `docs/cookbook/README.md`.
- **Sovereign-stack constraints:** the Art. 26(6) log-retention surface
  is operator-owned and must remain adapter-bound — the framework
  declares the retention contract and never ships a log store. No
  non-EU default endpoint may participate in the monitoring or
  notification chain.
- **Depends on:** F-WF-DPIA (Shipped — the FRIA entry cross-references
  the DPIA lifecycle rather than restating it).
- **Source:** EU AI Act (Regulation (EU) 2024/1689) Art. 26, Art. 27;
  `content/mappings/eu_ai_act/README.md` scope note (deployer track
  recorded as a sibling card).

### F-WF-AI-OVERSIGHT — EU AI Act Art. 14 human-oversight design and operation lifecycle

- **Status:** Shipped
- **Priority:** P2
- **Goal:** G-01 (content coverage — Art. 14 is a standing high-risk
  requirement with no playbook; the oversight measures it demands are
  operational, not documentary, and therefore compile), G-02
  (regulatory-graph closure — Art. 14 is unmapped and is the named
  dependency of the Art. 26(2) deployer oversight-assignment atom).
- **Acceptance criteria:**
  - `content/mappings/eu_ai_act/article-14-human-oversight.yaml`
    carries the Art. 14(1)–(5) atoms: oversight-by-design measures
    built into the system, measures identified for the deployer to
    implement, the Art. 14(4)(a)–(e) oversight capability set
    (understand capacity and limits, remain aware of automation bias,
    correctly interpret output, decide not to use or to disregard,
    intervene or halt), and the Art. 14(5) biometric two-person
    verification rule.
  - `content/playbooks/ai_human_oversight/` ships the CACAO v2 scaffold
    covering the operational loop an oversight function actually runs:
    establish-oversight-roster → brief-oversight-personnel →
    review-flagged-decisions → record-intervention →
    emit-oversight-evidence, with `mappings.yaml` and a
    workflow-local README.
  - A KPI/KRI pair under `content/metrics/` measuring the oversight
    loop (intervention rate and time-to-intervention on flagged
    decisions) with committed reference visualisations (G-04).
  - Three-target compile examples with byte-parity goldens (G-03) and a
    cookbook walkthrough.
- **Sovereign-stack constraints:** the oversight roster and the
  decision-review queue are operator-owned adapter-bound surfaces; the
  framework describes the contract and ships no personnel directory.
- **Depends on:** F-WF-EUAIACT-DEPLOYER (the Art. 26(2)
  oversight-assignment step hands off to this lifecycle).
- **Source:** EU AI Act (Regulation (EU) 2024/1689) Art. 14.

### F-WF-AGENTIC-RESPONSE — Fully-agentic adversary response

- **Status:** In Progress
- **Priority:** P2
- **Rationale:** Covers autonomous LLM-driven credential harvest, lateral
  movement and encryption chains — an attacker capability the rest of the
  catalogue assumes is human-paced.
- **Acceptance criteria:**
  - CACAO v2 artifact with `mappings.yaml` and a workflow-local README
    (SKELETON — shipped).
  - Three-target compile examples with byte-parity goldens (G-03) and a
    cookbook walkthrough (shipped).
  - Deterministic primitives under
    `content/playbooks/agentic_threat_response/primitives/` bound to the 5
    action steps, replay-safe and offline (CORE — **outstanding**).
  - Detection reads the agentic-activity signals the operator's telemetry
    already carries; the playbook mints no new sensor.
  - The five KPI/KRI entries already under `content/metrics/` for this
    surface (detection rate, false-positive rate, model-decision latency)
    keep their committed reference visualisations.
- **Sovereign-stack constraints:** The agentic-activity classifier is an
  adapter-bound operator surface; the framework ships the contract, not a
  model.
- **Depends on:** F-WF-03 (alert triage supplies the enriched signal)
- **Source:** FOUNDATION (operability); NIS2 Art. 21(2)(b); issue #890.
- **Shipped via:**
  - SKELETON — #678, #679, #680, #681
  - EXTEND — #747 (cookbook + metric set)

### F-WF-BACKUP-RECOVERY — Backup integrity and restore-drill lifecycle

- **Status:** In Progress
- **Priority:** P2
- **Rationale:** NIS2 Art. 21(2)(c) requires backup management and disaster
  recovery; an untested backup is an assertion, so the workflow is built
  around a non-destructive restore drill rather than a backup-exists check.
- **Acceptance criteria:**
  - CACAO v2 artifact with `mappings.yaml` and a workflow-local README
    (SKELETON — shipped).
  - Three-target compile examples with byte-parity goldens (G-03) and a
    cookbook walkthrough (shipped).
  - Deterministic primitives under
    `content/playbooks/backup_recovery/primitives/` bound to the 5 action
    steps, replay-safe and offline (CORE — shipped).
  - The restore drill is non-destructive by construction — no step writes to
    a production target.
  - The five metric entries for this surface keep their reference
    visualisations, including the integrity pass rate.
- **Sovereign-stack constraints:** The backup estate and the restore target
  are operator-owned; the framework ships no storage binding and no default
  endpoint.
- **Depends on:** F-WF-BCM (the continuity lifecycle this drill reports
  into)
- **Source:** FOUNDATION (operability); NIS2 Art. 21(2)(c); DORA Art. 12;
  issue #890.
- **Shipped via:**
  - SKELETON — #478, #483
  - CORE — #938 (five pure primitives with direct unit coverage, all 5
    action steps bound, the `__integrity_ok__` predicate filled, three
    worked examples refreshed onto the canonical core_body goldens).

### F-WF-BCM — Business-continuity event lifecycle

- **Status:** In Progress
- **Priority:** P2
- **Rationale:** The operator-side continuity lifecycle a NIS2 essential or
  important entity runs on a major outage, ransomware containment or
  supplier failure. Emits one milestone record per lifecycle stage.
- **Acceptance criteria:**
  - CACAO v2 artifact with `mappings.yaml` and a workflow-local README
    (SKELETON — shipped).
  - Three-target compile examples with byte-parity goldens (G-03) and a
    cookbook walkthrough (shipped).
  - Deterministic primitives under
    `content/playbooks/business_continuity/primitives/` bound to the 7
    action steps, replay-safe and offline (CORE — **outstanding**).
  - Each lifecycle milestone emits an `api_activity` record keyed to the
    event id — the house binding for workflow-emitted milestones, corrected
    from an invented availability class by #877.
  - Declaring an event does not require the operator to have pre-registered
    a plan; a continuity event with no plan on file is reported as such
    rather than blocking.
- **Sovereign-stack constraints:** The continuity plan register and the
  recovery targets are operator-owned adapter-bound surfaces.
- **Depends on:** F-WF-05 (incident management hands major incidents into
  this lifecycle)
- **Source:** FOUNDATION (operability); NIS2 Art. 21(2)(c); DORA Art. 11;
  issue #890.
- **Shipped via:**
  - SKELETON — #707

### F-WF-CRYPTO-POSTURE — Cryptography and encryption posture management

- **Status:** Shipped
- **Priority:** P2
- **Rationale:** NIS2 Art. 21(2)(h) names cryptography and, where
  appropriate, encryption. This is the posture-observation half: inventory
  the declared policy and the assets in its scope, then probe the
  certificate and cipher surface against it.
- **Acceptance criteria:**
  - CACAO v2 artifact with `mappings.yaml` and a workflow-local README
    (SKELETON — shipped).
  - Three-target compile examples with byte-parity goldens (G-03) and a
    cookbook walkthrough (shipped).
  - Deterministic primitives under
    `content/playbooks/crypto_posture_management/primitives/` bound to the 5
    action steps, replay-safe and offline (CORE — shipped, #907).
  - Probing is read-only: no step rotates a key, reissues a certificate or
    changes a cipher suite (shipped, #907).
  - A probe finding names the declared policy clause it contradicts, so a
    reviewer can tell a policy gap from a drift (shipped, #907 — and the
    EXTEND metric pair preserves the distinction on the counted findings).
- **Sovereign-stack constraints:** Certificate and key material never enters
  an emitted artifact — findings carry references and observed parameters
  only.
- **Depends on:** F-WF-CRYPTO-CONTROLS (the controls lifecycle this posture
  feeds)
- **Source:** FOUNDATION (auditability); NIS2 Art. 21(2)(h); issue #890.
- **Shipped via:**
  - SKELETON — #479, #482
  - CORE — #907 (five primitives, drift vs policy gap)
  - EXTEND — #925, closing #924 (kri.expiring_tls_certs@v1 and
    kri.overdue_key_rotations@v1 with committed reference
    visualisations, metric_refs wired both ways)

### F-WF-CRYPTO-CONTROLS — Cryptographic-controls lifecycle

- **Status:** In Progress
- **Priority:** P2
- **Rationale:** The controls half of the Art. 21(2)(h) surface: the
  operator-side lifecycle run against a documented cryptography policy,
  covering the lifecycle disciplines the policy is expected to state.
- **Acceptance criteria:**
  - CACAO v2 artifact with `mappings.yaml` and a workflow-local README
    (SKELETON — shipped).
  - Three-target compile examples with byte-parity goldens (G-03) and a
    cookbook walkthrough (shipped).
  - Deterministic primitives under
    `content/playbooks/cryptographic_controls/primitives/` bound to the 6
    action steps, replay-safe and offline (CORE — **outstanding**).
  - The policy is input, not content: the playbook scores against the
    operator's documented policy and ships no default cipher baseline.
  - A control with no documented policy clause behind it is reported as
    undocumented rather than as compliant.
- **Sovereign-stack constraints:** No key material, no default policy
  baseline — a shipped baseline would become a de-facto standard the
  framework has no authority to set.
- **Depends on:** F-WF-CRYPTO-POSTURE (supplies the observed posture)
- **Source:** FOUNDATION (auditability); NIS2 Art. 21(2)(h); GDPR Art.
  32(1)(a); issue #890.
- **Shipped via:**
  - SKELETON — #711, #712, #713
  - EXTEND — #726 (cookbook)

### F-WF-DSR — GDPR Chapter III data-subject-rights lifecycle

- **Status:** In Progress
- **Priority:** P2
- **Rationale:** The controller-side intake and fulfilment lifecycle for a
  data subject exercising a Chapter III right. The one-month Art. 12(3)
  clock makes the timing contract, not the request form, the hard part.
- **Acceptance criteria:**
  - CACAO v2 artifact with `mappings.yaml` and a workflow-local README
    (SKELETON — shipped).
  - Three-target compile examples with byte-parity goldens (G-03) and a
    cookbook walkthrough (shipped).
  - Deterministic primitives under
    `content/playbooks/data_subject_rights/primitives/` bound to the 7
    action steps, replay-safe and offline (CORE — **outstanding**).
  - The Art. 12(3) one-month response clock is anchored on a supplied
    awareness instant, never on a clock read inside a primitive, so a run is
    replayable and the deadline is auditable.
  - An extension under Art. 12(3) is recorded with its justification; an
    unjustified extension is not representable.
- **Sovereign-stack constraints:** Subject-supplied attributes are not
  stored by the workflow — identity is resolved against the controller's own
  records at runtime.
- **Depends on:** F-WF-DPIA (shares the GDPR lawful-basis mapping surface)
- **Source:** FOUNDATION (auditability); GDPR Arts. 12, 15–22; issue #890.
- **Shipped via:**
  - SKELETON — #621

### F-WF-DDOS — Availability-attack detection and response

- **Status:** In Progress
- **Priority:** P2
- **Rationale:** The availability dimension of the incident-handling
  capability: confirm an availability anomaly is an attack rather than
  organic load, classify the vector, and verify service restoration.
- **Acceptance criteria:**
  - CACAO v2 artifact with `mappings.yaml` and a workflow-local README
    (SKELETON — shipped).
  - Three-target compile examples with byte-parity goldens (G-03) and a
    cookbook walkthrough (shipped).
  - Deterministic primitives under
    `content/playbooks/ddos_response/primitives/` bound to the 6 action
    steps, replay-safe and offline (CORE — **outstanding**).
  - Classification distinguishes volumetric from connection-rate and
    application-layer vectors, because the mitigation differs and an
    aggregate 'under attack' verdict is not actionable.
  - Restoration is verified against observed traffic, not asserted on
    mitigation being applied.
- **Sovereign-stack constraints:** Mitigation is an adapter-bound operator
  surface; the framework describes the hand-off and ships no
  scrubbing-provider binding.
- **Depends on:** F-WF-05 (incident management owns the declared-incident
  path)
- **Source:** FOUNDATION (operability); NIS2 Art. 21(2)(b); issue #890.
- **Shipped via:**
  - SKELETON — #501, #505
  - EXTEND — #606 (cookbook)

### F-WF-DORA-TLPT — DORA Chapter IV resilience-testing programme

- **Status:** Shipped
- **Priority:** P2
- **Rationale:** The digital operational resilience testing programme a
  financial entity operates against its ICT risk-management framework,
  including threat-led penetration testing where in scope.
- **Acceptance criteria:**
  - CACAO v2 artifact with `mappings.yaml` and a workflow-local README
    (SKELETON — shipped).
  - Three-target compile examples with byte-parity goldens (G-03) and a
    cookbook walkthrough (shipped).
  - Deterministic primitives under
    `content/playbooks/dora_tlpt_programme/primitives/` bound to the 4
    action steps, replay-safe and offline (CORE — shipped, #904).
  - The programme composes existing testing evidence rather than executing
    tests — the framework does not run penetration tests (shipped, #904).
  - Scope determination is explicit: an entity out of TLPT scope produces a
    programme record saying so, rather than an empty one (shipped, #904 —
    and the EXTEND coverage KPI measures out-of-scope entities against the
    Art. 24 cadence only).
- **Sovereign-stack constraints:** Test findings stay in the operator's own
  store; the emitted record carries references, never finding bodies.
- **Depends on:** F-WF-DORA-SELFASSESS (the ICT risk-management framework
  this tests against)
- **Source:** FOUNDATION (auditability); DORA Arts. 24–27; issue #890.
- **Shipped via:**
  - SKELETON — #714, #715, #716
  - CORE — #904 (four DORA Ch. IV primitives, tier B → A)
  - EXTEND — #927, closing #926
    (kpi.dora_resilience_test_coverage@v1 paired with
    kri.tlpt_remediation_overdue@v1, metric_refs wired both ways,
    stale TODO(CORE) description lead-ins stripped)

### F-WF-EIDAS2-IDV — EU Digital Identity Wallet verification lifecycle

- **Status:** In Progress
- **Priority:** P2
- **Rationale:** The operator-side lifecycle for onboarding an EUDIW-enabled
  principal: consume a wallet attestation, verify it, and bind the verified
  identity to an account without retaining more than the verification
  outcome.
- **Acceptance criteria:**
  - CACAO v2 artifact with `mappings.yaml` and a workflow-local README
    (SKELETON — shipped).
  - Three-target compile examples with byte-parity goldens (G-03) and a
    cookbook walkthrough (shipped).
  - Deterministic primitives under
    `content/playbooks/eidas2_identity_verification/primitives/` bound to
    the 5 action steps, replay-safe and offline (CORE — **outstanding**).
  - Verification consumes the attestation and retains the outcome plus its
    provenance — not the attested attributes themselves.
  - A failed or expired attestation produces an explicit refusal outcome;
    there is no partial-trust state.
- **Sovereign-stack constraints:** Uses Regulation (EU) 2024/1183 reference
  schemas only, consistent with F-SV-02, and stores no wallet attribute
  payload.
- **Depends on:** F-SV-02 (the wallet-attestation typed-input pattern)
- **Source:** FOUNDATION (sovereignty); Regulation (EU) 2024/1183; issue
  #890.
- **Shipped via:**
  - SKELETON — #759, #761

### F-WF-EUAIACT-RISKMGMT — EU AI Act Art. 9 risk-management system

- **Status:** Shipped
- **Priority:** P2
- **Rationale:** The risk-management system Art. 9 requires providers of
  high-risk AI systems to establish, implement, document and maintain across
  the lifecycle — the provider-side counterpart to the shipped deployer and
  human-oversight lifecycles.
- **Acceptance criteria:**
  - CACAO v2 artifact with `mappings.yaml` and a workflow-local README
    (SKELETON — shipped).
  - Three-target compile examples with byte-parity goldens (G-03) and a
    cookbook walkthrough (shipped).
  - Deterministic primitives under
    `content/playbooks/eu_ai_act_risk_management/primitives/` bound to the 4
    action steps, replay-safe and offline.
  - The system is documented as a continuous lifecycle, not a one-off
    assessment, per Art. 9(2)'s iterative requirement.
  - Residual risk is recorded per identified risk rather than aggregated, so
    an Art. 9(5) judgement is traceable to the risk it was made about.
- **Sovereign-stack constraints:** No default risk taxonomy — the operator's
  own taxonomy is input, and a shipped one would become a de-facto standard.
- **Depends on:** F-WF-EUAIACT-DEPLOYER (the deployer-side lifecycle this
  pairs with)
- **Source:** FOUNDATION (auditability); EU AI Act (Regulation (EU)
  2024/1689) Art. 9; issue #890.
- **Shipped via:**
  - SKELETON — #682, #683, #684, #685
  - EXTEND — #687, #806, #807 (cookbook, mappings, metric pair)
  - CORE — #903 (four Art. 9 primitives bound to the four action steps;
    tier B -> A). Landed after EXTEND because the two axes ran separately:
    the mappings / telemetry / metrics overlay reached EXTEND at content
    version 0.3.0 while the steps still carried no `core_body`.

### F-WF-MFA-COMMS — MFA and secured-communications posture

- **Status:** Shipped
- **Priority:** P2
- **Acceptance criteria:**
  - `content/playbooks/mfa_secured_comms/` carries the CACAO playbook,
    `mappings.yaml`, primitives and a workflow-local README; compiled
    targets land under `examples/{n8n,temporal,langgraph}/mfa_secured_comms/`.
  - Probes the identity-provider surface to confirm enforcement rather than
    reading declared configuration.
  - Four deterministic primitives bind the action steps; three-target
    compile examples carry byte-parity goldens.
  - A cookbook walkthrough and a KPI entry under `content/metrics/` ship
    with it.
- **Sovereign-stack constraints:** The identity provider and the
  secured-communications surface are operator-owned; no credential enters an
  emitted artifact.
- **Depends on:** F-WF-08 (IAM auditor supplies the identity inventory)
- **Source:** FOUNDATION (auditability); NIS2 Art. 21(2)(j); DORA Art.
  9(4)(b); issue #890.
- **Shipped via:**
  - SKELETON — #480, #484
  - CORE — #577
  - EXTEND — #604 (cookbook + metric)

### F-WF-SOC2-EVIDENCE — SOC 2 readiness evidence collection

- **Status:** Shipped
- **Priority:** P1
- **Acceptance criteria:**
  - `content/playbooks/soc2_evidence_collector/` carries the CACAO playbook,
    `mappings.yaml`, four primitives and a workflow-local README; compiled
    targets land under
    `examples/{n8n,temporal,langgraph}/soc2_evidence_collector/`.
  - Aggregates evidence other playbooks already emit; collects no new
    telemetry, so a criterion without evidence reports as uncovered rather
    than triggering a scan.
  - Coverage is three-valued (`covered` / `draft_backed` / `uncovered`) and
    never a percentage — a ratio invites "N% SOC 2 compliant", which is not
    a defensible claim.
  - Emits no audit opinion: the document carries an explicit disclaimer and
    a `soc2_readiness_input` document kind.
  - Four deterministic primitives, three-target byte-parity examples, a
    cookbook walkthrough and a KPI/KRI pair under `content/metrics/`.
- **Sovereign-stack constraints:** The criteria set is runtime input, so the
  playbook cannot claim coverage of a criterion the repo does not carry. No
  attestation sink ships — where the document lands is a deployment
  decision.
- **Depends on:** F-CP-07 (access stream), F-WF-08, F-WF-11 (evidence
  producers)
- **Source:** FOUNDATION (auditability); AICPA Trust Services Criteria
  (2017, as revised); issue #890.
- **Shipped via:**
  - SKELETON + CORE — #884
  - EXTEND — #893 (cookbook + metric pair)

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
manual configuration, and the artifacts that let an operator
*demonstrate* the resulting posture rather than assert it.

The first three features landed the defaults. What followed them was
measurement: the catalogue now carries 21 sovereignty-tagged indicators
(15 KPIs, 6 KRIs) under `content/metrics/`. What it does not carry is any
way to turn an observation of those indicators into a dated, validated
artifact — sovereignty is the only FOUNDATION property with no evidence
stream, while the F-CP epic shipped seven for other surfaces. F-SV-04
through F-SV-06 close that, in that order: emit the evidence, declare
what the evidence has to show, then stop coverage indicators from
shipping without their residual-risk counterpart.

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

- **Status:** Shipped
- **Priority:** P2
- **Acceptance criteria:**
  - Pattern (under `patterns/eidas2_wallet/`) shows how to consume an
    EU Digital Identity Wallet attestation as a Pydantic-typed
    workflow input.
- **Sovereign-stack constraints:** Uses Regulation (EU) 2024/1183
  reference schemas only.
- **Depends on:** F-PT-03
- **Source:** Research `2026-05-16-eidas2-wallet-patterns.md` (private; available on request).
- **Shipped via:**
  - SKELETON — #377 (`patterns/eidas2_wallet/` Pydantic v2
    `WalletAttestationInput` typed-input model + cross-target fixture
    under `tests/fixtures/eidas2_wallet/` anchoring the byte-parity
    ring).
  - CORE-FANOUT-N8N — #378 (n8n credentials-node adapter under
    `compilers/n8n/patterns/eidas2_wallet_node.py` + worked example
    under `examples/n8n/eidas2_wallet/` + byte-parity golden).
  - CORE-FANOUT-TEMPORAL — #379 (Temporal `@activity.defn`
    `materialise_wallet_attestation_input_activity` under
    `compilers/temporal/patterns/eidas2_wallet_activity.py` + worked
    example under `examples/temporal/eidas2_wallet/` + cross-target
    byte-parity golden).
  - CORE-FANOUT-LANGGRAPH — #380 (LangGraph state→state node
    `materialise_wallet_attestation_input_node` under
    `compilers/langgraph/patterns/eidas2_wallet_node.py` + worked
    example under `examples/langgraph/eidas2_wallet/` closing the
    three-target byte-parity ring; input_id
    `50e1470262066f3c3e13f8e3bb966b3abf4798fc8cf22aed334e55c105f289dd`).

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

### F-SV-04 — Sovereignty posture evidence stream

- **Status:** Shipped
- **Shipped:** SKELETON (stream layout, artifact schema with the
  21-indicator completeness contract and `$ref`'d attestation
  vocabulary, twelve validation pins — #898); CORE (shared emitter +
  n8n / Temporal / LangGraph adapters, byte-parity worked examples on
  `infra_posture_management`, three-way emitter↔schema↔catalogue
  lockstep pins — #909, closing #899).
- **Priority:** P1
- **Rationale:** The catalogue measures the sovereign posture from 21
  angles but emits nothing. Ten evidence streams exist under
  `content/evidence/` and fifteen schemas under `schemas/evidence/`;
  none is sovereignty. An operator can therefore observe that they are
  EU-resident but cannot hand a reviewer a dated artifact saying so,
  which is the difference between claiming the property and evidencing
  it.
- **Acceptance criteria:**
  - `content/evidence/sovereignty/` ships with `README.md` and
    `SCHEMA.md` in the same layout as the seven F-CP streams.
  - `schemas/evidence/sovereignty.schema.json` validates a record
    carrying the assessment window, one observation per
    sovereignty-cluster indicator (`stable_id`, observed value, the
    threshold band it fell in) and an attestation state drawn from
    `schemas/attestation_state.json`.
  - The four-state vocabulary is *reused* from
    `schemas/attestation_state.json`, not redeclared — a test fails if
    the stream introduces a parallel state set.
  - A record omitting any sovereignty-cluster KPI fails validation, so
    the stream cannot silently under-report the posture it attests to.
  - All three compile targets emit a record that validates, and the
    committed examples regenerate byte-identically.
  - No numeric aggregate: the record carries per-indicator observations
    and never a single sovereignty score. A ratio invites "N% sovereign",
    which is not a defensible claim — the same reasoning that keeps a
    percentage out of the SOC 2 readiness attestation.
- **Sovereign-stack constraints:** No default sink and no network call —
  the stream is composed from observations the operator supplies. The
  emitted artifact carries no endpoint literal, so it cannot itself
  become a non-EU reference that
  `kri.hardcoded_non_eu_endpoint_reference_count@v1` would count.
- **Depends on:** F-CP-01
- **Source:** FOUNDATION (sovereignty); the sovereignty cluster under
  `content/metrics/`; issue #890.

### F-SV-05 — Declared sovereignty conformance profile

- **Status:** Shipped
- **Shipped:** single card (#915, closing #914) — the 26-indicator
  baseline at `content/profiles/sovereignty_conformance.yaml` with a
  per-indicator band and rationale, its schema, the all-HARD
  force-a-classification linter (`tools.lint_sovereignty_profile`),
  and the deterministic pure evaluator
  (`tools.evaluate_sovereignty_conformance` over
  `compilers._shared.evidence.sovereignty_profile`) with the
  tighten-freely / loosen-only-on-record override contract.
- **Priority:** P1
- **Rationale:** Twenty-one indicators each carry their own thresholds,
  but nothing declares *which* of them, at which bands, constitute the
  sovereign posture. Two deployments can both claim sovereignty on
  entirely different evidence, and neither is wrong, because there is no
  baseline to be wrong about.
- **Acceptance criteria:**
  - A profile artifact names the required indicator set and the band
    each indicator must meet for the posture to hold.
  - The profile is data, not code: a sovereignty-tagged metric added to
    the catalogue surfaces as unclassified rather than being silently
    excluded from the posture.
  - A linter fails when a sovereignty-tagged metric is absent from the
    profile, naming the metric and the file to edit — the same
    force-a-classification shape as the playbook family map.
  - An F-SV-04 evidence record can be evaluated against the profile
    deterministically: same record plus same profile yields the same
    verdict, with no clock read and no network access.
  - The verdict is per-indicator with a pass/fail roll-up, never a score.
  - Tightening a band in an operator's own profile is supported;
    loosening one below the declared baseline requires an explicit
    recorded override, so a relaxation is visible rather than inferred.
- **Sovereign-stack constraints:** Portable content only — the profile
  ships as an artifact the three targets read, not as runtime code.
- **Depends on:** F-SV-04
- **Source:** FOUNDATION (sovereignty); issue #890.

### F-SV-06 — Generalise the coverage/exposure pairing invariant

- **Status:** Shipped
- **Shipped:** stage 1 (`residual_risk_refs` field, generalised
  pairing lint, two existing pairings declared — #901); stage 2 (the
  five missing residual-risk KRIs with committed reference
  visualisations, `coverage_kpi_without_residual_risk` promoted to
  HARD, ceiling deleted — #910, closing #902).
- **Priority:** P2
- **Rationale:** The sovereignty pairing lint exists because an
  LM-endpoint coverage KPI cannot distinguish an
  operator-supplied or self-hosted endpoint from a confirmed non-EU one,
  so it must ship with a paired UNKNOWN-exposure KRI to stay honest. That
  reasoning is not specific to LM endpoints, but the lint is: the cluster
  holds 15 KPIs against 6 KRIs, so most coverage indicators carry no
  declared residual-risk counterpart at all.
- **Acceptance criteria:**
  - The pairing assertion applies to every sovereignty-cluster coverage
    KPI, not only the `lm_endpoint_*` family.
  - Each such KPI declares its counterpart **explicitly** rather than by
    name convention, so the pairing survives a rename on either side.
  - A coverage KPI with no declared counterpart fails the lint, with the
    KPI's `stable_id` in the message.
  - The existing LM-endpoint case is covered by the generalised rule and
    the bespoke linter is retired, not left in place as a second source
    of truth.
  - The CI lane keeps its current job name so branch protection is
    unaffected by the change.
- **Sovereign-stack constraints:** —
- **Depends on:** —
- **Source:** FOUNDATION (sovereignty);
  `tools/lint_sovereignty_pairing.py`; issue #890.

---

## Epic MET — Regulator-notification latency catalogue

Residual-risk (KRI) catalogue entries measuring statutory
incident-notification latency across the EU regulatory regimes.
Each feature ships a triad of KRIs — one per statutory clock — with
committed reference visualisations, OCSF Compliance Finding source-data
bindings, and warn / high / breach threshold bands calibrated against
the regulatory deadline.

### F-MET-CRA-LATENCY — CRA Art. 14 SRP dispatch-latency KRI triad

- **Status:** Shipped
- **Priority:** P1
- **Goal:** G-04 (KPI/KRI catalogue maturity — residual-risk latency
  coverage across every regulator-notification gate the framework
  targets).
- **Acceptance criteria:**
  - `content/metrics/` carries three KRI catalog entries covering the
    CRA Art. 14 timer cascade for the Single Reporting Platform (SRP)
    dispatch chain:
    - `kri.cra_early_warning_latency_hours@v1` — 24h clock (Art. 14(1)).
    - `kri.cra_full_notification_latency_hours@v1` — 72h clock
      (Art. 14(2)).
    - `kri.cra_final_report_latency_days@v1` — 14d / 30d clock
      (Art. 14(2)–(3) actively-exploited / severe-incident).
  - Each entry ships a sibling `.viz.md` reference visualisation with a
    Mermaid rendering and back-references `playbook.cra_srp_notify@v1`
    at the relevant CACAO step so the bidirectional link linter closes.
  - OCSF Compliance Finding (`telemetry.ocsf.compliance_finding@v1`)
    source-data binding declared per entry.
- **Sovereign-stack constraints:** —
- **Depends on:** F-METRICS-04
- **Source:** Cyber Resilience Act (Regulation (EU) 2024/2847) Art. 14;
  SRP go-live 11 Sept 2026.
- **Shipped via:**
  - SKELETON — #622 (three KRI entries + reference visualisations +
    playbook back-references + a G-03 compile-target restart-drift
    parity row under `tests/patterns/cra_srp_notify/`).

### F-MET-DORA-LATENCY — DORA Art. 17/19 ICT incident reporting latency KRI triad

- **Status:** Shipped
- **Priority:** P1
- **Goal:** G-04 (KPI/KRI catalogue maturity — residual-risk latency
  coverage across every regulator-notification gate the framework
  targets).
- **Acceptance criteria:**
  - `content/metrics/` carries three KRI catalog entries covering the
    DORA major-incident reporting timeline:
    - `kri.dora_incident_initial_report_latency_hours@v1` — 4h clock
      (Art. 19(4)(a)).
    - `kri.dora_incident_intermediate_report_latency_hours@v1` — 72h
      clock (Art. 19(4)(b)).
    - `kri.dora_incident_final_report_latency_days@v1` — one-month clock
      (Art. 19(4)(c)).
  - Each entry ships a sibling `.viz.md` reference visualisation with a
    Mermaid rendering, an OCSF Compliance Finding
    (`telemetry.ocsf.compliance_finding@v1`) source-data binding, and
    warn / high / breach threshold bands.
  - Catalog index in `content/metrics/README.md` updated to list the
    three new entries.
- **Sovereign-stack constraints:** —
- **Depends on:** F-METRICS-04
- **Source:** Digital Operational Resilience Act (Regulation (EU)
  2022/2554) Art. 17 (ICT-related incident management) and Art. 19(4)
  (reporting timelines).
- **Shipped via:**
  - SKELETON — #634 (three KRI entries + reference visualisations +
    catalog index update). Playbook back-references deferred to a
    follow-on card binding the KRIs to the shipped incident_management
    / ransomware_containment / identity_compromise regulator-
    notification chains.

### F-MET-NIS2-LATENCY — NIS2 Art. 23 incident notification latency KRI triad

- **Status:** Shipped
- **Priority:** P1
- **Goal:** G-04 (KPI/KRI catalogue maturity — residual-risk latency
  coverage across every regulator-notification gate the framework
  targets).
- **Acceptance criteria:**
  - `content/metrics/` carries three KRI catalog entries covering the
    NIS2 Art. 23(4) statutory clocks for essential/important entities:
    - `kri.nis2_incident_early_warning_latency_hours@v1` — 24h clock
      (Art. 23(4)(a)).
    - `kri.nis2_incident_notification_latency_hours@v1` — 72h clock
      (Art. 23(4)(b)).
    - `kri.nis2_incident_final_report_latency_days@v1` — one-month clock
      (Art. 23(4)(d)).
  - Each entry ships a sibling `.viz.md` reference visualisation with a
    Mermaid rendering, an OCSF Compliance Finding
    (`telemetry.ocsf.compliance_finding@v1`) source-data binding, and
    warn / high / breach threshold bands.
  - Catalog index in `content/metrics/README.md` updated to list the
    three new entries.
- **Sovereign-stack constraints:** —
- **Depends on:** F-METRICS-04
- **Source:** NIS2 Directive (EU) 2022/2555 Art. 23(4); enforcement
  active since October 2024.
- **Shipped via:**
  - SKELETON — #635 (three KRI entries + reference visualisations +
    catalog index update). Playbook back-references deferred to a
    follow-on card binding the KRIs to the shipped
    regulator-notification playbook chains.

### F-MET-GDPR-LATENCY — GDPR Art. 33/34 data-breach notification latency KRI triad

- **Status:** Shipped
- **Priority:** P1
- **Goal:** G-04 (KPI/KRI catalogue maturity — residual-risk latency
  coverage across every regulator-notification gate the framework
  targets).
- **Acceptance criteria:**
  - `content/metrics/` carries three KRI catalog entries covering the
    GDPR Art. 33/34 statutory clocks for personal-data breaches:
    - `kri.gdpr_breach_supervisory_authority_notification_latency_hours@v1`
      — 72h clock (Art. 33(1)).
    - `kri.gdpr_breach_data_subject_notification_latency_hours@v1` —
      "without undue delay" clock to affected data subjects
      (Art. 34(1)).
    - `kri.gdpr_breach_dpa_escalation_latency_days@v1` — DPO / DPA
      escalation clock supporting Art. 33(5) documentation duty.
  - Each entry ships a sibling `.viz.md` reference visualisation with a
    Mermaid rendering, an OCSF Compliance Finding
    (`telemetry.ocsf.compliance_finding@v1`) source-data binding, and
    warn / high / breach threshold bands.
  - Catalog index in `content/metrics/README.md` updated to list the
    three new entries.
- **Sovereign-stack constraints:** —
- **Depends on:** F-METRICS-04
- **Source:** GDPR (EU) 2016/679 Art. 33 (supervisory-authority
  notification) and Art. 34 (data-subject notification); enforcement
  active since 2018.
- **Shipped via:**
  - SKELETON — #636 (three KRI entries + reference visualisations +
    catalog index update). Playbook back-references deferred to a
    follow-on card binding the KRIs to the shipped
    breach-notification playbook chains.

### F-MET-AVAILABILITY — NIS2/DORA service-availability KPI/KRI sextet

- **Status:** Shipped
- **Priority:** P1
- **Goal:** G-04 (KPI/KRI catalogue maturity — operability-axis
  availability metrics closing the four-FOUNDATION-property coverage
  ring across the NIS2 / DORA service-continuity gates).
- **Acceptance criteria:**
  - `content/metrics/` carries six catalog entries covering the
    NIS2 Art. 21(2)(e) / DORA Art. 8 service-availability and
    business-continuity duties, split evenly between KPI-side
    performance signals and KRI-side residual-risk signals:
    - KPI side:
      - `kpi.service_availability_rate@v1` — measured availability
        against declared SLO for essential/important services.
      - `kpi.rto_compliance_rate@v1` — share of recovery events that
        met their declared RTO.
      - `kpi.service_continuity_test_frequency@v1` — cadence of
        business-continuity / disaster-recovery exercises.
    - KRI side:
      - `kri.availability_below_target_exposure@v1` — residual
        exposure from services running under their declared
        availability target.
      - `kri.rto_overrun_exposure_count@v1` — count of recovery
        events that overran their declared RTO.
      - `kri.continuity_test_overdue@v1` — count of
        services / plans whose continuity test is overdue against
        the declared cadence.
  - Each entry ships a sibling `.viz.md` reference visualisation with a
    Mermaid rendering, an OCSF Compliance Finding
    (`telemetry.ocsf.compliance_finding@v1`) source-data binding, and
    warn / high / breach threshold bands.
  - Catalog index in `content/metrics/README.md` updated to list the
    six new entries.
  - Nightly orphan-CI assertion lane in
    `.github/workflows/orphan-ci.yml` asserts the KPI/KRI sextet
    stays wired to the availability triad (metric ↔ visualisation ↔
    OCSF binding) so drift is caught out-of-band from PR CI.
- **Sovereign-stack constraints:** —
- **Depends on:** F-METRICS-04
- **Source:** NIS2 Directive (EU) 2022/2555 Art. 21(2)(e)
  (business-continuity and crisis-management measures); DORA
  (Regulation (EU) 2022/2554) Art. 8 (ICT business-continuity policy
  and response-and-recovery plans).
- **Shipped via:**
  - SKELETON — #639 (three KPI entries + reference visualisations +
    catalog index update).
  - EXTEND — #640 (three KRI-side residual-risk entries + reference
    visualisations + catalog index update).
  - CORE — #644 (nightly orphan-CI assertion lane covering the
    KPI/KRI sextet).

---

## Epic MAP — Regulatory OSCAL component-definition coverage

OSCAL component definitions per regulatory axis so an operator can feed
the SecOps-NG mapping surface into an OSCAL-aware tool chain. The
per-axis component definition is the auditable, machine-readable form
of the article-level YAML mappings under `content/mappings/<axis>/`.
This epic also carries structural crosswalks against frameworks that
sit alongside the EU statutory surface (for example NIST CSF 2.0),
where the deliverable is a YAML crosswalk rather than an OSCAL
component definition.

### F-MAP-GDPR-OSCAL — GDPR OSCAL component definition

- **Status:** Shipped
- **Priority:** P1
- **Goal:** G-02 (regulatory mapping coverage — closes the four-axis
  OSCAL component-definition parity gap so an operator can feed the
  GDPR mapping surface into an OSCAL-aware tool chain alongside CRA,
  DORA, and NIS2).
- **Acceptance criteria:**
  - `content/mappings/gdpr/oscal-component-definition.json` ships an
    OSCAL 1.1.2 component definition covering the shipped GDPR
    article anchors (Art. 5, 6, 15-22, 25, 26-28, 32, 33-34, 35).
  - Schema and coverage tests in
    `tests/content/test_oscal_gdpr_component_definition.py` validate
    the file against the vendored OSCAL 1.1.2 schema and assert every
    `(entry, control_ref)` pair from the article YAMLs appears as an
    `implemented-requirement`.
  - A nightly orphan-CI lane guards the file out-of-band: schema and
    coverage tests run on every nightly `main` build and the
    implemented-requirement count is asserted to stay at or above the
    SKELETON baseline (55 IRs).
- **Sovereign-stack constraints:** —
- **Depends on:** F-CP-01 (Risk-analysis stream) inbound anchors.
- **Source:** GDPR (EU) 2016/679 Art. 5, 6, 15-22, 25, 26-28, 32,
  33-34, 35.
- **Shipped via:**
  - SKELETON — #653 (OSCAL component definition JSON + schema and
    coverage test).
  - CORE — orphan-CI parity lane for the GDPR OSCAL component
    definition and this ROADMAP entry.

---

### F-MAP-NIST-CSF-20 — NIST CSF 2.0 crosswalk

- **Status:** Shipped
- **Priority:** P2
- **Goal:** G-06 (contributor adoption — a NIST CSF 2.0 crosswalk
  provides a second axis of navigation into the SecOps-NG catalogue
  for practitioners who already frame their reasoning around the
  CSF, widening community reach beyond EU-only readers).
- **Acceptance criteria:**
  - `content/mappings/nist_csf/csf-core-functions.yaml` ships a
    crosswalk against the CSF 2.0 Core at Category granularity
    (22 Categories across Govern / Identify / Protect / Detect /
    Respond / Recover) and at Subcategory granularity (all 106
    Subcategories per NIST CSWP 29), each anchored on
    `content/controls/` and `content/playbooks/` references or an
    explicit `gap_note` for outcomes the SecOps-NG catalogue does
    not exercise.
  - Shape gates in `tests/content/test_nist_csf_crosswalk.py`
    validate the YAML structure, the Subcategory ids against the
    CSF 2.0 layout, and the mutual exclusivity of
    `playbook_refs` / `gap_note` at the Subcategory level.
  - `docs/cookbook/nist_csf_crosswalk.md` is a practitioner
    walkthrough covering navigation, a worked example, and the
    cross-reference to the EU regime mappings.
- **Sovereign-stack constraints:** The crosswalk is a structural
  pointer against the operator's own catalogue; it does not carry
  the CSF Informative References (mappings to SP 800-53r5,
  ISO/IEC 27001:2022, CIS Controls v8) and does not constitute a
  legal or regulator interpretation of the CSF. The EU regime
  mappings under `content/mappings/{nis2,dora,cra,gdpr}/` remain
  authoritative for statutory obligations.
- **Depends on:** —
- **Source:** NIST CSWP 29, "The NIST Cybersecurity Framework (CSF)
  2.0", 26 February 2024.
- **Shipped via:**
  - SKELETON — PR #717 (22 Category-level entries across
    GV / ID / PR / DE / RS / RC).
  - CORE — PR #718 (all 106 Subcategory-level entries nested under
    their parent Categories, each with `playbook_refs` or
    `gap_note`; schema extension and shape tests).
  - EXTEND — PR #719 (practitioner cookbook walkthrough and
    ROADMAP `Shipped` flip).

---

### F-MAP-SOC2 — SOC 2 Trust Services Criteria crosswalk

- **Status:** Shipped
- **Priority:** P2
- **Goal:** G-06 (contributor adoption — a SOC 2 crosswalk provides
  a structural interoperability layer between the SecOps-NG
  catalogue and the AICPA Trust Services Criteria vocabulary,
  widening community reach to practitioners answering US-vendor
  due-diligence questionnaires or reasoning across SOC 2 and the
  EU statutory regimes). G-07 (operator adoption signal —
  practitioners evaluating for US-to-EU posture gaps have a
  criterion-by-criterion pointer from the TSC into the shipped
  catalogue).
- **Acceptance criteria:**
  - `content/mappings/soc2/tsc-*.yaml` ships a crosswalk against
    all five Trust Services categories (Security 33 Common
    Criteria, Availability 3, Confidentiality 2, Processing
    Integrity 5, Privacy 10), each anchored on
    `content/controls/` and `content/playbooks/` references or an
    explanatory `notes` block for criteria the SecOps-NG catalogue
    does not exercise operationally.
  - `content/mappings/soc2/oscal-component-definition.json` ships
    an OSCAL 1.1.2 component definition covering the SOC 2 surface,
    guarded by `tests/content/test_oscal_soc2_component_definition.py`
    and a round-trip test at
    `tests/content/test_oscal_soc2_component_definition_roundtrip.py`.
  - `content/mappings/d3fend/soc2.yaml` ships the D3FEND crosswalk
    against SOC 2, guarded by
    `tests/content/test_d3fend_soc2_crosswalk.py`.
  - `docs/cookbook/soc2_crosswalk.md` is a practitioner walkthrough
    covering navigation, a worked example on CC6.1 (logical access
    controls), the cross-reference to the EU regime mappings, and
    the boundary the crosswalk does not cover (AICPA Informative
    References, Type I / Type II opinion scoping, auditor
    workpapers, TSP 100 guidance).
- **Sovereign-stack constraints:** The crosswalk is a structural
  pointer against the operator's own catalogue; it does not carry
  the AICPA Informative References (mappings to SP 800-53r5,
  ISO/IEC 27001:2022, HIPAA, NIST CSF 2.0), does not constitute a
  SOC 2 attestation or a service auditor's report, and does not
  constitute a legal or regulator interpretation of the TSC. The
  EU regime mappings under `content/mappings/{nis2,dora,cra,gdpr}/`
  remain authoritative for statutory obligations.
- **Depends on:** —
- **Source:** AICPA Trust Services Criteria (2017, as revised),
  delivered under attestation standards AT-C 105 / AT-C 205.
- **Shipped via:**
  - Per-category YAML surface across the five Trust Services
    categories (Security, Availability, Confidentiality,
    Processing Integrity, Privacy).
  - OSCAL 1.1.2 component definition + round-trip test.
  - D3FEND ↔ SOC 2 crosswalk.
  - SKELETON — PR #720 (practitioner cookbook walkthrough
    and ROADMAP `Shipped` flip).

### F-MAP-EUAIACT-GPAI — EU AI Act Chapter V general-purpose AI model obligations

- **Status:** Shipped
- **Priority:** P1
- **Goal:** G-02 (regulatory-graph closure — the GPAI chapter is the
  single largest declared gap on the EU AI Act axis, recorded as out of
  scope in `content/mappings/eu_ai_act/README.md` and deferred to a
  sibling card; this is that card), G-05 (sovereignty — the Art. 55(1)(d)
  cybersecurity-protection obligation on systemic-risk models is where
  the sovereign-stack bias is most directly testable), G-06 (the
  agentic-AI operator community is the population this chapter binds,
  and it is the community least served by existing crosswalks).
- **Scope decision required:** bringing Chapter V in scope widens the
  addressed population from *high-risk AI system providers and
  deployers* to *general-purpose model providers*. That is a
  deliberate scope change, not an oversight — the entry is Proposed so
  it is decided on the record rather than by drift. If declined, the
  README scope note should be tightened to say the exclusion is
  permanent rather than pending.
- **Acceptance criteria:**
  - `content/mappings/eu_ai_act/article-53-gpai-provider-obligations.yaml`
    carries the Art. 53(1)(a)–(d) atoms: technical documentation of the
    model, information and documentation made available to downstream
    providers, the copyright policy, and the sufficiently detailed
    public summary of training content.
  - `content/mappings/eu_ai_act/article-55-systemic-risk-obligations.yaml`
    carries the Art. 55(1)(a)–(d) atoms for models with systemic risk:
    model evaluation including adversarial testing, assessment and
    mitigation of Union-level systemic risks, tracking and reporting of
    serious incidents with corrective measures, and an adequate level of
    cybersecurity protection for the model and its physical
    infrastructure.
  - The Art. 55(1)(c) serious-incident edge cross-references the shipped
    `eu_ai_act:art-73-serious-incident-reporting` entry, with the
    distinct-obligation note recorded in the same style as the existing
    NIS2 / DORA / CRA boundary notes (Chapter V reports to the AI
    Office; Art. 73 reports to the market-surveillance authority —
    parallel chains, not substitutes).
  - `content/mappings/eu_ai_act/oscal-component-definition.json` gains
    implemented-requirements for the new entries, and the existing
    `README.md` scope note is updated to move the GPAI chapter from
    **Out** to the shipped file list.
  - Orphan-CI stays clean; every new entry carries an authoritative
    EUR-Lex permalink.
- **Sovereign-stack constraints:** the Art. 55(1)(d) cybersecurity
  binding must anchor on existing control and telemetry IDs rather than
  introducing a model-hosting opinion — the framework maps obligations,
  it does not prescribe where a model runs.
- **Depends on:** none (mapping-only entry; the existing Art. 72 / 73
  post-market surfaces are already Shipped).
- **Source:** EU AI Act (Regulation (EU) 2024/1689) Chapter V, Art. 53
  and Art. 55; `content/mappings/eu_ai_act/README.md` scope note.

### F-MAP-EUAIACT-LOGGING — EU AI Act Art. 12 record-keeping and automatic logging

- **Status:** Proposed
- **Priority:** P2
- **Goal:** G-02 (regulatory-graph closure — Art. 12 is unmapped and is
  the obligation the Art. 26(6) deployer log-retention atom depends
  on), G-01 (the auditability foundation property is exactly what
  Art. 12 legislates; the shipped evidence-stream model already
  produces the artifact shape the article requires).
- **Acceptance criteria:**
  - `content/mappings/eu_ai_act/article-12-record-keeping.yaml` carries
    the Art. 12(1)–(3) atoms: automatic recording of events over the
    system lifetime, traceability appropriate to the intended purpose,
    and the Art. 12(3)(a)–(d) minimum log content for Annex III(1)(a)
    systems (period of each use, reference database checked, input
    data, and identification of the natural persons involved in
    verification).
  - The entry binds to the shipped evidence-stream model rather than
    proposing a new stream, naming the `incidents` and `access`
    streams as the carriers already in the catalogue, and pins the
    OCSF class the log records resolve against.
  - Orphan-CI stays clean; the article-level cross-reference from
    Art. 26(6) (once F-WF-EUAIACT-DEPLOYER lands) resolves both ways.
- **Sovereign-stack constraints:** log retention is an operator-owned
  surface — the mapping declares the record contract and retention
  obligation, never a storage backend.
- **Depends on:** F-CP-02 (incidents stream, Shipped), F-CP-07 (access
  stream, Shipped).
- **Source:** EU AI Act (Regulation (EU) 2024/1689) Art. 12; Annex III
  point 1(a).

### F-MAP-ORPHAN-PARITY — orphan-CI parity for the non-EU mapping axes

- **Status:** Shipped
- **Shipped:** stage 1 (#932) — the soc2 axis armed born-clean, with
  soc2_evidence_collector's missing home-axis citation authored
  (CC4.1) and pinned by test, making the EU manifests' "closed on
  the home axis" rationales CI-verified; stage 2 (#933) — the twelve
  soc2 interim skips became real TSC citations; package 3 (#934) —
  the d3fend exclusion documented per the accepted option-A memo,
  card criteria amended; package 2 (#944, closing #931) — the
  iso27001 and nist_csf axes armed born-clean (25 and 12 audited
  entries), nightly matrix at eight legs, and the repo-wide
  invariant holding: every finalized playbook on every axis is
  either cited or an audited, named decision. Follow-up citations
  for the fifteen interim entries tracked in #943.
- **Priority:** P2
- **Goal:** G-02 (a mapping axis without the orphan device cannot
  claim coverage — it can only claim files), G-08 (the device class
  proved itself on 2026-08-12: the EU-axis grace window expired and
  was caught only because a PR happened to run the suite that
  afternoon; on the unguarded axes the same rot is permanent and
  silent).
- **Rationale:** The orphan-CI device (finalized playbook must carry
  an inbound `playbook_refs:` citation or an audited
  `_orphan_skip.yaml` entry, 7-day grace window, per-axis KRI) runs
  on the five EU statutory axes only. `content/mappings/iso27001/`
  (4 mapping YAML), `soc2/` (5), `nist_csf/` (1) and `d3fend/` (7)
  have no manifest, no per-axis test, and no nightly lane — a
  playbook finalized without inbound coverage there is never named
  by anything. soc2 is the sharpest case: `soc2_evidence_collector`
  closes its inbound graph on exactly this unguarded axis, so the
  claim "closed on the home axis" that the EU manifests now cite is
  itself unverified by CI.
- **Acceptance criteria:**
  - `_orphan_skip.yaml` manifests, per-axis pytest modules, and
    nightly workflow rows for `iso27001`, `soc2` and `nist_csf`,
    same shape as the EU five (`tools.lint_playbook_orphans`
    parameterised, `kri_name_for(framework)` naming).
  - The initial manifests land audited the same way as the SKELETON
    batches: every currently-finalized playbook classified — real
    citation or an audited skip with domain rationale — in the PR
    that arms the assertion, so the device is born clean rather
    than born with a ceiling.
  - `d3fend` is assessed, not assumed: it is a technique crosswalk,
    not an obligation axis, and may warrant a different device or a
    documented exclusion. The decision and its rationale land in
    `content/mappings/d3fend/README.md` either way. (Decided —
    #931 option A, 2026-08-13: documented exclusion; playbooks
    connect through controls, and the six per-regime crosswalk
    test modules already guard both resolution directions. A
    via-controls coverage device, if ever warranted, belongs to
    the dangling-refs guard scope (#841).)
  - The per-axis KRI emission uses the shipped mechanism the EU
    five use: `kri_name_for(framework)` dashboard labels via
    `--format kri`, uploaded per matrix leg. (Amended per the
    #931 memo — the criterion originally said "join the catalogue
    with the same schema compliance as the EU five", written on
    the wrong assumption that the EU five had catalogue entries;
    catalogue-grade orphan metrics, if wanted, are their own
    G-04 card.)
- **Sovereign-stack constraints:** None beyond the house rule — the
  device is repo-local lint, no network, no telemetry.
- **Depends on:** —
- **Source:** 2026-08-12 repository review; the grace-window
  incident fixed by the audited-skip batch (#917); goal G-02.

---

## Epic ADOPT — Operator adoption signal

Public, community-owned surfaces that make operator adoption of
SecOps-NG visible without requiring the project to run telemetry.

### F-ADOPT-01 — USED-BY.md operator adoption registry

- **Status:** Shipped
- **Shipped:** SKELETON (`USED-BY.md` registry + self-attestation
  contributor guide, #614), CORE (Deployments & Adoption discussion
  template, #616), and EXTEND (scheduled CI reachability check for
  evidence links, #615) all merged to `main` — 2026-07-03.
- **Priority:** P1
- **Acceptance criteria:**
  - `USED-BY.md` exists at the repository root as a self-attestation
    registry (`Organisation | Deployment type | Playbooks in use |
    Since | Evidence link`) with a heading note stating the project
    does not collect telemetry and additions land via PR.
  - `docs/contributing/self-attesting-adoption.md` walks a contributor
    through fork → edit → PR against `main`, in community voice.
  - CORE — community outreach lands the first cohort of self-attested
    entries (target ≥ 5 publicly attestable references by Q4 2026).
    Community infrastructure:
    `.github/DISCUSSION_TEMPLATE/deployment-question.yml` — a
    Deployments & Adoption discussion template that surfaces
    evaluation and pilot interest in the open before it becomes a
    formal `USED-BY.md` entry.
  - EXTEND — CI check that every `USED-BY.md` row's evidence link is
    a reachable public URL (no login wall, HTTP 2xx on scheduled run).
- **Sovereign-stack constraints:** No telemetry, no analytics beacons,
  no maintainer-side collection — the registry is the signal.
- **Depends on:** —
- **Source:** Contributor-experience gap surfaced by the FOUNDATION /
  ROADMAP review; goal G-07 (operator adoption signal, Q4 2026).

### F-ADOPT-02 — Sovereignty conformance disclosure pack

- **Status:** Shipped
- **Shipped:** single card (#923, closing #922) — deterministic
  renderer (`tools.render_disclosure_pack`, allowlist construction +
  serialisation backstop + `--baseline` drift refusal), the pack
  schema as machine-readable redaction contract, the DISCLOSURE.md
  format and MUST-NOT documentation, the committed worked example
  carrying the reference posture's true failing rows, and the
  USED-BY.md / self-attestation-guide pointers, pinned by test.
- **Priority:** P1
- **Goal:** G-07 (the registry's `Evidence link` column currently
  points at whatever the operator happens to have public; this gives
  it a checkable artifact to point at), G-05 (the pack is the public
  face of the Epic SV chain — measured, evidenced, judged — and the
  first reason for an operator to run it end to end).
- **Rationale:** Epic SV completed on 2026-08-12: an operator can
  emit an F-SV-04 evidence record and evaluate it against the
  declared baseline deterministically. What they cannot yet do is
  *publish* the result safely. A disclosure pack is the redacted,
  self-contained subset of the verdict an operator can link from
  their `USED-BY.md` row — turning "we use it" into "we use it and
  here is the posture we hold", with the honest-verdict discipline
  intact (a pack that only renders passing rows is airbrushing).
- **Acceptance criteria:**
  - A documented pack format: profile stable id, evaluator verdict
    (all indicators, all outcomes — including `fail` and
    `unobserved`), the evidence-record digest rather than the raw
    record, and generation provenance (tool version, profile
    version). Never a score.
  - A redaction contract stating what the pack MUST NOT carry:
    endpoint literals, internal identifiers, raw observed values for
    indicators the operator marks sensitive — mirroring the F-SV-04
    constraint that the artifact cannot itself become a non-EU
    reference.
  - A deterministic renderer (`tools.render_disclosure_pack` or a
    documented `evaluate_sovereignty_conformance --disclosure` mode):
    same record + same profile → byte-identical pack.
  - A committed worked example generated from the reference
    `infra_posture_management` artifacts — carrying its true
    failing rows, per the F-SV-05 test discipline.
  - `USED-BY.md`'s heading note and
    `docs/contributing/self-attesting-adoption.md` name the pack as
    the preferred evidence-link target; the F-ADOPT-01 reachability
    check needs no change (a pack URL is a URL).
- **Sovereign-stack constraints:** Operator-published, pull-based —
  no submission endpoint, no telemetry. The renderer is pure and
  offline like the evaluator it wraps.
- **Depends on:** F-SV-04, F-SV-05 (both Shipped).
- **Source:** Epic SV completion review, 2026-08-12; goal G-07.

### F-ADOPT-03 — Adoption-signal metric pair in the catalogue

- **Status:** Shipped
- **Shipped:** single card (#930, closing #929) —
  kpi.attested_adoption_count@v1 (verified-evidence registry rows,
  target from the F-ADOPT-01 outreach goal) paired via
  residual_risk_refs with kri.adoption_evidence_rot_count@v1
  (failing evidence links, consecutive-run aging as the canonical
  drill-down), both registry-derived with committed reference
  visualisations, no telemetry.
- **Priority:** P2
- **Goal:** G-07 (the Sunday scorecard currently has no needle for
  adoption — the registry exists but nothing reads it), G-04 (the
  pair lands under the same schema, pairing and reference-viz
  discipline as the rest of the catalogue).
- **Rationale:** F-ADOPT-01 shipped the signal surface and F-ADOPT-02
  makes it checkable, but neither makes it *measured*. The catalogue
  is the house instrument for that, and the F-SV-06 rule applies
  unchanged: a coverage KPI without its residual-risk counterpart
  invites reading growth while rot accumulates silently.
- **Acceptance criteria:**
  - `kpi.attested_adoption_count@v1` — count of `USED-BY.md` rows
    whose evidence link passed the latest scheduled reachability
    check. Source of record is the registry file plus the check
    output; no telemetry, no analytics.
  - `kri.adoption_evidence_rot_count@v1` — rows whose evidence link
    failed that check; declared as the KPI's `residual_risk_refs`
    counterpart so the pairing lint holds.
  - Both carry committed reference visualisations and pass the
    catalogue schema, hygiene linter, and pairing lint with zero
    findings.
  - The Sunday scorecard reads the pair once they exist (scorecard
    wiring is the agent's lane; the acceptance boundary here is
    that the metrics exist and are correct).
- **Sovereign-stack constraints:** Registry-derived only — the
  project never collects operator data; the metrics read a file in
  its own repository.
- **Depends on:** F-ADOPT-01 (Shipped); pairs naturally with
  F-ADOPT-02.
- **Source:** 2026-08-12 repository review (G-07 milestone: one
  closed item, zero open, no pipeline); goal G-07.

---

## Revision history

- **v0 (2026-05-21).** Initial seed from FOUNDATION.md, ARCHITECTURE.md,
  and the NIS2 / GDPR mappings under `content/mappings/`. Subsequent
  revisions land via contributor PRs.
