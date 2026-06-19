# codebase_vuln_management — cookbook walkthrough

SBOM-driven codebase vulnerability management. The
`playbook.codebase_vuln_management@v1` CACAO playbook takes a freshly
produced or refreshed SBOM as input, pins its content hash, walks the
declared dependencies against a vulnerability database, resolves the
operator's coordinated-vulnerability-disclosure (CVD) policy into
per-finding `acknowledge_by` / `fix_by` / `disclose_by` deadlines, and
emits one disclosure-timeline-record per affected component+advisory
pair that the downstream metric streams (F-CP-04) and the auditor
bundle (F-WF-09) consume.

The regulatory anchors are NIS2 Article 21(2)(e) (security in network
and information systems acquisition, development, and maintenance —
specifically the codebase-side dependency-review and disclosure-window
surface) and CRA Annex I §2 (product-side vulnerability handling and
SBOM production for releases). The NIS2 mapping is
`nis2:art-21-2-e-codebase` in
[`content/mappings/nis2/article-21-2-e.yaml`](../../content/mappings/nis2/article-21-2-e.yaml).

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the deterministic
primitives package, the shared disclosure-timeline evidence emitter,
and the per-target adapter live in each.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/codebase_vuln_management/
├── README.md                    # workflow-local module tree
├── playbook.cacao.json          # canonical CACAO v2 source (playbook.codebase_vuln_management@v1)
└── primitives/
    ├── sbom.py                  # pin_sbom_content_hash + normalise_findings
    ├── disclosure_window.py     # resolve_disclosure_window — CVD policy → per-finding deadlines
    └── timeline.py              # build_disclosure_timeline_stub — emitter input shaping

content/evidence/codebase_vuln_management/
├── README.md
└── disclosure-timeline-record.schema.json   # per-finding evidence schema

compilers/_shared/evidence/disclosure_timeline.py
                                  # framework-agnostic shared emitter (deterministic id, atomic write)
