# data_protection_impact_assessment — cookbook walkthrough

Operator-side ex-ante assessment lifecycle a controller runs
*before* deploying processing that is likely to result in a high
risk to the rights and freedoms of natural persons. The
`playbook.data_protection_impact_assessment@v1` CACAO playbook
operates the screen-to-schedule chain across the ten steps GDPR
Article 35 codifies: screening against the Article 35(3)
mandatory triggers, classification against the operator's
processing-inventory surface, the four Article 35(7)(a)–(d)
content limbs (systematic description, necessity and
proportionality, risks to rights and freedoms, mitigations), the
Article 35(2) Data Protection Officer consultation, the Article
36(1) residual-risk gate, the durable DPIA document artifact for
the Article 5(2) accountability posture, and the Article 35(11)
review-cadence schedule.

The playbook is the **portable description of the DPIA
discharge**. It does not choose the operator's processing-
inventory join key (the Article 30 record of processing
activities is the canonical inventory surface, but its schema and
join-key are operator-owned), does not embed the risk-taxonomy
calibration heuristics, does not pin the identity of the
Data Protection Officer, and does not ship the DPIA-document
template. It describes the workflow shape the controller's stack
should run so the ten-step lifecycle is auditable, replayable,
and restart-safe — as a shipped Digital Commons artifact.

Distinct from the Article 33 / Article 34 personal-data-breach
notification lifecycle (owned by the sibling `incident_management`
and `data_exfil` playbooks) and from the Article 15–22 subject-
initiated rights lifecycle (owned by the sibling
`data_subject_rights` playbook): the DPIA is the **ex-ante**
process obligation the controller discharges *before* the
processing is bound to production. The breach-notification lane
is controller-initiated on a breach event, after the fact; the
rights lane is subject-initiated against already-collected data;
the DPIA lane is controller-initiated against processing that has
not yet begun, on the Article 35(1) high-risk test and the
Article 35(3) mandatory triggers.

This walkthrough wires the shipped playbook through all three
reference compile targets (n8n, Temporal, LangGraph) and shows
where each lifecycle stage — threshold screening, scoping, risk
assessment, safeguard design, DPO consultation, residual-risk
determination, document assembly, and review scheduling — lands
in each. Adapter bodies (processing-inventory join, DPO
consultation channel, review-scheduler surface, DPIA-document
template, supervisory-authority pre-consultation submission) are
declared as adapter-bound surfaces the operator wires; the
shipped CORE artifact (see § 2) lands the emitter fan-out, the
evidence-record schema, and the byte-parity goldens.

> The framework is framework-agnostic by construction. n8n /
> Temporal / LangGraph are *three of three* reference targets;
> the same CACAO source compiles into all of them. Operators
> run whichever target already lives in their stack.

## 1. Why this matters

GDPR Article 35 obliges the controller to carry out a data
protection impact assessment prior to processing that is likely
to result in a high risk to the rights and freedoms of natural
persons, and Article 36 obliges the controller to consult the
supervisory authority prior to processing where the DPIA
concludes that the risk would be high in the absence of
mitigations. The article set the workflow discharges:

- **Art. 35(1)** — the general obligation: carry out a DPIA
  prior to processing likely to result in a high risk, taking
  into account the nature, scope, context, and purposes of the
  processing.
- **Art. 35(2)** — where a Data Protection Officer has been
  designated, the controller seeks the DPO's advice when
  carrying out the assessment.
- **Art. 35(3)(a)–(c)** — the mandatory-DPIA triggers:
  systematic and extensive evaluation of personal aspects based
  on automated processing on which decisions producing legal or
  similarly significant effects are based; large-scale
  processing of special categories of data or personal data
  relating to criminal convictions and offences; systematic
  monitoring of a publicly accessible area on a large scale.
- **Art. 35(4)** — the supervisory authority's list of
  processing kinds that require a DPIA in the operator's
  jurisdiction.
- **Art. 35(7)(a)–(d)** — the four assessment content limbs:
  a systematic description of the processing operations and
  their purposes; an assessment of necessity and
  proportionality in relation to the purposes; an assessment
  of the risks to the rights and freedoms of data subjects;
  the measures envisaged to address the risks (safeguards,
  security measures, mechanisms).
