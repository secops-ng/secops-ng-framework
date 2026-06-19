# incident_management — workflow-local module tree

The canonical source playbook for F-WF-05 (incident management) ships as
the CACAO JSON at `content/playbooks/incident_management/playbook.cacao.json`
in this same directory. The subdirectory layout follows the precedent set
by every other multi-artifact playbook in the cookbook
(`ransomware_containment`, `post_incident_review`, …) and the resolution
of the layout question for F-WF-05; see
`docs/internal/f-wf-05-gap-inventory.md` § 4 question 3.

This directory carries the workflow-local Python artifacts the
per-target CORE action bodies (n8n / Temporal / LangGraph) will bind
against once the CORE-PRIM card lands:

- `primitives/` — deterministic helpers (stage-clock arithmetic,
  significance + cross-border classification policy, the
  regulator-submission contract that takes an operator-configured
  destination, the F-PT-02 incident-timeline binding layer) plus a
  DSPy signature reserved for the free-text fields on the final-report
  submission. Shipped in CORE-PRIM. The F-PT-02 binding ships as a
  thin in-package adapter (`PT02_BINDING_STATUS = "adapter"`) per the
  gap inventory § 4 question 1 — `patterns/incident_timeline/` is not
  yet on `main`. When that pattern module lands, the adapter swaps
  for the real binding without per-target CORE bodies changing
  shape.
- `payloads/` — workflow-local typed payload models for the four
  shapes the playbook handles: the intake event, the 24-hour early
  warning, the 72-hour notification, and the one-month final report.
  Workflow-local rather than under `content/telemetry/` for the same
  reason the alert_triage payloads are: these shapes are the
  operator-facing regulator-submission envelopes, not OCSF telemetry
  classes. Not yet present on disk — lands in CORE-PRIM.

Per the project's framework-agnostic stance, none of these modules
will import a runtime (no n8n SDK, no Temporal SDK, no LangGraph SDK).
They are pure Python plus Pydantic v2 and, for the free-text
signature, a lazy DSPy import.
