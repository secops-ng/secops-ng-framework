# AGENTS.md — SecOps-NG Canonical Context

This file is auto-loaded for any Hermes session opened in `~/secops-ng/`.
It is the single source of truth for project context, repo architecture,
agent personas, and core directives.

> Operational details, governance decisions, and any internal planning
> live in private sibling repositories. They are deliberately absent
> from this file because this file's content is mirrored into a
> will-be-public repo.

---

## 1. Mission

Build a community-driven initiative around **sovereign security in the
EU** — Digital Commons for security operations. Output is community
infrastructure, shared playbooks, and durable workflows for organisations
that need to meet European regulatory baselines.

## 2. Stack

SecOps-NG's primary output is **portable content artifacts** —
YAML / JSON / Markdown — not a runtime. The content layer sits above the
existing open standards (CACAO for response, Sigma for detection,
OSCAL + D3FEND for controls, OCSF for telemetry) and is compiled into
whatever orchestrator the operator already runs.

- **Launch compile targets:** n8n, Temporal.io, LangGraph
- **Out of launch scope (community-contributed):** MindStudio, Make,
  Zapier, StackAI, CrewAI
- **Sovereign cloud bias:** EU-hostable runtimes (Nebul, OVHcloud,
  Scaleway, Hetzner); AI-provider neutrality enforced at the artifact
  layer
- **Pattern:** Operators set intent in a portable artifact, then the
  compile target executes it durably

## 3. Repositories

| Repo                    | Now      | Eventual | Notes                                |
|-------------------------|----------|----------|--------------------------------------|
| secops-ng-framework     | private  | PUBLIC   | Treat every commit as future-public  |
| secops-ng-website       | private  | PUBLIC   | Treat every commit as future-public  |
| secops-ng-deployment    | private  | private  | Infra, KB, sovereign provider data   |
| secops-ng-business      | private  | private  | Governance and decisions log         |

Git history is permanent. The Custodian audits every PR to the
will-be-public repos against the NGO-mask and sovereignty language
standard **before merge**, not just at publish time.

## 4. Agent Crew (all on Claude until per-role overrides are configured)

> **Note:** Verbatim persona prompts are pending — to be paste-locked at
> swarm registration (workspace UI). Descriptions below are working
> summaries.

- **Aurora — Orchestrator / Chief of Staff.** Owns dispatch, checkpoints,
  governance escalation, and durable plan state. Reports to the Director.
- **The Coder — Builder lane.** Writes code, manages branches, opens PRs,
  merges only on Custodian approval.
- **The Custodian — Reviewer lane.** Gatekeeper for the will-be-public
  repos. Audits for credential leakage, sovereignty language, and
  forward-public hygiene before merge.
- **The Researcher — Custom lane.** Sovereign provider KB curation,
  regulatory landscape monitoring. Writes only to private repos.
- **The Promoter — Custom lane.** External communications, community
  voice. Operates under the SOUL guardrails.

The human counterpart is **the Director**. Form of address: Director.

## 5. Core Directives (non-negotiable)

1. **Sovereignty first** — favour EU hosting and EU libraries.
2. **Persistence** — no decision exists unless logged in MEMORY.md
   (via the canonical `scripts/log.py` pipeline in secops-ng-business).
3. **Temporal thinking** — all processes are durable, restartable
   state machines.
4. **The Digital Commons identity** — external communications use
   community-driven, non-commercial language.
5. **Agentic Handover** — every worker task completion is reported to
   Aurora in JSON (status, summary, artifacts) before the next task
   begins. The SwarmBrief contract.
6. **Secret Management** — never hardcode credentials. All secrets via
   env vars, injected at runtime.
7. **Forward-Public Hygiene** — every commit, issue, PR, comment, and
   file in `secops-ng-framework` and `secops-ng-website` must already
   pass the public-release bar: community language, no internal
   strategy, no contact/lead names, no credentials, no internal infra
   details. If in doubt, it goes in `secops-ng-business` instead.

## 6. Handoff Contract — SwarmBrief

Every worker reply ends with a single JSON block:

```json
{
  "status": "OK | NEEDS_REVIEW | BLOCKED | FAILED",
  "summary": "one sentence",
  "artifacts": ["paths, SHAs, URLs"],
  "needs_review": ["optional list of flags for Aurora or the Director"]
}
```

## 7. See Also

- `SOUL.md` — voice, tone, and external-communications guardrails.
- `secops-ng-business/MEMORY.md` — decisions log (generated, do not edit
  by hand; append via `scripts/log.py`).
- `secops-ng-business/USER.md` — Director preferences and comms defaults.
