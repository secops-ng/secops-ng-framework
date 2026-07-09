# GDPR data flow — nis2_art20_governance

Per-workflow GDPR data-flow entry for the `nis2_art20_governance`
playbook (`playbook.nis2_art20_governance@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/nis2_art20_governance/`](../../playbooks/nis2_art20_governance/).

---

## 1. Purpose

The workflow exists to discharge the NIS2 Directive (EU) 2022/2555
Article 20(1) management-body approval obligation on the operator's
documented governance cadence: convene the management-body
cybersecurity review cycle, present the current Article 21(2)(a)–(j)
risk-management posture and compliance status to the management
body, record the management approval of the cybersecurity
risk-management measures (with the Article 20(2) training-completion
attestation for management-body members carried on the approval
record), and emit the dated governance-record evidence artifact so
the auditable-lifecycle obligation is closed on every cycle. The
purpose is bounded to the four-step management-body approval-cycle
discharge and the dated governance-record it produces; the workflow
does not itself implement any of the Article 21(2) risk-management
measures (those are owned by the per-clause playbooks the roll-up
under `playbook.nis2_self_assessment@v1` enumerates), does not
mutate any operational control surface, and does not own the
distribution channel to a supervisory authority.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(c) — legal obligation**. The processing is
necessary for compliance with the operator's cybersecurity
governance obligations under **NIS2 Art. 20(1)** (management-body
approval of the cybersecurity risk-management measures adopted to
comply with Article 21, oversight of their implementation, and
liability for infringements) and **NIS2 Art. 20(2)** (cybersecurity
training for members of the management body). Supervisory
authorities exercise their tasks under NIS2 Chapter VII (Art. 32
for essential entities, Art. 33 for important entities) against the
management-body approval discipline; the dated governance-record is
the evidence the operator presents to demonstrate the obligation has
been discharged on the documented cadence.

Secondary: **GDPR Art. 6(1)(f) — legitimate interests** applies to
the internal governance portion of the workflow that is not strictly
mandated by the supervisory template — the operator's own composition
of the per-cycle posture snapshot beyond the enumerated Article
21(2)(a)–(j) buckets, the audit-trail attribution on the approval
record, and the internal referral-condition register. The operator
has a legitimate interest in maintaining a coherent view of its
management-body approval posture for its governance bodies and its
supervisory-authority interactions.

