# GDPR data flow — dora_ict_risk_selfassess

Per-workflow GDPR data-flow entry for the `dora_ict_risk_selfassess`
cookbook playbook (`playbook.dora_ict_risk_selfassess@v1`). Filled in
against [`_data-flow-template.md`](./_data-flow-template.md).
Together the seven sections below form the Art. 30 Record of
Processing Activity entry for this workflow.

Workflow source of truth:
[`content/playbooks/dora_ict_risk_selfassess/`](../../playbooks/dora_ict_risk_selfassess/).

---

## 1. Purpose

The workflow exists to produce a single dated attestation
demonstrating coverage of the five DORA Chapter II ICT risk
management sections (Article 6 ICT risk-management framework,
Article 7 ICT systems / protocols / tools, Article 8 identification,
Article 10 detection, Article 11 response and recovery) on the
self-assessment cadence the operator documents — primarily the
Art. 6(5) annual review of the ICT risk-management framework plus
the post-major-incident review trigger the same paragraph names. It
reads the operator's evidence store for the current self-assessment
window, binds each collected evidence record to the section atom it
discharges and the producing-playbook slug that emitted it, scores
each of the five sections against the operator's documented
four-bucket coverage rubric (present-and-current / present-but-stale
/ absent-with-declared-exception / absent-uncovered), and emits the
dated attestation record. The purpose is bounded to that
whole-Chapter roll-up decision and the metric hook it produces
(`kri.control_effectiveness@v1`); the workflow does not itself
discharge any of the per-section obligations (those are owned by the
per-section producing playbooks the outbound overlay enumerates) and
does not own the distribution channel to a supervisory authority.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(c) — legal obligation**. The processing is
necessary for compliance with the operator's ICT risk-management
obligations under **DORA Art. 6** (sound, comprehensive and
well-documented ICT risk-management framework, reviewed at least
annually under **Art. 6(5)** and upon the occurrence of major
ICT-related incidents); competent authorities exercise their tasks
under DORA Chapter VII against the whole Chapter II ICT risk
management surface, and the dated attestation is the evidence the
operator presents to demonstrate the obligation has been discharged
on the documented cadence.

Secondary: **GDPR Art. 6(1)(f) — legitimate interests** applies to
the internal governance portion of the workflow that is not strictly
mandated by the supervisory template — the operator's own
programme-level scoring against the four-bucket coverage rubric, the
whole-Chapter roll-up verdict beyond the per-section bucket
enumeration, and the audit-trail attribution on the dated
attestation record. The operator has a legitimate interest in
maintaining a coherent view of its Chapter II coverage posture for
its governance bodies and its competent-authority interactions.

Special-category data (Art. 9) is not the target of the workflow
and is not expected to be incidentally observed — the workflow
operates on aggregated per-section coverage buckets, not on
per-subject telemetry. If an operator's producing-playbook set
carries per-subject Art. 9 attributes into an evidence record whose
attribution surfaces on the attestation record, the operator MUST
re-score this section before the attestation binding is pinned.

## 3. Categories of data subjects and personal data

The workflow's inputs and outputs are heavily aggregated — the
intent of the roll-up is the whole-Chapter coverage attestation,
not per-subject reporting. The categories below cover the residual
personal data that can flow through the roll-up despite the
aggregation:

Data subjects:

- **Employees of the operator** named as producing-playbook owners
  or as authors of the four-bucket coverage rubric and the
  per-section freshness-threshold policy the scoring step binds
  against. Their identifier appears in the audit trail of the
  rubric ref and the producing-playbook attribution, not in the
  per-section bucket itself.
- **Employees of the operator** named as attestation signatories,
  where the operator's governance policy binds a signatory to the
  dated attestation record. The signatory's identifier appears on
  the attestation artifact as accountability metadata.
- **Employees of the operator** whose operational contribution feeds
  the lower-layer evidence records the collect step reads against
  (incident owners on `incident_management` /
  `ransomware_containment`, asset stewards on `asset_management`,
  supplier owners on `supply_chain_security`, detection engineers on
  `detection_engineering`, alert responders on `alert_triage`,
  backup operators on `backup_recovery`, on-call responders on
  `on_call_rotation`, and so on across the producing playbooks the
  five section atoms anchor against). The subject's identifier stays
  on the lower-layer evidence record; only the aggregated
  per-section bucket and the producing-playbook slug cross into the
  roll-up.

Categories of personal data:

- **Aggregated per-section coverage buckets** — the four scoring
  buckets applied to each of the five Chapter II section atoms
  (dora:art-6-framework, dora:art-7-systems-protocols-tools,
  dora:art-8-identification, dora:art-10-detection,
  dora:art-11-response-recovery), plus the whole-Chapter roll-up
  verdict. These carry no per-subject identifier; the personal-data
  status is inherited from the lower-layer producing playbooks the
  collect step reads from.
