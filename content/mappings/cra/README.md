# CRA — content/mappings/cra/

Crosswalk from Regulation (EU) 2024/2847 (Cyber Resilience Act, "CRA")
obligations to SecOps-NG content-model artifacts. CRA applies to
manufacturers, importers, and distributors of products with digital
elements placed on the EU market. The mapping focuses on the two
obligations that fit cleanly into the content model:

- **Annex I §1** essential cybersecurity requirements relevant to the
  product lifecycle, with SBOM production (Annex I §2(1)) as the
  primary artifact dependency;
- **Article 14** obligation to report actively exploited vulnerabilities
  and severe incidents to ENISA and to the relevant CSIRT.

## Scope

- **In:** structural mapping from named CRA articles and Annex I points
  to control, playbook, and metric IDs in the content model.
- **Out:** product-conformity assessment paths, CE-marking procedures,
  market-surveillance authority interactions.

## Citation policy

Citations point at the CRA instrument by CELEX and EUR-Lex URL. Application
date: the bulk of CRA obligations apply from 11 December 2027; the
incident-reporting obligation (Art. 14) applies earlier (11 September 2026
per Art. 71).

## ID conventions

Mapping IDs are `cra:<slug>` (e.g. `cra:annex-i-1-h`, `cra:art-14-early-warning`).

## OSCAL component-definition

`oscal-component-definition.json` is an OSCAL 1.1.2 component-definition
document mirroring the NIS2 and DORA siblings. One component (SecOps-NG)
carries one control-implementation set whose `implemented-requirements`
cover the in-scope CRA obligations:

- **Annex I §1 essential cybersecurity requirements** (CORE layer) —
  secure-by-default configuration, access control, confidentiality,
  integrity, availability, attack-surface limitation, logging and
  monitoring, and security-update capability;
- **Annex I §2 vulnerability-handling essential requirements**
  (SKELETON layer) — SBOM, vulnerability handling, coordinated
  vulnerability disclosure policy, security update dissemination;
- **Article 14 reporting obligations** (SKELETON layer) — early-warning
  (24h), 72-hour notification, final report, severe-incident
  notification to the coordinator CSIRT and ENISA.

Statement text is borrowed verbatim from each YAML entry's `obligation`
field; `source-entry-id`, `source-control-ref`, and `source-article`
props preserve the round-trip back to the YAML. D3FEND enrichment and
CORE/EXTEND coverage of additional CRA articles (Art.13 manufacturer
obligations, Annex I §3 conformance assessment, Art.10 importer and
distributor obligations, Annex II technical documentation) land in
follow-on layers. Schema-validation and YAML-coverage parity are enforced by
`tests/content/test_oscal_cra_component_definition.py` against the
OSCAL component schema vendored under
`tests/fixtures/oscal/oscal_component_schema-v1.1.2.json`.