Special-category data (Art. 9) is not the target of the workflow
and is not expected to be incidentally observed — the workflow
operates on the management-body member roster, aggregated per-clause
coverage buckets, and governance-decision records; no health,
biometric, or other Art. 9 categories are processed. If an
operator's governance-cadence catalogue or training-completion
register carries an Art. 9 attribute (medical accommodation on a
member's training-completion record, for example), the operator
MUST re-score this section before the binding is pinned.

## 3. Categories of data subjects and personal data

The workflow's inputs and outputs are dominated by the
management-body member roster and aggregated per-clause coverage
buckets. The categories below cover the personal data that flows
through the approval cycle:

Data subjects:

- **Members of the management body** of the essential or important
  entity — named as the approvers (or referrers) on the
  approval-record artifact and as the attestation subjects on the
  Article 20(2) training-completion attestation carried on the same
  record. Their identifier appears on the governance-decision record
  and on the training-completion register.
- **Employees of the operator** named as the authors of the
  governance-cadence catalogue, the per-cycle posture-snapshot
  composition, and the referral-condition register. Their identifier
  appears in the audit trail of the schedule, present, and approve
  steps.
- **Employees of the operator** named as producing-playbook owners
  or as evidence-record authors whose contribution feeds the
  per-cycle posture snapshot the present step composes over. Those
  identifiers stay on the lower-layer evidence records the
  `nis2_self_assessment` roll-up reads from; only the aggregated
  per-clause buckets cross into the posture snapshot this workflow
  presents to the management body.

Categories of personal data:

- **Management-body member identifiers** — the member's name and
  the reference to their seat on the management-body forum. Carried
  on the approval record as the accountability metadata Article
  20(1) names and on the training-completion attestation as the
  Article 20(2) subject.
- **Training-completion attestation attributes** — which
  management-body members completed the declared training and when.
  Carried on the approval-record artifact as the Article 20(2)
  discharge metadata; no training content or per-question response
  is carried in the record itself, only the completion attestation.
- **Governance-decision metadata** — the approval or referral
  outcome, the referral conditions where applicable, the meeting
  reference, the agenda-slot reference, and the approving-body
  reference. Personal identifiers in this metadata are limited to
  the approving members' names and the meeting scribe (where the
  operator's governance policy records one).
- **Aggregated per-clause coverage buckets** — the four scoring
  buckets applied to each of the ten Article 21(2)(a)–(j) sub-clause
  atoms. These carry no per-subject identifier; the personal-data
  status is inherited from the lower-layer producing playbooks the
  `nis2_self_assessment` roll-up reads from.
- **Audit-trail metadata** — governance-cycle identifier, review
  identifier, posture-snapshot identifier, approval-record
  identifier, evidence identifier, and the captured_at timestamp on
  the governance-record artifact. Personal identifiers in this
  metadata are limited to the invoking operator (where applicable)
  and the approving members carried through from the approval
  record.

The workflow does not introduce a new per-subject record beyond
what the operator's governance documentation already maintains for
its management body; the management-body member roster and the
training-completion register are pre-existing operator artefacts
whose ROPA is authored upstream. This data-flow document records
the workflow's read/compose relationship against those artefacts,
not a new collection surface.

## 4. Recipients

Internal recipients:

- The **operator's evidence store** — primary recipient of the
  dated governance-record evidence artifact at the log step. The
  store owns durable retention, integrity hashing, and downstream
  serve-to-reviewer access; the approval cycle does not.
- The **operator's management body** — the recipient of the
  per-cycle posture snapshot at the present step. Access is bounded
  to the forum session and the members entitled to the meeting
  material under the operator's governance policy.
- The **operator's governance function** owning the
  governance-cadence catalogue, the management-body member roster,
  and the referral-condition register. This function reads the
  approval-record artifact for internal control-effectiveness review
  and updates the catalogue / roster as the operator's posture
  evolves.
- The **operator's accountability owner** for NIS2 supervisory
  interactions (typically the Chief Information Security Officer or
  a documented alternative accountability surface). This owner reads
  the governance-record artifact for supervisory readiness and is
  the routing surface for a supervisory-authority Article 32 /
  Article 33 request against the management-body approval discipline.
- The **operator's audit-trail store** — recipient of the
  governance-cycle identifier, review identifier, and approval-record
  reference per run.

External / processor recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **supervisory authority** under NIS2 Chapter VII where the
  operator's discharge of the management-body approval obligation
  requires the governance-record to be surfaced (on request under
  Art. 32(2) or Art. 33(2), or on the schedule the operator's
  national transposition pins). The workflow does not itself submit
  to the supervisory authority; the operator's outbound submission
  surface reads the governance-record from the evidence store and
  forwards it under the transposition-specific submission chain.
  This is an outbound leg scored in §8.

Each operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production;
the framework does not ship the DPAs, but the data-flow record
names the dependency so a sovereignty review can verify it. The
management-body member roster is not shared with any external
processor by this workflow.

## 5. Retention

The workflow's durable artefacts are the **per-cycle posture
snapshot** (`__posture_snapshot_id__`), the **approval record**
(`__approval_record_id__`, carrying the Article 20(2)
training-completion attestation), and the **dated governance-record
evidence artifact** (`__evidence_id__`). Retention is the operator's
governance-record window:

- **Dated governance-record evidence artifacts** are retained for
  the operator's statutory NIS2 record-keeping period — typically
  the longest of (a) the supervisory authority's
  transposition-specific record-keeping period under NIS2 Art. 20(1)
  / Chapter VII, (b) the operator's board-records retention policy
  (management-body approval records are board records), and (c) the
  operator's litigation-hold policy. The operator configures the
  binding; the framework does not pick a default.
- **Approval records and per-cycle posture snapshots** are retained
  alongside the governance-record they feed into; they age under the
  same window because the governance-record's reproducibility depends
  on the input snapshot and approval record being available.
- **Training-completion attestation attributes** carried on the
  approval record are retained for the same window as the approval
  record; the operator's separate management-body member roster and
  training-completion register (upstream of this workflow) apply
  their own retention policy — this workflow does not shorten or
  extend those policies.
- **Audit-trail entries** identifying the governance-cycle reference
  and the review reference are retained under the audit-trail
  store's policy; they are the evidence the operator presents to
  demonstrate which governance cadence drove which approval record.
- **Lower-layer evidence records** (per-playbook evidence-stream
  entries feeding the posture snapshot) are NOT retained by this
  workflow; they age under their own data-flow records on the
  producing playbooks that own them.

The retention boundary is enforced by the evidence store's lifecycle
hook plus the audit-trail store's policy; the workflow itself is
stateless beyond the per-run artefacts.

## 6. Cross-border transfers

**No transfer** is the default scoring. The workflow is designed
to execute end-to-end on the operator's sovereign-hosted runtime
(one of the EU-hostable reference targets — n8n self-host, Temporal
self-host, or LangGraph self-host on an EU-resident sovereign
provider such as Nebul, OVHcloud, Scaleway, or Hetzner) with an
EU-resident governance-cadence catalogue, an EU-resident evidence
store, an EU-resident management-body member roster, and an
EU-resident evidence sink.

The technical controls that hold this scoring:

- The reference compile targets are framework-agnostic and run on
  the operator's own sovereign-hosted runtime; no SecOps-NG-hosted
  egress path exists in the workflow.
- The governance-cadence catalogue, the management-body member
  roster, and the training-completion register are operator-supplied
  and read locally; the framework ships no default endpoint and no
  fallback that could route a read outside the EU.
- The posture-composition step reads from the operator-supplied
  evidence store and composes the per-cycle snapshot locally; no
  external aggregation, classifier, or AI-assist service is invoked.
- The governance-record emission step composes the JSON-native
  record locally under a content-addressed filename derived from
  `SHA-256(governance_cycle|review_id|captured_at)`; the durable
  emitter wiring hands off to the operator's evidence store endpoint,
  which is operator-supplied.
- The supervisory-authority submission surface is out of scope for
  the workflow — the approval cycle writes to the evidence store;
  the operator's outbound submission chain reads from the store and
  is separately scored on its own data-flow record.

If an operator binds a non-EU evidence store, a non-EU
governance-cadence catalogue, a non-EU management-body roster, or
any external AI classifier on the posture-composition step, this
scoring breaks — the operator MUST re-score this section under
"transfer under SCCs / BCRs / derogation" and document the
supplementary measures (encryption-at-rest with operator-held keys,
pseudonymisation of the management-body member identifiers carried
in the approval record before egress) before the binding goes live.
Sovereignty review at compile time is the gate.

## 7. Data subject rights

- **Access (Art. 15).** A management-body member exercising a SAR
  against the operator can be answered by querying the approval
  records their identifier appears on (as approver / referrer) and
  the training-completion attestations their identifier appears on
  (as attestation subject). The governance-record artifact is
  addressable by governance-cycle identifier and carries the
  approving members' identifiers; the audit-trail store is
  searchable on the member's identifier. Employees named as
  authors of the governance-cadence catalogue, the referral-condition
  register, or the posture-composition step exercise their SAR
  through the audit-trail store on the same lookup.
- **Rectification (Art. 16).** Applicable where the approving member
  attribution, the training-completion attestation, or the
  referral-condition author reference is recorded incorrectly.
  Rectification flows through the operator's evidence store and the
  audit-trail store; the workflow inherits the corrected record on
  the next governance-cycle run. Rectification against the
  management-body member roster or the training-completion register
  upstream of this workflow is handled by the operator's governance
  documentation, not by this workflow.
- **Erasure (Art. 17).** The retention hook in §5 is the operational
  erasure pathway: governance-record artifacts and approval records
  age into the operator's governance-record window and are purged on
  TTL. A standalone subject-initiated erasure request against
  management-body approval records is generally constrained by the
  regulatory record-keeping obligation in §2 (Article 20(1) names
  the auditable-lifecycle obligation for the approval discipline);
  the operator's DPO is the gate. Erasure of a training-completion
  attestation is similarly constrained where the operator's
  transposition binds the attestation to a statutory record-keeping
  window; where it does not, the attestation ages under the
  operator's governance-record TTL.
- **Objection (Art. 21).** Where the lawful basis is
  **Art. 6(1)(c) legal obligation** (the primary basis in §2),
  Art. 21 does not apply to the supervisory-evidence portion of the
  processing. For the secondary **Art. 6(1)(f)** basis covering the
  internal governance portion (the referral-condition register, the
  audit-trail attribution beyond the approving-member identifiers),
  a data subject can object on grounds relating to their particular
  situation; the operational handling is to route the objection
  through the operator's DPO, with the overriding-legitimate-interest
  assessment as the gate. Members of the management body cannot
  meaningfully object to the recording of their approval or referral
  decisions on the governance record itself — that recording is the
  Article 20(1) obligation.
- **Automated decision-making (Art. 22).** The approval / referral
  decision is a human governance-body decision made in the
  management-body forum; the workflow records the decision, it does
  not automate it. The per-cycle posture snapshot is a deterministic
  read-and-aggregate over the operator's evidence store under an
  operator-supplied rubric; no legal or similarly significant effect
  on a data subject is produced by the workflow in its own right,
  so Art. 22 does not apply. If an operator binds a scoring policy
  whose output triggers an automated adverse action against a
  management-body member or an evidence-record author (automated
  performance-management consequence on a member with an overdue
  training attestation, for example), the operator MUST re-score
  this section.
