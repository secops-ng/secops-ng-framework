# GDPR data flow — dora_tlpt_programme

Per-workflow GDPR data-flow entry for the `dora_tlpt_programme`
playbook (`playbook.dora_tlpt_programme@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/dora_tlpt_programme/`](../../playbooks/dora_tlpt_programme/).

---

## 1. Purpose

The workflow exists to discharge the operator-side DORA Chapter IV
digital operational resilience testing programme — Article 24
(general requirements for the testing of digital operational
resilience: identify the critical or important functions, supporting
ICT assets, and third-party dependencies in scope for the testing
programme) and Article 26 (advanced testing based on threat-led
penetration testing: mandatory-TLPT decision against the ESAs Joint
Committee identification criteria, competent-authority notification,
red-team scoping approval, findings register, dated
competent-authority remediation attestation). It composes a DORT
scope catalogue for the current testing window, evaluates the
TLPT-mandatory trigger and opens the planning gate, packages the
red-team scoping submission for competent-authority approval, and
emits the dated remediation attestation to the operator's evidence
store on the mandatory-TLPT cycle. The purpose is bounded to that
testing-programme lifecycle discipline; the workflow does not
itself dispatch the red-team engagement, does not itself judge the
operator's tier-of-significance, and does not own the outbound
submission channel to the competent authority beyond the notification
and scoping-approval adapters.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(c) — legal obligation**. The processing is
necessary for compliance with the operator's DORA Chapter IV testing
obligations — **DORA Art. 24** (sound and comprehensive digital
operational resilience testing programme as an integral part of the
ICT risk-management framework) and **DORA Art. 26** (mandatory
threat-led penetration testing for financial entities identified
under the ESAs Joint Committee guidelines on TLPT identification (JC
2022 03), with competent-authority notification, scoping approval,
and dated remediation attestation). Competent authorities exercise
their tasks under DORA Chapter VII against the whole Chapter IV
testing-programme surface, and the dated remediation attestation is
the evidence the operator presents to demonstrate the obligation
has been discharged on the prescribed cadence.

Secondary: **GDPR Art. 6(1)(f) — legitimate interests** applies to
the internal governance portion of the workflow that is not strictly
mandated by the supervisory template — the operator's own
programme-level scope-catalogue composition beyond the Art. 24
minimum, the internal declared-severity-rubric binding on the
findings register, and the audit-trail attribution on the dated
attestation record. The operator has a legitimate interest in
maintaining a coherent view of its Chapter IV testing posture for
its governance bodies and its competent-authority interactions.

Special-category data (Art. 9) is not the target of the workflow
and is not expected to be incidentally observed — the workflow
operates on scope-catalogue identifiers, trigger-decision records,
scoping-submission identifiers, findings-register identifiers, and
attestation-record identifiers, not on per-subject telemetry. If an
in-scope critical or important function processes special-category
data, the red-team engagement outputs may incidentally carry that
data on the producing surface; that discharge is on the in-scope
function's own playbook (and its own data-flow record), not on this
testing-programme lifecycle.

## 3. Categories of data subjects and personal data

The workflow's inputs and outputs are heavily aggregated — the
intent of the testing programme is the whole-Chapter IV attestation,
not per-subject reporting. The categories below cover the residual
personal data that can flow through the lifecycle despite the
aggregation:

Data subjects:

- **Employees of the operator** named as accountability owners on
  the ICT-supported critical or important functions the scope
  catalogue enumerates, as authors of the declared severity rubric
  the findings register scores against, or as accountability
  signatories on the dated remediation attestation record. Their
  identifier appears in the audit trail of the catalogue reference,
  the rubric reference, and the attestation artifact as
  accountability metadata.
- **Employees of the operator** whose operational contribution feeds
  the lower-layer registers the scope-catalogue-composition step
  reads against (business-service register owners on the Art. 8
  identification surface, ICT-asset register owners, ICT third-party
  register owners). The subject's identifier stays on the lower-layer
  register; only the aggregated scope-catalogue reference and the
  function-to-asset-to-provider join cross into the testing
  programme.
- **Testers** on the red-team engagement (internal or external
  under the JC RTS Art. 27 certification, independence, and
  professional-indemnity-insurance criteria). Their identifier
  appears on the red-team scoping submission as the operator's
  declared engagement roster and on the findings register as the
  authoring identifier per finding.

Categories of personal data:

- **Scope-catalogue identifiers** — the identifiers of the ICT-
  supported critical or important functions in scope, the supporting
  ICT assets, and the ICT third-party service providers. These carry
  no per-subject identifier by themselves; where a function
  identifier resolves back to a subject-processing surface, the
  personal-data status is inherited from that lower-layer surface's
  data-flow record.
- **Accountability-owner attribution metadata** — the owner
  identifier per critical or important function, the rubric
  author, the attestation signatory. Personal identifiers here are
  limited to the operator's named accountability roster.
