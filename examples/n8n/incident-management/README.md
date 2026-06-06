# examples/n8n/incident-management

Worked example: the `playbook.incident_management@v1` CACAO v2 playbook
compiled by the n8n reference compiler. Operators can import
`workflow.n8n.json` directly into an n8n instance to see the topology
the emitter produces; binding the placeholder Set / IF cells to real
connectors (signal intake, deterministic classification, regulator
destinations for the three NIS2 Article 23 stages, timeline pattern
handle store) is the operator's job.

This is the **SKELETON** card of the F-WF-05 wave. Action bodies are
stub placeholders carrying only the CACAO I/O contract; no primitives
binding is in place yet — that lands in the CORE-PRIM card (card 5 of
the F-WF-05 wave per `docs/internal/f-wf-05-gap-inventory.md` § 3.1).

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/incident-management/playbook.cacao.json

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

    ./examples/n8n/incident-management/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

    PYTHONPATH=. python -m tools.compile \
        content/playbooks/incident-management/playbook.cacao.json \
        --target n8n \
        --out examples/n8n/incident-management/workflow.n8n.json

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

- Operator-bound bindings (incident signal source, deterministic
  classification policy implementation, regulator-submission
  destinations for the three NIS2 stages, F-PT-02 incident-timeline
  pattern handle store, timeline JSON persistence backend).
- Credentials, secrets, or environment-specific endpoints. The
  sovereign-stack constraint applies: the framework ships no default
  notification endpoint — operators wire concrete regulator
  destinations at the compile target's config layer (n8n credential).
- The deterministic significance / cross-border classification policy
  itself — that lands in the CORE-PRIM card.
- Stage-clock arithmetic, the regulator-submission contract, or the
  typed early-warning / 72h notification / final-report payload
  shapes — these all land in CORE-PRIM.

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
