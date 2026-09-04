# post_incident_review

CACAO v2 starter playbook for the post-incident review: timeline
collation → blameless review template → corrective-action tracking.
The playbook formalises learning into auditable, restartable state — it
does not re-litigate the incident.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.post_incident_review@v1`).

## Sigma references

Detection bindings on the timeline-collation step reference upstream
SigmaHQ rule IDs only; SecOps-NG does not re-author Sigma rules. The
rules selected here are anti-forensics / audit-tampering signals — their
presence in the incident window flags gaps in the evidence record so the
review template can explicitly address decisions made under partial
evidence rather than silently smoothing them over. The playbook surfaces
the full Sigma `external_references` list at the playbook level for
portability. Spot-checkable rule IDs:

- `a62b37e0-45d3-48d9-a517-90c1a1b0186b` — Eventlog Cleared
- `d99b79d2-0a6f-4f46-ad8b-260b6e17f982` — Security Eventlog Cleared
- `100ef69e-3327-481c-8e5c-6d80d9507556` — Important Windows Eventlog
  Cleared
- `cc36992a-4671-4f21-a91d-6c2b72a2edf5` — Suspicious Eventlog Clearing
  or Configuration Change Activity
- `69aeb277-f15f-4d2d-b32a-55e883609563` — Windows Event Auditing
  Disabled
- `0a13e132-651d-11eb-ae93-0242ac130002` — Audit Policy Tampering Via
  Auditpol
- `c6438007-e081-42ce-9483-b067fbef33c3` — Powershell Timestomp

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. Emitted
artifacts and golden tests live under
`tests/compilers/{n8n,temporal,langgraph}/test_post_incident_review.py`
(plus `examples/langgraph/post_incident_review/` for the LangGraph
worked example); they were authored by the three CORE cards (PRs #74,
#79, #86) against the shared CACAO fixture at
`tests/compilers/_shared/fixtures/post_incident_review.cacao.json`.
This directory ships the portable content only.

## Worked example

The cross-layer worked example — control, telemetry, metrics, and
regulatory cross-references that bind to this playbook — lives at
`../../../content-model/examples/post_incident_review/`. The metrics
shipped there are pinned by `x_secops_ng.metric_refs` above; the
regulatory cross-references wire the metrics into NIS2 / DORA / CRA
mapping packs under `../../mappings/`.

## Sources

- OASIS CACAO v2.0 specification
- ENISA — Good Practices for Supply Chain Cybersecurity
  (post-incident learning patterns)
- OCSF — Security Finding, Process Activity, File Activity, and
  Authentication event classes
- SigmaHQ — upstream anti-forensics / audit-tampering rule IDs
  referenced inline

## Binding status

Deliberately unbound. The 3 action steps compile with operator-TODO
bodies on all three targets and the playbook carries no `core_body`
primitive bindings; `catalog.py` reports it that way and the playbook
stays `experimental` under the Maturity ladder. This is a recorded
decision (#921 — PARK bucket, Director 2026-09-04), not neglect:
three steps of human facilitation — timeline collation, a blameless review, corrective-action tracking — where a deterministic primitive would be ceremony around a conversation. Reopening the park is a roadmap decision, not a bug — the
trigger would be that corrective-action tracking is ever wired into an audited evidence store.
