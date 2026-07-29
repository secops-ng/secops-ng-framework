# examples/temporal/eu_ai_act_deployer_obligations

Worked example: the `playbook.eu_ai_act_deployer_obligations@v1` CACAO
v2 playbook compiled by the Temporal reference compiler. Operators who
already run Temporal can import `workflow.temporal.py` into their
worker module to see the topology the emitter produces; binding the
activity bodies to real connectors (deployment register, provider
instructions-for-use store, oversight-assignment record, input-data
control surface, monitoring signal source, FRIA record store,
automatically generated log store) is the operator's job.

This is the deployer-side counterpart to the provider-side
`eu_ai_act_risk_management` example.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/eu_ai_act_deployer_obligations/playbook.cacao.json

Scenario, workflow, regulatory anchors (EU AI Act Art. 26(1)/(2)/(4)/
(5)/(6)/(7) and Art. 27), and OSCAL / D3FEND control bindings are
documented in that folder's `mappings.yaml`. This folder holds only the
emitted artifact, a co-located copy of the CACAO source, and the
regeneration command.

## Layout

| Path                    | Source compiler      | Format                |
|-------------------------|----------------------|-----------------------|
| `playbook.cacao.json`   | (input)              | CACAO v2 JSON         |
| `workflow.temporal.py`  | `compilers.temporal` | Python (`temporalio`) |

## Why this one suits a durable-execution runtime

The Art. 26(6) retention obligation runs for **at least six months**,
and the Art. 26(5) monitoring duty is a standing per-window activity
rather than a one-shot. The compiled workflow is a linear activity
chain, but the lifecycle it models is long-running and re-entrant: the
terminal state closes on a dated evidence artifact and the next
monitoring window re-enters at the start step. Operators binding this
to real activities should expect the retention and monitoring seams to
outlive any single workflow execution, and should not assume the
emitted chain is a single short-lived run.

The `__escalation_trigger_class__` output is deliberately distinct from
the monitoring observation identifier: its three values carry different
Art. 26(5) consequences (routine Art. 72 feedback; an Art. 79(1) risk
determination compelling notification *and* suspension; a serious
incident compelling immediate sequenced notification into the
provider-side Art. 73 chain). An activity that returns only the
observation loses the suspension trigger.

## Regeneration

From the repo root:

    ./examples/temporal/eu_ai_act_deployer_obligations/regenerate.sh

Equivalent direct invocation:

    PYTHONPATH=. python -m tools.compile \
        content/playbooks/eu_ai_act_deployer_obligations/playbook.cacao.json \
        --target temporal \
        --out examples/temporal/eu_ai_act_deployer_obligations/workflow.temporal.py

The drift guard between the committed worked example and the emitter
output is pinned by
`tests/examples/eu_ai_act_deployer_obligations/test_golden.py`.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
Temporal cluster should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
Temporal is open source (MIT) and Temporal Cloud is one hosting choice
among several; operators are free to run their own cluster on EU
sovereign infrastructure (Nebul, OVHcloud, Scaleway, Hetzner). We ship
the structure, the operator owns the data plane.
