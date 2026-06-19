# content/evidence/infra_posture_management/

Posture evidence stream — contributor home for the artifact emitted
by `playbook.infra_posture_management@v1`, the continuous variant of
the F-WF-02 posture-audit lane.

## What this stream is

An operator running framework-compiled workflows under NIS2 Article
21(2)(a) (risk-analysis and information-system-security policies,
including periodic re-assessment) has to demonstrate that the
posture of their in-scope infrastructure is not just policy on paper
— that it is *re-evaluated* on a declared cadence, that the results
are archived, and that each evaluation is pinned to the specific
policy version in force at evaluation time.

That demonstration takes the shape of one artifact per scheduled
re-execution of the infrastructure-posture-management workflow. The
artifact pins, mechanically:

- the posture-state snapshot the workflow collected over the
  operator's in-scope infrastructure manifest (cloud accounts,
  identity boundaries, network baseline),
- the per-control evaluation result set the workflow derived against
  that snapshot under the policy version in force at evaluation time,
- the usual provenance and captured-at / evaluated-at envelope.

This directory is the contributor home for that stream. The artifact
shape is declared in
[`schemas/evidence/posture.schema.json`](../../../schemas/evidence/posture.schema.json);
the regulatory anchor is
[`content/mappings/nis2/article-21-2-a.yaml`](../../mappings/nis2/article-21-2-a.yaml).

## Maturity

`SKELETON stub`. The required-field shape and the high-level
`posture_state` / `control_evaluation` envelopes are pinned so the
CORE-FANOUT sibling cards can bind primitive emitters against a stable
contract. The inner object shapes (the per-resource configuration
shape inside `posture_state`, the deviation-list inside
`control_evaluation`) are intentionally permissive at the SKELETON
layer; the EXTEND-schema sibling card tightens them once the
per-target emitters have been worked through.

## Relation to F-WF-02 posture-audit

[F-WF-02](../../../ROADMAP.md#f-wf-02--posture-audit) is the
**per-request** posture-audit lane: an operator or auditor submits a
manifest, the workflow walks it once, the report is returned. The
infrastructure-posture-management workflow whose evidence lives here
is the **continuous** lane: scheduled re-execution emits a posture
artifact on every tick so the same audit logic feeds a durable
evidence series rather than a one-shot report. The two lanes share
this schema; they differ in cadence (request-driven vs. scheduler-
driven) and in the durability of the artifact series.

## Pending siblings

- **EXTEND-schema** — tighten `posture_state` (per-resource
  configuration shape) and `control_evaluation` (deviation list) once
  the per-target emitters land.
- **CORE-FANOUT-{N8N,TMP,LG}** — per-target primitive bindings that
  read `collect-posture` / `evaluate-controls` outputs and emit
  artifacts conforming to this schema.
