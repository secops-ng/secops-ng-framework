# data_protection_impact_assessment

CACAO v2 SKELETON playbook operationalising the operator-side
**data protection impact assessment (DPIA) lifecycle** a controller
runs before deploying processing that is likely to result in a
high risk to the rights and freedoms of natural persons. GDPR
Article 35 mandates the assessment ahead of production wiring;
Article 36 gates supervisory-authority prior consultation on the
residual-risk threshold.

Distinct from the after-the-fact breach-notification lifecycle
(GDPR Articles 33-34, owned by the sibling `incident_management`
and `data_exfil` playbooks) and from the subject-initiated rights
lifecycle (GDPR Articles 15-22, owned by the sibling
`data_subject_rights` playbook): this is the proactive ex-ante
assessment lane that runs before the processing is bound to
production.

Status: **SKELETON**, with CORE-PRIM part 1 of 2 complete: the
first five action steps have deterministic primitives (see
*Primitives* below). The steps are not yet bound, so the compiled
targets still carry the scaffold. The DPO-consultation intake, the
supervisory-authority pre-consultation submission chain, and the
DPIA-document template arrive with part 2 and the wire.

## Contents

- `playbook.cacao.yaml` — the CACAO v2 artifact
  (`playbook.data_protection_impact_assessment@v1`), authored as
  YAML per the finalisation-marker convention (`.cacao.json` or
  `.cacao.yaml` both counted as finalised).
- `mappings.yaml` — outbound cross-references to the OSCAL
  controls, MITRE D3FEND techniques, OCSF event classes, and EU
  regulatory clauses this playbook operationalises. The SKELETON
  overlay pins the GDPR Article 35(1) / 35(3)(a) / 35(3)(b)
  anchors, the PM-9 / RA-3 / AU-9 OSCAL anchors called out in
  the task brief, and the D3-OAM D3FEND anchor on the
  identify_and_assess_risks step.
- `primitives/` — deterministic primitives, one per action step;
  the first five so far.

## Compile targets

`compile_targets` declares `[n8n, temporal, langgraph]`. Emitted
artifacts under `examples/{n8n,temporal,langgraph}/data_protection_impact_assessment/`
land in a follow-on CORE card once the risk-taxonomy binding,
the processing-inventory adapter, and the DPIA-document template
are populated.

## Step outline

1. **screen_dpia_triggers** — screen the processing envelope
   against the Article 35(3)(a-c) mandatory triggers, the
   operator's supervisory-authority Article 35(4) list, and the
   general Article 35(1) high-risk test. Sets `__dpia_case_id__`
   and `__dpia_required__`; records `__screening_result_ref__`.
2. **classify_processing_type** — resolve the processing shape
   against the Article 30 record of processing activities
   (RoPA) surface. Anchors the assessment scope.
3. **gather_processing_description** — assemble the Article
   35(7)(a) systematic description (purposes, categories,
   recipients, retention). Records
   `__processing_description_ref__`.
4. **assess_necessity_and_proportionality** — assess necessity
   and proportionality per Article 35(7)(b).
5. **identify_and_assess_risks** — apply the operator's risk
   taxonomy over the illegitimate-access, unauthorised-
   modification, and data-disappearance axes per Article
   35(7)(c). Records `__risk_assessment_ref__`.
6. **identify_and_document_mitigations** — document the
   safeguards, security measures, and mechanisms per Article
   35(7)(d). Records `__mitigations_ref__`.
7. **dpo_consultation** — seek DPO advice under Article 35(2).
   Records `__dpo_consultation_ref__`.
8. **determine_article_36_gate** — determine whether the
   residual risk triggers Article 36(1) prior consultation with
   the supervisory authority. Sets
   `__article_36_pre_consultation_flag__`.
9. **produce_dpia_document** — produce the durable DPIA
   document artifact. Records `__dpia_document_ref__`.
10. **schedule_review_cadence** — pin the Article 35(11) review
    hook to the operator's change-management surface. Records
    `__review_cadence__`.

## Primitives

CORE-PRIM part 1 of 2. The first five action steps have a
deterministic primitive under `primitives/`, executed directly by
`tests/playbooks/data_protection_impact_assessment/test_primitives.py`.
Every rule was checked against Regulation (EU) 2016/679 on EUR-Lex
and, where the Regulation leaves the method open, against WP248
rev.01.

| Step | Primitive |
|---|---|
| screen_dpia_triggers | `screening.screen_dpia_triggers` |
| classify_processing_type | `classification.classify_processing` |
| gather_processing_description | `description.compose_processing_description` |
| assess_necessity_and_proportionality | `necessity.assess_necessity_and_proportionality` |
| identify_and_assess_risks | `risk.assess_risks` |

Decisions the primitives fix:

