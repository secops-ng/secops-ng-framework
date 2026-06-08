# incident-management — cookbook walkthrough

NIS2 Article 23 three-stage incident reporting. The
`playbook.incident_management@v1` CACAO playbook intakes a significant
incident signal handed in by an upstream workflow (an alert-triage
close-out, a ransomware-containment close-out, or an operator-raised
ticket), classifies whether the event crosses the NIS2 Article 23(3)
significance threshold and whether it has Article 23(6) cross-border
impact, opens a deterministic incident timeline against the F-PT-02
incident-timeline pattern, submits the 24-hour early warning, submits
the 72-hour notification, conditionally submits the one-month final
report (free-text fields scoped to narrative, root cause, and applied
mitigations only), and closes the timeline so the regulator-shaped
JSON artefact is persisted at a repository-relative path consumed
downstream by F-CP-02.

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the deterministic
primitives package, the OpenTelemetry signal layer, and the
context-local `AuditTrail` mirror live in each.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/incident-management/
├── README.md                    # workflow-local module tree
├── playbook.cacao.json          # canonical CACAO v2 source (playbook.incident_management@v1)
└── primitives/
    ├── classification.py        # classify_significance — closed-alphabet rule table over IntakeSignals
    ├── classification_policy.yaml # the rule table the classifier matches against (first-match semantics)
    ├── stage_clock.py           # STAGE_DURATIONS + due_at + stage_window + verdict_for_submission
    ├── regulator_submission.py  # fail-closed resolve_destination + per-stage submission models
    ├── timeline_binding.py      # F-PT-02 incident-timeline adapter (open / record_event / close)
    └── signatures.py            # DSPy signature schema — narrative, root cause, mitigations only
