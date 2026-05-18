"""Durable append-only incident-timeline workflow.

Operators (or upstream detectors) append events via the ``append_event``
signal during incident response. The workflow waits — durably — for a
``close`` signal, at which point it canonicalises the buffered events
(sorted, deduplicated by ``event_id``) and persists a single timeline
artifact to disk. The workflow then returns a structured
:class:`IncidentTimelineResult` and exits.

Design constraints inherited from the framework's skeleton:

* The workflow body is deterministic — clocks come from
  :func:`workflow.wait_condition`, never :mod:`time`.
* Progression is driven by signals, not polling.
* All side effects live in :mod:`activities`.

``max_events`` bounds buffered state so tests and adversarial signallers
terminate cleanly. ``deadline_seconds`` is an optional safety valve that
forces the workflow to close itself if no ``close`` signal arrives in
time — useful for forgotten incidents.
"""

from __future__ import annotations

from datetime import timedelta

from pydantic import BaseModel, Field
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from .activities import (
        TimelineEvent,
        TimelineRef,
        canonicalise_events,
        persist_timeline,
    )


class IncidentTimelineInput(BaseModel):
    """Input payload for :class:`IncidentTimelineWorkflow`."""

    incident_id: str = Field(..., min_length=1)
    timeline_dir: str = Field(..., min_length=1)
    max_events: int = Field(default=1000, ge=1)
    deadline_seconds: int = Field(default=0, ge=0)  # 0 = no deadline


class IncidentTimelineResult(BaseModel):
    """Final result returned when the workflow closes."""

    incident_id: str
    event_count: int
    timeline: TimelineRef | None = None
    closed_by_deadline: bool = False


@workflow.defn
class IncidentTimelineWorkflow:
    """Durable append-only incident-timeline workflow.

    Internal state:

    * ``_buffer`` — every event accepted via ``append_event``, preserved
      in arrival order. Canonicalisation (sort + dedup) is deferred to
      close time so the workflow body stays a single linear sequence of
      decisions.
    * ``_closed`` — flipped by the ``close`` signal (or the deadline) to
      release the wait.
    * ``_cap`` — copied from ``payload.max_events`` at the start of
      ``run`` so the ``append_event`` signal handler can enforce the
      bound without re-reading the payload.
    """

    def __init__(self) -> None:
        self._buffer: list[TimelineEvent] = []
        self._closed: bool = False
        self._cap: int = 1000

    @workflow.run
    async def run(self, payload: IncidentTimelineInput) -> IncidentTimelineResult:
        self._cap = payload.max_events
        deadline_hit = False
        if payload.deadline_seconds > 0:
            try:
                await workflow.wait_condition(
                    lambda: self._closed,
                    timeout=timedelta(seconds=payload.deadline_seconds),
                )
            except TimeoutError:
                deadline_hit = True
                self._closed = True
        else:
            await workflow.wait_condition(lambda: self._closed)

        raw = [ev.model_dump() for ev in self._buffer]
        canonical = await workflow.execute_activity(
            canonicalise_events,
            args=[raw],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
        canonical_events = [TimelineEvent.model_validate(e) for e in canonical]

        timeline_ref: TimelineRef | None = None
        if canonical_events:
            ref = await workflow.execute_activity(
                persist_timeline,
                args=[
                    payload.incident_id,
                    [e.model_dump() for e in canonical_events],
                    payload.timeline_dir,
                ],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            timeline_ref = TimelineRef.model_validate(ref)

        return IncidentTimelineResult(
            incident_id=payload.incident_id,
            event_count=len(canonical_events),
            timeline=timeline_ref,
            closed_by_deadline=deadline_hit,
        )

    # ------------------------------------------------------------------ signals
    @workflow.signal
    def append_event(self, event: TimelineEvent) -> None:
        """Append one event to the in-flight incident timeline.

        Signals received after ``close`` are dropped silently — the
        workflow has already moved on and we don't want late detectors
        to grow state unbounded. Signals that would push ``_buffer``
        past ``max_events`` are also dropped, with the workflow closing
        itself once the cap is hit.
        """
        if self._closed:
            return
        if len(self._buffer) >= self._cap:
            self._closed = True
            return
        self._buffer.append(event)
        if len(self._buffer) >= self._cap:
            self._closed = True

    @workflow.signal
    def close(self) -> None:
        """Request the workflow finalise the timeline and exit."""
        self._closed = True

    # ------------------------------------------------------------------ queries
    @workflow.query
    def buffered_events(self) -> list[TimelineEvent]:
        """Events buffered so far, in arrival order (pre-canonicalisation)."""
        return list(self._buffer)

    @workflow.query
    def event_count(self) -> int:
        """Number of events buffered so far."""
        return len(self._buffer)
