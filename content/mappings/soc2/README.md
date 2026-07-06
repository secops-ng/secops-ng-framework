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
| Availability | `tsc-availability.yaml` | A1.1–A1.3 (3) |
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

The Availability category (`tsc-availability.yaml`) is present
with the three A-series criteria (A1.1 through A1.3) as draft
entries. A1.1 covers availability commitments and capacity
planning; A1.2 covers environmental protections, backup, and
recovery infrastructure; A1.3 covers testing of the recovery plan
procedures.

The remaining three Trust Services categories (Confidentiality,
Processing Integrity, Privacy) land as sibling files on future
cards.
