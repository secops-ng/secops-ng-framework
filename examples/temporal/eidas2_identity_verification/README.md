# examples/temporal/eidas2_identity_verification

Worked example: the `playbook.eidas2_identity_verification@v1` CACAO
v2 playbook compiled by the Temporal reference compiler. The emitted
`workflow.temporal.py` module carries a `@workflow.defn` orchestration
and one `@activity.defn` per CACAO action step, with the CACAO
control flow projected onto deterministic Temporal awaitables.

The activity bodies raise `NotImplementedError` at the SKELETON
layer: request-EUDIW-presentation, verify-PID-credential,
assess-assurance-level, emit-identity-audit-evidence, and
trigger-access-provisioning are each stubbed at the primitive
boundary. Sibling CORE-FANOUT cards land the primitive bindings
(OpenID4VP relying-party surface, trust-anchor-registry probe,
LoA-to-access-tier mapping, OCSF Account Change evidence emission,
onboarding hand-off).

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/eidas2_identity_verification/playbook.cacao.json

Regulatory anchors (NIS2 Art. 21(2)(i), DORA Art. 5, eIDAS 2.0) and
OSCAL / D3FEND / OCSF control bindings are documented in the
sibling `mappings.yaml`. This folder holds the emitted artifact, a
co-located byte-identical mirror of the CACAO source for easy diff
inspection, and the regeneration script.

## Layout

| Path                    | Source compiler       | Format            |
|-------------------------|-----------------------|-------------------|
| `playbook.cacao.json`   | (input mirror)        | CACAO v2 JSON     |
| `workflow.temporal.py`  | `compilers.temporal`  | Python stub       |
| `regenerate.sh`         | (tooling)             | bash script       |

## How to regenerate

From the repository root:

```sh
examples/temporal/eidas2_identity_verification/regenerate.sh
```

The script mirrors the canonical CACAO source and re-emits
`workflow.temporal.py` via the unified compile CLI.

## Sovereign-stack default

The Temporal cluster the workflow runs on is operator-hosted; no
hosted Temporal SaaS default is assumed. The activity bodies are
expected to bind against the operator's own OpenID4VP verifier and
EU trust-anchor registry — no non-EU trust anchor is modelled and
no Microsoft / Google EUDIW proxy surface is assumed anywhere in
the stub.
