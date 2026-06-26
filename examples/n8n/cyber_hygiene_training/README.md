# cyber_hygiene_training — n8n worked example

End-to-end demonstration of the SecOps-NG n8n reference compiler on
the `cyber_hygiene_training` CACAO playbook. It is aimed at an
integrator who already runs n8n and wants to adopt a portable
SecOps-NG playbook without re-platforming: the example shows exactly
which workflow shape the compiler produces, how the CACAO contract
surfaces on each node, and where the integrator owns the seams.

This worked example pins the n8n leg (target 2 of 3) of the
cross-target parity lane for the `cyber_hygiene_training` playbook
(NIS2 Art.21(2)(g)). The Temporal sibling already ships under
`../../temporal/cyber_hygiene_training/`; the LangGraph sibling lands
in a separate sibling card. Until all three are committed, this folder
pins the n8n slice of the three-target contract.

## Files in this directory

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input mirror)  | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |
| `regenerate.sh`       | (tooling)       | bash script       |
| `README.md`           | —               | This file.        |

The canonical input is the CACAO v2 playbook at
`../../../content/playbooks/cyber_hygiene_training/playbook.cacao.json`.
Scenario, regulatory anchors, control / metric / telemetry bindings,
and the operator-supplied bindings are documented in that folder's
`README.md`. This folder holds the emitted artifact, a co-located
byte-identical copy of the CACAO source for easy diff inspection, and
the regeneration script.

## How to import

1. In your own n8n instance, open the workflows list and choose
   **Import from File**.
2. Select `workflow.n8n.json` from this directory.
3. n8n loads eight nodes wired into the topology described below. The
   workflow is **inactive** by default — review and bind it to your own
   connectors before activating.

The emitted workflow is a *snapshot of intent*, not a runnable
playbook. The Set nodes carry the CACAO I/O contract as editable
assignments; binding those rows to real connectors (training-roster
inventory, per-cycle awareness and role-based assignment scheduler,
phishing-simulation exercise runner, completion-and-report-rate
tracker, dated training-attestation evidence store, and the
training-owner notification channel) is the operator's job.

## How to regenerate

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/cyber_hygiene_training/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

```bash
PYTHONPATH=. python -m tools.compile \
    content/playbooks/cyber_hygiene_training/playbook.cacao.json \
    --target n8n \
    --out examples/n8n/cyber_hygiene_training/workflow.n8n.json
```

The drift guard in
`tests/examples/n8n/cyber_hygiene_training/test_golden.py` fails the
suite if the committed `workflow.n8n.json` diverges from a fresh
regeneration, so the worked example stays honest as the compiler
evolves.

## Topology

The cyber_hygiene_training playbook is a linear evaluate-schedule-
exercise-track-attest-notify chain with no conditional branching at
the workflow layer. Eight n8n nodes, one per CACAO step:

1. `cyber_hygiene_training_start` (`manualTrigger`) — entry point;
   matches the CACAO `start` step. Carries the workflow-scope
   variables (`__training_window__`, `__training_scope__`, …) the
   operator's scheduler or operator-initiated trigger supplies.
2. `inventory training roster` (`set`) — resolve the in-scope training
   roster (mandatory and role-based tracks, joiner/leaver state) from
   the operator's HR / identity source; emits `__roster_id__`.
3. `schedule training cycle` (`set`) — schedule the per-cohort
   awareness and role-based training assignments for this cycle; emits
   `__cycle_id__`.
4. `run phishing simulation` (`set`) — run the cycle's
   phishing-simulation exercise against enrolled cohorts and capture
   delivery, click, and report telemetry; emits `__simulation_id__`.
   The simulation is a documented exercise; it does NOT trigger
   downstream incident response.
5. `track completion` (`set`) — track per-staff mandatory and
   role-based training completion against the cycle's due dates and
   per-cohort report-rate against the simulation; emits
   `__completion_id__`.
6. `evidence capture` (`set`) — persist a dated training-attestation
   record covering the roster snapshot, cycle assignments, simulation
   results, and completion tracking; emits `__attestation_id__`.
