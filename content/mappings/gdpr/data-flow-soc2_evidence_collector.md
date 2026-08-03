# GDPR data flow — soc2_evidence_collector

Per-workflow GDPR data-flow entry for the `soc2_evidence_collector`
cookbook playbook (`playbook.soc2_evidence_collector@v1`). Filled in
against [`_data-flow-template.md`](./_data-flow-template.md). Together
the seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/soc2_evidence_collector/`](../../playbooks/soc2_evidence_collector/).

---

## 1. Purpose

The workflow exists to tell an operator, before an auditor asks, which
AICPA Trust Services Criteria their existing evidence already supports
and which are uncovered. On each run it reads the criteria crosswalk
under `content/mappings/soc2/`, joins the evidence *references* other
playbooks emitted during the assessment window onto the criteria those
references claim to support, scores each criterion covered /
draft-backed / uncovered, and emits one dated readiness document naming
the gap and a role-shaped owner. The purpose is bounded to producing
that coverage picture: the workflow performs no assessment of its own,
issues no audit opinion, and does not retain the underlying evidence.

## 2. Lawful basis

**Art. 6(1)(f) — legitimate interests.** The operator has a legitimate
interest in knowing the state of its own control evidence before
committing to an audit, and in directing remediation at the criteria
that are actually uncovered rather than at a guess. The processing is
minimal by construction (see § 3: it handles identifiers of artifacts,
not their contents), so the balancing test resolves in favour of the
interest without a lesser-intrusive alternative being available —
there is no way to report coverage without reading which artifacts
exist.

Secondary basis where the operator is a regulated entity and the same
evidence surface is compelled: **Art. 6(1)(c) — legal obligation**.
No special-category data (Art. 9) is processed; the workflow never
reads artifact bodies, only their identifiers, streams and criteria
claims.

## 3. Categories of data subjects and personal data

**Data subjects: none directly.** This workflow is deliberately one
step removed from personal data. Its inputs are:

- criteria atoms from the crosswalk — regulatory text and mapping ids,
  no personal data;
- evidence *references* — an `artifact_id`, a `stream` name, and the
  `soc2:` criteria the artifact claims to support. **Not the artifact
  bodies.** Whatever personal data an upstream artifact contains stays
  in that artifact and in its own stream's ROPA entry;
- an `owner_role` — a **role**, validated against a lower-case,
  role-shaped pattern that rejects a personal name (the test
  `test_owner_is_a_role_never_a_person` pins this).

So the emitted attestation contains no personal data, and the residual
category is indirect only: an `artifact_id` is a pointer that could, in
combination with the producing stream, lead to a record about a person.
That is a pointer to personal data, not personal data, and it is
recorded here rather than dismissed.

## 4. Recipients

Internal only, by default. The attestation is written wherever the
operator's compile target puts it — the framework ships no transport.
Its intended readers are the named owner role, the operator's internal
compliance function, and, if the operator chooses to share it, a
prospective SOC 2 practitioner. The framework performs no disclosure:
nothing in this playbook transmits the document anywhere, which is why
§ 8 is not applicable.

No sub-processors are engaged by this workflow. It makes no network
calls of any kind — the primitives are pure and offline, with no clock
reads, no HTTP, and no LLM.

## 5. Retention

The framework retains nothing. The attestation carries `captured_at`
and a deterministic `attestation_id`, and the operator's evidence
pipeline decides how long the document is kept, under whatever
retention its own stream declares. Because the document holds no
personal data (§ 3), no personal-data retention clock starts here.

The pointers it does contain (`artifact_id` values) become stale
harmlessly: if the referenced artifact has been aged out under its own
stream's retention, the pointer resolves to nothing and the criterion
simply reads as unsupported on the next run.

## 6. Cross-border transfers

**Not applicable.** The workflow makes no network calls and ships no
transport, so there is no transfer — cross-border or otherwise — caused
by this playbook. Where a document is stored, and in which
jurisdiction, is determined by the operator's deployment and is
recorded against that deployment rather than here.

## 7. Data subject rights

**Indirect, and served at the upstream artifact.** Because the
attestation contains no personal data, an Art. 15 access request or an
Art. 17 erasure request cannot be satisfied *from* this document —
there is nothing about a person in it to disclose or erase.

Where a request concerns a record the attestation points at, it is
served against the upstream artifact and its own stream's ROPA entry.
Erasure upstream needs no action here: the pointer becomes unresolvable
and the criterion reads as unsupported on the next run, so this
playbook cannot keep an erased record alive by reference. Requests are
routed through the operator's own procedure — see
[`data_subject_rights`](../../playbooks/data_subject_rights/), the
playbook that owns the DSR intake and fulfilment lifecycle.

## 8. Outbound personal-data transfer

**Not applicable.** The workflow transmits nothing: it emits a document
into the operator's own pipeline and makes no outbound call. There is
therefore no outbound personal-data transfer to record, and no
recipient, safeguard or transfer mechanism to name.
