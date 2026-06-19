# examples/n8n/cloud_misconfiguration

Worked example: the `playbook.cloud_misconfiguration@v1` CACAO v2
playbook compiled by the n8n reference compiler. Operators can import
`workflow.json` directly into an n8n instance to see the topology the
emitter produces; binding the placeholder steps to real connectors
(CSPM / posture-management platform, cloud inventory and ownership
graph, ticketing / chat / paging channel, change-management system,
re-scan trigger) is the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/cloud_misconfiguration/playbook.cacao.json

Scenario, workflow, regulatory anchors (NIS2 Article 21(2)(e) / 21(2)(i),
DORA Articles 6 and 9), control / metric / telemetry bindings, and the
operator-supplied bindings are documented in that folder's `README.md`.
This folder holds the *emitted* artifact, a co-located byte-identical
copy of the CACAO source for easy diff inspection, and the regeneration
script.

## Layout

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input mirror)  | CACAO v2 JSON     |
| `workflow.json`       | `compilers.n8n` | n8n workflow JSON |
| `regenerate.sh`       | (tooling)       | bash script       |

## How to import

1. In your own n8n instance, open the workflows list and choose
   **Import from File**.
2. Select `workflow.json` from this directory.
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

    ./examples/n8n/cloud_misconfiguration/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.json` via `tools.compile --target n8n`. Equivalent
direct invocation:

    PYTHONPATH=. python -m tools.compile \
        content/playbooks/cloud_misconfiguration/playbook.cacao.json \
        --target n8n \
        --out examples/n8n/cloud_misconfiguration/workflow.json

The canonical playbook under
`content/playbooks/cloud_misconfiguration/playbook.cacao.json` is the
single source. The
`tests/examples/cloud_misconfiguration/test_n8n_workflow.py` suite
pins the byte-identical drift guard, the node-id ↔ CACAO-action-id
parity check, and the post Set-node-uplift semantic checks
(`in_args` / `out_args` surfacing, `x_secops_ng` reference
pass-through, no empty-assignment Set nodes, `noOp` reserved for the
`end` sentinel).

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

- Operator-bound bindings (CSPM / posture-management platform, cloud
  inventory and ownership graph, ticketing / chat / paging channel,
  change-management system, re-scan trigger, escalation paging
  endpoint).
- Credentials, secrets, or environment-specific endpoints.
- Suppression-window expressions, severity-classification logic, or
  remediation-attestation logic — these are intent-bearing values
  the operator sets when binding the workflow to their environment.
- The recurring-misconfiguration KRI accounting — that lives in the
  metric bindings referenced from the canonical playbook; the emitter
  carries only the steps that emit against it, not the metric itself.

Where a CACAO step expresses intent the target runtime cannot encode
(an `if-condition` with no machine-readable expression, etc.), the
emitter records the gap in `meta.secops_ng_notes` so a human
integrator sees exactly what they still need to wire.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
The operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
