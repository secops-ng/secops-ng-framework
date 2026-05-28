# examples/

End-to-end demos. Each subdirectory is a single CACAO playbook compiled
to every reference target (n8n, Temporal, LangGraph), with the input
playbook, the generated artifacts, and a short walkthrough.

## Index

- `n8n/threat-intel-ingest/`        — threat-intel ingest compiled to n8n
- `temporal/threat-intel-ingest/`   — threat-intel ingest compiled to Temporal
- `langgraph/threat-intel-ingest/`  — threat-intel ingest compiled to LangGraph

The canonical authored playbooks live under
`content/playbooks/<slug>/playbook.cacao.json`; the per-target
directories carry a copy of the source plus the generated artifact so a
reviewer can diff portable intent against target-native shape without
leaving the directory.
