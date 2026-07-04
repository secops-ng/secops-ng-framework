# examples/temporal/dora_ict_risk_selfassess

Worked example: the `dora_ict_risk_selfassess` CACAO v2 playbook
compiled by the Temporal reference compiler. Operators who already
run Temporal can import `workflow.temporal.py` into their worker
module to see the topology the emitter produces; binding the activity
bodies to real connectors (evidence-store adapter, per-section
coverage rubric, dated attestation artifact template, and the
operator's authoritative Chapter II section attribution) is the
operator's job.

This worked example pins the Temporal leg (target 1 of 3) of the
cross-target parity lane for the `dora_ict_risk_selfassess` playbook
(DORA Chapter II ICT risk management operator self-assessment
roll-up), alongside the n8n and LangGraph siblings under
`../../n8n/dora_ict_risk_selfassess/` and
`../../langgraph/dora_ict_risk_selfassess/`. Together the three
folders pin the full three-target contract for this playbook.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/dora_ict_risk_selfassess/playbook.cacao.json

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

    ./examples/temporal/dora_ict_risk_selfassess/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.temporal.py` via `tools.compile --target temporal`.

## Status

CORE — the Temporal artifact ships byte-deterministic from the
canonical CACAO source. Activity bodies remain `NotImplementedError`
stubs by design; the operator-facing attestation-report renderer and
community cookbook CORE entry land in the EXTEND tier.
