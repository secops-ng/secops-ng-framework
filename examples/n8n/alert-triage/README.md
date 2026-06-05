# examples/n8n/alert-triage

Worked example: the `playbook.alert_triage@v1` CACAO v2 source playbook
compiled by the n8n reference compiler. Operators can import
`workflow.n8n.json` directly into an n8n instance to see the topology
the emitter produces; binding the placeholder Set / IF / Switch nodes
to real connectors (detection-pipeline push / shared-store pull
ingestion, telemetry-context enrichment, suppression / known-benign
cache, response branches) is the operator's job.

The seven CORE action steps with a primitives binding (ingest, enrich,
suppress, classify, p1 / p2 / p3 response) compile to
`n8n-nodes-base.code` nodes that call the deterministic primitive
directly; the single absent-body step (p4 informational — log and
close) compiles to an `n8n-nodes-base.set` node carrying the CACAO I/O
contract as editable assignment rows.

## Source

Canonical CACAO source playbook:

    ../../../content/playbooks/alert-triage.cacao.yaml

The YAML is the authored form. The n8n emitter consumes JSON via the
CACAO parser, so `regenerate.sh` mirrors the YAML to a byte-deterministic
JSON form (`playbook.cacao.json`) alongside this README before emitting
the n8n workflow. The two formats round-trip through `yaml.safe_load`
+ `json.dumps`.

Scenario, workflow, regulatory anchors, control / metric / telemetry
bindings, and the source's TODO markers are documented in the canonical
YAML. This folder holds the emitted artifact, the co-located JSON
mirror for easy diff inspection, and the regeneration script.

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
   canonical source. The workflow is **inactive** by default —
   review and bind it to your own connectors before activating.

The emitted workflow is a *snapshot of intent*, not a runnable
playbook. The Code nodes for the seven bound steps call the
deterministic primitive (subject to the `PYTHONPATH` note below);
the Set node for p4 log-and-close carries the CACAO I/O contract
(`in_args` / `out_args`) plus the `x_secops_ng` reference bundles
(control, telemetry, metric) as editable assignments; the IF and
Switch nodes carry placeholder conditions. Binding those rows and
populating those conditions is the operator's job.

## Regeneration

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/alert-triage/regenerate.sh

The script mirrors the canonical CACAO YAML source into this folder
as `playbook.cacao.json` and re-emits `workflow.n8n.json` via
`tools.compile --target n8n`.

A drift guard between the committed worked example and a fresh
regeneration lands in the sibling F-WF-03 n8n golden test card; until
then this folder ships regenerated outputs that should be refreshed
manually after any change to the source or to `compilers/n8n/*`.

## Mirroring policy

The mapping from CACAO to n8n is the same one the compiler implements:

| CACAO step type             | n8n node type                                                |
|-----------------------------|--------------------------------------------------------------|
| `start`                     | `n8n-nodes-base.manualTrigger`                               |
| `action` + `core_body` ref  | `n8n-nodes-base.code` (calls the deterministic primitive)    |
| `action` + no `core_body`   | `n8n-nodes-base.set` (carries CACAO I/O + refs)              |
| `if-condition`              | `n8n-nodes-base.if`                                          |
| `switch-condition`          | `n8n-nodes-base.switch`                                      |
| `end`                       | `n8n-nodes-base.noOp`                                        |

Node ids preserve the CACAO step id verbatim so the two artifacts can
be cross-referenced by id alone. Node labels mirror the CACAO step
`name`. Sequencing (`on_completion` / `on_success` / `on_failure` /
switch `cases`) becomes n8n `connections` edges.

## Per-action wiring notes — CORE bodies

The eight CORE action steps split into two emission shapes depending
on whether the canonical CACAO step declares an `x_secops_ng.core_body`
reference into the deterministic primitives package:

- **`core_body` set (ingest, enrich, suppress, classify, p1 / p2 / p3
  response).** The emitter renders the step as an `n8n-nodes-base.code`
  node whose `pythonCode` is the exact primitive call (e.g.
  `from alert_triage.primitives.prioritisation import prioritise ;
  __priority_verdict__ = prioritise(...)`). The deterministic policy
  is the same across n8n / Temporal / LangGraph because the three
  targets call the same Python function.
