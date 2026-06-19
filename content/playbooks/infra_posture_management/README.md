# infra_posture_management

Continuous infrastructure-posture-management workflow for operators
who need to demonstrate, on a declared cadence, that their in-scope
infrastructure (cloud accounts, identity boundaries, network baseline)
still matches the posture policy the organisation has adopted under
NIS2 Article 21(2)(a).

This workflow is the **continuous variant** of the Shipped
[F-WF-02 posture-audit](../../../ROADMAP.md#f-wf-02--posture-audit)
lane. F-WF-02 is the per-request audit shape; this workflow is the
scheduled re-execution shape that re-derives a posture artifact on
every tick so a regulator-facing reviewer can read the artifact series
back as the operator-side trail for periodic re-assessment.

The workflow emits one posture-evidence artifact per execution against
[`schemas/evidence/posture.schema.json`](../../../schemas/evidence/posture.schema.json),
feeding the posture evidence stream under
[`content/evidence/infra_posture_management/`](../../evidence/infra_posture_management/).

## Maturity

`SKELETON` — scope is the CACAO topology plus the `x_secops_ng` joins
into the control / telemetry / metric layers. No compiler emitters,
no per-target byte-parity goldens, and no canonical primitive bindings
at this layer; those land in the sibling CORE / EXTEND cards (see
[Pending siblings](#pending-siblings)).

## State machine

```
workflow_start
   -> collect-posture
   -> evaluate-controls
   -> emit-posture-evidence
   -> workflow_end
```

Transitions are deterministic — every state has exactly one
`on_completion` successor, no conditional branching at this layer.

| State                      | Purpose                                                                                                                                                       |
|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `collect-posture`          | Walk the operator's in-scope infrastructure manifest and read the current posture-state snapshot (cloud-account read APIs, identity read APIs, network baseline). Read-only by contract. |
| `evaluate-controls`        | Evaluate each control declared in the operator's posture policy against the collected snapshot. Deterministic on the same snapshot and the same policy version. |
| `emit-posture-evidence`    | Combine snapshot + per-control evaluation into one posture-evidence artifact shaped against `schemas/evidence/posture.schema.json`. Byte-stable artifact id: SHA-256 of `workflow_id|execution_id|compile_target|policy_version`. |

## Regulatory anchor

NIS2 Article 21(2)(a) — risk-analysis and information-system-security
policies, including periodic re-assessment with dated ownership.
Mapping entry:
[`content/mappings/nis2/article-21-2-a.yaml`](../../mappings/nis2/article-21-2-a.yaml)
(`nis2:art-21-2-a`).

## Continuous vs. per-request

F-WF-02 (`workflows/posture_audit/` in the audit-time lane) is the
**per-request** posture-audit shape: an operator or auditor submits a
manifest, the workflow walks it once, the report is returned. This
workflow is the **continuous** shape: scheduled re-execution emits a
posture artifact on every tick so the same audit logic feeds a durable
evidence series rather than a one-shot report. The two lanes share
the posture-evidence schema; they differ in cadence (request-driven
vs. scheduler-driven) and in the durability of the artifact series.

## Sovereign-stack default

Source endpoints for `collect-posture` (cloud-account read APIs,
identity-provider read APIs, network-baseline read APIs) and the
artifact destination for `emit-posture-evidence` are operator-configured.
No default non-EU endpoint, no hosted-SaaS dependency, no vendor SDK
bundled. The reference compile targets (n8n, Temporal, LangGraph)
will emit to whatever the operator wires; the playbook commits to the
artifact contract, not the destination.

## Files

- `playbook.cacao.json` — the CACAO v2 skeleton
  (`playbook.infra_posture_management@v1`). Step bodies are
  declarative placeholders (`x_secops_ng.core_body.placeholder: true`);
  no primitive bindings at this layer.

## Pending siblings

This SKELETON intentionally stops at scaffold + control/telemetry/metric
joins. The remaining work is tracked as separate sibling cards Aurora
queues serially once this SKELETON merges (to avoid concurrent
byte-parity golden churn):

- **CORE-FANOUT-N8N** — n8n compiler emitter + byte-parity golden +
  worked example body under `examples/n8n/infra_posture_management/`.
- **CORE-FANOUT-TMP** — Temporal compiler emitter + byte-parity golden
  + worked example body under `examples/temporal/infra_posture_management/`.
- **CORE-FANOUT-LG** — LangGraph compiler emitter + byte-parity golden
  + worked example body under `examples/langgraph/infra_posture_management/`.
- **EXTEND-docs-closeout** — flip `F-WF-06` ROADMAP status from
  `Proposed` to `Shipped` and add the cookbook walkthrough.
