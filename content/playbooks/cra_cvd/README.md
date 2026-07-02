# cra_cvd

CACAO v2 SKELETON playbook operationalising the operator-side
**coordinated vulnerability disclosure (CVD)** lifecycle a manufacturer
of a product with digital elements runs when a reporter (security
researcher, downstream operator, finder) submits a vulnerability
report against a shipped product. Covers the triage-to-public-advisory
chain: intake → acknowledgement to the reporter → triage →
develop-fix → validate-fix → coordinate-disclosure → publish-advisory.

Distinct from `playbook.cra_srp_notify@v1`, which covers the
regulator-facing 24h / 72h / 14d-or-1-month timer cascade under CRA
Article 14 §1–§3. The two playbooks compose: when a case at triage is
actively-exploited or classified as a severe incident, this playbook
forks a sibling `cra_srp_notify` run keyed on `__case_id__` and
continues the disclosure lifecycle in parallel.

Status: **SKELETON**. Action steps are scaffolded as CACAO v2 sources
with `control_refs` / `telemetry_refs` / `metric_refs` stubs; the
acknowledgement-letter template, advisory template (including CSAF
2.0 emission), CVE-request adapter, and CSIRT-coordination adapter
are placeholders that a sibling CORE card lands.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.cra_cvd@v1`).
- `mappings.yaml` — outbound cross-references to the OSCAL controls,
  MITRE D3FEND techniques, OCSF event classes, and EU regulatory
  clauses this playbook operationalises. A sibling CORE card lands
  the full mappings overlay; the SKELETON overlay pins the
  regulatory + control surface so the inbound graphs close.

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`.
Emitted artifacts under
`examples/{n8n,temporal,langgraph}/cra_cvd/` land in a follow-on
CORE / EXTEND card once the acknowledgement / advisory templates and
adapters are populated.

## Regulatory anchors

- **Cyber Resilience Act (EU) 2024/2847, Article 14 §1** — obligation
  to operate a coordinated vulnerability disclosure policy for
  products with digital elements the manufacturer places on the
  market.
- **Cyber Resilience Act (EU) 2024/2847, Article 14 §6** —
  acknowledgement of received reports to the reporter within a
  policy-declared window (3 working days on the operator baseline).
- **CRA Article 14 §2 (overlap)** — when triage classifies a case as
  an actively-exploited vulnerability, the sibling `cra_srp_notify`
  playbook runs the 24h / 72h / 14-day submission chain in parallel.
- **NIS2 Article 23(1) (overlap)** — where the vulnerability produces
  a severe incident meeting the NIS2 threshold, the operator's NIS2
  incident-notification chain (through the sibling incident-management
  lane) runs in parallel with the disclosure lifecycle here. This
  SKELETON does not pin an outbound NIS2 mapping; the CORE card
  documents whether an outbound edge or a deliberate deferral is
  correct.
- **GDPR Article 33 (overlap)** — where the vulnerability affects
  personal data, the operator's GDPR breach-notification chain runs
  in parallel. This SKELETON does not pin an outbound GDPR mapping;
  the CORE card documents whether an outbound edge or a deliberate
  deferral is correct.

## Sources

- OASIS CACAO v2.0 specification
- Cyber Resilience Act (EU) 2024/2847, Article 14 §1 and §6
- ISO/IEC 29147:2018 — Vulnerability disclosure
- ISO/IEC 30111:2019 — Vulnerability handling processes
- OCSF v1.3.0 — Vulnerability Finding (class_uid 2002) and
  Compliance Finding (class_uid 2003) event classes
