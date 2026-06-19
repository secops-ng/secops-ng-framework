# Examples

Worked examples that show end-to-end use of SecOps-NG content artifacts
(CACAO playbooks, mappings, OCSF shapes, KPI/KRI catalog) through the
reference compilers into the orchestrator targets.

## Reference compilers

- [`langgraph/`](langgraph/) — agentic reference target. Worked
  examples of CACAO playbooks compiled to runnable LangGraph agent
  graphs.
- [`n8n/`](n8n/) — no-code reference target. Worked examples of CACAO
  playbooks compiled to n8n workflow JSON.
- [`temporal/`](temporal/) — durable-code reference target. Worked
  examples of CACAO playbooks compiled to Temporal workflow stubs.

| Playbook              | n8n                                                              | Temporal                                                                   |
|-----------------------|------------------------------------------------------------------|----------------------------------------------------------------------------|
| threat_intel_ingest   | [`n8n/threat_intel_ingest/`](n8n/threat_intel_ingest/)           | [`temporal/threat_intel_ingest/`](temporal/threat_intel_ingest/)           |

Additional rows land alongside their compiler outputs.
