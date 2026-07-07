# content/mappings/iso27001/

ISO/IEC 27001:2022 crosswalk.

## File convention

One YAML file per Annex A theme. The 2022 revision groups Annex A
controls into four themes:

| Theme | File | Controls |
|-------|------|----------|
| A.5 Organisational | `annex-a-5-organisational.yaml` | 37 |
| A.6 People | `annex-a-6-people.yaml` | 8 |
| A.7 Physical | `annex-a-7-physical.yaml` | 14 |
| A.8 Technological | `annex-a-8-technological.yaml` | 34 |

Each entry inside a theme file targets one numbered Annex A control,
with `id: iso27001:a-<theme>-<number>-<slug>` (kebab-case slug). See
`../README.md` for the schema-level shape and the canonical URN scheme
for artifact refs.

## Status

Draft. The A.5 organisational-controls theme file has landed with
its anchor entry (`iso27001:a-5-1-policies`, Annex A.5.1 Policies for
information security) and the A.5.2–A.5.6 batch:
`iso27001:a-5-2-roles-and-responsibilities` wires
`control.ict_risk_governance@v1` (already carrying A.5.2 on its
`oscal_refs` block);
`iso27001:a-5-3-segregation-of-duties` ships `control_refs: []`
pending a dedicated segregation-of-duties artifact, with the
in-catalogue practical surface (`control.least_privilege@v1`,
`control.privileged_access_review@v1`) called out in the entry note;
`iso27001:a-5-4-management-responsibilities` wires
`control.risk_management_policy@v1` and
`control.training_attestation@v1` (the policy-set and
attestation anchors that discharge the management-direction
discipline in practice);
`iso27001:a-5-5-contact-with-authorities` and
`iso27001:a-5-6-contact-with-special-interest-groups` both wire
`control.crisis_communication_plan@v1` (already carrying A.5.5 and
A.5.6 on its `oscal_refs` block), with A.5.6 also carrying
`playbook.threat_intel_ingest@v1` as the operational
community-intelligence ingest surface. The remaining A.5 controls
(A.5.7 through A.5.12) also land in `annex-a-5-organisational.yaml`,
bringing the theme to 12 of 37 entries:
`iso27001:a-5-7-threat-intelligence` ships `control_refs: []` pending
a dedicated threat-intelligence-management artifact, with
`playbook.threat_intel_ingest@v1` as the operational analyse-and-route
discharge (the community-intelligence contact surface anchored under
A.5.6 feeds it);
`iso27001:a-5-8-isms-in-project-management` ships `control_refs: []`
and `playbook_refs: []` pending a dedicated project-security-
integration artifact (the operator's project-management framework,
joined against the A.5.1 policy-set anchor and the A.8.32 change-
management anchor, discharges it in practice);
`iso27001:a-5-9-inventory-of-assets` wires
`control.asset_inventory_delta@v1` (already carrying A.5.9 on its
`oscal_refs` block) plus `playbook.asset_management@v1` as the
reconciliation-and-tagging discharge;
`iso27001:a-5-10-acceptable-use-of-assets` wires
`control.risk_management_policy@v1` as the policy-set anchor that
governs the topic-specific acceptable-use rules, with
`playbook_refs: []` (the discipline is policy-set rather than
operational-flow);
`iso27001:a-5-11-return-of-assets` wires `control.jml_evidence@v1`
(the leaver leg of the joiner-mover-leaver flow, PS-4 personnel-
termination discipline) as the practical anchor, with
`playbook_refs: []` (the physical-asset-return discipline is
discharged against the operator's own leaver-checklist evidence
referenced by the JML flow); and
`iso27001:a-5-12-classification-of-information` ships
`control_refs: []` and `playbook_refs: []` pending a dedicated
classification-scheme artifact (the operator's own scheme, joined
against A.5.9 inventory, A.5.1 policy-set, and A.5.10 acceptable-use,
discharges it in practice). The A.5.13–A.5.18 batch also lands in
`annex-a-5-organisational.yaml`, bringing the theme to 18 of 37
entries: `iso27001:a-5-13-labelling-of-information` ships
`control_refs: []` and `playbook_refs: []` pending a dedicated
labelling-scheme artifact (the operator's labelling procedures,
joined against the A.5.12 classification anchor, the A.5.9
asset-inventory pair, and the A.5.10 acceptable-use anchor,
discharge it in practice); `iso27001:a-5-14-information-transfer`
wires `control.risk_management_policy@v1` as the policy-set anchor
that governs the operator's transfer rules (crypto-posture under
A.8.24 exercises the confidentiality-in-transit slice);
`iso27001:a-5-15-access-control` wires
`control.access_enforcement@v1` and `control.least_privilege@v1`
(both already carrying A.5.15 on their `oscal_refs` block) plus
`playbook.iam_auditor@v1`; `iso27001:a-5-16-identity-management`
wires `control.jml_evidence@v1` and
`control.account_management@v1` (both already carrying A.5.16)
plus `playbook.onboarding_offboarding_tracker@v1` and
`playbook.iam_auditor@v1`;
`iso27001:a-5-17-authentication-information` ships
`control_refs: []` and `playbook_refs: []` pending a dedicated
credential-management artifact (the operator's credential
procedures, joined against A.8.5 secure-authentication, A.8.24
key-rotation, and A.5.1 policy-set, discharge it in practice); and
`iso27001:a-5-18-access-rights` wires
`control.cloud_identity_least_privilege@v1` (already carrying
A.5.18 alongside A.5.15) and `control.privileged_access_review@v1`
plus `playbook.iam_auditor@v1` and
`playbook.onboarding_offboarding_tracker@v1`. The A.5.19–A.5.25
batch also lands in `annex-a-5-organisational.yaml`, bringing the
theme to 25 of 37 entries:
`iso27001:a-5-19-information-security-in-supplier-relationships`
wires `control.supplier_inventory@v1` and
`control.provider_attestation@v1` (both already carrying A.5.19 on
their `oscal_refs` block) plus `playbook.supply_chain_security@v1`
and `playbook.contractual_obligations_tracker@v1`;
`iso27001:a-5-20-addressing-information-security-within-supplier-agreements`
ships `control_refs: []` pending a dedicated supplier-agreement
artifact, with `playbook.contractual_obligations_tracker@v1` and
`playbook.supply_chain_security@v1` as the contract-time and
relationship-time discharges;
`iso27001:a-5-21-managing-information-security-in-the-ict-supply-chain`
wires `control.sbom_capture@v1` (the component-visibility anchor)
plus `playbook.supply_chain_security@v1` and
`playbook.codebase_vuln_management@v1` as the relationship-side and
component-side discharges;
`iso27001:a-5-22-monitoring-review-and-change-management-of-supplier-services`
wires `control.provider_attestation@v1` (already carrying A.5.22 on
its `oscal_refs` block) plus `playbook.supply_chain_security@v1`
and `playbook.contractual_obligations_tracker@v1` for the
change-management discharge;
`iso27001:a-5-23-information-security-for-use-of-cloud-services`
wires `control.cspm_baseline@v1` and
`control.cloud_identity_least_privilege@v1` (the configuration and
identity slices of the shared-responsibility surface) plus
`playbook.cloud_misconfiguration@v1` and
`playbook.infra_posture_management@v1`;
`iso27001:a-5-24-information-security-incident-management-planning-and-preparation`
wires `control.incident_handling_capability@v1`,
`control.incident_timeline_signals@v1`, and
`control.oob_channel_probe@v1` (all already carrying A.5.24 on
their `oscal_refs` block) plus `playbook.incident_management@v1`
and `playbook.on_call_rotation@v1`; and
`iso27001:a-5-25-assessment-and-decision-on-information-security-events`
wires `control.incident_timeline_signals@v1`,
`control.dora_major_classifier@v1`,
`control.cra_submission_templates@v1`, and
`control.dora_submission_templates@v1` (all already carrying
A.5.25 on their `oscal_refs` block) plus
`playbook.alert_triage@v1` and `playbook.incident_management@v1`.
The remaining A.5 controls (A.5.26 through A.5.37) land as sibling
artifacts.
The A.5.26–A.5.37 batch closes the theme, bringing the A.5
organisational-controls coverage to 37 of 37 entries:
`iso27001:a-5-26-response-to-information-security-incidents` wires
`control.incident_handling_capability@v1` (already carrying A.5.26
on its `oscal_refs` block alongside A.5.24) and
`control.incident_timeline_signals@v1` plus
`playbook.incident_management@v1` and `playbook.on_call_rotation@v1`;
`iso27001:a-5-27-learning-from-information-security-incidents`
wires `control.post_incident_learning@v1` and
`control.recurring_incident_correlator@v1` (both already carrying
A.5.27 on their `oscal_refs` block) plus
`playbook.post_incident_review@v1` and
`playbook.incident_management@v1`;
`iso27001:a-5-28-collection-of-evidence` ships `control_refs: []`
pending a dedicated evidence-custody artifact (the operator's
forensic-readiness procedures, joined against the A.5.24 case-
record anchors, the A.5.33 records-protection surface, and the
`playbook.incident_management@v1` / `playbook.post_incident_review@v1`
discharges, exercise it in practice);
`iso27001:a-5-29-information-security-during-disruption` ships
`control_refs: []` pending a dedicated ISMS-continuity artifact
(the operator's BCM posture, joined against the A.5.30 restore-
drill anchor, the A.8.13 backup anchors, and the A.5.24 incident-
management planning anchors, exercises it in practice), with
`playbook.backup_recovery@v1` and `playbook.incident_management@v1`
as the operational discharges;
`iso27001:a-5-30-ict-readiness-for-business-continuity` wires
`control.restore_drill@v1` (already carrying A.5.30 on its
`oscal_refs` block alongside A.8.13) plus
`playbook.backup_recovery@v1` as the exercised-recovery discharge;
`iso27001:a-5-31-legal-statutory-regulatory-and-contractual-requirements`
ships `control_refs: []` pending a dedicated legal-register
artifact (the operator's own legal-and-compliance register,
joined against the A.5.1 policy-set, the A.5.20 supplier-
agreements surface, and the community-authored crosswalk under
`content/mappings/`, exercises it in practice), with
`playbook.contractual_obligations_tracker@v1` as the contract-
tracking discharge;
`iso27001:a-5-32-intellectual-property-rights` ships
`control_refs: []` and `playbook_refs: []` pending a dedicated
IPR artifact (the operator's IPR governance, joined against the
A.5.1 policy-set, the A.5.9 licensed-software inventory, the
A.5.20 supplier-agreements surface, and the A.5.31 legal-register
discipline, exercises it in practice);
`iso27001:a-5-33-protection-of-records` ships `control_refs: []`
and `playbook_refs: []` pending a dedicated records-retention
artifact (the operator's retention schedule and record-store
integrity posture, joined against the A.5.12 classification
surface, the A.8.10 information-deletion discipline, the A.8.13
backup anchors, and the A.5.31 legal-register discipline,
exercises it in practice);
`iso27001:a-5-34-privacy-and-protection-of-pii` ships
`control_refs: []` pending a dedicated privacy-programme artifact
(the operator's DPO / ROPA / privacy-programme surface exercises
the substantive privacy discipline in practice), with
`playbook.data_subject_rights@v1` and
`playbook.data_protection_impact_assessment@v1` as the two
GDPR-anchored operational discharges;
`iso27001:a-5-35-independent-review-of-information-security` wires
`control.security_assessment@v1` (already carrying A.5.35 on its
`oscal_refs` block) as the independent-assessment anchor, with
`playbook_refs: []` (A.5.35 is a governance-and-audit obligation
rather than an operational flow);
`iso27001:a-5-36-compliance-with-policies-rules-and-standards`
wires `control.ict_risk_framework_review@v1` and
`control.control_effectiveness_test@v1` (both already carrying
A.5.36 on their `oscal_refs` block) as the framework-level and
per-control review surfaces, with `playbook_refs: []`; and
`iso27001:a-5-37-documented-operating-procedures` ships
`control_refs: []` and `playbook_refs: []` because A.5.37 is the
meta-obligation that documented procedures exist — the SecOps-NG
catalogue as a whole (the `content/playbooks/` set and the
`content/controls/` set together, joined against the A.5.1
policy-set, the A.8.32 change-management anchor, and the A.5.36
compliance-review discipline) exercises the obligation.
Coverage on A.5 now stands at 37 of 37 entries landed, closing
the A.5 organisational-controls theme.

