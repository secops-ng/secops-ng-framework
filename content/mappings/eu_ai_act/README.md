# EU AI Act — content/mappings/eu_ai_act/

Crosswalk from Regulation (EU) 2024/1689 (EU AI Act) high-risk-provider
obligations to SecOps-NG content-model artifacts. Focus of the shipped
SKELETON pass is the **Art. 9 risk-management** lifecycle on high-risk
AI systems and the adjacent Art. 11 + Annex IV technical-documentation,
Art. 13 transparency, and Art. 72 post-market-monitoring surfaces the
`eu_ai_act_risk_management` playbook exercises step-by-step.

## Scope

- **In:** structural mapping from named EU AI Act articles to the
  control, playbook, and metric IDs the AI Act risk-management
  playbook backlinks. One YAML per article; each entry cites the
  authoritative EUR-Lex permalink.
- **Out:** Annex I prohibited practices, the GPAI chapter of the
  Regulation, Art. 43 conformity-assessment integration, and the
  Art. 6(3)–(6) provider derogation / Commission delegated-act track
  on the Annex III presumption. Those land as sibling cards.

## Files

- `article-6-classification.yaml` — Art. 6(1) Annex II product-safety
  intersection route and Art. 6(2) standalone Annex III route into
  the high-risk category. Gate condition on the identify-high-risk-
  AI-system step of the eu_ai_act_risk_management playbook.
- `annex-iii-use-cases.yaml` — Annex III enumeration (eight areas:
  biometrics; critical infrastructure; education and vocational
  training; employment and workers management; essential services;
  law enforcement; migration, asylum and border control;
  administration of justice and democratic processes).
- `article-9-risk-management.yaml` — Art. 9(1)–(6) risk-management
  system obligations on high-risk AI providers (lifecycle iteration,
  identify / estimate / evaluate cycle, residual-risk acceptability
  ceiling, testing across foreseeable-misuse conditions).
- `article-11-technical-documentation.yaml` — Art. 11 + Annex IV
  technical documentation obligations (bundle authoring and
  maintenance).
- `article-13-transparency.yaml` — Art. 13 transparency obligations
  (instructions for use, information duties toward deployers).
- `article-72-post-market-monitoring.yaml` — Art. 72 post-market
  monitoring plan and feedback into the Art. 9 risk-management cycle.
- `oscal-component-definition.json` — OSCAL 1.1.2 component definition
  mirroring the GDPR / CRA siblings; one implemented-requirement per
  (entry, control_ref) pair. Art. 6 classification and Annex III
  enumeration entries carry no `control_refs` (deterministic overlay
  lookup rather than an OSCAL control anchor) and are consequently
  not reflected in the OSCAL component definition.

## Citation policy

Citations point at the EU instrument (CELEX + EUR-Lex URL). The Act
is Regulation (EU) 2024/1689 (CELEX 32024R1689).

## ID conventions

Mapping IDs are `eu_ai_act:art-<n>[-<sub>]` for article-anchored
entries (e.g. `eu_ai_act:art-9-risk-management`,
`eu_ai_act:art-6-2-annex-iii-standalone`) and
`eu_ai_act:annex-<roman>-<paragraph>-<slug>` for Annex-anchored
entries (e.g. `eu_ai_act:annex-iii-1-biometrics`). Slug parts use
kebab-case.

## Cross-regime edges

The Art. 9(2) risk-analysis cycle is the AI-system-specific execution
surface for NIS2 Art. 21(2)(a) risk-analysis policies; the inbound
edge is recorded on `content/mappings/nis2/article-21-2-a.yaml`. For
high-risk AI systems processing personal data, Recital 9 of Regulation
(EU) 2024/1689 preserves GDPR obligations; the ex-ante Art. 35 DPIA
duty is captured on `content/mappings/gdpr/article-35-dpia.yaml`.

DORA (Regulation (EU) 2022/2554) Art. 6 ICT risk-management and CRA
(Regulation (EU) 2024/2847) Annex I product-security are
adjacent-but-distinct regimes: DORA runs on ICT operations of
financial entities and CRA on product security of products with
digital elements. Neither has a documented interaction with the
AI Act Art. 9 provider-side risk-management obligation on high-risk
AI systems that would justify a direct inbound edge from this
directory; the shipped `dora: []` / `cra: []` arrays on the playbook
overlay record that review.
