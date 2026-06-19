# content/evidence/contractual_obligations_tracker/

Contractual-obligations evidence stream — contributor home for the
artifact emitted by `playbook.contractual_obligations_tracker@v1`,
opening the NIS2 Article 21(2)(d) supply-chain control family at the
workflow layer.

## What this stream is

An operator running framework-compiled workflows under NIS2 Article
21(2)(d) (supply-chain security — security characteristics of direct
suppliers and service providers, with periodic re-attestation) has to
demonstrate that the security obligations it has accepted from each
supplier are inventoried, scheduled for review, and actually
re-reviewed before they go stale.

That demonstration takes the shape of one artifact per execution of
the contractual-obligations tracker workflow against a single
supplier-contract reference. The artifact pins, mechanically:

- the normalised contract record the workflow ingested (contract id,
  supplier reference, effective / expiry / jurisdiction envelope),
- the per-clause obligation set the workflow extracted (clause ref,
  obligation text, obligation kind, contractual cadence),
- the per-obligation review schedule the workflow derived from the
  obligation set and the operator's review-policy,
- the usual provenance and captured-at envelope.

This directory is the contributor home for that stream. The artifact
shape is declared in
[`schemas/evidence/contractual-obligations.schema.json`](../../../schemas/evidence/contractual-obligations.schema.json);
the regulatory anchor is
[`content/mappings/nis2/article-21-2-d.yaml`](../../mappings/nis2/article-21-2-d.yaml).

## Why a dedicated stream (not F-CP-03 supply-chain)

The F-CP-03 supply-chain evidence stream
([`content/evidence/supply-chain/`](../supply-chain/)) is the
**execution-time** surface: one artifact per workflow execution
enumerating the external-provider dependencies the workflow resolved
against, keyed on `(workflow_id, execution_id)` and enumerating
`provider_id` records.

This stream is the **contract-time** surface: one artifact per
supplier contract enumerating the obligations the operator has
accepted from that supplier and the per-obligation review schedule,
keyed on `contract_id` and enumerating `obligation` records.

The two surfaces share no key by design; they pin the operator's
supply-chain posture along orthogonal axes (what is being called at
runtime vs. what was contractually committed at procurement time).
The CORE-FANOUT sibling card will wire the cross-stream join on
`supplier_ref` ↔ `provider_id` (same shape vocabulary) once both
surfaces are at CORE.

## Maturity

`SKELETON stub`. The required-field shape and the high-level
`contract`, `obligations[]`, and `review_schedule[]` envelopes are
pinned so the CORE-FANOUT sibling cards can bind primitive emitters
against a stable contract. The inner object shapes (the clause-ref
grammar, the obligation-kind vocabulary lifted into a shared schema,
the per-obligation waiver / deferral envelope) are intentionally
permissive at the SKELETON layer; the EXTEND-schema sibling card
tightens them once the per-target emitters have been worked through.

## Pending siblings

- **EXTEND-schema** — tighten `obligation_record` (clause-ref grammar,
  shared `obligation_kind` vocabulary at
  `schemas/contractual_obligation_kind.json`) and `review_record`
  (shared `state` vocabulary at
  `schemas/obligation_review_state.json`, waiver / deferral envelope)
  once the per-target emitters land.
- **EXTEND-metrics** — author the supplier-attestation-staleness KRI
  and the supplier-obligation-coverage KPI in `content/metrics/` and
  wire them into the playbook and the schema.
- **CORE-FANOUT-{N8N,TMP,LG}** — per-target primitive bindings that
  read `extract-obligations` / `schedule-review` outputs and emit
  artifacts conforming to this schema.