The A.6 people-controls theme file is complete: all eight controls
(A.6.1 through A.6.8) are present in `annex-a-6-people.yaml`.
A.6.1 (screening), A.6.2 (terms and conditions of employment), A.6.4
(disciplinary process), and A.6.5 (responsibilities after termination
or change of employment) wire `control.jml_evidence@v1` against the
join/move/leave lifecycle surface, joined against
`playbook.onboarding_offboarding_tracker@v1`. A.6.2 additionally
wires `control.training_attestation@v1` for the
acknowledgement-of-policy surface. A.6.3 (awareness/education and
training) wires `control.training_attestation@v1` and
`control.phishing_simulation@v1` against
`playbook.cyber_hygiene_training@v1`. A.6.6 (confidentiality / NDAs)
ships `control_refs: []` and `playbook_refs: []` — the instrument is
the operator's own legal artifact, out of scope of the SecOps-NG
control catalogue; the signed-instrument evidence is captured in
practice against the joiner-side lifecycle already anchored on A.6.1
and A.6.2. A.6.7 (remote working) wires
`control.baseline_configuration@v1`, `control.least_privilege@v1`,
and `control.mfa_state_probe@v1` against
`playbook.mfa_secured_comms@v1`. A.6.8 (event reporting) wires
`control.incident_handling_capability@v1` and
`control.vuln_disclosure_intake@v1` (the latter's `oscal_refs`
block already carrying A.6.8) against
`playbook.incident_management@v1`. Coverage on A.6 now stands at
8 of 8 entries landed, closing the A.6 people-controls theme.