- **Art. 35(11)** — where necessary, the controller carries out
  a review to assess whether processing is performed in
  accordance with the DPIA, at least when there is a change of
  the risk represented by the processing operations.
- **Art. 36(1)** — the controller consults the supervisory
  authority prior to processing where the DPIA indicates that
  the processing would result in a high risk in the absence of
  measures taken by the controller to mitigate the risk.
- **Art. 36(2)** — the supervisory-authority consultation
  window: written advice within eight weeks of receipt of the
  request, extendable by six weeks taking into account the
  complexity of the intended processing.
- **Art. 5(2)** — the accountability posture: the controller is
  responsible for, and able to demonstrate compliance with, the
  Regulation's data-protection principles. The DPIA document is
  the primary discharge artifact for the processing envelope
  the assessment covers.

Deploying high-risk processing without a DPIA is a
supervisory-authority-visible event under Article 58(1)(a) and
an Article 83(4)(a) administrative-fine surface. Wiring the
assessment into an orchestration surface that survives worker
restart, records the ten-step lifecycle as durable evidence, and
gates deployment on the Article 36(1) residual-risk
determination is the audit-evident discharge of the obligation;
wiring it into a controller's document store "on best effort"
is not.

## 2. Source of truth

```
content/playbooks/data_protection_impact_assessment/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / GDPR overlay
└── playbook.cacao.yaml          # canonical CACAO v2 source (playbook.data_protection_impact_assessment@v1)

content/mappings/gdpr/article-35-dpia.yaml
                                  # GDPR Article 35 inbound anchors —
                                  # gdpr:art-35-1-dpia-high-risk-processing,
                                  # gdpr:art-35-3-a-dpia-systematic-evaluation,
                                  # gdpr:art-35-3-b-dpia-large-scale-processing

schemas/evidence/dpia.schema.json  # DPIA evidence-artifact schema
                                  # (screening outcome, residual-risk verdict,
                                  # DPO consultation record, Article 36(1)
                                  # prior-consultation flag)
```

The CACAO source is canonical. The ten-step lifecycle (one
`start`, ten `action` steps, one `end`) is the deterministic
policy the playbook *means*. The three worked examples under
`examples/{n8n,temporal,langgraph}/data_protection_impact_assessment/`
are the same playbook compiled into three orchestrator idioms.
The DPIA-evidence artifact each execution emits is pinned by
[`schemas/evidence/dpia.schema.json`](../../schemas/evidence/dpia.schema.json);
the schema deliberately excludes `compile_target` from the
`artifact_id` derivation so a replay under a different target
produces byte-identical evidence for the same
`(workflow_id, execution_id, captured_at)` input. Byte-parity is
asserted across all three targets by the goldens under
`tests/examples/data_protection_impact_assessment/`.

The G-01 traceability anchor for this workflow closes here: the
ROADMAP entry `F-WF-DPIA` (see [`ROADMAP.md`](../../ROADMAP.md))
names this cookbook, the shipped CACAO source, the compiled
targets, and the DPIA-evidence schema as the deliverables that
discharge Article 35 coverage on the content axis; G-02 closes
against the GDPR mappings file; G-03 closes against the
byte-parity goldens the CORE artifact lands.

## 3. CACAO topology

The workflow is a linear ten-step lifecycle. Each action step
carries the CACAO I/O contract (`in_args` / `out_args`) plus
`x_secops_ng` reference bundles pinning the OSCAL control anchor,
D3FEND technique (where a defensive-technique fit exists), and
OCSF telemetry class the step emits.

