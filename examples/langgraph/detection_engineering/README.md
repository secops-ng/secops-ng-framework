# examples/langgraph/detection_engineering

Worked example: the `playbook.detection_engineering@v1` CACAO v2
playbook compiled by the **LangGraph** reference compiler. The emitted
artifacts (target-neutral `graph_spec.json`, generated
`state_bindings.py`, and the hand-written `assemble.py`) are enough for
an integrator to assemble a `langgraph.graph.StateGraph` and see the
topology the emitter produces; wiring the placeholder `@tool` bodies to
real connectors (detection-store proposal intake, peer-review system,
the operator's production detection-store promotion endpoint, and the
metric sink that ingests the per-rule-version effectiveness snapshot)
is the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/detection_engineering/playbook.cacao.yaml

The four-state lifecycle (propose → review → ship → measure), the
NIS2 Article 21(2)(f) regulatory anchor, the OCSF Detection Finding
binding, and the indicator catalogue references the `measure` state
emits against are documented in that folder's `README.md`. This
directory holds the emitted GraphSpec + state bindings, the
hand-written reference assembly, the regeneration scripts, and the
per-rule-version effectiveness-snapshot artifact the LangGraph node
adapter at `compilers/langgraph/evidence/rule_effectiveness_node.py`
produces from the `measure` state's payload.

## Layout

| Path                                          | Source                                  | Format                       |
|-----------------------------------------------|-----------------------------------------|------------------------------|
| `playbook.cacao.json`                         | (mirror of canonical YAML)              | CACAO v2 JSON                |
| `graph_spec.json`                             | `compilers.langgraph.emit`              | target-neutral GraphSpec     |
| `state_bindings.py`                           | `compilers.langgraph.state`             | generated TypedDict + tools  |
| `assemble.py`                                 | hand-written reference                  | LangGraph `StateGraph` glue  |
| `_audit_mirror.py`                            | `compilers._shared.audit_mirror_cli`    | in-band audit-trail mirror   |
| `regenerate.sh`                               | (tooling — regenerates the workflow)    | bash script                  |
| `evidence/rule-effectiveness-snapshot.json`   | `compilers.langgraph.evidence`          | snapshot JSON                |
| `regenerate.py`                               | (tooling — regenerates the snapshot)    | python script                |

## How to assemble

1. Treat `graph_spec.json` as the topology contract — pure JSON, no
   runtime dependency. `assemble.py` shows the ~10-line pattern: load
   the GraphSpec, pick the generated `TypedDict` off
   `state_bindings`, walk `nodes` / `edges` / `conditional_edges`,
   then call `graph.compile()`.
2. Each `@tool`-decorated wrapper in `state_bindings.py` raises
   `NotImplementedError` by default; wire each one to your operator-side
   connector before invoking the graph. The detection_engineering
   playbook is a linear lifecycle (propose → review → ship → measure)
   with no CACAO branching in this artifact, so the conditional-edge
   router pattern stays empty here for parity with the sibling
   assemblies; the F-WF-04 EXTEND sibling slots a verdict-keyed router
   into the same shape.

The emitted artifacts are a *snapshot of intent*, not a runnable
playbook. Each tool wrapper carries the CACAO I/O contract
(`in_args` / `out_args`) in its typed signature; binding those to
real connectors is the operator's job. The `measure` state's output
is shaped per
`schemas/evidence/rule-effectiveness-snapshot.schema.json`; the
worked-example snapshot at `evidence/rule-effectiveness-snapshot.json`
shows the on-disk bytes the LangGraph node adapter writes for one
representative rule version.

## Observability

The emitter wraps every `@tool` body in an OpenTelemetry
`tool.<step_id>` span carrying stable `secops_ng.*` attributes
(playbook id, step id, step name, tool function name, workflow run-id
placeholder) and a parallel `AuditTrail.append` mirror written through
the co-located `_audit_mirror.py` sibling. The audit-trail mirror
records the same event in-band so audit holds even when no OTel
exporter is configured (F-CR-04 contract) — typical for disconnected,
sovereign, or air-gapped deployments where OTLP egress is unavailable.
See [../../../docs/observability/audit-mirror.md](../../../docs/observability/audit-mirror.md)
for the co-location decision, the JSONL replay envelope, and the
snapshot API used to drain a trail offline. Span names + attributes
match the n8n and Temporal compile targets so an OTel consumer sees
structurally compatible telemetry across all three reference compilers.

## Sovereign-stack constraint

Metric storage is operator-configured. The framework ships **no**
hosted-SaaS default endpoint for the effectiveness snapshot; the
operator's runtime is expected to point the node adapter's
`evidence_output_dir` at the volume their chosen metric sink ingests
from. LangGraph is open source (MIT) and runs as a Python process:
hosting it on EU sovereign infrastructure (Nebul, OVHcloud, Scaleway,
Hetzner) is a deployment choice, not a vendor decision.

## Regeneration

The LangGraph emitter is deterministic: same input bytes in, same
output bytes out. From the repo root:

    ./examples/langgraph/detection_engineering/regenerate.sh

regenerates `playbook.cacao.json`, `graph_spec.json`,
`state_bindings.py`, and `_audit_mirror.py` from the canonical CACAO
source. The per-rule-version effectiveness-snapshot artifact under
`evidence/` is regenerated separately by the sibling Python script:

    PYTHONPATH=. python examples/langgraph/detection_engineering/regenerate.py

The committed snapshot is byte-identical to the n8n sibling at
`../../n8n/detection_engineering/evidence/rule-effectiveness-snapshot.json`
and the Temporal sibling at
`../../temporal/detection_engineering/evidence/rule-effectiveness-snapshot.json`
— the per-target adapters are thin glue over a shared emitter, so any
drift between the three is a bug in one of the adapters.

## Pending follow-up work

Gating predicates on the `review → ship` and `ship → measure`
transitions, the full cross-target byte-parity goldens covering all
four lifecycle states, and the cookbook walkthrough land in follow-up
sibling cards tracked in `ROADMAP.md` § F-WF-04.
