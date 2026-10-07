# dora_major_incident_reporting

CACAO v2 playbook for the DORA Chapter III major-ICT-related
incident reporting lifecycle a financial entity discharges to its
competent authority per DORA Regulation (EU) 2022/2554 Article 19. The
playbook operates the three-milestone reporting cycle upstream anchored
on the Art. 18 classification decision: detect-and-classify →
major incident? (not major → close-and-archive) →
notify-authority-initial (Art. 19(4)(a), 4h / 24h) →
notify-authority-intermediate (Art. 19(4)(b), 72h after the initial
notification) → notify-authority-final (Art. 19(4)(c), one month after
the intermediate report) → close-and-archive.

## Timeline

DORA Art. 19 imposes a distinct three-milestone reporting cycle on an
incident classified as **major** under Art. 18 (operationalised by
Commission Delegated Regulation (EU) 2024/1772). The time limits are
set by Art. 5 of Commission Delegated Regulation (EU) 2025/301, and
each milestone's clock runs from the one before it:

1. **Initial notification** — as early as possible, within **4 hours**
   of classification as major, and no later than **24 hours** from
   awareness (Art. 5(1)(a)); when the incident is classified as major
   more than 24 hours after awareness, within 4 hours of classification
   (Art. 5(2)). ITS content shape per Commission Implementing
   Regulation (EU) 2024/2956.
2. **Intermediate report** — within **72 hours** of the *submission of
   the initial notification* (Art. 5(1)(b)), not of classification; an
   updated intermediate report follows when regular activities have
   recovered.
3. **Final report** — no later than **one month** after the
   intermediate report, or after the latest updated intermediate report
   (Art. 5(1)(c)).

## Authority chain

The competent authority for DORA reporting is the operator's sectoral
supervisor — one of the three European Supervisory Authorities (EBA,
ESMA, EIOPA) via the national competent authority (NCA) chain
prescribed by the operator's sector. The operator's designated
authority chain is a compile-target configuration input, not a
hardcoded endpoint. The three ESAs receive aggregated reporting from
the NCAs; the operator files to its NCA.

## When to invoke this vs `playbook.incident_management@v1`

Both playbooks discharge regulator-notification chains against a
significant / major incident, but they target different regimes and
different authority chains:

- `playbook.dora_major_incident_reporting@v1` (this playbook) — the
  DORA-flavoured lane for financial entities in scope of DORA. Fires
  on the Art. 18 classification decision and drives the three DORA
  Art. 19 milestones (4h/24h, 72h, one month) to the ESA / NCA
  authority chain against the Commission ITS content shape.
- `playbook.incident_management@v1` — the NIS2-flavoured lane for
  essential and important entities in scope of NIS2. Fires on the
  NIS2 Art. 23 significant-incident threshold and drives the NIS2
  Art. 23 milestones (24h early warning, 72h notification, one-month
  final report) to the CSIRT / competent-authority chain.

A single operator may be in scope of **both regimes** simultaneously
(most large EU financial entities are). In that case the two
playbooks fire in parallel on the same underlying incident against
different authority chains, and the operator files separate
notifications to separate authorities. Where the incident also
involves personal data, the GDPR Art. 33 / 34 breach-notification
chain fires in parallel as a third lane, discharged by the existing
breach-notification cluster (`playbook.data_exfil@v1`,
`playbook.identity_compromise@v1`,
`playbook.ransomware_containment@v1`,
`playbook.incident_management@v1`).

## When to invoke this vs `playbook.dora_tlpt_programme@v1`

`playbook.dora_tlpt_programme@v1` is the DORA **Chapter IV**
testing-programme discipline (Art. 24 general testing requirements
+ Art. 26 threat-led penetration testing). This playbook is the
DORA **Chapter III** reporting discipline. The two are separate
Chapters covering separate obligation surfaces — one is a cadenced
testing programme, the other is an incident-driven reporting cycle.
They share no runtime touchpoint.

## Status

`maturity: stable`, `content_version` 1.0.0. All five action steps bind
a deterministic primitive under `primitives/` through
`x_secops_ng.core_body`, each executed directly by
`tests/playbooks/dora_major_incident_reporting/test_primitives.py`, and
the three reference targets emit those calls; the walkthrough is
`docs/cookbook/dora_major_incident_reporting.md`. The graduation
checklist recomputes green: tier A, 5 of 5 real bindings, zero
placeholder bodies, zero blank predicates, zero schema errors,
three-target goldens.

| Step | Primitive |
|---|---|
| detect-and-classify | `classification.classify_major_incident` |
| notify-authority-initial | `notification.compose_initial_notification` |
| notify-authority-intermediate | `notification.compose_intermediate_report` |
| notify-authority-final | `notification.compose_final_report` |
| close-and-archive | `archive.compose_cycle_archive` |

Decisions the primitives fix:

