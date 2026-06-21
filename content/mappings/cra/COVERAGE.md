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

## Mapped (8 / 19)

| Playbook | Inbound entry |
|----------|---------------|
| `cloud_misconfiguration` | `cra:annex-i-1-secure-by-default` |
| `codebase_vuln_management` | `cra:annex-i-2-codebase-vuln-mgmt` |
| `data_exfil` | `cra:art-14-severe-incident` |
| `executive_metrics` | `cra:art-13-2-3-risk-assessment-metrics` |
| `identity_compromise` | `cra:annex-i-1-secure-by-default` |
| `post_incident_review` | `cra:art-14-final-report` |
| `ransomware_containment` | `cra:art-14-severe-incident` |
| `vuln_intake` | `cra:annex-i-2-*`, `cra:art-13-*`, `cra:art-14-*` |

## Orphaned (11 / 19)

Playbooks shipped without any inbound CRA entry. Each row notes the
nearest candidate CRA clause; the actual edge belongs in a per-clause
yaml under this directory rather than as a comment.

| Playbook | Nearest CRA clause | Notes |
|----------|--------------------|-------|
| `alert_triage` | Annex I §1(j) logging-and-monitoring | Operational triage of product-emitted signals. |
| `contractual_obligations_tracker` | Art. 13(4) component due diligence | Supplier / third-party attestation surface. |
| `detection_engineering` | Annex I §1(j) logging-and-monitoring | Rule lifecycle behind the §1(j) monitoring capability. |
| `iam_auditor` | Annex I §1(d) access control | Periodic access-attestation against the §1(d) baseline. |
| `incident_management` | (deliberate skip) | Regulator-notification engine for NIS2 Art. 23 / DORA Art. 19; the CRA Art. 14 product-vuln chain runs on `vuln_intake` and stays separate by design. See note in `content/playbooks/incident_management/mappings.yaml`. |
| `infra_posture_management` | Annex I §1(b) secure-by-default config | Configuration drift detection against the §1(b) baseline. |
| `it_security_support_agent` | Art. 13(12) single point of contact | User-facing reachability channel (paired with `on_call_rotation`). |
| `onboarding_offboarding_tracker` | Annex I §1(d) access control | Joiner/mover/leaver lifecycle behind §1(d). |
| `on_call_rotation` | Art. 13(12) single point of contact | After-hours reachability for the §2(5) coordinated-disclosure intake. |
| `phishing_triage` | Annex I §2(2) vulnerability-handling | Social-engineering vector that surfaces credential-exposure findings into the vuln-handling lane. |
| `threat_intel_ingest` | Art. 13(6) third-party vuln information | "Any relevant information provided by third parties" — upstream awareness channel. **Closed in the first per-clause increment shipped alongside this inventory.** |

## SKELETON / CORE / EXTEND split

This file is the SKELETON deliverable: inventory + one per-clause
increment. The CORE fan-out (closing the remaining 11 orphans, one
per-clause yaml per playbook) and the EXTEND layer (OSCAL component-
definition expansion, D3FEND cross-links, and the nightly
orphan-CI assertion that fires the G-02 KRI) are filed as sibling
cards.
