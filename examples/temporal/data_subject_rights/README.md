# examples/temporal/data_subject_rights

Worked example: the `data_subject_rights` CACAO v2 playbook
(GDPR Art. 15–22) compiled by the Temporal reference compiler.
Operators who already run Temporal can import `workflow.temporal.py`
into their worker module to see the topology the emitter produces;
binding the activity bodies to real connectors (subject-facing intake
surface, sovereign IdP verification, data-owner routing catalogue,
fulfilment-pack assembler, subject-facing response envelope, and the
evidence-store outcome writer) is the operator's job.

This worked example pins the Temporal leg (target 2 of 3) of the
cross-target parity lane for the `data_subject_rights` playbook. The
n8n and LangGraph siblings ship under `../../n8n/data_subject_rights/`
and `../../langgraph/data_subject_rights/`.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/data_subject_rights/playbook.cacao.yaml

Scenario, workflow, regulatory anchors, control / metric / telemetry
bindings, and the operator-supplied bindings are documented in that
folder's `README.md`. This folder holds only the emitted artifact, a
co-located JSON mirror of the CACAO source, and the regeneration
command.

## Layout

| Path                    | Source compiler      | Format                |
|-------------------------|----------------------|-----------------------|
| `playbook.cacao.json`   | (input mirror)       | CACAO v2 JSON         |
| `workflow.temporal.py`  | `compilers.temporal` | Python (Temporal SDK) |
| `regenerate.sh`         | (tooling)            | bash script           |
| `README.md`             | —                    | This file             |

## How to regenerate

After any change to the canonical playbook or to
`compilers/temporal/*`, refresh the committed artifacts from the repo
root:

```sh
./examples/temporal/data_subject_rights/regenerate.sh
```

The byte-parity golden test under
`tests/examples/temporal/data_subject_rights/test_golden.py` reruns
the emitter and fails if the committed artifact drifts.

## Response-window handling (G-03 restart-drift row)

Article 12(3) declares a one-month response window from the moment
the request is received. The Temporal activity signatures thread
`request_received_ts` through as an activity argument — the deadline
is derived from that external playbook-scoped input rather than from
`datetime.utcnow()` at the worker's current wall-clock. A worker
restart mid-workflow re-hydrates the same deadline. See
`tests/patterns/data_subject_rights/test_timer_restart_drift.py` for
the invariant asserted across all three targets.
