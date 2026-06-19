# iam-auditor

Capability-inventory workflow for operators that need to demonstrate,
on every workflow execution, that the running form was invoked by a
known caller and that the caller held only the capabilities it was
supposed to exercise on that run.

The workflow emits one access-evidence artifact per execution against
[`schemas/evidence/access.schema.json`](../../../schemas/evidence/access.schema.json),
feeding the F-CP-07 access evidence stream under
[`content/evidence/access/`](../../evidence/access/).

## Maturity

`SKELETON` — scope is the CACAO topology plus the `x_secops_ng` joins
into the control / telemetry / metric layers. No compiler emitters,
no per-target examples, no byte-parity goldens at this layer; those
land in the sibling CORE / EXTEND cards (see
[Pending siblings](#pending-siblings)).

## State machine

```
workflow_start
   -> enumerate-identities
   -> enumerate-capabilities
   -> emit-access-evidence
   -> workflow_end
```

Transitions are deterministic — every state has exactly one
`on_completion` successor, no conditional branching at this layer.

| State                   | Purpose                                                                                                                                                |
|-------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| `enumerate-identities`  | Resolve the caller identity that invoked the compiled workflow on this execution. Role-shaped (service-account name, runtime principal, automation role); never an individual personal name or a credential-shaped string. |
| `enumerate-capabilities`| Walk the closed capability list (verb.resource tokens) the resolved identity held at execution time. The F-PT-01 platform-side guarantee that the caller actually held the listed capabilities at boot is orthogonal and out of scope for this workflow. |
| `emit-access-evidence`  | Combine the caller-identity block and the capability list into one access-evidence artifact shaped against `schemas/evidence/access.schema.json`. Byte-stable artifact id: SHA-256 of `workflow_id|execution_id|compile_target`. |

## Regulatory anchor

NIS2 Article 21(2)(i) — human resources security, access-control
policies, and asset management. Mapping entry:
[`content/mappings/nis2/article-21-2-i.yaml`](../../mappings/nis2/article-21-2-i.yaml)
(`nis2:art-21-2-i`).

## Linkage to F-CP-07

This workflow is one of the producers of the access evidence stream.
The artifact shape is owned by `schemas/evidence/access.schema.json`;
the stream's contributor home is
[`content/evidence/access/`](../../evidence/access/). The IAM auditor
is not the only producer — any compiled workflow can be instrumented
to emit an access artifact — but it is the workflow whose purpose is
to produce one as the primary deliverable.

## Sovereign-stack default

The artifact destination is operator-configured. No default non-EU
endpoint. The reference compile targets (n8n, Temporal, LangGraph)
will emit to whatever the operator wires; the playbook commits to the
artifact contract, not the destination.

## Files

- `playbook.cacao.json` — the CACAO v2 skeleton
  (`playbook.iam_auditor@v1`). Step bodies are declarative placeholders;
  no `core_body` primitive bindings at this layer.

## Pending siblings

This SKELETON intentionally stops at scaffold + control/telemetry/metric
joins. The remaining work is tracked as separate sibling cards:

- **CORE-FANOUT** — n8n / Temporal / LangGraph compiler emitters that
  read this CACAO and emit per-target artefacts producing the access
  evidence artifact at execution time.
- **EXTEND-examples** — per-target worked examples under
  `examples/{n8n,temporal,langgraph}/iam-auditor/`.
- **EXTEND-tests-goldens** — per-target byte-parity goldens under
  `tests/examples/{n8n,temporal,langgraph}/iam-auditor/` plus a
  content-level fixture asserting the emitted artifact validates
  against `schemas/evidence/access.schema.json`.
