# GDPR data flow — data_protection_impact_assessment

Per-workflow GDPR data-flow entry for the
`data_protection_impact_assessment` cookbook playbook
(`playbook.data_protection_impact_assessment@v1`). Filled in
against [`_data-flow-template.md`](./_data-flow-template.md).
Together the seven sections below form the Art. 30 Record of
Processing Activity entry for this workflow, and §8 documents the
outbound personal-data transfer legs under GDPR Chapter V
(Art. 44–49) for any supervisory-authority pre-consultation
submission the lifecycle emits.

Workflow source of truth:
[`content/playbooks/data_protection_impact_assessment/`](../../playbooks/data_protection_impact_assessment/).

Status: SKELETON. The processing-inventory adapter, the risk-
taxonomy binding, the DPO-consultation intake, the DPIA-document
template, and the supervisory-authority pre-consultation
submission chain are declared as adapter-bound surfaces the
operator wires; the ROPA entry below scopes the personal-data
surface that is stable across those adapters (the assessed-
processing description, the risk assessment, the mitigations,
the DPO advice, and the durable DPIA-document artifact). A
sibling CORE card revisits this doc once the adapter surfaces
land.

---

## 1. Purpose

The workflow exists to operate the controller-side ex-ante data
protection impact assessment lifecycle GDPR Article 35 mandates
before processing likely to result in a high risk to the rights
and freedoms of natural persons may begin: screen the envisaged
processing against the Article 35(3)(a-c) mandatory-DPIA
triggers, the supervisory-authority Article 35(4) list, and the
general Article 35(1) high-risk test; where the screen fires,
assemble the Article 35(7)(a) systematic description, assess
necessity and proportionality under Article 35(7)(b), assess the
risks to the rights and freedoms of data subjects under Article
35(7)(c), identify and document the mitigations under Article
35(7)(d), seek the Data Protection Officer's advice under Article
35(2), determine whether the residual risk triggers Article 36(1)
prior consultation with the supervisory authority, produce the
durable DPIA-document artifact, and schedule the Article 35(11)
review hook against the operator's change-management surface. The
purpose is bounded to that screen-to-review chain and the per-
case correlation record that joins the milestones into a single
accountability-ledger record keyed on `__dpia_case_id__`. The
workflow does not itself operate the processing under
assessment — it assesses it — and does not perform incident
classification against NIS2 Art. 23 or GDPR Art. 33.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(c) — legal obligation**. The processing
is necessary for compliance with the controller's statutory duty
under GDPR Article 35 to carry out a data protection impact
assessment prior to processing that is likely to result in a high
risk. The lawful basis for processing the personal data the DPIA
lifecycle handles internally (the assessment-scope reference to
the processing envelope, the DPO consultation record, and the
Article 36 gate determination) is the Article 35 obligation
itself.

Secondary: **GDPR Art. 6(1)(f) — legitimate interests** applies
to the third-party processors involved in the assessment chain
when the operator binds them — the case-management / evidence-
pack store that carries the correlation record across the
lifecycle, the DPO-consultation intake surface, and the outbound
submission surface that emits any supervisory-authority pre-
consultation payload under Article 36(1). The operator has a
legitimate interest in operating a deterministic assessment
chain that discharges the Article 35 obligation and produces the
durable receipts the Article 5(2) accountability posture depends
on.

Special-category data (Art. 9) is only incidentally implicated:
the DPIA lifecycle assesses processing that may itself operate
on Art. 9 data, but the DPIA lifecycle's own inputs are the
processing-inventory reference, the risk determination, the
mitigations catalogue, and the DPO advice — none of which are
themselves Art. 9 personal data. Where the assessed processing
carries Art. 9 categories, the Article 35(3)(b) mandatory-DPIA
trigger fires at screen_dpia_triggers and the assessment records
the Art. 9 categories on the description artifact without the
lifecycle itself becoming an Art. 9 processing operation.

## 3. Categories of data subjects and personal data

Categories of data subjects whose data flows through the
workflow:

- **Data subjects of the assessed processing**, named only by
  reference: the DPIA document records the categories of
  subjects the assessed processing operates on (per Article
  35(7)(a)) but the assessment lifecycle itself does not read
  the subjects' personal data — it reads the description of the
  processing that reads their data. The join key is the
  processing-inventory identifier, not per-subject records.
