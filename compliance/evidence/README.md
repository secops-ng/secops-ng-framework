# Evidence Drop Directory

This is the **target directory for automated evidence drops** emitted by
SecOps-NG workflows. Human-authored documents live in `../nis2/` and
`../gdpr/`; machine-emitted artefacts live here.

## Structure (planned)

```
evidence/
├── governance/
│   └── approvals/                 # Article 20 — management-body approvals
├── risk-analysis/                 # Article 21(2)(a) — policy outputs
├── incidents/
│   └── <workflow-id>/
│       ├── awareness.json         # Article 23(4)(a) — the 24-hour anchor
│       ├── early-warning.json     # Article 23(4)(a)
│       ├── notification.json      # Article 23(4)(b)
│       └── final-report.json      # Article 23(4)(d)
├── vulns/                         # Article 21(2)(e) — triage decisions
├── supply-chain/                  # Article 21(2)(d), Article 22
├── crypto/                        # Article 21(2)(h)
├── access/                        # Article 21(2)(i)
└── effectiveness/                 # Article 21(2)(f)
```

## Contract

Every evidence artefact emitted to this directory **must**:

1. Be JSON or NDJSON (machine-readable, line-oriented where appropriate).
2. Carry an `evidence_kind` field naming which control article it provides
   evidence for, e.g. `"nis2:23:4:a"` or `"gdpr:30:1:c"`.
3. Carry a `workflow_id` and a `workflow_run_id` field linking back to the
   Temporal execution that produced it.
4. Carry an `emitted_at` ISO-8601 UTC timestamp.
5. Carry a `schema_version` so the contract can evolve safely.

## What goes here vs. what does not

**Goes here:** machine-emitted artefacts that are intended to be reviewed
in aggregate by humans (operator, supervisory authority, peer operator).

**Does not go here:**

- Raw alert payloads or raw telemetry. Those are workflow state, not
  evidence-of-compliance.
- Personal data in identifiable form. Pseudonymise before emission. The
  framework's pseudonymisation tooling will land alongside the emitters.
- Operator secrets. If a secret shows up in this directory the workflow
  is misconfigured; treat as an incident.

## Retention

Operator-configurable. Default retention rationale lives in
`../gdpr/data-flow-template.md` section 5. The Coder role will surface the
default as a typed config field.

<!-- coder:wire — the `secops_ng.evidence` module owns emission. Tests
     should assert the five required fields above on every emitted
     artefact. -->

## Why this directory is empty

It is intentionally empty in the scaffold commit. Evidence is produced at
runtime by workflow execution. A repository checkout should not contain
evidence from a previous operator's runs.
