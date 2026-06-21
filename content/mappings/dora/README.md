# DORA — content/mappings/dora/

Crosswalk from Regulation (EU) 2022/2554 (DORA) obligations to SecOps-NG
content-model artifacts. Focus is on the **major-ICT-incident reporting**
lane (Art. 17–19 and the ESAs RTS/ITS), the **ICT third-party risk** lane
(Art. 28–30), and the **vulnerability and patch management** lane
(Art. 9 anchored to the JC RTS on ICT risk management framework,
Commission Delegated Regulation (EU) 2024/1774, Art. 10). Out of scope
here: TLPT (Art. 26–27), CTPP designation watch (Art. 31 — a KB concern
in the private repos).

## Scope

- **In:** structural mapping from named DORA articles and the associated
  ESAs Delegated/Implementing Regulations to control, playbook, and
  metric IDs in the content model. Includes vulnerability and patch
  management procedures under the JC RTS on ICT risk management
  framework (Commission Delegated Regulation (EU) 2024/1774).
- **Out:** legal interpretation, the actual ITS submission transport,
  per-Member-State CSIRT routing.

## Files

- `article-5.yaml` — Art. 5 governance and organisation.
- `article-6.yaml` — Art. 6 ICT risk-management framework (annual
  review and ICT-auditor cycle).
- `article-6-governance.yaml` — Art. 6(4) clearly assigned functions
  and responsibilities for ICT-related tasks and the
  communication-cooperation-coordination arrangements (on-call
  responsibility).
- `article-7.yaml` — Art. 7 ICT systems, protocols and tools.
- `article-8.yaml` — Art. 8 identification (assets, functions,
  dependencies).
- `article-9-and-rts-vuln-mgmt.yaml` — Art. 9(4)(a) protection and
  prevention, anchored to the JC RTS on ICT risk management framework
  (Commission Delegated Regulation (EU) 2024/1774) Art. 10
  (Vulnerability and patch management procedures).
- `article-9-access-management.yaml` — Art. 9(4)(c) access-management
  policies, anchored to the JC RTS on ICT risk management framework
  (Commission Delegated Regulation (EU) 2024/1774) Arts. 20–22
  (identity management, access management, authentication).
- `article-10.yaml` — Art. 10 detection.
- `article-11.yaml` — Art. 11 response and recovery.
- `article-12.yaml` — Art. 12 backup policies and procedures,
  restoration and recovery procedures and methods.
- `article-13.yaml` — Art. 13 learning and evolving (post-incident
  review).
- `article-14.yaml` — Art. 14 communication (crisis communication
  plans).
- `article-19-and-28.yaml` — Art. 17–19 reporting milestones, Art. 28/30
  third-party risk register and contractual clauses.

## Citation policy

Citations point at the EU instrument (CELEX + EUR-Lex URL). DORA-specific
Delegated/Implementing Regulations (2024/1772, 2024/1774, 2024/2955,
2024/2956) are cited verbatim.

## ID conventions

Mapping IDs are `dora:art-<n>[-<sub>]` (e.g. `dora:art-19-initial-4h`,
`dora:art-28-third-party-register`). Slug parts use kebab-case.

## OSCAL component-definition

`oscal-component-definition.json` is an OSCAL 1.1.2 component-definition
document mirroring the NIS2 and CRA siblings. One component (SecOps-NG)
carries one control-implementation set whose `implemented-requirements`
cover the in-scope DORA articles:

- **Article 5 governance and organisation** (CORE layer) — internal
  governance and control framework, management-body responsibility,
  approved review cadence;
- **Article 6 ICT risk-management framework** (CORE layer) — documented
  framework with annual review and ICT-auditor cycle;
- **Article 7 ICT systems, protocols and tools** (CORE layer);
- **Article 8 identification** (CORE layer);
- **Article 9(4)(a) vulnerability and patch management** (CORE layer);
- **Article 10 detection** (CORE layer);
- **Article 11 response and recovery** (CORE layer);
- **Article 12 backup policies and restoration** (EXTEND layer);
- **Article 13 learning and evolving (post-incident review)** (EXTEND
  layer);
- **Article 14 crisis communication** (EXTEND layer);
- **Articles 18–19** (ICT-related incident classification and
  reporting).

Statement text is borrowed verbatim from each YAML entry's
`obligation` field; `source-entry-id`, `source-control-ref`, and
`source-article` props preserve the round-trip back to the YAML.
CORE-tier implemented-requirements for Art.5 and Art.6 also carry
`source-d3fend-technique` and `source-d3fend-entry-id` props anchoring
each obligation to a defensive technique in
`content/mappings/d3fend/dora.yaml`. Third-party-risk entries (Art. 28+)
land in a follow-on SKELETON. Schema-validation and YAML-coverage
parity are enforced by
`tests/content/test_oscal_dora_component_definition.py` against the
OSCAL component schema vendored under
`tests/fixtures/oscal/oscal_component_schema-v1.1.2.json`.

## Companion research

See research brief 2026-05-15-dora-incident-reporting.md for the
auto-population assessment (which fields are A / H / M) and for the
shared timeline-pattern recommendation with NIS2 Art. 23.
