# examples/temporal/alert-triage

Worked example: the `playbook.alert_triage@v1` CACAO v2 source playbook
compiled by the Temporal reference compiler. Operators who already run
Temporal can drop `workflow.temporal.py` into their worker module to
see the topology the emitter produces; binding the activity bodies for
the absent-body step (p4 informational — log and close) and the
operator-bound connectors (alert source, telemetry-context store,
suppression cache, response endpoints) is the operator's job.

The seven CORE action steps with a primitives binding (ingest, enrich,
suppress, classify, p1 / p2 / p3 response) emit `@activity.defn`
bodies that import the deterministic primitive directly; the single
absent-body step emits an `@activity.defn` that opens the span,
appends the audit record, and raises `NotImplementedError` so the
seam is visible at a glance.

## Source

Canonical CACAO playbook (YAML):

    ../../../content/playbooks/alert-triage.cacao.yaml

The YAML source carries scenario, regulatory anchors, control / metric
/ telemetry bindings, and the operator-supplied bindings. This folder
holds the emitted Temporal artifact, a byte-deterministic JSON mirror
of the YAML source (the Temporal emitter consumes JSON via the CACAO
parser), and the regeneration command.

## Files in this directory

| Path                    | Source compiler      | Format                |
|-------------------------|----------------------|-----------------------|
| `playbook.cacao.json`   | (input mirror)       | CACAO v2 JSON         |
| `workflow.temporal.py`  | `compilers.temporal` | Python (`temporalio`) |
| `regenerate.sh`         | n/a                  | regeneration script   |

The two formats round-trip through `yaml.safe_load` + `json.dumps`;
the schema is format-agnostic.

## Regeneration

Deterministic emitter; re-running yields byte-identical output. From
the repo root:

    ./examples/temporal/alert-triage/regenerate.sh

The script mirrors the canonical CACAO YAML source into the JSON form
this folder commits, then re-emits `workflow.temporal.py` via
`tools.compile --target temporal`. A drift test in
`tests/examples/alert_triage/` (sibling F-WF-03 follow-up) fails the
suite if the committed artifact diverges from a fresh regeneration, so
the worked example stays honest as the compiler evolves.

## Wiring it into your runtime

`workflow.temporal.py` is a Temporal `@workflow.defn` whose body calls
each `@activity.defn` in the topology the CACAO playbook defines. The
integrator pattern is:

1. Register the workflow class on a Temporal worker.
2. For the seven bound activities (ingest, enrich, suppress, classify,
   p1 / p2 / p3 response), expose the operator's existing connector
   inputs to the activity so the primitive call has the data it
   needs — alert source, enrichment provider, suppression cache,
   asset context, paging / on-call / review-queue endpoints.
3. For the single absent-body activity (p4 log-and-close), replace
   `raise NotImplementedError` with a call to the operator's
   telemetry-coverage / false-positive accounting sink.
4. Keep the per-activity `RetryPolicy` constants as defaults; tune
   timeouts and `maximum_attempts` to the operator's environment.

The `if-condition` after `enrich` reads the suppression decision and
routes to either the suppress-and-close branch or the
classify-and-prioritise branch. The `switch-condition` after
classification reads the priority bucket (`p1_severe`, `p2_high`,
`p3_routine`, `p4_informational`) and routes to the matching response
activity. Unknown / missing decisions fall through to the spec's
`default` branch, so a misbehaving classifier terminates the run
rather than dead-locking.

## Observability — OTel spans emitted by default

The Temporal reference compiler emits this worked example already
wrapped in OpenTelemetry instrumentation; an operator who runs the
generated `workflow.temporal.py` in their worker gets traces without
writing any glue.

Two span boundaries are emitted:

- **Activity span — `activity.<step_id>`.** Every `@activity.defn`
  body in `workflow.temporal.py` opens
  `tracer.start_as_current_span("activity.<step_id>", attributes={...})`
  around its body, before the primitive call (for bound activities)
  or before the `NotImplementedError` (for absent-body activities).
  Retries open a fresh span per Temporal attempt.
- **Workflow span — `workflow.<stable_id>`.** The `@workflow.defn`
  class's `run()` opens
  `tracer.start_as_current_span("workflow.<stable_id>", attributes={...})`
  at workflow entry. Activity spans started from this workflow run are
  children of it once the operator's collector links them via context
  propagation.

Span attributes use the shared `secops_ng.*` keyspace and are stable
across reference compilers (Temporal, LangGraph, n8n):

| Attribute key                | Carries                                              |
|------------------------------|------------------------------------------------------|
| `secops_ng.playbook.id`      | CACAO playbook id (`playbook--…`).                   |
| `secops_ng.playbook.version` | Content version pinned in the playbook.              |
| `secops_ng.step.id`          | CACAO step id (`action--…`).                         |
| `secops_ng.step.name`        | Human-readable step label from the playbook.         |
| `secops_ng.step.type`        | CACAO step type (`action`, `if-condition`, …).       |
| `secops_ng.tool.name`        | Emitted activity function name.                      |
| `secops_ng.compile.target`   | `temporal` on this artifact (target discriminator).  |

The `secops_ng.workflow.run_id` attribute is emitted as an empty-string
placeholder; the host worker binds Temporal's `info().workflow_id` /
`run_id` to it at runtime if the operator wires a span processor that
enriches outgoing spans with workflow context.

### Audit-trail mirror — offline / air-gapped

