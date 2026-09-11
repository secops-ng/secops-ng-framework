# ddos_response — n8n worked example

End-to-end demonstration of the SecOps-NG n8n reference compiler on the
ddos_response CACAO playbook. It is aimed at an integrator who already
runs n8n and wants to adopt a portable SecOps-NG playbook without
re-platforming: the example shows exactly which workflow shape the
compiler produces, how the CACAO contract surfaces on each node, and
where the integrator owns the seams.

This worked example pins the n8n end of the cross-target parity ring
for the `ddos_response` playbook (NIS2 Art.21(2)(b)). The Temporal
sibling ships under `../../temporal/ddos_response/` and the LangGraph
sibling under `../../langgraph/ddos_response/`; all three are pinned
by byte-parity goldens under `tests/examples/`.

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
playbook. The six action steps are `n8n-nodes-base.code` nodes whose
`pythonCode` is the exact primitive call from
`content/playbooks/ddos_response/primitives/`; the bodies assume
`PYTHONPATH` on the n8n host resolves that package. The external
inputs (`__service_inventory__`, `__vector_signals__`,
`__deadline_exceeded__`, `__validation_observations__`,
`__owner_channel__`) and the adapter seams (monitoring ingress,
mitigation-engagement surface, evidence store, notification channel)
are the operator's to wire against their connectors — see the
per-action notes below.

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
2. `detect availability anomaly` (`code`) — confirm the anomaly against
   the documented availability objective for the protected service.
3. `classify attack vector` (`code`) — categorise the anomaly as
   volumetric, protocol, or application-layer (or empty when
   classification could not be completed within the documented
   mitigation-engagement deadline).
4. `engage mitigation` (`code`) — exercise the operator's pre-bound
   response surface for the classified vector (upstream-scrubbing
   activation, rate-limit / WAF posture change, or failover to a
   documented standby).
5. `validate service restoration` (`code`) — probe the protected service
   against its documented availability objective and set
   `__service_restored__`.
6. `evidence capture` (`code`) — persist a dated attestation record
   covering the incident (vector, mitigation reference, restoration
   outcome).
7. `notify incident-management owner` (`code`) — surface the
   attestation to the incident-management owner via the operator's
   notification channel.
8. `ddos_response_end` (`noOp`) — end sentinel.

## Per-action wiring notes — CORE bodies

Every action step declares an `x_secops_ng.core_body` binding into the
deterministic primitives package, so the emitter renders each as a
Code node; the cross-target semantic contract is the primitives
package itself (Temporal binds via activity imports, LangGraph via
tool imports — all three call the same Python functions).

| Step id (suffix) | CACAO step | Deterministic primitive | Operator wires |
|---|---|---|---|
| `…000002` | detect availability anomaly | `detect.resolve_availability_trigger(protected_service, anomaly_window, service_inventory)` → `__trigger_envelope__` | the monitoring ingress raising the anomaly; `__service_inventory__` with the availability objective and all three pre-bound mitigation surfaces |
| `…000003` | classify attack vector | `classify.classify_attack_vector(signals=__vector_signals__, deadline_exceeded)` → `__classification__` | the packet-capture / flow-record reading that produces the three per-vector verdicts, and the deadline clock; the adapter extracts `__attack_vector__` (empty on the short-circuit) |
| `…000004` | engage mitigation | `mitigation.select_mitigation_engagement(attack_vector=__classification__.attack_vector, …, mitigation_surfaces=__trigger_envelope__.mitigation_surfaces)` → `__engagement__` | the response surface that executes the order (scrubbing provider activation, rate-limit / WAF posture push, or failover exercise); the adapter extracts `__mitigation_action_id__` |
| `…000005` | validate service restoration | `restoration.evaluate_service_restoration(availability_objective=__trigger_envelope__.availability_objective, observations=__validation_observations__)` → `__restoration_verdict__` | the observation surface supplying the validation-window samples; the adapter extracts `__service_restored__` |
| `…000006` | evidence capture | `evidence.compose_incident_evidence_record(…, restoration=__restoration_verdict__)` → `__evidence_record__` | the evidence store that publishes the record; the adapter extracts `__evidence_id__` |
| `…000007` | notify incident-management owner | `notify.compose_owner_notification(evidence_id=__evidence_record__.evidence_id, …, owner_channel=__owner_channel__)` → `__owner_notification__` | `__owner_channel__` and the messaging surface that delivers the page or the note |

The playbook is a linear chain (no `if-condition` / `switch-condition`
nodes); the short-circuit behaviour for an unclassified vector (the
engage primitive receives an empty vector and selects the
most-restrictive pre-bound mitigation) and for an unrestored service
(the evidence record carries the failure marker and the notification
pages) lives inside the primitives, not as a topology branch.

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
becomes n8n `connections` edges.

## What this example deliberately doesn't do

- It does not execute the workflow. The Code nodes call the
  deterministic primitives, but the external inputs and the adapter
  seams — anomaly-detection ingress, classifier verdicts, the
  mitigation surface, the restoration probe, the evidence store and
  the notification channel — are the integrator's to wire.
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
