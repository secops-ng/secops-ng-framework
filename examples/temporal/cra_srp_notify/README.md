# cra_srp_notify — Temporal worked example

Worked example: the `playbook.cra_srp_notify@v1` CACAO v2 playbook
compiled by the Temporal reference compiler. Operators who already run
Temporal can import `workflow.temporal.py` into their worker module to
see the topology the emitter produces; binding the activity bodies to
real connectors (SRP intake, ENISA availability, and the operator's
evidence store) is the operator's job.

This worked example is the Temporal leg of the three-target parity lane
for the `cra_srp_notify` playbook (CRA Art.14 SRP notification cascade).
Sibling n8n and LangGraph examples ship alongside under
`../../n8n/cra_srp_notify/` and `../../langgraph/cra_srp_notify/`.

## Source

Canonical CACAO playbook:
`../../../content/playbooks/cra_srp_notify/playbook.cacao.json`. That
folder documents the regulatory anchors (CRA Article 14 early warning /
notification / final report), variables (`__case_id__`,
`__clock_kind__`, `__awareness_ts__`, and the three SRP submission id
outputs), and the two branches of the awareness-anchored parallel.

## Files in this directory

| Path                  | Source compiler         | Format               |
|-----------------------|-------------------------|----------------------|
| `playbook.cacao.json` | (input mirror)          | CACAO v2 JSON        |
| `workflow.temporal.py`| `compilers.temporal`    | Python worker module |
| `regenerate.sh`       | (tooling)               | bash script          |
| `README.md`           | —                       | This file.           |

## How to run

The emitted module is a scaffold: activity functions and the workflow
`run()` raise `NotImplementedError` until the operator wires them to
their SRP intake surface. To import into a Temporal worker:

```python
from workflow_temporal import ACTIVITIES, WORKFLOW  # rename to your import path

worker = Worker(client, task_queue="cra-srp-notify",
                workflows=[WORKFLOW], activities=list(ACTIVITIES))
await worker.run()
```

## How to regenerate

The Temporal emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/temporal/cra_srp_notify/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.temporal.py` via `tools.compile --target temporal`.
Equivalent direct invocation:

```bash
PYTHONPATH=. python -m tools.compile \
    content/playbooks/cra_srp_notify/playbook.cacao.json \
    --target temporal \
    --out examples/temporal/cra_srp_notify/workflow.temporal.py
```

The drift guard in `tests/examples/cra_srp_notify/test_golden.py` fails
the suite if the committed `workflow.temporal.py` diverges from a fresh
regeneration.

## Topology

Five Temporal activities, one CACAO parallel branch fan-out, and the
workflow `run()` orchestrator:

1. `early_warning` — 24h early-warning submission (CRA Art.14). Emits
   `__srp_early_warning_id__`.
2. `wait_until_72h_deadline` — durable timer to `awareness + 72h`. In a
   live worker this is a `workflow.sleep(...)` against the awareness-
   anchored deadline; the emitted scaffold surfaces the intent and
   leaves the sleep body to the operator.
3. `full_notification` — 72h full-notification submission. Emits
   `__srp_full_notification_id__`.
4. `wait_until_final_report_deadline` — durable timer to
   `awareness + 14 days` (Art.14(2) actively-exploited vulnerability) or
   `awareness + 1 month` (Art.14(3) severe incident), selected by
   `__clock_kind__`.
5. `final_report` — final-report submission. Emits
   `__srp_final_report_id__`.

The workflow expresses the 72h clock and the 14d/30d clock as
concurrent branches (CACAO `parallel` step) — they are anchored on the
same `__awareness_ts__`, not on each other, so a live worker fans them
out with `asyncio.gather(...)` or two `execute_activity` calls awaited
in parallel.

## Where the SRP schema TODO lives

Each submission activity docstring carries a `TODO (CORE)` marker
mirroring the canonical CACAO source: the SRP intake schema is not yet
public (Commission page notes a pre-go-live testing period ahead of 11
September 2026). The scaffold's `raise NotImplementedError` body is
where the operator wires the submission payload once the schema is
published.

## What this example deliberately doesn't do

- It does not execute the workflow. Activity bodies raise
  `NotImplementedError` — the operator implements SRP intake, ENISA
  availability, and the awareness-anchored timer sleeps.
- It does not ship the SRP submission payload shape.
- It does not ship operator credentials, secrets, or environment-
  specific endpoints.

## Status

CORE — the Temporal artifact ships byte-deterministic from the canonical
CACAO source. Submission-body wiring waits on the SRP schema
publication; the EXTEND sibling deepens mappings and adds the cookbook
entry.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
Temporal cluster should do. No telemetry flows to this repository or to
the SecOps-NG project. Temporal is open source (MIT) and self-hostable;
running the cluster on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice the operator owns.
