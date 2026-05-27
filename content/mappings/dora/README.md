# DORA — content/mappings/dora/

Crosswalk from Regulation (EU) 2022/2554 (DORA) obligations to SecOps-NG
content-model artifacts. Focus is on the **major-ICT-incident reporting**
lane (Art. 17–19 and the ESAs RTS/ITS) and on the **ICT third-party risk**
lane (Art. 28–30). Out of scope here: TLPT (Art. 26–27), CTPP designation
watch (Art. 31 — a KB concern in the private repos).

## Scope

- **In:** structural mapping from named DORA articles and the associated
  ESAs Delegated/Implementing Regulations to control, playbook, and
  metric IDs in the content model.
- **Out:** legal interpretation, the actual ITS submission transport,
  per-Member-State CSIRT routing.

## Citation policy

Citations point at the EU instrument (CELEX + EUR-Lex URL). DORA-specific
Delegated/Implementing Regulations (2024/1772, 2024/2955, 2024/2956) are
cited verbatim.

## ID conventions

Mapping IDs are `dora:art-<n>[-<sub>]` (e.g. `dora:art-19-initial-4h`,
`dora:art-28-third-party-register`). Slug parts use kebab-case.

## Companion research

See research brief 2026-05-15-dora-incident-reporting.md for the
auto-population assessment (which fields are A / H / M) and for the
shared timeline-pattern recommendation with NIS2 Art. 23.
