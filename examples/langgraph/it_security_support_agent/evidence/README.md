# evidence/

Per-execution interaction-evidence artefact emitted by the LangGraph
node adapter for the IT and security support-agent workflow, shaped
against
[`schemas/evidence/incidents.schema.json`](../../../../schemas/evidence/incidents.schema.json)
(reused from F-CP-02).

The committed [`interaction-evidence.json`](interaction-evidence.json)
is the result of one representative execution: an incident-shaped
classification verdict driving the handoff path, so
`classification.significant=true` on the emitted artefact and the
F-CP-02 KPI surface counts the support→incident handoff once on the
same NIS2 Article 21(2)(b) anchor F-WF-05 discharges.

The LangGraph node adapter at
[`compilers/langgraph/evidence/interaction_evidence_node.py`](../../../../compilers/langgraph/evidence/interaction_evidence_node.py)
delegates to the workflow-local primitive
`content.playbooks.it_security_support_agent.primitives.artifact.build_interaction_artifact`
— the same primitive the n8n adapter and the Temporal activity use —
so the per-target byte-parity CORE invariant holds: the bytes here are
byte-identical to the n8n sibling at
[`examples/n8n/it_security_support_agent/evidence/interaction-evidence.json`](../../../n8n/it_security_support_agent/evidence/interaction-evidence.json)
and the Temporal sibling at
[`examples/temporal/it_security_support_agent/evidence/interaction-evidence.json`](../../../temporal/it_security_support_agent/evidence/interaction-evidence.json)
for the same canonical payload.

To regenerate after any change to the LangGraph node adapter, the
shared support-agent primitives, or the canonical playbook:

```sh
examples/langgraph/it_security_support_agent/regenerate.sh
```

The deterministic `<artifact_id>.json` the node writes is dropped
after the copy so the committed tree only carries the human-friendly
artefact.