The A.7 physical-controls theme file closes at 14 of 14 entries
landed in `annex-a-7-physical.yaml`. The theme opens with
`iso27001:a-7-1-physical-security-perimeters` and
`iso27001:a-7-2-physical-entry`; the A.7.3–A.7.14 batch closes it:
`iso27001:a-7-3-securing-offices-rooms-and-facilities`,
`iso27001:a-7-4-physical-security-monitoring`,
`iso27001:a-7-5-protecting-against-physical-and-environmental-threats`,
`iso27001:a-7-6-working-in-secure-areas`,
`iso27001:a-7-7-clear-desk-and-clear-screen`,
`iso27001:a-7-8-equipment-siting-and-protection`,
`iso27001:a-7-11-supporting-utilities`,
`iso27001:a-7-12-cabling-security`,
`iso27001:a-7-13-equipment-maintenance`, and
`iso27001:a-7-14-secure-disposal-or-re-use-of-equipment` all ship with
empty `control_refs` and an explanatory gap note because the SecOps-NG
control catalogue is currently scoped to logical / cyber controls (see
the coverage note in the theme file header); the operator's own
facilities-security evidence discharges the physical obligation.
Two entries do wire an existing anchor:
`iso27001:a-7-9-security-of-assets-off-premises` and
`iso27001:a-7-10-storage-media` wire
`control.asset_inventory_delta@v1` for the asset-tracking slice that
overlaps directly with the logical inventory the catalogue already
carries — the physical-handling, secure-transport, and disposal
slices still discharge against the operator's own procedures (with
A.7.14 and the logical A.8.10 information-deletion discipline joining
the disposal slice from the ISMS side).

