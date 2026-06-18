# GDPR data flow — detection-engineering

Per-workflow GDPR data-flow entry for the `detection-engineering`
cookbook playbook (`playbook.detection_engineering@v1`). Filled in
against [`_data-flow-template.md`](./_data-flow-template.md). Together
the seven sections below form the Art. 30 Record of Processing
Activity entry for this workflow.

Workflow source of truth:
[`content/playbooks/detection-engineering/`](../../playbooks/detection-engineering/).

This entry is the per-workflow ROPA record for a **content-routing
workflow** — its payload is candidate detection rules and the
verdicts / shipped-status / effectiveness-metric snapshots produced
as those rules move through the `propose → review → ship → measure`
lifecycle. The framework treats `__rule_id__`, `__rule_version__`,
and `__proposal_rationale__` as role-shaped opaque strings produced
by the operator's detection store and review process; they describe
detection content, not data subjects. The workflow is therefore
**out of scope for GDPR processing**: no personal data of a natural
person is processed, persisted, or emitted on the lifecycle path.
Each section below records the per-section consequence of that
out-of-scope finding so the F-GD-02 SKELETON guard has a coverage
entry to assert against and so a future operator extension that
introduces personal data on this path (for example, attaching the
proposer's identity to the rule-proposal envelope) has a documented
delta to declare.

---

## 1. Purpose

The workflow exists to move a candidate detection rule
deterministically through four states — propose, review, ship,
measure — so the operator's detection store records each
rule-version's lifecycle decisions and so the F-CP-06 effectiveness
evidence stream can consume the per-rule-version effectiveness
snapshot emitted by the `measure` state. The processed artifacts
are detection content (rule identifiers, version labels, peer-review
verdicts, shipped status, effectiveness-metric snapshots shaped per
`schemas/evidence/rule-effectiveness-snapshot.schema.json`) and the
rationale text the proposer attached to a candidate rule. None of
these are personal data of a natural person.

The workflow does not ingest, route, or persist subject-identifiable
attributes (no user identifiers, no email addresses, no IPs, no
user-agent strings, no per-subject behavioural records). The
effectiveness snapshot the `measure` state emits is shaped per
rule-version, not per subject; its `source_data` field references
an OCSF class identifier (the *shape* of the data the rule queries
against in production), not subject-level records.

## 2. Lawful basis

**Out of scope: no personal data processed in this workflow.**

GDPR Art. 6 lawful-basis selection is not engaged because the
workflow's payload — rule identifiers, version labels, review
verdicts, shipped-status flags, and per-rule-version
effectiveness-metric snapshots — does not constitute personal data
of an identified or identifiable natural person under Art. 4(1).
`__rule_id__`, `__rule_version__`, and `__proposal_rationale__` are
role-shaped opaque strings produced by the operator's detection
store and review process; they describe detection content, not
data subjects.

If a future operator extension binds subject-identifiable attributes
to the rule-proposal envelope (for example, attaching the proposer's
work-email address to `__proposal_rationale__`, or pinning the
effectiveness snapshot to a per-subject telemetry slice rather than
an OCSF class shape), this section must be revised to declare the
operator-side primary lawful basis under Art. 6(1) — typically
**Art. 6(1)(f) legitimate interests** for the maintainer's interest
in attributing rule authorship, with the standard balancing test
recorded. Until that extension lands, this workflow stays out of
scope and the F-GD-02 SKELETON guard records the out-of-scope
declaration as the lawful-basis coverage entry.

Special-category data (Art. 9) cannot be incidentally observed —
the workflow does not touch subject telemetry on any of its four
lifecycle states.

## 3. Categories of data subjects and personal data

**Out of scope: no personal data processed in this workflow.** No
categories of data subjects are processed.

The artifacts on the lifecycle path are detection-content
identifiers and review verdicts — `__rule_id__` (stable identifier
assigned by the operator's detection store), `__rule_version__`
(version label), `__proposal_rationale__` (short free-text
rationale describing the threat addressed, detection gap closed,
or ATT&CK technique bound), `__review_verdict__` (one of
`approved`, `changes_requested`, `rejected`), `__ship_status__`
(one of `production`, `staged`, `withdrawn`), and
`__effectiveness_snapshot_id__` (SHA-256 hex digest of the
effectiveness snapshot the `measure` state emits). None of these
identify or render identifiable a natural person.

If a future operator extension attaches identity attributes to the
proposal envelope or the review record (proposer email, reviewer
identity, requestor's organisation), this section must enumerate
the resulting categories explicitly per Art. 30(1)(c).

## 4. Recipients

**Out of scope: no personal data processed in this workflow.** No
recipients of personal data are engaged.

The downstream recipients of the workflow's *content* artifacts are
internal pipelines, not Art. 30(1)(d) recipients of personal data:
the operator's detection store consumes the `ship` state's
production-status assertion; the F-CP-06 effectiveness evidence
stream consumes the per-rule-version effectiveness snapshot emitted
by the `measure` state. Both of these are framework-internal
content paths and operate on the rule-version / metric shape, not
on subject records.

The framework does not select an external processor on this path.
The detection store is resolved at the compile target's config
layer (sovereign-stack constraint — the framework ships no default
detection store). If the operator binds a third-party detection
store or metric sink, the DPA dependency is recorded against that
binding in the operator's own ROPA — not against this workflow,
which has no personal-data payload to transfer.

## 5. Retention

**Out of scope: no personal data processed in this workflow.** No
storage-limitation period under Art. 5(1)(e) is engaged because
the persisted artifacts are detection-content records, not personal
data.

The workflow does persist content: the rule-proposal envelope is
written to the operator's detection store on `propose`, the review
verdict is recorded against the rule-version on `review`, the
production-status flag is set on `ship`, and the effectiveness
snapshot is sunk into the operator's configured metric sink on
`measure`. These are content artifacts and follow the operator's
detection-content lifecycle policy (typically: retain as long as
the rule-version is in scope of the detection programme; archive
on `withdrawn`). The retention mechanism for *those* artifacts is
the detection store's lifecycle policy, not a Chapter II personal-
data retention control.

If a future operator extension attaches subject-identifiable
attributes to any of the persisted records, this section must
declare the GDPR retention period and the technical mechanism
that enforces it.

## 6. Cross-border transfers

**Out of scope: no personal data processed in this workflow.**
Chapter V is not engaged because there is no personal-data payload
to transfer.

The content artifacts (rule-version envelopes, review verdicts,
effectiveness snapshots) flow only between framework-internal
pipelines and the operator-configured detection store and metric
sink. The operator's choice of detection store or metric sink is
the operator's sovereignty decision; this workflow does not invoke
a third-country processor on its critical path and does not depend
on a public-cloud-AI call to make any of the four state transitions.

If a future operator extension introduces a personal-data attribute
into the rule-proposal envelope and the operator's detection store
or metric sink is hosted outside the EU/EEA, this section must
declare the transfer instrument (adequacy decision / SCCs / BCRs /
derogation) and any supplementary measures.

## 7. Data subject rights

**Out of scope: no personal data processed in this workflow.**
Art. 12–22 rights are not engaged because no natural person is
identified or identifiable from the workflow's payload.

- **Access (Art. 15)** — not applicable; no subject's data is held.
- **Rectification (Art. 16)** — not applicable; no
  subject-supplied attributes are stored.
- **Erasure (Art. 17)** — not applicable; the rule-version
  lifecycle records are detection content, not subject records.
- **Objection (Art. 21)** — not applicable; no Art. 6(1)(f)
  processing is engaged.
- **Automated decision-making (Art. 22)** — not applicable; the
  review verdict and shipped-status decisions act on detection
  content, not on a natural person, and produce no legal or
  similarly significant effect on a subject.

If a future operator extension binds subject-identifiable
attributes to the lifecycle, this section must describe how the
extended workflow accommodates each engaged right.
