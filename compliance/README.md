# Compliance Evidence Commons

This directory is where SecOps-NG operators and the wider community collect,
shape, and publish **portable control mappings and evidence** for regulatory
regimes that matter to security workflows running on European sovereign
infrastructure.

The mappings here are OSCAL-aligned and orchestrator-neutral: they describe
which SecOps-NG content artifacts (CACAO playbooks, OCSF event shapes,
KPI/KRI definitions) satisfy which regulatory obligation, independent of
the runtime that ultimately executes the content.

It is not a checklist generator. It is not an audit-as-a-service.
It is a **shared scaffold** that any community member can adopt, fork, and
extend so that two operators running SecOps-NG in two different jurisdictions
can speak the same language to their auditors, supervisory authorities, and
peers.

## Scope

Currently scaffolded:

- `nis2/` — control mapping against the EU NIS2 Directive (Directive
  (EU) 2022/2555), focused on Articles 20–23 which govern governance,
  cybersecurity risk-management measures, reporting obligations, and the use
  of European cybersecurity certification schemes.
- `gdpr/` — data-flow templates aligned to Regulation (EU) 2016/679, covering
  the lawful-basis, retention, and cross-border-transfer questions an operator
  must be able to answer about telemetry that touches personal data.
- `evidence/` — the target directory for **automated evidence drops**
  emitted by SecOps-NG workflows. Human-authored documents live in `nis2/`
  and `gdpr/`; machine-emitted artefacts live in `evidence/`.

## Evidence-collection model

The premise: a durable SecOps workflow already produces, as a side effect of
executing, most of the evidence a regulator or a peer operator would ever
want to see. We just have to **capture it, structure it, and let the
community read it**.

The model has three layers:

1. **Human-authored control mappings** (`nis2/`, `gdpr/`) — markdown
   documents that map each regulatory obligation to one or more SecOps-NG
   capabilities, workflows, or operational practices. These are written by
   humans, reviewed in pull requests, and versioned alongside the code that
   implements them.
2. **Machine-emitted evidence** (`evidence/`) — JSON / NDJSON artefacts
   dropped by workflows at well-defined points (workflow start, tool-call
   boundary, decision point, workflow completion). Each artefact carries a
   pointer back to the control(s) it provides evidence for.
3. **Aggregation and review** — periodic community review of the corpus,
   surfacing gaps where a stated control has no corresponding evidence
   stream, and gaps where evidence is being collected but no control points
   at it.

## Voice

These documents are written for **community operators**, not enterprise
buyers. Compliance here is framed as community-protective: it is how we keep
each other safe, accountable, and welcome in regulated environments. It is
not a sales surface.

When citing legal instruments, cite article and paragraph numbers explicitly.
When making a claim that an operational practice satisfies an obligation,
link to the workflow, contract, or test that backs the claim.

## Status

**Scaffold only.** Coder will wire automated evidence collection into the
Temporal workflows in a subsequent commit. Markers labelled
`<!-- coder:wire -->` indicate the integration points.

## Contributing

Same rules as the rest of the framework: DCO sign-off, conventional
commits, pull requests for review. Compliance-relevant changes should be
flagged in the PR description so the Custodian role can review.

## License

Documentation in this directory is published under the same Apache-2.0
license as the rest of the framework. Where a document quotes regulatory
text directly, that text remains the property of its originating authority
and is reproduced under fair-use / informational exemptions.
