# schemas/

JSON Schema for every portable artifact shape:

- `playbook.schema.json`   CACAO v2 superset used by `../content/playbooks/`
- `metric.schema.json`     KPI / KRI entry shape
- `mapping.schema.json`    regulatory mapping document shape used by `../content/mappings/<regime>/*.yaml`
- `control.schema.json`    OSCAL component / D3FEND mapping shape

Validated by `tools/validate/`.