Each span the compiled module opens also appends an `AuditRecord` to a
context-local `AuditTrail` in the sibling `_audit_mirror.py` (emitted
next to `workflow.temporal.py`). The mirror runs unconditionally,
*before* any OTLP exporter is involved, so the audit property holds
even when the operator has not configured a collector — typical for
disconnected, sovereign, or air-gapped deployments where OTLP egress
is unavailable. Activities and workflow runs share the trail through
the contextvar, so a Temporal worker that processes multiple workflows
concurrently keeps each run's records isolated. See
[../../../docs/observability/audit-mirror.md](../../../docs/observability/audit-mirror.md)
for the co-location decision, the JSONL replay envelope, and the
snapshot API used to drain a trail offline.

### Operator configuration

The compiled artifact reads the standard OpenTelemetry environment
variables; nothing is hard-coded. The minimum the operator wires on
the Temporal worker process:

```sh
# OTLP collector — operator-provided. No default endpoint is set by
# the compiled artifact; if unset, spans are dropped and the audit
# mirror is the sole audit record.
export OTEL_EXPORTER_OTLP_ENDPOINT="https://otel.collector.example.eu:4317"
export OTEL_SERVICE_NAME="alert-triage-worker"
```

Sovereign-stack note: the collector should be EU-resident. Reference
choices include Grafana Alloy on Hetzner, OTLP → Tempo on Scaleway, or
an OVHcloud / Nebul-hosted collector — anything in operator-controlled
EU infrastructure works; `us-*` regional endpoints do not meet the
project's sovereignty posture.

The compiled artifact also stays provider-neutral by construction: the
emitter never imports a vendor SDK and never sets a default endpoint
that routes outside the operator's control. Pointing the OTLP exporter
at a managed APM is a downstream configuration choice the operator
owns end-to-end.

## Per-activity wiring notes — CORE bodies

The eight CORE action steps split into two emission shapes depending
on whether the canonical CACAO step declares an `x_secops_ng.core_body`
reference into the deterministic primitives package under
`content/playbooks/alert-triage/primitives/`:

- **`core_body` set (ingest, enrich, suppress, classify, p1 / p2 / p3
  response).** The `@activity.defn` body imports the primitive and
  produces the canonical alert payload / seen key / priority verdict /
  response directive (e.g.
  `validate_alert_payload(raw=..., source_shape=...)`,
  `canonical_seen_key(detection_rule_id=..., subject_ref=...,
  asset_ref=..., classification=...)`,
  `prioritise(detection_class=..., detection_severity=...,
  context=..., correlates_open_case=...)`,
  `escalation_route(...) / notify_on_call(...) /
  route_to_review_queue(...)`). Same Python functions called from
  n8n and LangGraph; same `PriorityVerdict.inputs_digest` on every
  target.
- **`core_body` absent (p4 informational — log and close).** The
  `@activity.defn` body opens the span, appends the `AuditRecord`,
  and then `raise NotImplementedError`. Integrator fills the body in
  against their telemetry-coverage / false-positive accounting
  sink — the seam is visible at a glance.

Per-activity retry policies are emitted alongside the activities
(`<ACTIVITY>_RETRY_POLICY` constants) so the operator pins them on
the `workflow.execute_activity` call sites in their own worker
assembly.

## Primitives contract

The priority bands, the suppression-window length, the canonical
seen-key shape, the typed alert payload schema, and the DSPy signature
schema for free-text fields are **code, not configuration**. They live
under `content/playbooks/alert-triage/primitives/`:

| Module             | What it pins                                                                       |
|--------------------|------------------------------------------------------------------------------------|
| `payloads.py`      | `validate_alert_payload(raw, source_shape) → AlertPayload`; two source shapes.     |
| `suppression.py`   | `canonical_seen_key(...)` + `SuppressionWindow` sliding-window membership.         |
| `prioritisation.py`| `prioritise(detection_class, detection_severity, context, correlates_open_case) → PriorityVerdict`. |
| `response.py`      | `escalation_route` + `notify_on_call` + `route_to_review_queue` deterministic directives. |
| `signatures.py`    | DSPy signature for free-text fields only — never the priority decision.            |

Operators who need to diverge fork the primitive module; they do not
override it via runtime config.

## Operator runtime hand-off contract

The Temporal reference compiler emits a worker module the integrator
drops next to their existing workers. The hand-off boundary:

| The framework ships                          | The operator owns                                            |
|----------------------------------------------|--------------------------------------------------------------|
| `@workflow.defn` class wiring the topology   | Temporal cluster (self-hosted, EU-resident).                 |
| `@activity.defn` for every CACAO action      | Worker registration, task-queue, namespace.                  |
| `core_body` bodies for ingest, enrich, suppress, classify, p1 / p2 / p3 response | Connector credentials and endpoints. |
| `NotImplementedError` stub for absent-body p4 log-and-close | Telemetry-coverage / false-positive accounting sink. |
| Per-activity `<ACTIVITY>_RETRY_POLICY` defaults | Production retry / concurrency / persistence tuning.       |
| `_audit_mirror.py` co-located AuditTrail     | OTel exporter endpoint (EU-resident collector).              |
| Cross-target replay determinism via shared primitives | Suppression window length, prioritisation thresholds — forked in `primitives/` rather than overridden at runtime. |

The walkthrough in
[`../../../docs/cookbook/alert-triage.md`](../../../docs/cookbook/alert-triage.md)
reads this end-to-end alongside the n8n and LangGraph targets.

## Sovereignty note

Temporal is open source (MIT) and runs as a server + worker process
pair: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. No
telemetry, no execution traces, no alert content, no identifying
flows reach this repository or the SecOps-NG project. The operator
runs Temporal on infrastructure they control — we ship the structure,
they own the data plane.
