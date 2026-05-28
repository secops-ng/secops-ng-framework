# threat-intel-ingest — n8n worked example

Emitted from `content/playbooks/threat-intel-ingest/playbook.cacao.json`
via `python -m compilers.n8n`.

- `playbook.cacao.json` — source CACAO playbook (copy of the canonical
  authored file under `content/`).
- `workflow.n8n.json` — n8n workflow JSON, import-ready via
  `n8n import:workflow` or the n8n REST API.

The emitter is deterministic: regenerating produces byte-identical
output. The `meta.secops_ng_notes` block on the workflow records any
lossy translations so a reviewer can see what was simplified without
diffing the source playbook.
