# examples/temporal/ddos_response

Worked example: the `playbook.ddos_response@v1` CACAO v2 playbook
compiled by the Temporal reference compiler. Operators who already run
Temporal can import `workflow.temporal.py` into their worker module to
see the topology the emitter produces; binding the activity bodies to
real connectors (availability-anomaly detector, attack-vector
classifier, mitigation-engagement surface, service-restoration probe,
dated-attestation evidence store, and the incident-management
notification channel) is the operator's job.

This worked example opens the cross-target parity lane for the
`ddos_response` playbook (NIS2 Art.21(2)(b)). The
n8n and LangGraph siblings land in separate CORE-FANOUT cards; until
then, this directory pins the Temporal end of the three-target
contract.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/ddos_response/playbook.cacao.json

Scenario, workflow, regulatory anchors, control / metric / telemetry
bindings, and the operator-supplied bindings are documented in that
folder's `README.md`. This folder holds only the emitted artifact, a
co-located copy of the CACAO source, and the regeneration command.

## Layout

| Path                    | Source compiler      | Format                |
|-------------------------|----------------------|-----------------------|
| `playbook.cacao.json`   | (input)              | CACAO v2 JSON         |
| `workflow.temporal.py`  | `compilers.temporal` | Python (`temporalio`) |

## Regeneration

Deterministic emitter; re-running yields byte-identical output. From
the repo root:

    ./examples/temporal/ddos_response/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.temporal.py` via `tools.compile --target temporal`.

## Status

Bound — the Temporal artifact ships byte-deterministic from the
canonical CACAO source, and all six `@activity.defn` bodies import and
call their deterministic primitive from
`content/playbooks/ddos_response/primitives/`. `NotImplementedError`
marks only the operator-integration seams (monitoring ingress,
response surface, evidence store, owner channel). The per-target
byte-parity goldens across n8n + Temporal + LangGraph live under
`tests/examples/`.