```

The CACAO source is canonical. The primitives package is the
deterministic policy the playbook *means*. The three worked examples
are the same playbook compiled into three orchestrator idioms.
Everything else — runtime, connectors, credentials, scanner endpoint,
advisory feed — is the operator's data plane.

The CACAO source ships as JSON
(`content/playbooks/codebase_vuln_management/playbook.cacao.json`); the
three worked examples each carry a mirror copy at
`examples/{n8n,temporal,langgraph}/codebase_vuln_management/playbook.cacao.json`
that is byte-identical to the canonical and refreshed by the
per-target `regenerate.sh`.

## 2. CACAO topology and primitives binding

The playbook ships six steps: one `start`, four `action`, one `end`.
All four action steps declare an `x_secops_ng.core_body` reference into
the deterministic primitives package; there are **no absent-body steps**
in this workflow — the CORE-FANOUT wave landed the bindings up-front in
the canonical source rather than via a per-target overlay.

| Step suffix | Step                  | `core_body` binding                                                                            | Status   |
|-------------|-----------------------|------------------------------------------------------------------------------------------------|----------|
| `…000001`   | start                 | edge wiring only — no body                                                                     | n/a      |
| `…000002`   | ingest-sbom           | `primitives.sbom.pin_sbom_content_hash`                                                        | bound    |
| `…000003`   | review-deps           | `primitives.sbom.normalise_findings`                                                           | bound    |
| `…000004`   | assess-disclosure     | `primitives.disclosure_window.resolve_disclosure_window`                                       | bound    |
| `…000005`   | track-timeline        | `primitives.timeline.build_disclosure_timeline_stub`                                           | bound    |
| `…000006`   | end                   | edge wiring only — no body                                                                     | n/a      |

Transitions are deterministic — each state has exactly one
`on_completion` successor, no conditional branching at this layer. The
per-finding fan-out (one record per `(component, advisory)` pair) lives
inside `review-deps` and `track-timeline` as the natural map step the
operator's runtime expresses in its own idiom (n8n SplitInBatches,
Temporal child workflow / activity loop, LangGraph map / fan-out).

## 3. Deterministic primitives — the contract

The SBOM content-hash anchor, the four-band severity tier, the
disclosure-window table the CVD policy resolves into, the
timeline-record input shape, and the `id` recipe a downstream
deduplicator joins on are **code, not configuration**. They live in
`content/playbooks/codebase_vuln_management/primitives/` and in the
shared emitter under `compilers/_shared/evidence/disclosure_timeline.py`.
Operators who need to diverge fork the primitive module; they do not
override it via runtime config.

The four bindings exercised today:

`pin_sbom_content_hash(sbom_bytes, sbom_format) -> str`
:   The `ingest-sbom` step takes the canonical SBOM artefact produced
    by the operator's build chain (CycloneDX or SPDX), validates the
    format, and pins the SHA-256 of the SBOM bytes. The hash anchors
    every downstream finding to a specific SBOM revision; a re-walk of
    the same SBOM produces the same hash and therefore the same record
    ids.

`normalise_findings(raw_findings, sbom_content_hash) -> Sequence[Finding]`
:   The `review-deps` step canonicalises the scanner output (NVD / OSV
    / GHSA / vendor) into the playbook's `Finding` contract: a
    PURL-shaped `component`, a canonical `advisory_id`, a four-band
    `severity` tier (`critical` / `high` / `medium` / `low`), and the
    OCSF-shaped `source_data` pointer (class_uid 2002 — Vulnerability
    Finding). The underlying advisory payload is deliberately *not*
    embedded — per AGENTS.md §3 it is operator-side data and stays in
    the operator's data plane.

`resolve_disclosure_window(severity, awareness_at, cvd_policy) -> DisclosureWindow`
:   The `assess-disclosure` step resolves the operator-supplied
    `cvd_policy` (a JSON-native dict of per-severity hour offsets)
    against the case's `awareness_at` ISO-8601 UTC timestamp and the
    finding's severity band. Returns the three absolutes
    (`acknowledge_by`, `fix_by`, `disclose_by`) as ISO-8601 `...Z`
    strings. `info` / `unknown` severities resolve to an empty window
    — the operator's CVD policy doesn't bind a disclosure timeline for
    findings without a real severity, and the downstream
    timeline-stub primitive emits an empty disclosure window.

`build_disclosure_timeline_stub(finding, disclosure_window, captured_at, ref_viz, source_data) -> DisclosureTimelineRecord`
:   The `track-timeline` step shapes the per-finding record the shared
    emitter under
    [`compilers/_shared/evidence/disclosure_timeline.py`](../../compilers/_shared/evidence/disclosure_timeline.py)
    serialises. The emitter is the single source of truth for the
    `id` recipe — SHA-256 of
    `<workflow_id>|<sbom_content_hash>|<component.purl>|<advisory_id>`
    (UTF-8, no separators around the pipes) — so a re-walk of the
    same SBOM against the same advisory re-derives the same id and
    downstream deduplication is trivial. `captured_at` is deliberately
    *not* part of the id so a re-emission of the same finding at a
    different wall-clock instant still dedupes.

Determinism is the property a regulator can replay against. The shared
emitter is the byte-identical anchor the cross-target byte-parity
property hangs off: the three per-target adapters are thin glue, and
the on-disk evidence record is byte-identical across n8n, Temporal,
and LangGraph for the same input context.

> **LM determinism.** SBOM hashing, finding normalisation,
> disclosure-window resolution, and timeline-record shaping are code,
> not LM. The codebase_vuln_management playbook does not bind any DSPy
> signature today — there is no free-text submission step at this
> layer (the CRA Article 14 / NIS2 Article 23 free-text submission
> chain lives in `vuln_intake` and `incident_management`).
> See `docs/FOUNDATION.md` § LLM determinism.

## 4. Per-target hand-off

### 4.1 n8n — operator-edited Set rows + Code-node bindings

`examples/n8n/codebase_vuln_management/workflow.n8n.json` carries the
CACAO topology as n8n nodes (`manualTrigger`, `set`, `code`, `noOp`),
with node ids preserving the CACAO step ids verbatim. The four bound
CORE steps emit `n8n-nodes-base.code` nodes whose `pythonCode` is the
exact primitive call — e.g.
`from content.playbooks.codebase_vuln_management.primitives.sbom import pin_sbom_content_hash ; __sbom_content_hash__ = pin_sbom_content_hash(__sbom_bytes__, __sbom_format__)`.
The Code-node body assumes `PYTHONPATH` on the n8n host resolves
`content.playbooks.codebase_vuln_management.primitives`; operators who
run n8n in a Python-free container drop a Python-runner Code node
between the Set node and the next step — see
[`examples/n8n/codebase_vuln_management/README.md`](../../examples/n8n/codebase_vuln_management/README.md)
under *Per-action wiring notes — CORE bodies*.

The `track-timeline` step routes the per-finding loop through the
shared evidence emitter; the n8n adapter calls
`compilers._shared.evidence.disclosure_timeline.emit_disclosure_timeline_artifact`
with the typed context and the operator-supplied evidence directory,
and the emitter writes the deterministic `<id>.json` to disk.

### 4.2 Temporal — `@activity.defn` bodies with retry policy

`examples/temporal/codebase_vuln_management/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action. The four bound activities
import the primitive (and the shared emitter for `track-timeline`) and
produce the canonical SBOM hash / normalised findings / disclosure
window / disclosure-timeline-record. There are no absent-body
activities in this workflow.

