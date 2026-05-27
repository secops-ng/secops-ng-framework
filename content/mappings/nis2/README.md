# NIS2 — content/mappings/nis2/

Crosswalk from Directive (EU) 2022/2555 (NIS2) obligations to SecOps-NG
content-model artifacts. One YAML file per obligation atom (Article 21(2)
subpoints (a)–(j) plus Article 23 incident-notification milestones).

## Scope

- **In:** structural mapping from named regulatory clauses to control,
  playbook, and metric IDs in the SecOps-NG content model.
- **Out:** legal interpretation. The `obligation` field paraphrases what
  the article requires; it is not legal advice and is not a substitute
  for reading the cited text.

## Citation policy

Citations point at the EU instrument (CELEX + EUR-Lex URL). National
transposition acts (NL Wbni, DE NIS2UmsuCG, FR transposition loi, …)
preserve Art. 21(2) vocabulary verbatim and are not branched here.

## ID conventions

Mapping IDs are `nis2:art-<n>-<sub>` (e.g. `nis2:art-21-2-a`,
`nis2:art-23-early-warning`). Slug parts use kebab-case. The full
addressable scheme is in `schemas/mapping.schema.json`.

## Validation

Validated by `tests/content/test_mappings.py` against
`schemas/mapping.schema.json` (JSON Schema Draft 2020-12).
