# LangGraph worked examples

End-to-end demonstrations of the LangGraph reference compiler: how a
portable CACAO playbook is lowered into a runnable agent graph that an
integrator can drop into their own `langgraph.graph.StateGraph`
runtime.

## Index

- [`vuln_intake/`](vuln_intake/) — vulnerability intake playbook. The
  first end-to-end worked example: portable CACAO playbook →
  GraphSpec JSON → generated state + `@tool` bindings → reference
  assembly. Includes a regeneration script and a drift test so the
  artifacts stay in lockstep with the compiler.
- [`threat_intel_ingest/`](threat_intel_ingest/) — threat-intelligence
  ingest playbook. Pull → normalise → confidence-threshold branch into
  blocklist propagation or detection-only activation.
- [`phishing_triage/`](phishing_triage/) — phishing_triage playbook.
  Ingest reported / mailbox-sweep email → enrich with email-security
  gateway, URL sandbox, attachment sandbox → suppression-cache check →
  intent classification → response branch (containment + ticketing or
  user-feedback close).
- [`identity_compromise/`](identity_compromise/) — identity_compromise
  response playbook. Triage identity signal → confirmation branch →
  MFA reset → session revocation → lateral-movement hunt → IAM audit
  and persistence removal.
- [`incident_management/`](incident_management/) — incident_management
  playbook (NIS2 Article 23 three-stage regulator timeline). Intake
  signal → classify significance + cross-border scope → open timeline
  → 24-hour early warning → 72-hour notification → optional one-month
  final report → close timeline. SKELETON state — `@tool` bodies raise
  `NotImplementedError` pending the CORE-PRIM card.

More worked examples land here as additional playbooks ship under
`content/playbooks/`. Each follows the same shape — playbook,
regenerated artifacts, hand-written assembly, sovereignty note — so
the directory stays predictable to read.

LangGraph is one of three reference compile targets (alongside n8n and
Temporal). The framework itself remains runtime-agnostic; these
examples exist so integrators who already run LangGraph can adopt
SecOps-NG playbooks without re-platforming.
