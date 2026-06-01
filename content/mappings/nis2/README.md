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

## Files

- `article-21-2-a.yaml` — Art. 21(2)(a) risk-analysis and
  information-system-security policies.
- `article-21-2-b.yaml` — Art. 21(2)(b) incident-handling capability.
- `article-21-2-c.yaml` — Art. 21(2)(c) business continuity, backup, and
  disaster recovery.
- `article-21-2-d.yaml` — Art. 21(2)(d) supply-chain security.
- `article-21-2-e.yaml` — Art. 21(2)(e) security in acquisition,
  development and maintenance (SBOM, vulnerability handling).
- `article-21-2-f.yaml` — Art. 21(2)(f) effectiveness assessment of
  risk-management measures.
- `article-21-2-g.yaml` — Art. 21(2)(g) basic cyber-hygiene and training.
- `article-21-2-h.yaml` — Art. 21(2)(h) cryptography and encryption.
- `article-21-2-i.yaml` — Art. 21(2)(i) HR security, access control,
  asset management.
- `article-21-2-j.yaml` — Art. 21(2)(j) authentication and secured
  communications.
- `article-23.yaml` — Art. 23(4) incident-notification timeline
  (early-warning at 24h, notification at 72h, final report at one month).

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
entries in `article-21-2-a.yaml` … `article-21-2-j.yaml` and
`article-23.yaml`: one implemented-requirement per mapping entry,
covering Article 21(2)(a)–(j) risk-management measures (10 entries) and
the Article 23(4) incident-notification timeline (3 entries:
early-warning at 24h, notification at 72h, final report at one month).
Entries with multiple `control_refs` emit repeated
`source-control-ref` props on the same implemented-requirement, keyed
back to the primary control via `control-id`. Statement text is borrowed
verbatim from each entry's `obligation` field. Schema-validation and
YAML-coverage parity are enforced by
`tests/content/test_oscal_nis2_component_definition.py` against the
OSCAL component schema vendored under
`tests/fixtures/oscal/oscal_component_schema-v1.1.2.json`. The DORA and
CRA OSCAL component-definitions are sibling artifacts tracked
separately.
