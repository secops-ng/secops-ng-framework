# examples/temporal/dora_tlpt_programme

Worked example: the `playbook.dora_tlpt_programme@v1` CACAO v2
playbook compiled by the Temporal reference compiler. This is the
operator-side lifecycle of the DORA Chapter IV digital operational
resilience testing programme — DORT-scope definition, TLPT-mandatory
decision and competent-authority notification, red-team scoping-
approval binding, and dated competent-authority remediation
attestation, anchored on the ECB TIBER-EU framework as the
implementation reference. Operators who already run Temporal can
import `workflow.temporal.py` into their worker module to see the
topology the emitter produces; binding the activity bodies to real
connectors (business-service / ICT-asset / ICT third-party registers,
competent-authority notification channel, scoping-submission
dispatcher, findings-register store, evidence-store publisher) is the
operator's job.

This worked example pins the Temporal leg (target 2 of 3) of the
cross-target parity lane for the `dora_tlpt_programme` playbook.
The n8n sibling ships under `../../n8n/dora_tlpt_programme/`; the
LangGraph sibling ships under `../../langgraph/dora_tlpt_programme/`.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/dora_tlpt_programme/playbook.cacao.json

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

    ./examples/temporal/dora_tlpt_programme/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.temporal.py` via `tools.compile --target temporal`.

## Status

CORE — the Temporal artifact ships byte-deterministic from the
canonical CACAO source and is pinned by the byte-parity drift guard
under `tests/examples/temporal/dora_tlpt_programme/`. Activity bodies
remain `NotImplementedError` stubs by design; adapter Protocols under
`patterns.dora_tlpt_programme` (competent-authority notification
channel, scoping-submission dispatcher, findings-register store,
evidence-store publisher) and the concrete TLPT-lifecycle primitives
are a follow-on.