| Step suffix | Step                                    | Discipline                                                                                                                             | Status         |
|-------------|-----------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | dpia_start                              | edge wiring only — no body                                                                                                             | n/a            |
| `…000002`   | screen_dpia_triggers                    | evaluate the Art. 35(1) high-risk test and Art. 35(3)(a)–(c) mandatory triggers; assign `__dpia_case_id__`; set `__dpia_required__` and `__screening_result_ref__` | adapter-bound  |
| `…000003`   | classify_processing_type                | resolve the processing envelope against the operator's Article 30 record-of-processing-activities inventory; anchor scope              | adapter-bound  |
| `…000004`   | gather_processing_description           | assemble the Article 35(7)(a) systematic description (purposes, categories of data and subjects, recipients, retention); sets `__processing_description_ref__` | adapter-bound  |
| `…000005`   | assess_necessity_and_proportionality    | assess Article 35(7)(b) necessity and proportionality of the processing in relation to the purposes                                    | adapter-bound  |
| `…000006`   | identify_and_assess_risks               | apply the operator's risk taxonomy over the Article 35(7)(c) rights-and-freedoms axis; sets `__risk_assessment_ref__`                  | adapter-bound  |
| `…000007`   | identify_and_document_mitigations       | document the Article 35(7)(d) safeguards, security measures, and mechanisms; sets `__mitigations_ref__`                                | adapter-bound  |
| `…000008`   | dpo_consultation                        | obtain the Article 35(2) DPO advice; sets `__dpo_consultation_ref__`                                                                   | adapter-bound  |
| `…000009`   | determine_article_36_gate               | determine the Article 36(1) residual-risk verdict; sets `__article_36_pre_consultation_flag__`                                         | adapter-bound  |
| `…00000a`   | produce_dpia_document                   | assemble the durable DPIA document for the Article 5(2) accountability posture; sets `__dpia_document_ref__`                           | adapter-bound  |
| `…00000b`   | schedule_review_cadence                 | pin the Article 35(11) review hook against the operator's change-management surface; sets `__review_cadence__`                         | adapter-bound  |
| `…00000f`   | dpia_end                                | edge wiring only — no body                                                                                                             | n/a            |

> A false `__dpia_required__` outcome at `screen_dpia_triggers`
> short-circuits the lifecycle: the negative screening is
> retained on the accountability ledger and the workflow exits
> without producing an Article 35(7) assessment. A false outcome
> at `determine_article_36_gate` (i.e. residual risk below the
> Article 36(1) high-risk threshold after mitigation) allows the
> processing to proceed once `produce_dpia_document` and
> `schedule_review_cadence` complete; a true outcome gates
> deployment on the supervisory-authority pre-consultation
> submission chain, which the shipped CORE artifact declares as
> an adapter-bound surface.

## 4. Playbook variables

The playbook operates on a small set of workflow-scope variables.
`__processing_ref__` is external — supplied by the operator at
lifecycle entry against the processing envelope under
assessment. The remainder are set by downstream steps as the
case progresses:

