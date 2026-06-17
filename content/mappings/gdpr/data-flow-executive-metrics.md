# GDPR data flow — executive-metrics

Per-workflow GDPR data-flow entry for the `executive-metrics`
cookbook playbook (`playbook.executive_metrics@v1`). Filled in
against [`_data-flow-template.md`](./_data-flow-template.md). Together
the seven sections below form the Art. 30 Record of Processing
Activity entry for this workflow.

Workflow source of truth:
[`content/playbooks/executive-metrics/`](../../playbooks/executive-metrics/).

---

## 1. Purpose

The workflow exists to roll the operator's pinned KPI/KRI catalog
into a board-ready summary on a recurring cadence: load the catalog
version, evaluate each entry's formula against the rollup window
over the operator's telemetry / workflow / control-attestation
sources, group the evaluations by `control_ref` to produce a
composite control-effectiveness score, annotate the in-flight
summary with a board-attention flag when any metric hits its breach
band, and emit the structured summary artifact for the operator's
downstream board pack pipeline. The purpose is bounded to that
reporting decision and the metric hooks it produces
(`kri.control_effectiveness@v1`,
`kpi.review_completion_sla@v1`,
`kpi.corrective_action_close_rate@v1`,
`kri.corrective_action_overdue@v1`); the workflow does not retain
per-subject behavioural data, does not author free-form narrative
on identifiable subjects, and does not own the distribution channel
to the board.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(c) — legal obligation**. The processing is
necessary for compliance with the operator's effectiveness-
assessment obligations under **NIS2 Art. 21(2)(f)** (policies and
procedures to assess the effectiveness of cybersecurity risk-
management measures) and, where the operator is in scope, **DORA
Art. 6** (ICT risk-management framework, periodic review) as
transposed nationally. The board-ready summary and the control-
effectiveness score are the evidence the operator presents to
demonstrate the effectiveness-assessment obligation has been
discharged on the configured cadence.

Secondary: **GDPR Art. 6(1)(f) — legitimate interests** applies to
the internal control-effectiveness rollup portion of the workflow
that is not strictly mandated by the regulator template — the
operator's own programme-level scoring, board-attention flagging,
and per-control weighting policy. The operator has a legitimate
interest in maintaining a coherent view of its security posture for
governance bodies, and the data subjects (employees whose
operational metric contributions are aggregated into the rollup)
have a reasonable expectation that aggregate effectiveness measures
are produced from their operational telemetry.

Special-category data (Art. 9) is not the target of the workflow
and is not expected to be incidentally observed — the workflow
operates on aggregated metric evaluations and control-effectiveness
scores, not on per-subject telemetry. If an operator's catalog
pins a metric whose formula evaluates per-subject Art. 9 attributes
(for example, a sector-specific KPI on subject demographics), the
operator MUST re-score this section before the catalog version is
pinned.

## 3. Categories of data subjects and personal data

The workflow's inputs and outputs are heavily aggregated — the
intent of the rollup is the programme-level effectiveness score,
not per-subject reporting. The categories below cover the residual
personal data that can flow through the rollup despite the
aggregation:

Data subjects:

- **Employees of the operator** whose operational telemetry feeds
  the per-metric evaluations (incident commanders whose review
  completion is measured by `kpi.review_completion_sla@v1`,
  corrective-action owners whose close rate is measured by
  `kpi.corrective_action_close_rate@v1` /
  `kri.corrective_action_overdue@v1`). The subject's identifier is
  not present in the rollup output; only their aggregated
  contribution is.
- **Employees of the operator** named as catalog-version pin
  signatories or as authors of the per-control weighting policy
  the operator binds at run time. Their identifier appears in the
  audit trail of the catalog ref, not in the board summary itself.

Categories of personal data:

- **Aggregated operational counters** — per-metric observed values,
  matched threshold bands (target / warn / breach), per-control
  effectiveness scores, programme-level score. These carry no
  per-subject identifier; the personal-data status is inherited
  from the lower-layer sources the formulas read from.
