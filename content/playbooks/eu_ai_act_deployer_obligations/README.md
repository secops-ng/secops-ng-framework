# eu_ai_act_deployer_obligations

**Status:** SKELETON · **Stable id:** `playbook.eu_ai_act_deployer_obligations@v1`

## Overview

Operator-side EU AI Act **Article 26 deployer-obligation lifecycle**,
gated by the **Article 27 fundamental-rights impact assessment**. It
fires on the operator's pre-deployment gate for a high-risk AI system
and again on each monitoring cycle once the system is in service. Inputs
are the operator's deployment register entry and the provider's
instructions for use; the artifact produced is a dated cycle-evidence
record joining the intended-use determination, the oversight assignment,
the monitoring observations, the fundamental-rights assessment and the
log-retention disposition.

Every other EU AI Act artifact in this catalogue anchors on the
**provider** — Art. 9 risk management, Art. 11 technical documentation,
Art. 13 transparency, Art. 15 robustness, Art. 72 post-market
monitoring, Art. 73 serious-incident reporting. This is the first on the
**deployer** side: the operator who runs a third-party high-risk AI
system rather than placing one on the market. Most organisations reading
this framework are deployers, not providers.

The five action steps are `confirm_intended_use` (Art. 26(1), gated on
the Art. 26(7) worker notice), `assign_human_oversight` (Art. 26(2)),
`monitor_operation` (Art. 26(4) and 26(5), carrying the lifecycle's only
escalation edge), `assess_fundamental_rights_impact` (Art. 27), and
`retain_logs_and_evidence` (Art. 26(6)).

## Regulatory anchors

- **EU AI Act (EU) 2024/1689, Article 26(1)** — use of the high-risk AI
  system in accordance with the instructions for use.
- **Article 26(2)** — assignment of human oversight to natural persons
  with the necessary competence, training, authority and support.
- **Article 26(4)** — relevance and representativeness of input data,
  binding only to the extent the deployer controls the input surface.
- **Article 26(5)** — monitoring, Art. 72 feedback to the provider,
  and the escalation duties: notification **and suspension** on an
  Art. 79(1) risk determination, and immediate *sequenced* notification
  on a serious incident (provider → importer or distributor →
  market-surveillance authorities).
- **Article 26(6)** — retention of automatically generated logs under
  the deployer's control, for a period appropriate to the intended
  purpose and at least six months.
- **Article 26(7)** — information to workers' representatives and
  affected workers *before* a workplace deployment is put into service.
- **Article 27(1)(a)–(f)** — the fundamental-rights impact assessment,
  performed prior to deploying, for public-law bodies, private entities
  providing public services, and deployers of the Annex III(5)(b)–(c)
  systems.
- **Article 27(4)** — complementarity with an existing GDPR Art. 35
  DPIA, and notification of the result to the market-surveillance
  authority.
- **GDPR (EU) 2016/679, Article 35 (overlap)** — the DPIA the FRIA
  complements. Discharged by
  `playbook.data_protection_impact_assessment@v1`; never composed here.
- **EU AI Act Article 73 (hand-off)** — the provider-side
  serious-incident reporting chain the Art. 26(5) escalation feeds. The
  deployer's notification is an input to that chain, not a substitute
  for it.

Inbound mappings:
[`article-26-deployer-obligations.yaml`](../../mappings/eu_ai_act/article-26-deployer-obligations.yaml)
and [`article-27-fria.yaml`](../../mappings/eu_ai_act/article-27-fria.yaml).

This playbook is SKELETON. Outbound OSCAL, OCSF and D3FEND closure
lands with the sibling **CORE** card, along with the deterministic
primitives and the three-target compile examples.

## How to compile

Not yet compilable. `x_secops_ng.compile_targets` is empty: this is
portable content only at SKELETON, and the step bodies are declared
rather than bound.

The sibling **CORE** card binds the deterministic primitives and lands
the emitted examples with byte-parity goldens, at which point they
appear at:

- n8n — `examples/n8n/eu_ai_act_deployer_obligations/`
- Temporal — `examples/temporal/eu_ai_act_deployer_obligations/`
- LangGraph — `examples/langgraph/eu_ai_act_deployer_obligations/`

## Operator customisation

CACAO variables the playbook exposes:

| Variable | Supplied by | Purpose |
|---|---|---|
| `__deployment_id__` | operator | Stable identifier of the high-risk AI system deployment; joins every record in the cycle |
| `__system_reference__` | operator | Reference to the provider's system and its accompanying instructions for use |

Adapter-bound surfaces the operator wires — the framework declares each
contract and ships none of them:

- **Deployment register** — read at `confirm_intended_use`.
- **Oversight-assignment record** — written at `assign_human_oversight`.
- **Input-data control surface** — read at `monitor_operation` for the
  Art. 26(4) determination.
- **Monitoring signal source** — read per window at `monitor_operation`.
- **Notification channels** — provider, importer or distributor, and the
  Member State market-surveillance authority.
- **FRIA record store and notification channel** — the Art. 27(5)
  template is unpublished by the AI Office, so the step declares the
  submission contract and emits a dated record rather than binding a
  guessed template shape.
- **Log store and evidence store** — the Art. 26(6) retention period is
  applied here. Six months is a floor, not a target; sector law may
  require longer.

Three things to get right when wiring this:

1. **The escalation edge has three triggers, not one.** Routine
   monitoring, an Art. 79(1) risk determination compelling suspension,
   and a serious incident compelling sequenced notification. Collapsing
   them loses the suspension duty.
2. **The FRIA complements a DPIA; it does not repeat or replace one.**
   Where the operator holds a DPIA for the same processing, this
   playbook reads it and assesses only the remainder.
3. **Two obligations are hard pre-deployment gates.** The Art. 26(7)
   notice and the Art. 27 assessment cannot be remediated
   retrospectively, so both are modelled as preconditions.

## Sources

- EU AI Act — [Regulation (EU) 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj),
  Articles 26, 27 and 79(1)
- GDPR — [Regulation (EU) 2016/679](https://eur-lex.europa.eu/eli/reg/2016/679/oj),
  Article 35
- OASIS CACAO v2.0 specification
- GDPR data-flow entry:
  [`data-flow-eu_ai_act_deployer_obligations.md`](../../mappings/gdpr/data-flow-eu_ai_act_deployer_obligations.md)
