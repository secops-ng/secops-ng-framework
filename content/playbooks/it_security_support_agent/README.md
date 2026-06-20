# it_security_support_agent

Ticket-shaped support-interaction workflow for operators who need to
demonstrate, on every IT and security support request handled by an
automated front-line, that the request was either resolved via the
declared self-service surface or **explicitly handed off to a human
responder** — never silently auto-closed.

This workflow opens the **NIS2 Article 21(2)(b)** support-to-incident
handoff surface alongside the F-WF-05 incident-management workflow
(`playbook.incident_management@v1`) — F-WF-05 is the read/triage/
contain/close lifecycle for an incident that already exists; this
workflow is the front-line interaction that decides whether a support
request becomes one. Both anchor onto the same F-CP-02 incidents
evidence stream and the same `nis2:art-21-2-b` clause mapping.

The workflow emits one interaction-evidence artifact per support
request against
[`schemas/evidence/incidents.schema.json`](../../../schemas/evidence/incidents.schema.json),
feeding the F-CP-02 incidents evidence stream under
[`content/evidence/incidents/`](../../evidence/incidents/). Support
interactions that close on automated resolution emit on the schema's
intake-only audit-close branch (`classification.significant=false`);
support interactions that fire a human handoff emit with
`classification.significant=true` so the incident-handling KPI surface
counts them once on the same NIS2 Article 21(2)(b) anchor F-WF-05
discharges.

## Maturity

`SKELETON` — scope is the CACAO topology plus the `x_secops_ng` joins
into the control / telemetry layers. No compiler emitters, no
per-target byte-parity goldens, and no canonical primitive bindings
at this layer; those land in the sibling CORE / EXTEND cards (see
[Pending siblings](#pending-siblings)).

## State machine

```
workflow_start
   -> ingest-support-request
   -> classify-request
   -> attempt-automated-resolution
   -> escalate-with-human-handoff
   -> emit-interaction-evidence
   -> workflow_end
```

Transitions are deterministic — every state has exactly one
`on_completion` successor, no conditional branching at this layer.
The handoff decision is encoded inside
`escalate-with-human-handoff` rather than as a conditional edge:
the step ALWAYS runs and materialises a closed handoff envelope
(with `handoff_fired` set accordingly) so the downstream evidence
artifact can pin the path explicitly.

| State                              | Purpose                                                                                                                                                                                                                                            |
|------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ingest-support-request`           | Read the support-request record referenced by `__support_request_ref__` from the operator-supplied ticketing source and bind it to a normalised in-workflow request record. Read-only by contract.                                                  |
| `classify-request`                 | Classify the request against the operator's policy. Closed verdict: `category` in {informational, actionable, incident-shaped}, severity band, ordered rule_ids. Deterministic on the same record + same policy version.                            |
| `attempt-automated-resolution`     | Attempt the declared automated-resolution path against the operator's self-service surface. Bounded by the operator-declared action set. Closed observation envelope on every outcome.                                                              |
| `escalate-with-human-handoff`      | **First-class explicit handoff step.** A support interaction MUST end with either an automated-resolution closure or a confirmed handoff to a human responder — never a silent auto-close. The handoff envelope is materialised on every execution. |
| `emit-interaction-evidence`        | Combine the closed envelopes into one interaction-evidence artifact against `schemas/evidence/incidents.schema.json`. Reuses the F-CP-02 incidents stream — significant=true on handoff, significant=false on automated closure.                    |

## Regulatory anchor

NIS2 Article 21(2)(b) — incident-handling capability. The
support-to-incident handoff is the front-line entry into the
incident-handling lifecycle the F-WF-05 incident-management workflow
discharges. Mapping entry:
[`content/mappings/nis2/article-21-2-b.yaml`](../../mappings/nis2/article-21-2-b.yaml)
(`nis2:art-21-2-b`). The mapping references both this playbook and
`playbook.incident_management@v1` — the two workflows discharge
complementary halves of the same obligation surface (front-line
support interaction → incident handoff → incident lifecycle).

## Relation to F-WF-05 incident management

F-WF-05 incident management (`playbook.incident_management@v1`) is the
**lifecycle owner** for an incident that has already been opened —
classify-significance, contain, eradicate, recover, and emit the
significance-anchored evidence artifact under the same incidents
stream. This workflow is the **interaction front-line**: one
support request per execution, classified, attempted-automatically,
and either closed or explicitly handed off to the human responder
that opens the incident on the F-WF-05 lifecycle. Both anchor onto
the same F-CP-02 incidents evidence stream and the same
`schemas/evidence/incidents.schema.json` artifact shape — the F-CP-02
schema already carries the closed `classification` envelope (with
`significant` and `cross_border` flags) that suffices for both
surfaces, so no new evidence schema is introduced at this SKELETON
layer.

## Reused evidence schema

The interaction-evidence shape this workflow emits is
`schemas/evidence/incidents.schema.json` (the F-CP-02 stream). The
schema's `classification` block (with the `significant=false`
intake-only audit-close branch) and `lifecycle` envelope together
suffice for the support-interaction evidence this workflow produces:
the support-only closure path emits on the intake-only branch, and
the handoff path emits with `significant=true` so the F-CP-02 incident
KPI surface picks it up exactly once. No new evidence schema is
introduced at the SKELETON layer.

## Sovereign-stack default

The ticketing source that `ingest-support-request` reads, the
self-service surface that `attempt-automated-resolution` calls
against, the responder-queue surface that
`escalate-with-human-handoff` acknowledges against, and the artifact
destination that `emit-interaction-evidence` writes to are all
operator-configured. No default hosted helpdesk, no ITSM-SaaS
dependency, no default non-EU endpoint, no vendor SDK bundled. The
responder-queue handle is role-shaped (responder rota, automation
responder role, on-call shift handle) by contract — personal-user
responder handles are rejected at the primitive boundary.

## Files

- `playbook.cacao.json` — the CACAO v2 skeleton
  (`playbook.it_security_support_agent@v1`). Step bodies are
  declarative placeholders at this layer (no primitive bindings yet);
  the canonical primitive set lands in the CORE-FANOUT sibling cards.

## Pending siblings

Queued serially after this SKELETON merges:

- **CORE-FANOUT-{N8N,TMP,LG}** — per-target compiler emitters and
  byte-parity goldens under
  `examples/{n8n,temporal,langgraph}/it_security_support_agent/`.
  Each target's CORE sibling binds its `x_secops_ng.core_body` to a
  deterministic primitive set under
  `content.playbooks.it_security_support_agent.primitives.*`.
- **EXTEND-schema** — if the closed `classification` +
  `lifecycle` envelope on `schemas/evidence/incidents.schema.json`
  proves insufficient for the support-interaction sub-shape
  (request_kind + automated_resolution.outcome + handoff envelope
  tightening), introduce a bounded extension under the same stream
  rather than a new stream.
- **EXTEND-metrics** — automated-resolution-rate KPI and
  handoff-acknowledgement-time KRI under `content/metrics/`. No
  metric_refs are pinned at the SKELETON layer to keep the repo-wide
  metric-link guard green.
- **EXTEND-docs-closeout** — flip ROADMAP F-WF-12 Proposed → Shipped
  and add the cookbook walkthrough.