- **The controller's designated Data Protection Officer** (where
  Article 37 requires designation): the DPO consultation record
  carries the DPO's identity and the advice they returned on the
  assessment.
- **Supervisory-authority contact points** (where the Article
  36(1) prior-consultation gate fires): the outbound submission
  carries the operator's declared point-of-contact identifiers
  the supervisory authority reads to route the consultation.

Categories of personal data the workflow processes:

- **Processing-inventory reference** — the Article 30 RoPA
  identifier that resolves the assessed processing envelope. Not
  itself personal data, but the join key against personal-data
  processing operations.
- **DPO consultation record** — the DPO's advice on the
  assessment, tagged to `__dpia_case_id__` and stored on the
  operator's evidence-store surface.
- **Supervisory-authority correspondence** (where the Article 36
  gate fires) — the outbound submission and any inbound
  supervisory-authority response, retained on the accountability
  ledger as part of the DPIA document.

## 4. Recipients

Internal recipients:

- **The controller's designated Data Protection Officer** — reads
  the assembled description, necessity-and-proportionality
  assessment, risk assessment, and mitigations documentation and
  writes the Article 35(2) advice record on the case.
- **The operator's evidence-store surface** — persists the DPIA
  document artifact and the per-case correlation record as the
  operator's Article 5(2) accountability posture.
- **The operator's change-management surface** — receives the
  Article 35(11) review-cadence hook `schedule_review_cadence`
  pins.

External recipients (only where the Article 36(1) gate fires):

- **The supervisory authority** — receives the pre-consultation
  submission and returns any Article 36(2) response. Wired
  against the operator's declared supervisory-authority-of-
  competence surface under Article 55. A Data Processing
  Agreement is not required for the supervisory-authority
  transfer leg (it is a controller-to-authority obligation
  transfer, not a processor engagement).

No other external recipients. The DPIA lifecycle does not
share the assessment with peer operators, threat-intel
communities, or downstream processors.

## 5. Retention

The DPIA document artifact and the per-case correlation record
are retained for the lifetime of the assessed processing plus
the operator's declared post-decommission accountability window
(minimum: the local statute-of-limitations horizon on any GDPR
claim that could be brought against the assessed processing).
Article 35(11) requires the controller to keep the assessment
under review; the review-cadence duration
`__review_cadence__` sets the maximum interval between reviews
absent a material change to the processing envelope, and each
review either re-validates the existing document or replaces it
with an updated one. Neither the DPO consultation record nor
the supervisory-authority correspondence has a shorter retention
than the parent DPIA case.

The retention is enforced by the evidence-store surface's
retention-policy binding, which reads the per-case decommission
signal from the operator's processing-inventory adapter (when
the assessed processing is retired, the DPIA case is transitioned
to `historical` and the post-decommission accountability window
begins). No time-to-live is set on the case while the assessed
processing is live.

## 6. Cross-border transfers

Default posture: **no transfer**. The DPIA lifecycle is a
controller-internal assessment process that runs entirely on
the operator's declared substrate. The processing-inventory
adapter, the evidence-store surface, the DPO-consultation
intake, and the change-management adapter are all EU-resident
where the SecOps-NG sovereignty-first foundation is honoured
(see [`docs/FOUNDATION.md`](../../../docs/FOUNDATION.md)). The
technical control holding the posture is the operator's
sovereign-hosted substrate binding: the same binding that keeps
the sibling data_subject_rights and incident_management
lifecycles EU-resident keeps this lifecycle EU-resident.

The one leg that may cross an operator-external boundary is the
supervisory-authority pre-consultation submission (§4 external
recipient above). The supervisory authority is an EU/EEA member-
state authority by definition of Article 55; the transfer stays
within the EU/EEA and does not invoke Chapter V. Where the
operator's competent supervisory authority is in a different
member state from the controller's establishment, the transfer
is EU-to-EU and no adequacy / SCCs / derogation instrument is
required.

No third-country transfer legs on the default posture. If the
operator swaps an EU-resident evidence-store surface for a US-
hosted one, the swap is flagged here explicitly and re-scored
under §8 before the binding is wired in production.

## 7. Data subject rights

