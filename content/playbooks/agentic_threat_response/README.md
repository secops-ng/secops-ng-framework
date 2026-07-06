# agentic_threat_response

CACAO v2 playbook for detecting and initially responding to fully-
agentic adversary activity — autonomous LLM-driven credential harvest,
lateral movement, and encryption chains observed at machine-speed
decision cadence. The playbook ingests an agentic-threat indicator,
isolates the affected credential set, contains the lateral-movement
path, hands off the case envelope to the incident-management engine
for the regulator-notification chain, and preserves evidence for the
NIS2 Article 23 notification obligation.

## Status

Experimental. Content version `0.3.0`: CACAO workflow shape, real
OSCAL / D3FEND / OCSF identifiers, and KPI hooks are wired end-to-end
against the shipped `content/metrics/` catalogue and
`content/telemetry/` OCSF class artifacts. Byte-parity goldens for
the n8n / Temporal / LangGraph compile targets live under
`examples/{n8n,temporal,langgraph}/agentic_threat_response/`.

## Motivation

Static SOAR playbooks are miscalibrated for the machine-speed
adversary decision cadence documented in the first wave of
fully-agentic operations (autonomous credential harvest, lateral
movement, and encryption chain with no human-in-loop; sub-minute
self-correction fingerprints). This scaffold closes the content-
coverage gap under NIS2 Article 21(2)(b) (incident-handling capability)
and Article 21(2)(e) (security in acquisition, development and
maintenance — including agentic-tool supply-chain surface) for the
top-5 NIS2 Article 21 control family set.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.agentic_threat_response@v1`).
- `mappings.yaml` — SKELETON outbound overlay. NIS2 Art. 21(2)(b) and
  Art. 21(2)(e) inbound edges are wired; CRA / DORA / GDPR inbound
  edges are deferred to sibling CORE / EXTEND cards and recorded on
  the respective `_orphan_skip.yaml` manifests so orphan-CI stays
  green. Schema:
  `../../../schemas/playbook-mappings.schema.json`.

## Workflow

1. **Ingest agentic-threat indicator** — receive the indicator (anomalous
   LLM API call volume, rapid credential-enumeration burst, lateral
   movement inside the observed self-correction window) and hydrate it
   with originating principal, source / destination context, and
   observed cadence.
2. **Isolate affected credential set** — revoke sessions, refresh and
   access tokens for the implicated principal at the IdP, disable the
   principal for the containment window, and alert the IAM auditor
   lane for the parallel scope audit and forced-rotation follow-on.
3. **Contain lateral-movement path** — apply a network micro-
   segmentation call along the resolved lateral edge so the operator
   cannot pivot off the implicated path during the containment window.
4. **Escalate to incident-management** — hand off the case envelope to
   `playbook.incident_management@v1` as the upstream-playbook intake
   so the NIS2 Article 23 early-warning and 72-hour notification chain
   is dispatched by the incident-management engine.
5. **Preserve evidence for notification chain** — persist LLM API call
   logs, the credential-enumeration timeline, the lateral-movement
   graph, and the containment-action ledger as an evidence bundle
   consumed by the downstream regulator-submission engine.

## Regulatory anchors (SKELETON)

- **NIS2 Article 21(2)(b)** — incident-handling capability. Inbound
  edge on `content/mappings/nis2/article-21-2-b.yaml` under
  `nis2:art-21-2-b`.
- **NIS2 Article 21(2)(e)** — security in acquisition, development and
  maintenance, including the agentic-tool supply-chain surface.
  Inbound edge on `content/mappings/nis2/article-21-2-e.yaml` under
  `nis2:art-21-2-e`.
- **NIS2 Article 23** — significant-incident notification. Dispatched
  by the downstream `playbook.incident_management@v1` engine from the
  case envelope this playbook hands off.

## Out of scope (this playbook)

- The DORA cross-regime inbound edge is deferred until the JC RTS on
  ICT risk management framework (Commission Delegated Regulation (EU)
  2024/1774) coverage is extended to the agentic-tradecraft indicator
  class. Skip entry lives at
  `content/mappings/dora/_orphan_skip.yaml`.
- The CRA cross-regime inbound edge is deferred pending a documented
  product-security interaction. Skip entry lives at
  `content/mappings/cra/_orphan_skip.yaml`.
- The GDPR data-flow surface (Article 30 RoPA) for this playbook is
  deferred to a follow-on card that authors
  `content/mappings/gdpr/data-flow-agentic_threat_response.md`. Skip
  entry lives at `content/mappings/gdpr/_orphan_skip.yaml`.

## Sources

- OASIS CACAO v2.0 specification.
- NIS2 Directive (EU) 2022/2555 — Articles 21(2)(b), 21(2)(e), 23.
- ENISA — Threat Landscape reporting on autonomous / agentic
  adversary tradecraft.