- **Findings-register per-finding attribution** — for each red-team
  finding, the authoring tester's identifier, the affected function
  identifier, the affected ICT-asset identifier, and the evidence
  pointer into the operator's evidence store. Where the underlying
  evidence carries per-subject payload from the in-scope function's
  processing surface, the personal-data status is inherited from
  that surface (a red-team finding against an
  `incident_management`-owned function points at that surface's
  data-flow record).
- **Competent-authority correspondence metadata** — the notification
  reference and the scoping-approval outcome. These carry
  submission-side identifiers (the operator's regulatory contact,
  the competent-authority acknowledgement reference) but no
  data-subject payload.
- **Audit-trail metadata** — invocation identifier, testing-window
  identifier, attestation timestamp, attestation-signatory reference.
  Personal identifiers in this metadata are limited to the
  accountability signatory and the run operator (where applicable).

The workflow does not introduce a new per-subject record. Where an
in-scope critical or important function's producing playbook carries
personal data (case records from `incident_management`, IAM audit
records from IAM-side producing playbooks), the per-subject record
stays on that producing playbook's evidence store and only the
aggregated finding metadata plus the evidence pointer cross into the
findings register.

## 4. Recipients

Internal recipients:

- The **operator's evidence store** — primary recipient of the
  dated competent-authority remediation attestation record at the
  remediation-tracking step. The store owns durable retention,
  integrity hashing, and downstream serve-to-reviewer access; the
  testing programme does not.
- The **operator's governance function** owning the declared
  severity rubric and the DORT scope catalogue. This function reads
  the attestation record for internal control-effectiveness review
  and updates the rubric / scope catalogue as the operator's posture
  evolves.
- The **operator's accountability owner** for DORA supervisory
  interactions (typically the management body designated under DORA
  Art. 5 or a documented alternative accountability surface). This
  owner reads the trigger-decision record, the scoping-submission
  record, and the remediation attestation for supervisory readiness
  and is the routing surface for competent-authority engagement on
  the Chapter IV testing programme.
- The **operator's audit-trail store** — recipient of the invocation
  record, the testing-window identifier, and the attestation-
  signatory reference per run.

External / processor recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **competent authority** under DORA Chapter VII, receiving:
  (a) the Art. 26(1) TLPT notification at the trigger-and-planning
  gate, (b) the Art. 26(3) red-team scoping submission for approval
  at the scoping-approval step, and (c) the Art. 26(8) dated
  remediation attestation on the closure lane. The workflow submits
  through the operator's declared competent-authority adapter
  binding (landed on the sibling EXTEND card under
  `patterns.dora_tlpt_programme`); the operator's outbound
  submission chain owns transport hardening and per-authority
  routing.
- The **external red-team provider** where the operator's declared
  tester posture is external under DORA Art. 27 (certification,
  independence, professional-indemnity-insurance criteria). The
  scoping submission carries the operator's declared rules of
  engagement and the DORT scope catalogue; the provider dispatches
  the engagement outside the playbook and returns the findings
  register through the operator's declared secure-return channel.
