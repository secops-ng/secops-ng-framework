# ddos_response — n8n worked example

End-to-end demonstration of the SecOps-NG n8n reference compiler on the
ddos_response CACAO playbook. It is aimed at an integrator who already
runs n8n and wants to adopt a portable SecOps-NG playbook without
re-platforming: the example shows exactly which workflow shape the
compiler produces, how the CACAO contract surfaces on each node, and
where the integrator owns the seams.

This worked example pins the n8n end of the cross-target parity ring
for the `ddos_response` playbook (NIS2 Art.21(2)(b)). The Temporal
sibling ships under `../../temporal/ddos_response/`; the LangGraph
sibling lands in a separate card. Until all three are committed, this
folder pins the n8n slice of the three-target contract.

## Files in this directory

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input mirror)  | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |
| `regenerate.sh`       | (tooling)       | bash script       |
| `README.md`           | —               | This file.        |

The canonical input is the CACAO v2 playbook at
`../../../content/playbooks/ddos_response/playbook.cacao.json`.
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
assignments; binding those rows to real connectors (availability-anomaly
detector, attack-vector classifier, mitigation-engagement surface,
service-restoration probe, dated-attestation evidence store, and the
incident-management notification channel) is the operator's job.

## How to regenerate

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/ddos_response/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

```bash
PYTHONPATH=. python -m tools.compile \
    content/playbooks/ddos_response/playbook.cacao.json \
    --target n8n \
    --out examples/n8n/ddos_response/workflow.n8n.json
```

The drift guard in `tests/examples/n8n/ddos_response/test_golden.py`
fails the suite if the committed `workflow.n8n.json` diverges from a
fresh regeneration, so the worked example stays honest as the compiler
evolves.

## Topology

The ddos_response playbook is a linear chain — detect, classify,
mitigate, validate, evidence, notify. Eight n8n nodes, one per CACAO
step:

1. `ddos_response_start` (`manualTrigger`) — entry point; matches the
   CACAO `start` step. Carries the `__*__` workflow-scope variables
   (`__protected_service__`, `__anomaly_window__`, `__attack_vector__`,
   `__mitigation_action_id__`, `__service_restored__`,
   `__evidence_id__`) the operator's monitoring surface or
   operator-initiated trigger supplies.
2. `detect availability anomaly` (`set`) — confirm the anomaly against
   the documented availability objective for the protected service.
3. `classify attack vector` (`set`) — categorise the anomaly as
   volumetric, protocol, or application-layer (or empty when
   classification could not be completed within the documented
   mitigation-engagement deadline).
4. `engage mitigation` (`set`) — exercise the operator's pre-bound
   response surface for the classified vector (upstream-scrubbing
   activation, rate-limit / WAF posture change, or failover to a
   documented standby).
5. `validate service restoration` (`set`) — probe the protected service
   against its documented availability objective and set
   `__service_restored__`.
6. `evidence capture` (`set`) — persist a dated attestation record
   covering the incident (vector, mitigation reference, restoration
   outcome).
7. `notify incident-management owner` (`set`) — surface the
   attestation to the incident-management owner via the operator's
   notification channel.
8. `ddos_response_end` (`noOp`) — end sentinel.

## CACAO contract surfaces on Set nodes

Every `action`-without-commands step in the CACAO source emits an n8n
`set` node whose **assignments** carry the CACAO contract one row per
field:

- `in.<name>` rows for each entry in the step's `in_args`.
- `out.<name>` rows for each entry in the step's `out_args`.
- `x_secops_ng.<key>` rows for each key under the step's
  `x_secops_ng` block (`control_refs`, `telemetry_refs`, `metric_refs`).

The values are left blank (or pre-seeded with the reference-id list,
for `x_secops_ng` rows) so the integrator can wire them to expressions
that pull from upstream nodes, n8n variables, or operator-bound
connectors. Concretely on this playbook:

| Set node | `in.` rows | `out.` rows | `x_secops_ng.` rows |
|----------|------------|-------------|---------------------|
| `detect availability anomaly` | `protected_service`, `anomaly_window` | — | `control_refs`, `telemetry_refs` |
| `classify attack vector` | `protected_service`, `anomaly_window` | `attack_vector` | `control_refs`, `telemetry_refs` |
| `engage mitigation` | `protected_service`, `attack_vector` | `mitigation_action_id` | `control_refs`, `telemetry_refs` |
| `validate service restoration` | `protected_service`, `mitigation_action_id` | `service_restored` | `control_refs`, `telemetry_refs` |
| `evidence capture` | `protected_service`, `attack_vector`, `mitigation_action_id`, `service_restored` | `evidence_id` | `control_refs`, `telemetry_refs` |
| `notify incident-management owner` | `evidence_id`, `protected_service`, `service_restored` | — | `telemetry_refs` |

The playbook is a linear chain (no `if-condition` / `switch-condition`
nodes); the short-circuit behaviour for an unclassified vector or an
unrestored service is carried inside the CACAO step bodies via the
operator-bound expressions on the Set rows, not as a topology branch.
The lossy translation per step is recorded in `meta.secops_ng_notes` so
the integrator sees exactly which seams need attention.

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
  them to their own anomaly-detection, classifier, mitigation,
  restoration-probe, evidence-store, and notification endpoints.
- It does not ship operator credentials, secrets, or environment-
  specific endpoints. Secrets stay with the operator.
- It does not encode attack-vector classification rules, mitigation
  thresholds, or the wording of the incident-management notification —
  these are intent-bearing values the operator sets when binding the
  workflow to their environment.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
n8n is open source (Sustainable Use License) and runs as a Node.js
process: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. The
operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.
