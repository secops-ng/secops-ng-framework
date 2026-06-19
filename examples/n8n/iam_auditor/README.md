# examples/n8n/iam_auditor

Worked example: the `playbook.iam_auditor@v1` CACAO v2 playbook
compiled by the n8n reference compiler. Operators can import
`workflow.n8n.json` directly into an n8n instance to see the topology
the emitter produces; binding the placeholder Set-node steps to real
connectors (identity provider, capability source, evidence sink) is
the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/iam_auditor/playbook.cacao.json

Scenario, workflow, regulatory anchor (NIS2 Article 21(2)(i)), and the
`x_secops_ng` reference bundles (control / telemetry / metric joins,
F-CP-07 access-evidence stream) are documented in that folder's
`README.md`. This folder holds the emitted artifact, a co-located
byte-identical copy of the CACAO source for easy diff inspection, the
regeneration scripts, and one representative access-evidence artifact
the F-CP-07 emitter produces at execution time.

## Layout

| Path                                    | Source compiler                       | Format            |
|-----------------------------------------|---------------------------------------|-------------------|
| `playbook.cacao.json`                   | (input mirror)                        | CACAO v2 JSON     |
| `workflow.n8n.json`                     | `compilers.n8n`                       | n8n workflow JSON |
| `regenerate.sh`                         | (tooling)                             | bash script       |
| `regenerate.py`                         | (tooling)                             | Python script     |
| `evidence/access-evidence.json`         | `compilers.n8n.evidence.access_node`  | F-CP-07 access record |

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
telemetry, metric) as editable assignments; binding those rows to
real connectors (identity provider, capability source, evidence sink)
is the operator's job.

## Regeneration

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/iam_auditor/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

    PYTHONPATH=. python -m tools.compile \
        content/playbooks/iam_auditor/playbook.cacao.json \
        --target n8n \
        --out examples/n8n/iam_auditor/workflow.n8n.json

The canonical playbook under
`content/playbooks/iam_auditor/playbook.cacao.json` is the single
source. The byte-parity test under
`tests/examples/n8n/iam_auditor/test_golden.py` pins the committed
worked example against the emitter so silent drift is caught at CI.

## Access-evidence artifact (F-CP-07)

The iam_auditor's `emit-access-evidence` state produces one
access-evidence artifact per execution against
`schemas/evidence/access.schema.json`. The committed
`evidence/access-evidence.json` is the byte-stable output of the n8n
adapter (`compilers.n8n.evidence.emit_access_artifact_n8n`) for the
representative payload pinned in `regenerate.py` — exactly what an
operator's n8n `executeCommand` / `Code` node materialises at runtime.

Regenerate from the repo root:

    PYTHONPATH=. python examples/n8n/iam_auditor/regenerate.py

The artifact is renamed from the deterministic
`<artifact_id>.json` (SHA-256 of `workflow_id|execution_id|compile_target`)
to a stable human-friendly filename for diffing; the byte-parity test
under `tests/examples/n8n/iam_auditor/test_golden.py` pins both the
workflow JSON and the access-evidence record against the adapter.

## Mirroring policy

The mapping from CACAO to n8n is the same one the compiler implements:

| CACAO step type    | n8n node type                                       |
|--------------------|-----------------------------------------------------|
| `start`            | `n8n-nodes-base.manualTrigger`                      |
| `action` (no cmds) | `n8n-nodes-base.set` (carries CACAO I/O + refs)     |
| `end`              | `n8n-nodes-base.noOp`                               |

Node ids preserve the CACAO step id verbatim so the two artifacts can
be cross-referenced by id alone. Node labels mirror the CACAO step
`name`. Sequencing (`on_completion`) becomes n8n `connections` edges.

## What this example does not do

The n8n reference compiler translates **structure** and the **CACAO
I/O contract**, not **business logic**. The emitted workflow carries
the topology of the playbook (steps, transitions), the per-step
`in_args` / `out_args`, and the `x_secops_ng` reference bundles as
Set rows. It does not carry:

- Operator-bound bindings (identity provider, capability source,
  evidence sink).
- Credentials, secrets, or environment-specific endpoints.
- The F-PT-01 platform-side refuse-at-boot guarantee that the caller
  actually held the listed capabilities — that lives in the platform
  layer; the workflow only carries the assertion shape.

Where a CACAO step expresses intent the target runtime cannot encode
(an `action` with no machine-readable `commands`), the emitter
inserts a Set-node placeholder and records the gap in
`meta.secops_ng_notes` so a human integrator sees exactly what they
still need to wire.

## Sovereign-stack default

The artifact destination is operator-configured. No default non-EU
endpoint. The n8n example writes the access-evidence artifact to a
local directory; the operator's runtime is expected to point the
adapter's `output_dir` at the volume their chosen evidence sink
ingests from.
