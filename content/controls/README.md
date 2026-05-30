# content/controls/

OSCAL component definitions and D3FEND tactic mappings. These are the
control-side anchors that playbooks and mappings reference.

## Cross-reference layer (CORE)

The mapping YAMLs under `content/mappings/{nis2,dora,cra}/` carry
`control_refs` of the form `control.<slug>@v1`. To make those bindings
actionable for operators who already speak OSCAL catalogs (NIST 800-53,
ISO/IEC 27001) and adversary-tactic models (MITRE D3FEND / ATT&CK), each
referenced control resolves to a **cross-reference file** under this
directory.

A cross-reference file:

- declares the SecOps-NG `stable_id` (matches the value used in
  `control_refs`);
- lists one or more `oscal_refs[]` — `{ catalog, control_id, title? }`
  back-references into recognised control catalogs (NIST 800-53 Rev5,
  CIS Controls v8, ISO/IEC 27001:2022 Annex A, NIS2 Article 21(2), DORA
  Article 5, CRA Annex I, …);
- lists one or more `d3fend_refs[]` — `{ d3f_id, technique_name?,
  url?, offensive_techniques_attack[]? }`, where
  `offensive_techniques_attack` is the set of MITRE ATT&CK technique IDs
  the D3FEND tactic is designed to counter;
- carries `provenance` (`source_url`, `captured_at`, optional `notes`)
  so consumers can re-check upstream drift.

The schema lives at `content-model/control_xref.schema.json`.

This is intentionally orthogonal to `content-model/control.schema.json`,
which models the full OSCAL component-definition for a SecOps-NG
control. The cross-reference layer is the **thin joining table** the
mapping layer needs first; the full component-definition shape will land
alongside the control implementations themselves.

### Inventory (CORE)

CORE ships cross-reference files for every `control_ref` referenced by
`content/mappings/{nis2,dora,cra}` — 28 stable IDs covering the full M0
regulatory surface. Each file anchors the SecOps-NG control to at least
one OSCAL catalog control (NIST 800-53 Rev5 and/or ISO/IEC 27001:2022
Annex A) and at least one MITRE D3FEND defensive technique, with the
offensive ATT&CK techniques the D3FEND tactic addresses captured where
applicable.

| Stable ID | Purpose |
|---|---|
| `control.asset_inventory_delta@v1` | Asset inventory delta capture |
| `control.backup_attestation@v1` | Backup attestation |
| `control.cert_posture_scan@v1` | TLS certificate posture scan |
| `control.cloud_identity_least_privilege@v1` | Cloud identity least-privilege posture |
| `control.control_effectiveness_test@v1` | Control effectiveness test |
| `control.cra_submission_templates@v1` | CRA notification submission templates |
| `control.crypto_policy_inventory@v1` | Cryptography policy inventory |
| `control.cspm_baseline@v1` | Cloud security posture baseline |
| `control.dora_major_classifier@v1` | DORA major incident classifier |
| `control.dora_submission_templates@v1` | DORA notification submission templates |
| `control.iac_policy_guardrail@v1` | Infrastructure-as-code policy guardrail |
| `control.incident_handling_capability@v1` | Incident-handling capability (seed) |
| `control.incident_timeline_signals@v1` | Incident timeline signal capture |
| `control.jml_evidence@v1` | Joiner-mover-leaver evidence |
| `control.key_rotation_evidence@v1` | Key rotation evidence |
| `control.mfa_state_probe@v1` | MFA state probe |
| `control.oob_channel_probe@v1` | Out-of-band emergency channel probe |
| `control.patch_evidence@v1` | Security update / patch evidence |
| `control.phishing_simulation@v1` | Phishing simulation |
| `control.privileged_access_review@v1` | Privileged access review |
| `control.provider_attestation@v1` | ICT third-party provider attestation |
| `control.recurring_incident_correlator@v1` | Recurring-incident correlator |
| `control.restore_drill@v1` | Restore drill |
| `control.risk_management_policy@v1` | Risk management policy |
| `control.sbom_capture@v1` | SBOM capture |
| `control.supplier_inventory@v1` | Supplier inventory |
| `control.training_attestation@v1` | Security training attestation |
| `control.vuln_disclosure_intake@v1` | Coordinated vulnerability disclosure intake |

### Resolution linter (EXTEND)

A standalone resolution linter walks every
`content/mappings/<regime>/*.yaml`, extracts each `control_ref`, and
asserts that the referenced cross-reference file exists, validates
against `content-model/control_xref.schema.json`, and is populated with
at least one `oscal_refs` entry, at least one `d3fend_refs` entry, and
`provenance.source_url` + `provenance.captured_at`.

Run it locally:

```bash
# Human-readable
python -m tools.lint_control_xref

# Machine-readable (CI / dashboards)
python -m tools.lint_control_xref --json
```

Exit code is non-zero whenever a finding is emitted. Finding codes
(stable surface for downstream consumers):

- `missing_xref_file` — a mapping `control_ref` has no
  `content/controls/<ref>.yaml`.
- `schema_violation` — the cross-reference file fails JSON Schema
  validation.
- `missing_oscal_refs` / `missing_d3fend_refs` — the file is present
  but carries no upstream catalog or D3FEND anchors.
- `missing_provenance_source_url` / `missing_provenance_captured_at`
  — provenance fields are absent.

The linter is wired into pytest at
`tests/content/test_control_xref_lint.py`, so CI fails whenever a new
mapping entry references a control that has not yet been populated
here.