- **Screening runs in a fixed order.** The Art. 35(10) exemption,
  then coverage by an existing assessment of similar processing
  (Art. 35(1)), then the Art. 35(3) cases and the Art. 35(4) list,
  then the Art. 35(5) list, then the WP248 rule that two of its nine
  criteria make a DPIA required in most cases. A controller sets two
  criteria aside only with a documented justification and, where a
  DPO is designated, the DPO's views. The controller may always elect
  a DPIA, and a negative screening is retained with its basis.
- **The DPIA is the controller's.** A record held in the processor
  role is refused under Art. 35(1).
- **Lawfulness gaps are recorded.** No Art. 6(1) basis, special
  categories without an Art. 9(2) condition, or criminal-offence data
  without the Art. 10 authority are carried to the necessity
  assessment.
- **The description records what it still lacks.** An undescribed
  legitimate interest where Art. 6(1)(f) is relied on, a data category
  with no storage period or criteria, a third-country recipient
  without a Chapter V basis, or no identified asset.
- **Necessity fails on a sufficient alternative.** If a less intrusive
  alternative would suffice, the processing is not necessary. Excess
  data categories or an unsettled storage period make it not
  proportionate. Lawfulness gaps and missing rights measures are owed.
- **Risks are assessed whole, on the operator's calibration.** Each
  risk names its sources, threats and impacts, with likelihood and
  severity on the operator's scale; it is high when both reach the
  operator's floor. Illegitimate access, undesired modification and
  disappearance must each be covered, or the assessment is
  incomplete.
- **Every record's id covers its whole content.** Two records that
  differ anywhere have different ids.

**Owed: part 2 and the wire.** Part 2 covers the mitigations, the DPO
consultation, the Art. 36 gate, the document and the review cadence.
The wire then binds all ten steps, adds the gates the description
promises (a negative screening ends the lifecycle), declares the
adapter inputs and regenerates the three targets.

## Regulatory anchors

| Step (playbook axis)              | Clause                        |
| --------------------------------- | ----------------------------- |
| Mandatory-DPIA screening          | GDPR Article 35(1), 35(3)(a-c), 35(4) |
| Systematic description            | GDPR Article 35(7)(a)         |
| Necessity and proportionality     | GDPR Article 35(7)(b)         |
| Risk assessment                   | GDPR Article 35(7)(c)         |
| Mitigations                       | GDPR Article 35(7)(d)         |
| DPO consultation                  | GDPR Article 35(2)            |
| Prior-consultation gate           | GDPR Article 36(1), 36(2)     |
| DPIA document / accountability    | GDPR Article 35, Article 5(2) |
| Review cadence                    | GDPR Article 35(11)           |

Inbound mappings live at
[`content/mappings/gdpr/article-35-dpia.yaml`](../../mappings/gdpr/article-35-dpia.yaml)
alongside the existing operational-anchor entries (data_exfil,
identity_compromise, ransomware_containment) whose deployment
triggers the DPIA obligation. The DPIA lifecycle itself is
authored as an additional inbound anchor on the same Article
35(1) / 35(3)(a) / 35(3)(b) entries in the same PR that lands
this SKELETON.

## Operator integration notes

The SKELETON declares the following adapter-bound surfaces the
operator wires; the CORE card lands the reference bindings:

- **Processing-inventory surface** — the operator's declared
  Article 30 record of processing activities (RoPA) as the
  canonical join key `classify_processing_type` and
  `gather_processing_description` read against.
- **Risk-taxonomy binding** — the operator's declared taxonomy
  over risk-source, risk-event, and impact axes (EDPB reference
  categories: illegitimate access, unauthorised modification,
  disappearance of personal data — plus operator-declared
  context-specific axes) that `identify_and_assess_risks`
  applies.
- **DPO-consultation intake** — the operator's routing surface
  to the designated Data Protection Officer, or the
  documented alternative accountability surface where no DPO
  is designated because Article 37 does not require it.
- **Supervisory-authority pre-consultation submission chain**
  — the outbound submission surface `determine_article_36_gate`
  triggers where the residual risk meets the Article 36(1)
  threshold. The Article 36(2) consultation window (up to
  eight weeks, extendable by six weeks) gates the processing
  before it may begin.
- **DPIA-document template** — the operator's declared
  document template `produce_dpia_document` assembles the
  Article 35(7)(a)-(d) content, the Article 35(2) DPO advice,
  the Article 36 gate outcome, and the Article 35(11) review-
  cadence schedule into.
- **Change-management adapter** — the operator's declared
  change-management surface `schedule_review_cadence` pins the
  Article 35(11) review trigger to.

## Sources

- OASIS CACAO v2.0 specification.
- General Data Protection Regulation (EU) 2016/679 —
  Article 35 (data protection impact assessment), Article 36
  (prior consultation), Article 35(11) (review), Article 5(2)
  (accountability).
- Article 29 Working Party WP248 rev.01 — Guidelines on Data
  Protection Impact Assessment (DPIA), endorsed by the
  European Data Protection Board.
- OCSF v1.3.0 — Compliance Finding (class_uid 2003) event
  class.