```

The CACAO source is canonical. The primitives package is the
deterministic policy the playbook *means*. The three worked examples
are the same playbook compiled into three orchestrator idioms.
Everything else — runtime, connectors, credentials, regulator
destinations — is the operator's data plane.

The CACAO source ships as JSON
(`content/playbooks/incident-management/playbook.cacao.json`) rather
than YAML; both shapes are first-class inputs to the per-target
compilers. The JSON is the single source of truth and the worked
examples each carry a mirror copy at
`examples/{n8n,temporal,langgraph}/incident-management/playbook.cacao.json`.

## 2. CACAO topology and primitives binding

The playbook ships 11 steps: one `start`, seven `action`, two
`if-condition`, one `end`. Of the seven action steps, four declare an
`x_secops_ng.core_body` reference into the deterministic primitives
package via the per-target overlay (see § 2.1); three stay absent-body
across the SKELETON wave and raise `NotImplementedError` from inside
the span + audit-mirror prologue until the upstream primitive lands.

| Step suffix | Step                                            | `core_body` binding (per-target overlay)                                       | Status   |
|-------------|-------------------------------------------------|--------------------------------------------------------------------------------|----------|
| `…000002`   | intake significant-incident signal              | (no upstream primitive yet — upstream-workflow handoff envelope deferred)      | absent   |
| `…000003`   | classify significance and cross-border scope    | `primitives.classification.classify_significance`                              | bound    |
| `…000004`   | significant? (if-condition)                     | edge wiring only — no body                                                     | n/a      |
| `…000005`   | open incident timeline                          | (no upstream primitive yet — F-PT-02 binding adapter present; open-call seam)  | absent   |
| `…000006`   | submit 24-hour early warning                    | `primitives.regulator_submission.resolve_destination(stage='early_warning')`   | bound    |
| `…000007`   | submit 72-hour notification                     | `primitives.stage_clock.verdict_for_submission(stage='notification', ...)`     | bound    |
| `…000008`   | final-report material complete? (if-condition)  | edge wiring only — no body                                                     | n/a      |
| `…000009`   | submit 1-month final report                     | `primitives.regulator_submission.resolve_destination(stage='final_report')`    | bound    |
| `…00000a`   | close incident timeline                         | (no upstream primitive yet — close-call seam against F-PT-02 adapter)          | absent   |

The four bindings shipped today are the byte-identical anchor the
cross-target replay property hangs off. The three absent-body steps
all share the same shape — span + `AuditTrail` mirror prologue, then
`raise NotImplementedError(...)` — so an integrator can identify each
seam at a glance.

### 2.1 The CORE-PRIM contract and the per-target overlay

The canonical `playbook.cacao.json` deliberately ships **without**
`x_secops_ng.core_body` blocks on the action steps in this SKELETON
wave. The per-step bindings instead live in
`examples/{n8n,temporal,langgraph}/incident-management/core_body.overlay.json`
and are layered onto each target's CACAO mirror at regeneration time.
The three overlays are **cell-for-cell identical** — same step ids,
same primitive references, same input / output names — so the three
compile targets stay in lock-step across the SKELETON wave.

The overlay collapses to empty and the per-target divergence closes
when a subsequent card promotes the `core_body` blocks upward into the
canonical source as the single source of truth. The per-example
divergence guard tests
(`tests/examples/incident_management/test_temporal_workflow.py`,
`tests/examples/incident_management/test_langgraph_graph.py`, and the
n8n sibling) pin the asymmetry until that promotion lands.

Asymmetry between the three regulator-submission steps (two bind the
fail-closed destination resolver, one binds the stage-clock verdict)
is a deliberate SKELETON demonstration: every primitive group named on
the wave card (stage-clock, classification, regulator-submission) is
exercised somewhere in the workflow, with the operator wiring the
second primitive per step (the clock check on the bound-destination
steps and the destination resolution on the bound-clock step) at the
target's body layer. Subsequent waves consolidate per-step bindings.

## 3. Deterministic primitives — the contract

The significance and cross-border classification table, the three-stage
NIS2 Article 23 clock durations (24 hours, 72 hours, one month), the
fail-closed destination resolver, the timeline-binding adapter contract,
and the DSPy signature schema for free-text fields are **code, not
configuration**. They live in
`content/playbooks/incident-management/primitives/`. Operators who need
to diverge fork the primitive module; they do not override it via
runtime config.

The four bindings exercised today:

`classify_significance(signals: IntakeSignals) -> ClassificationVerdict`
:   The classify step runs the inbound `IntakeSignals` envelope through
    the closed-alphabet rule table in `classification_policy.yaml`
    (first-match semantics; rule order and shape are validated at
    load time) and produces a `ClassificationVerdict` carrying the
    significance and cross-border booleans, the rule id that matched,
    an ordered tuple of every reason that fired, and a digest of the
    canonical signal inputs. The digest is what a replay-vs-original
    comparison string-equals against.

`resolve_destination(stage, destinations) -> str`
:   The submit-early-warning, submit-notification, and submit-final-report
    steps each resolve the operator-supplied
    `__notification_destinations__` dictionary at compile-target
    config layer (an n8n credential, a Temporal worker env binding, a
    LangGraph runtime config block) into the per-stage opaque
    destination handle. The resolver is **fail-closed**: an absent or
    empty entry raises `MissingDestinationError` rather than picking a
    default. The framework ships no default endpoint per the
    sovereign-stack constraint — operators name the regulator they
    report to.

`verdict_for_submission(stage, opened_at, now) -> StageVerdict`
:   The submit-notification step (and, when an operator wires the
    second primitive on the other submit steps, the corresponding
    submission too) checks the three-stage NIS2 Article 23 clock
    against the timeline `opened_at` anchor. `STAGE_DURATIONS` pins
    the 24-hour / 72-hour / one-month windows; `stage_window` produces
    the per-stage `[opened_at, due_at]` range; `verdict_for_submission`
    returns a `StageVerdict` carrying the stage label, the opened-at /
    due-at timestamps, the elapsed budget, and a digest of the
    canonical clock inputs.

`open_timeline(...)`, `record_event(...)`, `close_timeline(...)` — F-PT-02 adapter
:   The timeline-binding module ships today as a thin adapter
    (`PT02_BINDING_STATUS = "adapter"`) per the gap-inventory layout
    decision. The open / record / close call shapes are the contract the
    per-target CORE bodies will bind to; when the upstream
    `patterns/incident_timeline/` module lands, the adapter swaps for
    the real binding **without per-target CORE body shapes changing**.
    The timeline JSON artefact is persisted at
    `content/evidence/incidents/<incident-id>/timeline.json` and is
    consumed downstream by F-CP-02.

Determinism is the property a regulator can replay against. The
`ClassificationVerdict.inputs_digest` and the `StageVerdict.inputs_digest`
are the hex strings a replay diff string-equals against; they are the
same on every target because the policy is the same Python function
called through three different idioms.

> **LM determinism.** Significance classification, the stage clock,
> destination resolution, and the timeline binding are code, not LM.
> DSPy appears only in `primitives.signatures` and is reserved for the
> free-text fields on the final-report submission (operator-supplied
> narrative, root cause, applied mitigations) where free-text-in /
> structured-out is the only sensible shape. See
> `docs/FOUNDATION.md` § LLM determinism.

## 4. Per-target hand-off

### 4.1 n8n — operator-edited Set rows + Code-node bindings

`examples/n8n/incident-management/workflow.n8n.json` carries the CACAO
topology as n8n nodes (`manualTrigger`, `set`, `if`, `noOp`), with
node ids preserving the CACAO step ids verbatim. The four bound CORE
steps emit `n8n-nodes-base.code` nodes whose `pythonCode` is the exact
primitive call (e.g.
`from incident_management.primitives.classification import classify_significance ; __classification_verdict__ = classify_significance(__intake_signals__)`);
the three absent-body steps emit an `n8n-nodes-base.set` node carrying
the CACAO I/O contract as editable assignment rows.

Operators bind the Set rows and Code-node inputs to their connectors:

- intake → upstream-workflow handoff envelope (alert-triage close-out,
  ransomware-containment close-out, or operator-raised ticket)
- open / close timeline → F-PT-02 incident-timeline pattern handle
  store (the operator's persistence backend for the timeline JSON)
- submit early-warning / notification / final-report → operator's
  regulator endpoint per stage, resolved out of
  `__notification_destinations__`

The Code-node body for the four bound steps assumes `PYTHONPATH` on
the n8n host resolves `incident_management.primitives`. Operators who
run n8n in a Python-free container drop a single Python-runner Code
node between the Set node and the next step; the wiring is documented
in
[`examples/n8n/incident-management/README.md`](../../examples/n8n/incident-management/README.md)
under *Per-action wiring notes — CORE bodies*.

### 4.2 Temporal — `@activity.defn` bodies with retry policy

`examples/temporal/incident-management/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action. The four bound activities
import the primitive and produce the canonical classification verdict /
destination handle / stage verdict; the three absent-body activities
open the span, append the audit record, and then
`raise NotImplementedError` so an integrator sees exactly which seam
they still have to wire.

