# content/controls/

OSCAL component definitions and D3FEND tactic mappings. These are the
control-side anchors that playbooks and mappings reference.

## Cross-reference layer (SKELETON)

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

### Seed (worked example)

The SKELETON ships one populated cross-reference file:

- `control.incident_handling_capability@v1.yaml` — anchors the control
  referenced by `nis2:art-21-2-b` (NIS2 Article 21(2)(b) — incident
  handling) to NIST 800-53 Rev5 IR-4 / IR-8, ISO/IEC 27001:2022 A.5.24
  / A.5.26, and MITRE D3FEND D3-IRA (Incident Response Analysis) /
  D3-FA (Forensic Analysis).

### What CORE and EXTEND will follow up on

- **CORE** — populate cross-reference files for *every* `control_ref`
  referenced by `content/mappings/{nis2,dora,cra}` so the substrate
  covers the full M0 regulatory surface.
- **EXTEND** — add a linter under `tests/content/` that asserts each
  mappings entry's `control_ref` resolves to a control file with at
  least one `oscal_ref` and one `d3fend_ref`.

Until EXTEND lands, the absence of a cross-reference file for a given
`control_ref` is not an error — it's an unfilled cell in the substrate.
