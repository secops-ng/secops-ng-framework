# alert_triage — workflow-local module tree

The canonical source playbook for F-WF-03 (alert triage) ships as the
flat YAML at `content/playbooks/alert_triage.cacao.yaml` — the layout
question whether the YAML should move under this directory is a
separate refactor and is deliberately out of scope for this module
tree. See `docs/internal/f-wf-03-gap-inventory.md` § 4 question 1.

This directory carries the workflow-local Python artifacts the
per-target CORE action bodies (n8n / Temporal / LangGraph) bind
against:

- `primitives/` — deterministic helpers + the DSPy signature for the
  free-text analyst-narrative field. Prioritisation policy, suppression
  window, and typed-payload validators all live here so the per-target
  compilers depend on one shared contract.
- `payloads/` — workflow-local typed alert payload models for the two
  source shapes the playbook ingests (push from the detection pipeline,
  pull from a shared alert store). Workflow-local rather than under
  `content/telemetry/` because these shapes are the operator-facing
  alert envelope, not OCSF telemetry classes; the OCSF binding is
  documented on the CACAO playbook itself via `telemetry_refs`.

Per the project's framework-agnostic stance, none of these modules
import a runtime (no n8n SDK, no Temporal SDK, no LangGraph SDK). They
are pure Python plus Pydantic v2 and, for the free-text signature, a
lazy DSPy import.