Operators drop `workflow.temporal.py` next to their worker, register
the activities, and run the worker against their Temporal cluster.
The sibling `_audit_mirror.py` carries the `AuditRecord` / `AuditTrail`
types — no `compilers.*` import in the emitted artifact, so the worker
module is a self-contained drop-in.

Per-activity retry policies are emitted alongside the activities
(`<ACTIVITY>_RETRY_POLICY`) so the operator can pin them on the
`workflow.execute_activity` call sites in their worker assembly.

### 4.3 LangGraph — `@tool` wrappers + agentic-extension hook

`examples/langgraph/incident-management/state_bindings.py` carries the
`TypedDict` state, `@tool`-decorated action wrappers, and an
`AGENTIC_HOOK` slot for an LLM-driven node. `graph_spec.json` carries
the target-neutral topology (nodes, edges, conditional edges).
`assemble.py` is the canonical reference assembly that wires the spec
into a `StateGraph`.

The four bound tools import the primitive and update the typed state.
The three absent-body tools raise `NotImplementedError` after opening
their span and audit record. Operators wire the absent-body tools to
their own runtime, or swap any node for an LLM-driven callable that
fills the agentic hook (the natural seam is the free-text fields on
the final-report submission, where `primitives.signatures` provides
the DSPy schema).

