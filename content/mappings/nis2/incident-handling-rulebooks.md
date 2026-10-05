# NIS2 incident-handling rulebooks — crosswalk

The Luxembourg NIS2 competent authorities and CSIRTs (ANSSI, CSSF, CIRCL,
GOVCERT.LU, HCPN, ILR) publish *Operational guidance for incident
handling* as a set of rulebooks: one for triage and routing and one for
each of eight incident classes. The guidance is prose for a responder;
the playbooks here are the machine-readable counterparts. This crosswalk
says, per rulebook section, which playbooks exercise it.

- **Source:** [`nis2-rulebooks/nis2-rulebooks`](https://github.com/nis2-rulebooks/nis2-rulebooks),
  `rulebooks/operational-guidance-incident-handling.md`, version 1.0
  (28 September 2026), licence CC BY 4.0.
- **Pinned revision:** [`879b88197c0b`](https://github.com/nis2-rulebooks/nis2-rulebooks/blob/879b88197c0b48099c74ec9bf9bb36677c793a81/rulebooks/operational-guidance-incident-handling.md).
- **Machine-readable form:** [`incident-handling-rulebooks.yaml`](incident-handling-rulebooks.yaml),
  one entry per rulebook, one sub-entry per section (detection, containment,
  investigation, remediation, evidence, post-incident, communication).
- **Guard:** `tests/content/test_nis2_rulebooks_crosswalk.py` checks that
  every section names shipped playbooks or an explicit gap, that every
  reference resolves, and that the pin is recorded.

## Rulebook to playbooks

| Rulebook | Topic | Playbooks | Gap |
|---|---|---|---|
| 0 | Triage & Routing | `alert_triage`, `backup_recovery`, `incident_management`, `phishing_triage`, `post_incident_review`, `vuln_intake` | |
| 1 | Denial of Service (DoS) & Distributed Denial of Service (DDoS) | `business_continuity`, `data_exfil`, `ddos_response`, `detection_engineering`, `incident_management`, `patch_management`, `post_incident_review` | |
| 2 | Malware | `alert_triage`, `backup_recovery`, `business_continuity`, `data_exfil`, `detection_engineering`, `identity_compromise`, `incident_management`, `mfa_secured_comms`, `patch_management`, `post_incident_review`, `ransomware_containment`, `security_awareness_training`, `threat_intel_ingest` | |
| 3 | Exploitation of communication channels to gain access | `alert_triage`, `cyber_hygiene_training`, `detection_engineering`, `identity_compromise`, `incident_management`, `mfa_secured_comms`, `phishing_triage`, `security_awareness_training`, `threat_intel_ingest` | |
| 4 | Credential theft & account compromise | `alert_triage`, `data_exfil`, `detection_engineering`, `iam_auditor`, `identity_compromise`, `incident_management`, `mfa_secured_comms`, `patch_management`, `phishing_triage`, `security_awareness_training` | |
| 5 | Vulnerability exploitation | `alert_triage`, `business_continuity`, `codebase_vuln_management`, `data_exfil`, `identity_compromise`, `incident_management`, `patch_management`, `vuln_intake`, `vulnerability_management` | |
| 6 | Insider threat | `data_exfil`, `iam_auditor`, `identity_compromise`, `security_awareness_training` | gap, see [#1009](https://github.com/secops-ng/secops-ng-framework/issues/1009) |
| 7 | Data exfiltration | `alert_triage`, `backup_recovery`, `data_exfil`, `detection_engineering`, `identity_compromise`, `incident_management`, `patch_management`, `post_incident_review`, `threat_intel_ingest` | |
| 8 | Package compromission & supply chain attack | `alert_triage`, `asset_management`, `backup_recovery`, `business_continuity`, `codebase_vuln_management`, `contractual_obligations_tracker`, `data_exfil`, `detection_engineering`, `dora_tpr_management`, `identity_compromise`, `incident_management`, `patch_management`, `supply_chain_security`, `threat_intel_ingest` | |

## How to use it

Pick the rulebook you are in, open its entry in the YAML, and compile the
playbooks it names into the orchestrator you run (`docs/quickstart/`). The
rulebook stays the responder's narrative; the playbooks are the steps an
orchestrator can run, with the I/O contract, the evidence outputs and the
regulatory anchors (`content/mappings/nis2/article-*.yaml`) attached.

Where a section names several playbooks, the first is the primary and the
others cover a part of the section; the `outcome` text says which. A
`gap_note` names what no shipped playbook performs.

## What is not mapped

- **Rulebook 6, insider threat.** The HR, legal and intent dimensions have
  no playbook; the request is
  [#1009](https://github.com/secops-ng/secops-ng-framework/issues/1009).
  The technical overlap with data exfiltration and the IAM auditor is
  recorded in the sub-entries.
- **Organisational measures** inside other rulebooks (role assignment,
  analyst rotation, psychological support, restricted-circle
  communication) are the operator's; the notes say so where relevant.
- **Key watchpoints** are cautions rather than actions and are not
  sub-entries; read them in the source.

## Keeping it current

The upstream document is reviewed every six months. When it changes:
refresh the pinned revision in the YAML header and every `url`, re-read
the changed rulebooks against the playbook list, and update the
`outcome` paraphrases. The guard test fails if the pin is missing, not
if it is stale, so the review is a deliberate act.
