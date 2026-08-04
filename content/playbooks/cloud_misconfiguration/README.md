# cloud_misconfiguration

CACAO v2 starter playbook for responding to a cloud-posture (CSPM)
finding: ingest → enrich resource and owner → notify owner → guided
remediation → re-scan, with escalation if the re-scan fails.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact (`playbook.cloud_misconfiguration@v1`).

## Worked example

The cross-layer worked example — controls, telemetry, metrics, and
regulatory cross-references that bind to this playbook — lives at
`../../../content-model/examples/cloud_misconfiguration/`. Start with
the README there for the cross-reference graph and per-artifact stable
IDs:

- `control.cspm_baseline@v1`, `control.iac_policy_guardrail@v1`,
  `control.cloud_identity_least_privilege@v1`
- `telemetry.ocsf.compliance_finding@v1`,
  `telemetry.ocsf.cloud_resources_inventory_info@v1`
- `kpi.mttd_cloud_misconfig@v1`, `kpi.mttr_cloud_misconfig@v1`,
  `kpi.cloud_posture_coverage@v1`, `kri.recurring_cloud_misconfig@v1`

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. The
shared CACAO fixture lives at
`tests/compilers/_shared/fixtures/cloud_misconfiguration.cacao.json`.
Emitted artifacts and golden tests landed across the three CORE cards:

- n8n: `tests/compilers/n8n/test_cloud_misconfiguration.py`
- Temporal: `tests/compilers/temporal/test_cloud_misconfiguration.py` (PR #73)
- LangGraph: `examples/langgraph/cloud_misconfiguration/` plus
  `tests/compilers/langgraph/test_cloud_misconfiguration.py` (PR #85)

This directory ships the portable content only.

## Regulatory cross-references

The playbook is named in the regulatory mapping packs under
`content/mappings/`:

| Regime | Article  | Mapping entry                       |
|--------|----------|-------------------------------------|
| NIS2   | 21(2)(e) | `nis2:art-21-2-e`                   |
| NIS2   | 21(2)(i) | `nis2:art-21-2-i`                   |
| DORA   | 9(4)(a)  | `dora:art-9-vuln-mgmt` (companion)  |
| DORA   | 19(4)(a) | `dora:art-19-initial-4h` (escalation gate) |

## Sources

- OASIS CACAO v2.0 specification
- ENISA — Cloud Security: posture-management and misconfiguration guidance
- NIS2 Directive (EU) 2022/2555, Article 21(2)(e) and (i)
- DORA Regulation (EU) 2022/2554, Articles 9 and 19
- OCSF — Compliance Finding (2003) and Cloud Resources Inventory Info (5023)
- NIST SP 800-53 Rev. 5 — CM-2/CM-6/CM-8, AC-3/AC-6, SC-7/SC-8/SC-28
- MITRE D3FEND — System Configuration Permissions (D3-SCP),
  Resource Access Pattern Analysis (D3-RAPA)
- SigmaHQ — upstream rule IDs referenced via the playbook's
  `external_references`
