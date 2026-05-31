# examples/temporal/threat-intel-ingest

Worked example: the `playbook.threat_intel_ingest@v1` CACAO v2 playbook
compiled by the Temporal reference compiler. Operators who already run
Temporal can import `workflow.temporal.py` into their worker module to
see the topology the emitter produces; binding the activity bodies to
real connectors (STIX 2.1 / TAXII feed source, OCSF Threat Intelligence
normaliser, SIEM Sigma rule activation, perimeter / DNS / EDR blocklist
enforcement) is the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/threat-intel-ingest/playbook.cacao.json

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

    ./examples/temporal/threat-intel-ingest/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.temporal.py` via `tools.compile --target temporal`.

## Sovereignty note

Temporal is open source (MIT) and runs as a server + worker process
pair: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. No
telemetry, no execution traces, no identifying data flows reach this
repository or the SecOps-NG project. The operator runs Temporal on
infrastructure they control — we ship the structure, they own the
data plane.
