# security_awareness_training

CACAO v2 SKELETON playbook for the structured security-awareness
training programme lifecycle required by NIS2 Art. 21(2)(g). The
playbook operates the programme-governance surface upstream of the
per-cycle operational execution: schedule the training-needs
assessment → design or update the training content → deliver the
training to in-scope cohorts → record per-staff completion → report
the residual gap set to the training owner → close the cycle with a
dated cycle-review artifact.

This is the PROGRAMME-lifecycle companion to two existing playbooks
under NIS2 Art. 21(2)(g):

- `playbook.cyber_hygiene_training@v1` — the OPERATIONAL per-cycle
  materialisation (roster inventory, cycle assignment, phishing-
  simulation, completion tracking, attestation, notify).
- `playbook.phishing_triage@v1` — the REACTIVE incident-response
  companion.

Together the three cover the clause end-to-end: this playbook
authors what training the operator's programme requires,
`cyber_hygiene_training` discharges per-cycle execution against that
programme, and `phishing_triage` handles the incident lane.

Read-only and side-effect-free against operator infrastructure. The
delivery step writes delivery-intent records to the operator's
learning-management surface; the LMS owns final scheduling and
per-staff dispatch.

## Status

SKELETON. Only the CACAO v2 scaffold and the outbound overlay
(`mappings.yaml`) are populated. Per-target compile examples,
byte-parity goldens, telemetry emit bindings, per-cohort programme-
governance KPIs, and D3FEND / OCSF closure are owned by CORE and
EXTEND sibling cards.

## Steps

1. **schedule-assessment** — resolve required awareness and role-
   based training tracks per cohort against the declared programme
   scope; emit the per-cohort assessment artifact.
2. **design-content** — author or update the per-track curriculum
   against the assessment; emit the per-track curriculum artifact.
3. **deliver-training** — deliver the cycle's curriculum to in-scope
   cohorts along the operator's declared training channels; emit the
   per-cohort delivery artifact.
4. **record-completion** — read per-staff completion state from the
   learning-management surface; emit per-staff and per-cohort
   completion artifacts.
5. **report-gaps** — compose the residual-gap report (missed-
   mandatory, overdue role-based, uncovered regulatory training
   requirement) for the training owner.
6. **review-cycle** — close the cycle with a dated cycle-review
   artifact referencing the assessment, curriculum, delivery,
   completion, and gap-report records, plus recommendations feeding
   the next cycle's assessment.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.security_awareness_training@v1`).
- `mappings.yaml` — outbound overlay (OSCAL controls, D3FEND stub,
  OCSF stub, NIS2 Art. 21(2)(g), GDPR Art. 32(1)(b), ISO/IEC 27001
  Annex A.6.3).

## Goal links

- **G-01** — content coverage: structured programme-lifecycle
  playbook closing the NIS2 Art. 21(2)(g) programme-governance
  surface upstream of the already-shipped operational and reactive
  siblings under the same clause; advances the target of ≥ 25 CACAO
  v2 playbooks.
- **G-02** — regulatory-graph closure: NIS2 Art. 21(2)(g) primary
  anchor with sibling references to GDPR Art. 32(1)(b) staff-training
  organisational-measures obligation and ISO/IEC 27001 Annex A.6.3.

## Binding status

Deliberately unbound. The 6 action steps compile with operator-TODO
bodies on all three targets and the playbook carries no `core_body`
primitive bindings; `catalog.py` reports it that way and the playbook
stays `experimental` under the Maturity ladder. This is a recorded
decision (#921 — PARK bucket, Director 2026-09-04), not neglect:
the training lifecycle is LMS-owned in practice, and F-WF-SECAWARENESS shipped its real value — the control definitions and the programme-governance metrics — already; parked together with its `cyber_hygiene_training` companion pending a merge decision (park-both). Reopening the park is a roadmap decision, not a bug — the
trigger would be that the merge decision is taken, after which the surviving playbook is bound once.
