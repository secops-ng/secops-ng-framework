# examples/n8n/vuln-intake

Worked example: the `playbook.vuln_intake@v1` CACAO v2 playbook compiled
by the n8n reference compiler. Operators can import `workflow.json`
directly into an n8n instance to see the topology the emitter produces;
binding the placeholder steps to real connectors (CVD intake mailbox,
SBOM/asset inventory, ticketing system, advisory distribution) is the
operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/vuln-intake/playbook.cacao.json

Scenario, workflow, regulatory anchors (CRA Article 14, CRA Annex I
§2(1) / §2(7), NIS2 Article 23), control / metric / telemetry bindings,
and the operator-supplied bindings are documented in that folder's
`README.md`. This folder holds only the *emitted* artifact and the
command used to produce it.

## Layout

| Path             | Source compiler | Format            |
|------------------|-----------------|-------------------|
| `workflow.json`  | `compilers.n8n` | n8n workflow JSON |

## Regeneration

The n8n emitter is deterministic: same input bytes in, same output
bytes out. To regenerate this folder from a clean checkout:

    PYTHONPATH=. python -m tools.compile \
        content/playbooks/vuln-intake/playbook.cacao.json \
        --target n8n \
        --out examples/n8n/vuln-intake/workflow.json

The entry point is the unified `tools.compile` CLI with
`--target n8n`. The canonical playbook under
`content/playbooks/vuln-intake/playbook.cacao.json` is the single
source; this example is a hand-checked snapshot of the emitter output
that mirrors its structure one-to-one (one n8n node per CACAO action,
node ids and labels copied from the CACAO source).

Re-running the command yields byte-identical output. The
`tests/examples/vuln_intake/test_n8n_workflow.py` suite pins this
invariant alongside a node-id ↔ CACAO-action-id parity check so
accidental drift surfaces in review, not in an operator's runtime.

## Mirroring policy

The mapping from CACAO to n8n is the same one the compiler implements:

| CACAO step type    | n8n node type                        |
|--------------------|--------------------------------------|
| `start`            | `n8n-nodes-base.manualTrigger`       |
| `action`           | `n8n-nodes-base.noOp` (placeholder)  |
| `if-condition`     | `n8n-nodes-base.if`                  |
| `switch-condition` | `n8n-nodes-base.switch`              |
| `end`              | `n8n-nodes-base.noOp`                |

Node ids preserve the CACAO step id verbatim so the two artifacts can
be cross-referenced by id alone. Node labels mirror the CACAO step
`name`. Sequencing (`on_completion` / `on_success` / `on_failure` /
switch `cases`) becomes n8n `connections` edges.

## What this example does not do

The n8n reference compiler translates **structure**, not **business
logic**. The emitted workflow carries the topology of the playbook
(steps, transitions, conditional routing) plus the lossy-translation
notes recorded by the compiler under `meta.secops_ng_notes`. It does
not carry:

- Operator-bound bindings (CVD intake mailbox, SBOM / asset inventory,
  CVSS / EPSS scoring service, ticketing system, advisory distribution
  channel, regulator submission endpoint).
- Credentials, secrets, or environment-specific endpoints.
- CVSS / EPSS scoring logic, severity thresholds, or release-SLA
  values — these are intent-bearing values the operator sets when
  binding the workflow to their environment.
- The CRA Article 14 24h / 72h / 14d clock semantics — those live in
  the controls referenced from the canonical playbook; the emitter
  carries only the step that triggers the regulator-notification
  chain, not the clock itself.

Where a CACAO step expresses intent the target runtime cannot encode
(an `action` with no machine-readable `commands`, a switch with no
machine-readable `cases` expression, etc.), the emitter inserts an
explicit placeholder node and records the gap in
`meta.secops_ng_notes` so a human integrator sees exactly what they
still need to wire.

## Future compiler-driven emission

Today this example is produced by the unified `tools.compile` CLI
(`--target n8n`), which calls into `compilers/n8n/emit.py`. Future
work will fold this example into the same compiler-driven emission
contract as the other worked examples — regenerated from the canonical
CACAO source on every test run rather than maintained as a checked-in
snapshot. Until that lands, the drift guard in
`tests/examples/vuln_intake/test_n8n_workflow.py` plays the role.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
The operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
