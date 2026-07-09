# examples/temporal/threat_intel_ingest

Worked example: the `playbook.threat_intel_ingest@v1` CACAO v2 playbook
compiled by the Temporal reference compiler. Operators who already run
Temporal can import `workflow.temporal.py` into their worker module to
see the topology the emitter produces; binding the activity bodies to
real connectors (STIX 2.1 / TAXII feed source, OCSF Threat Intelligence
normaliser, SIEM Sigma rule activation, perimeter / DNS / EDR blocklist
enforcement) is the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/threat_intel_ingest/playbook.cacao.json

Scenario, workflow, regulatory anchors, control / metric / telemetry
bindings, and the operator-supplied bindings are documented in that
folder's `README.md`. This folder holds only the emitted artifact, a
co-located copy of the CACAO source, and the regeneration command.

## Layout

| Path                    | Source compiler      | Format                |
|-------------------------|----------------------|-----------------------|
| `playbook.cacao.json`   | (input)              | CACAO v2 JSON         |
| `workflow.temporal.py`  | `compilers.temporal` | Python (`temporalio`) |

## Regeneration

Deterministic emitter; re-running yields byte-identical output. From
the repo root:

    ./examples/temporal/threat_intel_ingest/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.temporal.py` via `tools.compile --target temporal`.

## Common pitfalls when binding activity bodies

The emitted `workflow.temporal.py` gives you a `@workflow.defn` with
the topology, per-step activity stubs, and the CACAO I/O contract as
typed arguments. The activity bodies are where operator judgement
lands. A short checklist of the pitfalls a maintainer already knows
but a first-time integrator does not:

- **Upstream rate-limiting and backpressure.** STIX 2.1 / TAXII
  collections publish on their own cadence and typically cap poll
  frequency. Do not put a naive retry loop inside the activity body;
  configure `RetryPolicy` on `workflow.execute_activity(...)` with a
  meaningful `initial_interval`, an exponential `backoff_coefficient`,
  and `non_retryable_error_types` for feed-side auth failures. If the
  feed publishes a `Retry-After` header, raise
  `ApplicationError("...", details=[retry_after_s])` and translate it
  into a Temporal-side timer in the workflow rather than sleeping
  inside the activity — a worker holding the slot on `time.sleep`
  starves the task queue.
- **Deduplication and idempotency keys.** The CACAO playbook exposes
  the STIX object `id` (a UUID pinned by the producer) as the stable
  key. Bind that field — not `created`, not `modified`, not the
  local ingest timestamp — as the idempotency key. Temporal activities
  are retried on transient failure; if the downstream connector
  (SIEM, blocklist gateway) is not itself idempotent, guard writes
  behind an activity-level dedup table keyed on STIX `id`, and prefer
  a `SignalWithStart` on the STIX `id` when fanning out to the
  detection-rule activation step.
- **Credentials and sovereign hosting.** Feed endpoints, SIEM API
  keys, and blocklist-gateway tokens belong in the worker's runtime
  environment — read them via `os.environ` in the worker startup
  and inject them into the activity via a shared dependency, not into
  workflow arguments (workflow inputs are persisted in event history
  forever). The repo's [`.env.example`](../../../.env.example)
  documents the variable names the reference examples expect; the
  sovereignty posture (which EU host runs the Temporal server + worker
  pair, which egress domain the feed uses) is discussed in
  [`docs/FOUNDATION.md`](../../../docs/FOUNDATION.md).
- **Temporal gotcha — activity timeout vs. retry policy.** The two
  most common mis-tunings when binding TAXII / SIEM / blocklist
  activities are (a) setting `start_to_close_timeout` shorter than the
  upstream feed's worst-case response time, so healthy calls get
  cancelled and retried into a rate-limit spiral, and (b) leaving
  `RetryPolicy.maximum_attempts` unset (unbounded) on an activity
  whose failure is deterministic (bad TAXII collection id, missing
  scope). The rule of thumb: `start_to_close_timeout` = p99 upstream
  latency × 1.5, and `maximum_attempts` is finite with feed-side auth
  errors in `non_retryable_error_types`. Distinguish deterministic
  failure from transience at the activity boundary.

## Sovereignty note

Temporal is open source (MIT) and runs as a server + worker process
pair: hosting it on EU sovereign infrastructure (Nebul, OVHcloud,
Scaleway, Hetzner) is a deployment choice, not a vendor decision. No
telemetry, no execution traces, no identifying data flows reach this
repository or the SecOps-NG project. The operator runs Temporal on
infrastructure they control — we ship the structure, they own the
data plane.
