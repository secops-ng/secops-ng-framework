# onboarding_offboarding_tracker

Identity-lifecycle grant/revoke-confirmation tracker for operators who
need to demonstrate, on every joiner / mover / leaver event against a
role-shaped runtime principal, that the declared capability delta was
applied and confirmed on the principal's downstream capability
surface.

This workflow opens the **NIS2 Article 21(2)(i)** joiner-mover-leaver
workflow surface alongside the F-WF-08 IAM auditor
(`playbook.iam_auditor@v1`) — the IAM auditor produces the
per-execution capability inventory of the caller that invoked any
compiled workflow; this workflow produces the per-lifecycle-event
grant/revoke confirmation. Both anchor onto the same F-CP-07 access
evidence stream and the same `nis2:art-21-2-i` clause mapping.

The workflow emits one access-evidence artifact per lifecycle event
against
[`schemas/evidence/access.schema.json`](../../../schemas/evidence/access.schema.json),
feeding the F-CP-07 access evidence stream under
[`content/evidence/access/`](../../evidence/access/).

## Maturity

`SKELETON` — scope is the CACAO topology plus the `x_secops_ng` joins
into the control / telemetry layers. No compiler emitters, no
per-target byte-parity goldens, and no canonical primitive bindings
at this layer; those land in the sibling CORE / EXTEND cards (see
[Pending siblings](#pending-siblings)).

## State machine

```
workflow_start
   -> ingest-lifecycle-event
   -> resolve-identity
   -> apply-capability-delta
   -> confirm-grant-revoke
   -> emit-access-evidence
   -> workflow_end
```

Transitions are deterministic — every state has exactly one
`on_completion` successor, no conditional branching at this layer.

| State                      | Purpose                                                                                                                                                                                                                          |
|----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ingest-lifecycle-event`   | Read the lifecycle-event record (joiner, mover, leaver) referenced by `__lifecycle_event_ref__` from the operator-supplied identity source and bind it to a normalised in-workflow event record. Read-only by contract.            |
| `resolve-identity`         | Resolve the principal handle against the operator's identity source. Principal is role-shaped — service-account, workflow-runtime, or automation role. Personal-user principals rejected at the primitive boundary.                |
| `apply-capability-delta`   | Apply the declared capability delta — grant the add-set on a joiner, adjust both sets on a mover, drain the remove-set on a leaver. Closed delta; deterministic on the same event record + same resolved principal.                |
| `confirm-grant-revoke`     | Re-read the closed capability list from the identity source and confirm the delta landed. Divergence between declared and observed surfaces as a confirmation-failure on the emitted access-evidence artifact.                     |
| `emit-access-evidence`     | Combine the resolved caller-identity block and the confirmed capability list into one access-evidence artifact against `schemas/evidence/access.schema.json`. Reuses the F-CP-07 access stream — same shape as the IAM auditor.    |

## Regulatory anchor

NIS2 Article 21(2)(i) — human-resources security, access-control
policies, and asset management (including joiner-mover-leaver
evidence, privileged-access review cadence, and asset inventory
delta capture). Mapping entry:
[`content/mappings/nis2/article-21-2-i.yaml`](../../mappings/nis2/article-21-2-i.yaml)
(`nis2:art-21-2-i`). The mapping references both this playbook and
`playbook.iam_auditor@v1` — the two workflows discharge complementary
halves of the same obligation surface.

## Relation to F-WF-08 IAM auditor

The F-WF-08 IAM auditor (`playbook.iam_auditor@v1`) is the
**read-side** capability-inventory producer: one access artifact per
workflow execution, pinning which caller invoked the running form and
which capabilities that caller held at boot. This workflow is the
**write-side** lifecycle counterpart: one access artifact per
joiner / mover / leaver event, pinning the declared capability delta
and the observed confirmation that the delta landed. Both anchor
onto the same F-CP-07 access evidence stream and the same
`schemas/evidence/access.schema.json` artifact shape — the F-CP-07
schema already carries the closed `caller_identity` + `capabilities`
envelope that suffices for both surfaces, so no new evidence schema
is introduced at this SKELETON layer.

## Reused evidence schema

The access-evidence shape this workflow emits is
`schemas/evidence/access.schema.json` (the F-CP-07 stream). The
schema's `caller_identity` block (role-shaped principal type and id)
and closed `capabilities` array (`verb.resource` tokens) suffice for
the grant/revoke-confirmation envelope this workflow produces; the
post-lifecycle capability surface IS the closed capability list the
F-CP-07 schema already pins. No new evidence schema is introduced at
the SKELETON layer.

## Sovereign-stack default

The identity source that `ingest-lifecycle-event` reads, the identity
source that `apply-capability-delta` writes to (delegated to the CORE
primitive bound in the CORE-FANOUT sibling card), and the artifact
destination that `emit-access-evidence` writes to are all
operator-configured. No default hosted IdP, no HR-SaaS dependency, no
default non-EU endpoint, no vendor SDK bundled. The principal handle
is role-shaped (service-account, workflow-runtime, automation role)
by contract — personal-user principals are rejected at the primitive
boundary.

## Files

- `playbook.cacao.json` — the CACAO v2 skeleton
  (`playbook.onboarding_offboarding_tracker@v1`). Step bodies are
  declarative placeholders at this layer (no primitive bindings yet);
  the canonical primitive set lands in the CORE-FANOUT sibling cards.

## Pending siblings

Queued serially after this SKELETON merges:

- **CORE-FANOUT-{N8N,TMP,LG}** — per-target compiler emitters and
  byte-parity goldens under
  `examples/{n8n,temporal,langgraph}/onboarding_offboarding_tracker/`.
  Each target's CORE sibling binds its `x_secops_ng.core_body` to a
  deterministic primitive set under
  `content.playbooks.onboarding_offboarding_tracker.primitives.*`.
- **EXTEND-schema** — if the closed `caller_identity` + `capabilities`
  envelope on `schemas/evidence/access.schema.json` proves
  insufficient for the lifecycle-event sub-shape (event_kind +
  declared_delta + observed_confirmation tightening), introduce a
  bounded extension under the same stream rather than a new stream.
- **EXTEND-metrics** — joiner-to-provisioned-time KRI and
  leaver-to-revoked-time KRI under `content/metrics/`. No metric_refs
  are pinned at the SKELETON layer to keep the repo-wide metric-link
  guard green.
- **EXTEND-docs-closeout** — flip ROADMAP F-WF-11 Proposed → Shipped
  and add the cookbook walkthrough.
