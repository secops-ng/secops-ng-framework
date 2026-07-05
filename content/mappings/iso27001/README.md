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
