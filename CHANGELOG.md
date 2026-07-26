# Changelog

All notable changes to the SecOps-NG framework are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] — 2026-07-24

First tagged release. Everything below has been on `main` and covered by
CI since the initial content waves; this entry gives operators a version
they can pin and contributors a reference point to work against. The
`0.x` series signals that content stable IDs are settled while the
schema surface may still move before `1.0.0`.

### Added

- **Playbooks** — 45 canonical CACAO v2 playbooks under
  `content/playbooks/`, spanning operational lifecycles (vulnerability
  triage, alert triage, incident management, detection engineering, IAM
  audit, on/offboarding, supply-chain security, patch and asset
  management, network-boundary reconciliation) and regulation-shaped
  lifecycles (DORA Art. 19 major-incident reporting and Chapter V
  third-party risk, CRA Art. 14 SRP notification and coordinated
  vulnerability disclosure, GDPR Art. 35 DPIA and data-subject rights,
  NIS2 Art. 20 governance and Art. 21 self-assessment, EU AI Act Art. 9
  risk management, eIDAS 2.0 identity verification).
- **Reference compilers** — n8n, Temporal and LangGraph emitters reading
  the same CACAO source, with worked examples under
  `examples/{n8n,temporal,langgraph}/` and byte-parity golden tests
  pinning cross-target determinism on every pull request.
- **Regulatory mappings** — nine crosswalk axes under
  `content/mappings/`: NIS2, DORA, CRA, GDPR, EU AI Act, ISO/IEC 27001
  Annex A, NIST CSF 2.0, SOC 2 Trust Services Criteria and MITRE
  D3FEND. Includes OSCAL component definitions for the DORA, CRA, GDPR
  and EU AI Act obligation sets, with per-obligation D3FEND technique
  anchors.
- **Metrics catalogue** — 138 KPI/KRI definitions under
  `content/metrics/`, each carrying thresholds, an OCSF source-data
  binding and a committed reference visualisation. Covers the
  regulator-notification latency families for CRA, DORA, NIS2, GDPR and
  the EU AI Act, plus detection, remediation, coverage and availability
  clusters.
- **Compliance evidence pipeline** — evidence streams for risk analysis,
  incidents, supply chain, vulnerabilities, crypto attestation, control
  effectiveness and access, each with a record schema and per-target
  emitters.
- **Controls and telemetry** — 41 control definitions under
  `content/controls/` and 12 OCSF telemetry class bindings under
  `content/telemetry/`.
- **Patterns** — reusable evidence-collector and incident-timeline
  spines under `patterns/`.
- **Cookbook** — 51 practitioner walkthroughs under `docs/cookbook/`,
  one per shipped playbook plus the regulatory-crosswalk entries.
- **Sovereign defaults** — an EU-resident inference-endpoint guard in the
  shared compiler layer, and OpenTelemetry instrumentation with an
  OTel-free audit-trail mirror emitted by every reference compiler.
- **Community substrate** — Code of Conduct, consent-based
  `GOVERNANCE.md`, a contribution guide with DCO sign-off, the playbook
  authoring quickstart, the `content/playbooks/_template/` scaffold and
  a pull-request template.
- **CI** — hygiene linter, orphan-CI regulatory-coverage matrix,
  three-target byte-parity matrix, GDPR lawful-basis guard,
  playbook-template conformance lint, quickstart gate and USED-BY link
  check, over a 469-file test suite.

### Notes

- Content stable IDs (`playbook.*@v1`, `control.*@v1`, `kpi.*@v1`,
  `kri.*@v1`, `telemetry.ocsf.*@v1`) are the compatibility surface and
  will not change within `0.x` without a changelog entry.
- The framework ships no runtime, agent framework or SOAR. n8n, Temporal
  and LangGraph are three reference compile targets, not the engine.
- Earlier `[Unreleased]` entries covering the DORA and CRA OSCAL
  component-definition layers are folded into the regulatory-mappings
  item above; per-article detail lives in `content/mappings/*/README.md`.

[Unreleased]: https://github.com/secops-ng/secops-ng-framework/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/secops-ng/secops-ng-framework/releases/tag/v0.1.0