- **`core_body` absent (p4 informational — log and close).** No
  upstream primitive exists yet for this body, so the emitter renders
  it as an `n8n-nodes-base.set` node carrying the CACAO I/O contract
  (`in_args` / `out_args` / `x_secops_ng` reference bundles) as
  editable assignment rows. Operator binds.

| Step id (suffix) | CACAO step | Deterministic primitive | Notes |
|---|---|---|---|
| `…000002` | ingest typed alert payload | `primitives.payloads.validate_alert_payload(raw=__raw_payload__, source_shape=__alert_source_shape__)` | Operator binds `__raw_payload__` to their detection-pipeline push endpoint or shared alert store connector; the dispatcher routes on `__alert_source_shape__`. |
| `…000003` | enrich with telemetry context | `primitives.suppression.canonical_seen_key(detection_rule_id=…, subject_ref=…, asset_ref=…, classification=…)` | Operator binds the telemetry-context store; the canonical seen key collapses re-fires onto the same case inside the configured suppression window. |
| `…000005` | suppress and close | `primitives.suppression.canonical_seen_key(...)` | Same primitive, called in the suppress branch to record the close-out key. |
| `…000006` | classify and prioritise (deterministic policy) | `primitives.prioritisation.prioritise(detection_class=…, detection_severity=…, context=__asset_context__, correlates_open_case=…)` | Produces `PriorityVerdict` carrying the band used by step `…000007`. Free-text fields (analyst narrative) are summarised via `primitives.signatures.signature_schema` only — never priority. |
| `…000008` | response: p1 severe — page and escalate | `primitives.response.escalation_route(priority=__priority__, asset_criticality=…, internet_exposed=…, regulated_data=…)` | Operator binds the paging tier and the escalation handoff to their incident-management playbook; SLA enforcement lives in `kpi.mttr_critical@v1`. |
| `…000009` | response: p2 high — notify on-call | `primitives.response.notify_on_call(...)` | Operator binds the on-call routing and notification cadence. |
| `…00000a` | response: p3 routine — queue for review | `primitives.response.route_to_review_queue(...)` | Operator binds the review-queue placement; SLA lives in `kpi.review_completion_sla@v1`. |
| `…00000b` | response: p4 informational — log and close | (no scoring primitive — telemetry-coverage close) | Operator records the alert for false-positive-rate denominator and detection-coverage view; KPIs `kpi.false_positive_rate@v1` / `kpi.detection_coverage@v1`. |

### Why the bound steps are Code nodes and not Set nodes

n8n's `n8n-nodes-base.code` node lets operators run JavaScript or
Python inline. For steps with an `x_secops_ng.core_body` ref, the
emitter synthesises a Code node directly so the deterministic
primitive is exercised in n8n the same way it is in Temporal and
LangGraph, for three reasons:

1. The CACAO playbook is the canonical source and the primitives
   package is the deterministic policy it *means*. Calling the
   primitive directly from the n8n Code node keeps replay
   determinism intact across targets.
2. The cross-target replay property — same alert in, same
   `PriorityVerdict.inputs_digest` out — holds only if every target
   calls the same Python function. n8n binds via Code-node import,
   Temporal binds via activity import, LangGraph binds via node
   import. All three call `alert_triage.primitives.*`.
3. Operators who run n8n on infrastructure without Python — typical
   for community deployments on the n8n cloud — can drop a
   Python-runner wrapper between the Code node and the next step
   (e.g. a downstream HTTP request to a small operator-hosted Python
   service exposing `prioritise(...)`). The wiring is a deployment
   decision, not a content decision.

The Code-node body assumes `PYTHONPATH` on the n8n host resolves
`alert_triage.primitives`. For the operator-runner wrapper pattern:

    # operator-supplied wiring — not emitted by the compiler
    from alert_triage.primitives.prioritisation import prioritise
    item = $input.item.json
    verdict = prioritise(
        detection_class=item['detection_class'],
        detection_severity=item['detection_severity'],
        context=item['asset_context'],
        correlates_open_case=item['correlates_open_case'],
    )
    return {'json': {**item, 'priority': verdict.priority}}

The runner is operator-configured (Python interpreter, PYTHONPATH
pointing at the operator's deployment of
`content/playbooks/alert-triage/`, network policy) so it is not
encoded in the worked example.

