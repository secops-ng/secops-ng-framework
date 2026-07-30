# examples/n8n/ai_human_oversight

Worked example: the `playbook.ai_human_oversight@v1` CACAO v2 playbook
compiled by the n8n reference compiler. Operators can import
`workflow.n8n.json` directly into an n8n instance to see the topology
the emitter produces; binding the placeholder Set-node steps to real
connectors (oversight roster, briefing record, the flagged-decision
queue, the intervention log and the evidence store) is the operator's
job.

This is the *exercise* half of EU AI Act human oversight. Its sibling
`eu_ai_act_deployer_obligations` covers the Art. 26(2) **assignment**;
this playbook covers Art. 14, which governs what the assignee must
actually be able to do and to evidence.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/ai_human_oversight/playbook.cacao.json

Scenario, workflow, regulatory anchors (EU AI Act Art. 14(1), 14(3)(a),
14(4)(a)-(e), 14(5)) and OSCAL / D3FEND control bindings are documented
in that folder's `mappings.yaml`. This folder holds the emitted
artifact, a co-located byte-identical copy of the CACAO source for easy
diff inspection, and the regeneration script.

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

## Three things a connector binding tends to destroy

The topology is linear, but three of the assignments carry legal weight
that a naive mapping will flatten:

- **`__intervention_type__` is separate from
  `__intervention_record_id__`.** Art. 14(4)(d)-(e) name four distinct
  exercises — decline to use, disregard the output, override or reverse
  it, and interrupt operation via a stop button. They carry different
  weight on review, and an aggregate intervention count that collapses
  them tells a reviewer nothing about severity. A halt is not a
  disregard.
- **`__biometric_two_person_verification__` needs two *separate*
  persons.** Art. 14(5) applies only to Annex III point 1(a) remote
  biometric identification, and one overseer confirming twice does not
  satisfy it. Where the narrow law-enforcement exemption is relied on,
  the record must carry the Union or national **legal basis actually
  relied on**, not merely a flag that an exemption was taken.
- **A review that found nothing is still evidence.** Most cycles
  produce reviews and no interventions. A connector that writes nothing
  when the intervention set is empty leaves a window
  indistinguishable from one where no oversight happened at all.

## Regeneration

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/ai_human_oversight/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

    PYTHONPATH=. python -m tools.compile \
        content/playbooks/ai_human_oversight/playbook.cacao.json \
        --target n8n \
        --out examples/n8n/ai_human_oversight/workflow.n8n.json

The canonical playbook under
`content/playbooks/ai_human_oversight/playbook.cacao.json` is the
single source. The drift guard between the committed worked example and
the emitter output is pinned by the ai_human_oversight example test
suite under `tests/examples/ai_human_oversight/`.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
n8n is open source (Sustainable Use License) and runs as a Node.js
process: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. The
operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
