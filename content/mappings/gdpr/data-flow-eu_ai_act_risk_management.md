# GDPR data flow — eu_ai_act_risk_management

Per-workflow GDPR data-flow entry for the `eu_ai_act_risk_management`
cookbook playbook (`playbook.eu_ai_act_risk_management@v1`). Filled
in against [`_data-flow-template.md`](./_data-flow-template.md).
Together the seven sections below form the Art. 30 Record of
Processing Activity entry for this workflow.

Workflow source of truth:
[`content/playbooks/eu_ai_act_risk_management/`](../../playbooks/eu_ai_act_risk_management/).

This workflow is a **lifecycle-governance** playbook: it operates the
EU AI Act Art. 9 identify / analyse / evaluate / adopt cycle over an
AI-system inventory record and its Annex IV technical-documentation
bundle. Recital 9 of Regulation (EU) 2024/1689 preserves the operator's
existing GDPR obligations for any high-risk AI system whose training,
validation, testing, or operational data contains personal data. This
data-flow record scores the workflow's own personal-data touchpoints;
personal-data flows internal to the AI system under assessment are
scored on that system's separate data-flow record, not here.

---

## 1. Purpose

The workflow exists to establish, implement, document, and maintain
the risk-management system Art. 9 of Regulation (EU) 2024/1689
requires providers of high-risk AI systems to operate throughout the
system's lifecycle. It inventories a candidate AI system against
Art. 6 read with Annex III, runs the Art. 9(2) identify / analyse /
evaluate / adopt cycle over the pinned use case, assembles the
technical documentation Art. 11 read with Annex IV pins, and closes
the loop with the Art. 72 post-market monitoring feedback that feeds
the next iteration under Art. 9(2)(c). The purpose is bounded to the
provider-side risk-management obligation and its Art. 11 / Annex IV
technical documentation output; the workflow does not itself run the
AI system, does not process the data the AI system processes, and
does not own the conformity-assessment intake (Art. 43) or the
CE-marking chain (Art. 48).

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(c) — legal obligation**. Article 9 of
Regulation (EU) 2024/1689 imposes a direct legal obligation on
providers of high-risk AI systems to operate a risk-management
system, and Article 11 read with Annex IV imposes the corresponding
obligation to draw up and keep the technical documentation. Where
the AI system under assessment processes personal data, Recital 9 of
Regulation (EU) 2024/1689 preserves the operator's GDPR obligations;
running the Art. 9 cycle in a way that documents personal-data
processing is itself a step the operator relies on to demonstrate
GDPR Art. 5(2) accountability against the AI-system data flow.

Secondary: **GDPR Art. 6(1)(f) — legitimate interests** applies to
the internal-governance metadata the workflow persists beyond the
strict Art. 9 / Art. 11 obligation — the risk-register audit trail,
the per-iteration author attribution on the risk-management record,
and the residual-risk-acceptability scoring beyond the Art. 9(5)
gate. The operator has a legitimate interest in maintaining a
coherent AI-system risk posture and its supervisory-authority
readiness against the market-surveillance surface Art. 74 pins.

Special-category data (GDPR Art. 9) is not the target of this
workflow — the workflow operates on AI-system metadata (Annex III
use-case classification, risk-management-system descriptions,
technical-documentation bundle references, post-market monitoring
signals) rather than on the personal data the AI system itself may
process. Where the AI system under assessment processes GDPR Art. 9
special-category data (biometric identification systems under
Annex III(1) are the canonical case), the special-category exposure
is scored on the AI system's own data-flow record; this workflow's
scoring records the exposure as an attribute of the pinned Annex III
use case rather than as its own processing surface. If an operator's
compile-time binding causes this workflow to persist per-subject
Art. 9 samples in the risk-register, the operator MUST re-score this
section before the binding is pinned.

## 3. Categories of data subjects and personal data

The workflow's inputs and outputs are AI-system-metadata records
rather than per-subject records. The categories below cover the
residual personal data that can flow through the risk-management
cycle despite the metadata-first design.

