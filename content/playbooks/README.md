# content/playbooks/

CACAO v2 response playbooks. One directory per scenario, each containing:

- `playbook.cacao.json`  the canonical artifact (CACAO v2 superset)
- `README.md`            human-readable description, prerequisites, expected telemetry
- `fixtures/`            sample input / output for compiler tests
- `mappings.yaml`        links into `../mappings/`, `../controls/`, `../metrics/`

Starter scenarios are placeholder directories; playbook authoring is tracked
by separate cards.
