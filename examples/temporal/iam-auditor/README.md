# examples/temporal/iam-auditor

Worked example: the `playbook.iam_auditor@v1` CACAO v2 playbook
compiled by the Temporal reference compiler. Operators who already
run Temporal can import `workflow.temporal.py` into their worker
module to see the topology the emitter produces; binding the activity
bodies to real connectors (identity provider, capability source,
evidence sink) is the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/iam-auditor/playbook.cacao.json

Scenario, workflow, regulatory anchor (NIS2 Article 21(2)(i)), and the
`x_secops_ng` reference bundles (control / telemetry / metric joins,
F-CP-07 access-evidence stream) are documented in that folder's
`README.md`. This folder holds the emitted artifact, a co-located
byte-identical copy of the CACAO source for easy diff inspection, the
regeneration scripts, and one representative access-evidence artifact
the F-CP-07 Temporal activity adapter produces at execution time.

## Layout

| Path                                    | Source compiler                                            | Format                |
|-----------------------------------------|------------------------------------------------------------|-----------------------|
| `playbook.cacao.json`                   | (input mirror)                                             | CACAO v2 JSON         |
| `workflow.temporal.py`                  | `compilers.temporal`                                       | Python (`temporalio`) |
| `regenerate.sh`                         | (tooling)                                                  | bash script           |
| `regenerate.py`                         | (tooling)                                                  | Python script         |
| `evidence/access-evidence.json`         | `compilers.temporal.evidence.access_activity`              | F-CP-07 access record |

## How to use

1. Copy `workflow.temporal.py` into your Temporal worker module (or
   import it directly if your worker layout permits).
2. Register the workflow and the per-step activities with your worker.
3. The generated activity bodies raise `NotImplementedError` by
   default — bind each one to your operator-side connector (identity
   provider, capability source, evidence sink) before starting the
   worker against a real task queue.

The emitted workflow is a *snapshot of intent*, not a runnable
playbook. The activity stubs carry the CACAO I/O contract (`in_args`
/ `out_args`) plus the `x_secops_ng` reference bundles (control,
telemetry, metric) on the OTel attribute set so a tracing collector
sees the join keys without any per-operator glue.

## Regeneration

The Temporal emitter is deterministic: same input bytes in, same
output bytes out. From the repo root:

    ./examples/temporal/iam-auditor/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.temporal.py` via `tools.compile --target temporal`.
Equivalent direct invocation:

    PYTHONPATH=. python -m tools.compile \
        content/playbooks/iam-auditor/playbook.cacao.json \
        --target temporal \
        --out examples/temporal/iam-auditor/workflow.temporal.py

The canonical playbook under
`content/playbooks/iam-auditor/playbook.cacao.json` is the single
source. The byte-parity test under
`tests/examples/temporal/iam-auditor/test_golden.py` pins the
committed worked example against the emitter so silent drift is
caught at CI.

## Access-evidence artifact (F-CP-07)

The iam-auditor's `emit-access-evidence` state produces one
access-evidence artifact per execution against
`schemas/evidence/access.schema.json`. The committed
`evidence/access-evidence.json` is the byte-stable output of the
Temporal activity adapter
(`compilers.temporal.evidence.emit_access_artifact_activity`) for the
representative payload pinned in `regenerate.py` — exactly what an
operator's Temporal worker materialises at runtime.

Regenerate from the repo root:

    PYTHONPATH=. python examples/temporal/iam-auditor/regenerate.py

The artifact is renamed from the deterministic
`<artifact_id>.json` (SHA-256 of `workflow_id|execution_id|compile_target`)
to a stable human-friendly filename for diffing; the byte-parity test
under `tests/examples/temporal/iam-auditor/test_golden.py` pins both
the workflow source and the access-evidence record against the
adapter.

The artifact_id intentionally differs from the n8n sibling — that is
the schema's per-target join — but every other anchor (workflow_id,
control_refs, regulation_refs, capabilities, captured_at) is
identical so a cross-target reviewer sees the same shape on both
sides.

## Observability — OTel spans emitted by default

The Temporal reference compiler emits this worked example already
wrapped in OpenTelemetry instrumentation; an operator who runs the
generated `workflow.temporal.py` in their worker gets traces without
writing any glue. Two span boundaries are emitted:

- **Activity span — `activity.<step_id>`.** Every `@activity.defn`
  body opens a span carrying the playbook id/version, the step id /
  name / type, and the compile-target attribute (`temporal`).
- **Workflow span — `workflow.<playbook_id>`.** The workflow run is
  wrapped in a parent span so activity spans nest under one trace.

## Mirroring policy

The mapping from CACAO to Temporal is the same one the compiler
implements:

| CACAO step type    | Temporal artifact                                                    |
|--------------------|----------------------------------------------------------------------|
| `start`            | workflow entrypoint                                                  |
| `action`           | `@activity.defn` async function + per-activity `RetryPolicy`         |
| `end`              | workflow exit                                                        |

Activity function names mirror the CACAO step name (sanitised to a
valid Python identifier); the originating CACAO `step_id` is recorded
verbatim in each activity docstring and on the OTel span attribute so
the two artifacts can be cross-referenced. Sequencing
(`on_completion`) becomes the linear `await workflow.execute_activity`
sequence inside the workflow function.

## What this example does not do

The Temporal reference compiler translates **structure** and the
**CACAO I/O contract**, not **business logic**. The emitted workflow
carries the topology of the playbook (steps, transitions), the
per-step `in_args` / `out_args`, and the `x_secops_ng` reference
bundles as OTel attributes. It does not carry:

- Operator-bound bindings (identity provider, capability source,
  evidence sink).
- Credentials, secrets, or environment-specific endpoints.
- The F-PT-01 platform-side refuse-at-boot guarantee that the caller
  actually held the listed capabilities — that lives in the platform
  layer; the workflow only carries the assertion shape.

Where a CACAO step expresses intent the target runtime cannot encode
(an `action` with no machine-readable `commands`), the emitter
leaves the activity body as `NotImplementedError` so a human
integrator sees exactly what they still need to wire.

## Sovereign-stack default

The artifact destination is operator-configured. No default non-EU
endpoint. The Temporal example writes the access-evidence artifact
to a local directory; the operator's runtime is expected to point the
activity's `output_dir` at the volume their chosen evidence sink
ingests from.
