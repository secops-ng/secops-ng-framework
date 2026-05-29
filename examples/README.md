# Examples

Worked examples that show end-to-end use of SecOps-NG content artifacts
(CACAO playbooks, mappings, OCSF shapes, KPI/KRI catalog) through the
reference compilers into the orchestrator targets.

## Reference compilers

- [`langgraph/`](langgraph/) — agentic reference target. Worked
  examples of CACAO playbooks compiled to runnable LangGraph agent
  graphs.
- [`temporal/`](temporal/) — durable-code reference target. Worked
  examples of CACAO playbooks compiled to Temporal workflow stubs.

| Playbook              | Temporal                                                              |
|-----------------------|-----------------------------------------------------------------------|
| threat-intel-ingest   | [`temporal/threat-intel-ingest/`](temporal/threat-intel-ingest/)      |

Additional targets (n8n) will land alongside their compilers.
