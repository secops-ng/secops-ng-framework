# data_subject_rights — n8n worked example

End-to-end demonstration of the SecOps-NG n8n reference compiler on
the `data_subject_rights` CACAO playbook (GDPR Art. 15–22). It is
aimed at an integrator who already runs n8n and wants to adopt a
portable SecOps-NG playbook without re-platforming: the example shows
exactly which workflow shape the compiler produces, how the CACAO
contract surfaces on each node, and where the integrator owns the
seams.

This worked example pins the n8n leg (target 1 of 3) of the
cross-target parity lane for the `data_subject_rights` playbook. The
Temporal and LangGraph siblings ship under
`../../temporal/data_subject_rights/` and
`../../langgraph/data_subject_rights/`; together the three folders
pin the full three-target contract for this playbook.

## Files in this directory

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input mirror)  | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |
| `regenerate.sh`       | (tooling)       | bash script       |
| `README.md`           | —               | This file.        |

The canonical input is the CACAO v2 playbook at
`../../../content/playbooks/data_subject_rights/playbook.cacao.yaml`.
Scenario, regulatory anchors (GDPR Art. 12–22), control / metric /
telemetry bindings, and the operator-supplied bindings are documented
in that folder's `README.md`. This folder holds the emitted artifact,
a co-located mirror of the CACAO source (JSON form for parity with
sibling targets), and the regeneration command.

## How to regenerate

After any change to the canonical playbook or to `compilers/n8n/*`,
refresh the committed artifacts from the repo root:

```sh
./examples/n8n/data_subject_rights/regenerate.sh
```

The script mirrors the canonical CACAO YAML into a byte-deterministic
JSON form and then emits `workflow.n8n.json` via the unified
`tools.compile` CLI. The byte-parity golden test under
`tests/examples/n8n/data_subject_rights/test_golden.py` reruns the
same pipeline and fails if the committed artifact drifts.

## Response-window handling

The 30-day GDPR Article 12(3) response window is derived from the
`__request_received_ts__` playbook variable, not from any
emitter-side clock. This is a G-03 restart-drift invariant asserted
across the three targets by
`tests/patterns/data_subject_rights/test_timer_restart_drift.py`.
Operators binding the intake nodes MUST stamp
`__request_received_ts__` at ingress and MUST NOT let downstream
nodes reach for `$now` / `Date.now()` when computing the deadline.
