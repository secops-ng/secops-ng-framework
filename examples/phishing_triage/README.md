# examples/phishing_triage

Worked example: the `playbook.phishing_triage@v1` CACAO v2 playbook
compiled by the three reference compilers shipped in this repo.

The intent is to make the compile path observable end-to-end:
operators can read the source CACAO playbook, the emitted artifact for
the orchestrator they actually run, and the regeneration command — all
in one folder.

## Source

Canonical CACAO playbook:

    ../../content/playbooks/phishing_triage/playbook.cacao.json

Scenario, workflow, regulatory anchors, and the operator-supplied
bindings are documented in that folder's `README.md`. This folder
holds only the *emitted* artifacts and the commands used to produce
them.

## Layout

| Path                          | Source compiler                  | Format                |
|-------------------------------|----------------------------------|-----------------------|
| `n8n/workflow.json`           | `compilers.n8n`                  | n8n workflow JSON     |
| `temporal/workflow.py`        | `compilers.temporal`             | Python (Temporal SDK) |
| `langgraph/graph_spec.json`   | `compilers.langgraph.emit`       | LangGraph graph spec  |

The Temporal and LangGraph emitters target the durable-code and
agentic-graph runtimes respectively. n8n is the no-code surface for
operators who run the no-code stack. The same CACAO source compiles
to all three — that is the whole point of the framework.

## Regeneration

All three emitters are deterministic: same input bytes in, same output
bytes out. To regenerate this folder from a clean checkout:

    PB=content/playbooks/phishing_triage/playbook.cacao.json

    PYTHONPATH=. python -m tools.compile "$PB" \
        --target n8n \
        --out examples/phishing_triage/n8n/workflow.json

    PYTHONPATH=. python -m compilers.temporal "$PB" \
        --out examples/phishing_triage/temporal/workflow.py

    PYTHONPATH=. python -m compilers.langgraph.emit "$PB" \
        > examples/phishing_triage/langgraph/graph_spec.json

Re-running each command yields byte-identical output. The
`tests/examples/phishing_triage/test_golden.py` suite pins this
invariant so accidental drift surfaces in review, not in an operator's
runtime.

## What the emitters do not do

The reference compilers translate **structure**, not **business
logic**. Each emitted artifact carries the topology of the playbook
(steps, transitions, conditional routing) plus the lossy-translation
notes recorded by the compiler. They do *not* carry:

- Operator-bound bindings (email-security platform, URL reputation
  source, attachment analyser, intent classifier, paging gateway).
- Credentials, secrets, or environment-specific endpoints.
- Detection logic — Sigma rule references are pinned upstream; no
  Sigma rules are authored in this repo.

Where a CACAO step expresses intent the target runtime cannot
encode (an `action` with no machine-readable `commands`, a switch with
no machine-readable `cases` expression, etc.), the emitter inserts an
explicit placeholder and records the gap in the artifact's
`secops_ng_notes` (n8n), workflow-level docstring (Temporal), or
ancillary state-binding module (LangGraph) so a human integrator sees
exactly what they still need to wire.

## Sovereignty note

The artifacts emitted here are descriptions of what the operator's
own runtime should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG
project. The operator runs the orchestrator on infrastructure they
control — we ship the structure, they own the data plane.
