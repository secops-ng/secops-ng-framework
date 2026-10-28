# examples/n8n/cloud_misconfiguration

Worked example: the `playbook.cloud_misconfiguration@v1` CACAO v2
playbook compiled by the n8n reference compiler. Operators can import
`workflow.json` directly into an n8n instance to see the topology the
emitter produces. Each of the seven action steps compiles to a Code
node that calls its bound primitive; binding the inputs those calls
read to real connectors (CSPM / posture-management platform, cloud
inventory and ownership graph, exception ledger, ticketing / chat /
paging channel, change-management system, re-scan trigger) is the
operator's job.

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
playbook. Each action step is a Code node that imports its primitive
from `content.playbooks.cloud_misconfiguration.primitives` and binds the
step's output envelope to the call, and the two IF nodes read the real
booleans extracted from the enrichment and re-scan envelopes. Supplying
the adapter inputs those calls read (the posture finding, the inventory
and ownership records, the exception ledger, the routing table, the
remediation attempt and the re-scan result) is the operator's job.

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
pins the byte-identical drift guard and the node-id ↔ CACAO-action-id
parity check, and
`tests/examples/n8n/cloud_misconfiguration/test_golden.py` checks that
every bound step is a Code node calling its primitive and that both IF
nodes read the extracted booleans. The Set-node checks stay in both
files for any step that is unbound again; with all seven bound they
have nothing to check.

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
`name`. Sequencing (`on_completion` / `on_success` / `on_failure`)
becomes n8n `connections` edges.

## What this example does not do

The emitted workflow carries the topology of the playbook (steps,
transitions, conditional routing), one Code node per action step
calling its primitive, and the lossy-translation notes recorded under
`meta.secops_ng_notes`, of which this playbook has none. It does not
carry:

- Operator-bound bindings (CSPM / posture-management platform, cloud
  inventory and ownership graph, ticketing / chat / paging channel,
  change-management system, re-scan trigger, escalation paging
  endpoint).
- Credentials, secrets, or environment-specific endpoints.
- The operator's policy: the classification policy, the exception
  ledger, the per-severity routing and the default ownership pool
  arrive as adapter inputs. The rules applied to them (suppression only
  by a live, exact, time-boxed entry; attested remediation; verification
  only by a fresh pass under the same baseline) are fixed in the
  primitives and pinned by their tests.
- The recurring-misconfiguration KRI itself. The suppression and
  escalation steps stamp it; the metric lives in the catalogue.

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
