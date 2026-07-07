# content/playbooks/

CACAO v2 response playbooks. One directory per scenario, each containing:

- `playbook.cacao.json`  the canonical artifact (CACAO v2 superset)
- `README.md`            human-readable description, prerequisites, expected telemetry
- `fixtures/`            sample input / output for compiler tests
- `mappings.yaml`        links into `../mappings/`, `../controls/`, `../metrics/`

Starter scenarios are placeholder directories; playbook authoring is tracked
by separate cards.

## Catalog

| Slug                      | Stable ID                              | Mappings overlay                                            |
|---------------------------|----------------------------------------|-------------------------------------------------------------|
| `data_exfil`              | `playbook.data_exfil@v1`               | _pending_                                                   |
| `agentic_threat_response` | `playbook.agentic_threat_response@v1`  | [`mappings.yaml`](agentic_threat_response/mappings.yaml) (SKELETON — placeholders) |
| `threat_intel_ingest`     | `playbook.threat_intel_ingest@v1`      | [`mappings.yaml`](threat_intel_ingest/mappings.yaml) (SKELETON — placeholders) |
| `eu_ai_act_risk_management` | `playbook.eu_ai_act_risk_management@v1` | [`mappings.yaml`](eu_ai_act_risk_management/mappings.yaml) (SKELETON — placeholders) |
| `cryptographic_controls`  | `playbook.cryptographic_controls@v1`   | [`mappings.yaml`](cryptographic_controls/mappings.yaml) (SKELETON — placeholders) |
| `dora_tlpt_programme`     | `playbook.dora_tlpt_programme@v1`      | [`mappings.yaml`](dora_tlpt_programme/mappings.yaml) (SKELETON — placeholders) |

The mappings overlay column links to the per-playbook `mappings.yaml`
(see `schemas/playbook-mappings.schema.json`). SKELETON rows ship
structural pointers only; sibling CORE / EXTEND cards populate real
OSCAL / D3FEND / OCSF IDs and KPI hooks.
