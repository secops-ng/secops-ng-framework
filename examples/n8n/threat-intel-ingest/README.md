# examples/n8n/threat-intel-ingest

Worked example: the `playbook.threat_intel_ingest@v1` CACAO v2 playbook
compiled by the n8n reference compiler. Operators can import
`workflow.n8n.json` directly into an n8n instance to see the topology
the emitter produces; binding the placeholder steps to real connectors
(TAXII client, SIEM, blocklist gateway) is the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/threat-intel-ingest/playbook.cacao.json

Scenario, workflow, regulatory anchors (NIS2 Article 21(2)(d), DORA
Article 19(2)), and the operator-supplied bindings are documented in
that folder's `README.md`. This folder holds only the *emitted*
artifact, a co-located copy of the CACAO source for review convenience,
and the command used to produce them.

## Layout

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input)         | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |

## Regeneration

The n8n emitter is deterministic: same input bytes in, same output
bytes out. To regenerate this folder from a clean checkout:

    PYTHONPATH=. python -m tools.compile \
        tests/compilers/_shared/fixtures/threat_intel_ingest.cacao.json \
        --target n8n \
        --out examples/n8n/threat-intel-ingest/workflow.n8n.json

The entry point is the unified `tools.compile` CLI with
`--target n8n`. The fixture under
`tests/compilers/_shared/fixtures/threat_intel_ingest.cacao.json` is a
canonical copy of the source playbook held under test isolation per
the parser contract; the two files are kept in sync.

Re-running the command yields byte-identical output. The
`tests/compilers/n8n/test_threat_intel_ingest.py` suite pins this
invariant against
`tests/compilers/n8n/golden/threat_intel_ingest.n8n.json` so accidental
drift surfaces in review, not in an operator's runtime.

## What the emitter does not do

The n8n reference compiler translates **structure**, not **business
logic**. The emitted workflow carries the topology of the playbook
(steps, transitions, conditional routing) plus the lossy-translation
notes recorded by the compiler under `meta.secops_ng_notes`. It does
not carry:

- Operator-bound bindings (TAXII / STIX feed endpoint, SIEM, perimeter
  / DNS / EDR blocklist gateway, ticketing system).
- Credentials, secrets, or environment-specific endpoints.
- Detection logic — Sigma rule references are pinned upstream at
  SigmaHQ; no Sigma rules are authored in this repo.
- Confidence thresholds or indicator scoring rules — these are
  intent-bearing values the operator sets when binding the workflow
  to their environment.

Where a CACAO step expresses intent the target runtime cannot encode
(an `action` with no machine-readable `commands`, a switch with no
machine-readable `cases` expression, etc.), the emitter inserts an
explicit placeholder node and records the gap in
`meta.secops_ng_notes` so a human integrator sees exactly what they
still need to wire.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
indicator data, no identifying flows reach this repository or the
SecOps-NG project. The operator runs n8n on infrastructure they
control — we ship the structure, they own the data plane.
