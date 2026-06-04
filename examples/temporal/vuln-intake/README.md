# examples/temporal/vuln-intake

Worked example: the `playbook.vuln_intake@v1` CACAO v2 playbook compiled
by the Temporal reference compiler. Operators who already run Temporal
can import `workflow.temporal.py` into their worker module to see the
topology the emitter produces; binding the activity bodies to real
connectors (coordinated-disclosure intake channel, CMDB / asset
correlation, patch and advisory pipeline, ticketing, and the EU Cyber
Resilience Act Article 14 regulator-notification chain for actively
exploited vulnerabilities) is the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/vuln-intake/playbook.cacao.json

Scenario, workflow, regulatory anchors, control / metric / telemetry
bindings, and the operator-supplied bindings are documented in that
folder's `README.md`. This folder holds only the emitted artifact, a
co-located copy of the CACAO source, and the regeneration command.

## Layout

| Path                    | Source compiler      | Format                |
|-------------------------|----------------------|-----------------------|
| `playbook.cacao.json`   | (input)              | CACAO v2 JSON         |
| `workflow.temporal.py`  | `compilers.temporal` | Python (`temporalio`) |

## Regeneration

Deterministic emitter; re-running yields byte-identical output. From
the repo root:

    ./examples/temporal/vuln-intake/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.temporal.py` via `tools.compile --target temporal`.

## Observability — OTel spans emitted by default

The Temporal reference compiler emits this worked example already
wrapped in OpenTelemetry instrumentation; an operator who runs the
generated `workflow.temporal.py` in their worker gets traces without
writing any glue.

Two span boundaries are emitted:

- **Activity span — `activity.<step_id>`.** Every `@activity.defn`
  body in `workflow.temporal.py` opens
  `tracer.start_as_current_span("activity.<step_id>", attributes={...})`
  around its body, before raising `NotImplementedError`. When the
  integrator fills the activity body in, the work happens inside the
  span; retries open a fresh span per Temporal attempt.
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
| `secops_ng.playbook.id`      | CACAO playbook id (e.g. `playbook--…`).              |
| `secops_ng.playbook.version` | Content version pinned in the playbook.              |
| `secops_ng.step.id`          | CACAO step id (e.g. `action--…`).                    |
| `secops_ng.step.name`        | Human-readable step label from the playbook.         |
| `secops_ng.step.type`        | CACAO step type (`action`, `playbook-action`, …).    |
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
export OTEL_SERVICE_NAME="vuln-intake-worker"
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

## Sovereignty note

Temporal is open source (MIT) and runs as a server + worker process
pair: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. No
telemetry, no execution traces, no identifying data flows reach this
repository or the SecOps-NG project. The operator runs Temporal on
infrastructure they control — we ship the structure, they own the
data plane.
