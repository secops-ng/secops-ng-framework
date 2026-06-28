# patch_management — cookbook walkthrough

Per-update coordinated patch / update rollout workflow against the
operator's own deployed estate. The `playbook.patch_management@v1`
CACAO playbook fires once per security update available against a
tracked package / image / firmware line: it ingests the advisory
against the operator's documented deployment-inventory row, classifies
the update against the operator's documented patch-criticality
taxonomy (security-critical, security-routine, feature-only), stages
the rollout to the canary cohort of the operator's documented
deployment-ring topology, validates the canary against the documented
health gates (functional probes, error-rate / latency deviation,
rollback readiness), fans out to the remaining rings on a green
canary, captures the dated patch-application evidence record, and
notifies the documented maintenance owner. The workflow operationalises
the per-event maintenance-rollout posture against pre-bound update
channels and ring cohorts; it does not author the operator's
patch-distribution architecture itself.

The regulatory anchor is NIS2 Article 21(2)(e) — security in
acquisition, development and maintenance — pinned by the
`nis2:art-21-2-e` mapping entry in
[`content/mappings/nis2/article-21-2-e.yaml`](../../content/mappings/nis2/article-21-2-e.yaml).
DORA Article 9(4)(a) (ICT protection and prevention, per-event
maintenance / patch-rollout slice, exercised under the JC RTS on ICT
risk management framework Commission Delegated Regulation
(EU) 2024/1774 Article 10 — vulnerability and patch management
procedures, including testing and rollback) is the co-anchored
inbound entry at
[`content/mappings/dora/article-9-maintenance-patch-rollout.yaml`](../../content/mappings/dora/article-9-maintenance-patch-rollout.yaml)
(`dora:art-9-maintenance-patch-rollout`). The CRA Annex I §2
security-updates binding for the per-event maintenance-rollout side
against the operator's own deployed estate is closed at
[`content/mappings/cra/annex-i-2-security-updates-rollout.yaml`](../../content/mappings/cra/annex-i-2-security-updates-rollout.yaml)
(`cra:annex-i-2-security-updates-rollout`); the CRA Annex I §2(7)
dissemination-cadence side is anchored separately against
`playbook.vuln_intake@v1`. The artifact shape is
[`schemas/evidence/patch.schema.json`](../../schemas/evidence/patch.schema.json)
(stream: `patch`).

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the deterministic
primitives package and the per-target adapter live in each.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/patch_management/
├── README.md                    # workflow-local module tree
├── mappings.yaml                # outbound playbook-mappings overlay
├── playbook.cacao.json          # canonical CACAO v2 source (playbook.patch_management@v1)
└── primitives/
    ├── detect.py                # detect_patch_availability — detect-patch-availability
    ├── classify.py              # classify_patch_criticality — classify-patch-criticality
    ├── stage.py                 # stage_rollout_to_canary_ring — stage-rollout-to-canary-ring
    ├── validate.py              # validate_canary — validate-canary
    ├── fanout.py                # fan_out_to_broad_rings — fan-out-to-broad-rings
    └── artifact.py              # build_patch_application_evidence_artifact — evidence-capture

schemas/evidence/patch.schema.json
                                  # per-execution patch-application evidence artifact schema (stream: patch)

content/controls/control.patch_evidence@v1.yaml
                                  # OSCAL SI-2 / SI-2(2) anchor and CRA Annex I §2 cross-reference

content/mappings/gdpr/data-flow-patch_management.md
                                  # GDPR Art. 30 Record of Processing Activity entry for this workflow
