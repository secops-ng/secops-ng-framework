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

- `article-19-and-28.yaml` — Art. 17–19 reporting milestones, Art. 28/30
  third-party risk register and contractual clauses.
- `article-9-and-rts-vuln-mgmt.yaml` — Art. 9(4)(a) protection and
  prevention, anchored to the JC RTS on ICT risk management framework
  (Commission Delegated Regulation (EU) 2024/1774) Art. 10
  (Vulnerability and patch management procedures).

## Citation policy

Citations point at the EU instrument (CELEX + EUR-Lex URL). DORA-specific
Delegated/Implementing Regulations (2024/1772, 2024/1774, 2024/2955,
2024/2956) are cited verbatim.

## ID conventions

Mapping IDs are `dora:art-<n>[-<sub>]` (e.g. `dora:art-19-initial-4h`,
`dora:art-28-third-party-register`). Slug parts use kebab-case.

## OSCAL component-definition (SKELETON)

`oscal-component-definition.json` is a minimal OSCAL 1.1.2
component-definition document mirroring the NIS2 layout. One component
(SecOps-NG) carries one control-implementation set whose
`implemented-requirements` cover the in-scope DORA articles for this
skeleton — Article 9(4)(a) (vulnerability and patch management) and
Articles 18–19 (ICT-related incident classification and reporting).
Statement text is borrowed verbatim from each YAML entry's
`obligation` field; `source-entry-id`, `source-control-ref`, and
`source-article` props preserve the round-trip back to the YAML.
Third-party-risk entries (Art. 28+), D3FEND enrichment, and a CRA
component land in follow-on SKELETONs. Schema-validation and
YAML-coverage parity are enforced by
`tests/content/test_oscal_dora_component_definition.py` against the
OSCAL component schema vendored under
`tests/fixtures/oscal/oscal_component_schema-v1.1.2.json`.

## Companion research

See research brief 2026-05-15-dora-incident-reporting.md for the
auto-population assessment (which fields are A / H / M) and for the
shared timeline-pattern recommendation with NIS2 Art. 23.
