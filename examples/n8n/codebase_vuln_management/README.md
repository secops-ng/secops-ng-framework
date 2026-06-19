# examples/n8n/codebase_vuln_management

Worked example: one disclosure-timeline evidence record emitted by the
**n8n** target for the F-WF-07 *codebase vulnerability management*
workflow. The canonical CACAO playbook lives at
`../../../content/playbooks/codebase_vuln_management/playbook.cacao.json`;
this folder holds one representative artefact emitted by the n8n
adapter, plus the regeneration script.

## Scope

CORE-N8N — the n8n target only. The disclosure-timeline-record
schema lives at
`../../../content/evidence/codebase_vuln_management/disclosure-timeline-record.schema.json`.
Per-target byte-parity goldens, the Temporal and LangGraph adapters,
and the cookbook walkthrough are separate sibling cards.

## Source

| Path                                                     | Purpose                          |
|----------------------------------------------------------|----------------------------------|
| `regenerate.py`                                          | Drives the n8n adapter end-to-end |
| `evidence/disclosure-timeline-record.json`               | One emitted finding              |

Regenerate after any change to the shared emitter or the n8n adapter,
from the repo root:

    PYTHONPATH=. python examples/n8n/codebase_vuln_management/regenerate.py

The adapter writes a deterministic `<id>.json`; the script copies it to
the human-friendly `evidence/disclosure-timeline-record.json` for
diffing and removes the sha-named twin so the committed tree only
carries the friendly name.

## What the record carries

Per the schema:

- `id` — SHA-256(`workflow_id|sbom_content_hash|component.purl|advisory_id`).
  Deterministic on those four inputs.
- `sbom_content_hash` — SHA-256 of the SBOM bytes the finding was
  derived from. Anchors the record to a specific SBOM revision.
- `advisory_id` — canonical advisory id (CVE / GHSA / OSV / vendor).
- `component` — affected component+version pinned against the SBOM,
  PURL-shaped so it joins back into the SBOM artefact.
- `severity` — four-band CVSS-derived tier
  (`critical` / `high` / `medium` / `low`).
- `disclosure_window` — `acknowledge_by` / `fix_by` / `disclose_by`
  deadlines computed against the operator's CVD policy
  (`policy_ref`).
- `source_data` — source-shape pointer for the finding. The
  underlying advisory payload is **not** embedded; the OCSF pointer
  (class_uid 2002 — Vulnerability Finding) is the public-bar-safe
  surface per AGENTS.md §3.
- `ref_viz` — visualisation pointer for the downstream
  dashboard / auditor-bundle surfaces.
- `captured_at` — UTC second-precision ISO-8601 timestamp the
  `assess-disclosure` step resolved the record.

## What this example does not do

- It does not emit a runnable `workflow.n8n.json`. The merged
  F-WF-07 SKELETON playbook ships placeholder action bodies that the
  topology-translating CACAO → n8n emitter cannot lower today; the
  CORE-N8N scope here is the *evidence emitter*, not the workflow
  translator. A runnable `workflow.n8n.json` lands once the
  CORE-FANOUT card wires action bodies into the playbook.
- It does not embed advisory text, reporter contact information, or
  raw SBOM payload. These are operator-side surfaces; per AGENTS.md
  §3 they may carry personal data and are out of scope at this
  layer.

## Sovereignty note

The default scanner / advisory feed an operator plugs into the
`ingest-sbom` and `review-deps` steps is an EU-installable CLI; the
operator runs it on infrastructure they control. No telemetry, no
findings, no SBOM bytes flow to this repository or to the SecOps-NG
project — we ship the structure, they own the data plane.
