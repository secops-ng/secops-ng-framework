# content/mappings/soc2/

SOC 2 crosswalk. The AICPA Trust Services Criteria (2017, as
revised) organise controls into five categories: Security (the
mandatory baseline, Common Criteria series), Availability,
Confidentiality, Processing Integrity, and Privacy.

## File convention

One YAML file per Trust Services category:

| Category | File | Criteria |
|----------|------|----------|
| Security (Common Criteria) | `tsc-security.yaml` | CC1.1–CC9.2 (33) |
| Availability | *future* | A-series |
| Confidentiality | *future* | C-series |
| Processing Integrity | *future* | PI-series |
| Privacy | *future* | P-series |

Entry ids use `soc2:<cc-slug>` where the slug carries the
criterion number and a kebab-case phrase, e.g.
`soc2:cc6-1-logical-access-controls`.

## Status

The Security category (`tsc-security.yaml`) is present with the
33 Common Criteria (CC1.1 through CC9.2) as draft entries. CC1–CC5
mirror the COSO 2013 internal-control components (control
environment, communication and information, risk assessment,
monitoring activities, control activities); CC6–CC9 are the
technology-specific extensions (logical/physical access, system
operations, change management, risk mitigation).

The other four Trust Services categories (Availability,
Confidentiality, Processing Integrity, Privacy) land as sibling
files on future cards.
