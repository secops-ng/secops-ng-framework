# backup_recovery — n8n worked example

End-to-end demonstration of the SecOps-NG n8n reference compiler on the
backup_recovery CACAO playbook. It is aimed at an integrator who already
runs n8n and wants to adopt a portable SecOps-NG playbook without
re-platforming: the example shows exactly which workflow shape the
compiler produces, how the CACAO contract surfaces on each node, and
where the integrator owns the seams.

This worked example opens the n8n end of the cross-target parity lane
for the `backup_recovery` playbook (NIS2 Art.21(2)(c), DORA Art.12).
The Temporal sibling already ships under
`../../temporal/backup_recovery/`; the LangGraph sibling lands in a
separate CORE-FANOUT card. Until all three are committed, this folder
pins the n8n slice of the three-target contract.

## Files in this directory

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input mirror)  | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |
| `regenerate.sh`       | (tooling)       | bash script       |
| `README.md`           | —               | This file.        |

The canonical input is the CACAO v2 playbook at
`../../../content/playbooks/backup_recovery/playbook.cacao.json`.
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
assignments; binding those rows to real connectors (restore-drill
scheduler, backup-integrity verifier, isolated drill-target executor,
dated-attestation evidence store, and the continuity-owner notification
channel) is the operator's job.

## How to regenerate

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/backup_recovery/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

```bash
PYTHONPATH=. python -m tools.compile \
    content/playbooks/backup_recovery/playbook.cacao.json \
    --target n8n \
    --out examples/n8n/backup_recovery/workflow.n8n.json
```

The drift guard in `tests/examples/n8n/backup_recovery/test_golden.py`
fails the suite if the committed `workflow.n8n.json` diverges from a
fresh regeneration, so the worked example stays honest as the compiler
evolves.

## Topology

The backup_recovery playbook is a single conditional branch on the
backup-integrity outcome, then a linear evidence-and-notify chain.
Eight n8n nodes, one per CACAO step:

1. `backup_recovery_start` (`manualTrigger`) — entry point; matches the
   CACAO `start` step. Carries the four `__*__` workflow-scope
   variables (`__drill_window__`, `__backup_scope__`,
   `__candidate_backup_id__`, `__integrity_ok__`, …) the operator's
   scheduler or operator-initiated trigger supplies.
2. `detect restore-drill trigger` (`set`) — resolve the drill window
   and backup scope, then select the most recent backup artifact.
3. `validate backup integrity` (`set`) — run the documented integrity
   checks (checksum, manifest, decryption key availability) and set
   `__integrity_ok__`.
4. `backup integrity ok?` (`if`) — branch on the integrity outcome.
   `true` routes to the restore drill; `false` short-circuits to the
   evidence-capture step with a failure record.
5. `execute restore drill` (`set`) — preferred path: restore the
   selected backup into an isolated drill target.
6. `evidence capture` (`set`) — convergence point: persist a dated
   attestation record covering the drill outcome (success or
   integrity-failure short-circuit).
7. `notify continuity owner` (`set`) — surface the attestation to the
   business-continuity owner via the operator's notification channel.
8. `backup_recovery_end` (`noOp`) — end sentinel.

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
| `detect restore-drill trigger` | `drill_window`, `backup_scope` | `candidate_backup_id` | `control_refs`, `telemetry_refs` |
| `validate backup integrity` | `candidate_backup_id` | `integrity_ok` | `control_refs`, `telemetry_refs`, `metric_refs` |
| `execute restore drill` | `candidate_backup_id`, `backup_scope` | `drill_result` | `control_refs`, `telemetry_refs` |
| `evidence capture` | `candidate_backup_id`, `integrity_ok`, `drill_result` | `attestation_id` | `control_refs`, `telemetry_refs`, `metric_refs` |
| `notify continuity owner` | `attestation_id`, `backup_scope` | — | `telemetry_refs` |

The single `if-condition` node (`backup integrity ok?`) emits an n8n
`if` node with a placeholder condition the operator must wire to the
upstream `out.integrity_ok` field. The lossy translation is recorded
in `meta.secops_ng_notes` so the integrator sees exactly which seams
need attention.

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
becomes n8n `connections` edges.

## What this example deliberately doesn't do

- It does not execute the workflow. The Set nodes carry the CACAO I/O
  contract but the right-hand values are blank — the integrator wires
  them to their own backup, restore-target, evidence-store, and
  notification endpoints.
- It does not ship operator credentials, secrets, or environment-
  specific endpoints. Secrets stay with the operator.
- It does not encode restore-target selection rules, integrity
  thresholds, or the wording of the continuity-owner notification —
  these are intent-bearing values the operator sets when binding the
  workflow to their environment.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
n8n is open source (Sustainable Use License) and runs as a Node.js
process: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. The
operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