```

The CACAO source is canonical. The primitives package is the
deterministic policy the playbook *means*. The three worked examples
under `examples/{n8n,temporal,langgraph}/patch_management/` are the
same playbook compiled into three orchestrator idioms. Everything
else — runtime, advisory-intake surface (vendor feeds, distribution-
channel release notifications, upstream package-registry events),
patch-criticality enrichment endpoints, distribution-channel push
endpoints, canary-health probe endpoints, evidence sink, and the
maintenance-owner notification channel — is the operator's data plane.

The CACAO source ships as JSON
(`content/playbooks/patch_management/playbook.cacao.json`); the three
worked examples each carry a mirror copy at
`examples/{n8n,temporal,langgraph}/patch_management/playbook.cacao.json`
that is byte-identical to the canonical and refreshed by the
per-target `regenerate.sh`.

## 2. CACAO topology and primitives binding

The playbook ships nine steps: one `start`, seven `action`, one `end`.
Six core-bound action steps declare an `x_secops_ng.core_body`
reference into the deterministic primitives package. The notify step
is an operator-bound runtime seam (dispatch on the documented
maintenance-owner channel) and carries no `core_body` binding — the
framework does not ship a default endpoint.

| Step suffix | Step                                  | `core_body` binding                                                              | Status         |
|-------------|---------------------------------------|----------------------------------------------------------------------------------|----------------|
| `…000001`   | start                                 | edge wiring only — no body                                                       | n/a            |
| `…000002`   | detect-patch-availability             | `primitives.detect.detect_patch_availability`                                    | bound          |
| `…000003`   | classify-patch-criticality            | `primitives.classify.classify_patch_criticality`                                 | bound          |
| `…000004`   | stage-rollout-to-canary-ring          | `primitives.stage.stage_rollout_to_canary_ring`                                  | bound          |
| `…000005`   | validate-canary                       | `primitives.validate.validate_canary`                                            | bound          |
| `…000006`   | fan-out-to-broad-rings                | `primitives.fanout.fan_out_to_broad_rings`                                       | bound          |
| `…000007`   | evidence-capture                      | `primitives.artifact.build_patch_application_evidence_artifact`                  | bound          |
| `…000008`   | notify-maintenance-owner              | operator-bound runtime seam — dispatch on the documented owner channel           | operator-bound |
| `…000009`   | end                                   | edge wiring only — no body                                                       | n/a            |

Transitions are deterministic — each state declares exactly one
`on_completion` successor, no conditional branching at the CACAO
layer. The canary-unhealthy branch is encoded in the fan-out step's
primitive (skip path with the explicit `broad_rollout_skip_reason =
"canary_unhealthy"` marker), not in a CACAO `playbook-condition`
step; the evidence-capture and notify steps still execute and the
maintenance owner is paged with the failure marker rather than the
failure being discovered later. One per-update execution emits
exactly one patch-application evidence record.

## 3. Deterministic primitives — the contract

The advisory normalisation against the operator's tracked deployment-
inventory, the closed patch-criticality classification taxonomy with
its `unclassified` short-circuit sentinel, the SHA-256-keyed
`staged_ring_id` and `broad_rollout_id` derivations, the closed
canary health-gate evaluation, the closed patch-application evidence
shape the schema pins, and the `artifact_id` recipe are **code, not
configuration**. They live in
`content/playbooks/patch_management/primitives/`. Operators who need
to diverge fork the primitive module; they do not override it via
runtime config.

The six bindings exercised today:

`detect_patch_availability(update_subject, update_reference, deployment_inventory_row) -> PatchAdvisoryObservation`
:   The `detect-patch-availability` step normalises the advisory
    observation that landed on the operator's documented advisory-
    intake surface (vendor feed, distribution channel, upstream
    release notification) against the operator-supplied tracked
    deployment-inventory row and emits a canonical update-subject +
    update-reference record alongside the `advisory_kind` and the
    `in_scope` marker. Read-only against both surfaces — no network,
    no clock, no vendor SDK. The deployment-inventory row supplies
    the ring topology and the patch-criticality taxonomy the
    downstream steps will classify against; the framework authors
    neither.

`classify_patch_criticality(update_subject, update_reference, severity_band, exploit_status, *, deadline_missed=False) -> str`
:   The `classify-patch-criticality` step resolves the update against
    the operator's documented patch-criticality taxonomy over the
    closed severity-band + exploit-status + feature-only inputs. The
    closed vocabulary is `security-critical`, `security-routine`,
    `feature-only`:

    - `security-critical` — exploitation observed or imminent; rollout
      deadline measured in hours / days.
    - `security-routine` — vulnerability addressed; no observed
      exploitation; rollout deadline measured in days / weeks.
    - `feature-only` — non-security update; rollout cadenced against
      the operator's documented maintenance window.

    The classification is best-effort and time-boxed. When the
    documented intake deadline elapses the primitive is invoked with
    `deadline_missed=True` and emits the sentinel `"unclassified"`
    so the operator is not held by a perfect-classification stall
    while the rollout deadline slips; the downstream stage-rollout
    step treats the `unclassified` sentinel (and the empty wire shape)
    as `security-critical` for scheduling purposes rather than
    waiting. Output is sorted-stable so two replays of the same
    inputs collapse to byte-identical bytes.

`stage_rollout_to_canary_ring(update_subject, update_reference, ring_topology, patch_criticality) -> str`
:   The `stage-rollout-to-canary-ring` step derives a SHA-256
    `staged_ring_id` over the canonical `(update_subject,
    update_reference, canary_ring, cadence)` tuple, where the canary
    cohort is the second entry of the operator's documented
    `test / canary / broad` ring topology and the cadence is selected
    by the classified `__patch_criticality__` (`security-critical →
    immediate`, `security-routine → next-window`, `feature-only →
    maintenance-window`; the `unclassified` sentinel and the empty
    wire shape both map to `immediate`). The compile target's runtime
    engages the update against the operator's distribution channel
    upstream; the primitive only emits the durable identifier. Two
    replays of the same `(update, ring, cadence)` produce byte-
    identical ids.

`validate_canary(functional_probe, error_rate_within_threshold, latency_within_threshold, rollback_ready) -> bool`
:   The `validate-canary` step evaluates the closed health-gate inputs
    (`functional_probe` in `{green, red, unknown}`, three booleans for
    error-rate / latency / rollback-readiness) and emits
    `__canary_healthy__ = True` iff the functional probe is green and
    all three threshold gates are true. The compile target's runtime
    reads the documented canary-health endpoints upstream; the
    primitive only evaluates the resulting closed gate combination.
    A `False` outcome does not block downstream steps — the evidence
    record is published with the failure marker, the fan-out step
    takes the deterministic skip path, and the notify step pages the
    maintenance owner with full context so the next maintenance lever
    (rollback the canary, escalate the advisory, hold the broad
    rollout) can be engaged.

`fan_out_to_broad_rings(update_subject, update_reference, staged_ring_id, broad_rings, canary_healthy) -> FanOutResult`
:   The `fan-out-to-broad-rings` step derives a SHA-256
    `broad_rollout_id` over the canonical `(update_subject,
    update_reference, staged_ring_id, sorted broad_rings)` tuple on
    a healthy canary; on an unhealthy canary the step is the
    deterministic skip path leaving `__broad_rollout_id__` empty with
    the explicit `broad_rollout_skip_reason = "canary_unhealthy"`
    marker so the evidence-capture step records the skip in the
    audit-evident chain without forcing the broad rollout against a
    failing canary. The compile target's runtime engages the update
    against the operator's distribution channel upstream; the
    primitive only emits the durable identifier or the skip marker.

`build_patch_application_evidence_artifact(workflow_id, execution_id, regulation_refs, control_refs, update_subject, update_reference, patch_criticality, staged_ring_id, canary_healthy, health_observations, broad_rollout_id, broad_rollout_skip_reason, captured_at, source_url, ...) -> PatchEvidenceArtifact`
:   The `evidence-capture` step shapes the JSON-native patch-
    application evidence record against
    [`schemas/evidence/patch.schema.json`](../../schemas/evidence/patch.schema.json).
    The deterministic `artifact_id` derives from
    `SHA-256(<workflow_id>|<execution_id>|<captured_at>)` (UTF-8, no
    separators around the pipes). `compile_target` is intentionally
    **not** part of the id — the three reference compilers (n8n,
    Temporal, LangGraph) re-derive byte-identical bytes from the same
    primitive output, and the cross-target byte-parity contract the
    F-WF-PATCH CORE-FANOUT siblings assert against holds across
    targets. The skip-marker invariant (`broad_rollout_id` empty iff
    `broad_rollout_skip_reason == "canary_unhealthy"`) and the
    `canary_healthy ↔ gate-combination` invariant are re-validated at
    the primitive boundary so an inconsistent record fails loud at
    emission rather than at schema-validation downstream.

The `artifact_id` derivation deliberately omits `compile_target` —
this is the same shape the asset_management evidence record uses, and
the inverse of the posture-evidence and incidents streams which key
on `compile_target` so each target produces its own artifact under
its own id. For patch_management, an operator running the same
per-update execution under more than one target emits the **same**
artifact bytes at the **same** path; cross-target duplication is
treated as redundant emission, not as a discriminator. Downstream
consumers join on `(workflow_id, execution_id)` and dedupe on
`artifact_id`.

> **LM determinism.** Advisory normalisation, criticality
> classification, ring derivation, canary-health evaluation, fan-out
> derivation, and evidence shaping are code, not LM. The
> patch_management playbook does not bind any DSPy signature — there
> is no free-text step at this layer. The advisory-intake read, the
> severity / exploit-status enrichment lookup, the canary-health probe
> read, and the maintenance-owner notification are mechanical walks of
> the operator's documented surfaces, not LM judgements. See
> [`docs/FOUNDATION.md`](../FOUNDATION.md) § LLM determinism.

## 4. Per-target hand-off

The deterministic primitives package shipped under CORE-PRIM; the per-
target evidence-emitter wiring (artifact-path, content-addressed
filename, atomic write) is owned by the F-WF-PATCH CORE-FANOUT sibling
cards and lands with that work. Until the CORE-FANOUT siblings ship,
the three worked-example artifacts under
`examples/{n8n,temporal,langgraph}/patch_management/` carry the CACAO
topology with the primitive call documented per action and the bodies
left as integrator seams (`NotImplementedError` stubs on the Temporal
and LangGraph stubs, editable Set rows on the n8n side). Each
worked example also ships a `regenerate.sh` that mirrors the canonical
CACAO source into the example folder and re-emits the per-target
artifact via `tools.compile`; running it from the repo root yields
byte-identical output, which is the property the per-target byte-
parity goldens assert against once the CORE-FANOUT siblings land.

### 4.1 n8n — operator-edited Set rows + Code-node bindings

`examples/n8n/patch_management/workflow.n8n.json` carries the CACAO
topology as n8n nodes (`manualTrigger`, `set`, `noOp`), with node ids
preserving the CACAO step ids verbatim. The seven action steps emit
`n8n-nodes-base.set` nodes carrying the CACAO I/O contract as
editable assignment rows — the n8n target ships as a **snapshot of
intent**, and the operator binds the Set rows to their own connectors
in their n8n instance:

- `detect-patch-availability` → advisory-intake surface (vendor feed,
  distribution channel, upstream release notification; HTTP / queue
  connector per source) + deployment-inventory row lookup.
- `classify-patch-criticality` → Python-runner Code node invoking
  `content.playbooks.patch_management.primitives.classify.classify_patch_criticality`
  on the canonicalised severity-band + exploit-status enrichment.
- `stage-rollout-to-canary-ring` → Python-runner Code node invoking
  `content.playbooks.patch_management.primitives.stage.stage_rollout_to_canary_ring`,
  followed by the operator's distribution-channel push call against
  the canary cohort.
- `validate-canary` → Python-runner Code node invoking
  `content.playbooks.patch_management.primitives.validate.validate_canary`
  on the observations read from the operator's documented canary-
  health endpoints (functional probes, error-rate / latency series,
  rollback-readiness attestation).
- `fan-out-to-broad-rings` → Python-runner Code node invoking
  `content.playbooks.patch_management.primitives.fanout.fan_out_to_broad_rings`,
  followed by the operator's distribution-channel push call against
  the remaining rings on a green canary.
- `evidence-capture` → `executeCommand` node calling the per-target
  patch-evidence adapter once it ships with CORE-FANOUT (the adapter
  routes the typed payload through the workflow-local primitive at
  `content.playbooks.patch_management.primitives.artifact` and writes
  the artifact bytes atomically via `os.replace` through a sibling
  `.tmp`).
- `notify-maintenance-owner` → operator's maintenance-owner
  notification channel (ticketing webhook, chat thread, change-
  management board connector).

The Code-node body for the bound steps assumes `PYTHONPATH` on the
n8n host resolves `content.playbooks.patch_management.primitives`;
operators who run n8n in a Python-free container drop a Python-runner
Code node ahead of the Set node. n8n is the **no-code** target; the
per-update trigger is the operator's webhook / advisory-intake feed
adapter at the front of the imported workflow. The compiled artefact
is a snapshot of intent — the operator wires the trigger, the
credential bindings on the advisory-intake and enrichment reads, the
distribution-channel push endpoints, the canary-health probe reads,
the evidence directory, and the maintenance-owner notification
channel in their own n8n instance.

### 4.2 Temporal — `@activity.defn` bodies with retry policy

`examples/temporal/patch_management/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action. Each activity docstring
names the primitive (or operator-bound seam) the activity discharges;
the bodies of the committed stub raise `NotImplementedError` pending
the worker-translator slice, so the operator wires the activity
implementations in their own assembly. The six core-bound activities
(`detect-patch-availability`, `classify-patch-criticality`,
`stage-rollout-to-canary-ring`, `validate-canary`,
`fan-out-to-broad-rings`, `evidence-capture`) document the primitive
call against the deterministic body under
`content.playbooks.patch_management.primitives.{detect,classify,stage,validate,fanout,artifact}`;
the notify activity documents the operator-bound seam (no default
endpoint).