## Observability — OTel + AuditTrail in the n8n runtime

n8n is a node-graph runtime, so OTel instrumentation is a per-node
operator concern rather than a per-node instruction in the emitted
JSON. The emitted workflow carries the topology and the CACAO I/O
contract; the operator wires the OTel exporter and the audit mirror
in their n8n host.

Two patterns work today:

- **Operator-side OTel wrapper.** An OpenTelemetry-instrumented n8n
  host (community OTel community-nodes or a custom wrapper around
  `n8n-nodes-base.code`) opens a span per executed node and tags it
  with the shared `secops_ng.*` attribute keyspace (`playbook.id`,
  `playbook.version`, `step.id`, `step.name`, `step.type`,
  `tool.name`, `compile.target = "n8n"`).
- **Python-runner AuditTrail mirror.** For the seven `core_body`-bound
  Code nodes, an operator-supplied wrapper around the primitive call
  can append an `AuditRecord` to the shared `AuditTrail` so the
  offline replay envelope (see
  [`../../../docs/observability/audit-mirror.md`](../../../docs/observability/audit-mirror.md))
  is consistent with the Temporal and LangGraph targets. The Set
  node for the absent-body step carries no audit body until the
  operator wires one alongside their connector.

The OTLP exporter endpoint, the n8n host process model, and the
choice of community-node or custom wrapper are operator-bound. The
sovereignty posture asks for an EU-resident collector — see
[`../../../docs/observability/audit-mirror.md`](../../../docs/observability/audit-mirror.md).

## What this example does not do

The n8n reference compiler translates **structure** and the
**CACAO I/O contract**, not **business logic**. The emitted workflow
carries the topology of the playbook (steps, transitions, conditional
routing), the per-step `in_args` / `out_args` and the `x_secops_ng`
reference bundles as Set rows, plus the lossy-translation notes
recorded under `meta.secops_ng_notes`. It does not carry:

- Operator-bound bindings (detection-pipeline push / shared-store
  pull alert sources, telemetry-context enrichment store, suppression
  / known-benign cache, response-branch ticketing / paging / queueing
  connectors).
- Credentials, secrets, or environment-specific endpoints.
- Detection logic — detection-rule references are pinned upstream;
  no detection rules are authored in this repo.
- Suppression-window length, intent-classification thresholds, or
  prioritisation policy values — these are pinned in
  `primitives.suppression` and `primitives.prioritisation` so the
  policy is the same across targets. Operators who diverge fork the
  primitive module rather than overriding at runtime.

Where a CACAO step expresses intent the target runtime cannot encode
(an `action` with no machine-readable `commands`, a switch with no
machine-readable `cases` expression, an if-condition with no
machine-readable expression, etc.), the emitter inserts an explicit
placeholder node and records the gap in `meta.secops_ng_notes` so a
human integrator sees exactly what they still need to wire.

## Operator runtime hand-off contract

The emitted artifact is a *snapshot of intent*, not a runnable
playbook. The hand-off boundary the n8n reference compiler draws:

| The framework ships              | The operator owns                                  |
|----------------------------------|----------------------------------------------------|
| CACAO topology as n8n nodes      | n8n host (self-hosted, EU-resident).               |
| Node ids preserving CACAO ids    | Connector credentials and endpoints.               |
| CACAO I/O contract as Set rows for absent-body steps | Detection-pipeline push / shared-store pull alert sources, telemetry-context enrichment store, suppression cache, response-branch connectors. |
| `core_body` Code nodes for ingest, enrich, suppress, classify, p1 / p2 / p3 response | `PYTHONPATH` reaching `alert_triage.primitives`, or a Python-runner Code node wrapping the call. |
| `meta.secops_ng_notes` for every lossy translation seam | Per-node OTel instrumentation and AuditTrail wrapper. |
| Cross-target replay determinism via shared primitives | Suppression window length, prioritisation thresholds — forked in `primitives/` rather than overridden at runtime. |

The walkthrough in
[`../../../docs/cookbook/alert-triage.md`](../../../docs/cookbook/alert-triage.md)
reads this end-to-end alongside the Temporal and LangGraph targets.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no alert
content, no identifying flows reach this repository or the SecOps-NG
project. The operator runs n8n on infrastructure they control — we
ship the structure, they own the data plane.
