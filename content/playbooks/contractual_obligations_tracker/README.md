# contractual_obligations_tracker

Supplier-contract obligation tracker for operators who need to
demonstrate, on a declared cadence, that the security obligations
they have accepted in supplier contracts (security-control
commitments, audit-right windows, attestation cadences,
sub-processor-disclosure clauses, breach-notification cadences) are
inventoried, scheduled for review, and actually re-reviewed before
they go stale.

This workflow opens the **NIS2 Article 21(2)(d) supply-chain security**
control family at the workflow layer. It complements the F-CP-03
supply-chain evidence stream (which surfaces the per-execution
dependency surface a workflow resolved against) by surfacing the
**per-contract obligation surface** the operator has accepted from
each supplier.

The workflow emits one obligation-evidence artifact per execution
against
[`schemas/evidence/contractual-obligations.schema.json`](../../../schemas/evidence/contractual-obligations.schema.json),
feeding the obligation evidence stream under
[`content/evidence/contractual_obligations_tracker/`](../../evidence/contractual_obligations_tracker/).

## Maturity

`SKELETON` — scope is the CACAO topology plus the `x_secops_ng` joins
into the control / telemetry layers. No compiler emitters, no
per-target byte-parity goldens, and no canonical primitive bindings
at this layer; those land in the sibling CORE / EXTEND cards (see
[Pending siblings](#pending-siblings)).

## State machine

```
workflow_start
   -> ingest-contract
   -> extract-obligations
   -> schedule-review
   -> emit-obligation-evidence
   -> workflow_end
```

Transitions are deterministic — every state has exactly one
`on_completion` successor, no conditional branching at this layer.

| State                       | Purpose                                                                                                                                                                       |
|-----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ingest-contract`           | Read the supplier-contract record referenced by `__contract_ref__` from the operator-supplied document store and bind it to a normalised in-workflow contract record. Read-only by contract. |
| `extract-obligations`       | Walk the ingested contract record and extract the per-clause obligations the operator has accepted (clause ref, obligation text, obligation kind, contractual cadence). Deterministic on the same record. |
| `schedule-review`           | Derive the per-obligation review schedule from the extracted obligation set and the operator's review-cadence policy. Pure derivation; no supplier contact on this step.       |
| `emit-obligation-evidence`  | Combine contract record + obligation set + review schedule into one obligation-evidence artifact shaped against `schemas/evidence/contractual-obligations.schema.json`.        |

## Regulatory anchor

NIS2 Article 21(2)(d) — supply-chain security, including the security
characteristics of direct suppliers and service providers, with
periodic re-attestation. Mapping entry:
[`content/mappings/nis2/article-21-2-d.yaml`](../../mappings/nis2/article-21-2-d.yaml)
(`nis2:art-21-2-d`).

Where the operator is in scope of Article 22's Union-level coordinated
risk assessment of critical supply chains, the obligation-evidence
artifact this workflow emits is the per-entity input shape the
Cooperation Group's aggregation envelope consumes.

## Relation to F-CP-03 supply-chain evidence stream

[F-CP-03](../../../ROADMAP.md) is the **execution-time** supply-chain
evidence stream: one artifact per workflow execution enumerating the
external-provider dependencies the workflow resolved against. This
workflow is the **contract-time** counterpart: one artifact per
supplier contract enumerating the obligations the operator has
accepted from that supplier and the per-obligation review schedule.
Together the two streams pin the operator's supply-chain posture
along both axes — what is being called at runtime, and what was
contractually committed at procurement time.

The shapes are intentionally distinct (F-CP-03 keys on
`(workflow_id, execution_id)` and enumerates `provider_id` records;
this stream keys on `(contract_id)` and enumerates `obligation`
records); a CORE-FANOUT sibling card will pin the cross-stream join
on `provider_id` ↔ `supplier_ref` once both surfaces are at CORE.

## Sovereign-stack default

The document-store endpoint that `ingest-contract` reads, and the
artifact destination that `emit-obligation-evidence` writes, are
operator-configured. No default non-EU endpoint, no hosted DMS
dependency, no vendor SDK bundled. The reference compile targets
(n8n, Temporal, LangGraph) will emit to whatever the operator wires;
the playbook commits to the artifact contract, not the destination.

## Files

- `playbook.cacao.json` — the CACAO v2 skeleton
  (`playbook.contractual_obligations_tracker@v1`). Step bodies are
  declarative placeholders at this layer (no primitive bindings yet);
  the canonical primitive set lands in the CORE-FANOUT sibling cards.

## Pending siblings

This SKELETON intentionally stops at scaffold + control/telemetry
joins. The remaining work is tracked as separate sibling cards queued
serially once this SKELETON merges (to avoid concurrent byte-parity
golden churn across the three reference targets):

- **CORE-FANOUT-N8N** — n8n compiler emitter + byte-parity golden +
  worked example body under `examples/n8n/contractual_obligations_tracker/`.
- **CORE-FANOUT-TMP** — Temporal compiler emitter + byte-parity golden
  + worked example body under `examples/temporal/contractual_obligations_tracker/`.
- **CORE-FANOUT-LG** — LangGraph compiler emitter + byte-parity golden
  + worked example body under `examples/langgraph/contractual_obligations_tracker/`.
- **EXTEND-schema** — tighten the obligation-evidence schema's inner
  envelopes (per-obligation clause shape, per-obligation review-state)
  once the per-target emitters have been worked through.
- **EXTEND-metrics** — author the supplier-attestation-staleness KRI
  and the supplier-obligation-coverage KPI in `content/metrics/` and
  wire their `metric_refs` into the playbook and the schema. Held
  out of SKELETON to keep the metric_refs / catalog link guard green.
- **EXTEND-docs-closeout** — flip `F-WF-10` ROADMAP status from
  `Proposed` to `Shipped` and add the cookbook walkthrough.
