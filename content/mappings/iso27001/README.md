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
(A.5.7 through A.5.37) land as sibling entries in that file on
subsequent cards.

The A.6 people-controls theme file has landed with its first two
entries (`iso27001:a-6-1-screening`, `iso27001:a-6-3-awareness`) in
`annex-a-6-people.yaml`; the remaining A.6 controls (A.6.2, A.6.4
through A.6.8) land as sibling entries in that file on subsequent
cards.

The A.7 physical-controls theme file has landed with its first two
entries (`iso27001:a-7-1-physical-security-perimeters`,
`iso27001:a-7-2-physical-entry`) in `annex-a-7-physical.yaml`; both
ship with empty `control_refs` because the SecOps-NG control catalogue
is currently scoped to logical / cyber controls (see the coverage note
in the theme file header). The remaining A.7 controls (A.7.3 through
A.7.14) land as sibling entries in that file on subsequent cards.

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
that consumes the DLP signal. The A.8.18–A.8.22 batch also lands in
`annex-a-8-technological.yaml`:
`iso27001:a-8-18-use-of-privileged-utility-programs` ships
`control_refs: []` pending a dedicated privileged-utility /
break-glass-tool artifact (the operator's admin-tool inventory,
invocation-logging, and the least-privilege / privileged-access
discipline anchored under A.8.2 discharge it in practice);
`iso27001:a-8-19-installation-of-software-on-operational-systems`
ships `control_refs: []` pending a dedicated software-installation
change-control artifact (the operator's change-management process,
signed-artefact / provenance verification, the configuration-
baseline discipline anchored under A.8.9, and the patch-management
discipline anchored under A.8.8 discharge it in practice);
`iso27001:a-8-20-networks-security` ships `control_refs: []`
pending a dedicated network-infrastructure-security artifact (the
operator's network-architecture documentation, device-hardening
baselines via A.8.9, management-plane access controls via A.8.2 /
A.8.3, and the log-and-monitor pair anchored under A.8.15 / A.8.16
discharge it in practice);
`iso27001:a-8-21-security-of-network-services` ships
`control_refs: []` pending a dedicated network-services-agreement
artifact (the operator's supplier-management process, joined
upstream against the A.5.19 supplier-management surface,
discharges it in practice); and
`iso27001:a-8-22-segregation-of-networks` ships `control_refs: []`
pending a dedicated segmentation-posture artifact (the operator's
zone architecture, policy-enforced flow rules, micro-segmentation
posture, and the configuration-baseline discipline anchored under
A.8.9 discharge it in practice). A.8 is the largest theme (34
controls); with the A.8.13–A.8.17 sibling batch (in review as
`annex-a-8-technological.yaml` sibling entries on a separate PR)
and this A.8.18–A.8.22 batch both landed on main, coverage will
stand at 22 of 34 entries landed. If the sibling A.8.13–A.8.17
batch has not yet merged when this batch lands, coverage stands
at 12 landed on main plus this A.8.18–A.8.22 batch (17 of 34);
the sibling batch will bring the total to 22 of 34 on merge. The
remaining A.8 controls (A.8.23 through A.8.34) land as sibling
entries in that file on subsequent cards.
