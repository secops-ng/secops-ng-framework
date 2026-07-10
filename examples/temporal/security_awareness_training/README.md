# examples/temporal/security_awareness_training

Worked example: the `playbook.security_awareness_training@v1` CACAO
v2 playbook compiled by the Temporal reference compiler. Operators
who already run Temporal can import `workflow.temporal.py` into their
worker module to see the topology the emitter produces; binding the
activity bodies to real connectors (training-needs assessment surface,
curriculum authoring / LMS, delivery dispatch, per-staff completion
store, gap-report notification channel, and the cycle-review artifact
store) is the operator's job.

This worked example pins the Temporal leg (target 2 of 3) of the
cross-target parity lane for the `security_awareness_training`
playbook (NIS2 Art.21(2)(g)), alongside the n8n and LangGraph
siblings under `../../n8n/security_awareness_training/` and
`../../langgraph/security_awareness_training/`.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/security_awareness_training/playbook.cacao.json

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

    ./examples/temporal/security_awareness_training/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.temporal.py` via `tools.compile --target temporal`.

## Status

CORE — the Temporal artifact ships byte-deterministic from the
canonical CACAO source. Activity bodies remain `NotImplementedError`
stubs by design; the per-target byte-parity goldens across n8n +
Temporal + LangGraph land here as CORE. Telemetry emit bindings and
per-cohort programme-governance KPIs are owned by EXTEND siblings.
