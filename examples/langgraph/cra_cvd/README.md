# cra_cvd — LangGraph worked example

Worked example: the `playbook.cra_cvd@v1` CACAO v2 playbook compiled by
the SecOps-NG LangGraph reference compiler. Operators who already run
LangGraph can import `assemble.build_graph()` to see the `StateGraph`
topology the emitter produces; binding the tool bodies to real
connectors (reporter channel, CVE-request adapter, CSIRT-coordination
adapter, PGP-signed delivery, and the evidence store) is the operator's
job.

This worked example is the LangGraph leg of the three-target parity
lane for the `cra_cvd` playbook. Sibling n8n and Temporal examples ship
alongside under `../../n8n/cra_cvd/` and `../../temporal/cra_cvd/`.

## Source

Canonical CACAO playbook:
`../../../content/playbooks/cra_cvd/playbook.cacao.json`. That folder
documents the regulatory anchors (CRA Article 14 §1 CVD policy and §6
acknowledgement window) and the linear seven-step disclosure lifecycle
from intake through published advisory.

## Files in this directory

| Path                  | Source compiler                         | Format                 |
|-----------------------|-----------------------------------------|------------------------|
| `playbook.cacao.json` | (input mirror)                          | CACAO v2 JSON          |
| `graph_spec.json`     | `compilers.langgraph.emit`              | GraphSpec JSON         |
| `state_bindings.py`   | `compilers.langgraph.state`             | Python state module    |
| `_audit_mirror.py`    | `compilers._shared.audit_mirror_cli`    | Python audit mirror    |
| `assemble.py`         | (hand-written, see below)               | Python assembly        |
| `regenerate.sh`       | (tooling)                               | bash script            |
| `README.md`           | —                                       | This file.             |

`assemble.py` is hand-written and intentionally so — the framework does
not ship a runtime `langgraph.graph.StateGraph` builder because
LangGraph is one of three compile targets, not the engine. Integrators
copy the assembly into their own runtime.

## How to run

```python
from assemble import build_graph  # rename to your import path

graph = build_graph()
result = graph.invoke({"__case_id__": "...", "__reporter_contact__": "..."})
```

The state bindings surface each CACAO variable as a typed field on the
`State` TypedDict. `langgraph` is imported lazily inside `build_graph()`
so the module lints and is collectable by the example smoke test
without `langgraph` installed.

## How to regenerate

The LangGraph emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/langgraph/cra_cvd/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `graph_spec.json` + `state_bindings.py` via
`compilers.langgraph.emit` and `compilers.langgraph.state`. The
`_audit_mirror.py` sibling is regenerated via
`compilers._shared.audit_mirror_cli`.

The drift guard in `tests/examples/cra_cvd/test_golden.py` fails the
suite if `graph_spec.json` diverges from a fresh regeneration.

## Topology

CACAO `start` / `end` sentinels elide into GraphSpec `entry` + `__END__`
edges. Seven action nodes remain, chained linearly:

- `entry` = `intake`.
- `intake` → `ack_to_reporter` → `triage` → `develop_fix` →
  `validate_fix` → `coordinate_disclosure` → `publish_advisory` →
  `__END__`.

Every edge is a plain successor edge; the playbook has no
`if-condition` steps and no `parallel` fan-out (the disclosure chain is
sequential by design — each step's output feeds the next). Conditional
branching lands in a future EXTEND card if the operator community wants
a re-triage or CSIRT-hold-cleared decision point exposed as a first-
class node.

## Where the reporter-communications and adapter TODOs live

Three of the seven nodes (`ack_to_reporter`, `coordinate_disclosure`,
`publish_advisory`) are adapter-bound. The generated `state_bindings.py`
tool stubs raise `NotImplementedError`; the operator wires them to:

- **Reporter channel** — outbound mail or PGP-signed delivery
  (`patterns.cra_cvd.PGPDeliveryRequest`).
- **CVE-request adapter** — CNA request; the reference contract lives
  at `patterns.cra_cvd.CVERequest` / `CVERequestResponse`.
- **CSIRT-coordination adapter** — for cases requiring national CSIRT
  coordination; contract at `patterns.cra_cvd.CSIRTCoordinationRequest`.

## What this example deliberately doesn't do

- It does not execute the graph. Tool stubs raise `NotImplementedError`
  — the operator implements the reporter channel and the three adapter
  surfaces.
- It does not ship CNA API tokens, CSIRT-coordination endpoints, or
  PGP secret keys.
- It does not select a CVE numbering authority or a national CSIRT —
  those are operator policy decisions.

## Status

CORE-PRIM — the LangGraph artifact ships byte-deterministic from the
canonical CACAO source. Adapter wiring stays operator-owned; the CORE
siblings have all landed and this three-target example closes the
G-03 byte-parity gap.

## Sovereignty note

The artifacts emitted here are a description of what the operator's own
LangGraph runtime should do. No telemetry flows to this repository or
to the SecOps-NG project. LangGraph is open source (MIT); running it on
EU sovereign infrastructure (Nebul, OVHcloud, Scaleway, Hetzner) is a
deployment choice the operator owns.