The sibling `_audit_mirror.py` carries the `AuditRecord` /
`AuditTrail` types — no `compilers.*` import in the emitted artifact,
so the worker module is a self-contained drop-in. Temporal is the
natural fit for the per-update rollout shape: each per-update
execution becomes one workflow run; the canary-validation window
becomes a Temporal timer; replay against the same Temporal event
history re-derives the same `artifact_id`. The per-update execution
is the unit a regulator-facing reviewer reads the artifact series
back against.

### 4.3 LangGraph — `@tool` wrappers + agentic-extension hook

`examples/langgraph/patch_management/state_bindings.py` carries the
`TypedDict` state and the `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (nodes, edges);
`assemble.py` is the hand-written reference assembly that wires the
GraphSpec + bindings into a `langgraph.graph.StateGraph`. The
committed `state_bindings.py` is a generated stub: each tool's
docstring names the primitive (or operator-bound seam) it discharges
and the body raises `NotImplementedError` until a human integrator
wires it to the operator's runtime — the six core-bound tools
(`detect-patch-availability`, `classify-patch-criticality`,
`stage-rollout-to-canary-ring`, `validate-canary`,
`fan-out-to-broad-rings`, `evidence-capture`) document the primitive
call against
`content.playbooks.patch_management.primitives.{detect,classify,stage,validate,fanout,artifact}`,
and the notify tool documents the operator-bound seam.

LangGraph is the agentic target — the natural seam an operator extends
with an LLM-driven node is *out of band* for this workflow. Advisory
normalisation, criticality classification, ring derivation, canary-
health evaluation, fan-out derivation, and evidence shaping are
mechanical walks of the operator's documented surfaces, not free-text
reasoning steps; adding an agentic hook here would defeat the
determinism the patch-application evidence record relies on. The
compiler never embeds an LLM SDK; the framework-wide EU-resident LM
endpoint guard re-applies the check at process startup
(`compilers/_shared/lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

