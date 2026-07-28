# ai_human_oversight

**Status:** SKELETON · **Stable id:** `playbook.ai_human_oversight@v1`

## Overview

The deployer-side EU AI Act **Article 14 human-oversight loop** — the
cycle an oversight function actually runs once oversight of a high-risk
AI system has been assigned. It fires on the operator's oversight
cadence for a deployment in service, and on the assignment edge handed
over by `playbook.eu_ai_act_deployer_obligations@v1`. Inputs are the
oversight roster, the provider's Art. 13 instructions for use, and the
queue of outputs flagged for review; the artifact produced is a dated
cycle-evidence record joining the roster, the briefings, the review
dispositions and any interventions.

Five steps: `establish_oversight_roster` → `brief_oversight_personnel`
→ `review_flagged_decisions` → `record_intervention` →
`emit_oversight_evidence`.

The distinction the whole playbook turns on: **Art. 26(2) requires
oversight to be *assigned*; Art. 14 requires it to be *exercised*.** A
named overseer who never reviewed anything satisfies the first and not
the second, and only the second produces evidence.

## Regulatory anchors

- **EU AI Act (EU) 2024/1689, Article 14(4)** — the operative anchor.
  Five capabilities the assigned overseer must be able to exercise:
  understand the system's capacities and limitations and monitor for
  anomalies, dysfunctions and unexpected performance (a); remain aware
  of automation bias (b); correctly interpret output (c); decide not to
  use the system or to disregard, override or reverse its output (d);
  and intervene or interrupt operation through a stop button or similar
  procedure (e).
- **Article 14(5)** — for Annex III point 1(a) remote biometric
  identification, no action or decision may be taken on the basis of an
  identification unless separately verified by **at least two** natural
  persons with the necessary competence, training and authority. Narrow
  exemption for law-enforcement, migration, border-control and asylum
  uses where Union or national law considers the requirement
  disproportionate.
- **Article 14(1) and 14(3)(a) (context, not discharged here)** — the
  provider designs the system so it can be effectively overseen and
  builds in what it can. A playbook cannot put a stop button into
  someone else's product.
- **Article 14(3)(b)** — the measures the provider identifies for the
  deployer to implement. These arrive through the Art. 13 instructions
  for use and are the input `brief_oversight_personnel` reads.
- **Article 26(2) (upstream gate)** — assignment of oversight to a
  competent, trained, authorised and supported natural person.
- **GDPR Article 22 (adjacent, overlap)** — human oversight is one way
  a decision avoids being "solely" automated, but Art. 22 is a right
  the data subject exercises while Art. 14 is a standing duty on the
  deployer. Satisfying Art. 14 does not discharge an Art. 22 request,
  and this playbook implements no Art. 22 response path.

Inbound mapping:
[`article-14-human-oversight.yaml`](../../mappings/eu_ai_act/article-14-human-oversight.yaml).

This playbook is SKELETON. Outbound OSCAL, OCSF and D3FEND closure,
the deterministic primitives and the three-target compile examples land
with the sibling **CORE** card.

## How to compile

Not yet compilable. `x_secops_ng.compile_targets` is empty: this is
portable content only at SKELETON, and the step bodies are declared
rather than bound.

The sibling **CORE** card binds the primitives and lands the emitted
examples with byte-parity goldens, at which point they appear at:

- n8n — `examples/n8n/ai_human_oversight/`
- Temporal — `examples/temporal/ai_human_oversight/`
- LangGraph — `examples/langgraph/ai_human_oversight/`

## Operator customisation

CACAO variables the playbook exposes:

| Variable | Supplied by | Purpose |
|---|---|---|
| `__deployment_id__` | operator | Identifier of the high-risk AI system deployment; shared with the deployer-obligations playbook so the assignment record and this loop join on one key |
| `__oversight_cycle__` | operator | The review window this cycle runs against (RFC 3339 interval) |

Adapter-bound surfaces the operator wires — the framework declares each
contract and ships none of them:

- **Oversight roster / rota surface** — read at
  `establish_oversight_roster`.
- **Delegation model** — the authority to disregard, override or halt.
  Recorded, not authored, by this playbook.
- **Briefing and attestation store** — written at
  `brief_oversight_personnel`.
- **Flagged-output queue** — read at `review_flagged_decisions`. Which
  outputs get flagged is an operator policy decision this playbook does
  not make.
- **Intervention channel** — the actual stop button or override path,
  which lives in the deployed system, not here.
- **Evidence store** — written at `emit_oversight_evidence`.

Three things to get right when wiring this:

1. **Authority is not competence.** Art. 14(4)(a)–(c) are competence
   limbs, evidenced by briefing records. Art. 14(4)(d)–(e) are
   authority limbs — a roster entry naming someone without the
   delegated power to halt produces an overseer who cannot lawfully
   oversee. Only the competence side has a control anchor in this
   catalogue; the authority side is recorded, and the asymmetry is
   deliberate.
2. **The Art. 14(5) two-person rule means two people.** One overseer
   confirming twice does not satisfy it, and both must independently
   carry competence, training and authority. Where the narrow
   law-enforcement exemption is relied on, record the Union or national
   legal basis — not merely that the exemption was taken.
3. **A quiet cycle still produces evidence.** A review that found
   nothing and a nil intervention record are as much proof of exercised
   oversight as an intervention is. Skipping the record on a quiet
   cycle is what makes oversight unprovable later.

## Sources

- EU AI Act — [Regulation (EU) 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj),
  Article 14, Article 26(2), Annex III point 1(a)
- GDPR — [Regulation (EU) 2016/679](https://eur-lex.europa.eu/eli/reg/2016/679/oj),
  Article 22
- OASIS CACAO v2.0 specification
