# cra_cvd — Temporal worked example

Worked example: the `playbook.cra_cvd@v1` CACAO v2 playbook compiled by
the Temporal reference compiler. Operators who already run Temporal can
import `workflow.temporal.py` into their worker module to see the
topology the emitter produces; binding the activity bodies to real
connectors (reporter channel, CVE-request adapter, CSIRT-coordination
adapter, PGP-signed delivery, and the operator's evidence store) is the
operator's job.

This worked example is the Temporal leg of the three-target parity lane
for the `cra_cvd` playbook. Sibling n8n and LangGraph examples ship
alongside under `../../n8n/cra_cvd/` and `../../langgraph/cra_cvd/`.

## Source

Canonical CACAO playbook:
`../../../content/playbooks/cra_cvd/playbook.cacao.json`. That folder
documents the regulatory anchors (CRA Article 14 §1 CVD policy and §6
acknowledgement window), variables (case id, reporter contact,
acknowledgement timestamp, triage verdict, fix reference,
actively-exploited flag, disclosure target date, advisory id, reporter
credit display), and the linear seven-step disclosure lifecycle.

## Files in this directory

| Path                  | Source compiler         | Format               |
|-----------------------|-------------------------|----------------------|
| `playbook.cacao.json` | (input mirror)          | CACAO v2 JSON        |
| `workflow.temporal.py`| `compilers.temporal`    | Python worker module |
| `regenerate.sh`       | (tooling)               | bash script          |
| `README.md`           | —                       | This file.           |

## How to run

The emitted module is a scaffold: activity functions and the workflow
`run()` raise `NotImplementedError` until the operator wires them to the
reporter channel and the three adapter surfaces. To import into a
Temporal worker:

```python
from workflow_temporal import ACTIVITIES, WORKFLOW  # rename to your import path

worker = Worker(client, task_queue="cra-cvd",
                workflows=[WORKFLOW], activities=list(ACTIVITIES))
await worker.run()
```

## How to regenerate

The Temporal emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/temporal/cra_cvd/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.temporal.py` via `tools.compile --target temporal`.
Equivalent direct invocation:

```bash
PYTHONPATH=. python -m tools.compile \
    content/playbooks/cra_cvd/playbook.cacao.json \
    --target temporal \
    --out examples/temporal/cra_cvd/workflow.temporal.py
```

The drift guard in `tests/examples/cra_cvd/test_golden.py` fails the
suite if the committed `workflow.temporal.py` diverges from a fresh
regeneration.

## Topology

Seven Temporal activities plus the workflow `run()` orchestrator,
wiring the CACAO seven-step disclosure chain:

1. `intake` — receive the reporter's submission and write the durable
   receipt used by the CRA Art. 14 §6 acknowledgement-SLA clock.
2. `ack_to_reporter` — dispatch the acknowledgement letter (see
   `content/playbooks/cra_cvd/templates/ack_letter.j2`) via the
   operator-bound reporter channel. Records `__reporter_ack_ts__`.
3. `triage` — evaluate reproducibility, severity, and actively-exploited
   status. Emits `__triage_verdict__` and `__actively_exploited__`
   (the latter is the join key against a sibling `cra_srp_notify` run
   if the case trips CRA Art. 14(2)).
4. `develop_fix` — capture the internal fix reference. Emits
   `__fix_ref__`.
5. `validate_fix` — validate the fix against the reporter's reproduction
   (with reporter cooperation where consented).
6. `coordinate_disclosure` — set the disclosure target date, request a
   CVE (CVE-request adapter), and — where a national CSIRT is
   co-coordinating — open the CSIRT-coordination hold. Emits
   `__disclosure_target_date__`.
7. `publish_advisory` — publish the CSAF 2.0 advisory (see
   `content/playbooks/cra_cvd/templates/advisory.csaf2.json.j2`) and
   the human-readable advisory (`advisory.md.j2`). Emits
   `__advisory_id__`.

The workflow is linear — every step's `on_completion` points at the
next. A live worker `execute_activity`s each stage in order; retry
policy, heartbeat cadence, and timeout are operator-owned.

## Where the reporter-communications and adapter TODOs live

Three activities are adapter-bound (`ack_to_reporter`,
`coordinate_disclosure`, `publish_advisory`). Each carries a docstring
mirroring the canonical CACAO description; the `raise NotImplementedError`
body is where the operator wires:

- **Reporter channel** — outbound mail or PGP-signed delivery
  (`patterns.cra_cvd.PGPDeliveryRequest`).
- **CVE-request adapter** — CNA request; the reference contract lives
  at `patterns.cra_cvd.CVERequest` / `CVERequestResponse`.
- **CSIRT-coordination adapter** — for cases requiring national CSIRT
  coordination; contract at `patterns.cra_cvd.CSIRTCoordinationRequest`.

## What this example deliberately doesn't do

- It does not execute the workflow. Activity bodies raise
  `NotImplementedError` — the operator implements the reporter channel,
  the CVE-request adapter, the CSIRT-coordination adapter, and the
  evidence store.
- It does not ship CNA API tokens, CSIRT-coordination endpoints, or
  PGP secret keys. Secrets stay with the operator.
- It does not select a CNA — that is an operator policy decision.

## Status

CORE-PRIM — the Temporal artifact ships byte-deterministic from the
canonical CACAO source. Adapter wiring stays operator-owned; the CORE
siblings have all landed and this three-target example closes the
G-03 byte-parity gap.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
Temporal cluster should do. No telemetry flows to this repository or to
the SecOps-NG project. Temporal is open source (MIT) and self-hostable;
running the cluster on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice the operator owns.
