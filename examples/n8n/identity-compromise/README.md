# identity-compromise — n8n worked example

End-to-end demonstration of the SecOps-NG n8n reference compiler on the
identity-compromise CACAO playbook. It is aimed at an integrator who
already runs n8n and wants to adopt a portable SecOps-NG playbook
without re-platforming: the example shows exactly which workflow shape
the compiler produces, how the CACAO contract surfaces on each node,
and where the integrator owns the seams.

## Files in this directory

| File | Role |
|------|------|
| `workflow.json` | n8n workflow JSON emitted by `compilers.n8n.emit` — import this into your own n8n instance. |
| `README.md` | This file. |

The canonical input is the CACAO v2 playbook at
`../../../content/playbooks/identity-compromise/playbook.cacao.json`
(frozen). Scenario, regulatory anchors, control / metric / telemetry
bindings, and the operator-supplied bindings are documented in that
folder's `README.md`. This folder holds only the *emitted* artifact.

## How to import

1. In your own n8n instance, open the workflows list and choose
   **Import from File**.
2. Select `workflow.json` from this directory.
3. n8n loads nine nodes wired into the topology described below. The
   workflow is **inactive** by default — review and bind it to your own
   connectors before activating.

The emitted workflow is a *snapshot of intent*, not a runnable
playbook. The Set nodes carry the CACAO I/O contract as editable
assignments; binding those rows to real connectors (identity-protection
signal source, IdP MFA / session management, SaaS session revocation
channel, lateral-movement hunt query backend, IAM inventory /
OAuth-grant audit surface, and any ticketing / paging endpoint) is the
operator's job.

## How to regenerate

After any change to the playbook or to `compilers/n8n/*`, refresh the
committed artifact from the repo root:

```bash
PYTHONPATH=. python -m tools.compile \
    content/playbooks/identity-compromise/playbook.cacao.json \
    --target n8n \
    --out examples/n8n/identity-compromise/workflow.json
```

The n8n emitter is deterministic: same input bytes in, same output
bytes out. The drift guard in
`tests/examples/identity_compromise/test_n8n_workflow.py` fails the
suite if the committed `workflow.json` diverges from a fresh
regeneration, so the worked example stays honest as the compiler
evolves.

## Topology

The identity-compromise playbook branches once on triage outcome, then
walks a linear containment chain. Nine n8n nodes, one per CACAO step:

1. `identity-compromise-start` (`manualTrigger`) — entry point;
   matches the CACAO `start` step.
2. `triage identity signal` (`set`) — collect the identity-protection
   signal and resolve it to a principal, then decide whether the
   compromise is confirmed.
3. `compromise confirmed?` (`if`) — branch on the triage outcome.
   `true` routes into the containment chain; `false` routes to the
   false-positive end sentinel.
4. `reset MFA factors` (`set`) — revoke and re-enrol the principal's
   MFA factors.
5. `revoke active sessions` (`set`) — invalidate all active sessions
   and OAuth refresh tokens for the principal.
6. `lateral-movement hunt` (`set`) — run a hunt query for
   post-compromise lateral activity by the principal.
7. `IAM audit and persistence removal` (`set`) — audit IAM grants and
   strip any attacker-planted persistence (rogue keys, OAuth apps,
   inbox rules).
8. `identity-compromise-end` (`noOp`) — confirmed-path end sentinel.
9. `identity-compromise-false-positive-end` (`noOp`) —
   false-positive-path end sentinel.

## CACAO contract surfaces on Set nodes

Every `action`-without-commands step in the CACAO source emits an n8n
`set` node whose **assignments** carry the CACAO contract one row per
field:

- `in.<name>` rows for each entry in the step's `in_args`.
- `out.<name>` rows for each entry in the step's `out_args`.
- `x_secops_ng.<key>` rows for each key under the step's
  `x_secops_ng` block (`detection_refs`, `control_refs`,
  `telemetry_refs`, `metric_refs`, and any KPI hooks).

The values are left blank (or pre-seeded with the reference-id list,
for `x_secops_ng` rows) so the integrator can wire them to expressions
that pull from upstream nodes, n8n variables, or operator-bound
connectors. Concretely on this playbook:

| Set node | `in.` rows | `out.` rows | `x_secops_ng.` rows |
|----------|------------|-------------|---------------------|
| `triage identity signal` | `signal_id`, `principal_id` | `compromise_confirmed` | `detection_refs`, `control_refs`, `telemetry_refs`, `metric_refs` |
| `reset MFA factors` | `principal_id` | — | `control_refs`, `metric_refs` |
| `revoke active sessions` | `principal_id` | `sessions_revoked_count` | `control_refs`, `telemetry_refs`, `metric_refs` |
| `lateral-movement hunt` | `principal_id` | `lateral_findings_count` | `detection_refs`, `control_refs`, `telemetry_refs`, `metric_refs` |
| `IAM audit and persistence removal` | `principal_id` | — | `detection_refs`, `control_refs`, `telemetry_refs` |

The `if-condition` node (`compromise confirmed?`) emits an n8n `if`
node with a placeholder condition the operator must wire to the
upstream `out.compromise_confirmed` field. The lossy translation is
recorded in `meta.secops_ng_notes` so the integrator sees exactly
which seams need attention.

## Mirroring policy

The mapping from CACAO to n8n is the same one the compiler implements
for every worked example in this directory:

| CACAO step type    | n8n node type                        |
|--------------------|--------------------------------------|
| `start`            | `n8n-nodes-base.manualTrigger`       |
| `action` (no commands) | `n8n-nodes-base.set` (CACAO I/O contract as assignments) |
| `if-condition`     | `n8n-nodes-base.if`                  |
| `switch-condition` | `n8n-nodes-base.switch`              |
| `end`              | `n8n-nodes-base.noOp`                |

Node ids preserve the CACAO step id verbatim so the two artifacts can
be cross-referenced by id alone. Node labels mirror the CACAO step
`name`. Sequencing (`on_completion` / `on_success` / `on_failure`)
becomes n8n `connections` edges.

## What this example deliberately doesn't do

- It does not execute the workflow. The Set nodes carry the CACAO I/O
  contract but the right-hand values are blank — the integrator wires
  them to their own identity-protection signal source, IdP MFA /
  session management API, SaaS session revocation channel,
  lateral-movement query backend, IAM inventory / OAuth-grant audit
  surface, and any ticketing / paging endpoint.
- It does not ship operator credentials, secrets, or environment-
  specific endpoints. Secrets stay with the operator.
- It does not encode confirmation thresholds, blast-radius scoping
  rules, or persistence-removal decision logic — these are
  intent-bearing values the operator sets when binding the workflow
  to their environment.
- It does not ship Sigma detection rules (impossible-travel,
  token-theft, OAuth-grant abuse, etc.). Those are referenced from
  the canonical playbook's `external_references` and live upstream at
  SigmaHQ; the emitter only surfaces the rule references on the
  `x_secops_ng.detection_refs` assignment row of the step that acts
  on a Sigma hit.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
n8n is open source (Sustainable Use License) and runs as a Node.js
process: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. The
operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