### 4.4 Regenerating the worked examples

After any change to the canonical playbook or to a per-target
compiler module, refresh the committed artifacts from the repo root:

```sh
./examples/n8n/patch_management/regenerate.sh
./examples/temporal/patch_management/regenerate.sh
./examples/langgraph/patch_management/regenerate.sh
```

Each script mirrors the canonical CACAO source into the example folder
and re-emits the per-target artifact via `tools.compile --target
{n8n,temporal,langgraph}`. The drift tests under
`tests/examples/patch_management/` (landing with the CORE-FANOUT
siblings) fail the suite if the committed artifacts diverge from a
fresh regeneration, so the worked examples stay honest as the
compilers evolve.

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
  assembled from `graph_spec.json`; tool span (`tool.<step_id>`)
  inside the `@tool` wrapper.

The OTLP exporter endpoint is operator-supplied
(`OTEL_EXPORTER_OTLP_ENDPOINT`). The compiler never sets a default and
never imports a vendor SDK; pointing the exporter at a managed APM is
a downstream choice the operator owns end-to-end. The sovereignty
posture asks for an EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline.

## 6. Metrics — what the rollout posture exposes

Three KPI / KRI entries surface the patch_management rollout posture
to the operator's metrics dashboard. The catalogue entries live under
`content/metrics/` and read against the dated patch-application
evidence record the workflow emits.