7. `notify gaps` (`set`) — surface the attestation and the
   policy-side / operations-side gaps to the training owner via the
   operator's notification channel.
8. `cyber_hygiene_training_end` (`noOp`) — end sentinel.

## CACAO contract surfaces on Set nodes

Every `action`-without-commands step in the CACAO source emits an n8n
`set` node whose **assignments** carry the CACAO contract one row per
field:

- `in.<name>` rows for each entry in the step's `in_args`.
- `out.<name>` rows for each entry in the step's `out_args`.
- `x_secops_ng.<key>` rows for each key under the step's
  `x_secops_ng` block (`control_refs`, `telemetry_refs`, `metric_refs`).

The values are left blank (or pre-seeded with the reference-id list,
for `x_secops_ng` rows) so the integrator can wire them to expressions
that pull from upstream nodes, n8n variables, or operator-bound
connectors. Concretely on this playbook:

| Set node | `in.` rows | `out.` rows | `x_secops_ng.` rows |
|----------|------------|-------------|---------------------|
| `inventory training roster` | `training_window`, `training_scope` | `roster_id` | `control_refs`, `telemetry_refs` |
| `schedule training cycle` | `roster_id`, `training_window` | `cycle_id` | `control_refs`, `telemetry_refs` |
| `run phishing simulation` | `cycle_id`, `training_scope` | `simulation_id` | `control_refs`, `telemetry_refs` |
| `track completion` | `cycle_id`, `simulation_id` | `completion_id` | `control_refs`, `telemetry_refs` |
| `evidence capture` | `roster_id`, `cycle_id`, `simulation_id`, `completion_id`, `training_window` | `attestation_id` | `control_refs`, `telemetry_refs` |
| `notify gaps` | `attestation_id`, `training_scope` | — | `telemetry_refs` |

The lossy translations the emitter notes (workflow-scope variables
flattened onto the trigger, CACAO contract rows surfaced as blank
Set assignments) are recorded in `meta.secops_ng_notes` so the
integrator sees exactly which seams need attention.

## Mirroring policy

The mapping from CACAO to n8n is the same one the compiler implements
for every worked example in this directory:

| CACAO step type    | n8n node type                        |
|--------------------|--------------------------------------|
| `start`            | `n8n-nodes-base.manualTrigger`       |
| `action` (no commands) | `n8n-nodes-base.set` (CACAO I/O contract as assignments) |
| `if-condition`     | `n8n-nodes-base.if`                  |
| `switch-condition` | `n8n-nodes-base.switch`              |
| `end`              | `n8n-nodes-base.noOp`                |

Node ids preserve the CACAO step id verbatim so the two artifacts can
be cross-referenced by id alone. Node labels mirror the CACAO step
`name`. Sequencing (`on_completion` / `on_success` / `on_failure`)
becomes n8n `connections` edges. This playbook is linear: every step
hands off via `on_completion`, so all node-to-node edges land on the
default n8n `main` output.

## What this example deliberately doesn't do

- It does not execute the workflow. The Set nodes carry the CACAO I/O
  contract but the right-hand values are blank — the integrator wires
  them to their own roster-inventory, scheduler, phishing-simulation
  runner, completion tracker, evidence store, and notification
  endpoints.
- It does not ship operator credentials, secrets, or environment-
  specific endpoints. Secrets stay with the operator.
- It does not encode mandatory-training tracks, role-based training
  assignments, phishing-simulation template selection, completion-rate
  / report-rate thresholds, or the wording of the training-owner
  notification — these are intent-bearing values the operator sets
  when binding the workflow to their environment.

## Status

SKELETON — the n8n artifact ships byte-deterministic from the
canonical CACAO source. Detection bindings (missed-training,
simulation-click upstream rule ids) and the per-cohort
training-overdue KPI catalogue entries are owned by CORE / EXTEND
siblings, per the SKELETON note on the canonical playbook.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
n8n is open source (Sustainable Use License) and runs as a Node.js
process: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. The
operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
