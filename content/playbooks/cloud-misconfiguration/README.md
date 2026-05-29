# cloud-misconfiguration

CACAO v2 starter playbook for responding to a cloud-posture (CSPM)
finding: ingest → enrich resource and owner → notify owner → guided
remediation → re-scan, with escalation if the re-scan fails.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact (`playbook.cloud_misconfiguration@v1`).

## Worked example

The cross-layer worked example — detection, control, telemetry, and
metrics artifacts that bind to this playbook — lives at
`../../../content-model/examples/cloud-misconfiguration/`. Start with
the README there for the cross-reference graph and per-artifact stable
IDs.

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. The
emitted artifacts under `examples/{n8n,temporal,langgraph}/cloud-misconfiguration/`
are produced deterministically from this playbook by the reference
compilers in `compilers/`; this directory ships the portable content
only.

## Sources

- OASIS CACAO v2.0 specification
- ENISA — Cloud Security: posture-management and misconfiguration guidance
- NIS2 Directive (EU) 2022/2555, Article 21(2)(e) and (i)
- DORA Regulation (EU) 2022/2554, Articles 9 and 19
- OCSF — Compliance Finding (2003) and Cloud Resource Inventory Info (5001)
- MITRE D3FEND — System Configuration Permissions, Resource Access Pattern Analysis
- SigmaHQ — upstream rule IDs referenced in the detection layer
