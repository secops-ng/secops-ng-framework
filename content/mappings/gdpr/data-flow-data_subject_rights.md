# GDPR data flow — data_subject_rights

Per-workflow GDPR data-flow entry for the `data_subject_rights`
cookbook playbook (`playbook.data_subject_rights@v1`). Filled in
against [`_data-flow-template.md`](./_data-flow-template.md).
Together the seven sections below form the Art. 30 Record of
Processing Activity entry for this workflow, and §8 documents the
outbound personal-data transfer legs under GDPR Chapter V
(Art. 44–49) for the subject-facing response envelope the
lifecycle emits.

Workflow source of truth:
[`content/playbooks/data_subject_rights/`](../../playbooks/data_subject_rights/).

Status: SKELETON. The verification, data-owner routing, and
response-envelope templates are declared as adapter-bound
surfaces the operator wires; the ROPA entry below scopes the
personal-data surface that is stable across those adapters
(subject contact, fulfilment-pack content, case correlation
record). A sibling CORE card revisits this doc once the adapter
surfaces land.

---

## 1. Purpose

The workflow exists to operate the controller-side lifecycle a
data subject exercises against personal data the controller
holds: receive a data subject rights (DSR) request through the
controller's declared intake surface, verify the requesting
party against the controller's declared subject-verification
surface (sovereign IdP integration point), classify the request
axis (access under Art. 15, rectification under Art. 16, erasure
under Art. 17, restriction under Art. 18, portability under
Art. 20, objection under Art. 21, or Article 22 automated-
decision-review concern), route it to the holding data-store
owners, compile the per-request fulfilment evidence pack, send
the controller's response on or before the Article 12(3) response
deadline, and record the outcome for the operator's Article 5(2)
accountability posture. The purpose is bounded to that
receive-to-record chain and the per-case correlation record that
joins the milestones into a single reportable-event ledger keyed
on `__case_id__`. The workflow does not itself review the
underlying automated decision an Article 22 concern names — it
classifies the concern and routes it to the operator's human-in-
the-loop review surface — and does not perform incident
classification against NIS2 Art. 23 or GDPR Art. 33.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(c) — legal obligation**. The processing
is necessary for compliance with the controller's statutory duty
under GDPR Articles 15-22 (rights of the data subject) and
Article 12 (modalities and response window) to fulfil a data
subject's request. The lawful basis for processing the personal
data carried inside the request envelope (subject contact,
verification evidence, per-owner acknowledgement records,
fulfilment-pack content) is the Chapter III obligation itself.

Secondary: **GDPR Art. 6(1)(f) — legitimate interests** applies
to the third-party processors involved in the fulfilment chain
when the operator binds them — the case-management / evidence-
pack store that carries the correlation record across the
lifecycle, the paging system that routes any manual-review page
on Article 22 concerns, and the outbound secure-delivery surface
that emits the response envelope to the subject. The operator has
a legitimate interest in operating a deterministic fulfilment
chain that discharges the Chapter III obligation and produces the
durable receipts the Article 5(2) accountability posture depends
on.

Special-category data (Art. 9) may be incidentally implicated
where the request concerns a data subject whose personal data
under processing includes Art. 9 categories (health, biometric,
racial or ethnic origin, political opinion, trade-union
membership, religious belief, sex-life). The fulfilment pack in
those cases carries the Art. 9 attributes exactly as the request
axis and the controller's holdings require (an access request
returns the Art. 9 data the controller holds on the subject; an
erasure request returns the deletion attestation over that data;
a portability request returns the Art. 9 data in the structured
data package). The lifecycle here does not itself extract Art. 9
conclusions or classify Art. 9 categories — it fulfils the
subject's request against the holdings the data-store owners
return.

## 3. Categories of data subjects and personal data

Data subjects:

- **Requesting data subjects** whose Chapter III rights the
  workflow fulfils, whose supplied contact channel is stored on
  the case record as `__subject_contact__` and referenced by
  `verify_identity` and `send_controller_response`.
- **Verification-surface holders** — the controller's declared
  sovereign IdP account-holders whose IdP-bound assertion the
  `verify_identity` step consumes for account-holder subjects, in
  their capacity as data subjects of the IdP.
- **Controller point-of-contact** named on the outbound response
  envelope, in an organisational-role capacity (data-protection
  officer or DSR-policy owner), whose work-email address appears
  on the response as the operator-side signatory.

Personal data:

- Subject contact channel (email address, postal address,
  sovereign IdP-bound identifier, or authenticated in-app account
  handle), stored on the case correlation record.
