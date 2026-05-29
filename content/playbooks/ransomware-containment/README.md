# ransomware-containment

CACAO v2 starter playbook for containing an in-progress ransomware event:
signal triage → endpoint isolation (EDR primary, network ACL fallback) →
identity revocation → backup verification → comms plan (IR lead + comms
officer + NIS2 Article 23 24-hour early-warning draft).

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.ransomware_containment@v1`).

## Sigma references

Detection bindings on individual workflow steps reference upstream
SigmaHQ rule IDs only; SecOps-NG does not re-author Sigma rules. The
playbook surfaces the full Sigma `external_references` list at the
playbook level (`external_references[]`) for portability. Spot-checkable
rule IDs:

- `c947b146-0abc-4c87-9c64-b17e9d7274a2` — Shadow Copies Deletion Using
  Operating Systems Utilities
- `21ff4ca9-f13a-41ad-b828-0077b2af2e40` — Deletion of Volume Shadow
  Copies via WMI with PowerShell
- `89f75308-5b1b-4390-b2d8-d6b2340efaf8` — Windows Backup Deleted Via
  Wbadmin.EXE
- `e3f673b3-65d1-4d80-9146-466f8b63fa99` — Suspicious Appended Extension
  (ransomware file rename)
- `192a0330-c20b-4356-90b6-7b7049ae0b87` — Successful Overpass the Hash
  Attempt

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. Emitted
artifacts under `examples/{n8n,temporal,langgraph}/ransomware-containment/`
are authored by the CORE card; this directory ships the portable
content only.

## Worked example

The cross-layer worked example — detection, control, telemetry, and
metrics artifacts that bind to this playbook — is authored by the EXTEND
card under `../../../content-model/examples/ransomware-containment/`.

## Sources

- OASIS CACAO v2.0 specification
- ENISA — Threat Landscape and Good Practices for Incident Notification
- NIS2 Directive (EU) 2022/2555, Article 23 — incident reporting
  obligations and the 24-hour early-warning clock
- DORA Regulation (EU) 2022/2554, Article 19 — reporting of major
  ICT-related incidents
- OCSF — Process Activity, File Activity, Network Activity,
  Authentication, and Security Finding event classes
- SigmaHQ — upstream ransomware-adjacent rule IDs referenced inline
