# threat-intel-ingest

Starter playbook for ingesting external cyber threat intelligence,
normalising indicators against OCSF, and propagating the result to
detection (Sigma rule activation) and blocking (network / EDR
blocklist) controls.

## Files

- `playbook.cacao.json` — OASIS CACAO v2 portable response, extended
  with the SecOps-NG content-model join keys under `x_secops_ng`.
- `mappings.yaml` — Sigma rule IDs (pointers to upstream SigmaHQ),
  OSCAL controls, MITRE D3FEND techniques, OCSF event classes,
  KPI/KRI metrics, NIS2 + DORA regulatory cross-references.

## Compile-target worked examples

The same `playbook.cacao.json` compiles to every reference target.
Generated artifacts live under `examples/`:

- `examples/n8n/threat-intel-ingest/workflow.n8n.json`
- `examples/temporal/threat-intel-ingest/workflow.py`
- `examples/langgraph/threat-intel-ingest/graph_spec.json`

Each target directory mirrors the source CACAO playbook alongside the
emitted artifact so a reviewer can diff portable intent against
target-native shape without leaving the directory.

To regenerate:

```
python -m compilers.n8n        content/playbooks/threat-intel-ingest/playbook.cacao.json --out examples/n8n/threat-intel-ingest/workflow.n8n.json
python -m compilers.temporal   content/playbooks/threat-intel-ingest/playbook.cacao.json --out examples/temporal/threat-intel-ingest/workflow.py
python -m compilers.langgraph  content/playbooks/threat-intel-ingest/playbook.cacao.json --out examples/langgraph/threat-intel-ingest/graph_spec.json
```

## Scope notes

- Sigma rule bodies live upstream at SigmaHQ; we ship IDs and a pointer
  only.
- Feed URLs and provider credentials are operator-supplied and injected
  at compile-target runtime (directive #6 — never embed secrets).
- Sovereign-provider classification (residency, ownership,
  sub-processor chain) reads from a private KB at runtime; this repo
  never ingests KB contents.