- Verification evidence (IdP assertion payload, or the out-of-
  band verification playbook's evidence record) held for the
  duration of the case plus the retention window recorded in §5.
- Fulfilment-pack content, which is the personal data the
  controller holds on the subject in the scope the request axis
  determines — for an access request the full Article 15(1)
  meta-information plus the subject-copy assembly, for an erasure
  request the deletion-attestation set, for a rectification
  request the applied-correction attestation set, for a
  restriction request the restriction-marker set, for a
  portability request the structured data package, for an
  objection request the cessation record or the overriding-
  legitimate-interest determination.
- Case correlation record: `__case_id__`, request-received
  timestamp, verification outcome, request-type classification,
  data-owner manifest, fulfilment-pack reference, response
  timestamp, response-deadline delta, and terminal outcome code.

## 4. Recipients

Recipients of the personal data the workflow emits:

- **Internal to the operator** — the case-management / evidence-
  pack store that carries the correlation record, the controller's
  DSR-policy owner (organisational role, not individual) for the
  response signatory, the paging system that routes any manual-
  review step on Article 22 concerns, and the operator's per-data-
  store owners whose stores hold the personal data the request
  concerns.
- **Downstream sibling playbooks** — none by default. The DSR
  lifecycle is subject-initiated against already-collected data;
  it does not fork sibling incident-notification playbooks. Where
  a DSR request incidentally surfaces a suspected personal-data
  breach on a data-store owner's return path (for example an
  erasure request the owner cannot fulfil because the store was
  compromised), the owner escalates through the operator's
  standard breach-notification chain, which is a separate
  workflow.
- **Requesting data subject** — the outbound response envelope
  emitted by `send_controller_response`, carrying the fulfilment-
  pack content scoped to the request axis under the Article 12
  modalities.
- **Downstream receiving controller** (Article 20(2) direct-
  transmission path where technically feasible and requested by
  the subject) — the structured data package the portability
  fulfilment emits.

Where a processor is involved (managed evidence-pack store,
paging vendor, secure-delivery surface for the response
envelope), a Data Processing Agreement (DPA) is in place under
GDPR Art. 28; the agreement itself lives outside the framework,
but the data-flow doc records the dependency.

## 5. Retention

- Case correlation record: retained for the operator's declared
  DSR-accountability window (typically five years, aligned to
  supervisory-authority information-order envelopes under
  Article 58(1)(a) and the Article 5(2) accountability posture)
  so a later regulator query against a fulfilled request can be
  answered from durable state. Enforced by evidence-pack expiry
  keyed on the case-closure timestamp plus the accountability-
  window offset.
- Subject contact channel: retained only for the case's active
  lifecycle plus the operator's declared retention window on the
  DSR-communication log (typically the same DSR-accountability
  window, minimising exposure). Subject opt-out of retention
  beyond the response window is honoured on request under the
  erasure hook in §7.
- Fulfilment-pack content: retained for the operator's declared
  DSR-accountability window as the audit-evident artifact of the
  fulfilment. An erasure fulfilment pack is a deletion-attestation
  record over the deleted data, not a copy of the deleted data.
- Verification evidence: retained for the case's active lifecycle
  plus a short verification-audit window (typically 90 days) so
  a challenge to the fulfilment can be adjudicated against the
  verification path, then purged. Sovereign-IdP-bound assertions
  are stored as opaque assertion identifiers, not as replayable
  credentials.

## 6. Cross-border transfers

**Default posture: no transfer.** All processing stays within the
EU/EEA when the controller runs the workflow on a sovereign-hosted
runtime with region-pinned processor endpoints and an EU-resident
subject-verification surface. The technical control that holds
this is the SecOps-NG sovereignty-first foundation (see
`docs/FOUNDATION.md`): compile-target artifacts default to EU-
resident processor bindings, the sovereign IdP integration point
resolves against an EU-resident IdP, and no public-cloud-AI call
is emitted on the outbound response leg.

Named transfer scenarios can arise depending on the operator's
bindings and the subject's location, scored in §8:

- The requesting subject is outside the EU/EEA (a subject
  temporarily abroad, or a non-EU resident whose personal data
  the EU-established controller holds). The outbound response leg
  to that subject is a transfer under GDPR Chapter V; §8 scores
  the Article 6(1)(c) legal-obligation ground for the operator's
  Chapter III fulfilment duty and the technical control (encryption
  in transit, EU-hosted mail transport on the operator side).
- The portability direct-transmission path (Article 20(2))
  targets a receiving controller outside the EU/EEA. The
  outbound transmission leg is a transfer under Chapter V; §8
  names the transfer instrument (adequacy where the receiving
  controller's country has an adequacy decision, otherwise the
  subject's Article 20(1) direct-hand-back path is preferred and
  the direct-transmission leg is scored under SCCs where the
  subject explicitly requests it).

## 7. Data subject rights

This IS the data-subject-rights workflow. Every right named
below is operationalised by the workflow itself, so the anchor is
`__case_id__` and the classify_request step, not a per-workflow
implementation note.

- **Access (Art. 15)** — routed as `__request_type__` = access.
  compile_fulfilment_evidence assembles the Article 15(1)
  meta-information block and the Article 15(3) subject-copy pack;
  send_controller_response emits the pack on or before the
  Article 12(3) deadline.
