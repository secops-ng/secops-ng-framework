# examples/n8n/threat-intel-ingest

Worked example: the `playbook.threat_intel_ingest@v1` CACAO v2 playbook
compiled by the n8n reference compiler. Operators can import
`workflow.n8n.json` directly into an n8n instance to see the topology
the emitter produces; binding the placeholder Set-node steps to real
connectors (TAXII / STIX feed endpoint, SIEM, perimeter / DNS / EDR
blocklist gateway, ticketing system) is the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/threat-intel-ingest/playbook.cacao.json

Scenario, workflow, regulatory anchors (NIS2 Article 21(2)(d), DORA
Article 19(2)), and the operator-supplied bindings are documented in
that folder's `README.md`. This folder holds the emitted artifact, a
co-located byte-identical copy of the CACAO source for easy diff
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

    ./examples/n8n/threat-intel-ingest/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

    PYTHONPATH=. python -m tools.compile \
        content/playbooks/threat-intel-ingest/playbook.cacao.json \
        --target n8n \
        --out examples/n8n/threat-intel-ingest/workflow.n8n.json

The canonical playbook under
`content/playbooks/threat-intel-ingest/playbook.cacao.json` is the
single source. The `tests/compilers/n8n/test_threat_intel_ingest.py`
suite pins the byte-identical drift guard between the committed worked
example and the checked-in golden under
`tests/compilers/n8n/golden/threat_intel_ingest.n8n.json`.

## Mirroring policy

The mapping from CACAO to n8n is the same one the compiler implements:

| CACAO step type    | n8n node type                                       |
|--------------------|-----------------------------------------------------|
| `start`            | `n8n-nodes-base.manualTrigger`                      |
| `action` (no cmds) | `n8n-nodes-base.set` (carries CACAO I/O + refs)     |
| `if-condition`     | `n8n-nodes-base.if`                                 |
| `switch-condition` | `n8n-nodes-base.switch`                             |
| `end`              | `n8n-nodes-base.noOp`                               |

Node ids preserve the CACAO step id verbatim so the two artifacts can
be cross-referenced by id alone. Node labels mirror the CACAO step
`name`. Sequencing (`on_completion` / `on_success` / `on_failure`)
becomes n8n `connections` edges.

## What this example does not do

The n8n reference compiler translates **structure** and the
**CACAO I/O contract**, not **business logic**. The emitted workflow
carries the topology of the playbook (steps, transitions, conditional
routing), the per-step `in_args` / `out_args` and the `x_secops_ng`
reference bundles as Set rows, plus the lossy-translation notes
recorded under `meta.secops_ng_notes`. It does not carry:

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
