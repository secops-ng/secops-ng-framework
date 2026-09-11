# examples/n8n/agentic_threat_response

Worked example: the `playbook.agentic_threat_response@v1` CACAO v2
playbook compiled by the n8n reference compiler. Operators can import
`workflow.n8n.json` directly into an n8n instance to see the topology
the emitter produces; binding the placeholder Set-node steps to real
connectors (agentic-threat detection source, IdP session / token
revocation, network micro-segmentation call, incident-management
hand-off, and evidence-bundle store for the NIS2 Article 23 chain) is
the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/agentic_threat_response/playbook.cacao.json

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
playbook. The five action steps are `n8n-nodes-base.code` nodes whose
`pythonCode` is the exact primitive call from
`content/playbooks/agentic_threat_response/primitives/`; the bodies
assume `PYTHONPATH` on the n8n host resolves that package. The
external inputs (`__raw_indicator__`, `__containment_window__`,
`__authorisation_policy__`, `__evidence_artifacts__`) and the adapter
seams (IdP execution, segmentation control plane, incident-management
dispatch, evidence store) are the operator's to wire against their
connectors — see the per-action notes below.

## Regeneration

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/agentic_threat_response/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

    PYTHONPATH=. python -m tools.compile \
        content/playbooks/agentic_threat_response/playbook.cacao.json \
        --target n8n \
        --out examples/n8n/agentic_threat_response/workflow.n8n.json

The canonical playbook under
`content/playbooks/agentic_threat_response/playbook.cacao.json` is the
single source. The drift guard between the committed worked example
and the emitter output is pinned by the agentic_threat_response example
test suite under `tests/examples/agentic_threat_response/`.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
n8n is open source (Sustainable Use License) and runs as a Node.js
process: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. The
operator runs n8n on infrastructure they control — we ship the
structure, they own the data plane.

## Per-action wiring notes — CORE bodies

Every action step declares an `x_secops_ng.core_body` binding into the
deterministic primitives package, so the emitter renders each as a Code
node; the cross-target semantic contract is the primitives package
itself (Temporal binds via activity imports, LangGraph via tool
imports — all three call the same Python functions).

| Step id (suffix) | CACAO step | Deterministic primitive | Operator wires |
|---|---|---|---|
| `…000002` | ingest agentic-threat indicator | `intake.hydrate_indicator(raw_indicator=__raw_indicator__)` → `__indicator_envelope__` | the detection-layer feed supplying `__raw_indicator__`; the adapter extracts `__affected_principal__` and mirrors `edges` into `__lateral_path__` |
| `…000003` | isolate affected credential set | `isolation.plan_credential_isolation(affected_principal, containment_window)` → `__isolation_plan__` | `__containment_window__` from the containment policy; the IdP endpoint that executes the ledger and the channel that delivers the IAM-auditor alert |
| `…000004` | contain lateral-movement path | `segmentation.derive_segmentation_rules(lateral_path=__indicator_envelope__.edges, authorisation_policy)` → `__segmentation_rules__` | `__authorisation_policy__` (the signed-off scope set); the segmentation control plane that applies the `deny_pivot` rules |
| `…000005` | escalate to incident-management | `escalation.compose_escalation_envelope(indicator_id, affected_principal, isolation_plan_id=__isolation_plan__.plan_id, segmentation_rule_ids=__segmentation_rules__.rules)` → `__escalation_envelope__` | the intake seam on the deployed `incident_management` workflow that receives the envelope |
| `…000006` | preserve evidence for notification chain | `evidence.seal_evidence_bundle(signal_id=__escalation_envelope__.signal_id, artifacts=__evidence_artifacts__)` → `__evidence_bundle_manifest__` | the evidence store supplying the four artifact refs + digests in `__evidence_artifacts__` and persisting the sealed bundle; the adapter extracts `__evidence_bundle__` |