- The **operator's threat-intelligence source** where the declared
  source is external (per Art. 26(2) the threat-intelligence must
  reflect the operator's threat landscape). The binding lands in
  the sibling EXTEND card; the workflow references the source
  identifier without reading subject-processing payload.

Each operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production;
the framework does not ship the DPAs, but the data-flow record names
the dependency so a sovereignty review can verify it. The
competent-authority relationship is regulatory rather than a
processor relationship, but the operator's outbound submission
adapter is scored for transfer characteristics in §6.

## 5. Retention

The workflow's durable artefacts are the **DORT scope catalogue**
(`__dort_scope_catalogue__`), the **TLPT trigger decision**
(`__tlpt_trigger_decision__`), the **red-team scoping submission
record** (`__red_team_scoping_id__`), the **findings register**
(`__findings_register_id__`), and the **dated remediation
attestation** (`__remediation_attestation_id__`). Retention is the
operator's governance-record window:

- **Dated remediation attestation records** are retained for the
  operator's statutory DORA record-keeping period — typically the
  longest of (a) the competent authority's sector-specific
  record-keeping period under DORA Chapter IV / Chapter VII, (b) the
  operator's board-records retention policy, and (c) the operator's
  litigation-hold policy. The operator configures the binding; the
  framework does not pick a default.
- **Findings registers, scoping submissions, and trigger decisions**
  are retained alongside the attestation record they feed into;
  they age under the same window because the attestation's
  reproducibility depends on the input scoping-and-findings chain
  being available.
- **DORT scope catalogues** are retained for the testing-programme
  cycle (per Art. 26(1) at least every three years unless the
  competent authority prescribes otherwise) plus the operator's
  record-keeping period beyond the last catalogue that discharged
  a mandatory TLPT.
- **Audit-trail entries** identifying the testing-window reference
  and the attestation signatory are retained under the audit-trail
  store's policy.
- **Lower-layer records** (per-function evidence entries from
  in-scope playbooks) are NOT retained by the testing programme;
  they age under their own data-flow records on the producing
  playbooks that own them.

The retention boundary is enforced by the evidence store's
lifecycle hook plus the audit-trail store's policy; the workflow
itself is stateless beyond the per-run artefacts.

## 6. Cross-border transfers

**No transfer** is the default scoring. The workflow is designed
to execute end-to-end on the operator's sovereign-hosted runtime
(one of the EU-hostable reference targets — n8n self-host, Temporal
self-host, or LangGraph self-host on an EU-resident sovereign
provider) with EU-resident business-service / ICT-asset / ICT
third-party registers, an EU-resident competent-authority
notification adapter reading to an EU authority, and an EU-resident
evidence store.

The technical controls that hold this scoring:

- The reference compile targets are framework-agnostic and run on
  the operator's own sovereign-hosted runtime; no SecOps-NG-hosted
  egress path exists in the workflow.
- The lower-layer registers (business-service, ICT-asset, ICT
  third-party) are operator-supplied; the framework ships no
  default endpoint and no fallback that could route a read outside
  the EU.
- The competent-authority notification and scoping-approval adapters
  target the operator's national competent authority under DORA
  Chapter VII — always an EU authority by the regime's construction.
- The evidence store is operator-supplied; the attestation-emission
  step composes the JSON-native record locally under a
  content-addressed filename derived from
  `SHA-256(workflow_id|execution_id|captured_at)` and hands off to
  the operator's evidence store endpoint.

If an operator binds a non-EU red-team provider on the external
tester posture (a US-domiciled TLPT vendor, for example), a non-EU
threat-intelligence source, or a non-EU evidence store, this scoring
breaks — the operator MUST re-score this section under "transfer
under SCCs / BCRs / derogation" and document the supplementary
measures (encryption-at-rest with operator-held keys of the findings
register, pseudonymisation of accountability-owner attribution
before egress, secure-return channel hardening on the external
provider relationship) before the binding goes live. Sovereignty
review at compile time is the gate; DORA Art. 27 tester-criteria
review is the parallel supervisory gate on the tester relationship
specifically.

## 7. Data subject rights

- **Access (Art. 15).** A subject who exercises a SAR against the
  operator can be answered against the accountability roster the
  workflow reads (owner-of-function attribution, rubric-author
  attribution, attestation-signatory attribution) plus the tester
  roster on the red-team engagement. Where the SAR reaches into the
  underlying in-scope function's per-subject processing surface,
  the SAR is answered against that surface's data-flow record
  rather than against the testing-programme artefacts. The
  audit-trail entry identifying the attestation signatory is
  searchable on that signatory's identifier.
- **Rectification (Art. 16).** Applicable where the accountability-
  owner attribution, the rubric-author reference, the tester-roster
  attribution, or the attestation-signatory attribution is recorded
  incorrectly. Rectification flows through the operator's evidence
  store and the audit-trail store; the workflow inherits the
  corrected record on the next testing-programme run.
- **Erasure (Art. 17).** The retention hook in §5 is the
  operational erasure pathway: attestation records, findings
  registers, scoping submissions, trigger decisions, and DORT
  scope catalogues age into the operator's governance-record
  window and are purged on TTL. A standalone subject-initiated
  erasure request against the testing programme is generally not
  operationally meaningful — the artefacts are aggregated and
  carry no per-subject identifier beyond the roster attributions —
  and per-subject erasure flows through the lower-layer producing
  playbooks' erasure paths. Erasure against the accountability-
  signatory or tester-roster attribution is constrained by the
  regulatory record-keeping obligation in §2; the operator's DPO
  is the gate.
- **Objection (Art. 21).** Where the lawful basis is **Art. 6(1)(c)
  legal obligation** (the primary basis in §2), Art. 21 does not
  apply to the supervisory-evidence portion of the processing. For
  the secondary **Art. 6(1)(f)** basis covering the internal
  governance portion of the testing programme, a data subject can
  object on grounds relating to their particular situation; the
  operational handling is to route the objection through the
  operator's DPO, with the overriding-legitimate-interest
  assessment as the gate.
- **Automated decision-making (Art. 22).** The TLPT-mandatory
  trigger evaluation is a deterministic rule-based check against
  the JC 2022 03 criteria and the operator's declared
  tier-of-significance; the red-team scoping approval-binding step
  records the competent-authority response deterministically; the
  remediation-status roll-up is a deterministic aggregation over
  per-finding closure state under an operator-supplied severity
  rubric. The workflow as shipped does not produce a legal or
  similarly significant effect on a data subject in its own right,
  so Art. 22 does not apply. If an operator binds an automated
  policy whose output triggers an automated adverse action against
  a subject named in the accountability or tester roster (automated
  performance-management consequence on an evidence-record author,
  automated supervisory-facing attribution of an uncovered-finding
  to a named individual), the operator MUST re-score this section.