- **The classifier encodes the Art. 8(1) combination rule of Commission
  Delegated Regulation (EU) 2024/1772, not its numeric thresholds.** An
  incident is major when critical services are affected *and* either
  malicious unauthorised access that may cause data loss was identified
  or two or more materiality thresholds are met; critical services are
  mandatory on both limbs. Whether each criterion's threshold is met is
  the operator's classification policy's determination and the
  primitive's input — the RTS threshold rule pack is deferred to its own
  card, as the shared Art. 19 report builder already records. Recurring
  incidents aggregate only with two or more occurrences within six
  months and the same apparent root cause.
- **The three submissions reuse the existing Art. 19 report builder**
  (`compilers/_shared/evidence/dora_art19_report.py`) rather than
  re-implementing the evidence schema. The primitives add the
  JSON-native boundary, the chain between milestones (each is composed
  from its predecessor's output, so none can be skipped or reordered),
  each milestone's `due_at` and `within_deadline`, and the gate that a
  non-major incident is never reported.
- **Deadlines follow Delegated Regulation (EU) 2025/301 Art. 5:**
  initial — the earlier of 4 hours after classification and 24 hours
  after awareness, or 4 hours after a classification made more than
  24 hours after awareness; intermediate — 72 hours after the initial
  notification was submitted; final — one calendar month after the
  intermediate report, with the end-of-month clamp. The optional
  Art. 5(4) weekend and bank-holiday extension is not applied, so the
  deadline is the strict one every entity can rely on.
- **The archive** is always emitted. It refuses a major incident without
  its complete, linked chain and a non-major incident with any report
  attached, and records each milestone's deadline outcome.

Choices settled at the wire:

- **The not-major gate exists.** The detect-and-classify step promised a
  branch the topology did not have; an `if-condition` on
  `__incident_major__`, extracted from `__classification__`, now routes
  a non-major incident straight to close-and-archive. The notification
  primitives still refuse a non-major incident, so the gate and the
  primitives agree.
- **Two deadlines were corrected against the regulation text.** The
  intermediate report had been timed from classification, and the
  initial notification ignored Art. 5(2); both now follow Art. 5, so an
  on-time report is never recorded as overrun.
- **The archive takes the three reports as separate inputs**, each unset
  on the not-major branch (the n8n trigger supplies `""`), rather than
  a list the topology could not assemble.
- **The contract grows from 7 to 34 variables:** 21 adapter inputs
  (the classification criteria and instant, per-milestone submission
  instants, impact, mitigation and acknowledgement references, the
  awareness instant, the run URL, cross-regime references and the run
  context), one envelope per step, the gate boolean, and the five
  existing identifiers, now extracted from the envelopes.

Submission-adapter and authority-channel bindings, and the per-cycle
KPIs, remain EXTEND work.

## Steps

1. **detect-and-classify** — evaluate the incident against the Art. 18
   classification criteria (Commission Delegated Regulation (EU)
   2024/1772) and emit the classification-decision record.
2. **major incident?** — the gate: a major incident files the three
   reports; a non-major one goes straight to close-and-archive, so the
   dated decision still closes the audit-evident chain.
3. **notify-authority-initial** — package the initial notification
   against the ITS content shape (Commission Implementing Regulation
   (EU) 2024/2956) and dispatch to the competent authority. Due within
   4 hours of classification / 24 hours from awareness.
4. **notify-authority-intermediate** — package the intermediate report
   against the ITS content shape and dispatch. Due within 72 hours of
   the initial notification's submission.
5. **notify-authority-final** — package the final report (root-cause
   analysis, final impact figures, remediation, lessons learned,
   action plan, residual-risk statement) and dispatch. Fires no later
   than one month after the intermediate report.
6. **close-and-archive** — compose the dated cycle-archival record
   referencing the classification decision, the three submissions,
   the authority acknowledgements, and any cross-regime notification
   chains (NIS2 Art. 23, GDPR Art. 33-34). The archival record is
   the audit-evident cycle closure.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.dora_major_incident_reporting@v1`).
- `mappings.yaml` — outbound overlay (OSCAL controls, D3FEND stub,
  OCSF stub, DORA Art. 19 primary, NIS2 Art. 23 cross-regime sibling,
  GDPR Art. 33-34 cross-regime sibling).
- `primitives/` — the deterministic primitives the five action steps
  bind; see Status.

## Goal links

- **G-01** — content coverage: dedicated DORA-flavoured major-ICT-
  related-incident reporting playbook closing the Chapter III surface
  upstream of the existing NIS2 Art. 23-flavoured
  `incident_management` playbook; advances the target of ≥ 25 CACAO
  v2 playbooks.
- **G-02** — regulatory-graph closure: DORA Art. 19 (4)(a)/(b)/(c)
  and Art. 18(1) primary anchors, with sibling references to NIS2
  Art. 23(4)(b) and GDPR Art. 33 for the cross-regime parallel-
  notification relationship.