- **Catalog-version metadata** — pin identifier and audit-trail
  entry naming the signatory who pinned the version for the run.
- **Audit-trail metadata** — invocation identifier, run timestamp,
  catalog ref, board-attention flag state. Personal identifiers
  in this metadata are limited to the catalog pin signatory and
  the run operator (where applicable).

The workflow does not introduce a new per-subject record. Where a
catalog entry's formula reads from a lower-layer source that
carries personal data (the incident-management workflow's case
store, the post-incident-review workflow's corrective-action
register), the per-subject record stays on that lower-layer store
and only the aggregated counter crosses into the rollup.

## 4. Recipients

Internal recipients:

- The **board pack pipeline** — primary recipient of the emitted
  summary artifact and the board-attention flag when set. The
  pipeline owns distribution, signing, and archival; the rollup
  does not.
- The **risk-management governance** function (the control_refs
  `control.control_effectiveness_test@v1` and
  `control.risk_management_policy@v1`) that owns the per-control
  weighting policy and the breach-band response.
- The **corrective-action register** (inherited from the post-
  incident-review workflow) — recipient of any catalog entry
  flagged as failing validation during the resolve step; the
  rollup records the validation failure rather than letting a
  malformed entry inflate or deflate effectiveness.
- The **operator's audit-trail store** — recipient of the
  invocation record, catalog pin, and board-attention-flag state
  per run.

External / processor recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **catalog source of truth** — the operator's metrics
  catalog registry, repository, or document store. The workflow
  reads from this source; it does not write back.
- The **summary-artifact store** that the downstream board pack
  pipeline consumes — typically the operator's GRC tool, board-
  pack repository, or document store.

Each operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production;
the framework does not ship the DPAs, but the data-flow record
names the dependency so a sovereignty review can verify it. Where
the rollup reads from a lower-layer source that already has its own
processor relationships (the parent incident-case store, the OCSF
telemetry store), those DPAs are inherited from the lower-layer
workflows' data-flow records rather than re-asserted here.

## 5. Retention

The workflow's durable artefacts are the **per-metric evaluations**
(`__metric_evaluations__`), the **control-effectiveness score**
(`__control_effectiveness_score__`), and the **board-ready summary
artifact** (`__board_summary_id__`). Retention is the operator's
governance-record window:

- **Board-ready summary artifacts** are retained for the operator's
  governance-record window — typically the longest of (a) the
  regulator's statutory record-keeping period under NIS2 Art. 21(2)
  (f) and DORA Art. 6 for effectiveness assessments, (b) the
  operator's board-records retention policy, and (c) the
  operator's litigation-hold policy. The operator configures the
  binding; the framework does not pick a default.
- **Per-metric evaluations and control-effectiveness scores** are
  retained alongside the summary artifact they feed into; they age
  under the same window because the summary's reproducibility
  depends on the input evaluations being available.
- **Catalog-version pin records** are retained for the audit-trail
  store's window; they are the evidence the operator presents to
  demonstrate which catalog version drove which run.
- **Lower-layer source records** (incident-case store entries,
  corrective-action register entries, OCSF telemetry) are NOT
  retained by the rollup; they age under their own data-flow
  records on the workflows that own them.

The retention boundary is enforced by the summary-artifact store's
lifecycle hook plus the audit-trail store's policy; the workflow
itself is stateless beyond the per-run artifacts.

## 6. Cross-border transfers

**No transfer** is the default scoring. The workflow is designed to
execute end-to-end on the operator's sovereign-hosted runtime (one of
the EU-hostable reference targets — n8n self-host, Temporal self-host,
or LangGraph self-host on Nebul / OVHcloud / Scaleway / Hetzner) with
an EU-resident catalog source, EU-resident lower-layer telemetry
and workflow stores, and an EU-resident summary-artifact store
inherited from the operator's existing GRC stack.