The DPIA lifecycle does not itself hold personal data of the
data subjects whose processing is under assessment; those
subjects' rights (Articles 15-22) are exercised against the
assessed processing, not against the DPIA document. The DPO,
whose consultation record is stored on the case, is a natural
person whose subject rights the operator honours through the
DPO's employment relationship with the controller (Article 37-
39 protect the DPO's independence; personal data about the DPO
held on the case is limited to identifier and advice).

Per canonical section:

- **Access (Art. 15)** — a data subject asking to see how the
  controller assesses the processing that touches them is
  answered by disclosing the DPIA document (or an
  appropriately-redacted extract where the document contains
  another subject's or another party's protected content) via
  the operator's DSR intake surface (the sibling
  `data_subject_rights` playbook is the operator-side
  lifecycle).
- **Rectification (Art. 16)** — applicable if the DPO's
  consultation record or the operator-side identifier fields
  are wrong; corrections are applied on the case and the
  correction attestation flows back through the DSR lifecycle.
- **Erasure (Art. 17)** — the retention hook in §5 is the
  answer: the DPIA case is retained for the accountability
  window; erasure requests against the case are subject to the
  Article 17(3)(b)/(e) exemptions for legal-obligation
  compliance and defence of legal claims, which the DPIA
  document itself is evidence of.
- **Objection (Art. 21)** — not applicable to the DPIA
  lifecycle itself (its lawful basis is Art. 6(1)(c), against
  which Article 21 does not run). Objections raised against
  the assessed processing are exercised against that
  processing's controller-side lifecycle, not against the DPIA.
- **Automated decision-making (Art. 22)** — the DPIA lifecycle
  does not itself make automated decisions producing legal or
  similarly significant effects on data subjects. The
  determine_article_36_gate step's boolean output is a
  controller-side decision about the assessed processing's
  regulatory posture, not a decision about a data subject.

## 8. Outbound personal-data transfer

The DPIA lifecycle has one outbound personal-data transfer leg:
the **supervisory-authority pre-consultation submission** the
determine_article_36_gate step triggers where the residual risk
meets the Article 36(1) threshold.

- **Destination class.** Regulator — the supervisory authority
  of competence under Article 55 for the controller's
  establishment. The submission carries the DPIA document (or
  the operator's declared prior-consultation packaging of it),
  the DPO advice under Article 35(2), and the operator's point-
  of-contact identifiers.
- **Transfer mechanism.** **no transfer** — the destination is
  EU/EEA-resident by definition of Article 55. Where the
  supervisory authority is in a different EU/EEA member state
  from the controller's establishment (for example a lead-
  supervisory-authority arrangement under the one-stop-shop
  mechanism of Article 56), the transfer stays intra-EU and no
  Chapter V instrument applies. The technical control holding
  the posture is the operator's supervisory-authority
  submission-surface binding to a regulator-operated portal
  (or, in the interim before every DPA operates one, an
  EU-resident secure-delivery channel the operator's DPO has
  vetted with the DPA).
- **EU-residency posture (Directive 1 — sovereignty-first).**
  The default posture the framework ships is EU-resident
  destinations only, sovereign-hosted runtime, no public-cloud-
  AI egress on the outbound leg. The submission-surface binding
  is the compile-time knob a CORE card lands; an operator
  swapping the sovereign-submission binding for a non-EU
  processor would break the `no transfer` scoring and require
  re-scoring under Article 46 / Article 49 — the DPIA lifecycle
  refuses such a swap by default because the destination class
  (a supervisory authority) does not admit a non-EU transfer
  instrument.
- **Data minimisation on egress (Art. 5(1)(c)).** The outbound
  payload carries the assembled DPIA document, the DPO advice,
  the residual-risk profile, and the operator's point-of-
  contact identifiers. It does not carry per-subject records of
  the data subjects whose processing is under assessment
  (Article 36(1) authorises the supervisory authority to seek
  further information under Article 58(1)(a) if needed;
  volunteering per-subject records ahead of that request is
  not required and would violate the data-minimisation
  principle on the outbound leg).

Cross-reference §6 — that section scores the DPIA lifecycle's
processing as a whole as `no transfer` on the default posture;
this section enumerates the single outbound leg (the
supervisory-authority submission) and confirms it stays
intra-EU/EEA under Article 55/56. The two scorings are
consistent by construction: no third-country transfer instrument
applies to a supervisory-authority destination class.
