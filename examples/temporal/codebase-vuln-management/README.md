# examples/temporal/codebase-vuln-management

Worked example: one disclosure-timeline evidence record emitted by the
**Temporal** target for the F-WF-07 *codebase vulnerability
management* workflow. The canonical CACAO playbook lives at
`../../../content/playbooks/codebase-vuln-management/playbook.cacao.json`;
this folder holds one representative artefact emitted by the Temporal
activity adapter, plus the regeneration script.

## Scope

CORE-TEMPORAL — the Temporal target only. The disclosure-timeline-record
schema lives at
`../../../content/evidence/codebase-vuln-management/disclosure-timeline-record.schema.json`.
The n8n adapter ships at `../../n8n/codebase-vuln-management/`; the
LangGraph adapter and the per-target byte-parity goldens land in
separate sibling cards.

## Source

| Path                                                     | Purpose                                |
|----------------------------------------------------------|----------------------------------------|
| `regenerate.py`                                          | Drives the Temporal activity end-to-end |
| `evidence/disclosure-timeline-record.json`               | One emitted finding                    |

Regenerate after any change to the shared emitter or the Temporal
adapter, from the repo root:

    PYTHONPATH=. python examples/temporal/codebase-vuln-management/regenerate.py

The activity writes a deterministic `<id>.json`; the script copies it
to the human-friendly `evidence/disclosure-timeline-record.json` for
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

The Temporal activity is a thin async adapter
(`@activity.defn`-decorated) that delegates to the framework-agnostic
emitter under `compilers/_shared/evidence/disclosure_timeline.py`.
Record shape, schema-conforming serialisation, deterministic `id`,
and the atomic-write contract all live on the shared helper so the
n8n, Temporal, and LangGraph targets share one source of truth — the
inputs are pinned byte-identical to the n8n sibling so the per-target
adapters write byte-identical records.

## What this example does not do

- It does not emit a runnable `workflow.temporal.py`. The merged
  F-WF-07 SKELETON playbook ships placeholder action bodies that the
  topology-translating CACAO → Temporal emitter cannot lower today;
  the CORE-TEMPORAL scope here is the *evidence emitter activity*,
  not the workflow translator. A runnable `workflow.temporal.py`
  lands once the CORE-FANOUT card wires action bodies into the
  playbook.
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