Data subjects:

- **Employees of the operator** named as the provider under
  Regulation (EU) 2024/1689 Art. 3(3) or as the accountability owner
  under Art. 22 for the pinned AI system. Their identifier appears
  on the risk-management-system record as accountability metadata
  and on the technical-documentation bundle's Annex IV Section 5
  (risk-management-system description) as authorship attribution.
- **Employees of the operator** named as the authors of a
  particular Art. 9(2) iteration — the individual who ran the
  identification / analysis step, the individual who signed off the
  adopted risk-management measures, the individual who curates the
  post-market monitoring feedback. Their identifier appears in the
  risk-register audit trail rather than in the Art. 11 documentation
  bundle itself.
- **Data subjects whose personal data flows through the AI system
  under assessment**, referenced only by category and by the
  Annex III use-case classification pinned on this workflow's
  inventory step. Per-subject records stay with the AI-system's own
  data-flow record; the risk-management record cites the category
  and the Annex III pin so the Art. 9(2)(a) identification step
  can score the risk to the affected rights and freedoms
  (Art. 9(2)(a) explicitly reads on health, safety, and fundamental
  rights, which includes the GDPR-protected right to protection of
  personal data under GDPR Art. 1).

Categories of personal data:

- **AI-system metadata records** — the Annex III use-case pin, the
  provider / deployer role determination under Art. 3(3) and (4),
  the Art. 6(3) derogation self-declaration where applicable. These
  carry the operator-employee identifiers of the provider and
  accountability owner but no per-subject payload from the AI
  system's own processing.
- **Risk-management-system records** — the risk register per
  Art. 9(2)(a)–(d), the residual-risk-acceptability score per
  Art. 9(5), the risk-treatment measures adopted, and the author
  attribution on each iteration. Per-subject identifiers appear
  only via the author-attribution metadata.
- **Technical-documentation bundle references** — the Annex IV
  section-by-section bundle identifier and the authorship
  attribution on each section. The bundle body is out of scope for
  this data-flow record; the workflow persists the reference and
  the audit-trail metadata only.
- **Post-market monitoring signals** — the Art. 72 monitoring-plan
  reference and the per-signal identifier fed back into the Art. 9(2)(c)
  loop. Personal-data content in the signals stays with the AI
  system's own data-flow record; this workflow persists the
  signal reference and the ingestion timestamp only.
- **Audit-trail metadata** — invocation identifier, per-iteration
  timestamp, author reference, accountability signatory reference.
  Personal identifiers in this metadata are limited to the operator
  employees exercising provider-side accountability under
  Regulation (EU) 2024/1689 Art. 22.

The workflow does not introduce a new per-subject record. Where the
AI system under assessment processes personal data, the per-subject
record stays with that system's own data-flow record and only the
category-level reference plus the Annex III use-case pin cross into
the risk-management record.

## 4. Recipients

Internal recipients:

- The **operator's evidence store** — primary recipient of the
  risk-register, the residual-risk-acceptability score, the
  technical-documentation bundle reference, and the per-iteration
  audit-trail entries. The store owns durable retention, integrity
  hashing, and downstream serve-to-reviewer access; the workflow
  does not.
- The **operator's provider-role accountability owner** under
  Regulation (EU) 2024/1689 Art. 22 (the accountability owner for
  the pinned AI system, typically a documented product owner or
  an equivalent accountability surface). This owner reads the
  risk-management record for internal control-effectiveness review
  and is the routing surface for a market-surveillance-authority
  Art. 74 request against the AI system.
- The **operator's DPO** where the AI system under assessment
  processes personal data — DPO reads the risk-management record
  for its bearing on the GDPR Art. 5(2) accountability posture the
  operator maintains for the AI system's own personal-data
  processing.
- The **operator's audit-trail store** — recipient of the per-run
  invocation record, the per-iteration timestamp, the author
  reference, and the accountability signatory reference.

