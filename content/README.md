# content/

Portable, vendor-neutral artifacts. Plain YAML / JSON / Markdown.
Every file in this tree must be runtime-agnostic — no orchestrator-specific
syntax, no embedded credentials, no model choices baked in.

Subtrees:

- `playbooks/`   CACAO v2 response playbooks, one directory per scenario.
- `detections/`  Curated *references* to Sigma rules (we do not fork rules).
- `controls/`    OSCAL component definitions and D3FEND tactic mappings.
- `telemetry/`   OCSF event schema bindings and sample payloads.
- `metrics/`     KPI / KRI catalog as YAML.
- `mappings/`    Regulatory crosswalks (NIS2, DORA, CRA, GDPR, ISO 27001, SOC 2).
