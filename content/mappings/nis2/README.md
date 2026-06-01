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

## OSCAL component-definition

`oscal-component-definition.json` is an OSCAL 1.1.2
component-definition document that exposes the same control coverage in
the NIST OSCAL serialization. One component (SecOps-NG) carries one
control-implementation set whose `implemented-requirements` mirror the
entries in `article-21-and-23.yaml`: one implemented-requirement per
mapping entry, covering Article 21(2)(a)–(j) risk-management measures
(10 entries) and the Article 23(4) incident-notification timeline
(3 entries: early-warning at 24h, notification at 72h, final report at
one month). Entries with multiple `control_refs` emit repeated
`source-control-ref` props on the same implemented-requirement, keyed
back to the primary control via `control-id`. Statement text is borrowed
verbatim from each entry's `obligation` field. Schema-validation and
YAML-coverage parity are enforced by
`tests/content/test_oscal_nis2_component_definition.py` against the
OSCAL component schema vendored under
`tests/fixtures/oscal/oscal_component_schema-v1.1.2.json`. The DORA and
CRA OSCAL component-definitions are sibling artifacts tracked
separately.
