# GDPR data flow — cyber_hygiene_training

Per-workflow GDPR data-flow entry for the `cyber_hygiene_training`
cookbook playbook (`playbook.cyber_hygiene_training@v1`). Filled in
against [`_data-flow-template.md`](./_data-flow-template.md).
Together the seven sections below form the Art. 30 Record of
Processing Activity entry for this workflow.

Workflow source of truth:
[`content/playbooks/cyber_hygiene_training/`](../../playbooks/cyber_hygiene_training/).

---

## 1. Purpose

The workflow exists to operate the basic cyber-hygiene and staff
cybersecurity-training posture surface required by NIS2 Art.
21(2)(g): inventory the in-scope training roster against the
declared training scope, schedule the per-cycle awareness and
role-based training assignments, run the cycle's phishing-simulation
exercise, track completion of mandatory training and report-rate on
the simulation, capture a dated training-attestation artifact, and
notify the training owner of any gaps. The purpose is bounded to
that exercise decision and the metric hooks it produces
(`kpi.training_completion_rate@v1`, `kpi.phishing_sim_click_rate@v1`);
the workflow does not author the operator's training or hygiene
policy itself, does not adjudicate staff disciplinary outcomes from
simulation results, and the phishing-simulation step is a documented
exercise that does not trigger downstream incident response or
alter production mailflow controls.

## 2. Lawful basis

**Art. 6(1)(f) — legitimate interests**, with **Art. 6(1)(c) —
legal obligation** available as a secondary basis where the
operator runs under NIS2-implementing national law that compels
the periodic training and hygiene exercise this playbook operates.

The legitimate-interests case rests on the operator's interest in
maintaining the cyber-hygiene posture of the entity, balanced
against the limited intrusion the workflow makes into personal
data: it reads staff identifiers and role/cohort membership from
the HR / identity source, completion state from the learning-
management surface, and per-recipient simulation interaction
metadata from the simulation dispatch endpoint. No special-category
data within the meaning of GDPR Art. 9 is inspected by the
workflow.

Where the operator runs under a NIS2-implementing national law that
compels this exercise, Art. 6(1)(c) carries the same processing
under a stronger basis. The phishing-simulation step in particular
relies on the legitimate-interest balance: the simulation is
clearly labelled and serves the awareness purpose, the per-recipient
interaction data is not used for individual performance management
or disciplinary action, and the aggregate metrics (cohort click-rate
and report-rate) are what the operator surfaces in the attestation.

## 3. Categories of data subjects and personal data

**Data subjects**: employees and other in-scope staff of the
operator enumerated in `__training_scope__` (typically all human
users of the operator's information systems subject to mandatory
awareness training, plus the role-holders subject to role-based
training tracks, plus the cohorts enrolled in the phishing-
simulation programme). The training owner notified at the
notify-gaps step is also a data subject in scope.

**Personal data categories**:

- **Staff identifiers** — work-account identifiers (employee ID,
  corporate email address, or directory-service username) read by
  the inventory-training-roster step from the HR / identity source.
- **Cohort and role membership** — the per-staff cohort assignment
  and role-based-track assignment used by the scheduling step.
- **Training-state metadata** — per-staff completion state per
  track, completed-at timestamp, overdue-by-days delta read by the
  track-completion step from the learning-management surface.
- **Simulation-interaction metadata** — per-recipient record of
  template id, delivered-at, clicked (boolean), reported (boolean),
  and time-to-report emitted by the run-phishing-simulation step.
- **Training-owner identifier** — name and contact endpoint of the
  training owner notified at the notify-gaps step (ticketing system
  identifier, chat thread identifier, email address — the operator's
  pre-bound channel only).

**Out of scope** (deliberate omission): authentication secrets,
training-content responses or free-text submissions, any biometric
or other Art. 9 special-category data, and any individual
performance-management or disciplinary data sourced from the
simulation results.

## 4. Recipients

- **Operator's evidence store** — primary recipient of the dated
  training-attestation record (the audit-evident artifact NIS2 Art.
  21(2)(g) reviewers read), which carries the per-cohort aggregate
  completion-rate, click-rate, and report-rate, plus the per-staff
  overdue-completion records.
- **Training owner** along their pre-bound channel — receives the
  attestation reference and the gap summary via the notify-gaps
  step. The notification carries the attestation reference and the
  aggregate gap summary, not the per-recipient simulation-
  interaction records.
- **Catalogue metric pipeline** that reads
  `kpi.training_completion_rate@v1` and
  `kpi.phishing_sim_click_rate@v1` from the emitted records for
  programme-level rollup (handled by the sibling `executive_metrics`
  workflow); the rollup operates on aggregate counts, not per-staff
  records.

