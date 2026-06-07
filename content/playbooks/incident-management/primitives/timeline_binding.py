"""F-PT-02 incident-timeline binding adapter.

The F-WF-05 incident-management workflow signals the F-PT-02
incident-timeline pattern at three points:

* ``open_timeline`` — at the start of the regulator window. Returns
  an opaque ``timeline_handle`` that every subsequent submission
  threads through.
* ``record_event`` — after each of the three regulator submissions
  (early-warning, 72h notification, one-month final report).
* ``close_timeline`` — at the end of the workflow. The pattern
  persists the canonical regulator-shaped timeline JSON at
  ``content/evidence/incidents/<incident-id>/timeline.json`` for
  downstream consumption by F-CP-02.

Per the F-WF-05 gap inventory § 4 question 1, the ``patterns/`` tree
is not currently present on ``main``. ROADMAP marks F-PT-02 Shipped
but no ``patterns/incident_timeline/`` module is on disk for the
CORE-PRIM card to bind directly against. The gap inventory's mitigation
(§ 4 q.1, second reading) is: ship a thin adapter under
``primitives/`` that names the contract the CORE-WIRE cards will use,
with a documented TODO so a separate F-PT-02 archaeology / relocation
pass can swap the adapter for the real binding when the pattern module
lands. That is what this module is.

The adapter's contract is the public-facing surface the per-target
CORE action bodies bind against today; the underlying implementation
is a deterministic in-memory event recorder that produces the
regulator-shaped timeline JSON the gap inventory promises F-CP-02 can
consume. When the F-PT-02 pattern module lands on disk, the adapter's
``__pt02_binding_status__`` flips from ``"adapter"`` to ``"pattern"``
and the in-memory recorder is swapped for the real pattern, *without*
the per-target CORE bodies changing shape.

TODO(F-PT-02): replace the in-memory recorder below with a call
through to ``patterns.incident_timeline`` when the pattern module is
on disk. Tracked by F-WF-05 gap inventory § 4 question 1; see
``docs/internal/f-wf-05-gap-inventory.md``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import PurePosixPath
from typing import Literal
from uuid import UUID

from .stage_clock import StageName, stages_in_order

__all__ = [
    "PT02_BINDING_STATUS",
    "TimelineClosure",
    "TimelineEvent",
    "TimelineSession",
    "open_timeline",
    "record_event",
    "close_timeline",
    "timeline_artefact_path",
]


# When the F-PT-02 pattern module lands, this constant flips to
# ``"pattern"`` and the in-memory recorder below is swapped for the
# real binding. The CORE-WIRE cards (6/7/8) pin against the constant
# in their audit-trail metadata so a binding-status flip is visible
# in the worked-example diffs.
PT02_BINDING_STATUS: Literal["adapter", "pattern"] = "adapter"


@dataclass(frozen=True)
class TimelineEvent:
    """One event on the regulator-shaped timeline."""

    event_id: str
    stage: StageName | Literal["timeline_open", "timeline_close"]
    occurred_at: datetime
    summary: str
    payload_digest: str


@dataclass
class TimelineSession:
    """In-memory representation of an open incident-management timeline.

    Mutable on purpose — the recorder threads the same session through
    the three regulator submissions and the close action. The
    contract surface (the dataclass shape) is what the F-PT-02 pattern
    module's real session object will mirror when the adapter is
    swapped out.
    """

    handle: str
    incident_id: UUID
    opened_at: datetime
    events: list[TimelineEvent] = field(default_factory=list)
    closed_at: datetime | None = None
    binding_status: Literal["adapter", "pattern"] = PT02_BINDING_STATUS


@dataclass(frozen=True)
class TimelineClosure:
    """Frozen receipt returned by :func:`close_timeline`."""

    incident_id: UUID
    handle: str
    opened_at: datetime
    closed_at: datetime
    artefact_path: str
    event_count: int
    binding_status: Literal["adapter", "pattern"]


def _require_utc(name: str, value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(
            f"{name} must be a datetime, got {type(value).__name__}"
        )
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            f"{name} must be timezone-aware so the timeline has a "
            "deterministic absolute reference."
        )
    if value.utcoffset() != timedelta(0):
        return value.astimezone(timezone.utc)
    return value


def _digest(*parts: str) -> str:
    payload = "\u001f".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def open_timeline(
    *, incident_id: UUID, opened_at: datetime
) -> TimelineSession:
    """Open a new incident-management timeline.

    Produces a :class:`TimelineSession` carrying an opaque handle the
    CACAO ``__timeline_handle__`` variable will hold. Every subsequent
    submission threads through this session; the close action persists
    the events as the regulator-shaped timeline JSON.
    """
    if not isinstance(incident_id, UUID):
        raise TypeError(
            f"incident_id must be a UUID, got {type(incident_id).__name__}"
        )
    opened = _require_utc("opened_at", opened_at)
    handle = "incident-timeline/" + _digest(str(incident_id), opened.isoformat())
    session = TimelineSession(
        handle=handle,
        incident_id=incident_id,
        opened_at=opened,
    )
    session.events.append(
        TimelineEvent(
            event_id=_digest(handle, "open"),
            stage="timeline_open",
            occurred_at=opened,
            summary="timeline opened",
            payload_digest=_digest(str(incident_id), "open"),
        )
    )
    return session


def record_event(
    session: TimelineSession,
    *,
    stage: StageName,
    occurred_at: datetime,
    summary: str,
    payload_digest: str,
) -> TimelineEvent:
    """Append a regulator-submission event to ``session``.

    Args:
        session: An open :class:`TimelineSession` from
            :func:`open_timeline`.
        stage: Regulator-submission stage. Closed alphabet —
            :data:`stage_clock.StageName`.
        occurred_at: Timezone-aware instant the regulator submission
            was dispatched.
        summary: Short audit-trail-ready description.
        payload_digest: Short hex digest over the submission payload,
            so a replay-vs-original comparison on the regulator-shaped
            timeline JSON is a single string-equal check.

    Returns:
        The :class:`TimelineEvent` that was appended.
    """
    if session.closed_at is not None:
        raise ValueError(
            f"timeline {session.handle!r} is already closed; cannot "
            "record additional events"
        )
    if stage not in stages_in_order():
        raise ValueError(
            f"unknown stage {stage!r}; expected one of "
            f"{stages_in_order()!r}"
        )
    occurred = _require_utc("occurred_at", occurred_at)
    event = TimelineEvent(
        event_id=_digest(session.handle, stage, occurred.isoformat()),
        stage=stage,
        occurred_at=occurred,
        summary=summary,
        payload_digest=payload_digest,
    )
    session.events.append(event)
    return event


def timeline_artefact_path(incident_id: UUID) -> str:
    """Return the repository-relative path the timeline JSON is persisted at.

    Joined into the path the close action returns into the CACAO
    ``__timeline_artefact_path__`` variable. Forward slash separator —
    operators run on every host the framework supports.
    """
    return str(
        PurePosixPath("content")
        / "evidence"
        / "incidents"
        / str(incident_id)
        / "timeline.json"
    )


def close_timeline(
    session: TimelineSession, *, closed_at: datetime
) -> TimelineClosure:
    """Close ``session`` and return the :class:`TimelineClosure` receipt.

    The receipt names the path at which the close-timeline action
    will persist the regulator-shaped timeline JSON
    (``content/evidence/incidents/<incident-id>/timeline.json``).
    Persistence itself is the per-target CORE body's responsibility;
    the adapter only names the path and the binding status.
    """
    if session.closed_at is not None:
        raise ValueError(
            f"timeline {session.handle!r} is already closed at "
            f"{session.closed_at.isoformat()}"
        )
    closed = _require_utc("closed_at", closed_at)
    session.closed_at = closed
    session.events.append(
        TimelineEvent(
            event_id=_digest(session.handle, "close"),
            stage="timeline_close",
            occurred_at=closed,
            summary="timeline closed",
            payload_digest=_digest(str(session.incident_id), "close"),
        )
    )
    return TimelineClosure(
        incident_id=session.incident_id,
        handle=session.handle,
        opened_at=session.opened_at,
        closed_at=closed,
        artefact_path=timeline_artefact_path(session.incident_id),
        event_count=len(session.events),
        binding_status=session.binding_status,
    )


