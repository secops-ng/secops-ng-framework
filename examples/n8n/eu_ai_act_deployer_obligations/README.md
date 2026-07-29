# examples/n8n/eu_ai_act_deployer_obligations

Worked example: the `playbook.eu_ai_act_deployer_obligations@v1` CACAO
v2 playbook compiled by the n8n reference compiler. Operators can
import `workflow.n8n.json` directly into an n8n instance to see the
topology the emitter produces; binding the placeholder Set-node steps
to real connectors (deployment register, provider instructions-for-use
store, oversight-assignment record, input-data control surface,
monitoring signal source, FRIA record store, and the automatically
generated log store) is the operator's job.

This is the deployer-side counterpart to the provider-side
`eu_ai_act_risk_management` example: it models the operator who *runs*
a third-party high-risk AI system in production rather than the one who
places one on the market.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/eu_ai_act_deployer_obligations/playbook.cacao.json

Scenario, workflow, regulatory anchors (EU AI Act Art. 26(1)/(2)/(4)/
(5)/(6)/(7) and Art. 27), and OSCAL / D3FEND control bindings are
documented in that folder's `mappings.yaml`. This folder holds the
emitted artifact, a co-located byte-identical copy of the CACAO source
for easy diff inspection, and the regeneration script.

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

## Two properties worth preserving when you bind it

The compiled topology is linear, but two of the assignments carry legal
weight that a naive connector binding will flatten:

- **`__escalation_trigger_class__` is separate from
  `__monitoring_observation_id__` on purpose.** Its three values have
  different consequences under Art. 26(5): routine monitoring feeds the
  provider's Art. 72 loop; an Art. 79(1) risk determination compels
  notification *and* suspension of use without undue delay; a serious
  incident compels immediate sequenced notification — provider first,
  then importer or distributor, then the market-surveillance
  authorities. Collapsing the class into the observation loses the
  suspension trigger.
- **Negative determinations are outputs, not empty fields.** An
  out-of-scope Art. 27 determination and a non-control determination
  under Art. 26(4) are both dated evidence. A connector that writes
  null on "not applicable" destroys the record the obligation is
  discharged by.

## Regeneration

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/eu_ai_act_deployer_obligations/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

    PYTHONPATH=. python -m tools.compile \
        content/playbooks/eu_ai_act_deployer_obligations/playbook.cacao.json \
        --target n8n \
        --out examples/n8n/eu_ai_act_deployer_obligations/workflow.n8n.json

The canonical playbook under
`content/playbooks/eu_ai_act_deployer_obligations/playbook.cacao.json`
is the single source. The drift guard between the committed worked
example and the emitter output is pinned by the
eu_ai_act_deployer_obligations example test suite under
`tests/examples/eu_ai_act_deployer_obligations/`.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
n8n is open source (Sustainable Use License) and runs as a Node.js
process: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. The
operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
