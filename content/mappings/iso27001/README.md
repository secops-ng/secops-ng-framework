# content/mappings/iso27001/

ISO/IEC 27001:2022 crosswalk.

## File convention

One YAML file per Annex A theme. The 2022 revision groups Annex A
controls into four themes:

| Theme | File | Controls |
|-------|------|----------|
| A.5 Organisational | `annex-a-5-organisational.yaml` | 37 |
| A.6 People | `annex-a-6-people.yaml` | 8 |
| A.7 Physical | `annex-a-7-physical.yaml` | 14 |
| A.8 Technological | `annex-a-8-technological.yaml` | 34 |

Each entry inside a theme file targets one numbered Annex A control,
with `id: iso27001:a-<theme>-<number>-<slug>` (kebab-case slug). See
`../README.md` for the schema-level shape and the canonical URN scheme
for artifact refs.

## Status

Draft. First entry (`iso27001:a-5-1-policies`, Annex A.5.1 Policies for
information security) establishes the conventions; sibling entries and
theme files land as subsequent cards close them.

The A.6 people-controls theme file has landed with its first two
entries (`iso27001:a-6-1-screening`, `iso27001:a-6-3-awareness`) in
`annex-a-6-people.yaml`; the remaining A.6 controls (A.6.2, A.6.4
through A.6.8) land as sibling entries in that file on subsequent
cards.

The A.7 physical-controls theme file has landed with its first two
entries (`iso27001:a-7-1-physical-security-perimeters`,
`iso27001:a-7-2-physical-entry`) in `annex-a-7-physical.yaml`; both
ship with empty `control_refs` because the SecOps-NG control catalogue
is currently scoped to logical / cyber controls (see the coverage note
in the theme file header). The remaining A.7 controls (A.7.3 through
A.7.14) land as sibling entries in that file on subsequent cards.
