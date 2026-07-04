# dora_ict_risk_selfassess — n8n worked example

End-to-end demonstration of the SecOps-NG n8n reference compiler on
the `dora_ict_risk_selfassess` CACAO playbook (DORA Chapter II ICT
risk management operator self-assessment roll-up). It is aimed at an
integrator who already runs n8n and wants to adopt a portable
SecOps-NG playbook without re-platforming: the example shows exactly
which workflow shape the compiler produces, how the CACAO contract
surfaces on each node, and where the integrator owns the seams.

This worked example pins the n8n leg (target 1 of 3) of the
cross-target parity lane for the `dora_ict_risk_selfassess` playbook.
The Temporal and LangGraph siblings ship under
`../../temporal/dora_ict_risk_selfassess/` and
`../../langgraph/dora_ict_risk_selfassess/`; together the three
folders pin the full three-target contract for this playbook.

## Files in this directory

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input mirror)  | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |
| `regenerate.sh`       | (tooling)       | bash script       |
| `README.md`           | —               | This file.        |

The canonical input is the CACAO v2 playbook at
`../../../content/playbooks/dora_ict_risk_selfassess/playbook.cacao.json`.
Scenario, regulatory anchors, control / metric / telemetry bindings,
and the operator-supplied bindings are documented in that folder's
`README.md`. This folder holds the emitted artifact, a co-located
byte-identical copy of the CACAO source for easy diff inspection, and
the regeneration script.

## How to import

1. In your own n8n instance, open the workflows list and choose
   **Import from File**.
2. Select `workflow.n8n.json` from this directory.
3. n8n loads six nodes wired into the topology described below. The
   workflow is **inactive** by default — review and bind it to your
   own connectors before activating.

The emitted workflow is a *snapshot of intent*, not a runnable
playbook. The Set nodes carry the CACAO I/O contract as editable
assignments; binding those rows to real connectors (the operator's
evidence-store adapter, per-section coverage rubric, and dated
attestation artifact template) is the operator's job.

## How to regenerate

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/dora_ict_risk_selfassess/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

```bash
PYTHONPATH=. python -m tools.compile \
    content/playbooks/dora_ict_risk_selfassess/playbook.cacao.json \
    --target n8n \
    --out examples/n8n/dora_ict_risk_selfassess/workflow.n8n.json
```

The drift guard in
`tests/examples/n8n/dora_ict_risk_selfassess/test_golden.py` fails
the suite if the committed `workflow.n8n.json` diverges from a fresh
regeneration, so the worked example stays honest as the compiler
evolves.

## Topology

The dora_ict_risk_selfassess playbook is a linear
collect-map-score-attest chain with no conditional branching at the
workflow layer. Six n8n nodes, one per CACAO step:

1. `dora_ict_risk_selfassess_start` (`manualTrigger`) — entry point;
   matches the CACAO `start` step. Carries the workflow-scope
   variable (`__assessment_window__`) the operator's scheduler,
   Art. 6(5) annual-review trigger, or supervisory-authority request
   supplies.
2. `collect section evidence` (`set`) — collect evidence from the
   operator's evidence store keyed on the five DORA Chapter II ICT
   risk management section atoms (Art. 6 framework, Art. 7 systems /
   protocols / tools, Art. 8 identification, Art. 10 detection,
   Art. 11 response and recovery); emits `__section_atoms__` and
   `__evidence_set_id__`.
3. `map evidence to sections` (`set`) — bind each collected evidence
   record to the section it discharges plus the originating playbook
   slug under the SecOps-NG content-model overlay; emits
   `__section_mapping__`.
4. `score per-section coverage` (`set`) — score each of the five
   sections against the operator's documented coverage rubric
   (present-and-current / present-but-stale / absent-with-declared-
   exception / absent-uncovered); emits `__section_scoring__`.
5. `report attestation` (`set`) — assemble the durable per-section
   attestation artifact plus the whole-Chapter roll-up verdict; emits
   `__attestation_id__`.
6. `dora_ict_risk_selfassess_end` (`noOp`) — end sentinel.

## CACAO contract surfaces on Set nodes

Every `action`-without-commands step in the CACAO source emits an n8n
`set` node whose **assignments** carry the CACAO contract one row per
field:

- `in.<name>` rows for each entry in the step's `in_args`.
- `out.<name>` rows for each entry in the step's `out_args`.
- `x_secops_ng.<key>` rows for each key under the step's
  `x_secops_ng` block (`control_refs`, `telemetry_refs`,
  `metric_refs`).

The values are left blank (or pre-seeded with the reference-id list,
for `x_secops_ng` rows) so the integrator can wire them to expressions
that pull from upstream nodes, n8n variables, or operator-bound
connectors.

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
  them to their own evidence-store adapter, per-section coverage
  rubric, and dated attestation artifact template.
- It does not ship operator credentials, secrets, or environment-
  specific endpoints. Secrets stay with the operator.
- It does not encode the operator's authoritative Chapter II
  section attribution, coverage-verdict thresholds, or the wording of
  the attestation report — these are intent-bearing values the
  operator sets when binding the workflow to their environment.

## Status

CORE — the n8n artifact ships byte-deterministic from the canonical
CACAO source. The operator-facing attestation-report renderer and the
community cookbook CORE entry land in the EXTEND tier.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
n8n is open source (Sustainable Use License) and runs as a Node.js
process: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. The
operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
