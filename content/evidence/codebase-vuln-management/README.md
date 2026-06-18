# codebase-vuln-management — evidence stream stub

Per-finding disclosure-timeline records produced by the
`codebase-vuln-management` workflow
(`playbook.codebase_vuln_management@v1`).

## Schema

[`disclosure-timeline-record.schema.json`](./disclosure-timeline-record.schema.json)
— typed shape for one per-finding disclosure-timeline record:

- `advisory_id` — canonical advisory anchor (CVE / GHSA / OSV).
- `component` — PURL-shaped affected component+version, pinned
  against the SBOM at `sbom_content_hash`.
- `severity` — four-band tier (`critical` / `high` / `medium` /
  `low`).
- `disclosure_window` — `policy_ref` + `acknowledge_by` / `fix_by` /
  `disclose_by` ISO-8601 UTC absolute timestamps.
- `source_data` — OCSF / telemetry-URN pointer (no embedded raw
  payload).
- `ref_viz` — opaque visualisation pointer reserved for the
  EXTEND-docs-cookbook sibling.

The field shape mirrors `schemas/evidence/effectiveness.schema.json`
(G-04 metric field shape) so downstream auditor-bundle consumers can
ingest records off a single source-shape vocabulary.

## Maturity

`SKELETON` — schema and field inventory are pinned; no detector
implementation, no scanner-CLI invocation, no per-target byte-parity
golden ships at this layer. Those land on the F-WF-07 CORE-FANOUT and
EXTEND-tests-goldens sibling cards.

## Public-bar discipline

Operator-side strings stay role-shaped or URN-shaped; individual
personal names, credential-shaped strings, and raw SBOM / advisory
payloads carrying personal data are out of scope per
[`AGENTS.md`](../../../AGENTS.md) §3 and rejected at the schema
boundary.