- **`kri.patch_rollout_overdue_exposure@v1`** — count of security
  updates whose broad-ring rollout has not completed inside the
  documented per-criticality rollout deadline in the evaluation
  window. The KRI surfaces the unmitigated-exposure tail an
  Art. 21(2)(e) reviewer reads against the maintenance obligation.
  Catalogue: [`content/metrics/patch_rollout_overdue_exposure.yaml`](../../content/metrics/patch_rollout_overdue_exposure.yaml).
  Visualisation guidance: [`content/metrics/patch_rollout_overdue_exposure.viz.md`](../../content/metrics/patch_rollout_overdue_exposure.viz.md).
- **`kpi.patch_rollout_success_rate@v1`** — share of per-update
  executions in the evaluation window whose broad-ring rollout
  completed with the canary observed healthy (i.e. the
  `canary_healthy = true ∧ broad_rollout_id ≠ ""` slice over total
  executions). Catalogue:
  [`content/metrics/patch_rollout_success_rate.yaml`](../../content/metrics/patch_rollout_success_rate.yaml).
  Visualisation guidance: [`content/metrics/patch_rollout_success_rate.viz.md`](../../content/metrics/patch_rollout_success_rate.viz.md).
- **`kpi.patch_disseminated_on_time@v1`** — share of per-update
  executions in the evaluation window whose broad-ring rollout
  completed inside the documented per-criticality deadline (the
  on-time-rate complement to the overdue-exposure KRI). Catalogue:
  [`content/metrics/patch_disseminated_on_time.yaml`](../../content/metrics/patch_disseminated_on_time.yaml).
  Visualisation guidance: [`content/metrics/patch_disseminated_on_time.viz.md`](../../content/metrics/patch_disseminated_on_time.viz.md).

