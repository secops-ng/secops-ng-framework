# examples/langgraph/codebase_vuln_management

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the codebase vulnerability management CACAO playbook (F-WF-07 —
NIS2 Art. 21(2)(e), CRA Annex I §2). It is aimed at an integrator who
already runs LangGraph and wants to adopt the portable SecOps-NG
playbook without re-platforming: the example shows exactly which
artifacts the compiler produces, how they fit together, and where the
integrator owns the seams.

The canonical CACAO playbook lives at
`../../../content/playbooks/codebase_vuln_management/playbook.cacao.json`;
this folder holds the LangGraph artifacts emitted from it plus one
representative disclosure-timeline evidence record produced by the
LangGraph node adapter.

## Files in this directory

| File | Role |
|------|------|
| `playbook.cacao.json` | Portable CACAO v2 playbook — byte-identical mirror of the canonical source. |
| `graph_spec.json` | Target-neutral GraphSpec (nodes, edges, conditional edges) emitted by `compilers.langgraph.emit`. |
| `state_bindings.py` | Generated `TypedDict` state + `@tool`-decorated action wrappers; tool bodies call the deterministic primitives in `content.playbooks.codebase_vuln_management.primitives`. |
| `_audit_mirror.py` | Dependency-free `AuditTrail` / `AuditRecord` sibling materialised by the compiler. |
| `assemble.py` | Hand-written reference assembly that wires the GraphSpec + bindings into a `langgraph.graph.StateGraph`. |
| `regenerate.sh` | Re-runs both emitters from the canonical playbook and overwrites the mirrored CACAO + the generated artifacts. |
| `regenerate.py` | Drives the LangGraph evidence node adapter end-to-end to refresh `evidence/disclosure-timeline-record.json`. |
| `evidence/disclosure-timeline-record.json` | One emitted disclosure-timeline finding for the worked example. |

## How to regenerate

After any change to the canonical playbook or to
`compilers/langgraph/*`, refresh the committed artifacts from the
repo root:

```bash
./examples/langgraph/codebase_vuln_management/regenerate.sh
```

The script mirrors the canonical CACAO source into this folder and
re-emits `graph_spec.json` and `state_bindings.py` from it using
`compilers.langgraph.emit` and `compilers.langgraph.state`. A
byte-parity golden test in
`tests/examples/codebase_vuln_management/test_langgraph_workflow_golden.py`
fails the suite if the committed artifacts diverge from a fresh
regeneration, so the worked example stays honest as the compiler
evolves.

To refresh the disclosure-timeline evidence record (independent of the
workflow graph), regenerate via the shared emitter:

```bash
PYTHONPATH=. python examples/langgraph/codebase_vuln_management/regenerate.py
```

## Cross-target pointers

The same canonical playbook ships under the other two reference
compile targets so an integrator can compare lowerings side by side:

- [`examples/n8n/codebase_vuln_management/`](../../n8n/codebase_vuln_management/) — n8n no-code workflow.
- [`examples/temporal/codebase_vuln_management/`](../../temporal/codebase_vuln_management/) — Temporal durable workflow stub.

The disclosure-timeline evidence record emitted by the LangGraph node
adapter is byte-identical to the n8n and Temporal siblings — the
shared emitter under `compilers/_shared/evidence/disclosure_timeline.py`
is the single source of truth and the per-target adapters are thin
glue.

## What the workflow does

The CACAO playbook is a four-step SBOM-driven loop:

1. `ingest-sbom` — pin the SHA-256 of the canonical SBOM artefact for
   the release under review.
2. `review-deps` — walk the SBOM's top-level dependencies against a
   vulnerability database (NVD, OSV, GHSA) using the operator's
   locally-runnable scanner CLI, canonicalise to the playbook contract.
3. `assess-disclosure` — resolve per-finding disclosure-window
   deadlines from the operator's CVD policy and the scanner-derived
   severity tier.
4. `track-timeline` — emit one disclosure-timeline record per finding
   for the downstream metrics streams.

The four `@tool` wrappers in `state_bindings.py` call the deterministic
primitives under
`content.playbooks.codebase_vuln_management.primitives.*` — the CORE
action bodies are wired, not placeholder `NotImplementedError` stubs.
Operators replace the per-finding loop (steps 3 and 4) in their own
runtime's native idiom (LangGraph map / fan-out).

## What the record carries

Per `content/evidence/codebase_vuln_management/disclosure-timeline-record.schema.json`:

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

The LangGraph node is a plain `state -> partial-state` function that
delegates to the framework-agnostic emitter under
`compilers/_shared/evidence/disclosure_timeline.py`. Record shape,
schema-conforming serialisation, deterministic `id`, and the atomic-
write contract all live on the shared helper so the n8n, Temporal, and
LangGraph targets share one source of truth — the inputs are pinned
byte-identical across the three siblings so the per-target adapters
write byte-identical records.

## What this example does not do

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
