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
are regenerated from the canonical source, which is not yet bound, so
the action bodies are still operator placeholders rather than primitive
calls.

## Status

`maturity: experimental`, CORE-PRIM complete. Each of the five action
steps has a deterministic primitive under `primitives/`, executed
directly by `tests/playbooks/data_exfil/test_primitives.py`:

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

**Owed: the wire.** The CACAO steps do not yet carry
`x_secops_ng.core_body`, so `catalog.py` reports 0 of 5 bound. Binding
the five steps, declaring the variables they need, regenerating the
examples and recomputing the Maturity ladder is the CORE-WIRE card.

## Sources

- OASIS CACAO v2.0 specification
- ENISA — Threat Landscape and Good Practices for Incident Notification
- NIS2 Directive (EU) 2022/2555, Article 23 — incident reporting obligations
- DORA Regulation (EU) 2022/2554, Article 19 — reporting of major ICT-related incidents
- OCSF — DLP Activity and Security Finding event classes
- SigmaHQ — upstream rule IDs referenced in the detection layer