The committed `workflow.temporal.py` is a generated stub: CORE
primitive calls are inlined into the activity bodies under the
`@activity.defn` decorators, while the workflow lowering itself (the
`@workflow.run` method) still raises `NotImplementedError` pending the
workflow-translator slice — operators wire the per-finding loop and
the activity scheduling in their worker assembly. Per-activity retry
policies are emitted alongside the activities
(`<ACTIVITY>_RETRY_POLICY`) so the operator can pin them on the
`workflow.execute_activity` call sites.

The sibling `_audit_mirror.py` carries the `AuditRecord` / `AuditTrail`
types — no `compilers.*` import in the emitted artifact, so the
worker module is a self-contained drop-in. The Temporal evidence
adapter is the durable surface that exercises the shared emitter under
deterministic execution; replay against the same Temporal event
history re-derives the same record id.

### 4.3 LangGraph — `@tool` wrappers + agentic-extension hook

`examples/langgraph/codebase_vuln_management/state_bindings.py` carries
the `TypedDict` state and the four `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (nodes, edges).
`assemble.py` is the canonical reference assembly that wires the spec
into a `StateGraph`. The four bound tools import the primitive (and
the shared emitter for `track-timeline`) and update the typed state;
there are no absent-body tools.

LangGraph is the agentic target — the natural seam an operator extends
with an LLM-driven node is the `review-deps` step (an agentic triage
pass over the raw scanner output before `normalise_findings` produces
the canonical contract). The compiler never embeds an LLM SDK; the
operator wires the agentic hook to self-hosted open-weights inference
or to an EU-hosted managed endpoint without regenerating the artifact.
The framework-wide EU-resident LM endpoint guard re-applies the check
at process startup (`_lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 5. Observability — OTel + AuditTrail in every target

Every emitted action opens an OpenTelemetry span and appends an
`AuditRecord` to a context-local `AuditTrail` *before* the primitive
call. The mirror runs unconditionally, ahead of any OTLP exporter, so
the audit property holds even when the operator has not configured a
collector — typical for disconnected, sovereign, or air-gapped
deployments.

Span attributes use the shared `secops_ng.*` keyspace and are stable
across the three targets:

| Attribute key                | Carries                                              |
|------------------------------|------------------------------------------------------|
| `secops_ng.playbook.id`      | CACAO playbook id (`playbook--…`).                   |
| `secops_ng.playbook.version` | Content version pinned in the playbook.              |
| `secops_ng.step.id`          | CACAO step id (`action--…`).                         |
| `secops_ng.step.name`        | Human-readable step label.                           |
| `secops_ng.step.type`        | CACAO step type (`action`, `start`, `end`).          |
| `secops_ng.tool.name`        | Emitted tool / activity / Code-node function name.   |
| `secops_ng.compile.target`   | `n8n` / `temporal` / `langgraph` discriminator.      |

Span boundaries per target:

- **n8n** — the compiled workflow is a snapshot of intent; OTel
  instrumentation is a per-node operator concern documented per
  node-id, not a runtime guarantee of the emitted JSON.
- **Temporal** — workflow span (`workflow.<stable_id>`) at workflow
  entry; activity span (`activity.<step_id>`) on every activity body,
  with retries opening a fresh child span per Temporal attempt.
- **LangGraph** — node span (`node.<step_id>`) wrapping every node
  assembled in `assemble.py`; tool span (`tool.<step_id>`) inside the
  `@tool` wrapper.

