# GDPR data flow — ai_human_oversight

Per-workflow GDPR data-flow entry for the `ai_human_oversight`
playbook (`playbook.ai_human_oversight@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/ai_human_oversight/`](../../playbooks/ai_human_oversight/).

---

## 1. Purpose

Evidence that human oversight of a high-risk AI system was not merely
assigned but actually exercised, as EU AI Act Article 14 requires.
Concretely: record who held oversight of a named deployment during a
review window and with what delegated authority; record that each
overseer was briefed on that specific system's capacities, limitations
and interpretation aids; record the disposition of each output flagged
for review; record any exercise of the power to decline, disregard,
override or halt; and emit the dated cycle record joining them.

The personal data is incidental to a compliance record. The workflow
makes no decision about anyone — it documents that a human was in a
position to intervene in decisions the *AI system* makes, and whether
they did.

## 2. Lawful basis

Primary: **Art. 6(1)(c) — compliance with a legal obligation.** The
records exist because Regulation (EU) 2024/1689 compels them: Art. 14(4)
requires the overseer to be capable, Art. 14(5) requires two-person
verification for Annex III(1)(a) biometric identification, and Art. 26(2)
requires the assignment these records evidence. The operator has no
discretion over whether to hold them.

Secondary: **Art. 6(1)(f) — legitimate interests**, for any detail
retained beyond the statutory minimum for the operator's own assurance.
The Art. 21 objection right in §7 attaches to that margin only.

**Special-category data (Art. 9):** not processed by this workflow, but
the boundary needs care. Where the overseen system performs remote
biometric identification (Annex III point 1(a)), the *system* processes
biometric data, and the Art. 14(5) branch records that two named people
verified an identification. The verification record references the
identification event; it does not carry the biometric template. Keep it
that way — recording the underlying biometric in an oversight log would
convert a compliance record into a special-category processing surface
with no lawful basis established here.

## 3. Categories of data subjects and personal data

| Data subject category | Personal data in this workflow |
|---|---|
| **Rostered overseers** — the operator's staff assigned under Art. 26(2) | Name or role identifier, the authority delegated to them, per-deployment briefing records and attestation dates, and the shift or window they held |
| **Intervening overseers** — a subset of the above | The intervention record: who acted, when, which of decline / disregard / override / halt, and the stated basis |
| **Art. 14(5) verifiers** — for Annex III(1)(a) deployments | Both named verifiers per confirmed identification, recorded separately, plus their competence and authority basis |
| **Persons affected by the reviewed outputs** | Reference only. A review disposition points at the flagged output by identifier; the person the output concerns is not enumerated in the oversight record, and should not be |

The last row is the one to hold the line on. An oversight log that
copies the content of every reviewed decision would accumulate a
shadow record of everyone the AI system touched. The record needs the
disposition and the reference, not the payload.

## 4. Recipients

- **Internal** — the operator's governance function (roster and
  authority records), the evidence store (cycle records), and the
  operator's Art. 26(5) monitoring surface, which consumes
  interventions as signals about the system.
- **The provider of the AI system** — indirectly. An intervention is
  evidence about system behaviour and feeds the deployer's Art. 26(5)
  duty to inform the provider, which in turn feeds the provider's
  Art. 72 post-market monitoring. What travels is the system-behaviour
  signal, not the overseer's identity.
- **Market-surveillance authority** — on request, as part of the
  evidence that oversight was exercised. A public authority acting
  under statutory powers, not a processor.

No external processor is invoked by the workflow. Where the roster,
briefing store or evidence store is a third-party service, that
provider is an Art. 28 processor and the dependency is the operator's
to record.

## 5. Retention

Bound to the deployment, not to a fixed clock: the oversight records
are retained for as long as the high-risk AI system is in service plus
the operator's evidentiary tail, because they are the evidence that
Art. 14 was satisfied while it ran. Where the same deployment falls
under the Art. 26(6) log-retention duty discharged by
`playbook.eu_ai_act_deployer_obligations@v1`, that period is a floor
for the joined cycle record — at least six months, and a period
appropriate to the intended purpose.

Briefing attestations follow the operator's training-records retention,
since they double as evidence for `control.training_attestation@v1`.

Enforcement is operator-side. The framework declares the retention
contract and the dated record stating which period was applied; it
ships no store and enforces no TTL.

## 6. Cross-border transfers

**No transfer**, by default and by construction. Every recipient in §4
is EU-resident: the operator's own governance and evidence surfaces,
the provider of a high-risk AI system placed on the Union market, and a
Member State market-surveillance authority. The EU-resident
inference-endpoint guard in the shared compiler layer holds the posture
for any compiled target, and the workflow makes no public-cloud-AI
call.

The swap that would break this scoring is the operator hosting the
roster, briefing store or evidence store outside the EU/EEA, at which
point the §3 records leave the Union and the leg needs re-scoring under
Art. 46 with supplementary measures. That is an operator binding, not a
framework default.

## 7. Data subject rights

- **Access (Art. 15)** — an overseer's data sits in the roster,
  briefing and intervention records, all keyed on the deployment
  identifier and review window, so a Subject Access Request resolves by
  the windows the person was rostered for.
- **Rectification (Art. 16)** — applies to roster and briefing
  attributes that may be recorded wrongly or go stale. A correction is
  a new record; the superseded one is retained because it evidences who
  held oversight at the time.
- **Erasure (Art. 17)** — substantially restricted while the deployment
  is in service. The records exist under Art. 6(1)(c), so Art. 17(3)(b)
  applies and the retention hook in §5 is the operative mechanism
  rather than on-request deletion.
- **Objection (Art. 21)** — not available against the Art. 6(1)(c)
  records. Available against any Art. 6(1)(f) margin per §2, handled by
  dropping that margin while the statutory record stands.
- **Automated decision-making (Art. 22)** — the relationship deserves
  stating precisely, because this workflow sits closer to Art. 22 than
  most. The workflow makes **no** automated decision; it records human
  review of decisions the overseen system makes. Human oversight under
  Art. 14 is in fact one of the mechanisms by which a deployer can
  ensure a decision is not based *solely* on automated processing. But
  the two duties are not interchangeable: Art. 22 is a right the data
  subject exercises, Art. 14 is a standing obligation that operates
  whether or not anyone objects, and satisfying Art. 14 does not
  discharge an Art. 22 request. This playbook implements no Art. 22
  response path; it produces the evidence that a human was in the loop.
