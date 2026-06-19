# ransomware_containment — n8n worked example

End-to-end demonstration of the SecOps-NG n8n reference compiler on the
ransomware_containment CACAO playbook. It is aimed at an integrator who
already runs n8n and wants to adopt a portable SecOps-NG playbook
without re-platforming: the example shows exactly which workflow shape
the compiler produces, how the CACAO contract surfaces on each node,
and where the integrator owns the seams.

## Files in this directory

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input mirror)  | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |
| `regenerate.sh`       | (tooling)       | bash script       |
| `README.md`           | —               | This file.        |

The canonical input is the CACAO v2 playbook at
`../../../content/playbooks/ransomware_containment/playbook.cacao.json`
(frozen). Scenario, regulatory anchors, control / metric / telemetry
bindings, and the operator-supplied bindings are documented in that
folder's `README.md`. This folder holds the emitted artifact, a
co-located byte-identical copy of the CACAO source for easy diff
inspection, and the regeneration script.

## How to import

1. In your own n8n instance, open the workflows list and choose
   **Import from File**.
2. Select `workflow.n8n.json` from this directory.
3. n8n loads ten nodes wired into the topology described below. The
   workflow is **inactive** by default — review and bind it to your own
   connectors before activating.

The emitted workflow is a *snapshot of intent*, not a runnable
playbook. The Set nodes carry the CACAO I/O contract as editable
assignments; binding those rows to real connectors (EDR isolation API,
network ACL / SDN fallback, IdP session and token revocation,
backup-verification system, ticketing / paging channel, and the NIS2
Article 23 24-hour early-warning reporting channel) is the operator's
job.

## How to regenerate

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/ransomware_containment/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

```bash
PYTHONPATH=. python -m tools.compile \
    content/playbooks/ransomware_containment/playbook.cacao.json \
    --target n8n \
    --out examples/n8n/ransomware_containment/workflow.n8n.json
```

The drift guard in
`tests/examples/ransomware_containment/test_n8n_workflow.py` fails the
suite if the committed `workflow.n8n.json` diverges from a fresh
regeneration, so the worked example stays honest as the compiler
evolves.

## Topology

The ransomware_containment playbook branches twice, then converges on a
linear containment chain. Ten n8n nodes, one per CACAO step:

1. `ransomware-start` (`manualTrigger`) — entry point; matches the
   CACAO `start` step.
2. `triage signal` (`set`) — collect ransomware indicators from the
   EDR, SIEM, and any anomaly-detection feed the operator already runs.
3. `ransomware confirmed?` (`if`) — branch on the triage outcome.
   `true` routes to the EDR-capability check; `false` routes to the end
   sentinel.
4. `EDR available?` (`if`) — second branch on detection-capability
   availability. `true` routes to the EDR isolation node; `false`
   routes to the network ACL fallback so the playbook still completes
   when the EDR is unavailable.
5. `endpoint isolation — EDR isolate` (`set`) — preferred isolation
   path.
6. `endpoint isolation — network ACL deny (fallback)` (`set`) —
   fallback isolation path.
7. Both isolation branches converge on the linear chain:
   `identity revocation` (`set`) → `backup verification` (`set`) →
   `comms plan` (`set`) → `ransomware-end` (`noOp`).

## CACAO contract surfaces on Set nodes

Every `action`-without-commands step in the CACAO source emits an n8n
`set` node whose **assignments** carry the CACAO contract one row per
field:

- `in.<name>` rows for each entry in the step's `in_args`.
- `out.<name>` rows for each entry in the step's `out_args`.
- `x_secops_ng.<key>` rows for each key under the step's
  `x_secops_ng` block (`detection_refs`, `control_refs`,
  `telemetry_refs`, `metric_refs`, and any KPI hooks).

The values are left blank (or pre-seeded with the reference-id list,
for `x_secops_ng` rows) so the integrator can wire them to expressions
that pull from upstream nodes, n8n variables, or operator-bound
connectors. Concretely on this playbook:

| Set node | `in.` rows | `out.` rows | `x_secops_ng.` rows |
|----------|------------|-------------|---------------------|
| `triage signal` | `signal_id` | `affected_host`, `affected_identity`, `ransomware_confirmed`, `edr_available` | `detection_refs`, `telemetry_refs`, `metric_refs` |
| `endpoint isolation — EDR isolate` | `affected_host` | — | `detection_refs`, `control_refs`, `telemetry_refs`, `metric_refs` |
| `endpoint isolation — network ACL deny (fallback)` | `affected_host` | — | `control_refs`, `telemetry_refs`, `metric_refs` |
| `identity revocation` | `affected_identity` | — | `detection_refs`, `control_refs`, `telemetry_refs`, `metric_refs` |
| `backup verification` | — | `latest_known_good_snapshot`, `snapshot_integrity_ok` | `detection_refs`, `control_refs`, `telemetry_refs`, `metric_refs` |
| `comms plan` | `affected_host`, `affected_identity`, `latest_known_good_snapshot`, `snapshot_integrity_ok` | — | `control_refs`, `telemetry_refs`, `metric_refs` |

The two `if-condition` nodes (`ransomware confirmed?`,
`EDR available?`) emit an n8n `if` node with a placeholder condition
the operator must wire to the upstream `out.*` field. The lossy
translation is recorded in `meta.secops_ng_notes` so the integrator
sees exactly which seams need attention.

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
  them to their own EDR, IdP, backup, ticketing, comms, and reporting
  endpoints.
- It does not ship operator credentials, secrets, or environment-
  specific endpoints. Secrets stay with the operator.
- It does not encode confirmation thresholds, isolation-fallback
  decision rules, or the NIS2 Article 23 24-hour early-warning report
  wording — these are intent-bearing values the operator sets when
  binding the workflow to their environment.
- It does not ship Sigma detection rules (shadow-copy deletion,
  ransomware file rename, overpass-the-hash, etc.). Those are
  referenced from the canonical playbook's `external_references` and
  live upstream at SigmaHQ; the emitter only surfaces the rule
  references on the `x_secops_ng.detection_refs` assignment row of the
  step that acts on a Sigma hit.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
n8n is open source (Sustainable Use License) and runs as a Node.js
process: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. The
operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
