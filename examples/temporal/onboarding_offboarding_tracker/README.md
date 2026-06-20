# examples/temporal/onboarding_offboarding_tracker

SKELETON-FANOUT scaffold shell. This directory pins the operator-facing
layout for the temporal worked example of the
`playbook.onboarding_offboarding_tracker@v1` on-boarding /
off-boarding tracker workflow (F-WF-11; NIS2 Article 21(2)(i)). The
canonical CACAO source lives at
`../../../content/playbooks/onboarding_offboarding_tracker/playbook.cacao.json`
and is mirrored here byte-identical so the diff against the eventual
emitted artefact is easy to inspect.

## Maturity

`SKELETON-FANOUT` — scaffold only. No temporal workflow emitter binding,
no representative access-evidence artifact, and no byte-parity
golden under `tests/examples/temporal/onboarding_offboarding_tracker/` at
this layer. The compiler emitter, the per-execution evidence
artifact, and the byte-parity golden land in the F-WF-11
CORE-FANOUT-TMP sibling card queued serially after this SKELETON
merges (to avoid concurrent byte-parity golden churn across the
three targets).

## Layout

| Path                       | Source compiler          | Status at SKELETON                                                          |
|----------------------------|--------------------------|-----------------------------------------------------------------------------|
| `playbook.cacao.json`      | (input mirror)           | Byte-identical mirror of the canonical SKELETON playbook                    |
| `regenerate.sh`            | (tooling)                | Re-mirrors the canonical playbook into this directory                       |
| `regenerate.py`            | (tooling)                | Placeholder; no evidence emitter bound until CORE-FANOUT-TMP                |
| `workflow.temporal.py`        | `compilers.temporal`          | **Not present at SKELETON.** Emitted in CORE-FANOUT-TMP.                    |
| `evidence/`                | (per-execution output)   | Placeholder; representative access-evidence artifact lands in CORE-FANOUT-TMP |

## How to regenerate (SKELETON)

From the repository root:

```sh
examples/temporal/onboarding_offboarding_tracker/regenerate.sh
```

The script copies the canonical CACAO source over the local mirror so
this directory stays in sync with
`content/playbooks/onboarding_offboarding_tracker/`. It does **not**
emit a temporal workflow artefact at this layer — the canonical playbook
ships with declarative placeholder step bodies (no `core_body`
bindings), so there are no primitive bindings for the temporal compiler
emitter to translate yet. The emitter and the worked-artefact
emission land in F-WF-11 CORE-FANOUT-TMP.

## Source

- Canonical playbook: [`content/playbooks/onboarding_offboarding_tracker/`](../../../content/playbooks/onboarding_offboarding_tracker/)
- Access-evidence schema (reused from F-CP-07): [`schemas/evidence/access.schema.json`](../../../schemas/evidence/access.schema.json)
- Access evidence stream contributor home: [`content/evidence/access/`](../../../content/evidence/access/)
- Regulatory anchor (NIS2 Article 21(2)(i)): [`content/mappings/nis2/article-21-2-i.yaml`](../../../content/mappings/nis2/article-21-2-i.yaml)

## Sovereign-stack default

The identity source the workflow reads and writes, and the
access-evidence store the emitted artifact targets, are
operator-configured. No default hosted IdP, no HR-SaaS dependency, no
default non-EU endpoint, no vendor SDK bundled. The reference n8n
compile-target binding lands in F-WF-11 CORE-FANOUT-TMP.
