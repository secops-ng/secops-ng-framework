# examples/temporal/cloud_misconfiguration

Worked example: the `playbook.cloud_misconfiguration@v1` CACAO v2
playbook compiled by the Temporal reference compiler. Operators who
already run Temporal can import `workflow.temporal.py` into their worker
module to see the topology the emitter produces; binding the activity
bodies to real connectors (CSPM / posture-management platform, cloud
inventory and ownership graph, ticketing / chat / paging channel,
change-management system, re-scan trigger) is the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/cloud_misconfiguration/playbook.cacao.json

Scenario, workflow, regulatory anchors (NIS2 Article 21(2)(e) / 21(2)(i),
DORA Articles 6 and 9), control / metric / telemetry bindings, and the
operator-supplied bindings are documented in that folder's `README.md`.
This folder holds only the emitted artifact, a co-located copy of the
CACAO source, and the regeneration command.

## Layout

| Path                    | Source compiler      | Format                |
|-------------------------|----------------------|-----------------------|
| `playbook.cacao.json`   | (input)              | CACAO v2 JSON         |
| `workflow.temporal.py`  | `compilers.temporal` | Python (`temporalio`) |

## Regeneration

Deterministic emitter; re-running yields byte-identical output. From
the repo root:

    ./examples/temporal/cloud_misconfiguration/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.temporal.py` via `tools.compile --target temporal`.

## Mirroring policy

The mapping from CACAO to Temporal is the same one the compiler
implements:

| CACAO step type    | Temporal artifact                              |
|--------------------|------------------------------------------------|
| `start`            | (workflow entry point, no activity)            |
| `action`           | `@activity.defn` async function                |
| `if-condition`     | workflow control flow (compiler-emitted)       |
| `switch-condition` | workflow control flow (compiler-emitted)       |
| `end`              | (workflow return, no activity)                 |

Each CACAO `action` becomes exactly one `@activity.defn` function whose
name is the CACAO action's `name` slugified to a valid Python
identifier, plus a `RetryPolicy` constant. The function docstring
records the CACAO `step_id` verbatim so the two artifacts can be
cross-referenced. The emitted workflow class exposes the playbook's
`stable_id` and the ordered activity tuple in its docstring; the
ordered tuple is also exported as the module-level `ACTIVITIES`
constant so a worker bootstrap can register them without knowing the
playbook's internals.

## What this example does not do

The Temporal reference compiler translates **structure**, not
**business logic**. The emitted stub carries the topology of the
playbook (activities, retry policies, the workflow class shell) but
the activity bodies and workflow control flow are intentionally
`NotImplementedError`:

- Operator-bound bindings (CSPM / posture-management platform, cloud
  inventory and ownership graph, ticketing / chat / paging channel,
  change-management system, re-scan trigger, escalation paging
  endpoint) are not embedded — the operator wires them at
  activity-worker startup.
- Credentials, secrets, and environment-specific endpoints are not
  embedded — secrets stay with the operator and are injected at
  worker startup, not at compile time.
- Suppression-window expressions, severity-classification logic, and
  remediation-attestation logic are not embedded — these are
  intent-bearing values the operator sets when binding the workflow
  to their environment.
- The recurring-misconfiguration KRI accounting is not embedded —
  that lives in the metric bindings referenced from the canonical
  playbook; the emitter carries only the activities that emit
  against it, not the metric itself.
- It does not pick a Temporal deployment posture. Self-hosted
  (Temporal OSS on EU sovereign infrastructure) and managed
  (Temporal Cloud) are both supported by the same emitted source.

## Sovereignty note

Temporal is open source (MIT) and runs as a server + worker process
pair: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. The
emitter never embeds a connection string, task-queue name, or
credential, so the operator can target a self-hosted cluster or an
EU-region managed namespace without regenerating the artifact. The
artifact emitted here is a description of what the operator's own
Temporal worker should do — no telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
The operator runs Temporal on infrastructure they control; we ship the
structure, they own the data plane.
