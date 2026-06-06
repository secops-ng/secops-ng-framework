# examples/temporal/incident-management

Worked example: the `playbook.incident_management@v1` CACAO v2 playbook
compiled by the Temporal reference compiler. Operators who already run
Temporal can drop `workflow.temporal.py` into their worker module to
see the topology the emitter produces; binding the activity bodies to
real connectors (incident signal intake, deterministic significance /
cross-border classification, F-PT-02 incident-timeline pattern handle
store, regulator-submission destinations for the three NIS2 Article 23
stages, timeline JSON persistence backend) is the operator's job.

This is the **SKELETON** card of the F-WF-05 wave. Action bodies are
stub placeholders that raise `NotImplementedError` and carry only the
CACAO I/O contract; no primitives binding is in place yet — that lands
in the CORE-PRIM card (card 5 of the F-WF-05 wave).

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/incident-management/playbook.cacao.json

Scenario, workflow, regulatory anchors (NIS2 Article 23, DORA Article
19, ENISA incident-reporting guidance), control / metric / telemetry
bindings, and the operator-supplied notification-destination contract
are documented in that folder's `README.md`. This folder holds only the
emitted artifact, a co-located copy of the CACAO source, and the
regeneration command.

## Layout

| Path                    | Source compiler      | Format                |
|-------------------------|----------------------|-----------------------|
| `playbook.cacao.json`   | (input)              | CACAO v2 JSON         |
| `workflow.temporal.py`  | `compilers.temporal` | Python (`temporalio`) |

## Regeneration

Deterministic emitter; re-running yields byte-identical output. From
the repo root:

    ./examples/temporal/incident-management/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.temporal.py` via `tools.compile --target temporal`.

## What this example deliberately doesn't do

- It does not execute the workflow. The `@activity.defn` bodies raise
  `NotImplementedError`; integrators wire them to their own runtime
  (incident signal intake, deterministic significance / cross-border
  classification, the F-PT-02 incident-timeline pattern handle store,
  regulator-submission destinations for the three NIS2 stages,
  timeline JSON persistence backend).
- It does not ship operator credentials, endpoints, or environment.
  Secrets stay with the operator — the sovereign-stack constraint
  applies, so regulator destinations come from the operator's own
  config layer (no default endpoint is shipped).
- It does not implement the deterministic significance / cross-border
  classification policy or the typed early-warning / 72h notification /
  final-report payload shapes. Those land in CORE-PRIM.
- It does not bind a specific runtime topology (retry policy beyond
  the emitted default, concurrency, persistence backend, stage-clock
  arithmetic). Those are runtime concerns the integrator applies in
  their own assembly; the stage-clock primitive itself lands in
  CORE-PRIM.

## Sovereignty note

Temporal is open source (MIT) and runs as a server + worker process
pair: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. No
telemetry, no execution traces, no incident content, no regulator
notifications reach this repository or the SecOps-NG project. The
operator runs Temporal on infrastructure they control — we ship the
structure, they own the data plane.
