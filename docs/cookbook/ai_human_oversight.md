# ai_human_oversight — cookbook walkthrough

Practitioner walkthrough of the **EU AI Act Article 14 human-oversight
lifecycle**, shipped as
[`playbook.ai_human_oversight@v1`](../../content/playbooks/ai_human_oversight/).
It is aimed at the operator who has already assigned human oversight of a
high-risk AI system and now has to show that oversight was *exercised*.

> This walkthrough is community reference material. It asserts that the
> named SecOps-NG artifacts exercise the Art. 14 lifecycle in practice;
> it is **not** a legal interpretation of Regulation (EU) 2024/1689.
> Whether a system is high-risk, and whether your organisation is the
> provider or the deployer, are determinations you make on your own
> legal surface.

## 1. Assignment is not exercise

This is the whole reason the playbook exists, and it is the one thing to
carry away if you read nothing else.

| | article | question | playbook |
|---|---|---|---|
| **assignment** | 26(2) | is someone named, competent, trained, empowered, supported? | [`eu_ai_act_deployer_obligations`](eu_ai_act_deployer_obligations.md) |
| **exercise** | 14 | did they actually review, intervene, and leave evidence? | **this one** |

A named overseer who never reviewed anything satisfies Art. 26(2) on
paper and Art. 14 not at all. Only the second leaves evidence, and only
the second is what a market-surveillance authority can inspect after the
fact.

The two playbooks join on `__deployment_id__`, so an assignment record
and the oversight cycles run under it resolve to one key.

## 2. Source of truth

```
content/playbooks/ai_human_oversight/        # this playbook
content/mappings/eu_ai_act/article-14-human-oversight.yaml   # inbound anchor

content/metrics/eu_ai_act_oversight_intervention_rate.yaml            # § 6
content/metrics/eu_ai_act_oversight_intervention_latency_hours.yaml   # § 6

examples/n8n/ai_human_oversight/             # compiled worked examples
examples/temporal/ai_human_oversight/
examples/langgraph/ai_human_oversight/
```

The CACAO playbook is canonical. The three example directories are
byte-deterministic regenerations of it, pinned by
`tests/examples/ai_human_oversight/test_golden.py`.

## 3. The loop

```
establish_oversight_roster
    → brief_oversight_personnel
        → review_flagged_decisions
            → record_intervention
                → emit_oversight_evidence
```

Linear, five nodes, **no conditional edges**. The conditionality Art. 14
contains lives in state rather than topology — see § 5.

| step | article | produces |
|---|---|---|
| `establish_oversight_roster` | 14(4) | `__oversight_roster_id__` |
| `brief_oversight_personnel` | 14(4)(a)–(c) | `__briefing_record_id__` |
| `review_flagged_decisions` | 14(4), 14(5) | `__review_disposition_id__`, `__biometric_two_person_verification__` |
| `record_intervention` | 14(4)(d)–(e) | `__intervention_record_id__`, `__intervention_type__` |
| `emit_oversight_evidence` | 14(1) | `__oversight_evidence_id__` |

### The roster's authority limb is the one that gets skipped

Art. 14(4)(d)–(e) require the overseer to be able to decline use,
disregard or override output, and interrupt operation. A roster entry
naming someone **without recorded delegated authority produces an
overseer who cannot lawfully oversee** — and, importantly for § 6, one
whose intervention rate will read as zero. If your intervention rate is
flat at zero, check the roster before you check the overseers.

## 4. A review that found nothing is still evidence

`record_intervention` always runs, and emits a **nil record** where the
window produced no intervention. Most cycles produce reviews and no
interventions; that is the normal, healthy case.

This matters twice over:

- **For the evidence.** An empty intervention set with no review record
  is indistinguishable from no oversight at all.
- **For the metrics.** The nil record is excluded from the intervention
  count but its parent review stays in the denominator. Count records
  instead of exercises and every window scores 1.0, measuring nothing.

## 5. Two things easy to lose

**`__intervention_type__` is a separate value from the intervention
record.** Art. 14(4)(d)–(e) name four distinct exercises — decline to
use, disregard the output, override or reverse it, interrupt operation.
A halt is not a disregard. They all flow into the same evidence step, so
they are carried as state rather than as branches, but an aggregate that
collapses them tells a reviewer nothing about severity.

**Art. 14(5) is a conditional field, not a conditional edge.**
`__biometric_two_person_verification__` is populated only on Annex III
point 1(a) remote biometric identification deployments and is empty
everywhere else. Two properties it exists to preserve:

- The verification requires **two separate natural persons**. One
  overseer confirming twice does not satisfy it.
- Where the narrow law-enforcement exemption is relied on, the record
  must name the **Union or national legal basis actually relied on** —
  not merely a flag that an exemption was taken.

## 6. Metrics — and why they ship as a pair

Two catalog entries, and neither is safe to read alone.

