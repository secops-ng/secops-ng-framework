# compilers/temporal/

Emits Temporal workflow stubs (Python) from a CACAO v2 playbook.

## What it produces

One generated module per playbook, containing:

- One `@workflow.defn` class — `run()` raises `NotImplementedError` carrying
  the playbook `stable_id`. Control-flow lowering (transitions, branches,
  parallel) is intentionally deferred to a follow-up card.
- One `@activity.defn` async function per CACAO `action` /
  `playbook-action` step. Each body raises `NotImplementedError` carrying
  the CACAO `step_id` so a runtime worker fails loudly with a deterministic
  message pointing at the source step.
- `WORKFLOW` and `ACTIVITIES` registry symbols a worker bootstrap can import
  without re-scanning the module.

Control-flow step types (`start`, `end`, `if-condition`, `while-condition`,
`switch-condition`, `parallel`) do **not** produce activities — they become
workflow code when lowering lands.

## Usage

```python
from compilers.temporal import emit_file

source = emit_file("content/playbooks/vuln-intake/playbook.cacao.json")
```

Output is deterministic: the same AST always yields byte-identical source.

## Scope

This module is **stub-only**. It does not import `temporalio` itself, makes
no I/O beyond reading the input file, and emits no business logic. An
integrator fills the activity bodies and the `run()` orchestration against
their own runtime.

## Observability

The compiler emits OpenTelemetry instrumentation by default: every
`@activity.defn` body opens an `activity.<step_id>` span and the
`@workflow.defn` `run()` opens a `workflow.<stable_id>` span. Span
attributes use the shared `secops_ng.*` keyspace —
`secops_ng.playbook.id`, `secops_ng.playbook.version`,
`secops_ng.step.id`, `secops_ng.step.name`, `secops_ng.step.type`,
`secops_ng.tool.name`, `secops_ng.compile.target=temporal`, and a
`secops_ng.workflow.run_id` placeholder bound by the host runtime. A
sibling `_audit_mirror.py` appends an `AuditRecord` per span so the
audit property holds when OTLP is offline. See the worked example
[`examples/temporal/vuln-intake/`](../../examples/temporal/vuln-intake/)
and its `Observability` section for the operator-config envelope
(`OTEL_EXPORTER_OTLP_ENDPOINT`, EU-resident collector guidance,
provider neutrality).
