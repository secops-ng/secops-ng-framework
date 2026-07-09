# examples/temporal/dora_major_incident_reporting

Worked example: the `playbook.dora_major_incident_reporting@v1` CACAO
v2 playbook compiled by the Temporal reference compiler. Operators who
already run Temporal can import `workflow.temporal.py` into their
worker module to see the topology the emitter produces; binding the
activity bodies to real connectors (incident register, Art. 18
classification-decision store, ITS submission channel to the competent
authority, and the evidence-archival store) is the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/dora_major_incident_reporting/playbook.cacao.json

Scenario, workflow, regulatory anchors (DORA Art. 19 with the Art. 18
classification predicate, the Commission Delegated Regulation (EU)
2024/1772 RTS on classification, and the Commission Implementing
Regulation (EU) 2024/2956 ITS on reporting content), and
OSCAL / D3FEND control bindings are documented in that folder's
`mappings.yaml`. This folder holds only the emitted artifact, a
co-located copy of the CACAO source, and the regeneration command.

## Layout

| Path                    | Source compiler      | Format                |
|-------------------------|----------------------|-----------------------|
| `playbook.cacao.json`   | (input)              | CACAO v2 JSON         |
| `workflow.temporal.py`  | `compilers.temporal` | Python (`temporalio`) |

## Regeneration

From the repo root:

    ./examples/temporal/dora_major_incident_reporting/regenerate.sh

Equivalent direct invocation:

    PYTHONPATH=. python -m tools.compile \
        content/playbooks/dora_major_incident_reporting/playbook.cacao.json \
        --target temporal \
        --out examples/temporal/dora_major_incident_reporting/workflow.temporal.py

The drift guard between the committed worked example and the emitter
output is pinned by
`tests/examples/dora_major_incident_reporting/test_golden.py`.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
Temporal cluster should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
Temporal is open source (MIT) and Temporal Cloud is one hosting choice
among several; operators are free to run their own cluster on EU
sovereign infrastructure (Nebul, OVHcloud, Scaleway, Hetzner). We ship
the structure, the operator owns the data plane.
