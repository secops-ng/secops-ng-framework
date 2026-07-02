# cra_srp_notify — n8n worked example

End-to-end demonstration of the SecOps-NG n8n reference compiler on the
`cra_srp_notify` CACAO playbook. Aimed at an integrator who already runs
n8n and wants to adopt the CRA Article 14 notification cascade without
re-platforming: the example shows the workflow shape the compiler
produces, how the CACAO durable-delay contract surfaces on each node,
and where the integrator owns the seams (SRP intake binding, evidence
capture, ENISA availability).

This worked example is the n8n leg of the three-target parity lane for
the `cra_srp_notify` playbook (CRA Art.14 SRP notification cascade).
Sibling Temporal and LangGraph examples ship alongside under
`../../temporal/cra_srp_notify/` and `../../langgraph/cra_srp_notify/`.

## Files in this directory

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input mirror)  | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |
| `regenerate.sh`       | (tooling)       | bash script       |
| `README.md`           | —               | This file.        |

The canonical input is the CACAO v2 playbook at
`../../../content/playbooks/cra_srp_notify/playbook.cacao.json`.
Regulatory anchors (CRA Article 14, SRP intake, ENISA availability),
control / metric / telemetry bindings, and the awareness-anchored clocks
are documented on that canonical source. This folder holds the emitted
artifact, a co-located byte-identical copy of the CACAO source for easy
diff inspection, and the regeneration script.

## How to import

1. In your own n8n instance, open the workflows list and choose
   **Import from File**.
2. Select `workflow.n8n.json` from this directory.
3. n8n loads the seven-node topology described below. The workflow is
   **inactive** by default — bind the SRP intake and evidence-store
   connectors before activating.

The emitted workflow is a *snapshot of intent*, not a runnable playbook.
The Set nodes carry the CACAO I/O contract (case id, clock kind,
awareness timestamp, submission-id outputs) as editable assignments; the
integrator binds them to their own SRP intake surface once the SRP
schema is public.

## How to regenerate

The n8n emitter is deterministic: same input bytes in, same output bytes
out. From the repo root:

    ./examples/n8n/cra_srp_notify/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

```bash
PYTHONPATH=. python -m tools.compile \
    content/playbooks/cra_srp_notify/playbook.cacao.json \
    --target n8n \
    --out examples/n8n/cra_srp_notify/workflow.n8n.json
```

The drift guard in `tests/examples/cra_srp_notify/test_golden.py` fails
the suite if the committed `workflow.n8n.json` diverges from a fresh
regeneration, so the worked example stays honest as the compiler
evolves.

## Topology

The CRA Article 14 cascade branches after the 24h early warning so the
72h clock and the 14d-or-30d final-report clock run concurrently — the
two later deadlines are anchored on the same awareness timestamp, not on
each other. Seven n8n nodes, one per CACAO step:

1. `cra_srp_notify_start` (`manualTrigger`) — entry point; carries the
   workflow-scope variables (`__case_id__`, `__clock_kind__`,
   `__awareness_ts__`, and the three submission-id outputs) that the
   upstream classifier or scheduler supplies.
2. `early_warning` (`set`) — 24h early-warning submission to the SRP,
   with simultaneous availability to ENISA per Article 14. Emits
   `__srp_early_warning_id__`.
3. `run 72h + final-report clocks in parallel` (`set` / fan-out) — CACAO
   `parallel` step; fans out to the two durable-delay branches.
4. `wait until 72h deadline` (`set`) — durable wait to `awareness + 72h`.
   The n8n rendering carries the delay as an editable assignment; a live
   integrator swaps it for an `n8n-nodes-base.wait` node against their
   own timer surface.
5. `full_notification` (`set`) — 72h full-notification submission. Emits
   `__srp_full_notification_id__`.
6. `wait until final-report deadline` (`set`) — durable wait to
   `awareness + 14d` (Art.14(2) actively-exploited vulnerability) or
   `awareness + 1 month` (Art.14(3) severe incident), selected by
   `__clock_kind__`.
7. `final_report` (`set`) — final-report submission. Emits
   `__srp_final_report_id__`.
8. `cra_srp_notify_end` (`noOp`) — end sentinel.

## Where the SRP schema TODO lives

The three submission steps (`early_warning`, `full_notification`,
`final_report`) each carry a `TODO (CORE)` marker on the CACAO source
description because the SRP intake schema is not yet public — the
Commission's CRA reporting page notes a pre-go-live testing period ahead
of 11 September 2026. The Set-node assignments compile through as
placeholder rows; a follow-up card lands the schema-conformant payload
builder once the SRP schema is published.

## CACAO contract surfaces on Set nodes

Every `action`-without-commands step in the CACAO source emits an n8n
`set` node whose **assignments** carry the CACAO contract one row per
field:

- `in.<name>` rows for each entry in the step's `in_args`.
- `out.<name>` rows for each entry in the step's `out_args`.
- `x_secops_ng.<key>` rows for each key under the step's `x_secops_ng`
  block (`control_refs`, `telemetry_refs`, `metric_refs`).

The values are left blank (or pre-seeded with the reference-id list, for
`x_secops_ng` rows) so the integrator can wire them to expressions that
pull from upstream nodes, n8n variables, or operator-bound connectors.

The lossy translations the emitter notes (workflow-scope variables
flattened onto the trigger, CACAO contract rows surfaced as blank Set
assignments) are recorded in `meta.secops_ng_notes` so the integrator
sees exactly which seams need attention.

## What this example deliberately doesn't do

- It does not execute the workflow. The Set nodes carry the CACAO I/O
  contract but the right-hand values are blank until the integrator
  binds SRP intake, ENISA availability, and the operator's evidence
  store.
- It does not ship the SRP submission payload shape — the SRP intake
  schema is not yet public and both n8n and its siblings mark the
  payload rows `TODO (CORE)`.
- It does not ship operator credentials, secrets, or environment-
  specific endpoints. Secrets stay with the operator.

## Status

CORE — the n8n artifact ships byte-deterministic from the canonical
CACAO source. Submission-body wiring waits on the SRP schema
publication (Commission pre-go-live testing period ahead of 11 September
2026); the EXTEND sibling deepens mappings and adds the cookbook entry.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no identifying
data flows to this repository or to the SecOps-NG project. n8n runs as a
Node.js process; hosting it on EU sovereign infrastructure (Nebul,
OVHcloud, Scaleway, Hetzner) is a deployment choice, not a vendor
decision. The operator runs n8n on infrastructure they control — we ship
the structure, they own the data plane.