The technical controls that hold this scoring:

- The reference compile targets are framework-agnostic and run on
  the operator's own sovereign-hosted runtime; no SecOps-NG-hosted
  egress path exists in the workflow.
- The catalog source is operator-supplied through `__catalog_ref__`;
  the framework ships no default endpoint and no fallback that
  could route a catalog read outside the EU.
- The per-metric evaluation step reads from lower-layer telemetry,
  workflow, and control-attestation sources already resident on the
  operator's stack; no external aggregation service is invoked.
- The scoring policy (per-control weighting, KRI penalty function,
  missing-evidence treatment) is operator-supplied and executes
  locally; the framework only pins the input contract and the
  output shape.
- The emit step hands the summary artifact to the operator's board
  pack pipeline endpoint, which is operator-supplied.

If an operator binds a non-EU catalog registry, a non-EU summary-
artifact store, a non-EU scoring-policy service, or any external AI
classifier on the rollup's narrative fields, this scoring breaks —
the operator MUST re-score this section under "transfer under
SCCs / BCRs / derogation" and document the supplementary measures
(encryption-at-rest with operator-held keys, pseudonymisation of
any subject identifiers carried in catalog-entry attribution before
egress) before the binding goes live. Sovereignty review at compile
time is the gate.

## 7. Data subject rights

- **Access (Art. 15).** A subject who exercises a SAR against the
  operator can be answered by querying the lower-layer sources the
  rollup reads from (the incident-case store, the corrective-
  action register, the OCSF telemetry store). The rollup output is
  aggregated and does not carry per-subject identifiers; the SAR
  is answered against the lower-layer workflows' data-flow records
  rather than against the rollup artifact. The audit-trail entry
  identifying the catalog pin signatory is searchable on that
  signatory's identifier.
- **Rectification (Art. 16).** Applicable where the catalog pin or
  audit-trail attribution is recorded incorrectly. Rectification
  flows through the operator's catalog source of truth and the
  audit-trail store; the workflow inherits the corrected record on
  the next run. Per-subject rectification against the lower-layer
  sources is handled by those workflows' rectification paths.
- **Erasure (Art. 17).** The retention hook in §5 is the
  operational erasure pathway: summary artifacts and the per-
  metric evaluations age into the operator's governance-record
  window and are purged on TTL. A standalone subject-initiated
  erasure request against the rollup is generally not
  operationally meaningful — the artifacts are aggregated and
  carry no per-subject identifier — and per-subject erasure
  flows through the lower-layer workflows' erasure paths.
  Erasure against the catalog pin or audit-trail attribution is
  constrained by the regulatory record-keeping obligation in §2;
  the operator's DPO is the gate.
- **Objection (Art. 21).** Where the lawful basis is
  **Art. 6(1)(c) legal obligation** (the primary basis in §2),
  Art. 21 does not apply to the regulator-evidence portion of the
  processing. For the secondary **Art. 6(1)(f)** basis covering
  the internal control-effectiveness rollup, a data subject can
  object on grounds relating to their particular situation; the
  operational handling is to route the objection through the
  operator's DPO, with the overriding-legitimate-interest
  assessment as the gate. Because the rollup output is aggregated
  the practical effect of an objection is on the lower-layer
  workflows' contribution to the aggregate, not on the aggregate
  itself.
- **Automated decision-making (Art. 22).** The control-
  effectiveness scoring is a deterministic aggregation step under
  an operator-supplied weighting policy; the breach-band
  branching is a routing decision that hands off to a human-
  owned board pack pipeline. The workflow as shipped does not
  produce a legal or similarly significant effect on a data
  subject in its own right, so Art. 22 does not apply. If an
  operator binds a scoring policy whose output triggers an
  automated adverse action against a subject named in the lower-
  layer sources (automated performance-management consequence on
  a metric owner's contribution, automated regulator-facing
  attribution of a breach band to a named individual), the
  operator MUST re-score this section.
