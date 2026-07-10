# security_awareness_training — n8n worked example

End-to-end demonstration of the SecOps-NG n8n reference compiler on
the `security_awareness_training` CACAO playbook. It is aimed at an
integrator who already runs n8n and wants to adopt a portable
SecOps-NG playbook without re-platforming: the example shows exactly
which workflow shape the compiler produces, how the CACAO contract
surfaces on each node, and where the integrator owns the seams.

This worked example pins the n8n leg (target 1 of 3) of the
cross-target parity lane for the `security_awareness_training`
playbook (NIS2 Art.21(2)(g)). The Temporal and LangGraph siblings
ship in the same fan-out under `../../temporal/security_awareness_training/`
and `../../langgraph/security_awareness_training/`; together the three
folders pin the full three-target contract for this playbook.

## Files in this directory

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input mirror)  | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |
| `regenerate.sh`       | (tooling)       | bash script       |
| `README.md`           | —               | This file.        |

The canonical input is the CACAO v2 playbook at
`../../../content/playbooks/security_awareness_training/playbook.cacao.json`.
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
assignments; binding those rows to real connectors (training-needs
assessment surface, curriculum authoring / LMS, delivery dispatch,
per-staff completion store, gap-report notification channel, and the
cycle-review artifact store) is the operator's job.

## How to regenerate

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/security_awareness_training/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

```bash
PYTHONPATH=. python -m tools.compile \
    content/playbooks/security_awareness_training/playbook.cacao.json \
    --target n8n \
    --out examples/n8n/security_awareness_training/workflow.n8n.json
```

The drift guard in
`tests/examples/security_awareness_training/test_n8n_security_awareness_training.py`
fails the suite if the committed `workflow.n8n.json` diverges from a
fresh regeneration, so the worked example stays honest as the compiler
evolves.

## Topology

The security_awareness_training playbook is a linear programme-lifecycle
chain with no conditional branching at the workflow layer: assess,
design, deliver, record, report, review. Eight n8n nodes, one per
CACAO step:

1. `security_awareness_training_start` (`manualTrigger`) — entry point;
   matches the CACAO `start` step. Carries the workflow-scope variables
   (`__training_window__`, `__training_scope__`, …) the operator's
   scheduler or operator-initiated trigger supplies.
2. `schedule assessment` (`set`) — schedule the training-needs
   assessment against the in-scope cohorts for this cycle; emits
   `__assessment_id__`.
3. `design content` (`set`) — design or update the training content
   against the assessment output; emits `__curriculum_id__`.
4. `deliver training` (`set`) — dispatch the training to the in-scope
   cohorts via the operator's learning-management surface; emits
   `__delivery_id__`.
5. `record completion` (`set`) — record per-staff completion against
   the delivery; emits `__completion_id__`.
6. `report gaps` (`set`) — surface the residual gap set to the
   training owner; emits `__gap_report_id__`.
7. `review cycle` (`set`) — close the cycle with a dated cycle-review
   artifact; emits `__cycle_review_id__`.
8. `security_awareness_training_end` (`noOp`) — end sentinel.

## CACAO contract surfaces on Set nodes

Every `action`-without-commands step in the CACAO source emits an n8n
`set` node whose **assignments** carry the CACAO contract one row per
field:

- `in.<name>` rows for each entry in the step's `in_args`.
- `out.<name>` rows for each entry in the step's `out_args`.
- `x_secops_ng.<key>` rows for each key under the step's
  `x_secops_ng` block (`control_refs` at SKELETON; `telemetry_refs`
  and `metric_refs` are owned by EXTEND siblings).

The values are left blank (or pre-seeded with the reference-id list,
for `x_secops_ng` rows) so the integrator can wire them to expressions
that pull from upstream nodes, n8n variables, or operator-bound
connectors. Concretely on this playbook:

| Set node | `in.` rows | `out.` rows | `x_secops_ng.` rows |
|----------|------------|-------------|---------------------|
| `schedule assessment` | `training_window`, `training_scope` | `assessment_id` | `control_refs` |
| `design content` | `assessment_id`, `training_scope` | `curriculum_id` | `control_refs` |
| `deliver training` | `curriculum_id`, `training_scope` | `delivery_id` | `control_refs` |
| `record completion` | `delivery_id`, `training_window` | `completion_id` | `control_refs` |
| `report gaps` | `completion_id`, `assessment_id` | `gap_report_id` | `control_refs` |
| `review cycle` | `assessment_id`, `curriculum_id`, `delivery_id`, `completion_id`, `gap_report_id`, `training_window` | `cycle_review_id` | `control_refs` |

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
  them to their own training-needs assessment, curriculum store, LMS
  delivery, completion tracker, gap-report notification, and cycle-
  review archive endpoints.
- It does not ship operator credentials, secrets, or environment-
  specific endpoints. Secrets stay with the operator.
- It does not encode cohort selection, curriculum thresholds,
  completion cutoffs, gap-report addressees, or cycle-review wording
  — these are intent-bearing values the operator sets when binding
  the workflow to their environment.

## Status

CORE — the n8n artifact ships byte-deterministic from the canonical
CACAO source, alongside the Temporal and LangGraph siblings.
Telemetry emit bindings and per-cohort programme-governance KPIs are
owned by EXTEND siblings, per the SKELETON note on the canonical
playbook.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
n8n is open source (Sustainable Use License) and runs as a Node.js
process: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. The
operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