### `kpi.eu_ai_act_oversight_intervention_rate@v1`

Share of reviewed decisions on which an Art. 14(4)(d)–(e) power was
exercised. It exists to detect **rubber-stamping** — an oversight
function that reviews steadily and never once uses its authority. That
is the specific Art. 14 failure mode, and it is invisible to any measure
of assignment or review volume, both of which look healthy while it
happens.

**The direction is not monotone, and the catalog entry says so.** Higher
is better only across the low end: the move from zero to a small non-zero
rate is the move from oversight that never intervenes to oversight that
does. Above the floor the reading inverts — a high and rising rate is
evidence the *AI system* is degrading, not that oversight improved. The
indicator deliberately refuses to score that direction rather than
letting a dashboard imply "more interventions = better oversight".

Thresholds are **floors** (0.02 / 0.005 / 0), entered by falling below.
Where nothing was reviewed the headline is *undefined*, not zero —
scoring an empty window as a breach would fire the rubber-stamping alarm
at an operator whose system produced nothing reviewable.

### `kri.eu_ai_act_oversight_intervention_latency_hours@v1`

Hours from a decision entering the review queue to the intervention being
recorded, aggregated as **p95**. Where the KPI asks whether oversight is
exercised at all, this asks whether it is exercised in time to matter.

**Latency on a halt is the reading that matters most**, because a halt is
the only exercise whose value decays to nothing once the output has been
acted on. A disregard recorded late still corrects the record; a halt
recorded late prevented nothing. Both the formula and the reference
visualisation slice by intervention type for that reason.

**The 8 / 24 / 72-hour bands are not law.** Art. 14 sets no clock — it
requires oversight to be possible and effective and says nothing about
elapsed time, unlike the statutory Art. 73(2)–(4) bounds that
`kri.eu_ai_act_report_clock_margin_days@v1` measures against. Eight hours
is sized to one working day; re-derive it from how fast the overseen
system's output takes effect.

### Why neither works alone

Reviews with no intervention are **excluded** from the latency metric.
Including them at zero would drive it toward zero in exactly the
rubber-stamping case the KPI exists to catch — so the two indicators
would look healthy for the same wrong reason. Read together, an idle
oversight function shows up as a floor breach on the rate even while the
latency looks perfect.

## 7. Compiling it

```bash
PYTHONPATH=. python -m tools.compile \
    content/playbooks/ai_human_oversight/playbook.cacao.json \
    --target n8n --out /tmp/workflow.n8n.json
```

Worked examples for all three targets ship in-tree, each with its own
README and `regenerate.sh`:

- [n8n](../../examples/n8n/ai_human_oversight/) — import
  `workflow.n8n.json`; inactive by default.
- [Temporal](../../examples/temporal/ai_human_oversight/) — oversight is
  a standing duty on a cadence, so the roster and briefing seams outlive
  any single execution.
- [LangGraph](../../examples/langgraph/ai_human_oversight/) — linear
  five-node graph, zero conditional edges.

Start on n8n. It is the only target that preserves control flow and
imports without writing Python.

## 8. Operator customisation points

Adapter-bound surfaces the framework declares and never ships:

- **Oversight roster / rota surface** — read and written at
  `establish_oversight_roster`. The framework ships no personnel
  directory.
- **Briefing record** — the Art. 14(4)(a)–(c) competence evidence.
- **Flagged-decision queue** — the review surface, and the source of the
  queue-entry timestamp the latency KRI starts its clock from. Poor
  instrumentation here shows up as an excluded count, not a clean p95.
- **Intervention log.**
- **Evidence store** — where the dated cycle artifact lands.

## 9. What this cookbook does not cover

- **Art. 14(1) and 14(3)(a)** — the provider's duty to design oversight
  measures *into* the system. A deployer-side playbook cannot put a stop
  button into someone else's product; the mapping records the duty and
  binds no control.
- **Art. 26(2) assignment** — see
  [`eu_ai_act_deployer_obligations`](eu_ai_act_deployer_obligations.md).
- **GDPR Art. 22.** Art. 14 oversight is one mechanism by which a
  decision avoids being based *solely* on automated processing, but
  Art. 22 is a right the data subject exercises while Art. 14 is a
  standing duty operating regardless. Satisfying one does not discharge
  the other, and this playbook implements no Art. 22 response path.

## 10. References

- Regulation (EU) 2024/1689 (EU AI Act) — [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2024/1689/oj):
  Art. 14(1) oversight, Art. 14(3)(a) provider design measures,
  Art. 14(4)(a)–(e) the capability set, Art. 14(5) biometric two-person
  verification, Art. 26(2) deployer assignment, Annex III(1)(a) remote
  biometric identification.
- Regulation (EU) 2016/679 (GDPR) — [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj):
  Art. 22 automated individual decision-making.
- OASIS CACAO v2.0 — workflow step types and the `x_` extension
  namespace this artifact uses.
