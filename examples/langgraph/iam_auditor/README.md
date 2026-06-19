# examples/langgraph/iam_auditor

Worked example: the `playbook.iam_auditor@v1` CACAO v2 playbook
compiled by the LangGraph reference compiler. Integrators who already
run LangGraph can copy `graph_spec.json` and `state_bindings.py` into
their own runtime, wire the `@tool` bodies to real connectors
(identity provider, capability source, evidence sink), and own the
result. `assemble.py` is the hand-written reference that stitches the
emitted artifacts into a `langgraph.graph.StateGraph`.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/iam_auditor/playbook.cacao.json

Scenario, workflow, regulatory anchor (NIS2 Article 21(2)(i)), and the
`x_secops_ng` reference bundles (control / telemetry / metric joins,
F-CP-07 access-evidence stream) are documented in that folder's
`README.md`. This folder holds the emitted artifacts, a co-located
byte-identical copy of the CACAO source for easy diff inspection, the
regeneration scripts, and one representative access-evidence artifact
the F-CP-07 LangGraph node adapter produces at execution time.

## Layout

| Path                                | Source compiler                                          | Format                    |
|-------------------------------------|----------------------------------------------------------|---------------------------|
| `playbook.cacao.json`               | (input mirror)                                           | CACAO v2 JSON             |
| `graph_spec.json`                   | `compilers.langgraph.emit`                               | GraphSpec JSON            |
| `state_bindings.py`                 | `compilers.langgraph.state`                              | Generated TypedDict + tools |
| `assemble.py`                       | (hand-written reference)                                 | Python                    |
| `_audit_mirror.py`                  | `compilers._shared.audit_mirror_cli`                     | Python (dependency-free)  |
| `regenerate.sh`                     | (tooling)                                                | bash script               |
| `regenerate.py`                     | (tooling)                                                | Python script             |
| `evidence/access-evidence.json`     | `compilers.langgraph.evidence.access_node`               | F-CP-07 access record     |

## How to use

1. Copy `graph_spec.json`, `state_bindings.py`, and `_audit_mirror.py`
   into your LangGraph integration package (or import them directly
   if your layout permits).
2. Build the `StateGraph` following the pattern in `assemble.py`: load
   the GraphSpec, pick the generated `TypedDict`, add one node per
   GraphSpec node, set the entry point, add the plain edges and
   conditional-edge routers.
3. Replace each `@tool`-decorated wrapper's `NotImplementedError` body
   with your runtime call (identity provider, capability source,
   evidence sink). The `AGENTIC_HOOK` placeholder is where an
   LLM-driven node slots in if the integrator wants one.

The emitted artifacts are a *snapshot of intent*, not a runnable
playbook. The `@tool` bodies raise `NotImplementedError`; integrators
wire them to their own runtime. Secrets, endpoints, and environment
stay with the operator.

## Regeneration

The LangGraph emitters are deterministic: same input bytes in, same
output bytes out. From the repo root:

    ./examples/langgraph/iam_auditor/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `graph_spec.json`, `state_bindings.py`, and the dependency-
free `_audit_mirror.py` sibling. Equivalent direct invocations:

    PYTHONPATH=. python -m compilers.langgraph.emit  \
        examples/langgraph/iam_auditor/playbook.cacao.json \
        > examples/langgraph/iam_auditor/graph_spec.json

    PYTHONPATH=. python -m compilers.langgraph.state \
        examples/langgraph/iam_auditor/playbook.cacao.json \
        > examples/langgraph/iam_auditor/state_bindings.py

    PYTHONPATH=. python -m compilers._shared.audit_mirror_cli \
        --out examples/langgraph/iam_auditor/_audit_mirror.py

The canonical playbook under
`content/playbooks/iam_auditor/playbook.cacao.json` is the single
source. The byte-parity test under
`tests/examples/langgraph/iam_auditor/test_golden.py` pins the
committed worked example against the emitters so silent drift is
caught at CI.

## Access-evidence artifact (F-CP-07)

The iam_auditor's `emit-access-evidence` state produces one
access-evidence artifact per execution against
`schemas/evidence/access.schema.json`. The committed
`evidence/access-evidence.json` is the byte-stable output of the
LangGraph node adapter
(`compilers.langgraph.evidence.emit_access_artifact_node`) for the
representative typed context pinned in `regenerate.py` — exactly what
an integrator's LangGraph node materialises at runtime.

Regenerate from the repo root:

    PYTHONPATH=. python examples/langgraph/iam_auditor/regenerate.py

The artifact is renamed from the deterministic `<artifact_id>.json`
(SHA-256 of `workflow_id|execution_id|compile_target`) to a stable
human-friendly filename for diffing; the byte-parity test under
`tests/examples/langgraph/iam_auditor/test_golden.py` pins the
access-evidence record against the adapter.

The input typed context is kept aligned with the n8n and Temporal
siblings at `examples/n8n/iam_auditor/regenerate.py` and
`examples/temporal/iam_auditor/regenerate.py`: every anchor
(`workflow_id`, `control_refs`, `regulation_refs`, `capabilities`,
`captured_at`) is identical; only `compile_target` and `execution_id`
differ by design so the per-target adapters land at deterministic but
distinct `artifact_id` values.

## Observability — OTel spans emitted by default

Two span layers are emitted for every action step, matching the other
LangGraph worked examples:

- **Tool span — `tool.<step_id>`.** Each `@tool`-decorated wrapper in
  `state_bindings.py` opens the span around its body, so a span is
  always emitted regardless of whether the integrator binds the tool
  directly or routes through an LLM-driven `ToolNode`.
- **Node span — `node.<step_id>`.** Every node assembled in
  `assemble.py` is wrapped in `node.<step_id>` via the local
  `_wrap_node_span` helper before being handed to
  `StateGraph.add_node`. The node span is the parent of the tool span
  inside it.

Span attributes use the shared `secops_ng.*` keyspace and are stable
across reference compilers. The audit-trail mirror
(`_audit_mirror.py`, dependency-free) appends an `AuditRecord` per
node entry so audit holds even when no OTLP exporter is configured —
useful for sovereign / disconnected deployments.

## What this example does not do

The LangGraph reference compiler translates **structure** and the
**CACAO I/O contract**, not **business logic**. The emitted artifacts
carry the topology of the playbook (nodes, edges, conditional
routers), the per-step `in_args` / `out_args` typing, and the
`x_secops_ng` reference bundles as OTel span attributes. They do not
carry:

- Operator-bound bindings (identity provider, capability source,
  evidence sink).
- Credentials, secrets, or environment-specific endpoints.
- An LLM provider for the agentic-extension hook (`AGENTIC_HOOK` is a
  documented placeholder; the operator chooses a provider that matches
  their sovereignty posture at integration time).
- The F-PT-01 platform-side refuse-at-boot guarantee that the caller
  actually held the listed capabilities — that lives in the platform
  layer; the workflow only carries the assertion shape.

## Sovereign-stack default

The artifact destination is operator-configured. No default non-EU
endpoint. The LangGraph example writes the access-evidence artifact
to a local directory; the operator's runtime is expected to point the
node's `evidence_output_dir` at the volume their chosen evidence sink
ingests from.
