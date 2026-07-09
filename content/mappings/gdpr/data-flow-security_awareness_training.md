# GDPR data flow — security_awareness_training

Per-workflow GDPR data-flow entry for the `security_awareness_training`
cookbook playbook (`playbook.security_awareness_training@v1`). Filled
in against [`_data-flow-template.md`](./_data-flow-template.md).
Together the seven sections below form the Art. 30 Record of
Processing Activity entry for this workflow.

Workflow source of truth:
[`content/playbooks/security_awareness_training/`](../../playbooks/security_awareness_training/).

Programme-lifecycle companion to the already-shipped
`cyber_hygiene_training` (per-cycle operational execution) and
`phishing_triage` (reactive incident lane) playbooks under NIS2
Art. 21(2)(g). Where those two discharge the operational and
reactive halves of the clause, this workflow authors the structured
training programme upstream — assessment, curriculum, delivery,
completion-recording, gap-report, cycle-review — and the seven
sections below score the personal-data touchpoints that programme-
governance layer exercises.

---

## 1. Purpose

The workflow exists to operate the structured security-awareness
training programme lifecycle required by NIS2 Art. 21(2)(g):
schedule the training-needs assessment against the in-scope
programme surface, design or update the per-track training
curriculum against the assessment, deliver the cycle's curriculum
to in-scope cohorts along the operator's declared training
channels, record per-staff completion from the learning-management
surface, report the residual gap set (missed-mandatory, overdue
role-based, uncovered regulatory training requirement) to the
training owner, and close the cycle with a dated cycle-review
artifact. The purpose is bounded to that programme-governance
decision loop; the workflow does not author the operator's
underlying training policy itself, does not adjudicate individual
performance-management or disciplinary outcomes, and does not
overlap with the per-cycle operational execution the sibling
`cyber_hygiene_training` playbook covers.

## 2. Lawful basis

**Art. 6(1)(f) — legitimate interests**, with **Art. 6(1)(c) —
legal obligation** available as a secondary basis where the
operator runs under NIS2-implementing national law that compels
the periodic security-awareness training programme this playbook
governs.

The legitimate-interests case rests on the operator's interest in
maintaining a structured, audit-evident security-awareness training
programme balanced against the limited intrusion the workflow
makes into personal data: it reads staff identifiers and cohort /
role membership from the HR / identity source during assessment,
reads per-staff completion state from the learning-management
surface during record-completion, and emits per-staff completion
records and per-cohort aggregates into the operator's evidence
store. No special-category data within the meaning of GDPR Art. 9
is inspected by the workflow.

Where the operator runs under a NIS2-implementing national law
that compels the periodic programme this playbook governs,
Art. 6(1)(c) carries the same processing under a stronger basis.
The completion-recording and gap-reporting steps rely on the
legitimate-interest balance: per-staff completion records are used
for programme-governance reporting to the training owner and are
not used for individual performance management or disciplinary
action.

## 3. Categories of data subjects and personal data

**Data subjects**: employees and other in-scope staff of the
operator enumerated in `__training_scope__` (all human users of
the operator's information systems subject to mandatory awareness
training, plus role-holders subject to role-based training tracks).
The training owner notified indirectly through the gap-report and
cycle-review artifacts is also a data subject in scope.

**Personal data categories**:

- **Staff identifiers** — work-account identifiers (employee ID,
  corporate email address, or directory-service username) read by
  the schedule-assessment step from the HR / identity source and
  by the record-completion step from the learning-management
  surface.
- **Cohort and role membership** — the per-staff cohort assignment
  and role-based-track assignment resolved by the assessment step.
- **Training-state metadata** — per-staff completion state per
  track, completed-at timestamp, and overdue-by-days delta read by
  the record-completion step from the learning-management surface
  and rolled up into per-cohort aggregate.
