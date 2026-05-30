# examples/n8n/identity-compromise

Worked example: the `playbook.identity_compromise@v1` CACAO v2 playbook
compiled by the n8n reference compiler. Operators can import
`workflow.json` directly into an n8n instance to see the topology the
emitter produces; binding the placeholder steps to real connectors
(identity-protection signal source, IdP MFA / session management,
SaaS session revocation, lateral-movement hunt query backend, IAM
inventory / OAuth-grant audit) is the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/identity-compromise/playbook.cacao.json

Scenario, workflow, regulatory anchors, control / metric / telemetry
bindings, and the operator-supplied bindings are documented in that
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
        content/playbooks/identity-compromise/playbook.cacao.json \
        --target n8n \
        --out examples/n8n/identity-compromise/workflow.json

The entry point is the unified `tools.compile` CLI with
`--target n8n`. The canonical playbook under
`content/playbooks/identity-compromise/playbook.cacao.json` is the
single source; this example is a hand-checked snapshot of the emitter
output that mirrors its structure one-to-one (one n8n node per CACAO
action, node ids and labels copied from the CACAO source).

Re-running the command yields byte-identical output. The
`tests/examples/identity_compromise/test_n8n_workflow.py` suite pins
this invariant alongside a node-id ↔ CACAO-action-id parity check so
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
`name`. Sequencing (`on_completion` / `on_success` / `on_failure`)
becomes n8n `connections` edges.

## What this example does not do

The n8n reference compiler translates **structure**, not **business
logic**. The emitted workflow carries the topology of the playbook
(steps, transitions, conditional routing) plus the lossy-translation
notes recorded by the compiler under `meta.secops_ng_notes`. It does
not carry:

- Operator-bound bindings (identity-protection signal source, IdP MFA
  / session management API, SaaS session revocation channel, ticketing
  / paging endpoint, lateral-movement query backend, IAM inventory /
  OAuth-grant audit surface).
- Credentials, secrets, or environment-specific endpoints.
- Confirmation thresholds, blast-radius scoping rules, or
  persistence-removal logic — these are intent-bearing values the
  operator sets when binding the workflow to their environment.
- Sigma detection rules — those are referenced from the canonical
  playbook's `external_references` and live upstream at SigmaHQ; the
  emitter only carries the structural steps that act on a Sigma hit,
  not the rules themselves.

Where a CACAO step expresses intent the target runtime cannot encode
(an `action` with no machine-readable `commands`, an `if-condition`
with no machine-readable expression, etc.), the emitter inserts an
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
`tests/examples/identity_compromise/test_n8n_workflow.py` plays the
role.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
The operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
