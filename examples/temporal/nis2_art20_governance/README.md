# examples/temporal/nis2_art20_governance

Worked example: the `playbook.nis2_art20_governance@v1` CACAO v2
playbook compiled by the Temporal reference compiler. The emitted
`workflow.temporal.py` module carries a `@workflow.defn` orchestration
and one `@activity.defn` per CACAO action step, with the CACAO
control flow projected onto deterministic Temporal awaitables.

The activity bodies raise `NotImplementedError` at the SKELETON
layer: schedule-management-review, present-risk-posture,
approve-risk-measures, and log-governance-evidence are each stubbed
at the primitive boundary. Sibling CORE-PRIMITIVES landed the
primitive bindings (governance-cadence catalogue probe, evidence-store
posture-snapshot composition, management-body decision-record shape,
OCSF API Activity governance-record emission) which the operator
wires into these activity shells.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/nis2_art20_governance/playbook.cacao.json

Regulatory anchors (NIS2 Directive (EU) 2022/2555 Article 20(1)
management-body approval, Article 20(2) management-body training,
Article 21(2)(a)–(j) downstream obligation surface) and OSCAL /
D3FEND / OCSF control bindings are documented in the sibling
`mappings.yaml`. This folder holds the emitted artifact, a co-located
byte-identical mirror of the CACAO source for easy diff inspection,
and the regeneration script.

## Layout

| Path                    | Source compiler       | Format            |
|-------------------------|-----------------------|-------------------|
| `playbook.cacao.json`   | (input mirror)        | CACAO v2 JSON     |
| `workflow.temporal.py`  | `compilers.temporal`  | Python stub       |
| `regenerate.sh`         | (tooling)             | bash script       |

## How to regenerate

From the repository root:

```sh
examples/temporal/nis2_art20_governance/regenerate.sh
```

The script mirrors the canonical CACAO source and re-emits
`workflow.temporal.py` via the unified compile CLI.

## Sovereign-stack default

The Temporal cluster the workflow runs on is operator-hosted; no
hosted Temporal SaaS default is assumed. The activity bodies are
expected to bind against the operator's own governance-cadence
catalogue, evidence store, and management-body approval-record
surface — no proprietary governance-tooling SDK is assumed and no
non-EU compliance-SaaS adapter is modelled anywhere in the stub.