The three metrics read the same evidence stream the workflow emits;
no separate metric-emitter wiring is layered onto the runtime path.
Operators dashboard the KPI / KRI series against their own metrics
backend (Prometheus, OTLP-receiving collector, evidence-store query
layer) — the catalogue entries pin the field-level read contract;
the framework does not ship a hosted dashboard.

## 7. Replay and audit story

Two replay properties are pinned for patch_management.

**Per-execution deterministic replay** — the workflow-local primitive
at `content.playbooks.patch_management.primitives.artifact` produces a
byte-identical record on every re-emission against the same execution
context. The record `artifact_id` is
`SHA-256(workflow_id|execution_id|captured_at)`; the `staged_ring_id`
re-derives the same SHA-256 over the same `(update_subject,
update_reference, canary_ring, cadence)` tuple, and the
`broad_rollout_id` re-derives the same SHA-256 over the same
`(update_subject, update_reference, staged_ring_id, sorted
broad_rings)` tuple on a healthy canary.

**Per-target byte-stable goldens, cross-target byte-parity** — once
the F-WF-PATCH CORE-FANOUT siblings ship the per-target byte-parity
goldens at `tests/examples/patch_management/test_{n8n,temporal,langgraph}_workflow_golden.py`
and the per-target patch-application evidence goldens, each test will
pin (a) the per-target workflow artefact (`workflow.n8n.json` /
`workflow.temporal.py` / `graph_spec.json` + `state_bindings.py`),
(b) the per-target patch-application evidence record, and (c) the
byte-equality of the co-located CACAO mirror against the canonical
source under `content/playbooks/patch_management/`. Because
`artifact_id` is **not** keyed on `compile_target`, the three per-
target records resolve to the same `artifact_id` for the same
execution context — cross-target byte-parity is asserted on the bytes
of the record themselves, not on the path discriminator. If a
primitive or any per-target adapter changes, regenerate the worked
example via the per-target `regenerate.sh` and commit the diff
intentionally; the drift guard flips green again.

## 8. Regulatory traceability

The patch_management workflow closes the maintenance-rollout corner of
the framework's regulatory graph across three EU instruments. Each
inbound mapping file backlinks `playbook.patch_management@v1`;
[`content/playbooks/patch_management/mappings.yaml`](../../content/playbooks/patch_management/mappings.yaml)
pins the outbound side so the graph is closed in both directions.

- **NIS2 Article 21(2)(e)** — security in acquisition, development
  and maintenance. The patch_management playbook is the operational
  discharge of the maintenance limb against the operator's own
  deployed estate (the vulnerability-handling and SBOM-disclosure
  limbs of the same Article lean on `playbook.vuln_intake@v1` and
  `playbook.codebase_vuln_management@v1` respectively). Inbound:
  [`content/mappings/nis2/article-21-2-e.yaml`](../../content/mappings/nis2/article-21-2-e.yaml)
  (`nis2:art-21-2-e`).
