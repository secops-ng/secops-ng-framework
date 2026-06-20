# evidence/

Per-execution interaction-evidence artefact emitted by the n8n
adapter for the IT and security support-agent workflow, shaped against
[`schemas/evidence/incidents.schema.json`](../../../../schemas/evidence/incidents.schema.json)
(reused from F-CP-02).

The committed [`interaction-evidence.json`](interaction-evidence.json)
is the result of one representative execution: an incident-shaped
classification verdict driving the handoff path, so
`classification.significant=true` on the emitted artefact and the
F-CP-02 KPI surface counts the support→incident handoff once on the
same NIS2 Article 21(2)(b) anchor F-WF-05 discharges.

To regenerate after any change to the n8n adapter, the shared
support-agent primitives, or the canonical playbook:

```sh
examples/n8n/it_security_support_agent/regenerate.sh
```

The deterministic `<artifact_id>.json` the adapter writes is dropped
after the copy so the committed tree only carries the human-friendly
artefact.
