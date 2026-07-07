# content/mappings/nist_csf/

NIST CSF 2.0 crosswalk. The NIST Cybersecurity Framework 2.0
(NIST CSWP 29, published 26 February 2024) organises the CSF Core
around six Functions and 22 Categories, with a Subcategory layer
underneath. This directory carries the SecOps-NG crosswalk to the
CSF 2.0 Core.

## File convention

One YAML file per structural level of the CSF Core:

| Level | File | Entries |
|-------|------|---------|
| Categories (Core Functions) | `csf-core-functions.yaml` | 22 |
| Subcategories | (future CORE card) | ~106 |

Entry ids use `nist_csf:<slug>` where the slug carries the CSF
Category identifier and a kebab-case phrase, e.g.
`nist_csf:pr-aa-identity-management-authentication-and-access-control`.

## CSF 2.0 structure

Six Functions, 22 Categories:

| Function | Category identifiers |
|----------|----------------------|
| Govern (GV)   | GV.OC, GV.RM, GV.RR, GV.PO, GV.OV, GV.SC |
| Identify (ID) | ID.AM, ID.RA, ID.IM |
| Protect (PR)  | PR.AA, PR.AT, PR.DS, PR.PS, PR.IR |
| Detect (DE)   | DE.CM, DE.AE |
| Respond (RS)  | RS.MA, RS.AN, RS.CO, RS.MI |
| Recover (RC)  | RC.RP, RC.CO |

The Govern Function is new in CSF 2.0 and subsumes the CSF 1.1
`ID.GV` (Governance) Category — governance concerns were promoted
out of Identify into their own Function. This crosswalk reflects
the 2.0 layout only; no CSF 1.1 anchors ship here.

## Status

The Category level (`csf-core-functions.yaml`) is present with all
22 Categories across GV / ID / PR / DE / RS / RC as draft entries.
The Subcategory level (~106 leaf outcomes such as `GV.OC-01`,
`PR.AA-05`) is deliberately out of scope for the SKELETON and lands
on a sibling CORE card. Coverage of the CSF Informative References
(mappings to NIST SP 800-53r5, ISO/IEC 27001:2022, CIS Controls v8,
etc.) is out of scope of this directory entirely — the SecOps-NG
crosswalk asserts against the operator's own catalogue, not against
the CSF Informative References.

## Regime scope caveat

CSF 2.0 is a US-origin voluntary framework maintained by NIST, not
an EU statutory instrument. The crosswalk is a structural pointer
against the operator's own control catalogue — the assertion is
that the named artifacts exercise the Category outcomes in practice,
not that they constitute a legal or regulator interpretation of the
CSF. Where a CSF Category outcome overlaps an EU obligation already
carried under `content/mappings/nis2/` or `content/mappings/dora/`,
those regime-specific crosswalks remain the authoritative pointer
for the statutory surface (see the RS.CO entry note in
`csf-core-functions.yaml`).

## Value

CSF 2.0 is the reference vocabulary US-origin and global operator
communities use when evaluating security programmes and portable
tooling. Carrying the crosswalk lets an operator running an EU
regulatory baseline (NIS2, DORA, CRA) present the same catalogue
against a CSF 2.0 assessment without re-authoring evidence — the
same control and playbook artifacts discharge both the EU
statutory obligations and the CSF Category outcomes.

## Reference

NIST CSWP 29, "The NIST Cybersecurity Framework (CSF) 2.0",
February 26, 2024. <https://doi.org/10.6028/NIST.CSWP.29>
