# cryptographic_controls — n8n worked example

End-to-end demonstration of the SecOps-NG n8n reference compiler on
the `cryptographic_controls` CACAO playbook. This is the write-side
lifecycle counterpart to `crypto_posture_management`: it operates the
key-generate / key-rotate / key-revoke branch, the encryption-
enforcement gate against declared at-rest and in-transit floors, the
certificate issue / renew / revoke branch, and the dated lifecycle
attestation NIS2 Art. 21(2)(h) and DORA Art. 9(2)/(3) anchor on.

This worked example pins the n8n leg (target 1 of 3) of the
cross-target parity lane for the `cryptographic_controls` playbook.
The Temporal sibling ships under
`../../temporal/cryptographic_controls/`; the LangGraph sibling ships
under `../../langgraph/cryptographic_controls/`. Together the three
folders pin the full three-target contract for this playbook.

## Files in this directory

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input mirror)  | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |
| `regenerate.sh`       | (tooling)       | bash script       |
| `README.md`           | —               | This file.        |

The canonical input is the CACAO v2 playbook at
`../../../content/playbooks/cryptographic_controls/playbook.cacao.json`.
Scenario, regulatory anchors, control / metric / telemetry bindings,
and the operator-supplied bindings are documented in that folder's
`README.md`. This folder holds the emitted artifact, a co-located
byte-identical copy of the CACAO source for easy diff inspection, and
the regeneration script.

## How to import

1. In your own n8n instance, open the workflows list and choose
   **Import from File**.
2. Select `workflow.n8n.json` from this directory.
3. n8n loads eight nodes wired into the topology described below. The
   workflow is **inactive** by default — review and bind it to your own
   connectors before activating.

The emitted workflow is a *snapshot of intent*, not a runnable
playbook. The Set nodes carry the CACAO I/O contract as editable
assignments; binding those rows to real connectors (crypto-policy
inventory, KMS backend for the key-lifecycle branch, storage-encryption
and TLS-endpoint backends for the enforcement gate, CA backend for the
certificate-lifecycle branch, dated-attestation evidence store, and
the cryptography-owner notification channel) is the operator's job.

## How to regenerate

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/cryptographic_controls/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

```bash
PYTHONPATH=. python -m tools.compile \
    content/playbooks/cryptographic_controls/playbook.cacao.json \
    --target n8n \
    --out examples/n8n/cryptographic_controls/workflow.n8n.json
```

The drift guard in
`tests/examples/n8n/cryptographic_controls/test_golden.py` fails the
suite if the committed `workflow.n8n.json` diverges from a fresh
regeneration, so the worked example stays honest as the compiler
evolves.

## Topology

The cryptographic_controls playbook is a linear resolve-policy /
key-lifecycle / enforce-encryption / certificate-lifecycle /
record-evidence / notify chain. Eight n8n nodes, one per CACAO step:

1. `cryptographic_controls_start` (`manualTrigger`) — entry point.
   Carries the workflow-scope variables (`__lifecycle_event__`,
   `__crypto_scope__`) the operator's KMS/CA control plane, scheduler,
   or operator-initiated trigger supplies.
2. `resolve policy inventory` (`set`) — resolve the operator's declared
   cryptography policy at the start of the lifecycle event; emits
   `__policy_inventory_id__`.
3. `key lifecycle` (`set`) — discharge the generate / rotate / revoke
   branch of the key-lifecycle discipline against the operator's KMS
   backend; emits `__key_lifecycle_record__`.
4. `enforce encryption` (`set`) — evaluate the at-rest and in-transit
   enforcement gate on the target workload; emits
   `__enforcement_decision__`.
5. `certificate lifecycle` (`set`) — discharge the issue / renew /
   revoke branch of the certificate-lifecycle discipline against the
   operator's CA backend; emits `__cert_lifecycle_record__`.
6. `record lifecycle evidence` (`set`) — persist the dated lifecycle-
   attestation record; emits `__lifecycle_attestation_id__`.
7. `notify crypto owner` (`set`) — surface the attestation to the
   cryptography owner via the operator's notification channel.
8. `cryptographic_controls_end` (`noOp`) — end sentinel.

## CACAO contract surfaces on Set nodes

Every `action`-without-commands step in the CACAO source emits an n8n
`set` node whose **assignments** carry the CACAO contract one row per
field:

- `in.<name>` rows for each entry in the step's `in_args`.
- `out.<name>` rows for each entry in the step's `out_args`.
- `x_secops_ng.<key>` rows for each key under the step's
  `x_secops_ng` block (`control_refs`, `telemetry_refs`).

The values are left blank (or pre-seeded with the reference-id list,
for `x_secops_ng` rows) so the integrator can wire them to expressions
that pull from upstream nodes, n8n variables, or operator-bound
connectors.

The lossy translations the emitter notes (workflow-scope variables
flattened onto the trigger, CACAO contract rows surfaced as blank Set
assignments) are recorded in `meta.secops_ng_notes` so the integrator
sees exactly which seams need attention.

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
becomes n8n `connections` edges. This playbook is linear: every step
hands off via `on_completion`, so all node-to-node edges land on the
default n8n `main` output.

## What this example deliberately doesn't do

- It does not execute the workflow. The Set nodes carry the CACAO I/O
  contract but the right-hand values are blank — the integrator wires
  them to their own KMS, CA, storage-encryption, TLS-endpoint,
  evidence-store, and notification connectors.
- It does not ship operator credentials, secrets, or environment-
  specific endpoints. Secrets stay with the operator.
- It does not encode the algorithm floor, key-size floor, TLS-version
  floor, per-key-class rotation cadence, per-key-class expiry buffer,
  the CA trust anchors, or the wording of the cryptography-owner
  notification — these are intent-bearing values the operator sets
  when binding the workflow to their environment.

## Status

CORE — the n8n artifact ships byte-deterministic from the canonical
CACAO source and is pinned by the byte-parity drift guard under
`tests/examples/n8n/cryptographic_controls/`. Adapter Protocols under
`patterns.cryptographic_controls` (KMS backend, CA backend, storage-
encryption backend, TLS-endpoint backend) and the enforcement-gate
policy evaluator are a follow-on; the cookbook walkthrough for
operators lands in the sibling EXTEND card.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
n8n is open source (Sustainable Use License) and runs as a Node.js
process: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. The
operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
