# examples/n8n/eidas2_identity_verification

Worked example: the `playbook.eidas2_identity_verification@v1` CACAO
v2 playbook compiled by the n8n reference compiler. Operators can
import `workflow.n8n.json` into an n8n instance to see the topology
the emitter produces for the eIDAS 2.0 EUDIW identity-verification
lifecycle (request-EUDIW-presentation → verify-PID-credential →
assess-assurance-level → emit-identity-audit-evidence →
trigger-access-provisioning).

Binding the placeholder Set-node steps to real connectors — the
OpenID4VP presentation-request adapter, the trust-anchor-registry
probe against the Member-State Trusted List / LOTL aggregator, the
LoA-to-access-tier mapping table, the OCSF Account Change evidence
sink, and the downstream `onboarding_offboarding_tracker` hand-off —
is the operator's job. The framework ships no default endpoint and
no non-EU trust-anchor SDK.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/eidas2_identity_verification/playbook.cacao.json

Scenario, workflow, regulatory anchors (NIS2 Art. 21(2)(i) /
DORA Art. 5 / eIDAS 2.0), and OSCAL / D3FEND control bindings are
documented in that folder's `mappings.yaml`. This folder holds the
emitted artifact, a co-located byte-identical copy of the CACAO
source for easy diff inspection, and the regeneration script.

## Layout

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input mirror)  | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |
| `regenerate.sh`       | (tooling)       | bash script       |

## How to regenerate

From the repository root:

```sh
examples/n8n/eidas2_identity_verification/regenerate.sh
```

The script copies the canonical CACAO source over the local mirror
and re-emits `workflow.n8n.json` via the unified compile CLI.

## Sovereign-stack default

The wallet-side surface, the trust-anchor registry the credential
issuer resolves against, and the identity-verification audit-evidence
store the workflow writes to are operator-configured. No default
hosted verifier, no non-EU trust anchor assumed, no Microsoft /
Google EUDIW proxy modelled. The trust-anchor probe is expected to
resolve against Member-State Trusted Lists and the LOTL aggregator
per Commission Implementing Decision (EU) 2015/1505 as maintained
under eIDAS 2.0.