The A.8 technological-controls theme file has landed with its first
two entries (`iso27001:a-8-1-user-endpoint-devices`,
`iso27001:a-8-2-privileged-access-rights`) and the A.8.3–A.8.7 batch
in `annex-a-8-technological.yaml`. A.8.1 ships with empty
`control_refs` pending an endpoint-posture control artifact; A.8.2
wires `control.privileged_access_review@v1`,
`control.account_management@v1`, and `control.least_privilege@v1`
(all already carrying `A.8.2` on their `oscal_refs` block) plus
`playbook.iam_auditor@v1`. In the A.8.3–A.8.7 batch:
`iso27001:a-8-3-information-access-restriction` wires
`control.access_enforcement@v1` (already carrying A.8.3 on its
`oscal_refs` block) and `control.least_privilege@v1`, with
`playbook.iam_auditor@v1` as the operational discharge;
`iso27001:a-8-4-access-to-source-code` ships `control_refs: []`
pending a dedicated source-code access / change-management artifact
(the operator's version-control access matrix and CI/CD role
bindings discharge it in practice);
`iso27001:a-8-5-secure-authentication` wires
`control.mfa_state_probe@v1` and
`control.service_identification_authentication@v1` (both already
carrying A.8.5) plus `playbook.mfa_secured_comms@v1`;
`iso27001:a-8-6-capacity-management` ships `control_refs: []`
pending a dedicated capacity-monitoring artifact (the operator's
observability stack discharges it in practice); and
`iso27001:a-8-7-protection-against-malware` ships `control_refs: []`
pending a dedicated anti-malware artifact, with
`playbook.threat_intel_ingest@v1` already exercising the
threat-intelligence ingest slice that feeds those tools. The
A.8.8–A.8.12 batch also lands in `annex-a-8-technological.yaml`:
`iso27001:a-8-8-management-of-technical-vulnerabilities` wires
`control.patch_evidence@v1` and `control.vuln_disclosure_intake@v1`
(both already carrying A.8.8 on their `oscal_refs` block) plus the
five-playbook operational discharge across `playbook.vuln_intake@v1`,
`playbook.patch_management@v1`,
`playbook.codebase_vuln_management@v1`,
`playbook.infra_posture_management@v1`, and
`playbook.cloud_misconfiguration@v1`;
`iso27001:a-8-9-configuration-management` wires
`control.configuration_settings@v1`,
`control.baseline_configuration@v1`,
`control.iac_policy_guardrail@v1`, and
`control.cspm_baseline@v1` (all already carrying A.8.9) plus
`playbook.infra_posture_management@v1` and
`playbook.cloud_misconfiguration@v1`;
`iso27001:a-8-10-information-deletion` ships `control_refs: []`
pending a dedicated information-deletion / media-sanitisation
artifact (the operator's retention-schedule enforcement and
media-disposal procedures discharge it in practice, with GDPR
Art. 17 erasure separately anchored under
`playbook.data_subject_rights@v1`);
`iso27001:a-8-11-data-masking` ships `control_refs: []` pending a
dedicated masking / pseudonymisation artifact (the operator's
data-classification pipeline and non-prod masking transforms
discharge it in practice); and
`iso27001:a-8-12-data-leakage-prevention` ships `control_refs: []`
pending a dedicated DLP-posture control artifact, with
`playbook.data_exfil@v1` already anchoring the response-side chain
that consumes the DLP signal. The A.8.13–A.8.17 batch also lands in
`annex-a-8-technological.yaml`:
`iso27001:a-8-13-information-backup` wires
`control.backup_attestation@v1` and `control.restore_drill@v1` (both
already carrying A.8.13 on their `oscal_refs` block) plus
`playbook.backup_recovery@v1` as the operational
restore-drill discharge;
`iso27001:a-8-14-redundancy-of-information-processing-facilities`
ships `control_refs: []` pending a dedicated redundancy / failover
artifact (the operator's infrastructure-architecture posture and DR
failover-test evidence discharge it in practice);
`iso27001:a-8-15-logging` ships `control_refs: []` pending a
dedicated audit-record artifact (the operator's log-generation
posture and SIEM / log-pipeline discharge it in practice, with the
monitoring side that consumes the log surface separately anchored
under A.8.16);
`iso27001:a-8-16-monitoring-activities` wires
`control.detection_coverage_evidence@v1` (already carrying A.8.16
on its `oscal_refs` block) plus `playbook.detection_engineering@v1`
(coverage-authoring lifecycle) and `playbook.alert_triage@v1`
(signal-consumption / response-routing surface); and
`iso27001:a-8-17-clock-synchronisation` ships `control_refs: []`
pending a dedicated time-source artifact (the operator's NTP / PTP
posture discharges it in practice; A.8.17 is a precondition of the
A.8.15 / A.8.16 log-and-monitor pair). The A.8.23–A.8.27 batch also
lands in `annex-a-8-technological.yaml`:
`iso27001:a-8-23-web-filtering` ships `control_refs: []` and
`playbook_refs: []` pending a dedicated web-filtering artifact (the
operator's egress-filtering enforcement point, joined against the
malware-protection discipline anchored under A.8.7 and the
log-and-monitor pair anchored under A.8.15 / A.8.16, discharges it
in practice);
`iso27001:a-8-24-use-of-cryptography` wires
`control.crypto_policy_inventory@v1`,
`control.cert_posture_scan@v1`, and
`control.key_rotation_evidence@v1` (all already carrying A.8.24 on
their `oscal_refs` block) plus `playbook.crypto_posture_management@v1`
as the operational cryptography-posture discharge;
`iso27001:a-8-25-secure-development-life-cycle` ships
`control_refs: []` and `playbook_refs: []` pending a dedicated
secure-SDLC artifact (the operator's SDLC governance, joined against
A.8.4 source-code access, A.8.8 technical vulnerabilities, A.8.9
configuration management, and A.8.19 software installation,
discharges it in practice);
`iso27001:a-8-26-application-security-requirements` ships
`control_refs: []` and `playbook_refs: []` pending a dedicated
application-security-requirements artifact (the operator's
requirements-engineering process, joined against the A.8.25
secure-SDLC umbrella and the A.8.8 / A.8.3 / A.8.5 anchors,
discharges it in practice); and
`iso27001:a-8-27-secure-system-architecture-and-engineering-principles`
ships `control_refs: []` and `playbook_refs: []` pending a dedicated
architecture-principles artifact (the operator's architecture-
governance posture, joined against A.8.25 secure-SDLC, A.8.9
configuration management, A.8.2 / A.8.3 least-privilege, A.8.20
networks security, and A.8.22 segregation-of-networks, discharges
it in practice). The A.8.28–A.8.34 batch closes the theme:
`iso27001:a-8-28-secure-coding` ships `control_refs: []` pending a
dedicated secure-coding standards artifact (the operator's in-build
static-analysis / dependency-scanning / secret-scanning enforcement
posture, joined against the A.8.25 secure-SDLC umbrella, A.8.4
source-code access, and A.8.8 technical vulnerabilities, discharges
it in practice) plus `playbook.codebase_vuln_management@v1` as the
downstream code-vulnerability triage surface;
`iso27001:a-8-29-security-testing-in-development-and-acceptance`
ships `control_refs: []` pending a dedicated security-testing
acceptance-gate artifact (the operator's in-CI SAST / DAST / SCA /
secret-scanning execution joined against A.8.25 and A.8.28
discharges it in practice) plus `playbook.codebase_vuln_management@v1`
as the downstream triage surface;
`iso27001:a-8-30-outsourced-development` wires
`control.sbom_capture@v1` (already carrying A.8.30 on its
`oscal_refs` block) as the concrete provenance-and-composition
artifact against which outsourced software delivery is exercised,
with the wider outsourced-supervision surface discharged against
the operator's supplier-management posture;
`iso27001:a-8-31-separation-of-development-test-and-production-environments`
ships `control_refs: []` and `playbook_refs: []` pending a
dedicated environment-separation artifact (the operator's
environment topology, joined against A.8.3 access-restriction,
A.8.9 configuration management, A.8.11 data masking, A.8.22
segregation of networks, and A.8.32 change management, discharges
it in practice);
`iso27001:a-8-32-change-management` wires
`control.iac_policy_guardrail@v1` (already carrying A.8.32 on its
`oscal_refs` block) plus `playbook.infra_posture_management@v1` and
`playbook.patch_management@v1` for the posture-drift and patch-
release change slices;
`iso27001:a-8-33-test-information` ships `control_refs: []` and
`playbook_refs: []` pending a dedicated test-information protection
artifact (the operator's test-data posture, joined against A.8.3,
A.8.11 masking, and A.8.31 separation, discharges it in practice,
with `playbook.data_subject_rights@v1` as the erasure surface
against inadvertently landed personal data); and
`iso27001:a-8-34-protection-of-information-systems-during-audit-testing`
ships `control_refs: []` and `playbook_refs: []` pending a dedicated
audit-testing governance artifact (the operator's audit-engagement
posture, joined against A.8.3, A.8.15 / A.8.16 log-and-monitor,
A.8.31 environment separation, and A.8.32 change management,
discharges it in practice). Coverage on A.8 now stands at 34 of 34
entries landed (pending #664 A.8.18–A.8.22 which is on a sibling
in-flight branch); once #664 merges, the A.8 theme file will carry
the full 34-entry surface with no gaps.

