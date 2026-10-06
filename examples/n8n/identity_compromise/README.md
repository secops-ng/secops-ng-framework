# examples/n8n/identity_compromise

Worked example: the `playbook.identity_compromise@v1` CACAO v2 playbook
compiled by the n8n reference compiler. Operators can import
`workflow.n8n.json` directly into an n8n instance to see the topology
the emitter produces. Every action step is a Code node calling its
deterministic primitive; binding the inputs those calls read to real
connectors (identity-protection signal source, IdP MFA / session
management, SaaS tenant session inventories, lateral-movement hunt
query backend, IAM inventory / OAuth-grant audit surface) is the
operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/identity_compromise/playbook.cacao.json

Scenario, workflow, regulatory anchors, control / metric / telemetry
bindings, and the operator-supplied bindings are documented in that
folder's `README.md`. This folder holds the emitted artifact, a
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
playbook. The Code nodes call the bound primitives; binding the
adapter inputs they read to real connectors is the operator's job.

## Regeneration

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/identity_compromise/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

    PYTHONPATH=. python -m tools.compile \
        content/playbooks/identity_compromise/playbook.cacao.json \
        --target n8n \
        --out examples/n8n/identity_compromise/workflow.n8n.json

The canonical playbook under
`content/playbooks/identity_compromise/playbook.cacao.json` is the
single source. The drift guard between the committed worked example
and the emitter output is pinned by the identity_compromise example
test suite under `tests/examples/identity_compromise/`, and the
per-compiler golden is pinned by `tests/compilers/n8n/test_golden.py`.

## Mirroring policy

The mapping from CACAO to n8n is the same one the compiler implements:

| CACAO step type    | n8n node type                                       |
|--------------------|-----------------------------------------------------|
| `start`            | `n8n-nodes-base.manualTrigger`                      |
| `action` (bound)   | `n8n-nodes-base.code` (imports and calls `core_body`) |
| `action` (unbound) | `n8n-nodes-base.set` (carries CACAO I/O + refs)     |
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
routing) and one primitive call per action step. With every step
bound, `meta.secops_ng_notes` records no lossy translations. It does
not carry:

- Operator-bound adapters (identity-protection signal source, IdP MFA
  / session management API, SaaS tenant session inventories,
  lateral-movement query backend, IAM inventory / OAuth-grant audit
  surface).
- Credentials, secrets, or environment-specific endpoints.
- Detection logic — Sigma rule references (impossible-travel,
  token-theft, OAuth-grant abuse, etc.) are pinned upstream at
  SigmaHQ; no Sigma rules are authored in this repo.
- The operator's inputs: benign patterns, the principal's privilege,
  the hunt lookback window and the compromise-window start arrive as
  adapter inputs. The confirmation rule and the persistence-removal
  rule are fixed in the primitives and pinned by their tests.

Where a CACAO step expresses intent the target runtime cannot encode
(an `action` with no machine-readable `commands`, a switch with no
machine-readable `cases` expression, etc.), the emitter inserts an
explicit placeholder node and records the gap in
`meta.secops_ng_notes` so a human integrator sees exactly what they
still need to wire.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
n8n is open source (Sustainable Use License) and runs as a Node.js
process: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. The
operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
