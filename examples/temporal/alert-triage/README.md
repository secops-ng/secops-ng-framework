# examples/temporal/alert-triage

Worked example: the alert-triage CACAO v2 source playbook compiled by
the Temporal reference compiler. Operators who already run Temporal can
import `workflow.temporal.py` into their worker module to see the
topology the emitter produces; binding the activity bodies to real
connectors (alert source, suppression check, classifier, response
branches) is the operator's job.

This worked example is **SKELETON** — the workflow control flow, step
ids, activity signatures, and the start → ingest → enrich → if(suppress)
→ classify → switch(priority{p1,p2,p3,p4}) → end shape are committed;
activity bodies are deliberately stubbed (`NotImplementedError`) so the
example imports cleanly without any tool or model binding. Real
bindings land in follow-up CORE/EXTEND work against the source playbook.

## Source

Canonical CACAO playbook (YAML):

    ../../../content/playbooks/alert-triage.cacao.yaml

The YAML source carries scenario, regulatory anchors, control / metric
/ telemetry bindings, and the operator-supplied bindings. This folder
holds the emitted Temporal artifact, a byte-deterministic JSON mirror
of the YAML source (the Temporal emitter consumes JSON via the CACAO
parser), and the regeneration command.

## Files in this directory

| Path                    | Source compiler      | Format                |
|-------------------------|----------------------|-----------------------|
| `playbook.cacao.json`   | (input mirror)       | CACAO v2 JSON         |
| `workflow.temporal.py`  | `compilers.temporal` | Python (`temporalio`) |
| `regenerate.sh`         | n/a                  | regeneration script   |

The two formats round-trip through `yaml.safe_load` + `json.dumps`;
the schema is format-agnostic.

## Regeneration

Deterministic emitter; re-running yields byte-identical output. From
the repo root:

    ./examples/temporal/alert-triage/regenerate.sh

The script mirrors the canonical CACAO YAML source into the JSON form
this folder commits, then re-emits `workflow.temporal.py` via
`tools.compile --target temporal`. A drift test in
`tests/examples/alert_triage/` (sibling F-WF-03 follow-up) fails the
suite if the committed artifact diverges from a fresh regeneration, so
the worked example stays honest as the compiler evolves.

## Wiring it into your runtime

`workflow.temporal.py` is a Temporal `@workflow.defn` whose body calls
each `@activity.defn` stub in the topology the CACAO playbook defines.
The integrator pattern is:

1. Register the workflow class on a Temporal worker.
2. Replace each activity body (`raise NotImplementedError`) with a call
   to the operator's existing connector — alert source, enrichment
   provider, suppression cache, classifier, response-branch ticketing
   / containment actions.
3. Keep the per-activity `RetryPolicy` constants as defaults; tune
   timeouts and `maximum_attempts` to the operator's environment.

The `if-condition` after `enrich` reads the suppression decision and
routes to either the suppress-and-close branch or the
classify-and-prioritise branch. The `switch-condition` after
classification reads the priority bucket (`p1_severe`, `p2_high`,
`p3_routine`, `p4_informational`) and routes to the matching response
activity. Unknown / missing decisions fall through to the spec's
`default` branch, so a misbehaving classifier terminates the run
rather than dead-locking.

## Sovereignty note

Temporal is open source (MIT) and runs as a server + worker process
pair: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. No
telemetry, no execution traces, no alert content, no identifying
flows reach this repository or the SecOps-NG project. The operator
runs Temporal on infrastructure they control — we ship the structure,
they own the data plane.
