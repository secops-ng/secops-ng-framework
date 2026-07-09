# examples/n8n/nis2_art20_governance

Worked example: the `playbook.nis2_art20_governance@v1` CACAO v2
playbook compiled by the n8n reference compiler. Operators can
import `workflow.n8n.json` into an n8n instance to see the topology
the emitter produces for the NIS2 Article 20 management-body
cybersecurity governance lifecycle (schedule-management-review →
present-risk-posture → approve-risk-measures →
log-governance-evidence).

Binding the placeholder Set-node steps to real connectors — the
operator's governance-cadence catalogue probe, the evidence-store
probe that composes the per-cycle Article 21(2)(a)–(j) posture
snapshot, the management-body decision-record and Article 20(2)
training-completion attestation surface, and the OCSF API Activity
(class_uid 6003) governance-record evidence sink — is the operator's
job. The framework ships no default management-body forum surface
and no proprietary governance-tooling adapter.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/nis2_art20_governance/playbook.cacao.json

Scenario, workflow, regulatory anchors (NIS2 Directive (EU) 2022/2555
Article 20(1) management-body approval, Article 20(2) management-body
training, Article 21(2)(a)–(j) downstream obligation surface), and
OSCAL / D3FEND control bindings are documented in that folder's
`mappings.yaml`. This folder holds the emitted artifact, a co-located
byte-identical copy of the CACAO source for easy diff inspection, and
the regeneration script.

## Layout

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input mirror)  | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |
| `regenerate.sh`       | (tooling)       | bash script       |

## How to regenerate

From the repository root:

```sh
examples/n8n/nis2_art20_governance/regenerate.sh
```

The script copies the canonical CACAO source over the local mirror
and re-emits `workflow.n8n.json` via the unified compile CLI.

## Sovereign-stack default

The management-body forum surface (which forum, which agenda slot,
which meeting cadence), the evidence store the per-cycle posture
snapshot is composed against, the management-body approval-record
surface, and the governance-record evidence sink are all
operator-configured. No default hosted governance-tooling surface is
assumed, and no non-EU compliance-SaaS adapter is modelled. The
Article 20(2) training-completion attestation binds against the
operator's own management-body member roster.
