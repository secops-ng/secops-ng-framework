# examples/temporal/ransomware-containment

Worked example: the `playbook.ransomware_containment@v1` CACAO v2 playbook
compiled by the Temporal reference compiler. Operators who already run
Temporal can import `workflow_stub.py` into their worker module to see
the topology the emitter produces; binding the activity bodies to real
connectors (EDR isolation API, network ACL / SDN fallback,
IdP session and token revocation, backup-verification system,
ticketing / paging and NIS2 Article 23 24-hour early-warning
reporting channel) is the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/ransomware-containment/playbook.cacao.json

Scenario, workflow, regulatory anchors, control / metric / telemetry
bindings, and the operator-supplied bindings are documented in that
folder's `README.md`. This folder holds only the *emitted* artifact and
the command used to produce it.

## Layout

| Path                | Source compiler      | Format                |
|---------------------|----------------------|-----------------------|
| `workflow_stub.py`  | `compilers.temporal` | Python (`temporalio`) |

## Regeneration

The Temporal emitter is deterministic: same input bytes in, same output
bytes out. To regenerate this folder from a clean checkout:

    python -m compilers.temporal \
        content/playbooks/ransomware-containment/playbook.cacao.json \
        --out examples/temporal/ransomware-containment/workflow_stub.py

The entry point is `python -m compilers.temporal` (see
`compilers/temporal/__main__.py`); the underlying function is
`compilers.temporal.emit.emit_file`. The canonical playbook under
`content/playbooks/ransomware-containment/playbook.cacao.json` is the
single source; this example is a hand-checked snapshot of the emitter
output that mirrors its structure one-to-one (one `@activity.defn` per
CACAO action, activity names derived from the CACAO action ids).

Re-running the command yields byte-identical output. The
`tests/examples/ransomware_containment/test_temporal_workflow.py` suite
pins this invariant alongside an activity-name ↔ CACAO action-id parity
check so accidental drift surfaces in review, not in an operator's
runtime.

## Mirroring policy

The mapping from CACAO to Temporal is the same one the compiler
implements:

| CACAO step type    | Temporal artifact                              |
|--------------------|------------------------------------------------|
| `start`            | (workflow entry point, no activity)            |
| `action`           | `@activity.defn` async function                |
| `if-condition`     | workflow control flow (compiler-emitted)       |
| `switch-condition` | workflow control flow (compiler-emitted)       |
| `end`              | (workflow return, no activity)                 |

Each CACAO `action` becomes exactly one `@activity.defn` function whose
name is the CACAO action's `name` slugified to a valid Python
identifier, plus a `RetryPolicy` constant. The function docstring
records the CACAO `step_id` verbatim so the two artifacts can be
cross-referenced. The emitted workflow class exposes the playbook's
`stable_id` and the ordered activity tuple in its docstring; the
ordered tuple is also exported as the module-level `ACTIVITIES`
constant so a worker bootstrap can register them without knowing the
playbook's internals.

## What this example does not do

The Temporal reference compiler translates **structure**, not
**business logic**. The emitted stub carries the topology of the
playbook (activities, retry policies, the workflow class shell) but
the activity bodies and workflow control flow are intentionally
`NotImplementedError`:

- Operator-bound bindings (EDR isolation API, network ACL
  / SDN fallback channel, IdP session / token revocation API,
  backup-verification system, NIS2 Article 23 24-hour early-warning
  reporting channel) are not embedded — the operator wires them at
  activity-worker startup.
- Credentials, secrets, and environment-specific endpoints are not
  embedded — secrets stay with the operator and are injected at
  worker startup, not at compile time.
- Confirmation thresholds, isolation-fallback decision rules, and
  the NIS2 Article 23 24-hour early-warning report wording are not
  embedded — these are intent-bearing values the operator sets when
  binding the workflow to their environment.
- Sigma detection rules (shadow-copy deletion, ransomware file rename,
  overpass-the-hash, etc.) are not embedded — those are referenced
  from the canonical playbook's `external_references` and live
  upstream at SigmaHQ; the emitter only carries the structural
  activity that acts on a Sigma hit, not the rule itself.
- It does not pick a Temporal deployment posture. Self-hosted
  (Temporal OSS on EU sovereign infrastructure) and managed
  (Temporal Cloud) are both supported by the same emitted source.

## Future compiler-driven emission

Today this example is produced by `python -m compilers.temporal`,
which calls into `compilers/temporal/emit.py`. Future work will fold
this example into the same compiler-driven emission contract as the
other worked examples — regenerated from the canonical CACAO source on
every test run rather than maintained as a checked-in snapshot. Until
that lands, the drift guard in
`tests/examples/ransomware_containment/test_temporal_workflow.py` plays
the role.

## Sovereignty note

Temporal is open source (MIT) and runs as a server + worker process
pair: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. The
emitter never embeds a connection string, task-queue name, or
credential, so the operator can target a self-hosted cluster or an
EU-region managed namespace without regenerating the artifact. The
artifact emitted here is a description of what the operator's own
Temporal worker should do — no telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
The operator runs Temporal on infrastructure they control; we ship the
structure, they own the data plane.
