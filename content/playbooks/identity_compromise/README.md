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
Maturity: `draft`

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact.
- `mappings.yaml` — outbound overlay: Sigma, OSCAL, OCSF and regulatory
  references.
- `primitives/` — the deterministic primitives the five action steps
  bind at CORE-WIRE; see Status.

The emitted artifacts ship under
`examples/{n8n,temporal,langgraph}/identity_compromise/`, the
practitioner walkthrough is `docs/cookbook/identity_compromise.md`, and
the cross-layer worked example lives under
`../../../content-model/examples/identity_compromise/`. The examples are
regenerated from the canonical source, which is not yet bound, so the
action bodies are still operator placeholders.

## Status

`maturity: draft` — the catalogue's only one — with CORE-PRIM complete.
Each of the five action steps has a deterministic primitive under
`primitives/`, executed directly by
`tests/playbooks/identity_compromise/test_primitives.py`:

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

**Owed: the wire.** The CACAO steps do not yet carry
`x_secops_ng.core_body`, so `catalog.py` reports 0 of 5 bound. The
F-WF-CORE-WAVE-1 card commits to binding this playbook and promoting it
out of `draft` on a recomputed checklist; that is the CORE-WIRE card.

## Sources

- OASIS CACAO v2.0 specification
- SigmaHQ — upstream identity-protection rules (referenced, not re-authored)
- MITRE ATT&CK — Credential Access (TA0006), Lateral Movement (TA0008)
- ENISA threat landscape — identity and access management
