# examples/temporal/cloud_misconfiguration

Worked example: the `playbook.cloud_misconfiguration@v1` CACAO v2
playbook compiled by the Temporal reference compiler. Operators who
already run Temporal can import `workflow.temporal.py` into their worker
module to see the topology the emitter produces. Each of the seven
activity bodies imports and calls its bound primitive. Sequencing the
activities through the two gates (the workflow's `run` method still
raises `NotImplementedError`, as it does for every playbook) and
binding the inputs the primitives read to real connectors (CSPM /
posture-management platform, cloud inventory and ownership graph,
exception ledger, ticketing / chat / paging channel, change-management
system, re-scan trigger) is the operator's job.

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

The emitted module carries the activities, their retry policies and
the workflow class shell. Each activity calls its bound primitive; the
workflow's control flow is left to the integrator. It does not carry:

- Operator-bound bindings (CSPM / posture-management platform, cloud
  inventory and ownership graph, ticketing / chat / paging channel,
  change-management system, re-scan trigger, escalation paging
  endpoint) are not embedded — the operator wires them at
  activity-worker startup.
- Credentials, secrets, and environment-specific endpoints are not
  embedded — secrets stay with the operator and are injected at
  worker startup, not at compile time.
- The operator's policy is not embedded: the classification policy,
  the exception ledger, the per-severity routing and the default
  ownership pool arrive as adapter inputs. The rules applied to them
  are fixed in the primitives and pinned by their tests.
- The recurring-misconfiguration KRI itself is not embedded. The
  suppression and escalation activities stamp it; the metric lives in
  the catalogue.
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
