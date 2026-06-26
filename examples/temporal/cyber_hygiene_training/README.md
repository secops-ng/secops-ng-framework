# examples/temporal/cyber_hygiene_training

Worked example: the `playbook.cyber_hygiene_training@v1` CACAO v2
playbook compiled by the Temporal reference compiler. Operators who
already run Temporal can import `workflow.temporal.py` into their
worker module to see the topology the emitter produces; binding the
activity bodies to real connectors (training-roster inventory,
per-cycle awareness and role-based assignment scheduler,
phishing-simulation exercise runner, completion-and-report-rate
tracker, dated training-attestation evidence store, and the
training-owner notification channel) is the operator's job.

This worked example opens the cross-target parity lane for the
`cyber_hygiene_training` playbook (NIS2 Art.21(2)(g)). The n8n and
LangGraph siblings land in separate sibling cards; until then, this
directory pins the Temporal end of the three-target contract.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/cyber_hygiene_training/playbook.cacao.json

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

    ./examples/temporal/cyber_hygiene_training/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.temporal.py` via `tools.compile --target temporal`.

## Status

SKELETON — the Temporal artifact ships byte-deterministic from the
canonical CACAO source. Activity bodies remain `NotImplementedError`
stubs by design; the per-target byte-parity goldens across n8n +
Temporal + LangGraph land in the sibling fan-out cards once the
remaining two compile targets ship.
