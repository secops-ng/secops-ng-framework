# `incident_timeline` — durable append-only incident-timeline builder

A durable Temporal workflow that accepts incident events from operators
or upstream detectors during a response, canonicalises them on close,
and writes a single timeline artifact to disk. The workflow body is
deterministic and survives worker restarts; the responding humans and
detectors can come and go without losing the running narrative.

## When to use it

You are running incident response and you want:

* A single durable place to append events as they happen, from any
  source — humans on a call, detectors firing into a queue, runbooks
  signalling their own completion.
* A canonical, sorted, deduplicated timeline artifact at the end —
  one JSON file per incident, hashed, with the event order resolved
  by observation time.
* Late corrections to be possible — re-signalling an event with the
  same ``event_id`` replaces the earlier version.
* A safety valve so a forgotten incident closes itself instead of
  hanging around forever.

The pattern deliberately does **not** decide how events are routed to
the workflow — that's the caller's job (a Slack/Teams bridge, a SIEM
forwarder, an operator CLI). The workflow contract is the signal
surface.

## Surface

### Input

```python
class IncidentTimelineInput(BaseModel):
    incident_id: str
    timeline_dir: str            # where persist_timeline writes
    max_events: int = 1000       # cap on buffered events
    deadline_seconds: int = 0    # 0 = no deadline; else seconds to wait for close
```

### Signals

* `append_event(event: TimelineEvent)` — append one event. Re-signalling
  with an existing ``event_id`` replaces the earlier entry at close time.
* `close()` — finalise the timeline and exit.

### Queries

* `buffered_events() -> list[TimelineEvent]` — events buffered so far,
  in arrival order (pre-canonicalisation).
* `event_count() -> int` — number of events buffered so far.

### Result

```python
class IncidentTimelineResult(BaseModel):
    incident_id: str
    event_count: int             # post-dedup
    timeline: TimelineRef | None # None if no events were appended
    closed_by_deadline: bool     # True if the deadline fired
```

### Activities

* `canonicalise_events(events) -> list[TimelineEvent]` — sorts events by
  ``observed_at`` (then ``event_id``) and collapses duplicates by
  ``event_id``. Pushed into an activity so the workflow body never
  depends on host sort stability.
* `persist_timeline(incident_id, events, timeline_dir) -> TimelineRef` —
  writes a single JSON artifact (`<incident_id>.json`) with the
  canonical events. Idempotent: repeated calls overwrite the same path.

## Durability notes

* Buffered state survives worker restarts — the signal handler appends
  to ``_buffer`` and Temporal persists that state in history. A
  responder's laptop can disconnect mid-incident and the running
  timeline is unaffected.
* ``max_events`` bounds buffered state so an adversarial or buggy
  signaller can't grow workflow state unbounded. Hitting the cap auto-
  closes the workflow with whatever has been collected.
* ``deadline_seconds`` is a safety valve — if no ``close`` signal
  arrives in time, the workflow closes itself and ``closed_by_deadline``
  in the result is ``True``. Set ``0`` to wait indefinitely.
* Signals received after ``close`` are dropped silently. Late detectors
  can keep firing without growing state or breaking the artifact.

## Fixtures

`fixtures/sample_incident.yaml` is a generic-labelled seed file you can
adapt for a smoke test — three out-of-order events that exercise the
sort and the persist path.

## Tests

Run from the framework root:

```
pytest patterns/incident_timeline/tests -q
```

Five tests are bundled: multi-signal canonicalisation, empty close, late
signals dropped, deadline-driven close, and a deterministic replay
test under `temporalio.testing.WorkflowEnvironment`.
