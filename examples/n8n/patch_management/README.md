# patch_management — n8n worked example

End-to-end demonstration of the SecOps-NG n8n reference compiler on the
patch_management CACAO playbook. It is aimed at an integrator who
already runs n8n and wants to adopt a portable SecOps-NG playbook
without re-platforming: the example shows exactly which workflow shape
the compiler produces, how the CACAO contract surfaces on each node,
and where the integrator owns the seams.

This worked example pins the n8n end of the cross-target parity ring
for the `patch_management` playbook (NIS2 Art.21(2)(e) — security in
acquisition, development and maintenance). Temporal and LangGraph
siblings land in separate cards; until all three are committed, this
folder pins the n8n slice of the three-target contract.

## Files in this directory

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input mirror)  | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |
| `regenerate.sh`       | (tooling)       | bash script       |
| `README.md`           | —               | This file.        |

The canonical input is the CACAO v2 playbook at
`../../../content/playbooks/patch_management/playbook.cacao.json`.
Scenario, regulatory anchors, control / metric / telemetry bindings,
and the operator-supplied bindings are documented in that folder's
`README.md`. This folder holds the emitted artifact, a co-located
byte-identical copy of the CACAO source for easy diff inspection, and
the regeneration script.

## How to import

1. In your own n8n instance, open the workflows list and choose
   **Import from File**.
2. Select `workflow.n8n.json` from this directory.
3. n8n loads nine nodes wired into the topology described below. The
   workflow is **inactive** by default — review and bind it to your own
   connectors before activating.

The emitted workflow is a *snapshot of intent*, not a runnable
playbook. The Set nodes carry the CACAO I/O contract as editable
assignments; binding those rows to real connectors (advisory-intake
surface, patch-criticality classifier, deployment-ring scheduler,
canary-health probe, broad-ring rollout surface, dated-attestation
evidence store, and the maintenance-owner notification channel) is the
operator's job.

## How to regenerate

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/patch_management/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

```bash
PYTHONPATH=. python -m tools.compile \
    content/playbooks/patch_management/playbook.cacao.json \
    --target n8n \
    --out examples/n8n/patch_management/workflow.n8n.json
```

The drift guard in `tests/examples/n8n/patch_management/test_golden.py`
fails the suite if the committed `workflow.n8n.json` diverges from a
fresh regeneration, so the worked example stays honest as the compiler
evolves.

## Topology

The patch_management playbook is a linear chain — detect, classify,
stage, validate-canary, fan-out, evidence, notify. Nine n8n nodes, one
per CACAO step:

1. `patch_management_start` (`manualTrigger`) — entry point; matches
   the CACAO `start` step. Carries the `__*__` workflow-scope variables
   (`__update_subject__`, `__update_reference__`,
   `__patch_criticality__`, `__staged_ring_id__`, `__canary_healthy__`,
   `__broad_rollout_id__`, `__evidence_id__`) the operator's
   advisory-intake surface or operator-initiated trigger supplies.
2. `detect patch availability` (`set`) — confirm a security update is
   available against a tracked package / image / firmware line in the
   operator's documented deployment inventory.
3. `classify patch criticality` (`set`) — categorise the update against
   the operator's documented patch-criticality taxonomy
   (security-critical, security-routine, feature-only), or leave empty
   when classification could not be completed within the documented
   intake deadline.
4. `stage rollout to canary ring` (`set`) — engage the update against
   the documented canary / test-fleet ring named in the operator's
   deployment-ring topology.
5. `validate canary` (`set`) — probe the canary ring against the
   documented health gates (functional probes, error-rate / latency
   deviation, rollback readiness) and set `__canary_healthy__`.
6. `fan out to broad rings` (`set`) — exercise the operator's
   pre-bound broad-ring rollout surface; populates
   `__broad_rollout_id__` on a green canary, left empty on the
   canary-unhealthy branch.
7. `evidence capture` (`set`) — persist a dated patch-application
   attestation record covering the update (criticality, canary
   outcome, broad-rollout reference).
8. `notify maintenance owner` (`set`) — surface the attestation to the
   maintenance owner via the operator's notification channel.
9. `patch_management_end` (`noOp`) — end sentinel.

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
| `detect patch availability` | `update_subject`, `update_reference` | — | `control_refs`, `telemetry_refs`, `metric_refs` |
| `classify patch criticality` | `update_subject`, `update_reference` | `patch_criticality` | `control_refs`, `telemetry_refs`, `metric_refs` |
| `stage rollout to canary ring` | `update_subject`, `update_reference`, `patch_criticality` | `staged_ring_id` | `control_refs`, `telemetry_refs`, `metric_refs` |
| `validate canary` | `update_subject`, `staged_ring_id` | `canary_healthy` | `control_refs`, `telemetry_refs`, `metric_refs` |
| `fan out to broad rings` | `update_subject`, `update_reference`, `staged_ring_id`, `canary_healthy` | `broad_rollout_id` | `control_refs`, `telemetry_refs`, `metric_refs` |
| `evidence capture` | `update_subject`, `update_reference`, `patch_criticality`, `staged_ring_id`, `canary_healthy`, `broad_rollout_id` | `evidence_id` | `control_refs`, `telemetry_refs`, `metric_refs` |
| `notify maintenance owner` | `evidence_id`, `update_subject`, `canary_healthy` | — | `telemetry_refs`, `metric_refs` |

The playbook is a linear chain (no `if-condition` / `switch-condition`
nodes); the short-circuit behaviour for an unclassified update or an
unhealthy canary is carried inside the CACAO step bodies via the
operator-bound expressions on the Set rows, not as a topology branch.
The lossy translation per step is recorded in `meta.secops_ng_notes` so
the integrator sees exactly which seams need attention.

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
  them to their own advisory-intake, classifier, ring-scheduler,
  canary-health-probe, broad-rollout, evidence-store, and notification
  endpoints.
- It does not ship operator credentials, secrets, or environment-
  specific endpoints. Secrets stay with the operator.
- It does not encode patch-criticality taxonomy rules, canary-health
  thresholds, rollout cadences, or the wording of the
  maintenance-owner notification — these are intent-bearing values the
  operator sets when binding the workflow to their environment.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
n8n is open source (Sustainable Use License) and runs as a Node.js
process: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. The
operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
