"""Stage-clock arithmetic for the NIS2 Article 23 three-stage timeline.

The incident_management workflow (F-WF-05) is bounded by three
regulator-submission stages whose windows start at the
incident-detection instant (the timeline open) and close at fixed
offsets fixed by NIS2 Article 23(4):

* ``early_warning`` — 24 hours after timeline open.
* ``notification`` — 72 hours after timeline open.
* ``final_report`` — one calendar month after timeline open
  (interpreted here as 30 days, which is the most conservative
  uniform-length reading consistent with the ENISA Technical Guideline
  and is what the workflow's deterministic replay-vs-original test
  pins against; an operator who prefers calendar-month arithmetic
  swaps the helper in their compile target's adapter layer without
  changing the contract).

The primitive is pure code — no DSPy, no LM, no clock-of-record
side-channel. Inputs are timezone-aware UTC datetimes and the closed
:data:`StageName` alphabet; outputs are frozen :class:`StageWindow`
records and a :class:`StageVerdict` for "is the submit happening on
time?" decisions. Determinism is the contract: two replays of the
same incident timeline against the same submission timestamps return
byte-identical verdicts.

Per ``docs/FOUNDATION.md`` §LLM determinism, the regulator-clock
decision is exactly the class of fact that must be deterministic code.
The free-text fields on the final-report submission are the only DSPy
reach for this workflow; see :mod:`.signatures`.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal, Tuple

__all__ = [
    "STAGE_DURATIONS",
    "StageBudget",
    "StageName",
    "StageVerdict",
    "StageWindow",
    "due_at",
    "elapsed",
    "stage_window",
    "stages_in_order",
    "verdict_for_submission",
]


# Closed alphabet of regulator-submission stages. Mirrors the keys the
# operator-supplied ``__notification_destinations__`` CACAO variable
# carries; adding a stage here is a deliberate change that updates the
# variable's documented keys first, then propagates into this alphabet.
StageName = Literal["early_warning", "notification", "final_report"]


# NIS2 Article 23(4) cadence. Ordered so a per-stage sweep walks the
# regulator timeline in real-world order; index also stable for the
# digest.
_STAGE_ORDER: Tuple[StageName, ...] = (
    "early_warning",
    "notification",
    "final_report",
)

# Stage durations measured from the timeline-open instant. One calendar
# month is interpreted as 30 days — see the module docstring for the
# rationale.
STAGE_DURATIONS: dict[StageName, timedelta] = {
    "early_warning": timedelta(hours=24),
    "notification": timedelta(hours=72),
    "final_report": timedelta(days=30),
}


def stages_in_order() -> Tuple[StageName, ...]:
    """Return the regulator-stage alphabet in canonical chronological order.

    The order is the NIS2 Article 23(4) cadence (24h → 72h → 1 month).
    Callers that iterate per-stage use this helper rather than reading
    the underlying tuple directly so the alphabet stays a single source
    of truth.
    """
    return _STAGE_ORDER


# ---------------------------------------------------------------------------
# Time-source assertions
# ---------------------------------------------------------------------------


def _require_utc(name: str, value: datetime) -> datetime:
    """Reject naive datetimes; normalise to UTC.

    The stage clock is the regulator-of-record clock — the workflow's
    audit trail records it; downstream consumers (F-CP-02) replay
    against it. A naive datetime would let a local-timezone wall clock
    drift the verdict by hours; a non-UTC aware datetime would let the
    same wall-clock instant carry different offsets across replays.
    Both fail closed here.
    """
    if not isinstance(value, datetime):
        raise TypeError(
            f"{name} must be a datetime, got {type(value).__name__}"
        )
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            f"{name} must be timezone-aware so the regulator clock has a "
            "deterministic absolute reference; got a naive datetime."
        )
    if value.utcoffset() != timedelta(0):
        # Normalise to UTC so the digest of a same-instant value is
        # stable regardless of the carrying offset. The semantic
        # instant is preserved; only the carrying offset changes.
        return value.astimezone(timezone.utc)
    return value


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def due_at(*, opened_at: datetime, stage: StageName) -> datetime:
    """Return the absolute deadline for ``stage`` measured from ``opened_at``.

    Args:
        opened_at: Timezone-aware datetime at which the incident
            timeline was opened (the workflow's ``open_timeline``
            action signalling the F-PT-02 pattern's start).
        stage: One of :data:`StageName`. Lookup is exhaustive — an
            unknown stage raises :class:`ValueError`.

    Returns:
        UTC-normalised :class:`datetime` at which the stage's
        regulator-submission window closes.
    """
    if stage not in STAGE_DURATIONS:
        raise ValueError(
            f"unknown stage {stage!r}; expected one of "
            f"{tuple(STAGE_DURATIONS)!r}"
        )
    return _require_utc("opened_at", opened_at) + STAGE_DURATIONS[stage]


def elapsed(*, opened_at: datetime, now: datetime) -> timedelta:
    """Return the elapsed time between ``opened_at`` and ``now``.

    Both arguments must be timezone-aware. The result is a regular
    :class:`timedelta`; negative values are returned as-is so a caller
    can detect a clock-of-record going backwards (the same shape an
    audit-trail anomaly takes).
    """
    return _require_utc("now", now) - _require_utc("opened_at", opened_at)


# ---------------------------------------------------------------------------
# StageWindow + StageBudget value objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StageWindow:
    """A regulator-submission window: open instant, due instant, duration.

    Attributes:
        stage: Closed-alphabet stage name.
        opened_at: UTC-normalised timeline-open instant.
        due_at: UTC-normalised deadline (opened_at + duration).
        duration: The configured stage duration. Carried so a caller
            inspecting the window does not have to look up
            :data:`STAGE_DURATIONS` separately.
    """

    stage: StageName
    opened_at: datetime
    due_at: datetime
    duration: timedelta


def stage_window(*, opened_at: datetime, stage: StageName) -> StageWindow:
    """Build a :class:`StageWindow` for ``stage`` from ``opened_at``."""
    opened = _require_utc("opened_at", opened_at)
    return StageWindow(
        stage=stage,
        opened_at=opened,
        due_at=due_at(opened_at=opened, stage=stage),
        duration=STAGE_DURATIONS[stage],
    )


@dataclass(frozen=True)
class StageBudget:
    """Remaining-time view of a stage window at a given ``now`` instant.

    Attributes:
        stage: Closed-alphabet stage name.
        opened_at: UTC-normalised timeline-open instant.
        due_at: UTC-normalised stage deadline.
        now: UTC-normalised reference instant the budget was evaluated
            against.
        remaining: ``due_at - now``. Negative when the window has
            already closed.
        is_overdue: True when ``remaining`` is non-positive.
    """

    stage: StageName
    opened_at: datetime
    due_at: datetime
    now: datetime
    remaining: timedelta
    is_overdue: bool


def stage_budget(
    *, opened_at: datetime, stage: StageName, now: datetime
) -> StageBudget:
    """Return a :class:`StageBudget` for ``stage`` evaluated at ``now``.

    The "remaining" arithmetic is on absolute timedeltas; an overrun
    surfaces as ``is_overdue=True`` and a negative ``remaining``.
    """
    window = stage_window(opened_at=opened_at, stage=stage)
    now_utc = _require_utc("now", now)
    remaining = window.due_at - now_utc
    return StageBudget(
        stage=stage,
        opened_at=window.opened_at,
        due_at=window.due_at,
        now=now_utc,
        remaining=remaining,
        is_overdue=remaining <= timedelta(0),
    )


# ---------------------------------------------------------------------------
# StageVerdict — replay-friendly "was the submission on time?" decision
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StageVerdict:
    """Replay-friendly on-time / overdue decision for a regulator submission.

    Frozen so the per-target compilers (n8n, Temporal, LangGraph) can
    pin against a single handle on the audit trail.

    Attributes:
        stage: Closed-alphabet stage name.
        opened_at: UTC-normalised timeline-open instant.
        submitted_at: UTC-normalised submission instant.
        due_at: UTC-normalised stage deadline.
        on_time: True iff ``submitted_at <= due_at``.
        slack: ``due_at - submitted_at``. Negative when the submission
            overran the window; the magnitude is the overrun.
        reasons: Ordered tuple naming every observation that fired.
        inputs_digest: Short hex digest over the canonical inputs so a
            replay-vs-original comparison is a single string-equal
            check on this field.
    """

    stage: StageName
    opened_at: datetime
    submitted_at: datetime
    due_at: datetime
    on_time: bool
    slack: timedelta
    reasons: Tuple[str, ...]
    inputs_digest: str


def _digest(
    stage: str, opened_at: datetime, submitted_at: datetime
) -> str:
    """Short hex digest over the canonical stage-clock inputs.

    Covers stage + opened_at + submitted_at; due_at and on_time are
    derived from these three, so a single string-equal check on the
    digest is sufficient to pin replay-vs-original. UTC ISO-8601
    canonicalisation so two equivalent-but-formatted-differently
    inputs yield the same digest.
    """
    payload = "\u001f".join(
        [
            stage,
            opened_at.isoformat(),
            submitted_at.isoformat(),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def verdict_for_submission(
    *,
    stage: StageName,
    opened_at: datetime,
    submitted_at: datetime,
) -> StageVerdict:
    """Apply the deterministic on-time / overdue decision.

    Args:
        stage: Closed-alphabet stage name. Unknown values raise
            :class:`ValueError` — the Literal type carries the contract
            at the boundary, but call sites that bypass type checking
            (e.g. a ``dict.get`` on raw input) would otherwise hit a
            KeyError; surface the failure as a domain error here.
        opened_at: Timezone-aware timeline-open instant.
        submitted_at: Timezone-aware submission instant.

    Returns:
        :class:`StageVerdict` carrying the on-time flag, the slack,
        every reason that fired, and a digest of the canonical inputs.

    Raises:
        ValueError: ``stage`` is not in :data:`STAGE_DURATIONS` or
            either datetime is naive.
        TypeError: Either datetime is not a :class:`datetime` instance.
    """
    if stage not in STAGE_DURATIONS:
        raise ValueError(
            f"unknown stage {stage!r}; expected one of "
            f"{tuple(STAGE_DURATIONS)!r}"
        )
    opened = _require_utc("opened_at", opened_at)
    submitted = _require_utc("submitted_at", submitted_at)
    window = stage_window(opened_at=opened, stage=stage)
    slack = window.due_at - submitted
    on_time = slack >= timedelta(0)

    reasons: list[str] = [
        f"stage={stage} window={STAGE_DURATIONS[stage]}",
        f"opened_at={opened.isoformat()}",
        f"due_at={window.due_at.isoformat()}",
        f"submitted_at={submitted.isoformat()}",
    ]
    if on_time:
        reasons.append(f"on_time=true slack={slack}")
    else:
        reasons.append(f"on_time=false overrun={-slack}")

    return StageVerdict(
        stage=stage,
        opened_at=opened,
        submitted_at=submitted,
        due_at=window.due_at,
        on_time=on_time,
        slack=slack,
        reasons=tuple(reasons),
        inputs_digest=_digest(stage, opened, submitted),
    )
