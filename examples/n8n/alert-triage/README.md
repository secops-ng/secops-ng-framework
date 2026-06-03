# examples/n8n/alert-triage

Worked example: the `playbook.alert_triage@v1` CACAO v2 source playbook
compiled by the n8n reference compiler. Operators can import
`workflow.n8n.json` directly into an n8n instance to see the topology
the emitter produces; binding the placeholder Set / IF / Switch nodes
to real connectors (detection-pipeline push / shared-store pull
ingestion, telemetry-context enrichment, suppression / known-benign
cache, classification + prioritisation policy, response branches) is
the operator's job.

This worked example is **SKELETON** — the workflow graph and step
ids are committed (start → ingest → enrich → if(suppress) → classify →
switch(priority{p1,p2,p3,p4}) → end). The IF condition expression and
the Switch case rules are emitted as placeholders because the CACAO
source carries them as intent rather than machine-readable expressions
at this stage; node bodies (commands, agentic bindings, prioritisation
policy code) land in follow-up CORE/EXTEND work against the source.

## Source

Canonical CACAO source playbook:

    ../../../content/playbooks/alert-triage.cacao.yaml

The YAML is the authored form. The n8n emitter consumes JSON via the
CACAO parser, so `regenerate.sh` mirrors the YAML to a byte-deterministic
JSON form (`playbook.cacao.json`) alongside this README before emitting
the n8n workflow. The two formats round-trip through `yaml.safe_load`
+ `json.dumps`.

Scenario, workflow, regulatory anchors, control / metric / telemetry
bindings, and the source's TODO markers are documented in the canonical
YAML. This folder holds the emitted artifact, the co-located JSON
mirror for easy diff inspection, and the regeneration script.

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
   canonical source. The workflow is **inactive** by default —
   review and bind it to your own connectors before activating.

The emitted workflow is a *snapshot of intent*, not a runnable
playbook. The Set nodes carry the CACAO I/O contract (`in_args` /
`out_args`) plus the `x_secops_ng` reference bundles (control,
detection, telemetry, metric) as editable assignments; the IF and
Switch nodes carry placeholder conditions. Binding those rows and
populating those conditions is the operator's job.

## Regeneration

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/alert-triage/regenerate.sh

The script mirrors the canonical CACAO YAML source into this folder
as `playbook.cacao.json` and re-emits `workflow.n8n.json` via
`tools.compile --target n8n`.

A drift guard between the committed worked example and a fresh
regeneration lands in the sibling F-WF-03 n8n golden test card; until
then this folder ships SKELETON outputs that should be regenerated
manually after any change to the source or to `compilers/n8n/*`.

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
`name`. Sequencing (`on_completion` / `on_success` / `on_failure` /
switch `cases`) becomes n8n `connections` edges.

## What this example does not do

The n8n reference compiler translates **structure** and the
**CACAO I/O contract**, not **business logic**. The emitted workflow
carries the topology of the playbook (steps, transitions, conditional
routing), the per-step `in_args` / `out_args` and the `x_secops_ng`
reference bundles as Set rows, plus the lossy-translation notes
recorded under `meta.secops_ng_notes`. It does not carry:

- Operator-bound bindings (detection-pipeline push / shared-store
  pull alert sources, telemetry-context enrichment store, suppression
  / known-benign cache, classification + prioritisation policy code,
  response-branch ticketing / paging / queueing connectors).
- Credentials, secrets, or environment-specific endpoints.
- Detection logic — detection-rule references are pinned upstream;
  no detection rules are authored in this repo.
- Suppression-window length, intent-classification thresholds, or
  prioritisation policy values — these are intent-bearing values the
  operator sets when binding the workflow to their environment.

Where a CACAO step expresses intent the target runtime cannot encode
(an `action` with no machine-readable `commands`, a switch with no
machine-readable `cases` expression, an if-condition with no
machine-readable expression, etc.), the emitter inserts an explicit
placeholder node and records the gap in `meta.secops_ng_notes` so a
human integrator sees exactly what they still need to wire.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no alert
content, no identifying flows reach this repository or the SecOps-NG
project. The operator runs n8n on infrastructure they control — we
ship the structure, they own the data plane.