- **Rectification (Art. 16)** — routed as `__request_type__` =
  rectification. route_to_data_owners routes the correction
  request; compile_fulfilment_evidence assembles the applied-
  correction attestation; the Article 19 recipient-communication
  obligation is discharged on the per-owner acknowledgement
  envelopes.
- **Erasure (Art. 17)** — routed as `__request_type__` =
  erasure. Per-owner deletion attestation with per-owner
  Article 17(3) retention-exemption records where applicable.
- **Restriction (Art. 18)** — routed as `__request_type__` =
  restriction. record_outcome records the Article 18(3)
  subsequent-lifting-notification hook.
- **Portability (Art. 20)** — routed as `__request_type__` =
  portability. compile_fulfilment_evidence assembles the
  structured, commonly-used, machine-readable data package;
  send_controller_response emits it to the subject or, under
  Article 20(2), transmits it to the receiving controller where
  technically feasible.
- **Objection (Art. 21)** — routed as `__request_type__` =
  objection. Either a cessation record or an overriding-
  legitimate-interest determination.
- **Automated decision-making (Art. 22)** — classified at
  classify_request and routed to the operator's human-in-the-loop
  review surface as part of the objection lane. The lifecycle
  does not itself review the underlying automated decision.

The workflow inherits, as any workflow does, the meta-obligation
under Article 12: modalities (concise, transparent, intelligible,
clear-and-plain-language), the one-month response deadline
(extendable by two months under Article 12(3)), and the refusal-
with-remedy structure under Article 12(5)-(6) that names the
subject's onward remedies (Article 77 supervisory-authority
complaint; Article 79 judicial remedy).

## 8. Outbound personal-data transfer

Outbound legs the DSR lifecycle emits, each scored against GDPR
Chapter V:

- **send_controller_response → requesting subject** — outbound
  response envelope carrying the fulfilment-pack content to the
  subject's supplied contact channel. Destination class: data
  subject. Transfer mechanism: **no transfer** by default (EU-
  resident subject, EU-hosted secure-delivery transport); where
  the subject is in a third country, **adequacy (Art. 45)** where
  the country has an adequacy decision, otherwise **SCCs
  (Art. 46)** on the operator's secure-delivery processor plus
  supplementary measures (encryption in transit; encrypted
  attachment for the fulfilment pack where the subject's public
  key is available). EU-residency posture: EU-hosted delivery
  transport pinned on the operator's compile-target binding; a
  non-EU delivery-transport swap breaks the scoring and requires
  re-scoring. Data minimisation: the envelope carries the
  fulfilment-pack content scoped to the request axis only —
  meta-information for access, applied-correction record for
  rectification, deletion attestation for erasure, restriction
  marker for restriction, structured data package for
  portability, cessation record or overriding-legitimate-interest
  determination for objection.
- **send_controller_response → receiving controller (Art. 20(2)
  direct-transmission path)** — outbound portability transmission
  where the subject has requested direct transmission to another
  controller. Destination class: downstream receiving controller.
  Transfer mechanism: **no transfer** where the receiving
  controller is EU-resident; **adequacy (Art. 45)** where the
  receiving controller is in an adequacy-covered third country;
  **SCCs (Art. 46)** where the receiving controller is elsewhere
  and the subject has explicitly requested the direct-transmission
  leg despite the third-country target. EU-residency posture:
  the direct-transmission leg is preferred only where the
  receiving controller is EU-resident; a non-EU receiving
  controller triggers the Article 20(1) direct-hand-back path to
  the subject as the safer default unless the subject overrides.
  Data minimisation: the structured data package carries only the
  personal data the subject has provided to the controller and
  which the processing is based on consent under Art. 6(1)(a) /
  9(2)(a) or on a contract under Art. 6(1)(b).
- **record_outcome → operator evidence-pack store** — outbound
  persistence of the case correlation record to the operator's
  evidence-pack store. Destination class: processor bound to a
  Data Processing Agreement under Art. 28. Transfer mechanism:
  **no transfer** by default (EU-resident evidence-pack store);
  swapping to a non-EU-resident store breaks the scoring and
  requires re-scoring under Art. 46 with supplementary measures
  (encryption at rest with operator-held keys, minimisation of
  the correlation record on egress). Data minimisation: the
  correlation record carries the case-lifecycle metadata and the
  outcome code; it does not carry a copy of the fulfilment-pack
  content on the persistence leg (the fulfilment pack itself is
  stored on the same substrate under the same posture, but the
  correlation record's role is the timeline audit trail rather
  than a duplicate of the pack).

Cross-reference §6: the two named third-country scenarios
(subject outside the EU/EEA; portability direct-transmission to a
non-EU receiving controller) are the only outbound legs that
break the `no transfer` default; both are scored above under
Chapter V, so §6 remains consistent with §8.
