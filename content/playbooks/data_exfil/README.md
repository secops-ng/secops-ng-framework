# data_exfil

CACAO v2 starter playbook for responding to a confirmed-or-suspected
data-exfiltration signal: DLP / egress signal → scope assessment →
containment → regulator / affected-party notification gate.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact (`playbook.data_exfil@v1`).
- `mappings.yaml` — outbound overlay: Sigma, OSCAL, OCSF and regulatory
  references.
- `primitives/` — the deterministic primitives the five action steps
  bind at CORE-WIRE; see Status.

## Worked example

The cross-layer worked example — detection, control, telemetry, and
metrics artifacts that bind to this playbook — lives at
`../../../content-model/examples/data_exfil/`. Start with the README
there for the cross-reference graph and per-artifact stable IDs.

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. The
emitted artifacts ship under `examples/{n8n,temporal,langgraph}/data_exfil/`,
with the practitioner walkthrough at `docs/cookbook/data_exfil.md`. They
call the bound primitives: five n8n Code nodes, and Temporal activity
and LangGraph tool bodies that import and call them. The Temporal target
still leaves workflow control flow to the integrator, as it does for
every playbook.

## Status

`maturity: stable`, `content_version` 1.0.0. All five action steps bind
a deterministic primitive under `primitives/` through
`x_secops_ng.core_body`, each executed directly by
`tests/playbooks/data_exfil/test_primitives.py`, and the three reference
targets emit those calls. The graduation checklist recomputes green:
tier A, 5 of 5 real bindings, zero placeholder bodies, zero blank
predicates, zero schema errors, three-target goldens.

| Step | Primitive |
|---|---|
| triage signal | `triage.triage_egress_signal` |
| scope assessment | `scope.assess_exfil_scope` |
| containment | `containment.compose_exfil_containment` |
| notify regulator | `notification.compose_regulator_notification` |
| notify affected party | `notification.compose_subject_notification` |

Decisions the primitives fix:

- **Triage feeds scope assessment, not a gate.** The playbook has no
  branch after triage, so the known-benign verdict travels in the triage
  record and scope assessment closes such a signal out. A known-benign
  destination never clears a signal that also saw a staging archive
  created — exfiltration through a sanctioned destination is a standard
  technique.
- **Uninspected content is the worst case.** Encrypted or unclassifiable
  content, or a transfer with no findings at all, is flagged; the
  subject count becomes a lower bound, and it routes to the regulator,
  is contained, and triggers data-subject notice as the most sensitive
  class would.
- **Containment is proportionate:** egress block and session revocation
  always; credential rotation from `confidential` up; host isolation
  from `restricted` up or past the subject threshold. Protected hosts
  and identities wait for approval.
- **One regulator notice per applicable regime, each on its own clock
  from awareness:** GDPR Art. 33(1) at 72 hours (only when personal data
  may be affected), NIS2 Art. 23(4)(a) and DORA Art. 19(4)(a) at 24
  hours. A required notice no configured channel can carry fails loud.
- **The data-subject determination always carries its basis** under
  GDPR Art. 34 — an unjustified non-notification is not representable.

Contract choices settled at the wire. The contract grows from 5 to 21
variables: 11 adapter inputs, one envelope per step, and four of the
five existing names, now fields extracted from the scope envelope at the
adapter seam (`__signal_id__` stays the trigger input).

- **The gates read extracted fields.** `__exfil_confirmed__` and
  `__regulator_required__` come from `__scope_assessment__`, and stay
  real booleans because both gates compare them to `true`.
- **The clocks run from awareness.** `__aware_at__` is an adapter input:
  the instant the operator became aware of the breach, which both
  notification steps read. A value before detection fails loud.
- **Lists ride as strings.** CACAO variables have no list type, so
  `__benign_patterns__` and `__dlp_findings__` carry JSON-native lists
  that the target's adapter seam marshals.
- **Nothing is optional.** No input has an unset meaning, so an empty
  string from the n8n trigger fails loud rather than being read as a
  default.

## Sources

- OASIS CACAO v2.0 specification
- ENISA — Threat Landscape and Good Practices for Incident Notification
- NIS2 Directive (EU) 2022/2555, Article 23 — incident reporting obligations
- DORA Regulation (EU) 2022/2554, Article 19 — reporting of major ICT-related incidents
- OCSF — DLP Activity and Security Finding event classes
- SigmaHQ — upstream rule IDs referenced in the detection layer
