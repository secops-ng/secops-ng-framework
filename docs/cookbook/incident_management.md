# incident_management — cookbook walkthrough

NIS2 Article 23 three-stage incident reporting. The
`playbook.incident_management@v1` CACAO playbook intakes a significant
incident signal handed in by an upstream workflow (an alert_triage
close-out, a ransomware_containment close-out, or an operator-raised
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
content/playbooks/incident_management/
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
(`content/playbooks/incident_management/playbook.cacao.json`) rather
than YAML; both shapes are first-class inputs to the per-target
compilers. The JSON is the single source of truth and the worked
examples each carry a mirror copy at
`examples/{n8n,temporal,langgraph}/incident_management/playbook.cacao.json`.

## 2. CACAO topology and primitives binding

The playbook ships 11 steps: one `start`, seven `action`, two
`if-condition`, one `end`. All seven action steps declare an
`x_secops_ng.core_body` reference into the deterministic primitives
package **on the canonical source** (the overlay era is closed — see
§ 2.1); the playbook is `stable` at `content_version` 1.0.0 under the
Maturity ladder.

| Step suffix | Step                                            | `core_body` binding (canonical source)                                         | Status   |
|-------------|-------------------------------------------------|--------------------------------------------------------------------------------|----------|
| `…000002`   | intake significant-incident signal              | `primitives.intake.derive_incident_id`                                         | bound    |
| `…000003`   | classify significance and cross-border scope    | `primitives.classification.classify_significance`                              | bound    |
| `…000004`   | significant? (if-condition)                     | edge wiring only — no body                                                     | n/a      |
| `…000005`   | open incident timeline                          | `primitives.timeline_binding.open_timeline`                                    | bound    |
| `…000006`   | submit 24-hour early warning                    | `primitives.regulator_submission.resolve_destination(stage='early_warning')`   | bound    |
| `…000007`   | submit 72-hour notification                     | `primitives.stage_clock.verdict_for_submission(stage='notification', ...)`     | bound    |
| `…000008`   | final-report material complete? (if-condition)  | edge wiring only — no body                                                     | n/a      |
| `…000009`   | submit 1-month final report                     | `primitives.regulator_submission.resolve_destination(stage='final_report')`    | bound    |
| `…00000a`   | close incident timeline                         | `primitives.timeline_binding.close_timeline`                                   | bound    |

The seven bindings are the byte-identical anchor the cross-target
replay property hangs off. The remaining `NotImplementedError` in the
emitted artifacts marks only operator-integration seams (submission
endpoints, notification channels — the connectors the operator
wires), which is emitter-standard across every bound playbook: span +
`AuditTrail` mirror prologue first, so the seam is identifiable at a
glance.

### 2.1 Single source of truth — the overlay era, closed

During the SKELETON wave the per-step bindings lived in a per-target
`core_body.overlay.json` layered onto each mirror at regeneration
time, with the canonical source deliberately binding-free. That seam
is **closed**: the `core_body` blocks were promoted onto the canonical
`playbook.cacao.json` as the single source of truth, the overlay
collapsed to empty, and the divergence guard was replaced — at its own
instruction — by a seam-closure test
(`tests/examples/test_n8n_incident_management.py::test_wave_seam_is_closed_and_mirror_is_byte_identical`)
that pins the overlay empty and the mirror byte-identical to the
canonical. A contributor re-introducing per-target divergence trips
that test instead of silently forking the source of truth.

One deliberate asymmetry persists in the shipped bindings: of the
three regulator-submission steps, two bind the fail-closed destination
resolver and one binds the stage-clock verdict — every primitive group
(stage-clock, classification, regulator-submission, timeline binding,
intake derivation) is exercised somewhere in the workflow, and the
operator wires the complementary primitive per step (the clock check
on the bound-destination steps, the destination resolution on the
bound-clock step) at the target's body layer.

## 3. Deterministic primitives — the contract

The significance and cross-border classification table, the three-stage
NIS2 Article 23 clock durations (24 hours, 72 hours, one month), the
fail-closed destination resolver, the timeline-binding adapter contract,
and the DSPy signature schema for free-text fields are **code, not
configuration**. They live in
`content/playbooks/incident_management/primitives/`. Operators who need
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

### 4.1 n8n — code-node bindings, operator-wired connectors

`examples/n8n/incident_management/workflow.n8n.json` carries the CACAO
topology as n8n nodes (`manualTrigger`, `code`, `if`, `noOp`), with
node ids preserving the CACAO step ids verbatim. All seven bound
action steps emit `n8n-nodes-base.code` nodes whose `pythonCode` is
the exact primitive call (e.g.
`from incident_management.primitives.classification import classify_significance ; __classification_verdict__ = classify_significance(__intake_signals__)`);
no Set-node placeholders remain.

Operators wire the Code-node inputs to their connectors:

- intake → upstream-workflow handoff envelope (alert_triage close-out,
  ransomware_containment close-out, or operator-raised ticket)
- open / close timeline → F-PT-02 incident-timeline pattern handle
  store (the operator's persistence backend for the timeline JSON)
- submit early-warning / notification / final-report → operator's
  regulator endpoint per stage, resolved out of
  `__notification_destinations__`

The Code-node bodies assume `PYTHONPATH` on the n8n host resolves
`incident_management.primitives`. Operators who run n8n in a
Python-free container drop a single Python-runner Code node ahead of
the chain; the wiring is documented in
[`examples/n8n/incident_management/README.md`](../../examples/n8n/incident_management/README.md)
under *Per-action wiring notes — CORE bodies*.

### 4.2 Temporal — `@activity.defn` bodies with retry policy

`examples/temporal/incident_management/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action. All seven activities
import their primitive and produce the canonical incident id /
classification verdict / timeline handle / destination handle / stage
verdict; the only remaining `NotImplementedError` marks the
operator-integration seams (submission endpoints, the timeline
persistence backend) so an integrator sees exactly which seam is
theirs.

Operators drop `workflow.temporal.py` next to their worker, register
the activities, and run the worker against their Temporal cluster.
The sibling `_audit_mirror.py` carries the `AuditRecord` / `AuditTrail`
types — no `compilers.*` import in the emitted artifact, so the worker
module is a self-contained drop-in.

Per-activity retry policies are emitted alongside the activities
(`<ACTIVITY>_RETRY_POLICY`) so the operator can pin them on the
`workflow.execute_activity` call sites in their worker assembly.

### 4.3 LangGraph — `@tool` wrappers + agentic-extension hook

`examples/langgraph/incident_management/state_bindings.py` carries the
`TypedDict` state, `@tool`-decorated action wrappers, and an
`AGENTIC_HOOK` slot for an LLM-driven node. `graph_spec.json` carries
the target-neutral topology (nodes, edges, conditional edges).
`assemble.py` is the canonical reference assembly that wires the spec
into a `StateGraph`.

All seven tools import their primitive and update the typed state;
the operator-integration seams stay marked with `NotImplementedError`
after their span and audit record. Operators wire those seams to
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

Every emitted action opens an OpenTelemetry
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

Two replay properties are pinned for incident_management.

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

## 6.1 DORA Art. 19 report variant (F-SV-03)

For operators in DORA scope, the incident-management workflow also
emits a **technical-incident report variant** consumable as a DORA
Art. 19 submission. The variant is a per-target overlay on the same
F-WF-05 timeline — no new playbook, no new schema beyond the variant
record shape.

- **Schema.** Report-variant record pinned at
  [`schemas/evidence/dora-art19-technical-incident-report.schema.json`](../../schemas/evidence/dora-art19-technical-incident-report.schema.json);
  report-milestone enum at
  [`schemas/dora_art19_report_milestone.json`](../../schemas/dora_art19_report_milestone.json)
  (initial / intermediate / final / deferred-final).
- **Per-target emitters.** Each compile target has its own emitter
  bound to the shared variant-field derivation:
  [`compilers/n8n/evidence/dora_art19_report_node.py`](../../compilers/n8n/evidence/dora_art19_report_node.py),
  [`compilers/temporal/evidence/dora_art19_report_activity.py`](../../compilers/temporal/evidence/dora_art19_report_activity.py),
  and
  [`compilers/langgraph/evidence/dora_art19_report_node.py`](../../compilers/langgraph/evidence/dora_art19_report_node.py).
  Shared derivation lives at
  [`compilers/_shared/evidence/dora_art19_report.py`](../../compilers/_shared/evidence/dora_art19_report.py).
- **Worked examples.** Per-target compiled examples land under
  `examples/{n8n,temporal,langgraph}/dora_art19_report/`.
- **Byte-parity goldens.** Drift guards under
  `tests/examples/dora_art19_report/` pin each target's emitter output
  to a committed golden so the report variant survives regulator diff.
  Variant-schema contract is pinned in
  `tests/content_model/test_dora_art19_report_variant_schema.py`.
- **Submission templates and major-incident classifier.** The
  operator-bound submission templates and the DORA major-incident
  classifier live as policy in
  [`content/controls/control.dora_submission_templates@v1.yaml`](../../content/controls/control.dora_submission_templates@v1.yaml)
  and
  [`content/controls/control.dora_major_classifier@v1.yaml`](../../content/controls/control.dora_major_classifier@v1.yaml).
- **Sovereign-stack note.** Submission destinations (the operator's
  competent authority endpoint) remain operator-configured at runtime;
  the framework ships no default endpoint and no submission transport.

The report variant is a downstream rendering — it does not change the
F-WF-05 timeline or the F-CR-04 incident-evidence record, and operators
outside DORA scope can ignore the emitters entirely.

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

- [`content/playbooks/incident_management/playbook.cacao.json`](../../content/playbooks/incident_management/playbook.cacao.json)
  — canonical CACAO source.
- [`content/playbooks/incident_management/README.md`](../../content/playbooks/incident_management/README.md)
  — workflow-local module tree.
- [`examples/n8n/incident_management/README.md`](../../examples/n8n/incident_management/README.md)
- [`examples/temporal/incident_management/README.md`](../../examples/temporal/incident_management/README.md)
- [`examples/langgraph/incident_management/README.md`](../../examples/langgraph/incident_management/README.md)
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
