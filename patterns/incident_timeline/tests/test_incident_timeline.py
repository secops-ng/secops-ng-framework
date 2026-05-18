"""Standalone tests for the incident-timeline pattern.

Five things are proved here:

1. Behaviour — multiple ``append_event`` signals followed by ``close``
   produce a canonical, sorted, deduplicated timeline artifact on disk.
2. Empty close — closing with no buffered events yields a result with
   zero events and no timeline artifact (no empty files left behind).
3. Late signals — ``append_event`` arriving after ``close`` is silently
   dropped, not appended to the persisted timeline.
4. Deadline — the safety-valve deadline closes the workflow when no
   ``close`` signal arrives in time.
5. Determinism — the workflow body replays cleanly through Temporal's
   ``WorkflowEnvironment`` time-skipping harness.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from pathlib import Path

import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Replayer, Worker

from patterns.incident_timeline.activities import (
    TimelineEvent,
    TimelineRef,
    canonicalise_events,
    persist_timeline,
)
from patterns.incident_timeline.workflow import (
    IncidentTimelineInput,
    IncidentTimelineResult,
    IncidentTimelineWorkflow,
)

TASK_QUEUE = "incident-timeline-test-queue"


def _event(event_id: str, observed_at: str, *, detail: str = "ok") -> TimelineEvent:
    return TimelineEvent(
        event_id=event_id,
        observed_at=observed_at,
        source="detector-alpha",
        kind="anomaly-detected",
        detail=detail,
    )


def _assert_timeline_persisted(
    ref: TimelineRef,
    *,
    expected_incident_id: str,
    expected_event_ids: list[str],
) -> None:
    """Sync helper — keep disk reads out of the async test body."""
    path = Path(ref.path)
    assert path.exists()
    body = path.read_bytes()
    assert hashlib.sha256(body).hexdigest() == ref.sha256
    doc = json.loads(body)
    assert doc["incident_id"] == expected_incident_id
    assert doc["event_count"] == len(expected_event_ids)
    persisted_ids = [e["event_id"] for e in doc["events"]]
    assert persisted_ids == expected_event_ids


@pytest.mark.asyncio
async def test_multi_signal_canonical_timeline(tmp_path: Path) -> None:
    """Many appends + close: canonical sorted/deduplicated timeline persists."""
    timeline_dir = tmp_path / "timelines"
    payload = IncidentTimelineInput(
        incident_id="incident-0001",
        timeline_dir=str(timeline_dir),
        max_events=100,
    )

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[IncidentTimelineWorkflow],
            activities=[canonicalise_events, persist_timeline],
        ):
            handle = await env.client.start_workflow(
                IncidentTimelineWorkflow.run,
                payload,
                id=f"it-multi-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )
            # Out-of-order arrival; one duplicate id with corrected detail.
            await handle.signal(
                IncidentTimelineWorkflow.append_event,
                _event("ev-002", "2026-01-01T08:05:00+00:00"),
            )
            await handle.signal(
                IncidentTimelineWorkflow.append_event,
                _event("ev-001", "2026-01-01T08:00:00+00:00"),
            )
            await handle.signal(
                IncidentTimelineWorkflow.append_event,
                _event("ev-003", "2026-01-01T08:30:00+00:00"),
            )
            # Re-signal ev-002 with a corrected detail; later wins.
            await handle.signal(
                IncidentTimelineWorkflow.append_event,
                _event("ev-002", "2026-01-01T08:05:00+00:00", detail="corrected"),
            )
            await handle.signal(IncidentTimelineWorkflow.close)
            result: IncidentTimelineResult = await handle.result()

    assert result.event_count == 3
    assert result.closed_by_deadline is False
    assert result.timeline is not None
    _assert_timeline_persisted(
        result.timeline,
        expected_incident_id="incident-0001",
        expected_event_ids=["ev-001", "ev-002", "ev-003"],
    )
    # Confirm dedup took the latest signal's detail.
    persisted = json.loads(Path(result.timeline.path).read_bytes())  # noqa: ASYNC240
    ev2 = next(e for e in persisted["events"] if e["event_id"] == "ev-002")
    assert ev2["detail"] == "corrected"


@pytest.mark.asyncio
async def test_close_with_no_events_yields_empty_result(tmp_path: Path) -> None:
    """Close with zero buffered events: no artifact, zero count, clean exit."""
    timeline_dir = tmp_path / "timelines"
    payload = IncidentTimelineInput(
        incident_id="incident-empty",
        timeline_dir=str(timeline_dir),
    )

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[IncidentTimelineWorkflow],
            activities=[canonicalise_events, persist_timeline],
        ):
            handle = await env.client.start_workflow(
                IncidentTimelineWorkflow.run,
                payload,
                id=f"it-empty-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )
            await handle.signal(IncidentTimelineWorkflow.close)
            result = await handle.result()

    assert result.event_count == 0
    assert result.timeline is None
    assert not (timeline_dir / "incident-empty.json").exists()


@pytest.mark.asyncio
async def test_signals_after_close_are_dropped(tmp_path: Path) -> None:
    """``append_event`` after ``close`` does not extend the buffer."""
    timeline_dir = tmp_path / "timelines"
    payload = IncidentTimelineInput(
        incident_id="incident-late",
        timeline_dir=str(timeline_dir),
    )

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[IncidentTimelineWorkflow],
            activities=[canonicalise_events, persist_timeline],
        ):
            handle = await env.client.start_workflow(
                IncidentTimelineWorkflow.run,
                payload,
                id=f"it-late-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )
            await handle.signal(
                IncidentTimelineWorkflow.append_event,
                _event("ev-001", "2026-01-01T08:00:00+00:00"),
            )
            await handle.signal(IncidentTimelineWorkflow.close)
            # Race: signal may land before or after the workflow accepts
            # close; Temporal serialises signals, so this one is processed
            # against post-close state and must be dropped.
            await handle.signal(
                IncidentTimelineWorkflow.append_event,
                _event("ev-LATE", "2026-01-01T09:00:00+00:00"),
            )
            result = await handle.result()

    assert result.event_count == 1
    assert result.timeline is not None
    _assert_timeline_persisted(
        result.timeline,
        expected_incident_id="incident-late",
        expected_event_ids=["ev-001"],
    )


@pytest.mark.asyncio
async def test_deadline_closes_workflow_without_close_signal(tmp_path: Path) -> None:
    """The safety-valve deadline finalises the timeline without ``close``."""
    timeline_dir = tmp_path / "timelines"
    payload = IncidentTimelineInput(
        incident_id="incident-deadline",
        timeline_dir=str(timeline_dir),
        deadline_seconds=3600,
    )

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[IncidentTimelineWorkflow],
            activities=[canonicalise_events, persist_timeline],
        ):
            handle = await env.client.start_workflow(
                IncidentTimelineWorkflow.run,
                payload,
                id=f"it-deadline-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )
            await handle.signal(
                IncidentTimelineWorkflow.append_event,
                _event("ev-001", "2026-01-01T08:00:00+00:00"),
            )
            # time-skipping env advances virtual clock past 3600s.
            result = await handle.result()

    assert result.closed_by_deadline is True
    assert result.event_count == 1
    assert result.timeline is not None


@pytest.mark.asyncio
async def test_replay_is_deterministic(tmp_path: Path) -> None:  # noqa: ASYNC240
    """Recorded history replays cleanly — no NondeterminismError."""
    timeline_dir = tmp_path / "timelines"
    payload = IncidentTimelineInput(
        incident_id="incident-replay",
        timeline_dir=str(timeline_dir),
    )

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[IncidentTimelineWorkflow],
            activities=[canonicalise_events, persist_timeline],
        ):
            handle = await env.client.start_workflow(
                IncidentTimelineWorkflow.run,
                payload,
                id=f"it-replay-{uuid.uuid4()}",
                task_queue=TASK_QUEUE,
            )
            await handle.signal(
                IncidentTimelineWorkflow.append_event,
                _event("ev-002", "2026-01-01T08:05:00+00:00"),
            )
            await handle.signal(
                IncidentTimelineWorkflow.append_event,
                _event("ev-001", "2026-01-01T08:00:00+00:00"),
            )
            # Brief yield so signals are interleaved with workflow ticks
            # in history — gives Replayer something to chew on.
            await asyncio.sleep(0)
            await handle.signal(IncidentTimelineWorkflow.close)
            await handle.result()

            history = await handle.fetch_history()
            replayer = Replayer(workflows=[IncidentTimelineWorkflow])
            await replayer.replay_workflow(history)