- **Producing-playbook attribution metadata** — the playbook slug,
  the evidence-record identifier, and the SecOps-NG content-model
  overlay refs (control, telemetry, metric) that carry across from
  the producing playbook. Per-subject identifiers stay on the
  lower-layer record and are not carried into the mapping output.
- **Unbound-evidence flag** — the mapping step records evidence
  records that do not bind to a documented section atom as unbound
  and flags them on the attestation record. The flag carries the
  producing-playbook attribution but not the lower-layer per-subject
  payload.
- **Declared-exception attribution** — where a section is scored
  absent-with-declared-exception, the attestation record cites the
  dated Art. 6 ICT-risk-management-framework exception and the
  exception's author (an operator employee). The exception body
  stays on the operator's governance store; only the exception
  reference crosses into the attestation.
- **Audit-trail metadata** — invocation identifier, assessment
  window identifier, attestation timestamp, attestation signatory
  reference. Personal identifiers in this metadata are limited to
  the attestation signatory and the run operator (where
  applicable).

The workflow does not introduce a new per-subject record. Where a
producing playbook's evidence stream carries personal data (case
records from `incident_management`, IAM audit records from IAM-side
producing playbooks, on-call roster entries from `on_call_rotation`),
the per-subject record stays on that producing playbook's evidence
store and only the aggregated per-section bucket plus the
attribution metadata cross into the roll-up.

## 4. Recipients

Internal recipients:

- The **operator's evidence store** — primary recipient of the
  dated DORA Chapter II ICT risk management self-assessment
  attestation record at the report step. The store owns durable
  retention, integrity hashing, and downstream serve-to-reviewer
  access; the roll-up does not.
- The **operator's governance function** owning the four-bucket
  coverage rubric, the per-section freshness-threshold policy, and
  the declared-exception register. This function reads the
  attestation record for internal control-effectiveness review
  and updates the rubric / thresholds as the operator's posture
  evolves.
- The **operator's accountability owner** for DORA supervisory
  interactions (typically the management body designated under DORA
  Art. 5 or a documented alternative accountability surface). This
  owner reads the attestation record for supervisory readiness and
  is the routing surface for a competent-authority request against
  the whole Chapter II ICT risk management surface.
- The **operator's audit-trail store** — recipient of the
  invocation record, the assessment-window identifier, and the
  attestation-signatory reference per run.

