# ransomware_containment

CACAO v2 starter playbook for containing an in-progress ransomware event:
signal triage → endpoint isolation (EDR primary, network ACL fallback) →
identity revocation → backup verification → comms plan (IR lead + comms
officer + NIS2 Article 23 24-hour early-warning draft).

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.ransomware_containment@v1`).
- `mappings.yaml` — outbound overlay: Sigma, OSCAL, OCSF and regulatory
  references.
- `primitives/` — the deterministic primitives the six action steps
  bind; see Status.

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

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. The
emitted artifacts ship under
`examples/{n8n,temporal,langgraph}/ransomware_containment/`, with the
practitioner walkthrough at `docs/cookbook/ransomware_containment.md`.
Every action body calls its primitive: six n8n Code nodes, and
Temporal activity and LangGraph tool bodies that import and call it. The
Temporal target still leaves workflow control flow to the integrator, as
it does for every playbook.

## Worked example

The cross-layer worked example — detection, control, telemetry, and
metrics artifacts that bind to this playbook — lives under
`../../../content-model/examples/ransomware_containment/`.

## Status

`maturity: stable`, `content_version` 1.0.0. All six action steps bind
a deterministic primitive under `primitives/` through
`x_secops_ng.core_body`, each executed directly by
`tests/playbooks/ransomware_containment/test_primitives.py`, and the
three reference targets emit those calls. The graduation checklist
recomputes green: tier A, 6 of 6 real bindings, zero placeholder bodies,
zero blank predicates, zero schema errors, three-target goldens.

| Step | Primitive |
|---|---|
| triage signal | `triage.triage_ransomware_signal` |
| endpoint isolation — EDR isolate | `isolation.compose_edr_isolation` |
| endpoint isolation — network ACL deny (fallback) | `isolation.compose_network_isolation` |
| identity revocation | `identity.compose_identity_revocation` |
| backup verification | `backup.select_known_good_snapshot` |
| comms plan | `comms.compose_comms_plan` |

Decisions the primitives fix, because they start containment:

- **Confirmation is an explicit rule.** A decisive artifact (a known
  ransomware binary or a ransom note), a mass file-extension rename with
  at least one corroborating indicator, or shadow-copy *and*
  backup-catalogue deletion together. The last is the pre-encryption
  stage, the best moment to contain, so the rule does not wait for
  encryption. An analyst verdict decides when present, and a
  disagreement with the evidence is recorded as an override.
- **A protected host or principal waits for approval.** Automatically
  isolating a domain controller, or disabling a break-glass or backup
  service account, can do more harm than the incident.
- **Revocation lists what the IdP cannot do.** Tokens or Kerberos
  tickets the IdP cannot revoke are named, not claimed.
- **Known-good means verified.** The selected snapshot is the newest one
  taken strictly before the compromise window whose digest matches the
  backup catalogue; failed candidates are listed with their reasons. The
  step never restores.
- **The early warning is staged, never sent.** The comms plan pages the
  IR lead and comms officer and drafts the NIS2 Art. 23(4)(a) early
  warning, due 24 hours from detection, for human sign-off; a late draft
  records the overrun.
- Every containment step re-checks the gates behind it, so a mis-wired
  branch fails loud instead of acting on an unconfirmed signal.

Contract choices settled at the wire. The contract grows from 7 to 26
variables: the adapter inputs each primitive reads, one envelope per
step, and six of the seven existing names, now fields extracted from
those envelopes at the adapter seam (`__signal_id__` stays the trigger
input).

- **The gates read extracted fields.** `__ransomware_confirmed__` and
  `__edr_available__` come from `__triage_record__`, and stay real
  booleans because both gates compare them to `true`.
- **The compromise window is an adapter input.**
  `__compromise_window_start__` is the earliest indicator, not
  detection, because dwell time precedes detection. Triage sees
  indicator names but not their timestamps, so the hydration or
  forensic-timeline adapter that has them supplies it.
- **An unset analyst verdict is empty.** The n8n trigger surfaces an
  unset variable as `""`, and triage treats it as no ruling.
- **Lists ride as strings.** CACAO variables have no list type, so
  `__snapshots__` and `__protected_identities__` carry JSON-native lists
  that the target's adapter seam marshals.
- **No principal is a valid answer.** `__affected_identity__` is null
  when the signal implicates no identity, and the identity step then
  emits an empty directive rather than failing.

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
