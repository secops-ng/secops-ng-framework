# ddos_response

CACAO v2 playbook for the incident-handling capability on the
availability/denial-of-service attack dimension: detect availability
anomaly → classify attack vector → engage mitigation (upstream
scrubbing / rate-limit / failover) → validate service restoration →
capture dated evidence → notify incident-management owner. Operates
the per-event response against the operator's pre-bound mitigation
surface; it does not author the operator's anti-DDoS architecture.

## Status

Stable — `content_version` 1.0.0 under the Maturity ladder. All six
action steps carry `x_secops_ng.core_body` bindings into the
deterministic primitives under `primitives/`
(`detect.resolve_availability_trigger`,
`classify.classify_attack_vector`,
`mitigation.select_mitigation_engagement`,
`restoration.evaluate_service_restoration`,
`evidence.compose_incident_evidence_record`,
`notify.compose_owner_notification`), each executed directly by the
unit suite under `tests/playbooks/ddos_response/`. The three worked
examples under `examples/{n8n,temporal,langgraph}/ddos_response/` are
regenerated from the bound source: n8n emits six Code nodes, and the
Temporal activities and LangGraph tools import their primitives, with
`NotImplementedError` marking only the operator-integration seams
(monitoring ingress, the response surface, the evidence store, the
owner channel). The NIS2 Art. 21(2)(b) outbound overlay and the DORA
Art. 11 inbound anchor
(`content/mappings/dora/article-11-availability-response.yaml`) cite
the playbook; the CRA Annex I §1(h) inbound entry remains an audited
skip under `content/mappings/cra/_orphan_skip.yaml`. Still open, and
recorded as such: the detection bindings for mitigation-surface
misconfiguration (scrubber not engaged, rate-limit pushed to the wrong
zone, unhealthy standby) wait on upstream rule ids from the operator's
posture-management layer, and the time-to-mitigation /
availability-restoration metric emitters remain a separate
metrics-layer card — the steps carry no `metric_refs` until that
catalogue entry lands.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.ddos_response@v1`).
- `mappings.yaml` — outbound overlay (OSCAL controls, OCSF telemetry,
  NIS2 Art. 21(2)(b)).
- `primitives/` — the six deterministic primitives the action steps
  bind: pure, offline, LLM-free. Mitigation is an adapter-bound
  operator surface — the framework ships the hand-off and no
  scrubbing-provider binding; restoration is verified against
  observed traffic, never asserted on the mitigation having been
  applied.

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. The
emitted artifacts live under `examples/{n8n,temporal,langgraph}/ddos_response/`
with byte-parity goldens under `tests/examples/`, regenerated from
the bound canonical source via each directory's `regenerate.sh`.