- **DORA Article 9(4)(a)** — ICT protection and prevention, per-event
  maintenance / patch-rollout slice. The operative Level 2 detail is
  Commission Delegated Regulation (EU) 2024/1774 (JC RTS on ICT risk
  management framework) Article 10 — vulnerability and patch
  management procedures, including testing and rollback. The
  patch_management playbook materialises the per-event maintenance
  slice of that obligation against the operator's deployed estate:
  detect-classify-stage-validate-fan-out against the documented ring
  topology with a dated patch-application evidence record. The
  per-event maintenance / patch-rollout slice is mapped separately
  from the vulnerability-handling lifecycle anchor
  (`dora:art-9-vuln-mgmt` on the inbound CVD-intake side) so the
  inbound graph stays atom-per-obligation. Inbound:
  [`content/mappings/dora/article-9-maintenance-patch-rollout.yaml`](../../content/mappings/dora/article-9-maintenance-patch-rollout.yaml)
  (`dora:art-9-maintenance-patch-rollout`).
- **CRA Annex I §2** — security updates throughout the declared
  support period. The §2(7) dissemination-cadence side (update +
  advisory pair produced by the coordinated-disclosure intake
  surface) is anchored separately at `cra:annex-i-2-security-updates`
  against `playbook.vuln_intake@v1`; the per-event maintenance-
  rollout side against the operator's own deployed estate is what
  patch_management operationalises and is the closure landed in this
  cookbook scope. Inbound:
  [`content/mappings/cra/annex-i-2-security-updates-rollout.yaml`](../../content/mappings/cra/annex-i-2-security-updates-rollout.yaml)
  (`cra:annex-i-2-security-updates-rollout`).
- **GDPR Article 30 (Record of Processing Activity)** — the workflow
  operates on deployment-inventory identifiers, advisory references,
  ring-cohort identifiers, and attestation records. No personal data
  is processed; the per-workflow Record of Processing Activity entry
  at
  [`content/mappings/gdpr/data-flow-patch_management.md`](../../content/mappings/gdpr/data-flow-patch_management.md)
  pins the no-personal-data posture explicitly.