| Variable                                | External? | Set by                                     | Purpose                                                                                                                                    |
|-----------------------------------------|-----------|--------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| `__processing_ref__`                    | yes       | operator-supplied                          | reference to the processing operation under assessment; joined against the operator's Article 30 record-of-processing-activities inventory |
| `__dpia_case_id__`                      | no        | `screen_dpia_triggers`                     | correlation key across the ten steps and against the operator's evidence store                                                             |
| `__dpia_required__`                     | no        | `screen_dpia_triggers`                     | boolean screening verdict against Art. 35(1), Art. 35(3)(a)–(c), and the operator's Art. 35(4) supervisory-authority list                  |
| `__screening_result_ref__`              | no        | `screen_dpia_triggers`                     | reference to the screening-decision artifact retained on the accountability ledger regardless of the boolean outcome                       |
| `__processing_description_ref__`        | no        | `gather_processing_description`            | Article 35(7)(a) systematic description (purposes, categories of data and subjects, recipients, retention, transfer legs)                  |
| `__risk_assessment_ref__`               | no        | `identify_and_assess_risks`                | Article 35(7)(c) risks-to-rights-and-freedoms assessment (per-risk likelihood, severity, and residual-risk profile)                        |
| `__mitigations_ref__`                   | no        | `identify_and_document_mitigations`        | Article 35(7)(d) safeguards, security measures, and mechanisms; per-risk mitigation attribution                                            |
| `__dpo_consultation_ref__`              | no        | `dpo_consultation`                         | Article 35(2) DPO advice record (or the operator's alternative-accountability-surface record where no DPO is designated per Art. 37)       |
| `__article_36_pre_consultation_flag__`  | no        | `determine_article_36_gate`                | Article 36(1) residual-risk verdict against the mitigated risk profile                                                                     |
| `__dpia_document_ref__`                 | no        | `produce_dpia_document`                    | durable DPIA document artifact for the Article 5(2) accountability posture                                                                 |
| `__review_cadence__`                    | no        | `schedule_review_cadence`                  | ISO 8601 duration recording the Article 35(11) maximum review interval absent a material processing change                                 |

The screening-outcome handling is the invariant that pins
correctness of the whole lifecycle: the screening record is
retained on the accountability ledger **whether or not** a full
DPIA is subsequently produced. A negative screening is
audit-evident on the operator's Article 5(2) surface — an
Article 58(1)(a) supervisory-authority information order will
ask *why* the controller concluded a DPIA was not required, and
the retained screening result is the answer.

## 5. Adapter-bound surfaces

Five operator-owned surfaces sit behind adapter shims in the
lifecycle. The framework describes the CACAO contract each
surface writes into; it does not ship the surface.

### 5.1 Processing-inventory join (Article 30 RoPA)

`classify_processing_type` and `gather_processing_description`
read the processing envelope from the operator's Article 30
record-of-processing-activities inventory. The RoPA is the
canonical join key for the DPIA — the assessment scope is a
single processing envelope in the RoPA, and the Article 35(7)(a)
description is a systematic view of that envelope's declared
purposes, categories of data and subjects, recipients, and
retention. The framework ships **no default RoPA schema**: the
per-controller inventory shape sits with the operator, and the
adapter reads whatever inventory surface the operator has
declared (a Postgres inventory table, a Notion-backed RoPA
document, a compliance-platform export). What the framework
declares is the join contract: `__processing_ref__` is the
inventory row-id.

### 5.2 DPO consultation channel

`dpo_consultation` delegates to the operator's declared DPO
consultation surface. Two lanes ship as adapter-bound surfaces:

- **DPO-designated (Article 37 applies).** Where the controller
  has designated a DPO, the adapter routes the assembled
  Article 35(7)(a)–(d) content to that officer's consultation
  channel (structured-review request against the operator's
  ticketing surface, or an email-plus-response envelope against
  the DPO's channel of record). The DPO's written advice is
  recorded on the case as `__dpo_consultation_ref__`.
- **No DPO designated (Article 37 does not require it).** Where
  the controller has not designated a DPO, the adapter records
  that fact plus the alternative-accountability-surface the
  controller relies on (senior-management sign-off record,
  cross-functional-review committee minutes) as
  `__dpo_consultation_ref__`. The Article 35(2) obligation is
  conditional; the accountability posture is not.

The framework ships **no default DPO identity**, no
credential material, and no substitute for a missing
consultation record.

### 5.3 Article 36 pre-consultation submission chain

`determine_article_36_gate` sets the boolean flag; the
downstream submission chain is adapter-bound. Where the flag is
true, the controller consults the supervisory authority under
Article 36(1) and the processing may not begin until the
Article 36(2) consultation window completes (up to eight weeks,
extendable by six weeks). The submission-chain adapter carries
the supervisory-authority-facing envelope shape, the
per-authority submission channel (each EU supervisory authority
publishes its own), and the deadline gating on
`produce_dpia_document` — the DPIA document is a required
attachment to the pre-consultation submission.

### 5.4 DPIA-document template

`produce_dpia_document` assembles the durable artifact against
the operator's declared DPIA-document template. The template
shape is operator-owned; what the framework declares is the
content the template must carry: the Article 35(7)(a) systematic
description, the Article 35(7)(b) necessity-and-proportionality
assessment, the Article 35(7)(c) risk assessment, the
Article 35(7)(d) mitigations, the Article 35(2) DPO advice, the
Article 36(1) gate outcome, and the Article 35(11) review
schedule. The document is the primary response to any subsequent
Article 58(1)(a) supervisory-authority information order.

### 5.5 Review scheduler

`schedule_review_cadence` pins the Article 35(11) review hook
against the operator's change-management surface. The adapter
subscribes to the operator's change-events for the processing
envelope (RoPA edits, purpose changes, retention changes,
underlying-technology substrate changes) and re-triggers the
DPIA lifecycle on any material change. The cadence duration
(`__review_cadence__`) records the maximum interval between
reviews absent such a change; the change-driven trigger is the
primary review path, and the cadence is the fallback.

## 6. Regulatory anchors

**GDPR Chapter IV — Articles 35 and 36 and Article 5(2).** The
regulation prescribes the ex-ante assessment obligation, the
supervisory-authority prior-consultation gate, and the
accountability posture the DPIA document discharges. Inbound
anchors live at
[`content/mappings/gdpr/article-35-dpia.yaml`](../../content/mappings/gdpr/article-35-dpia.yaml)
under the mapping ids `gdpr:art-35-1-dpia-high-risk-processing`,
`gdpr:art-35-3-a-dpia-systematic-evaluation`, and
`gdpr:art-35-3-b-dpia-large-scale-processing`. Each backlinks
`playbook.data_protection_impact_assessment@v1`. Article 36(1)
prior consultation is folded onto the Article 35(1) entry via
the `determine_article_36_gate` step — the gate discharges the
controller-side determination that Article 36(1) requires before
the processing may begin.

**Article 29 Working Party WP248 rev.01 (endorsed by the EDPB)
— Guidelines on Data Protection Impact Assessment.** The
guidelines frame the operator-facing expectations for the
Article 35(3) mandatory-DPIA triggers (evaluation-or-scoring;
automated-decision with legal or similarly significant effect;
systematic monitoring; sensitive-data or highly-personal data;
large-scale processing; matching or combining datasets;
vulnerable-subject processing; innovative use or applying new
technological or organisational solutions; preventing subjects
from exercising a right or using a service or contract). The
`screen_dpia_triggers` adapter pins the guidelines as the
reference shape for the trigger set the screening step
evaluates.

**OSCAL controls** — from
[`content/playbooks/data_protection_impact_assessment/mappings.yaml`](../../content/playbooks/data_protection_impact_assessment/mappings.yaml):

- **PM-9** — *Risk Management Strategy*, anchored on
  `screen_dpia_triggers` via the `control.risk_management_policy@v1`
  cross-reference. The DPIA is the per-processing-envelope
  discharge of the operator's risk-management strategy against
  the rights-and-freedoms axis GDPR Article 35 codifies.
- **RA-3** — *Risk Assessment*, anchored on
  `identify_and_assess_risks` and
  `assess_necessity_and_proportionality`. RA-3 requires the
  organisation to conduct an assessment of risk including
  likelihood and impact determination; the Article 35(7)(c)
  assessment is the personal-data axis of that determination.
- **AU-9** — *Protection of Audit Information*, anchored on
  `produce_dpia_document` and `schedule_review_cadence` via the
  `control.incident_timeline_signals@v1` cross-reference. The
  DPIA document is the audit-information surface the operator's
  Article 5(2) accountability posture is discharged against.

**MITRE D3FEND v1.0.0** — `D3-OAM` *Operational Activity
Mapping* is selected on `identify_and_assess_risks` as the
closest-fitting defensive technique for the systematic-
description-of-processing-operations discharge Article 35(7)(a)
requires and the risk-and-mitigations mapping the assessment
produces. The remaining nine steps carry no D3FEND technique:
the workflow is a discharge discipline for an ex-ante process
obligation, not a runtime countermeasure against an adversary
behaviour, and the closest fit is the operational-activity
mapping at the assessment gate.

**OCSF v1.3.0** — one class binding.
`Compliance Finding` (class_uid 2003, category Findings),
direction `emits`, is emitted at each of the ten action steps
as the structured per-milestone record the compliance layer
routes on. One Compliance Finding per lifecycle milestone,
keyed to `__dpia_case_id__`, so the operator's Article 5(2)
accountability posture can be computed and audited from the
emitted telemetry alone.

**DPIA-evidence schema.** The
[`dpia.schema.json`](../../schemas/evidence/dpia.schema.json)
evidence artifact pins the closed screening outcome, the
residual-risk verdict, the DPO consultation record, the
`article_36_prior_consultation_flag`, the Article 35 /
Article 36 `regulation_refs`, and the `control_refs` list.
`artifact_id` derives deterministically from
`SHA-256(workflow_id|execution_id|captured_at)` — the field
does not key on `compile_target`, so a replay under a different
target produces byte-identical evidence bytes.

## 7. Per-target hand-off

### 7.1 n8n — Set nodes over the ten-step lifecycle

`examples/n8n/data_protection_impact_assessment/workflow.n8n.json`
carries the CACAO topology as n8n nodes (one `manualTrigger`, one
`set` node per action, one `noOp` terminal). Node ids preserve
the CACAO step ids verbatim. Each action node emits a
`n8n-nodes-base.set` carrying the CACAO I/O contract as editable
assignment rows plus the `x_secops_ng` reference bundles.

Operators bind the Set rows to their connectors:

- `screen_dpia_triggers` → the operator's screening surface (a
  Function node against the Article 35(3) trigger set; an
  HTTP Request node against a compliance-platform screening
  endpoint; or a Set node when the trigger evaluation is
  authored inline by the assessor). Writes `__dpia_case_id__`,
  `__dpia_required__`, `__screening_result_ref__`.
- `classify_processing_type` → the operator's RoPA-inventory
  connector (Postgres node against the inventory table; HTTP
  Request node against the inventory API; or an Airtable /
  Notion node when the RoPA lives there).
- `gather_processing_description` → the RoPA-extraction path
  (Function node materialising the Article 35(7)(a) description
  against the joined inventory row); writes
  `__processing_description_ref__`.
- `assess_necessity_and_proportionality` → the necessity-and-
  proportionality template (Set node with the reasoning rows,
  or a Subflow invocation against a shared template).
- `identify_and_assess_risks` → the operator's risk-taxonomy
  surface (Function node applying the taxonomy over the
  description; or an HTTP Request against a shared risk-registry
  engine); writes `__risk_assessment_ref__`.
- `identify_and_document_mitigations` → the safeguards catalogue
  (Set node against the operator's per-control mitigation
  library); writes `__mitigations_ref__`.
- `dpo_consultation` → the DPO-consultation channel (Send Email
  node against the DPO's channel of record; HTTP Request node
  against the operator's ticketing surface; or a Wait node on a
  webhook trigger when the DPO responds asynchronously); writes
  `__dpo_consultation_ref__`.
- `determine_article_36_gate` → the residual-risk gate (Function
  node reading the assessment-and-mitigations pair against the
  operator's Article 36(1) threshold); writes
  `__article_36_pre_consultation_flag__`.
- `produce_dpia_document` → the DPIA-document assembler
  (Function node materialising the durable artifact against the
  operator's template); writes `__dpia_document_ref__`.
- `schedule_review_cadence` → the change-management connector
  (HTTP Request against the operator's change-tracking surface,
  or a Cron node when the fallback cadence is the primary
  review path); writes `__review_cadence__`.

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/data_protection_impact_assessment/regenerate.sh
```

The script mirrors the canonical CACAO YAML into a
byte-deterministic JSON form and then emits `workflow.n8n.json`
via the unified `tools.compile` CLI. The byte-parity golden
test under
`tests/examples/data_protection_impact_assessment/test_n8n_workflow_golden.py`
reruns the same pipeline and fails if the committed artifact
drifts.

### 7.2 Temporal — activities over the ten-step lifecycle

`examples/temporal/data_protection_impact_assessment/workflow.temporal.py`
carries the CACAO topology as a Temporal workflow with one
activity per action step. `__processing_ref__` is threaded
through the workflow signature as an argument — the inventory
join, the Article 35(7) content assembly, and the Article 36
gate all read from that external playbook-scoped input rather
than from a worker-local scope. A worker restart mid-workflow
re-hydrates the same inventory-row scope against Temporal's
event-history replay contract, so a re-emission of the
DPIA-evidence artifact produces byte-identical
`artifact_id` bytes.

Operators bind the activity bodies to real connectors:

- `screen_dpia_triggers` — the screening activity; the
  reference binding evaluates the Article 35(3) trigger set
  against the processing envelope and stamps
  `__dpia_case_id__`.
- `classify_processing_type` — the RoPA-inventory activity.
- `gather_processing_description` — the description-assembly
  activity.
- `assess_necessity_and_proportionality`,
  `identify_and_assess_risks`,
  `identify_and_document_mitigations` — the three assessment
  activities carrying the Article 35(7)(b)–(d) content.
- `dpo_consultation` — the DPO-consultation activity. The
  DPO-side response is typically async; Temporal's signal
  primitive is the natural fit — the activity waits on a
  `dpo_advice_received` signal, so an operator's channel of
  record can post the advice back to the workflow without
  polling.
- `determine_article_36_gate` — the residual-risk gate
  activity.
- `produce_dpia_document` — the document-assembly activity.
- `schedule_review_cadence` — the review-scheduler activity.
  The Article 35(11) change-driven review is typically
  externalised as a Temporal cron-workflow the operator's
  change-management surface signals into.

To regenerate the compiled artifact from the repo root:

```sh
./examples/temporal/data_protection_impact_assessment/regenerate.sh
```

The byte-parity golden test under
`tests/examples/data_protection_impact_assessment/test_temporal_workflow_golden.py`
reruns the emitter and fails if the committed artifact drifts.

### 7.3 LangGraph — nodes and state over the ten-step lifecycle

`examples/langgraph/data_protection_impact_assessment/graph_spec.json`
carries the CACAO topology as a target-neutral GraphSpec (nodes,
edges); `state_bindings.py` emits the `TypedDict` state and the
`@tool`-decorated action wrappers plus the agentic-extension
hook. `__processing_ref__` is expressed as a state field
threaded through node bodies — the RoPA join, the Article 35(7)
content, and the Article 36 gate all read from state, so a
checkpoint reload re-hydrates the same assessment scope.

The audit-mirror sibling `_audit_mirror.py` (see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md))
carries the OTel-free durable audit trail on LangGraph runs
where the operator has not wired an OTLP collector.

Operators bind the tool bodies to real connectors:

- `screen_dpia_triggers` → screening surface tool.
- `classify_processing_type`,
  `gather_processing_description`,
  `assess_necessity_and_proportionality`,
  `identify_and_assess_risks`,
  `identify_and_document_mitigations` — one tool per
  assessment step against the operator's substrate.
- `dpo_consultation` → DPO-consultation tool + optional
  agentic-extension hook. The agentic-extension surface is
  where the operator's LangGraph agent can pause the graph on
  the DPO's asynchronous review and resume on the
  advice-received signal.
- `determine_article_36_gate` → residual-risk gate tool.
- `produce_dpia_document` → DPIA-document assembler tool.
- `schedule_review_cadence` → review-scheduler tool.

To regenerate the compiled artifacts from the repo root:

```sh
./examples/langgraph/data_protection_impact_assessment/regenerate.sh
```

## 8. Byte-parity across compile targets — the G-03 invariant

The DPIA-evidence artifact each execution emits is anchored by
the evidence schema at
[`schemas/evidence/dpia.schema.json`](../../schemas/evidence/dpia.schema.json).
The `artifact_id` field is a SHA-256 hex digest over
`<workflow_id>|<execution_id>|<captured_at>` (UTF-8, single
pipe separators, no surrounding whitespace) and **does not
include the compile target in its input**. A replay of the same
`(workflow_id, execution_id, captured_at)` triple under n8n,
Temporal, or LangGraph produces byte-identical evidence bytes.

Concretely, across the three targets:

- **n8n** — the DPIA-evidence emitter reads `execution_id`
  from the workflow-execution scope and `captured_at` from the
  emitting node's evaluation. The `artifact_id` derivation is
  authored in the emitter template, not in the target-specific
  Function nodes, so re-executions and n8n version changes do
  not drift the hash.
- **Temporal** — the emitter activity reads `execution_id` as
  the Temporal workflow-run id and `captured_at` from a
  workflow-local timestamp threaded through the activity call,
  not from `datetime.utcnow()` inside the activity body. A
  history-replay re-derives the identical hash.
- **LangGraph** — the emitter tool reads `execution_id` from
  the LangGraph thread/checkpoint id and `captured_at` from
  state, not from `time.time()` inside the tool body. A
  checkpoint reload re-derives the identical hash.

The byte-parity invariant is asserted across all three targets
by the goldens under
`tests/examples/data_protection_impact_assessment/`. The
`test_dpia_evidence_record_golden.py` test in that suite reruns
the emitter fan-out under a synthetic
`(workflow_id, execution_id, captured_at)` fixture and asserts
the emitted DPIA-evidence bytes are identical across n8n,
Temporal, and LangGraph.

The reason for the target-agnostic anchor is regulatory, not
stylistic. The Article 5(2) accountability posture is a posture
about the *processing envelope*, not about the *orchestrator*.
An operator who migrates from n8n to Temporal (or runs both on
different processing envelopes concurrently) must be able to
consolidate their DPIA-evidence store without dedup drift; the
framework refuses the drift-shape by construction.

## 9. Playbook chain — where data_protection_impact_assessment sits

The DPIA lifecycle interacts with several neighbouring playbooks
on the operator's substrate. The interactions are documented at
the CACAO source but are worth calling out in a cookbook context
so a reader can situate the workflow:

- **`data_subject_rights`** — the Article 15–22 subject-
  initiated rights lifecycle is subject-initiated against
  already-collected data; the DPIA lifecycle is
  controller-initiated *before* the processing is bound to
  production. A DSR request that surfaces processing the
  controller had not previously assessed is a leading signal
  that a retro-DPIA is owed for that envelope; the hand-off
  is a controller-side decision documented in the operator's
  policy, not a branch in either workflow.
- **`incident_management` / `data_exfil`** — the Article 33 /
  Article 34 personal-data-breach notification lifecycle is
  controller-initiated on a breach event, after the fact. A
  post-incident review that recommends a change to the
  processing envelope's safeguards triggers a
  `schedule_review_cadence` invocation of the DPIA lifecycle
  against the affected envelope; the two lanes share the
  operator's evidence store by contract.
- **`iam_auditor`** — the DPIA lifecycle reads the operator's
  processing-inventory surface; `iam_auditor` audits the
  identity-access posture that surface depends on. A failing
  `iam_auditor` posture is a leading indicator that the
  RoPA-join key is stale; the two playbooks share the
  inventory integration point.
- **`contractual_obligations_tracker`** — DPIA scopes that
  extend across a controller's processor (Article 28) join
  the processor-side DPIA content through the DPA-obligation
  surface the `contractual_obligations_tracker` playbook
  maintains. The processor-side description feeds back into
  `gather_processing_description` on the controller-side
  DPIA workflow.

## 10. What this cookbook deliberately does not cover

- **The processing-inventory (RoPA) schema.** The per-controller
  Article 30 record-of-processing-activities inventory shape,
  its join key, and its per-owner routing catalogue are
  operator-owned. The framework describes the join contract; it
  does not ship the inventory.
- **The DPO identity.** The Article 35(2) consultation is
  routed to whichever DPO the controller has designated (or to
  the operator's alternative-accountability-surface where no
  DPO is designated per Article 37). Individual DPO identities
  are operator-owned and sit behind the adapter.
- **The risk-taxonomy calibration.** The Article 35(7)(c)
  assessment reads the operator's declared risk taxonomy
  (per-risk likelihood, severity, and residual-risk calibration
  bands) — the taxonomy content is operator-owned. The
  framework describes the assessment shape; it does not ship
  the taxonomy.
- **The DPIA-document template.** The Article 35(7)(a)–(d)
  content and the Article 35(2) DPO-advice attachment are
  assembled into the operator's declared document template;
  the template shape is operator-owned.
- **The supervisory-authority pre-consultation submission
  channel.** Each EU supervisory authority publishes its own
  Article 36(1) submission surface (per-authority form,
  per-authority reference-number allocation, per-authority
  channel of record). The framework declares the boolean gate
  and the required document set; the submission channel sits
  with the operator.
- **The Article 36(2) consultation-window management.** The
  eight-week (extendable to fourteen-week) supervisory-
  authority consultation window is externalised to the
  operator's compliance calendar; the framework records the
  gate outcome but does not manage the wait.
- **The processing deployment gate itself.** The DPIA
  lifecycle produces the assessment artifact and the Article
  36(1) gate outcome; the actual gating of the processing
  deployment on those outputs sits with the operator's change-
  management and deployment surfaces, not with this workflow.

## 11. References

- OASIS CACAO v2.0 specification.
- General Data Protection Regulation (EU) 2016/679 —
  Article 5(2), Chapter IV (Articles 24–43, in particular
  Articles 35, 36, and 37).
- Article 29 Working Party WP248 rev.01 — Guidelines on Data
  Protection Impact Assessment (DPIA), endorsed by the EDPB.
- NIST SP 800-53 Rev. 5 — PM-9 Risk Management Strategy, RA-3
  Risk Assessment, AU-9 Protection of Audit Information.
- MITRE D3FEND v1.0.0 — D3-OAM Operational Activity Mapping.
- OCSF v1.3.0 — Compliance Finding (class_uid 2003) event class.