The agentic-extension slot is provider-neutral by construction: the
compiler never embeds an LLM SDK, so the operator wires the hook to
self-hosted open-weights inference or to an EU-hosted managed endpoint
without regenerating the artifact. The framework-wide EU-resident LM
endpoint guard re-applies the check at process startup
(`_lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 5. Observability — OTel + AuditTrail in every target

Every emitted action — bound or absent-body — opens an OpenTelemetry
span and appends an `AuditRecord` to a context-local `AuditTrail`
*before* the primitive call or the `NotImplementedError`. The mirror
runs unconditionally, ahead of any OTLP exporter, so the audit
property holds even when the operator has not configured a collector
— typical for disconnected, sovereign, or air-gapped deployments.

Span attributes use the shared `secops_ng.*` keyspace and are stable
across the three targets:

| Attribute key                | Carries                                              |
|------------------------------|------------------------------------------------------|
| `secops_ng.playbook.id`      | CACAO playbook id (`playbook--…`).                   |
| `secops_ng.playbook.version` | Content version pinned in the playbook.              |
| `secops_ng.step.id`          | CACAO step id (`action--…`).                         |
| `secops_ng.step.name`        | Human-readable step label.                           |
| `secops_ng.step.type`        | CACAO step type (`action`, `if-condition`, …).       |
| `secops_ng.tool.name`        | Emitted tool / activity / Code-node function name.   |
| `secops_ng.compile.target`   | `n8n` / `temporal` / `langgraph` discriminator.      |

Span boundaries per target:

- **n8n** — the compiled workflow is a snapshot of intent; OTel
  instrumentation is a per-node operator concern, documented per
  node-id, not a runtime guarantee of the emitted JSON.
- **Temporal** — workflow span (`workflow.<stable_id>`) at workflow
  entry; activity span (`activity.<step_id>`) on every activity body,
  with retries opening a fresh child span per Temporal attempt.
- **LangGraph** — node span (`node.<step_id>`) wrapping every node
  assembled in `assemble.py`; tool span (`tool.<step_id>`) inside the
  `@tool` wrapper. The node span is the parent of the tool span so a
  trace shows one `node.*` per step with the matching `tool.*` child.

The OTLP exporter endpoint is operator-supplied
(`OTEL_EXPORTER_OTLP_ENDPOINT`). The compiler never sets a default
endpoint and never imports a vendor SDK; pointing the exporter at a
managed APM is a downstream choice the operator owns end-to-end. The
sovereignty posture asks for an EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline.

## 6. Replay and audit story

Two replay properties are pinned for incident-management.

**Same-target deterministic replay** —
`tests/examples/test_incident_management_replay.py` feeds the same
intake signal envelope through one compile target twice and asserts
the bound primitives produce byte-identical state. The
`ClassificationVerdict.inputs_digest` and the
`StageVerdict.inputs_digest` are the single strings the test compares;
the F-PT-02 timeline adapter's `_digest(...)` of the timeline anchor
is the third. Determinism is a property of the policy, not of the
runtime.

**Cross-target byte-parity replay** —
`tests/examples/test_incident_management_happy_path.py` runs the same
intake signal through n8n + Temporal + LangGraph and asserts the bound
CORE outputs match across all three. The three targets call the same
Python primitives through three different orchestrator idioms; the
shared digests are what a regulator diffs to confirm the property held.

The byte-parity drift guards under
`tests/examples/incident_management/` pin each committed worked
example to a fresh emitter run from the canonical CACAO source plus
the per-target overlay. If the compiler or the playbook changes,
regenerate via the per-target `regenerate.sh` and commit the diff
intentionally; the drift guard flips green again.

## 7. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys, no
  regulator endpoints. Connectors and regulator destinations are
  operator-bound at runtime against environment variables documented
  per target; the framework ships no default endpoint per the
  sovereign-stack constraint.
- **Deployment topology.** Worker concurrency, retry policies beyond
  the per-activity defaults, persistence backends, n8n hosting,
  LangGraph host process model — those are runtime concerns the
  operator applies in their own assembly.
- **Late final-report re-entry.** When the root-cause and applied-
  mitigations narrative for the final report is not ready by the
  one-month boundary, the playbook closes the timeline with a
  deferred-final-report marker. The late submission ships through a
  separate operator-driven re-entry that is intentionally out of
  scope for this entry.
- **Per-deployment YAML.** This playbook ships no separate
  operator-facing `config.yaml`; per-case inputs are the CACAO
  `playbook_variables` block bound at compile time via the standard
  `__double_underscore__` substitution.

## 8. References

- [`content/playbooks/incident-management/playbook.cacao.json`](../../content/playbooks/incident-management/playbook.cacao.json)
  — canonical CACAO source.
- [`content/playbooks/incident-management/README.md`](../../content/playbooks/incident-management/README.md)
  — workflow-local module tree.
- [`examples/n8n/incident-management/README.md`](../../examples/n8n/incident-management/README.md)
- [`examples/temporal/incident-management/README.md`](../../examples/temporal/incident-management/README.md)
- [`examples/langgraph/incident-management/README.md`](../../examples/langgraph/incident-management/README.md)
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
