# cra_srp_notify

CACAO v2 starter playbook operationalising the Cyber Resilience Act
Article 14 notification cascade for manufacturers of products with
digital elements: a shared 24-hour early-warning / 72-hour full
notification / 14-day-or-1-month final report chain addressed to the
manufacturer's main-establishment CSIRT through the EU Single
Reporting Platform (SRP), with simultaneous availability to ENISA per
Article 14. Fired by a sibling incident-handling or vulnerability-
intake playbook when the operator's classification step trips the
Article 14(2) actively-exploited-vulnerability clock or the Article
14(3) severe-incident clock; this playbook is the shared regulator-
notification chain those upstream playbooks hand off to.

Status: SKELETON. The SRP intake schema is not yet public (the
Commission's CRA reporting page notes a pre-go-live testing period
ahead of 11 September 2026). The workflow expresses the 24h / 72h /
14d-or-30d clock cascade as first-class CACAO parallel and delay
steps so any reference compile target can carry the clocks as
durable state; the submission-body shape is a placeholder until the
SRP schema is published, at which point a sibling CORE card lands
the schema-conformant payload builder.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.cra_srp_notify@v1`).
- `mappings.yaml` — outbound cross-references to the OSCAL controls,
  MITRE D3FEND techniques, OCSF event classes, and EU regulatory
  clauses this playbook operationalises. The inbound CRA entries live
  at `content/mappings/cra/article-14-and-annex-i.yaml`.

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`.
Emitted artifacts under
`examples/{n8n,temporal,langgraph}/cra_srp_notify/` carry the
durable-timer scaffolding for the three clock legs on each reference
runtime.

## Regulatory anchors

- **Cyber Resilience Act (EU) 2024/2847, Article 14** — manufacturer
  reporting obligations: 24-hour early warning, 72-hour full
  notification, 14-day final report for actively-exploited
  vulnerabilities under Art. 14(2), 1-month final report for severe
  incidents under Art. 14(3).
- **CRA Annex I §2** — essential cybersecurity requirements the
  reporting chain evidences (vulnerability-handling process,
  coordinated disclosure, security-update dissemination).
- **European Commission — CRA reporting obligations** — the Single
  Reporting Platform address surface, applicable 11 September 2026.

## Sources

- OASIS CACAO v2.0 specification
- Cyber Resilience Act (EU) 2024/2847, Article 14 and Annex I §2
- European Commission — CRA reporting obligations
  (https://digital-strategy.ec.europa.eu/en/policies/cra-reporting)
- ENISA — Threat Landscape and Good Practices for Incident
  Notification
- OCSF v1.3.0 — Compliance Finding (2003) event class
