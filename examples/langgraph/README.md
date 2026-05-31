# LangGraph worked examples

End-to-end demonstrations of the LangGraph reference compiler: how a
portable CACAO playbook is lowered into a runnable agent graph that an
integrator can drop into their own `langgraph.graph.StateGraph`
runtime.

## Index

- [`vuln-intake/`](vuln-intake/) — vulnerability intake playbook. The
  first end-to-end worked example: portable CACAO playbook →
  GraphSpec JSON → generated state + `@tool` bindings → reference
  assembly. Includes a regeneration script and a drift test so the
  artifacts stay in lockstep with the compiler.
- [`threat-intel-ingest/`](threat-intel-ingest/) — threat-intelligence
  ingest playbook. Pull → normalise → confidence-threshold branch into
  blocklist propagation or detection-only activation.
- [`phishing-triage/`](phishing-triage/) — phishing-triage playbook.
  Ingest reported / mailbox-sweep email → enrich with email-security
  gateway, URL sandbox, attachment sandbox → suppression-cache check →
  intent classification → response branch (containment + ticketing or
  user-feedback close).

More worked examples land here as additional playbooks ship under
`content/playbooks/`. Each follows the same shape — playbook,
regenerated artifacts, hand-written assembly, sovereignty note — so
the directory stays predictable to read.

LangGraph is one of three reference compile targets (alongside n8n and
Temporal). The framework itself remains runtime-agnostic; these
examples exist so integrators who already run LangGraph can adopt
SecOps-NG playbooks without re-platforming.
