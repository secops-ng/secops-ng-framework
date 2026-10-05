# ransomware_containment — n8n worked example

End-to-end demonstration of the SecOps-NG n8n reference compiler on the
ransomware_containment CACAO playbook. It is aimed at an integrator who
already runs n8n and wants to adopt a portable SecOps-NG playbook
without re-platforming: the example shows exactly which workflow shape
the compiler produces, how the CACAO contract surfaces on each node,
and where the integrator owns the seams.

## Files in this directory

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input mirror)  | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |
| `regenerate.sh`       | (tooling)       | bash script       |
| `README.md`           | —               | This file.        |

The canonical input is the CACAO v2 playbook at
`../../../content/playbooks/ransomware_containment/playbook.cacao.json`
(frozen). Scenario, regulatory anchors, control / metric / telemetry
bindings, and the operator-supplied bindings are documented in that
folder's `README.md`. This folder holds the emitted artifact, a
co-located byte-identical copy of the CACAO source for easy diff
inspection, and the regeneration script.

## How to import

1. In your own n8n instance, open the workflows list and choose
   **Import from File**.
2. Select `workflow.n8n.json` from this directory.
3. n8n loads ten nodes wired into the topology described below. The
   workflow is **inactive** by default — review and bind it to your own
   connectors before activating.

The emitted workflow is a *snapshot of intent*, not a runnable
playbook. The Code nodes call the bound primitives; binding the
adapter inputs they read to real connectors (EDR status and isolation
API, network ACL / SDN fallback, IdP session and token revocation,
backup platform and catalogue, paging channels, and the NIS2 Article 23
24-hour early-warning staging path) is the operator's job.

## How to regenerate

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/ransomware_containment/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

```bash
PYTHONPATH=. python -m tools.compile \
    content/playbooks/ransomware_containment/playbook.cacao.json \
    --target n8n \
    --out examples/n8n/ransomware_containment/workflow.n8n.json
```

The drift guard in
`tests/examples/ransomware_containment/test_n8n_workflow.py` fails the
suite if the committed `workflow.n8n.json` diverges from a fresh
regeneration, so the worked example stays honest as the compiler
evolves.

## Topology

The ransomware_containment playbook branches twice, then converges on a
linear containment chain. Ten n8n nodes, one per CACAO step:

1. `ransomware-start` (`manualTrigger`) — entry point; matches the
   CACAO `start` step.
2. `triage signal` (`code`) — decide confirmation and EDR availability
   from the hydrated signal.
3. `ransomware confirmed?` (`if`) — branch on the triage outcome.
   `true` routes to the EDR-capability check; `false` routes to the end
   sentinel.
4. `EDR available?` (`if`) — second branch on detection-capability
   availability. `true` routes to the EDR isolation node; `false`
   routes to the network ACL fallback so the playbook still completes
   when the EDR is unavailable.
5. `endpoint isolation — EDR isolate` (`code`) — preferred isolation
   path.
6. `endpoint isolation — network ACL deny (fallback)` (`code`) —
   fallback isolation path.
7. Both isolation branches converge on the linear chain:
   `identity revocation` (`code`) → `backup verification` (`code`) →
   `comms plan` (`code`) → `ransomware-end` (`noOp`).

## Primitive calls

Every action step binds a deterministic primitive through
`x_secops_ng.core_body`, and emits an n8n `code` node that imports it
and binds the step's output envelope to the call. The module prefix is
`content.playbooks.ransomware_containment.primitives`:

| Code node | Primitive | Reads | Writes |
|-----------|-----------|-------|--------|
| `triage signal` | `triage.triage_ransomware_signal` | `__hydrated_signal__`, `__edr_status__`, `__analyst_verdict__` | `__triage_record__` |
| `endpoint isolation — EDR isolate` | `isolation.compose_edr_isolation` | `__triage_record__`, `__authorisation_policy__`, `__requested_at__` | `__edr_isolation_directive__` |
| `endpoint isolation — network ACL deny (fallback)` | `isolation.compose_network_isolation` | `__triage_record__`, `__authorisation_policy__`, `__chokepoint_ref__`, `__requested_at__` | `__network_isolation_directive__` |
| `identity revocation` | `identity.compose_identity_revocation` | `__triage_record__`, `__idp_capabilities__`, `__protected_identities__`, `__requested_at__` | `__identity_revocation_directive__` |
| `backup verification` | `backup.select_known_good_snapshot` | `__snapshots__`, `__backup_catalogue__`, `__compromise_window_start__` | `__backup_selection__` |
| `comms plan` | `comms.compose_comms_plan` | `__triage_record__`, `__backup_selection__`, `__comms_channels__`, `__drafted_at__` | `__comms_plan__` |

The two `if-condition` nodes (`ransomware confirmed?`,
`EDR available?`) emit n8n `if` nodes whose conditions read
`__ransomware_confirmed__` and `__edr_available__`, fields extracted
from `__triage_record__` at the adapter seam. With every step bound and
both conditions machine-readable, `meta.secops_ng_notes` records no
lossy translations.

## Mirroring policy

The mapping from CACAO to n8n is the same one the compiler implements
for every worked example in this directory:

| CACAO step type    | n8n node type                        |
|--------------------|--------------------------------------|
| `start`            | `n8n-nodes-base.manualTrigger`       |
| `action` (bound)   | `n8n-nodes-base.code` (imports and calls `core_body`) |
| `action` (unbound) | `n8n-nodes-base.set` (CACAO I/O contract as assignments) |
| `if-condition`     | `n8n-nodes-base.if`                  |
| `switch-condition` | `n8n-nodes-base.switch`              |
| `end`              | `n8n-nodes-base.noOp`                |

Node ids preserve the CACAO step id verbatim so the two artifacts can
be cross-referenced by id alone. Node labels mirror the CACAO step
`name`. Sequencing (`on_completion` / `on_success` / `on_failure`)
becomes n8n `connections` edges.

## What this example deliberately doesn't do

- It does not execute the workflow. The Code nodes call the
  primitives, but the inputs they read come from adapters the
  integrator wires to their own EDR, IdP, backup, paging, and reporting
  endpoints, and the directives they emit are executed there.
- It does not ship operator credentials, secrets, or environment-
  specific endpoints. Secrets stay with the operator.
- It does not encode the operator's policy: which hosts and principals
  are protected, whether isolation is automatic, which channels page
  whom. Those arrive as adapter inputs. The confirmation rule and the
  24-hour early-warning clock are fixed in the primitives and pinned by
  their tests.
- It does not ship Sigma detection rules (shadow-copy deletion,
  ransomware file rename, overpass-the-hash, etc.). Those are
  referenced from the canonical playbook's `external_references` and
  live upstream at SigmaHQ. The per-step `detection_refs` stay on the
  canonical playbook; a bound step's Code node carries the primitive
  call, not the reference bundles.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
n8n is open source (Sustainable Use License) and runs as a Node.js
process: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. The
operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
