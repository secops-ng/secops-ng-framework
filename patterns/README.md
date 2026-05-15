# Pattern Library

Short, named, copy-pastable durable Temporal workflow patterns for sovereign
operations. Each pattern is self-contained: one workflow file, one activities
file, fixtures, README, and tests. No cross-pattern imports.

The pattern library is the framework's "copy this" surface — small enough to
read in one sitting, durable enough to run in production, sovereignty-native
by default.

## Patterns

| Pattern                                          | What it does                                                            |
|--------------------------------------------------|-------------------------------------------------------------------------|
| [`evidence_collector`](./evidence_collector/)    | Durable, restartable evidence gathering against a declared control set. |
| `provider_attestation` _(planned, see #16)_      | Periodic verification that a declared sovereign provider still meets KB criteria. |
| `incident_timeline` _(planned, see #16)_         | Durable append-only incident timeline builder.                          |

## Contribution rules

A pattern is in scope for this library if it:

1. Solves a recurring sovereign-operations problem at the workflow layer.
2. Fits in ~200 lines of workflow code plus tests (split if larger).
3. Takes file-based or signal-based input only — no live cloud credentials,
   no third-party API keys committed.
4. Uses generic fixture labels (`workload-a`, `eu-provider-alpha`) — never
   real vendor or organisation names.
5. Ships with a replay test using `temporalio.testing` to prove determinism.
6. Compiles standalone — no imports from other patterns.

A pattern is **out of scope** if it requires live cloud APIs (those belong in
private operational repos) or named third-party data (route those through
the knowledge base in a private repo).

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
