# identity_compromise

CACAO v2 playbook for responding to a detected account compromise —
credential theft, an MFA bypass, an anomalous or impossible-travel
sign-in, or a suspicious OAuth grant: identity-signal triage → MFA
factor reset → session revocation across the IdP and SaaS tenants →
lateral-movement hunt over the principal's blast radius → IAM audit and
removal of residual persistence. Detection authoring stays upstream at
SigmaHQ; the playbook references the rule IDs.

Stable ID: `playbook.identity_compromise@v1`
Compile targets: `n8n`, `temporal`, `langgraph`
Maturity: `stable`

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact.
- `mappings.yaml` — outbound overlay: Sigma, OSCAL, OCSF and regulatory
  references.
- `primitives/` — the deterministic primitives the five action steps
  bind; see Status.

The emitted artifacts ship under
`examples/{n8n,temporal,langgraph}/identity_compromise/`, the
practitioner walkthrough is `docs/cookbook/identity_compromise.md`, and
the cross-layer worked example lives under
`../../../content-model/examples/identity_compromise/`. Every action
body calls its primitive: five n8n Code nodes, and Temporal activity
and LangGraph tool bodies that import and call them. The Temporal
target still leaves workflow control flow to the integrator, as it does
for every playbook.

## Status

`maturity: stable`, `content_version` 1.0.0, promoted straight from
`draft` — the catalogue's last one — as the F-WF-CORE-WAVE-1 card
committed. All five action steps bind a deterministic primitive under
`primitives/` through `x_secops_ng.core_body`, each executed directly by
`tests/playbooks/identity_compromise/test_primitives.py`, and the three
reference targets emit those calls. The graduation checklist recomputes
green: tier A, 5 of 5 real bindings, zero placeholder bodies, zero blank
predicates, zero schema errors, three-target goldens.

| Step | Primitive |
|---|---|
| triage identity signal | `triage.triage_identity_signal` |
| reset MFA factors | `mfa.compose_mfa_reset` |
| revoke active sessions | `sessions.compose_session_revocation` |
| lateral-movement hunt | `hunt.summarise_lateral_hunt` |
| IAM audit and persistence removal | `persistence.plan_persistence_removal` |

Decisions the primitives fix:

- **Benign patterns clear impossible travel and nothing else.** Planned
  travel or sanctioned automation can explain an odd location; they
  cannot explain a sign-in that bypassed MFA, MFA being disabled, or a
  role being misused.
- **Confirmation is an explicit rule:** a decisive detection (MFA
  bypass, MFA disabled, AssumeRole misuse), two distinct uncleared
  detections, or — for a privileged principal — any uncleared detection,
  because the blast radius of an admin account justifies containment on
  one signal. An analyst verdict decides when present; a disagreement
  with the rule is recorded as an override.
- **What does not apply is recorded, not faked.** A service principal
  or workload identity has no MFA factors, so the reset records that it
  does not apply. Session revocation names the tenants the principal can
  reach that no adapter enumerated. The hunt reports which surfaces were
  never queried — the gap `kpi.lateral_hunt_coverage` measures — and
  counts distinct resources touched inside the lookback window.
- **Persistence removal is rule-bound.** Anything on the principal's IAM
  surface created inside the compromise window without an authorising
  change record is removed, standing-privilege role assignments
  included. Everything kept carries its reason.
- Every containment step re-checks the confirmed-branch gate, so a
  mis-wired branch fails loud.

Contract choices settled at the wire. The contract grows from 5 to 24
variables: 14 adapter inputs, one envelope per step, and three of the
five existing names, now fields extracted from those envelopes at the
adapter seam (`__principal_id__` and `__signal_id__` stay the trigger
inputs).

- **The gate reads an extracted field.** `__compromise_confirmed__`
  comes from `__triage_record__` and stays a real boolean, because the
  gate compares it to `true`. `__sessions_revoked_count__` and
  `__lateral_findings_count__` come from the session and hunt
  envelopes.
- **The compromise window is an adapter input.**
  `__compromise_window_start__` is when the compromise began, and the
  window closes at detection. Triage sees detection names and the
  detection time but not the start, so the sign-in history or
  forensic-timeline adapter that has it supplies it.
- **An unset analyst verdict is empty.** The n8n trigger surfaces an
  unset variable as `""`, and triage treats it as no ruling. No other
  input is optional.
- **Lists ride as strings.** CACAO variables have no list type, so the
  eight list inputs (benign patterns, registered factors, live
  sessions, reachable and enumerated tenants, hunt findings, hunted
  surfaces, IAM items) carry JSON-native lists that the target's
  adapter seam marshals.

## Sources

- OASIS CACAO v2.0 specification
- SigmaHQ — upstream identity-protection rules (referenced, not re-authored)
- MITRE ATT&CK — Credential Access (TA0006), Lateral Movement (TA0008)
- ENISA threat landscape — identity and access management
