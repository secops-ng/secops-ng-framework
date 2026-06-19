# examples/n8n/incident_management

Worked example: the `playbook.incident_management@v1` CACAO v2 playbook
compiled by the n8n reference compiler. Operators can import
`workflow.n8n.json` directly into an n8n instance to see the topology
the emitter produces; binding the placeholder Set / IF cells to real
connectors (signal intake, deterministic classification, regulator
destinations for the three NIS2 Article 23 stages, timeline pattern
handle store) is the operator's job.

This is the **SKELETON** card of the F-WF-05 wave with the n8n CORE
wire-in applied. The canonical CACAO source still carries SKELETON
stubs for every action body; the per-step ``x_secops_ng.core_body``
bindings that drive the n8n Code-node primitive calls (classification
table, fail-closed regulator-destination resolver, three-stage NIS2
Article 23 stage clock) are layered onto this directory's CACAO mirror
by ``core_body.overlay.json`` at regeneration time. The overlay
collapses to empty and the divergence closes when the sibling
CORE-WIRE-TMPRL and CORE-WIRE-LG cards land and the canonical gains
the ``core_body`` blocks as the single source of truth — see
``core_body.overlay.json`` and ``tests/examples/test_n8n_incident_management.py``
for the divergence guard.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/incident_management/playbook.cacao.json

Scenario, workflow, regulatory anchors (NIS2 Article 23, DORA Article
19, ENISA incident-reporting guidance), control / metric / telemetry
bindings, and the operator-supplied notification-destination contract
are documented in that folder's `README.md`. This folder holds the
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
telemetry, metric) as editable assignments; the IF nodes carry
placeholder conditions. Binding those rows and populating those
conditions is the operator's job.

## Regeneration

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/incident_management/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

    PYTHONPATH=. python -m tools.compile \
        content/playbooks/incident_management/playbook.cacao.json \
        --target n8n \
        --out examples/n8n/incident_management/workflow.n8n.json

The drift guard between the committed worked example and the emitter
output lives in `tests/examples/test_n8n_incident_management.py`.

## Mirroring policy

The mapping from CACAO to n8n is the same one the compiler implements:

| CACAO step type    | n8n node type                                       |
|--------------------|-----------------------------------------------------|
| `start`            | `n8n-nodes-base.manualTrigger`                      |
| `action` (no cmds) | `n8n-nodes-base.set` (carries CACAO I/O + refs)     |
| `if-condition`     | `n8n-nodes-base.if`                                 |
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

- Operator-bound bindings (incident signal source, regulator-submission
  destinations the operator wires for the three NIS2 stages,
  notification transport between the resolved destination and the
  regulator endpoint itself, F-PT-02 incident-timeline pattern handle
  store, timeline JSON persistence backend). The fail-closed
  destination resolver, classification table, and three-stage NIS2
  Article 23 clock are wired into the n8n Code nodes by the
  ``core_body.overlay.json`` overlay — but the operator still binds
  concrete destinations and transports at the n8n credential layer.
- Credentials, secrets, or environment-specific endpoints. The
  sovereign-stack constraint applies: the framework ships no default
  notification endpoint — operators wire concrete regulator
  destinations at the compile target's config layer (n8n credential).
- DSPy reach beyond the free-text fields of the one-month final report
  (per ``content/playbooks/incident_management/primitives/signatures.py``
  — regulated decisions are deterministic code, not LM).

Where a CACAO step expresses intent the target runtime cannot encode
(an `action` with no machine-readable `commands`, an if-condition with
no machine-readable expression), the emitter inserts an explicit
placeholder node and records the gap in `meta.secops_ng_notes` so a
human integrator sees exactly what they still need to wire.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no incident
content, no regulator notifications reach this repository or the
SecOps-NG project. The operator runs n8n on infrastructure they
control — we ship the structure, they own the data plane.