- **Training-owner identifier** — name and contact endpoint of the
  training owner referenced in the gap-report and cycle-review
  artifacts (ticketing system identifier, chat thread identifier,
  email address — the operator's pre-bound channel only).

**Out of scope** (deliberate omission): authentication secrets,
training-content responses or free-text submissions, any biometric
or other Art. 9 special-category data, and any individual
performance-management or disciplinary data.

## 4. Recipients

- **Operator's evidence store** — primary recipient of the dated
  cycle-review artifact and the per-track curriculum, per-cohort
  delivery, per-staff and per-cohort completion, and residual gap-
  report records emitted by the workflow.
- **Training owner** — receives the gap-report and cycle-review
  references through the operator's pre-bound programme-governance
  channel (ticketing system, chat thread, email); the notification
  carries programme-level aggregates and the residual gap set, not
  per-staff records.
- **Catalogue metric pipeline** that reads programme-governance
  KPIs against the emitted records for programme-level rollup
  (handled by the sibling `executive_metrics` workflow); the rollup
  operates on aggregate counts, not per-staff records.

No external processor is invoked by the default configuration; the
HR / identity source, the learning-management surface, the
evidence store, and the notification channel are all operator-
bound infrastructure. Operators integrating a third-party
learning-management product engage that provider's own GDPR
posture (typically under a Data Processing Agreement); the DPA
itself lives outside the framework, but the dependency is visible
in the operator's binding of `__training_scope__`.

## 5. Retention

The dated cycle-review record is retained as the operator's
NIS2 Art. 21(2)(g) programme-governance evidence under the
operator's regulatory-retention overlay; the retention mechanism
is the evidence-bundle expiry rule shared with the other evidence
streams under `schemas/evidence/bundle.schema.json`. This workflow
does not maintain its own retention schedule.

The assessment, curriculum, delivery, per-staff completion, and
gap-report artifacts the workflow produces sit alongside the
cycle-review under the same retention overlay. Per-staff completion
records expire on the same schedule and are NOT retained in a
parallel performance-management store.

## 6. Cross-border transfers

**No transfer.** The default configuration runs the assessment,
curriculum authoring, delivery-intent emission, completion
recording, gap-report composition, and cycle-review emission
entirely against operator-bound, EU-resident endpoints (the
operator's HR / identity source, learning-management surface,
evidence store, and notification channel). No public-cloud-AI
dependency is wired on the workflow's hot path. Operators MAY swap
in a non-EU-hosted learning-management product, HR source,
evidence store, or notification channel; doing so is visible on a
fork of this data-flow doc, but is not the default and is not the
configuration the framework ships.

Where the operator's learning-management surface is non-EU-hosted
on the production side, the per-staff records this workflow reads
cross a Chapter V boundary on the upstream read; the operator's
overall binding (and its DPA / SCC posture) governs that boundary,
not this playbook. This data-flow doc flags the dependency so it
remains visible in review.

## 7. Data subject rights

Subject Access Requests, rectification requests, erasure requests,
and objections that bear on the staff records this workflow reads
are answered against the operator's HR / identity source and
learning-management surface — those surfaces are the authoritative
record-holders for the data subject.

The cycle-review, assessment, curriculum, delivery, per-staff
completion, and gap-report artifacts this workflow emits to the
evidence store carry derivative state (assignment, completion
state, overdue-by-days) sourced from the upstream surfaces. A
subject who has exercised an erasure right against the upstream
HR source has had their identity record removed there; the
derivative records held in the evidence store expire under the
regulatory-retention overlay (§5) and the operator's evidence-store
erasure procedure covers the case where erasure is exercised mid-
retention. The playbook does not maintain a parallel subject-
record store that must be erased independently.

Objections to the legitimate-interests basis (§2) against the
programme itself are answered at the operator level — the
discipline exists to discharge a regulatory obligation on the
operator, not on individual subjects. **Art. 22** (automated
decision-making producing legal or similarly significant effects)
does not apply to the workflow as shipped: no automated adverse
action is taken against the data subject from completion or gap-
report data. If an operator binds downstream automation that would
take such an adverse action, the operator MUST re-score this
section.

## 8. Outbound personal-data transfer

**No outbound personal-data transfer in the default configuration
— N/A.** Per §6, the default binding keeps the assessment,
curriculum authoring, delivery-intent emission, completion
recording, gap-report composition, and cycle-review emission on
operator-bound, EU-resident endpoints; the per-staff records and
per-cohort aggregates the workflow produces do not leave the
operator's EU-resident infrastructure.

The non-default-binding case where an operator wires a non-EU-
hosted learning-management product, HR source, evidence store, or
notification channel introduces a Chapter V outbound leg on the
binding the operator chose; that leg's scoring (destination class,
transfer mechanism, EU-residency posture, data minimisation) is
the operator's responsibility on their fork of this data-flow doc,
and the dependency is flagged in §4 and §6 so the swap is visible
in review.

Cross-reference §6: the workflow-as-a-whole cross-border scoring
is **no transfer** under the default configuration and this §8
carries no contradicting leg under that configuration.

If a future revision extends the workflow's artifacts to carry
training-content responses or per-individual performance-management
data, this section MUST be re-scored against the canonical
four-axis shape and §3 amended in the same change.