The OTLP exporter endpoint is operator-supplied
(`OTEL_EXPORTER_OTLP_ENDPOINT`). The compiler never sets a default and
never imports a vendor SDK; pointing the exporter at a managed APM is
a downstream choice the operator owns end-to-end. The sovereignty
posture asks for an EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline.

## 6. Replay and audit story

Two replay properties are pinned for codebase_vuln_management.

**Same-target deterministic replay** — the shared emitter under
`compilers/_shared/evidence/disclosure_timeline.py` produces a
byte-identical record on every re-emission with the same context. The
record `id` is `SHA-256(workflow_id|sbom_content_hash|component.purl|advisory_id)`;
`captured_at` is deliberately excluded from the id so re-emission at a
later wall-clock instant still dedupes against the original.

**Cross-target byte-parity** — the three committed worked-example
records under
`examples/{n8n,temporal,langgraph}/codebase_vuln_management/evidence/disclosure-timeline-record.json`
are byte-identical. The byte-parity goldens under
`tests/examples/codebase_vuln_management/` pin the on-disk bytes of
both the per-target workflow artefact
(`test_{n8n,temporal,langgraph}_workflow_golden.py`) and the per-target
evidence record (`test_{n8n,temporal,langgraph}_disclosure_timeline.py`)
against a fresh emitter run from the canonical CACAO source. If the
compiler or the shared emitter changes, regenerate the worked example
via the per-target `regenerate.sh` and commit the diff intentionally;
the drift guard flips green again.

The cross-target byte-parity is the property a regulator diffs to
confirm the playbook means the same thing on every runtime an operator
might already have deployed. The shared emitter is the single source of
truth and the per-target adapters are thin glue.

## 7. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys, no scanner
  endpoints, no advisory feeds. The scanner CLI, the vulnerability
  database, and the storage backend for the disclosure-timeline
  records are operator-bound at runtime against environment variables
  documented per target; the framework ships no default endpoint per
  the sovereign-stack constraint.
- **Deployment topology.** Worker concurrency, retry policies beyond
  the per-activity defaults, persistence backends, n8n hosting,
  LangGraph host process model — those are runtime concerns the
  operator applies in their own assembly.
- **SBOM production.** This playbook consumes a freshly produced SBOM;
  the build-chain step that produces it (CycloneDX or SPDX) is
  upstream and operator-owned. The CRA Annex I §2(1) obligation that
  a vendor produce an SBOM for a release lives in the operator's
  build pipeline, not in this workflow.
- **Advisory payload, reporter contact, raw SBOM bytes.** These are
  operator-side surfaces and may carry personal data; per AGENTS.md
  §3 they stay in the operator's data plane and are intentionally
  out of scope for the per-finding evidence record this workflow
  emits.
- **Per-deployment YAML.** This playbook ships no separate
  operator-facing `config.yaml`; per-case inputs are the CACAO
  `playbook_variables` block bound at compile time via the standard
  `__double_underscore__` substitution.

## 8. References

- [`content/playbooks/codebase_vuln_management/playbook.cacao.json`](../../content/playbooks/codebase_vuln_management/playbook.cacao.json)
  — canonical CACAO source.
- [`content/playbooks/codebase_vuln_management/README.md`](../../content/playbooks/codebase_vuln_management/README.md)
  — workflow-local module tree.
- [`content/evidence/codebase_vuln_management/disclosure-timeline-record.schema.json`](../../content/evidence/codebase_vuln_management/disclosure-timeline-record.schema.json)
  — per-finding evidence schema.
- [`content/mappings/nis2/article-21-2-e.yaml`](../../content/mappings/nis2/article-21-2-e.yaml)
  — NIS2 Art. 21(2)(e) mapping; entry `nis2:art-21-2-e-codebase` is
  the codebase-side anchor.
- [`compilers/_shared/evidence/disclosure_timeline.py`](../../compilers/_shared/evidence/disclosure_timeline.py)
  — shared framework-agnostic evidence emitter.
- [`examples/n8n/codebase_vuln_management/README.md`](../../examples/n8n/codebase_vuln_management/README.md)
- [`examples/temporal/codebase_vuln_management/README.md`](../../examples/temporal/codebase_vuln_management/README.md)
- [`examples/langgraph/codebase_vuln_management/README.md`](../../examples/langgraph/codebase_vuln_management/README.md)
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
