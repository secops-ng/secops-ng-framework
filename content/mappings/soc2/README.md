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
| Confidentiality | `tsc-confidentiality.yaml` | C1.1–C1.2 (2) |
| Processing Integrity | `tsc-processing-integrity.yaml` | PI1.1–PI1.5 (5) |
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

The Confidentiality category (`tsc-confidentiality.yaml`) is
present with the two C-series criteria (C1.1 through C1.2) as
draft entries. C1.1 covers identification and maintenance of
confidential information; C1.2 covers disposal of confidential
information. The classification scheme itself and the
media-disposal procedures remain operator-owned artifacts;
anchors here discharge the structural surfaces (asset inventory,
leaver-side asset return, reconciliation-and-disposal flow).

The Processing Integrity category (`tsc-processing-integrity.yaml`)
is present with the five PI-series criteria (PI1.1 through PI1.5)
as draft entries. PI1.1 covers the quality of information that
supports internal controls; PI1.2 covers input controls
(completeness and accuracy); PI1.3 covers processing controls
(complete, accurate, timely, authorised output); PI1.4 covers
delivery of output to authorised users; PI1.5 covers storage of
inputs, in-processing items, and outputs. Anchors here discharge
the surfaces where security operations overlap with processing
integrity (control-effectiveness evidence, authorised-delivery
access enforcement, storage-completeness backup evidence and
asset inventory); the application-layer input, processing, and
output-accuracy controls themselves sit outside the SecOps-NG
catalogue and ship as gap notes on the relevant entries.

The remaining Trust Services category (Privacy) lands as a
sibling file on a future card.
