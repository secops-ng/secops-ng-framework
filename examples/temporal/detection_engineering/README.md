# examples/temporal/detection_engineering

Worked example: the `playbook.detection_engineering@v1` CACAO v2
playbook compiled by the **Temporal** reference compiler. The emitted
``workflow.temporal.py`` is a stub a Temporal worker can register
directly to see the topology the emitter produces; wiring the
placeholder activities to real connectors (detection-store proposal
intake, peer-review system, the operator's production detection-store
promotion endpoint, and the metric sink that ingests the per-rule-version
effectiveness snapshot) is the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/detection_engineering/playbook.cacao.yaml

The four-state lifecycle (propose → review → ship → measure), the
NIS2 Article 21(2)(f) regulatory anchor, the OCSF Detection Finding
binding, and the indicator catalogue references the `measure` state
emits against are documented in that folder's `README.md`. This
directory holds the emitted workflow stub, the regeneration script,
and the per-rule-version effectiveness-snapshot artifact the Temporal
activity adapter at
`compilers/temporal/evidence/rule_effectiveness_activity.py` produces
from the `measure` state's payload.

## Layout

| Path                          | Source                                  | Format               |
|-------------------------------|-----------------------------------------|----------------------|
| `workflow.temporal.py`        | `compilers.temporal`                    | Temporal Python stub |
| `regenerate.sh`               | (tooling — regenerates the workflow)    | bash script          |
| `evidence/rule-effectiveness-snapshot.json` | `compilers.temporal.evidence` | snapshot JSON       |
| `regenerate.py`               | (tooling — regenerates the snapshot)    | python script        |

## How to register

1. In your Temporal worker bootstrap, import the generated module.
   The emitter exports `WORKFLOW`, `ACTIVITIES`, and `RETRY_POLICIES`
   tuples — zip them when registering with `Worker(...)` so each
   activity carries the retry policy the canonical playbook pins.
2. Each `@activity.defn` body raises `NotImplementedError` by default;
   wire each one to your operator-side connector before running the
   workflow. The `@workflow.run` entry point likewise raises until the
   compile-lowering sibling lands.

The emitted workflow is a *snapshot of intent*, not a runnable
playbook. Each activity carries the CACAO I/O contract (`in_args` /
`out_args`) in its typed signature; binding those to real connectors
is the operator's job. The `measure` state's output is shaped per
`schemas/evidence/rule-effectiveness-snapshot.schema.json`; the
worked-example snapshot at `evidence/rule-effectiveness-snapshot.json`
shows the on-disk bytes the Temporal activity adapter writes for one
representative rule version.

## Observability

The emitter wraps every activity body in an OpenTelemetry
``activity.<step_id>`` span carrying stable ``secops_ng.*`` attributes
(playbook id, step id, step name, step type, tool function name,
compile target = ``temporal``) and a parallel ``AuditTrail.append``
mirror. The workflow ``run()`` entry point opens an outer
``workflow.<stable_id>`` span. The audit-trail mirror records the same
event in-band so audit holds even when no OTel exporter is configured
(F-CR-04 contract). Span names + attributes match the n8n sibling and
the LangGraph compile target so an OTel consumer sees structurally
compatible telemetry across all three reference compilers.

## Sovereign-stack constraint

Metric storage is operator-configured. The framework ships **no**
hosted-SaaS default endpoint for the effectiveness snapshot; the
operator's runtime is expected to point the activity adapter's
`output_dir` at the volume their chosen metric sink ingests from.

## Regeneration

The Temporal emitter is deterministic: same input bytes in, same
output bytes out. From the repo root:

    ./examples/temporal/detection_engineering/regenerate.sh

regenerates `workflow.temporal.py` from the canonical CACAO source.
The per-rule-version effectiveness-snapshot artifact under `evidence/`
is regenerated separately by the sibling Python script:

    PYTHONPATH=. python examples/temporal/detection_engineering/regenerate.py

The committed snapshot is byte-identical to the n8n sibling at
`../../n8n/detection_engineering/evidence/rule-effectiveness-snapshot.json`
— the per-target adapters are thin glue over a shared emitter, so any
drift between the two is a bug in one of the adapters.

## Pending follow-up work

Gating predicates on the `review → ship` and `ship → measure`
transitions, per-target byte-parity goldens covering all four
lifecycle states, and the cookbook walkthrough land in follow-up
sibling cards tracked in `ROADMAP.md` § F-WF-04. The reference
emitter for LangGraph lands alongside in its own sibling card.
