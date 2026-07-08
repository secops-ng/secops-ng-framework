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

## Mapped (17 / 19)

| Playbook | Inbound entry |
|----------|---------------|
| `alert_triage` | `cra:annex-i-1-l-logging-monitoring-alert-triage` |
| `cloud_misconfiguration` | `cra:annex-i-1-secure-by-default` |
| `codebase_vuln_management` | `cra:annex-i-2-codebase-vuln-mgmt` |
| `contractual_obligations_tracker` | `cra:art-13-4-component-due-diligence-contracts` |
| `crypto_posture_management` | `cra:annex-i-1-confidentiality`, `cra:annex-i-1-e-confidentiality-crypto-posture` |
| `cryptographic_controls` | `cra:annex-i-1-e-confidentiality-crypto-lifecycle` |
| `data_exfil` | `cra:art-14-severe-incident` |
| `detection_engineering` | `cra:annex-i-1-l-logging-monitoring-detection-engineering` |
| `executive_metrics` | `cra:art-13-2-3-risk-assessment-metrics` |
| `iam_auditor` | `cra:annex-i-1-d-access-control-iam-auditor` |
| `identity_compromise` | `cra:annex-i-1-secure-by-default` |
| `infra_posture_management` | `cra:annex-i-1-b-secure-by-default-infra-posture` |
| `it_security_support_agent` | `cra:art-13-12-spoc-it-support-agent` |
| `on_call_rotation` | `cra:art-13-12-spoc-on-call-rotation` |
| `onboarding_offboarding_tracker` | `cra:annex-i-1-d-access-control-jml` |
| `phishing_triage` | `cra:annex-i-2-2-vuln-handling-phishing` |
| `post_incident_review` | `cra:art-14-final-report` |
| `ransomware_containment` | `cra:art-14-severe-incident` |
| `vuln_intake` | `cra:annex-i-2-*`, `cra:art-13-*`, `cra:art-14-*` |

## Orphaned (2 / 19)

Playbooks shipped without any inbound CRA entry. Each row notes the
nearest candidate CRA clause; the actual edge belongs in a per-clause
yaml under this directory rather than as a comment.

| Playbook | Nearest CRA clause | Notes |
|----------|--------------------|-------|
| `incident_management` | (deliberate skip) | Regulator-notification engine for NIS2 Art. 23 / DORA Art. 19; the CRA Art. 14 product-vuln chain runs on `vuln_intake` and stays separate by design. See note in `content/playbooks/incident_management/mappings.yaml`. |
| `threat_intel_ingest` | Art. 13(6) third-party vuln information | "Any relevant information provided by third parties" — upstream awareness channel. **Closed in the first per-clause increment shipped alongside this inventory.** |

## SKELETON / CORE / EXTEND split

This file is the SKELETON deliverable: inventory + one per-clause
increment. The CORE fan-out (closing the remaining 11 orphans, one
per-clause yaml per playbook) and the EXTEND layer (OSCAL component-
definition expansion, D3FEND cross-links, and the nightly
orphan-CI assertion that fires the G-02 KRI) are filed as sibling
cards.

## Orphan-CI assertion

The nightly G-02 KRI assertion lives at
`tools/lint_cra_playbook_orphans.py` and runs from
`.github/workflows/cra-orphan-ci.yml` on `main`, on every PR that
touches `content/playbooks/` or `content/mappings/cra/`, and on a
nightly schedule. Two firing lanes:

* **Regression (immediate).** A playbook that previously carried an
  inbound `playbook_refs:` citation under a CRA YAML and lost it in
  the current diff fails the build immediately.
* **Net-new (7-day grace).** A finalized playbook with no inbound
  CRA citation trips once its CACAO finalization marker is older
  than 7 days, so CORE per-edge cards can land in their own PRs
  without forcing the EXTEND mapping into the same change.

Deliberate, audited exclusions live in
`content/mappings/cra/_orphan_skip.yaml`. Each entry requires a
`slug` (pointing at a finalized playbook directory) and a
`rationale`; the assertion validates both shape and target on every
run.

The workflow also emits a `--format kri` payload as a build
artifact (`g-02-cra-kri/g-02-cra.json`) for the dashboard ingest:
shape is `{kri_id, kri_name, regime, status, coverage, findings,
emitted_at}`, with `status` one of `ok | degraded | tripped`.
