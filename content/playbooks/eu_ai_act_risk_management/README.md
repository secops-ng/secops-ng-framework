# eu_ai_act_risk_management

CACAO v2 SKELETON playbook for the risk-management system
Article 9 of the EU AI Act (Regulation (EU) 2024/1689) requires
providers of high-risk AI systems to establish, implement, document
and maintain. The playbook inventories a high-risk AI system against
Annex III, iterates the Art. 9(2) identify / analyse / evaluate
cycle, assembles the technical documentation Art. 11 read with
Annex IV pin, and closes the loop with the post-market monitoring
feedback Art. 9(2)(c) reads together with Art. 72.

## Status

SKELETON (content version `0.1.0`). Ships the CACAO scaffold and a
placeholder mappings overlay only. No compiled examples, no metric
wiring, no inbound-regulator YAML edges yet — those land on sibling
CORE / EXTEND / G-02 cards. The AI Act enforcement wave that
motivates this scaffold begins with the July 2026 provisions
following OJ entry-into-force under Art. 113 (staggered application
of the Chapters).

## Purpose

Give operators a portable, framework-agnostic scaffold for the
Art. 9 risk-management system so the same lifecycle-governance shape
travels across n8n, Temporal, and LangGraph without re-authoring per
runtime. The playbook is deliberately the risk-management surface;
sibling playbooks (yet to be authored) cover the adjacent AI-Act
obligations: data governance (Art. 10), record-keeping (Art. 12),
transparency and provision of information to deployers (Art. 13),
human oversight (Art. 14), accuracy / robustness / cybersecurity
(Art. 15), and the post-market monitoring surface itself (Art. 72).

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.eu_ai_act_risk_management@v1`).
- `mappings.yaml` — SKELETON outbound overlay. Every field carries
  either a real pin or a `todo: true` placeholder pointing to the
  sibling G-02 card. Schema:
  `../../../schemas/playbook-mappings.schema.json`.

## Workflow (SKELETON stubs)

1. **Identify high-risk AI system** — inventory the AI system,
   resolve whether it is a high-risk AI system under Art. 6 read
   with Annex III (or against a Union-harmonisation-legislation
   entry per Art. 6(1) and Annex I), and pin the Annex III
   use-case category.
2. **Assess risk under Art. 9(2)** — iterate the Art. 9(2)
   risk-management cycle: identification and analysis of known and
   reasonably foreseeable risks under Art. 9(2)(a); estimation and
   evaluation of risks emerging under intended purpose and
   reasonably foreseeable misuse under Art. 9(2)(b); evaluation of
   post-market monitoring signals under Art. 9(2)(c); adoption of
   targeted risk-management measures under Art. 9(2)(d).
3. **Assemble technical documentation** — draw up the Art. 11 read
   with Annex IV technical documentation before the system is
   placed on the market or put into service, including the detailed
   description of the risk-management system per Art. 9.
4. **Monitor post-market signals** — operate the Art. 72 post-market
   monitoring plan and feed its signals back into the Art. 9(2)(c)
   step of the next iteration so residual-risk acceptability under
   Art. 9(5) stays defended.

## Regulatory anchors (SKELETON)

### EU AI Act — Regulation (EU) 2024/1689

- **Art. 9(1)** — establishment, implementation, documentation, and
  maintenance of a risk-management system for a high-risk AI
  system. Anchored end-to-end on this playbook.
- **Art. 9(2)** — iterative identify / estimate / evaluate / adopt
  cycle. Anchored on the "assess risk under Art. 9(2)" step;
  Art. 9(2)(c) closes with the "monitor post-market signals" step.
- **Art. 9(5)** — residual-risk acceptability. Measured on
  metrics landed by the sibling EXTEND card.
- **Art. 11 read with Annex IV** — technical documentation. Anchored
  on the "assemble technical documentation" step.
- **Art. 13** — transparency and provision of information to
  deployers (instructions for use). Adjacent obligation; a sibling
  playbook (yet to be authored) owns the deployer-facing
  instructions surface. This scaffold's technical-documentation
  step feeds it.
- **Art. 72** — post-market monitoring by providers. The Art. 9(2)(c)
  loop-back edge reads its signals from the Art. 72 plan.

### NIS2 Directive (EU) 2022/2555

- **Art. 21(2)(a)** — policies on risk analysis and information-
  system security. The Art. 9(2) risk-analysis step of this
  playbook is the AI-system-specific execution surface for the
  risk-analysis policy obligation NIS2 imposes on essential and
  important entities. Inbound YAML edge deferred to the sibling
  G-02 card.

### Adjacent regimes (feasibility notes only — SKELETON)

- **GDPR** — Art. 35 DPIA obligation interacts with the Art. 9
  risk-management cycle when the high-risk AI system processes
  personal data. Recital 9 of Regulation (EU) 2024/1689 preserves
  GDPR obligations. Inbound YAML edge deferred to the G-02 card
  that opens the eu_ai_act ↔ gdpr edge.
- **DORA** — Art. 6 ICT risk-management framework applies to
  financial entities and is anchored on the operator-side
  incident-management / dora_ict_risk_selfassess lane, not on the
  product-lifecycle surface AI Act Art. 9 governs. The G-02 card
  reviews whether a cross-regime edge is warranted; the current
  reading is that they are adjacent-but-distinct.
- **CRA** — Annex I product-security obligations for products with
  digital elements are adjacent to AI Act Art. 9 for AI systems
  that are themselves CRA-covered products. The G-02 card reviews
  whether a cross-regime edge is warranted; the current reading is
  that they are adjacent-but-distinct.

## Out of scope (this SKELETON)

- Per-target compiled emissions (n8n / Temporal / LangGraph). The
  `compile_targets` array is deliberately empty; the CORE card
  populates it once the stub actions carry compilable action
  bodies.
- KPI / KRI metric wiring. `metric_refs` is empty; the EXTEND card
  lands metric catalogue entries for residual-risk-acceptability
  and post-market-signal-turnaround measurements.
- Inbound regulator-side YAML edges (`content/mappings/eu_ai_act/`,
  `content/mappings/nis2/article-21-2-a.yaml`,
  `content/mappings/gdpr/`). Deferred to sibling G-02 cards.
- Adjacent AI-Act obligations (Art. 10 data governance, Art. 12
  record-keeping, Art. 13 deployer instructions, Art. 14 human
  oversight, Art. 15 accuracy / robustness / cybersecurity, Art. 72
  post-market monitoring as its own playbook). Separate playbooks
  to be authored under G-01.

## Sources

- OASIS CACAO v2.0 specification.
- Regulation (EU) 2024/1689 — EU Artificial Intelligence Act,
  Articles 6, 9, 11, 13, 72, and Annexes III and IV.
- NIS2 Directive (EU) 2022/2555 — Article 21(2)(a).
- NIST AI Risk Management Framework (AI 100-1) — Govern / Map /
  Measure / Manage functions, referenced for the CORE-phase OSCAL
  pin selection.