External / processor recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **notified body** designated under Regulation (EU) 2024/1689
  Art. 43 for AI systems whose conformity-assessment procedure
  under Annex VII requires notified-body involvement. The
  technical-documentation bundle assembled by the "assemble
  technical documentation" step is read by the notified body for
  the Annex VII conformity assessment. This is an outbound leg
  scored in §8 when populated (skeleton-pending).
- The **national market-surveillance authority** under
  Regulation (EU) 2024/1689 Art. 74 where the operator's provider-
  side obligations require the risk-management record and the
  Annex IV bundle to be surfaced on request. The workflow does not
  itself submit to the market-surveillance authority; the
  operator's outbound submission surface reads the record from the
  evidence store and forwards it under the transposition-specific
  chain. This is an outbound leg scored in §8 when populated
  (skeleton-pending).

Each operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production
where the risk-management record's author-attribution or
accountability-signatory metadata is disclosed to the processor. The
framework does not ship the DPAs; the data-flow record names the
dependency so a sovereignty review can verify it.

## 5. Retention

The workflow's durable artefacts are the **risk-register**
(`__risk_register_id__`), the **technical-documentation bundle
reference** (`__technical_documentation_id__`), and the **post-market
monitoring signal ledger** (`__post_market_signal__`). Retention is
constrained by Regulation (EU) 2024/1689 record-keeping obligations
and by the operator's GDPR-storage-limitation policy.

- **Technical-documentation bundle references and risk-register
  entries** are retained for the statutory record-keeping period
  Regulation (EU) 2024/1689 Art. 18 pins — the provider MUST keep
  the technical documentation, the Art. 9 risk-management-system
  documentation, and the Art. 12 logs at the disposal of the
  national competent authorities for **10 years after the AI system
  has been placed on the market or put into service**. The
  operator's evidence-store lifecycle hook enforces the ten-year
  floor; a longer window applies where the operator's own
  governance-record policy or an active market-surveillance
  investigation extends it.
- **Post-market monitoring signal ledger entries** are retained
  under the Art. 72 post-market monitoring plan the operator
  documents. The Regulation does not pin a fixed period for the
  monitoring plan itself; the operator's plan pins the window and
  the evidence store enforces it.
- **Audit-trail metadata** (invocation record, per-iteration
  timestamp, author reference) is retained under the audit-trail
  store's policy, aligned with the ten-year floor on the
  risk-management record it attributes.

The retention boundary is enforced by the evidence store's
lifecycle hook plus the audit-trail store's policy; the workflow
itself is stateless beyond the per-run artefacts. Where the AI
system under assessment is decommissioned, the ten-year floor
continues to run from the date the system was placed on the market
or put into service, not from the decommissioning date.

## 6. Cross-border transfers

**No transfer** is the default scoring. The workflow is designed to
execute end-to-end on the operator's sovereign-hosted runtime (one
of the EU-hostable reference targets — n8n self-host, Temporal
self-host, or LangGraph self-host on an EU-resident sovereign
provider) with an EU-resident evidence store, EU-resident audit-
trail store, and EU-resident technical-documentation bundle store.

The technical controls that hold this scoring:

- The reference compile targets are framework-agnostic and run on
  the operator's own sovereign-hosted runtime; no SecOps-NG-hosted
  egress path exists in the workflow.
- The evidence store, the audit-trail store, and the
  technical-documentation bundle store are operator-supplied; the
  framework ships no default endpoint and no fallback that could
  route a persist call outside the EU.
- The Art. 9(2) identify / analyse / evaluate / adopt cycle steps
  execute locally against operator-supplied Annex III rubric and
  risk-treatment-policy artefacts; no external classifier or
  aggregation service is invoked.
- The Art. 11 / Annex IV technical-documentation-bundle-assembly
  step composes the bundle locally from operator-supplied section
  templates; no external documentation-authoring service is
  invoked.
