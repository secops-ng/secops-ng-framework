# data_exfil

CACAO v2 starter playbook for responding to a confirmed-or-suspected
data-exfiltration signal: DLP / egress signal → scope assessment →
containment → regulator / customer notification gate.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact (`playbook.data_exfil@v1`).

## Worked example

The cross-layer worked example — detection, control, telemetry, and
metrics artifacts that bind to this playbook — lives at
`../../../content-model/examples/data_exfil/`. Start with the README
there for the cross-reference graph and per-artifact stable IDs.

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. Emitted
artifacts under `examples/{n8n,temporal,langgraph}/data_exfil/` are
authored by the CORE card; this directory ships the
portable content only.

## Sources

- OASIS CACAO v2.0 specification
- ENISA — Threat Landscape and Good Practices for Incident Notification
- NIS2 Directive (EU) 2022/2555, Article 23 — incident reporting obligations
- DORA Regulation (EU) 2022/2554, Article 19 — reporting of major ICT-related incidents
- OCSF — DLP Activity and Security Finding event classes
- SigmaHQ — upstream rule IDs referenced in the detection layer
