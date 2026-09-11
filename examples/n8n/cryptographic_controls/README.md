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
3. n8n loads nine nodes wired into the topology described below. The
   workflow is **inactive** by default — review and bind it to your own
   connectors before activating.

The emitted workflow is a *snapshot of intent*, not a runnable
playbook. The six action steps are `n8n-nodes-base.code` nodes whose
`pythonCode` is the exact primitive call from
`content/playbooks/cryptographic_controls/primitives/`; the bodies
assume `PYTHONPATH` on the n8n host resolves that package, and the
Switch node routes the run on `__lifecycle_event__`. The external
inputs (`__declared_policy__`, `__key_record__`,
`__certificate_record__`, the enforcement observations, `__event_ts__`,
`__owner_channel__`) and the adapter seams (crypto-policy inventory,
KMS backend, storage-encryption and TLS-endpoint backends, CA backend,
evidence store, owner channel) are the operator's to wire.

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

The cryptographic_controls playbook resolves the policy, routes on
`__lifecycle_event__` to one of three lifecycle branches
(key-lifecycle, enforce-encryption, certificate-lifecycle), and
converges on the record-evidence / notify chain. Nine n8n nodes, one
per CACAO step (the lifecycle switch included):

1. `cryptographic_controls_start` (`manualTrigger`) — entry point.
   Carries the workflow-scope variables the operator's KMS/CA control
   plane, scheduler, or operator-initiated trigger supplies —
   `__lifecycle_event__` and `__crypto_scope__` among them.
2. `resolve policy inventory` (`code`) — resolve the operator's declared
   cryptography policy at the start of the lifecycle event; emits
   `__policy_inventory_id__`.
3. `route on lifecycle event` (`switch`) — route the run on
   `__lifecycle_event__`: the three key events to step 4, the three
   certificate events to step 6, `enforcement-gate` to step 5.
4. `key lifecycle` (`code`) — judge the executed generate / rotate /
   revoke action against the policy snapshot; emits
   `__key_lifecycle_record__`.
5. `enforce encryption` (`code`) — evaluate the at-rest and in-transit
   enforcement gate on the target workload; emits
   `__enforcement_decision__`.
6. `certificate lifecycle` (`code`) — judge the executed issue / renew /
   revoke action against the trust anchors and the expiry buffer; emits
   `__cert_lifecycle_record__`.
7. `record lifecycle evidence` (`code`) — persist the dated lifecycle-
   attestation record; emits `__lifecycle_attestation_id__`. All three
   branches converge here.
8. `notify crypto owner` (`code`) — surface the attestation to the
   cryptography owner via the operator's notification channel.
9. `cryptographic_controls_end` (`noOp`) — end sentinel.

## Per-action wiring notes — CORE bodies

Every action step declares an `x_secops_ng.core_body` binding into the
deterministic primitives package, so the emitter renders each as a Code
node; the cross-target semantic contract is the primitives package
itself (Temporal binds via activity imports, LangGraph via tool
imports — all three call the same Python functions).

| Step id (suffix) | CACAO step | Deterministic primitive | Operator wires |
|---|---|---|---|
| `…000002` | resolve policy inventory | `policy.resolve_policy_inventory(crypto_scope, declared_policy)` → `__policy_inventory__` | the policy store supplying `__declared_policy__` (or null); the adapter extracts `__policy_inventory_id__` |
| `…000009` | route on lifecycle event | — (Switch node on `__lifecycle_event__`) | nothing — the workflow routes the run |
| `…000003` | key lifecycle | `keys.record_key_lifecycle(lifecycle_event, key_record, policy_inventory)` → `__key_lifecycle_result__` | the KMS backend executing the action and supplying `__key_record__` (metadata only — material is refused) |
| `…000004` | enforce encryption | `enforcement.decide_enforcement_gate(workload_ref, observed_at, at_rest, in_transit, policy_inventory)` → `__enforcement_result__` | the storage-encryption and TLS-endpoint surfaces supplying the observed conditions; the provisioning control plane consuming the decision |
| `…000005` | certificate lifecycle | `certificates.record_certificate_lifecycle(lifecycle_event, certificate_record, policy_inventory)` → `__cert_lifecycle_result__` | the CA backend executing the action and supplying `__certificate_record__` |
| `…000006` | record lifecycle evidence | `attestation.compose_lifecycle_attestation(lifecycle_event, event_ts, policy_inventory, …)` → `__lifecycle_attestation__` | the evidence store publishing the attestation; the adapter extracts `__lifecycle_attestation_id__` |
| `…000007` | notify crypto owner | `notify.compose_owner_notification(…, has_breach=__lifecycle_attestation__.has_breach, has_policy_gap=…, owner_channel)` → `__owner_notification__` | `__owner_channel__` and the messaging surface that delivers it |

The lossy translations the emitter notes (workflow-scope variables
flattened onto the trigger) are recorded in `meta.secops_ng_notes` so
the integrator sees exactly which seams need attention.

## Mirroring policy

The mapping from CACAO to n8n is the same one the compiler implements
for every worked example in this directory:

| CACAO step type    | n8n node type                        |
|--------------------|--------------------------------------|
| `start`            | `n8n-nodes-base.manualTrigger`       |
| `action` with `core_body` | `n8n-nodes-base.code` (the primitive call as `pythonCode`) |
| `action` without `core_body` | `n8n-nodes-base.set` (CACAO I/O contract as assignments) — none remain on this playbook |
| `if-condition`     | `n8n-nodes-base.if`                  |
| `switch-condition` | `n8n-nodes-base.switch`              |
| `end`              | `n8n-nodes-base.noOp`                |

Node ids preserve the CACAO step id verbatim so the two artifacts can
be cross-referenced by id alone. Node labels mirror the CACAO step
`name`. Sequencing (`on_completion` / `on_success` / `on_failure`)
becomes n8n `connections` edges. This playbook branches once: the
`switch-condition` fans out to the three lifecycle branches on the
Switch node's per-case outputs, and every other step hands off via
`on_completion` on the default `main` output.

## What this example deliberately doesn't do

- It does not execute the workflow. The Code nodes call the
  deterministic primitives, but the external inputs and the adapter
  seams — KMS, CA, storage-encryption, TLS-endpoint, evidence store
  and notification channel — are the integrator's to wire.
- It does not ship operator credentials, secrets, or environment-
  specific endpoints. Secrets stay with the operator.
- It does not encode the algorithm floor, key-size floor, TLS-version
  floor, per-key-class rotation cadence, per-key-class expiry buffer,
  the CA trust anchors, or the wording of the cryptography-owner
  notification — these are intent-bearing values the operator sets
  when binding the workflow to their environment.

## Status

Bound — the n8n artifact ships byte-deterministic from the canonical
CACAO source and is pinned by the byte-parity drift guard under
`tests/examples/n8n/cryptographic_controls/`. All six action steps are
Code nodes calling their deterministic primitive, and the
enforcement-gate policy evaluator is one of them; the KMS, CA,
storage-encryption, TLS-endpoint, evidence-store and notification
surfaces are the operator's data plane. The operator walkthrough is
[`docs/cookbook/cryptographic_controls.md`](../../../docs/cookbook/cryptographic_controls.md).

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
n8n is open source (Sustainable Use License) and runs as a Node.js
process: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. The
operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