- The Art. 72 post-market monitoring signal ingest reads from an
  operator-supplied monitoring endpoint local to the AI system's
  deployment; the workflow does not itself pull from an external
  telemetry aggregator.
- The notified-body and market-surveillance-authority submission
  surfaces are out of scope for the workflow — the risk-management
  cycle writes to the evidence store; the operator's outbound
  submission chain reads from the store and is separately scored on
  its own data-flow record (skeleton-pending §8).

If an operator binds a non-EU evidence store, a non-EU audit-trail
store, a non-EU technical-documentation bundle store, a non-EU
Annex III classifier or risk-scoring service, or a non-EU post-
market monitoring aggregator, this scoring breaks — the operator
MUST re-score this section under "transfer under SCCs / BCRs /
derogation" and document the supplementary measures
(encryption-at-rest with operator-held keys, pseudonymisation of
any operator-employee identifiers carried in the author-attribution
metadata before egress) before the binding goes live. Sovereignty
review at compile time is the gate.

## 7. Data subject rights

- **Access (Art. 15).** A subject who exercises a SAR against the
  operator can be answered on this workflow's records by returning
  the operator-employee identifier and role attribution that
  appears in the risk-management record (provider-role
  accountability owner, iteration author, accountability
  signatory) and the audit-trail metadata attributing them to a
  particular Art. 9(2) iteration or Annex IV bundle section. Where
  the AI system under assessment carries the subject's personal
  data, the SAR is answered against that AI system's own data-flow
  record rather than against the risk-management record; this
  workflow's records carry no per-subject payload from the AI
  system's own processing beyond the Annex III use-case category
  reference.
- **Rectification (Art. 16).** Applicable where the accountability-
  signatory attribution, the iteration-author reference, or the
  provider-role determination is recorded incorrectly. Rectification
  flows through the operator's evidence store and the audit-trail
  store; the workflow inherits the corrected record on the next
  iteration. Per-subject rectification against the AI system's own
  processing is handled by that system's rectification path.
- **Erasure (Art. 17).** The retention floor in §5 (ten years under
  Regulation (EU) 2024/1689 Art. 18) constrains erasure of the
  risk-management record and the technical-documentation bundle
  during that window; the operator's DPO is the gate. Erasure of
  operator-employee attribution metadata inside that window is
  constrained by the regulatory record-keeping obligation, not by
  the workflow. Outside the window, the operator's evidence-store
  lifecycle hook purges the record on TTL and per-subject erasure
  against the (now purged) attribution metadata is operationally
  moot.
- **Objection (Art. 21).** Where the lawful basis is
  **Art. 6(1)(c) legal obligation** (the primary basis in §2),
  Art. 21 does not apply to the Regulation (EU) 2024/1689 Art. 9
  and Art. 11 discharge portions of the processing. For the
  secondary **Art. 6(1)(f)** basis covering the internal-governance
  metadata portion of the workflow, a data subject can object on
  grounds relating to their particular situation; the operational
  handling is to route the objection through the operator's DPO,
  with the overriding-legitimate-interest assessment as the gate.
  Because the workflow's records are AI-system metadata rather than
  per-subject records, the practical effect of an objection is
  narrow.
- **Automated decision-making (Art. 22).** The Art. 9(2)
  identify / analyse / evaluate / adopt cycle is a deterministic
  human-in-the-loop discipline as shipped: the identification and
  analysis steps operate against an operator-supplied Annex III
  rubric with named-author attribution, the residual-risk-
  acceptability decision under Art. 9(5) is signed by the
  accountability owner, and the technical-documentation-bundle
  assembly is a curated composition. The workflow as shipped does
  not produce a legal or similarly significant effect on a data
  subject in its own right, so Art. 22 does not apply. If an
  operator binds an automated Annex III classifier or an automated
  risk-scoring policy whose output directly feeds an adverse
  decision on a subject named in the AI system's own processing,
  the automated-decision-making analysis moves to the AI system's
  own data-flow record and the operator MUST re-score this
  section.
