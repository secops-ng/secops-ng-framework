# CRA mapping coverage — playbook → Article tie-ins

Inventory of which shipped playbooks under `content/playbooks/` carry
an inbound entry in `content/mappings/cra/`. CRA is the laggard regime
on the G-02 regulatory-mapping coverage axis (NIS2 already has full
per-clause Art. 21 coverage; CRA bundles Art. 13, Art. 14, and Annex I
into three files and reaches a subset of the playbook catalogue).

Inbound coverage is the canonical lens: a playbook is "mapped" when at
least one CRA entry's `playbook_refs:` cites it. The playbook-mappings
schema's fixed top-level keys (oscal/d3fend/ocsf/nis2/dora) do not yet
carry a `cra:` block — extending the schema is filed as a sibling
EXTEND card; for now CRA closure is asserted in comments at the foot
of each playbook overlay.

## Mapped (14 / 19)

| Playbook | Inbound entry |
|----------|---------------|
| `alert_triage` | `cra:annex-i-1-l-logging-monitoring-alert-triage` |
| `cloud_misconfiguration` | `cra:annex-i-1-secure-by-default` |
| `codebase_vuln_management` | `cra:annex-i-2-codebase-vuln-mgmt` |
| `contractual_obligations_tracker` | `cra:art-13-4-component-due-diligence-contracts` |
| `data_exfil` | `cra:art-14-severe-incident` |
| `executive_metrics` | `cra:art-13-2-3-risk-assessment-metrics` |
| `identity_compromise` | `cra:annex-i-1-secure-by-default` |
| `it_security_support_agent` | `cra:art-13-12-spoc-it-support-agent` |
| `on_call_rotation` | `cra:art-13-12-spoc-on-call-rotation` |
| `onboarding_offboarding_tracker` | `cra:annex-i-1-d-access-control-jml` |
| `phishing_triage` | `cra:annex-i-2-2-vuln-handling-phishing` |
| `post_incident_review` | `cra:art-14-final-report` |
| `ransomware_containment` | `cra:art-14-severe-incident` |
| `vuln_intake` | `cra:annex-i-2-*`, `cra:art-13-*`, `cra:art-14-*` |

## Orphaned (5 / 19)

Playbooks shipped without any inbound CRA entry. Each row notes the
nearest candidate CRA clause; the actual edge belongs in a per-clause
yaml under this directory rather than as a comment.

| Playbook | Nearest CRA clause | Notes |
|----------|--------------------|-------|
| `detection_engineering` | Annex I §1(l) logging-and-monitoring | Rule lifecycle behind the §1(l) monitoring capability. |
| `iam_auditor` | Annex I §1(d) access control | Periodic access-attestation against the §1(d) baseline. |
| `incident_management` | (deliberate skip) | Regulator-notification engine for NIS2 Art. 23 / DORA Art. 19; the CRA Art. 14 product-vuln chain runs on `vuln_intake` and stays separate by design. See note in `content/playbooks/incident_management/mappings.yaml`. |
| `infra_posture_management` | Annex I §1(b) secure-by-default config | Configuration drift detection against the §1(b) baseline. |
| `threat_intel_ingest` | Art. 13(6) third-party vuln information | "Any relevant information provided by third parties" — upstream awareness channel. **Closed in the first per-clause increment shipped alongside this inventory.** |

## SKELETON / CORE / EXTEND split

This file is the SKELETON deliverable: inventory + one per-clause
increment. The CORE fan-out (closing the remaining 11 orphans, one
per-clause yaml per playbook) and the EXTEND layer (OSCAL component-
definition expansion, D3FEND cross-links, and the nightly
orphan-CI assertion that fires the G-02 KRI) are filed as sibling
cards.