## OSCAL component-definition

`oscal-component-definition.json` is an OSCAL 1.1.2 component-definition
document that exposes the ISO/IEC 27001:2022 Annex A crosswalk in the
NIST OSCAL serialization. One component (SecOps-NG) carries one
control-implementation set whose `implemented-requirements` mirror the
entries in `annex-a-5-organisational.yaml`, `annex-a-6-people.yaml`,
`annex-a-7-physical.yaml`, and `annex-a-8-technological.yaml`: one
implemented-requirement per `(entry, control_ref)` pair across the four
theme files. Entries whose `control_refs` list is empty are
principle-level or discharged indirectly through companion artifacts
(described in the per-control prose above) and are consequently not
reflected in the OSCAL surface. Statement text is borrowed verbatim
from each entry's `obligation` field. Schema-validation and
YAML-coverage parity are enforced by
`tests/content/test_oscal_iso27001_component_definition.py` against
the OSCAL component schema vendored under
`tests/fixtures/oscal/oscal_component_schema-v1.1.2.json`. The CRA,
GDPR, NIS2, DORA, and EU AI Act OSCAL component-definitions are sibling
artifacts tracked separately.

A.8.18–A.8.22 are pending against a sibling in-flight branch (PR
#664 on the crosswalk YAMLs). At SKELETON time those entries are
absent from `main` and therefore absent from this component definition;
once the pending PR merges, the generator is re-run and the SKELETON
baseline in
`tests/content/test_oscal_iso27001_component_definition.py` is
revised alongside the regenerated component definition.
