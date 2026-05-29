# examples/n8n/data-exfil

Worked example: the `playbook.data_exfil_response@v1` CACAO v2 playbook
compiled by the n8n reference compiler. Operators can import
`workflow.json` directly into an n8n instance to see the topology the
emitter produces; binding the placeholder steps to real connectors is
the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/data-exfil/playbook.cacao.json

Scenario, workflow, regulatory anchors (NIS2 Article 23, DORA
Article 19), and the operator-supplied bindings are documented in that
folder's `README.md`. This folder holds only the *emitted* artifact and
the command used to produce it.

## Layout

| Path             | Source compiler | Format            |
|------------------|-----------------|-------------------|
| `workflow.json`  | `compilers.n8n` | n8n workflow JSON |

## Regeneration

The n8n emitter is deterministic: same input bytes in, same output
bytes out. To regenerate this folder from a clean checkout:

    PYTHONPATH=. python -m tools.compile \
        tests/compilers/_shared/fixtures/data_exfil.cacao.json \
        --target n8n \
        --out examples/n8n/data-exfil/workflow.json

The entry point is the unified `tools.compile` CLI with
`--target n8n`. The fixture under
`tests/compilers/_shared/fixtures/data_exfil.cacao.json` is a canonical
copy of the source playbook held under test isolation per the parser
contract; the two files are kept in sync.

Re-running the command yields byte-identical output. The
`tests/compilers/n8n/test_data_exfil.py` suite pins this invariant
against `tests/compilers/n8n/golden/data_exfil.n8n.json` so accidental
drift surfaces in review, not in an operator's runtime.

## What the emitter does not do

The n8n reference compiler translates **structure**, not **business
logic**. The emitted workflow carries the topology of the playbook
(steps, transitions, conditional routing) plus the lossy-translation
notes recorded by the compiler under `meta.secops_ng_notes`. It does
not carry:

- Operator-bound bindings (DLP platform, egress gateway, IAM provider,
  ticketing system, notification gateway).
- Credentials, secrets, or environment-specific endpoints.
- Detection logic — Sigma rule references are pinned upstream; no
  Sigma rules are authored in this repo.
- Containment decisions or notification thresholds — these are
  intent-bearing values the operator sets when binding the workflow to
  their environment.

Where a CACAO step expresses intent the target runtime cannot encode
(an `action` with no machine-readable `commands`, a switch with no
machine-readable `cases` expression, etc.), the emitter inserts an
explicit placeholder node and records the gap in
`meta.secops_ng_notes` so a human integrator sees exactly what they
still need to wire.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
The operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
