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
