# examples/temporal/eu_ai_act_risk_management

Worked example: the `playbook.eu_ai_act_risk_management@v1` CACAO v2
playbook compiled by the Temporal reference compiler. Operators who
already run Temporal can import `workflow.temporal.py` into their
worker module to see the topology the emitter produces; binding the
activity bodies to real connectors (AI-system inventory, Annex III
use-case catalogue, risk-register store, technical-documentation
bundle store, post-market monitoring signal source) is the operator's
job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/eu_ai_act_risk_management/playbook.cacao.json

Scenario, workflow, regulatory anchors (EU AI Act Art. 6 / 9 / 11 /
Annex IV / 72), and OSCAL / D3FEND control bindings are documented in
that folder's `mappings.yaml`. This folder holds only the emitted
artifact, a co-located copy of the CACAO source, and the regeneration
command.

## Layout

| Path                    | Source compiler      | Format                |
|-------------------------|----------------------|-----------------------|
| `playbook.cacao.json`   | (input)              | CACAO v2 JSON         |
| `workflow.temporal.py`  | `compilers.temporal` | Python (`temporalio`) |

## Regeneration

From the repo root:

    ./examples/temporal/eu_ai_act_risk_management/regenerate.sh

Equivalent direct invocation:

    PYTHONPATH=. python -m tools.compile \
        content/playbooks/eu_ai_act_risk_management/playbook.cacao.json \
        --target temporal \
        --out examples/temporal/eu_ai_act_risk_management/workflow.temporal.py

The drift guard between the committed worked example and the emitter
output is pinned by
`tests/examples/eu_ai_act_risk_management/test_golden.py`.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
Temporal cluster should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
Temporal is open source (MIT) and Temporal Cloud is one hosting choice
among several; operators are free to run their own cluster on EU
sovereign infrastructure (Nebul, OVHcloud, Scaleway, Hetzner). We ship
the structure, the operator owns the data plane.
