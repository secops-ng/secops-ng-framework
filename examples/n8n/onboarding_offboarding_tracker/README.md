# examples/n8n/onboarding_offboarding_tracker

CORE-FANOUT-N8N worked example. This directory pins the operator-facing
layout for the n8n worked example of the
`playbook.onboarding_offboarding_tracker@v1` on-boarding /
off-boarding tracker workflow (F-WF-11; NIS2 Article 21(2)(i)). The
canonical CACAO source lives at
`../../../content/playbooks/onboarding_offboarding_tracker/playbook.cacao.json`
and is mirrored here byte-identical so the diff against the emitted
artefact is easy to inspect.

## Maturity

`CORE-FANOUT-N8N` — the n8n workflow emitter is bound, the five action
bodies carry deterministic `core_body` bindings into
`content.playbooks.onboarding_offboarding_tracker.primitives.*`, and
one representative access-evidence artefact is materialised under
`evidence/`. The byte-parity goldens for this worked example land
under `tests/examples/onboarding_offboarding_tracker/`. CORE-FANOUT-TMP
and CORE-FANOUT-LG follow in serial sibling cards.

## Layout

| Path                       | Source compiler          | Status                                                                      |
|----------------------------|--------------------------|-----------------------------------------------------------------------------|
| `playbook.cacao.json`      | (input mirror)           | Byte-identical mirror of the canonical playbook                             |
| `regenerate.sh`            | (tooling)                | Re-mirrors the canonical playbook and re-emits the worked artefacts         |
| `regenerate.py`            | (tooling)                | Drives the primitive chain and the n8n access-evidence adapter              |
| `workflow.n8n.json`        | `compilers.n8n`          | Compiled n8n workflow JSON — Code-node bodies for the five CORE primitives  |
| `evidence/access-evidence.json` | `compilers.n8n.evidence` | One representative per-execution access-evidence artefact (F-CP-07 shape)   |

## How to regenerate

From the repository root:

```sh
examples/n8n/onboarding_offboarding_tracker/regenerate.sh
```

The script copies the canonical CACAO source over the local mirror,
re-emits `workflow.n8n.json` via the n8n compiler, and re-emits
`evidence/access-evidence.json` via the n8n access-evidence adapter
driven by the local `regenerate.py`.

## Source

- Canonical playbook: [`content/playbooks/onboarding_offboarding_tracker/`](../../../content/playbooks/onboarding_offboarding_tracker/)
- Primitives: [`content/playbooks/onboarding_offboarding_tracker/primitives/`](../../../content/playbooks/onboarding_offboarding_tracker/primitives/)
- Access-evidence schema (reused from F-CP-07): [`schemas/evidence/access.schema.json`](../../../schemas/evidence/access.schema.json)
- Access evidence stream contributor home: [`content/evidence/access/`](../../../content/evidence/access/)
- Regulatory anchor (NIS2 Article 21(2)(i)): [`content/mappings/nis2/article-21-2-i.yaml`](../../../content/mappings/nis2/article-21-2-i.yaml)

## Sovereign-stack default

The identity source the workflow reads and writes, and the
access-evidence store the emitted artifact targets, are
operator-configured. No default hosted IdP, no HR-SaaS dependency, no
default non-EU endpoint, no vendor SDK bundled. The reference n8n
compile target ships Code-node bodies that import from
`content.playbooks.onboarding_offboarding_tracker.primitives`; the
operator's runtime is expected to make that package importable
alongside the n8n instance.

## Relation to F-WF-08 IAM auditor

The F-WF-08 IAM auditor produces one access artifact per workflow
*execution* (the read-side capability inventory of the caller that
invoked the running form). This workflow produces one access artifact
per *lifecycle event* (the write-side joiner/mover/leaver
confirmation). Both anchor onto the same F-CP-07 access evidence
stream and the same `schemas/evidence/access.schema.json` artifact
shape — the F-CP-07 schema's closed `caller_identity` + `capabilities`
envelope suffices for both surfaces at this layer. A closed
lifecycle-event sub-shape (event_kind + declared_delta +
observed_confirmation tightening) is the EXTEND-schema sibling's job,
not CORE-FANOUT-N8N's.

## Pending siblings

Queued serially after this CORE-FANOUT-N8N merges:

- **CORE-FANOUT-TMP** — Temporal emitter and byte-parity golden under
  `examples/temporal/onboarding_offboarding_tracker/`.
- **CORE-FANOUT-LG** — LangGraph emitter and byte-parity golden under
  `examples/langgraph/onboarding_offboarding_tracker/`.
- **EXTEND-schema** — if the closed `caller_identity` + `capabilities`
  envelope on `schemas/evidence/access.schema.json` proves
  insufficient for the lifecycle-event sub-shape, introduce a bounded
  extension under the same stream rather than a new stream.
- **EXTEND-metrics** — joiner-to-provisioned-time KRI and
  leaver-to-revoked-time KRI under `content/metrics/`.
- **EXTEND-docs-closeout** — flip ROADMAP F-WF-11 Proposed → Shipped
  and add the cookbook walkthrough.
