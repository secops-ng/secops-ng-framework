# examples/n8n/detection_engineering

Worked example: the `playbook.detection_engineering@v1` CACAO v2
playbook compiled by the n8n reference compiler. Operators can import
`workflow.n8n.json` directly into an n8n instance to see the topology
the emitter produces; binding the placeholder Set-node steps to real
connectors (detection-store proposal intake, peer-review system, the
operator's production detection-store promotion endpoint, and the
metric sink that ingests the per-rule-version effectiveness snapshot)
is the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/detection_engineering/playbook.cacao.yaml

The four-state lifecycle (propose → review → ship → measure), the
NIS2 Article 21(2)(f) regulatory anchor, the OCSF Detection Finding
binding, and the indicator catalogue references the `measure` state
emits against are documented in that folder's `README.md`. This
directory holds the emitted workflow artifact, the regeneration
script, and the per-rule-version effectiveness-snapshot artifact the
adapter at `compilers/n8n/evidence/rule_effectiveness_node.py`
produces from the `measure` state's payload.

## Layout

| Path                          | Source                                  | Format               |
|-------------------------------|-----------------------------------------|----------------------|
| `workflow.n8n.json`           | `compilers.n8n`                         | n8n workflow JSON    |
| `regenerate.sh`               | (tooling — regenerates the workflow)    | bash script          |
| `evidence/rule-effectiveness-snapshot.json` | `compilers.n8n.evidence`  | snapshot JSON        |
| `regenerate.py`               | (tooling — regenerates the snapshot)    | python script        |

## How to import

1. In your own n8n instance, open the workflows list and choose
   **Import from File**.
2. Select `workflow.n8n.json` from this directory.
3. n8n loads the nodes wired into the four-state topology described
   in the canonical playbook. The workflow is **inactive** by
   default — review and bind it to your own connectors before
   activating.

The emitted workflow is a *snapshot of intent*, not a runnable
playbook. The Set nodes for each lifecycle state carry the CACAO
I/O contract (`in_args` / `out_args`) plus the `x_secops_ng`
reference bundles (control, telemetry, metric) as editable
assignments; binding those rows to real connectors is the operator's
job. The `measure` state's output is shaped per
`schemas/evidence/rule-effectiveness-snapshot.schema.json`; the
worked-example snapshot at `evidence/rule-effectiveness-snapshot.json`
shows the on-disk bytes the n8n adapter writes for one representative
rule version.

## Sovereign-stack constraint

Metric storage is operator-configured. The framework ships **no**
hosted-SaaS default endpoint for the effectiveness snapshot; the
operator's runtime is expected to point the n8n adapter's
`output_dir` at the volume their chosen metric sink ingests from.

## Regeneration

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/detection_engineering/regenerate.sh

regenerates `workflow.n8n.json` from the canonical CACAO source.
The per-rule-version effectiveness-snapshot artifact under
`evidence/` is regenerated separately by the sibling Python script:

    PYTHONPATH=. python examples/n8n/detection_engineering/regenerate.py

## Pending follow-up work

Gating predicates on the `review → ship` and `ship → measure`
transitions, per-target byte-parity goldens covering all four
lifecycle states, and the cookbook walkthrough land in follow-up
sibling cards tracked in `ROADMAP.md` § F-WF-04. The reference
emitters for Temporal and LangGraph land alongside in their own
sibling cards.
