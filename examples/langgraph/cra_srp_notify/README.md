# cra_srp_notify — LangGraph worked example

Worked example: the `playbook.cra_srp_notify@v1` CACAO v2 playbook
compiled by the SecOps-NG LangGraph reference compiler. Operators who
already run LangGraph can import `assemble.build_graph()` to see the
`StateGraph` topology the emitter produces; binding the tool bodies to
real connectors (SRP intake, ENISA availability, evidence store) is the
operator's job.

This worked example is the LangGraph leg of the three-target parity
lane for the `cra_srp_notify` playbook (CRA Art.14 SRP notification
cascade). Sibling n8n and Temporal examples ship alongside under
`../../n8n/cra_srp_notify/` and `../../temporal/cra_srp_notify/`.

## Source

Canonical CACAO playbook:
`../../../content/playbooks/cra_srp_notify/playbook.cacao.json`. That
folder documents the regulatory anchors, the awareness-anchored 24h /
72h / 14d-or-30d timer cascade, and the CACAO `parallel` step that
fans the 72h and final-report clocks out from a single awareness
timestamp.

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
result = graph.invoke({"__case_id__": "...", "__clock_kind__": "actively_exploited_vulnerability",
                       "__awareness_ts__": "2026-09-01T09:00:00Z"})
```

The state bindings surface each CACAO variable as a typed field on the
`State` TypedDict. `langgraph` is imported lazily inside
`build_graph()` so the module lints and is collectable by the example
smoke test without `langgraph` installed.

## How to regenerate

The LangGraph emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/langgraph/cra_srp_notify/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `graph_spec.json` + `state_bindings.py` via
`compilers.langgraph.emit` and `compilers.langgraph.state`. The
`_audit_mirror.py` sibling is regenerated via
`compilers._shared.audit_mirror_cli`.

The drift guard in `tests/examples/cra_srp_notify/test_golden.py` fails
the suite if `graph_spec.json` diverges from a fresh regeneration.

## Topology

CACAO `start` / `end` sentinels elide into GraphSpec `entry` +
`__END__` edges. Five nodes remain (three action steps, one parallel
fan-out, plus the two durable-delay action steps), wired as:

- `entry` = `early_warning` (24h).
- `early_warning` → `parallel` step (fan-out).
- `parallel` branches into `wait_until_72h_deadline` and
  `wait_until_final_report_deadline` — both anchored on the same
  `__awareness_ts__`, not on each other.
- `wait_until_72h_deadline` → `full_notification` → `__END__`.
- `wait_until_final_report_deadline` → `final_report` → `__END__`.

The durable delays are expressed as LangGraph nodes whose body is
"interrupt-then-resume-at-timestamp" — the integrator adapts the wait
mechanism to their runtime (checkpointer-backed interrupts, external
scheduler callback, or a persistence layer that survives worker
restart). The GraphSpec is the intent; the wait mechanism is the seam.

## Where the SRP schema TODO lives

Each submission node's `state_bindings.py` docstring carries a `TODO
(CORE)` marker mirroring the canonical CACAO source: the SRP intake
schema is not yet public (Commission page notes a pre-go-live testing
period ahead of 11 September 2026). The generated tool stubs raise
`NotImplementedError`; the operator wires the SRP payload once the
schema is published.

## What this example deliberately doesn't do

- It does not execute the graph. Tool stubs raise `NotImplementedError`
  — the operator implements SRP intake, ENISA availability, and the
  awareness-anchored wait mechanism.
- It does not ship the SRP submission payload shape.
- It does not ship operator credentials or environment-specific
  endpoints.

## Status

CORE — the LangGraph artifact ships byte-deterministic from the
canonical CACAO source. Submission-body wiring waits on the SRP schema
publication; the EXTEND sibling deepens mappings and adds the cookbook
entry.

## Sovereignty note

The artifacts emitted here are a description of what the operator's own
LangGraph runtime should do. No telemetry flows to this repository or
to the SecOps-NG project. LangGraph is open source (MIT); running it on
EU sovereign infrastructure (Nebul, OVHcloud, Scaleway, Hetzner) is a
deployment choice the operator owns.
