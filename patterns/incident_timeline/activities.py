"""Activities for the incident-timeline pattern.

Two activities, both pure side-effect boundaries — disk writes, hashing,
ISO timestamps. The workflow body stays deterministic.

* :func:`canonicalise_events` accepts a list of raw event dicts and
  returns them sorted by ``observed_at`` (then ``event_id`` as a stable
  tiebreaker) with duplicates by ``event_id`` collapsed. Sorting is
  pushed into an activity so the workflow body never depends on the
  host's sort stability or locale.
* :func:`persist_timeline` writes the canonical timeline as JSON to
  ``<timeline_dir>/<incident_id>.json`` and returns a structured
  :class:`TimelineRef`. Idempotent — repeated calls with the same body
  overwrite the same path.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from temporalio import activity


class TimelineEvent(BaseModel):
    """One append-only timeline event.

    ``event_id`` is the deduplication key. ``observed_at`` is the wall
    clock time the event happened (ISO-8601). ``source`` and ``kind``
    are short labels for the upstream detector and the category of the
    event; ``detail`` is free-form.
    """

    event_id: str = Field(..., min_length=1)
    observed_at: str = Field(..., min_length=1)  # ISO-8601
    source: str = Field(..., min_length=1)
    kind: str = Field(..., min_length=1)
    detail: str = ""


class TimelineRef(BaseModel):
    """Reference to a persisted canonical timeline artifact."""

    incident_id: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    event_count: int = Field(..., ge=0)
    sha256: str = Field(..., min_length=64, max_length=64)
    closed_at: str = Field(..., min_length=1)  # ISO-8601, UTC


@activity.defn
async def canonicalise_events(events: list[dict[str, Any]]) -> list[TimelineEvent]:
    """Return events sorted by ``observed_at`` with duplicate ids collapsed.

    Later occurrences of the same ``event_id`` overwrite earlier ones —
    operators may correct an event after the fact by re-signalling with
    the same id.
    """
    activity.logger.info("canonicalising %d raw events", len(events))
    by_id: dict[str, TimelineEvent] = {}
    for raw in events:
        ev = TimelineEvent.model_validate(raw)
        by_id[ev.event_id] = ev
    return sorted(by_id.values(), key=lambda e: (e.observed_at, e.event_id))


@activity.defn
async def persist_timeline(
    incident_id: str,
    events: list[dict[str, Any]],
    timeline_dir: str,
) -> TimelineRef:
    """Persist the canonical timeline as JSON and return a structured ref."""
    record = {
        "incident_id": incident_id,
        "event_count": len(events),
        "events": events,
    }
    body = json.dumps(record, indent=2, sort_keys=True).encode("utf-8")
    path = await asyncio.to_thread(_write_timeline, timeline_dir, incident_id, body)
    return TimelineRef(
        incident_id=incident_id,
        path=str(path),
        event_count=len(events),
        sha256=hashlib.sha256(body).hexdigest(),
        closed_at=datetime.now(UTC).isoformat(),
    )


def _write_timeline(timeline_dir: str, incident_id: str, body: bytes) -> Path:
    target_dir = Path(timeline_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = target_dir / f"{incident_id}.json"
    artifact_path.write_bytes(body)
    return artifact_path
