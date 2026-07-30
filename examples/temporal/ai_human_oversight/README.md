# examples/temporal/ai_human_oversight

Worked example: the `playbook.ai_human_oversight@v1` CACAO v2 playbook
compiled by the Temporal reference compiler. Operators who already run
Temporal can import `workflow.temporal.py` into their worker module to
see the topology the emitter produces; binding the activity bodies to
real connectors (oversight roster, briefing record, the flagged-decision
queue, the intervention log, the evidence store) is the operator's job.

This is the *exercise* half of EU AI Act human oversight — Art. 14. Its
sibling `eu_ai_act_deployer_obligations` covers the Art. 26(2)
**assignment**.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/ai_human_oversight/playbook.cacao.json

Scenario, workflow, regulatory anchors (EU AI Act Art. 14(1),
14(3)(a), 14(4)(a)-(e), 14(5)) and OSCAL / D3FEND control bindings are
documented in that folder's `mappings.yaml`. This folder holds only the
emitted artifact, a co-located copy of the CACAO source, and the
regeneration command.

## Layout

| Path                    | Source compiler      | Format                |
|-------------------------|----------------------|-----------------------|
| `playbook.cacao.json`   | (input)              | CACAO v2 JSON         |
| `workflow.temporal.py`  | `compilers.temporal` | Python (`temporalio`) |

## Why this one suits a durable-execution runtime

Art. 14 oversight is a **standing duty on a cadence**, not a one-shot.
The playbook runs per review window, and the terminal state closes on a
dated cycle-evidence artifact before the next window re-enters at the
start step. Two consequences for anyone binding real activities:

- The roster and briefing seams are expected to **outlive any single
  workflow execution**. A roster resolved for one window is normally
  the input to several, and a briefing discharges Art. 14(4)(a)-(c)
  for a deployment rather than for a run.
- The review activity is the long pole. It waits on human disposition
  of flagged outputs, so it is the one place where a durable timer and
  a heartbeat earn their keep; treating it as a short-lived call will
  produce timeouts that look like oversight failures in the evidence.

`__intervention_type__` is a separate output from
`__intervention_record_id__` on purpose: Art. 14(4)(d)-(e) name four
distinct exercises (decline, disregard, override, halt) that carry
different weight on review. An activity returning only the record loses
the severity signal.

## Regeneration

From the repo root:

    ./examples/temporal/ai_human_oversight/regenerate.sh

Equivalent direct invocation:

    PYTHONPATH=. python -m tools.compile \
        content/playbooks/ai_human_oversight/playbook.cacao.json \
        --target temporal \
        --out examples/temporal/ai_human_oversight/workflow.temporal.py

The drift guard between the committed worked example and the emitter
output is pinned by
`tests/examples/ai_human_oversight/test_golden.py`.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
Temporal cluster should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
Temporal is open source (MIT) and Temporal Cloud is one hosting choice
among several; operators are free to run their own cluster on EU
sovereign infrastructure (Nebul, OVHcloud, Scaleway, Hetzner). We ship
the structure, the operator owns the data plane.
