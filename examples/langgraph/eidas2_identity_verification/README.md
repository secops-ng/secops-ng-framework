# examples/langgraph/eidas2_identity_verification

Worked example: the `playbook.eidas2_identity_verification@v1` CACAO
v2 playbook compiled by the LangGraph reference compiler. The
emitter walks the CACAO topology and produces two artifacts:

- `graph_spec.json` — target-neutral immutable description of the
  graph nodes, edges, entry pointer, and finish pointer.
- `state_bindings.py` — generated `TypedDict` state schema and
  `@tool`-decorated stubs for the five CACAO action steps.

Wiring the graph into a live LangGraph runtime, binding the tool
stubs to real primitives, and adding a conditional edge on the
`__verification_verdict__` branch is the operator's job. The
`_audit_mirror.py` sibling is the co-located dependency-free
audit-record helper — see `docs/observability/audit-mirror.md` for
the co-location rationale.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/eidas2_identity_verification/playbook.cacao.json

Regulatory anchors (NIS2 Art. 21(2)(i), DORA Art. 5, eIDAS 2.0) and
OSCAL / D3FEND / OCSF bindings live in the sibling `mappings.yaml`.

## Layout

| Path                   | Source compiler            | Format                |
|------------------------|----------------------------|-----------------------|
| `playbook.cacao.json`  | (input mirror)             | CACAO v2 JSON         |
| `graph_spec.json`      | `compilers.langgraph.emit` | LangGraph GraphSpec   |
| `state_bindings.py`    | `compilers.langgraph.state`| Generated Python stub |
| `_audit_mirror.py`     | `compilers._shared`        | Audit-record helper   |
| `regenerate.sh`        | (tooling)                  | bash script           |

## How to regenerate

From the repository root:

```sh
examples/langgraph/eidas2_identity_verification/regenerate.sh
```

The script mirrors the canonical CACAO source, re-emits the
GraphSpec via `compilers.langgraph.emit`, re-emits the generated
state bindings via `compilers.langgraph.state`, and re-emits the
audit-mirror sibling via `compilers._shared.audit_mirror_cli`.

## Sovereign-stack default

LangGraph is a Python library that runs in the operator's own
runtime; no hosted-SaaS default is assumed. The tool stubs are
expected to bind against the operator's own OpenID4VP verifier and
the EU trust-anchor registry. No non-EU trust anchor, no Microsoft /
Google EUDIW proxy, and no third-party LLM provider is assumed at
this layer.
