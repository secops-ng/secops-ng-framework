# examples/temporal/cryptographic_controls

Worked example: the `playbook.cryptographic_controls@v1` CACAO v2
playbook compiled by the Temporal reference compiler. This is the
write-side lifecycle counterpart to `crypto_posture_management`:
key-generate / key-rotate / key-revoke, encryption-enforcement gate
against declared at-rest and in-transit floors, certificate issue /
renew / revoke, dated lifecycle attestation. Operators who already
run Temporal can import `workflow.temporal.py` into their worker
module to see the topology the emitter produces; binding the activity
bodies to real connectors (crypto-policy inventory, KMS backend, CA
backend, storage-encryption and TLS-endpoint backends, evidence
store, cryptography-owner notification channel) is the operator's
job.

This worked example pins the Temporal leg (target 2 of 3) of the
cross-target parity lane for the `cryptographic_controls` playbook.
The n8n sibling ships under `../../n8n/cryptographic_controls/`; the
LangGraph sibling ships under `../../langgraph/cryptographic_controls/`.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/cryptographic_controls/playbook.cacao.json

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

    ./examples/temporal/cryptographic_controls/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.temporal.py` via `tools.compile --target temporal`.

## Status

CORE — the Temporal artifact ships byte-deterministic from the
canonical CACAO source and is pinned by the byte-parity drift guard
under `tests/examples/temporal/cryptographic_controls/`. Activity
bodies remain `NotImplementedError` stubs by design; adapter Protocols
under `patterns.cryptographic_controls` (KMS backend, CA backend,
storage-encryption backend, TLS-endpoint backend) and the enforcement-
gate policy evaluator are a follow-on.