No external processor is invoked by the default configuration; the
HR / identity source, the learning-management surface, the
phishing-simulation dispatch endpoint, the evidence store, and the
notification channel are all operator-bound infrastructure.
Operators integrating a third-party learning-management product or
phishing-simulation platform engage that provider's own GDPR
posture (typically under a Data Processing Agreement); the DPA
itself lives outside the framework, but the dependency is visible
in the operator's binding of `__training_scope__`.

## 5. Retention

The dated training-attestation record is retained as the operator's
NIS2 Art. 21(2)(g) evidence under the operator's regulatory-
retention overlay; the retention mechanism is the evidence-bundle
expiry rule shared with the other evidence streams under
`schemas/evidence/bundle.schema.json`. This workflow does not
maintain its own retention schedule.

The training-roster snapshot, cycle assignment, simulation-run, and
completion-tracking artifacts the workflow produces sit alongside
the attestation under the same retention overlay. Per-recipient
simulation-interaction records inside those artifacts are bounded
to identifiers and interaction metadata; once the parent evidence
bundle expires, the per-recipient records expire with it. Per-staff
completion records expire on the same schedule and are NOT retained
in a parallel performance-management store.

## 6. Cross-border transfers

**No transfer.** The default configuration runs the roster
inventory, the cycle scheduling, the phishing-simulation dispatch,
the completion tracking, the evidence-capture emission, and the
notify dispatch entirely against operator-bound, EU-resident
endpoints (the operator's HR / identity source, learning-management
surface, simulation dispatch endpoint, evidence store, and
notification channel). No public-cloud-AI dependency is wired on
the workflow's hot path. Operators MAY swap in a non-EU-hosted
learning-management product, phishing-simulation platform, HR
source, evidence store, or notification channel; doing so is
visible on a fork of this data-flow doc, but is not the default
and is not the configuration the framework ships.

Where the operator's learning-management surface or phishing-
simulation platform is non-EU-hosted on the production side, the
per-staff records this workflow reads or emits cross a Chapter V
boundary on the upstream read/write; the operator's overall
binding (and its DPA / SCC posture) governs that boundary, not
this playbook. This data-flow doc flags the dependency so it
remains visible in review.

## 7. Data subject rights

Subject Access Requests, rectification requests, erasure requests,
and objections that bear on the staff records this workflow reads
are answered against the operator's HR / identity source and
learning-management surface — those surfaces are the authoritative
record-holders for the data subject.

The attestation record and the per-staff and per-recipient records
this workflow emits to the evidence store carry derivative state
(completion state, completed-at, simulation click/report) sourced
from the upstream surfaces. A subject who has exercised an erasure
right against the upstream HR source has had their identity record
removed there; the derivative records held in the evidence store
expire under the regulatory-retention overlay (§5) and the
operator's evidence-store erasure procedure covers the case where
erasure is exercised mid-retention. The playbook does not maintain
a parallel subject-record store that must be erased independently.

Objections to the legitimate-interests basis (§2) against the
training and simulation exercise itself are answered at the
operator level — the discipline exists to discharge a regulatory
obligation on the operator, not on individual subjects.
**Art. 22** (automated decision-making producing legal or similarly
significant effects) does not apply to the workflow as shipped:
the simulation-interaction metadata is not used to take an adverse
automated action against the data subject. If an operator binds a
classifier or downstream automation that would take such an
adverse action from simulation results, the operator MUST re-score
this section.

## 8. Outbound personal-data transfer

**No outbound personal-data transfer in the default configuration
— N/A.** Per §6, the default binding keeps the roster inventory,
the cycle scheduling, the phishing-simulation dispatch, the
completion tracking, the evidence-capture emission, and the notify
dispatch on operator-bound, EU-resident endpoints; the per-staff
and per-recipient records the workflow produces do not leave the
operator's EU-resident infrastructure.

The non-default-binding case where an operator wires a non-EU-
hosted learning-management product, phishing-simulation platform,
HR source, evidence store, or notification channel introduces a
Chapter V outbound leg on the binding the operator chose; that
leg's scoring (destination class, transfer mechanism, EU-residency
posture, data minimisation) is the operator's responsibility on
their fork of this data-flow doc, and the dependency is flagged in
§4 and §6 so the swap is visible in review.

Cross-reference §6: the workflow-as-a-whole cross-border scoring
is **no transfer** under the default configuration and this §8
carries no contradicting leg under that configuration.

If a future revision binds a non-default learning-management or
simulation surface, or extends the attestation record to carry
training-content responses or per-individual performance-management
data, this section MUST be re-scored against the canonical
four-axis shape and §3 amended in the same change.
