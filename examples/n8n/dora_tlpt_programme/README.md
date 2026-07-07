# dora_tlpt_programme — n8n worked example

End-to-end demonstration of the SecOps-NG n8n reference compiler on
the `dora_tlpt_programme` CACAO playbook. This is the operator-side
lifecycle of the DORA Chapter IV digital operational resilience
testing programme — Article 24 (general requirements for the testing
of digital operational resilience) and Article 26 (advanced testing
of ICT tools, systems and processes based on threat-led penetration
testing), anchored on the ECB TIBER-EU framework as the implementation
reference. Distinct from the `dora_ict_risk_selfassess` whole-Chapter II
roll-up: this playbook is the Chapter IV testing-programme discipline.

This worked example pins the n8n leg (target 1 of 3) of the
cross-target parity lane for the `dora_tlpt_programme` playbook. The
Temporal sibling ships under `../../temporal/dora_tlpt_programme/`; the
LangGraph sibling ships under `../../langgraph/dora_tlpt_programme/`.
Together the three folders pin the full three-target contract for this
playbook.

## Files in this directory

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input mirror)  | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |
| `regenerate.sh`       | (tooling)       | bash script       |
| `README.md`           | —               | This file.        |

The canonical input is the CACAO v2 playbook at
`../../../content/playbooks/dora_tlpt_programme/playbook.cacao.json`.
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
   workflow is **inactive** by default — review and bind it to your own
   connectors before activating.

The emitted workflow is a *snapshot of intent*, not a runnable
playbook. The Set nodes carry the CACAO I/O contract as editable
assignments; binding those rows to real connectors (business-service /
ICT-asset / ICT third-party registers for the scope step, competent-
authority notification channel for the trigger-gate and scoping-approval
steps, findings-register store and evidence-store publisher for the
remediation-tracking step) is the operator's job.

## How to regenerate

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/dora_tlpt_programme/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

```bash
PYTHONPATH=. python -m tools.compile \
    content/playbooks/dora_tlpt_programme/playbook.cacao.json \
    --target n8n \
    --out examples/n8n/dora_tlpt_programme/workflow.n8n.json
```

The drift guard in
`tests/examples/n8n/dora_tlpt_programme/test_golden.py` fails the
suite if the committed `workflow.n8n.json` diverges from a fresh
regeneration, so the worked example stays honest as the compiler
evolves.

## Topology

The dora_tlpt_programme playbook is a linear four-step lifecycle:
define-DORT-scope / TLPT-trigger-and-planning-gate / red-team-scoping-
approval / remediation-tracking. Six n8n nodes, one per CACAO step:

1. `dora_tlpt_programme_start` (`manualTrigger`) — entry point.
   Carries the workflow-scope variables (`__testing_window__`,
   `__entity_significance_tier__`) the operator's governance surface,
   scheduler, or supervisory trigger supplies.
2. `define DORT scope` (`set`) — resolve the DORT-scope catalogue
   against the operator's business-service / ICT-asset / ICT
   third-party registers per DORA Art. 24; emits
   `__dort_scope_catalogue__`.
3. `TLPT trigger and planning gate` (`set`) — evaluate whether TLPT
   is mandatory in the current window against the JC 2022 03 criteria
   and the operator's declared significance tier per DORA Art. 26(1);
   emits `__tlpt_trigger_decision__`.
4. `red-team scoping approval` (`set`) — package the red-team scoping
   submission for competent-authority approval per DORA Art. 26(3);
   emits `__red_team_scoping_id__`.
5. `remediation tracking` (`set`) — compose the findings register and
   emit the dated competent-authority remediation attestation per
   DORA Art. 26(8); emits `__findings_register_id__` and
   `__remediation_attestation_id__`.
6. `dora_tlpt_programme_end` (`noOp`) — end sentinel.

## CACAO contract surfaces on Set nodes

Every `action`-without-commands step in the CACAO source emits an n8n
`set` node whose **assignments** carry the CACAO contract one row per
field:

- `in.<name>` rows for each entry in the step's `in_args`.
- `out.<name>` rows for each entry in the step's `out_args`.
- `x_secops_ng.<key>` rows for each key under the step's
  `x_secops_ng` block (`control_refs`, `telemetry_refs`).

The values are left blank (or pre-seeded with the reference-id list,
for `x_secops_ng` rows) so the integrator can wire them to expressions
that pull from upstream nodes, n8n variables, or operator-bound
connectors.

The lossy translations the emitter notes (workflow-scope variables
flattened onto the trigger, CACAO contract rows surfaced as blank Set
assignments) are recorded in `meta.secops_ng_notes` so the integrator
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
becomes n8n `connections` edges. This playbook is linear: every step
hands off via `on_completion`, so all node-to-node edges land on the
default n8n `main` output.

## What this example deliberately doesn't do

- It does not execute the workflow. The Set nodes carry the CACAO I/O
  contract but the right-hand values are blank — the integrator wires
  them to their own business-service register, ICT-asset register,
  ICT third-party register, competent-authority notification channel,
  scoping-submission dispatcher, findings-register store, and
  evidence-store publisher.
- It does not ship operator credentials, secrets, or environment-
  specific endpoints. Secrets stay with the operator.
- It does not encode the operator's declared significance tier, the
  JC 2022 03 criteria evaluation, the mandatory-TLPT-cycle cadence,
  the tester-selection criteria under Art. 27, the severity rubric,
  the remediation-timeline model, or the wording of the competent-
  authority attestation — these are intent-bearing values the
  operator sets when binding the workflow to their environment.

## Status

CORE — the n8n artifact ships byte-deterministic from the canonical
CACAO source and is pinned by the byte-parity drift guard under
`tests/examples/n8n/dora_tlpt_programme/`. Adapter Protocols under
`patterns.dora_tlpt_programme` (competent-authority notification
channel, scoping-submission dispatcher, findings-register store,
evidence-store publisher) and the concrete TLPT-lifecycle primitives
are a follow-on; the cookbook walkthrough for operators lands in the
sibling EXTEND card.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
n8n is open source (Sustainable Use License) and runs as a Node.js
process: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. The
operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
