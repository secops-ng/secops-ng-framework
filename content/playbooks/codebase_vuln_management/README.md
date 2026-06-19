# codebase_vuln_management

SBOM-driven codebase vulnerability management playbook for operators
that build or distribute software under NIS2 Art. 21(2)(e) and the CRA
Annex I §2 product-side vulnerability-handling obligations.

This workflow takes a freshly produced or refreshed SBOM as input,
walks the declared dependencies against a vulnerability database,
assesses each finding against the operator's coordinated-vulnerability-
disclosure (CVD) policy, and emits per-finding disclosure-timeline
records that downstream metrics streams consume.

## Maturity

`CORE` — scope is the four-state CACAO topology, the per-finding
disclosure-timeline record schema, the NIS2 / CRA mapping stubs, and
the per-step action bodies bound to deterministic primitives at
`content.playbooks.codebase_vuln_management.primitives.*`. The n8n
and Temporal compile targets emit per-target artefacts (see
[Pending siblings](#pending-siblings) for the LangGraph slice).

## State machine

```
ingest-sbom -> review-deps -> assess-disclosure -> track-timeline
```

Transitions are deterministic — every state has exactly one
`on_completion` successor, no conditional branching at this layer. The
EXTEND-tests-goldens sibling will add the per-target byte-parity
golden suite that pins these transitions.

| State              | Purpose                                                            |
|--------------------|--------------------------------------------------------------------|
| `ingest-sbom`      | Ingest the canonical SBOM artefact produced by the operator's build chain (CycloneDX or SPDX), pin its content hash, and stamp the workflow case. |
| `review-deps`      | Walk the SBOM's top-level dependencies against a vulnerability database (NVD, OSV, GHSA), produce one finding per affected component+version pair. |
| `assess-disclosure`| Score each finding against the operator's CVD policy: severity tier, fixed-version availability, disclosure-window deadlines (Annex I §2(2) "without delay" + the CVD policy's published timetable). |
| `track-timeline`   | Emit one disclosure-timeline record per finding (see [`disclosure-timeline-record.schema.json`](../../evidence/codebase_vuln_management/disclosure-timeline-record.schema.json)) so the downstream metric streams pick it up. |

## Sovereign-stack default

The reference scanner is a CLI installable from an EU-hosted package
index. No hosted scanner SaaS dependency, no non-EU default endpoint.
Operators MAY swap in any locally-runnable scanner that produces the
same finding shape; the playbook commits to the finding contract, not
the scanner binary.

## Files

- `playbook.cacao.json` — the CACAO v2 source
  (`playbook.codebase_vuln_management@v1`). Per-step action bodies
  are bound to deterministic primitives at
  `content.playbooks.codebase_vuln_management.primitives.*`.

## GDPR scope

This workflow processes dependency / SBOM metadata, not personal data.
The lawful-basis position is "out of scope: no personal data processed
in this workflow", stated in full in
[`content/mappings/gdpr/data-flow-codebase_vuln_management.md`](../../mappings/gdpr/data-flow-codebase_vuln_management.md).

## Regulatory anchors

- NIS2 Art. 21(2)(e) — security in network and information systems
  acquisition, development, and maintenance, including vulnerability
  handling and disclosure, and SBOM production for releases.
- CRA Annex I §2(1) — SBOM in machine-readable form.
- CRA Annex I §2(2) — address and remediate vulnerabilities without
  delay.
- CRA Annex I §2(5) — coordinated-vulnerability-disclosure policy.
- CRA Annex I §2(7) — security-update dissemination.

Mappings:

- [`content/mappings/nis2/article-21-2-e.yaml`](../../mappings/nis2/article-21-2-e.yaml)
  (entry `nis2:art-21-2-e-codebase`).
- [`content/mappings/cra/article-14-and-annex-i.yaml`](../../mappings/cra/article-14-and-annex-i.yaml)
  (entry `cra:annex-i-2-codebase-vuln-mgmt`).

## Pending siblings

The CORE-FANOUT-N8N and CORE-FANOUT-TMP slices have landed (n8n and
Temporal compile targets emit per-target artefacts under
`examples/{n8n,temporal}/codebase_vuln_management/` and the
disclosure-timeline-record evidence emitter ships under
`compilers/_shared/evidence/disclosure_timeline.py`). The remaining
work is tracked as separate sibling cards that land after this one:

- **CORE-FANOUT-LG** — the LangGraph compile target for this
  workflow, mirroring the n8n / Temporal emitters and pinning the
  per-target byte-parity golden under
  `tests/examples/codebase_vuln_management/`.
- **EXTEND-tests-goldens** — cross-target byte-parity test pinning
  the n8n / Temporal / LangGraph disclosure-timeline records as
  byte-identical against the shared emitter.
- **EXTEND-docs-cookbook** — cookbook walkthrough (intake an SBOM,
  resolve findings, file a CVD report) under `docs/cookbook/`.
