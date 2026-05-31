# examples/temporal/phishing-triage

Worked example: the `playbook.phishing_triage@v1` CACAO v2 playbook
compiled by the Temporal reference compiler. Operators who already run
Temporal can import `workflow.temporal.py` into their worker module to
see the topology the emitter produces; binding the activity bodies to
real connectors (user-reported / mailbox-sweep email source, email
security gateway / URL sandbox / attachment sandbox enrichment,
suppression cache, intent classifier, response-branch ticketing /
containment actions) is the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/phishing-triage/playbook.cacao.json

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

    ./examples/temporal/phishing-triage/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.temporal.py` via `tools.compile --target temporal`.

## Sovereignty note

Temporal is open source (MIT) and runs as a server + worker process
pair: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. No
telemetry, no execution traces, no email content, no identifying flows
reach this repository or the SecOps-NG project. The operator runs
Temporal on infrastructure they control — we ship the structure, they
own the data plane.
