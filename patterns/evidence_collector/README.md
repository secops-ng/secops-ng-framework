# `evidence_collector` — durable evidence gathering against a control set

A durable Temporal workflow that walks a declared set of controls, runs an
evidence-collection activity per control, and persists an artifact for each
one. Controls can be added mid-run via signal; the workflow survives worker
restarts and resumes from where it left off without double-processing a
control that already produced an artifact.

## When to use it

You have a list of controls (access reviews, log retention checks, encryption
posture snapshots, retention spot-checks, ...) and you want to:

* Run the collection step against each one durably.
* Resume cleanly if a worker is recycled mid-run.
* Add more controls partway through without restarting.
* End up with one artifact per control, written to a known directory.

The pattern deliberately does **not** decide what evidence to collect — that
belongs in the activity. Replace the body of `collect_evidence` to point at
your real evidence sources (SIEM queries, KB lookups, configuration reads).

## Surface

### Input

```python
class EvidenceCollectorInput(BaseModel):
    controls: list[Control]   # initial control set
    artifact_dir: str         # absolute path; activity writes here
```

### Control

```python
class Control(BaseModel):
    control_id: str           # stable, unique within a run
    description: str          # one-line human-readable label
```

### Signals

* `add_control(control: Control)` — queue an additional control while the
  workflow is running. Duplicate `control_id`s are skipped.
* `finish()` — once the pending queue drains, exit cleanly.

### Queries

* `collected() -> list[ArtifactRef]` — artifacts produced so far. Useful for
  operator dashboards and tests.
* `pending_count() -> int` — controls still waiting for collection.

### Result

```python
class EvidenceCollectorResult(BaseModel):
    artifacts: list[ArtifactRef]   # one per collected control
```

### Activity

`collect_evidence(control, artifact_dir) -> ArtifactRef` writes a JSON
artifact (`<control_id>.json`) into `artifact_dir` and returns a structured
reference (control id, path, sha256, collected_at). Replace the body for
real evidence sources; the workflow contract stays the same.

## Durability notes

* The workflow body is signal-driven — it blocks on `wait_condition` and
  never polls.
* `_seen` tracks which `control_id`s have been queued. Replays land on the
  same set, so duplicate signals collapse deterministically.
* `_collected` is appended to only after each activity completes, so the
  history records exactly one artifact per successful collection.
* If the worker dies after the activity has written the artifact but before
  the workflow records it, Temporal will retry the activity. The activity
  is therefore idempotent: it overwrites the artifact file for the same
  `control_id` rather than failing on conflict.

## Fixtures

`fixtures/sample_controls.yaml` is a generic example control set
(`workload-a`, `workload-b`, `workload-c`). Generated artifacts live under
`fixtures/artifacts/` and are gitignored.

## Tests

`tests/` holds the standalone test suite — a replay test that proves the
workflow is deterministic, plus behaviour tests for signal handling, the
de-duplication invariant, and the activity's idempotence.