External / processor recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **competent authority** under DORA Chapter VII where the
  operator's discharge of the Art. 6(5) annual-review obligation
  requires the attestation to be surfaced (on request under the
  competent-authority supervisory framework, or on the schedule the
  operator's national implementation pins). The workflow does not
  itself submit to the competent authority; the operator's outbound
  submission surface reads the attestation from the evidence store
  and forwards it under the sector-specific submission chain.

Each operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production;
the framework does not ship the DPAs, but the data-flow record names
the dependency so a sovereignty review can verify it. Where the
roll-up reads from a lower-layer producing playbook that already has
its own processor relationships (the `incident_management` case
store, the `alert_triage` telemetry store), those DPAs are inherited
from the producing playbook's data-flow record rather than
re-asserted here.

## 5. Retention

The workflow's durable artefacts are the **per-section coverage
scoring set** (`__section_scoring__`), the **evidence-to-section
mapping** (`__section_mapping__`), and the **dated attestation
record** (`__attestation_id__`). Retention is the operator's
governance-record window:

- **Dated attestation records** are retained for the operator's
  statutory DORA record-keeping period — typically the longest of
  (a) the competent authority's sector-specific record-keeping
  period under DORA Chapter II / Chapter VII, (b) the operator's
  board-records retention policy, and (c) the operator's
  litigation-hold policy. The operator configures the binding; the
  framework does not pick a default.
- **Per-section coverage scoring sets and evidence-to-section
  mappings** are retained alongside the attestation record they
  feed into; they age under the same window because the
  attestation's reproducibility depends on the input scoring and
  mapping being available.
- **Audit-trail entries** identifying the assessment-window
  reference and the attestation signatory are retained under the
  audit-trail store's policy; they are the evidence the operator
  presents to demonstrate which self-assessment cadence drove
  which attestation.
- **Lower-layer evidence records** (per-playbook evidence-stream
  entries) are NOT retained by the roll-up; they age under their
  own data-flow records on the producing playbooks that own them.

The retention boundary is enforced by the evidence store's
lifecycle hook plus the audit-trail store's policy; the workflow
itself is stateless beyond the per-run artefacts.

## 6. Cross-border transfers

**No transfer** is the default scoring. The workflow is designed
to execute end-to-end on the operator's sovereign-hosted runtime
(one of the EU-hostable reference targets — n8n self-host, Temporal
self-host, or LangGraph self-host on an EU-resident sovereign
provider) with an EU-resident evidence store, EU-resident
producing-playbook stores, and an EU-resident attestation sink.

The technical controls that hold this scoring:

- The reference compile targets are framework-agnostic and run on
  the operator's own sovereign-hosted runtime; no SecOps-NG-hosted
  egress path exists in the workflow.
- The evidence store is operator-supplied; the framework ships no
  default endpoint and no fallback that could route an evidence
  read outside the EU.
- The per-section mapping and scoring steps read from
  operator-supplied rubric and threshold policy artefacts and
  execute locally; no external aggregation or classifier service
  is invoked.
- The attestation-emission step composes the JSON-native record
  locally under a content-addressed filename derived from
  `SHA-256(workflow_id|execution_id|captured_at)`; the durable
  emitter wiring (artifact-path, atomic write, notification to
  the operator's accountability owner) hands off to the operator's
  evidence store endpoint, which is operator-supplied.
- The competent-authority submission surface is out of scope for
  the workflow — the roll-up writes to the evidence store; the
  operator's outbound submission chain reads from the store and
  is separately scored on its own data-flow record.

If an operator binds a non-EU evidence store, a non-EU rubric or
threshold registry, a non-EU scoring or classifier service on the
per-section mapping, or any external AI classifier on the unbound-
evidence flagging, this scoring breaks — the operator MUST re-score
this section under "transfer under SCCs / BCRs / derogation" and
document the supplementary measures (encryption-at-rest with
operator-held keys, pseudonymisation of any subject identifiers
carried in producing-playbook attribution before egress) before the
binding goes live. Sovereignty review at compile time is the gate.

## 7. Data subject rights

- **Access (Art. 15).** A subject who exercises a SAR against the
  operator can be answered by querying the lower-layer producing
  playbooks the roll-up reads from (the case stores on
  `incident_management` / `alert_triage`, the on-call roster
  entries on `on_call_rotation`, the supplier records on
  `supply_chain_security`). The attestation record is aggregated
  and does not carry per-subject identifiers beyond the
  accountability signatory and the declared-exception author; the
  SAR is answered against the producing playbooks' data-flow
  records rather than against the attestation artifact. The
  audit-trail entry identifying the attestation signatory is
  searchable on that signatory's identifier.
- **Rectification (Art. 16).** Applicable where the attestation
  signatory attribution, the declared-exception author reference,
  or the producing-playbook attribution is recorded incorrectly.
  Rectification flows through the operator's evidence store and
  the audit-trail store; the workflow inherits the corrected
  record on the next self-assessment run. Per-subject rectification
  against the lower-layer producing playbooks is handled by those
  workflows' rectification paths.
- **Erasure (Art. 17).** The retention hook in §5 is the
  operational erasure pathway: attestation records and the
  per-section scoring sets age into the operator's governance-record
  window and are purged on TTL. A standalone subject-initiated
  erasure request against the roll-up is generally not
  operationally meaningful — the artifacts are aggregated and
  carry no per-subject identifier beyond the signatory /
  declared-exception author references — and per-subject erasure
  flows through the lower-layer producing playbooks' erasure
  paths. Erasure against the attestation signatory or the
  declared-exception author attribution is constrained by the
  regulatory record-keeping obligation in §2; the operator's DPO
  is the gate.
- **Objection (Art. 21).** Where the lawful basis is
  **Art. 6(1)(c) legal obligation** (the primary basis in §2),
  Art. 21 does not apply to the supervisory-evidence portion of
  the processing. For the secondary **Art. 6(1)(f)** basis
  covering the internal governance portion of the roll-up, a data
  subject can object on grounds relating to their particular
  situation; the operational handling is to route the objection
  through the operator's DPO, with the overriding-legitimate-
  interest assessment as the gate. Because the attestation output
  is aggregated the practical effect of an objection is on the
  lower-layer producing playbooks' contribution to the aggregate,
  not on the aggregate itself.
- **Automated decision-making (Art. 22).** The per-section coverage
  scoring is a deterministic aggregation step under an
  operator-supplied four-bucket rubric and per-section freshness
  threshold; the whole-Chapter roll-up verdict is a deterministic
  composition over the five section buckets. The workflow as
  shipped does not produce a legal or similarly significant
  effect on a data subject in its own right, so Art. 22 does not
  apply. If an operator binds a scoring policy whose output
  triggers an automated adverse action against a subject named in
  the lower-layer producing playbooks (automated performance-
  management consequence on an evidence-record author, automated
  supervisory-facing attribution of an uncovered-section finding
  to a named individual), the operator MUST re-score this section.
