# ddos_response

CACAO v2 SKELETON playbook for the incident-handling capability on the
availability/denial-of-service attack dimension: detect availability
anomaly → classify attack vector → engage mitigation (upstream
scrubbing / rate-limit / failover) → validate service restoration →
capture dated evidence → notify incident-management owner. Operates
the per-event response against the operator's pre-bound mitigation
surface; it does not author the operator's anti-DDoS architecture.

## Status

SKELETON. The playbook artifact and the NIS2 Art. 21(2)(b)
incident-handling overlay land here; CORE-layer cards add the
detection bindings (mitigation-surface misconfiguration signals)
together with their D3FEND pins, and the per-target compiler
emissions (n8n / Temporal / LangGraph goldens); an EXTEND card wires
the time-to-mitigation and availability-restoration metric emitters
against the operator's evidence store. DORA Art. 11 and CRA Annex I
§1(h) availability-response inbound entries are deliberately deferred
to separate inbound-closure cards (see the gap notes in
`mappings.yaml` and the audited skip entries under
`content/mappings/dora/_orphan_skip.yaml` and
`content/mappings/cra/_orphan_skip.yaml`).

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.ddos_response@v1`).
- `mappings.yaml` — outbound overlay (OSCAL controls, OCSF telemetry,
  NIS2 Art. 21(2)(b)).

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. Emitted
artifacts and golden tests are owned by CORE-layer sibling cards; this
directory ships the portable content only.
