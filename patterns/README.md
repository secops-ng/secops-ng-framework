# Pattern Library

Short, named, copy-pastable durable Temporal workflow patterns for sovereign
operations. Each pattern is self-contained: one workflow file, one activities
file, fixtures, README, and tests. No cross-pattern imports.

The pattern library is the framework's "copy this" surface — small enough to
read in one sitting, durable enough to run in production, sovereignty-native
by default.

## Patterns

### [`evidence_collector`](./evidence_collector/)

A durable Temporal workflow that walks a declared set of controls, runs an
evidence-collection activity per control, and persists one artifact per
control. New controls can be added mid-run by signal; the workflow survives
worker restarts and resumes without double-processing controls that have
already produced an artifact. Use it as the spine of any periodic
controls-evidence run where partial progress must outlive the worker.

### [`provider_attestation`](./provider_attestation/)

A durable Temporal workflow that periodically re-checks whether a declared
sovereign provider still satisfies a set of criteria, writes one attestation
record per cycle, and emits a structured regression event the moment a
criterion that previously passed starts failing. Use it to keep a continuous,
auditable record of provider posture and to wire regressions into whatever
downstream channel — ticket, chat, follow-up workflow — your operation uses.

### [`incident_timeline`](./incident_timeline/)

A durable Temporal workflow that accepts incident events from operators and
upstream detectors during a response, canonicalises them on close, and writes
a single sorted, deduplicated timeline artifact per incident. Late
corrections replace earlier versions of the same event, a safety timeout
closes forgotten incidents, and the resulting JSON is hashed for audit. Use
it as the durable backbone behind your response bridge.

## Contributing a new pattern

Every new pattern must ship as a single PR that includes:

a. **A README** under `patterns/<name>/README.md` stating intent, when to
   use it, and the full signal / query / input / output interface.
b. **A sample fixture** under `patterns/<name>/fixtures/` — generic labels
   only (`workload-a`, `eu-provider-alpha`), never real vendor or
   organisation names.
c. **Replay coverage** — a test using `temporalio.testing` that replays
   recorded history to prove the workflow body is deterministic.
d. **Custodian review** for forward-public hygiene before merge: community
   voice, no internal infrastructure, no client or contributor names, no
   credentials, no live-API dependencies.

In scope: recurring sovereign-operations problems solved at the workflow
layer, in roughly 200 lines of workflow code plus tests, with file-based or
signal-based input only, and no imports from other patterns.

Out of scope: anything that requires live cloud APIs (route through a
private operational repo), anything that needs real third-party data
(route through the knowledge base in a private repo), or anything that
cannot be exercised with a committed fixture.

## Layout

Every pattern follows the same shape:

```
patterns/<name>/
├── README.md          # what it does, when to use it, signal/query surface
├── workflow.py        # the @workflow.defn class — deterministic body
├── activities.py      # @activity.defn functions — the side-effect boundary
├── fixtures/          # sample inputs and (gitignored) sample outputs
└── tests/             # standalone + replay tests
```

Tests are auto-discovered by pytest because `patterns` is on `testpaths`
in `pyproject.toml`.