The OSCAL anchor across all three instruments is
[`control.patch_evidence@v1`](../../content/controls/control.patch_evidence@v1.yaml)
(NIST SP 800-53 Rev. 5 SI-2 and SI-2(2) — Flaw Remediation and
Automated Flaw Remediation Status). The D3FEND closure pins
[`D3-OAM`](https://d3fend.mitre.org/technique/d3f:OperationalActivityMapping/)
on the detect step (operational vulnerability / advisory data intake),
[`D3-SYSVA`](https://d3fend.mitre.org/technique/d3f:SystemVulnerabilityAssessment/)
on the classify step (CVSS / EPSS / exploit-status enrichment), and
[`D3-SU`](https://d3fend.mitre.org/technique/d3f:SoftwareUpdate/) on
both the stage and fan-out steps (engaging the update against the
operator's documented distribution channel). The validate, evidence-
capture, and notify steps are deliberately not pinned to a single
D3FEND tag — rationale is documented in the header comment of the
playbook's `mappings.yaml`.

## 9. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys. The
  advisory-intake surface, the patch-criticality enrichment endpoints,
  the distribution-channel push endpoints, the canary-health probe
  endpoints, the patch-application evidence sink, and the maintenance-
  owner notification channel are all operator-bound at runtime against
  environment variables documented per target; the framework ships no
  default endpoint and bundles no hosted patch-distribution SaaS per
  the sovereign-stack posture.
- **Patch-distribution architecture.** This playbook consumes the
  documented deployment-ring topology and update-channel set the
  operator already maintains — it does not author either. Which
  package mirror the operator runs, which image registry they treat
  as authoritative, which firmware-distribution surface they consume,
  and the ring-cohort composition between `test / canary / broad` are
  upstream operator concerns out of scope for this workflow. The
  framework commits to the per-event rollout contract, not the
  distribution-architecture composition.
- **Change-management process.** OSCAL CM-3 (Configuration Change
  Control) is deliberately not pinned: the playbook operationalises
  the per-update rollout slice, not the operator's standing change-
  management process. The change-control plan-authoring surface
  lives in governance documentation; pinning CM-3 here would
  conflate the per-event rollout discipline with the plan-authoring
  surface.
- **Vulnerability scanning / advisory ingestion.** OSCAL RA-5 is
  deliberately not pinned: vulnerability scanning and advisory
  ingestion are the upstream of the patch_management trigger surface,
  anchored by `playbook.vuln_intake@v1` and
  `playbook.codebase_vuln_management@v1` in their own overlays.
- **Deployment topology.** Worker concurrency, retry policies beyond
  the per-activity defaults, persistence backends, n8n hosting, the
  scheduler driving the advisory intake, LangGraph host process
  model — those are runtime concerns the operator applies in their
  own assembly.
- **Personal data in patch records.** Operator-side patch records may
  carry deployment-inventory identifiers, advisory references, ring-
  cohort identifiers, and attestation records; per AGENTS.md §3 they
  MUST stay role-shaped or opaque. Individual personal names,
  credential-shaped strings, and raw configuration secret material
  are out of scope and rejected at the schema boundary. The GDPR
  Record of Processing Activity entry accompanying this overlay
  ([`content/mappings/gdpr/data-flow-patch_management.md`](../../content/mappings/gdpr/data-flow-patch_management.md))
  pins the no-personal-data posture explicitly.
- **Per-deployment YAML.** This playbook ships no separate operator-
  facing `config.yaml`; per-update inputs are the CACAO
  `playbook_variables` block bound at compile time via the standard
  `__double_underscore__` substitution.

## 10. References

- [`content/playbooks/patch_management/playbook.cacao.json`](../../content/playbooks/patch_management/playbook.cacao.json)
  — canonical CACAO source.
- [`content/playbooks/patch_management/README.md`](../../content/playbooks/patch_management/README.md)
  — workflow-local module tree.
- [`content/playbooks/patch_management/mappings.yaml`](../../content/playbooks/patch_management/mappings.yaml)
  — outbound playbook-mappings overlay (OSCAL SI-2 / SI-2(2),
  D3FEND D3-OAM / D3-SYSVA / D3-SU, OCSF API Activity,
  NIS2 Art. 21(2)(e), DORA Art. 9(4)(a) maintenance / patch-rollout,
  CRA Annex I §2 security-updates-rollout inbound closures).
- [`schemas/evidence/patch.schema.json`](../../schemas/evidence/patch.schema.json)
  — per-execution patch-application evidence artifact schema
  (stream: `patch`).
- [`content/controls/control.patch_evidence@v1.yaml`](../../content/controls/control.patch_evidence@v1.yaml)
  — OSCAL SI-2 / SI-2(2) anchor and CRA Annex I §2 cross-reference.
- [`content/mappings/nis2/article-21-2-e.yaml`](../../content/mappings/nis2/article-21-2-e.yaml)
  — NIS2 Art. 21(2)(e) mapping; entry `nis2:art-21-2-e` is the
  security-in-acquisition-development-and-maintenance anchor.
- [`content/mappings/dora/article-9-maintenance-patch-rollout.yaml`](../../content/mappings/dora/article-9-maintenance-patch-rollout.yaml)
  — DORA Art. 9(4)(a) mapping; entry
  `dora:art-9-maintenance-patch-rollout` is the per-event
  maintenance / patch-rollout slice anchor.
- [`content/mappings/cra/annex-i-2-security-updates-rollout.yaml`](../../content/mappings/cra/annex-i-2-security-updates-rollout.yaml)
  — CRA Annex I §2 mapping; entry
  `cra:annex-i-2-security-updates-rollout` is the per-event
  maintenance-rollout side against the operator's deployed estate.
- [`content/mappings/gdpr/data-flow-patch_management.md`](../../content/mappings/gdpr/data-flow-patch_management.md)
  — GDPR Article 30 Record of Processing Activity entry.
- [`content/metrics/patch_rollout_overdue_exposure.yaml`](../../content/metrics/patch_rollout_overdue_exposure.yaml)
  — KRI catalogue entry (overdue-exposure tail).
- [`content/metrics/patch_rollout_success_rate.yaml`](../../content/metrics/patch_rollout_success_rate.yaml)
  — KPI catalogue entry (broad-rollout success rate).
- [`content/metrics/patch_disseminated_on_time.yaml`](../../content/metrics/patch_disseminated_on_time.yaml)
  — KPI catalogue entry (on-time dissemination rate).
- [`examples/n8n/patch_management/regenerate.sh`](../../examples/n8n/patch_management/regenerate.sh)
- [`examples/temporal/patch_management/regenerate.sh`](../../examples/temporal/patch_management/regenerate.sh)
- [`examples/langgraph/patch_management/regenerate.sh`](../../examples/langgraph/patch_management/regenerate.sh)
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
