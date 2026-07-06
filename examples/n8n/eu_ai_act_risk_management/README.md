# examples/n8n/eu_ai_act_risk_management

Worked example: the `playbook.eu_ai_act_risk_management@v1` CACAO v2
playbook compiled by the n8n reference compiler. Operators can import
`workflow.n8n.json` directly into an n8n instance to see the topology
the emitter produces; binding the placeholder Set-node steps to real
connectors (AI-system inventory, Annex III use-case catalogue,
risk-register store, technical-documentation bundle store, and the
post-market monitoring signal source) is the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/eu_ai_act_risk_management/playbook.cacao.json

Scenario, workflow, regulatory anchors (EU AI Act Art. 6 / 9 / 11 /
Annex IV / 72), and OSCAL / D3FEND control bindings are documented in
that folder's `mappings.yaml`. This folder holds the emitted artifact,
a co-located byte-identical copy of the CACAO source for easy diff
inspection, and the regeneration script.

## Layout

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input mirror)  | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |
| `regenerate.sh`       | (tooling)       | bash script       |

## How to import

1. In your own n8n instance, open the workflows list and choose
   **Import from File**.
2. Select `workflow.n8n.json` from this directory.
3. n8n loads the nodes wired into the topology described in the
   canonical playbook. The workflow is **inactive** by default —
   review and bind it to your own connectors before activating.

The emitted workflow is a *snapshot of intent*, not a runnable
playbook. The Set nodes carry the CACAO I/O contract (`in_args` /
`out_args`) plus the `x_secops_ng` reference bundles (control,
detection, telemetry, metric) as editable assignments; binding those
rows to real connectors is the operator's job.

## Regeneration

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/eu_ai_act_risk_management/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

    PYTHONPATH=. python -m tools.compile \
        content/playbooks/eu_ai_act_risk_management/playbook.cacao.json \
        --target n8n \
        --out examples/n8n/eu_ai_act_risk_management/workflow.n8n.json

The canonical playbook under
`content/playbooks/eu_ai_act_risk_management/playbook.cacao.json` is
the single source. The drift guard between the committed worked
example and the emitter output is pinned by the
eu_ai_act_risk_management example test suite under
`tests/examples/eu_ai_act_risk_management/`.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
n8n is open source (Sustainable Use License) and runs as a Node.js
process: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. The
operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
