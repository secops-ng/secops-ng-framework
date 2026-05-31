# examples/n8n/on-call-rotation

Worked example: the `playbook.on_call_rotation@v1` CACAO v2 playbook
compiled by the n8n reference compiler. Import `workflow.n8n.json`
into an n8n instance to see the topology the emitter produces; binding
placeholder steps to real connectors (roster source, paging system,
ticketing, notifier) is the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/on-call-rotation/playbook.cacao.json

Scenario, workflow, and operator-supplied bindings are documented in
that folder's `README.md`. This folder holds only the emitted artifact,
a co-located copy of the CACAO source, and the regeneration command.

## Layout

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input)         | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |

## Regeneration

Deterministic emitter; re-running yields byte-identical output. From
the repo root:

    ./examples/n8n/on-call-rotation/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.

## Sovereignty note

No telemetry, no execution traces, no identifying data flows to this
repository. The operator runs n8n on infrastructure they control — we
ship the structure, they own the data plane.
