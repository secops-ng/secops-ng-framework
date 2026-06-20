"""Review-schedule derivation primitive (schedule-review).

Pure derivation: per obligation, derive the next-review-due timestamp
deterministically from
``(last_reviewed_at, cadence, operator-policy fallback cadence)`` and
emit one ``review_schedule[]`` entry per obligation paired one-to-one
with ``obligations[]``. No network, no clock; the ``captured_at``
anchor on the artifact and the operator's review-policy are the only
time sources.

The state classifier is intentionally minimal at this layer — review
state is derived from the relationship between the captured_at anchor
and the next_review_due_at timestamp:

* ``unknown``   — no last_reviewed_at on file (newly extracted).
* ``current``   — next_review_due_at > captured_at + due_soon_window.
* ``due_soon``  — next_review_due_at within due_soon_window of captured_at.
* ``overdue``   — captured_at > next_review_due_at.

The ``waived`` state is operator-driven and arrives via the policy's
``waived_obligation_ids`` list. The EXTEND-schema sibling card tightens
the waiver / deferral envelope; this primitive returns the SKELETON
enum as-is.

Design constraints
------------------

* **Pure / replayable.** No network, no clock, no LLMs.
* **Deterministic.** Output is paired one-to-one with the sorted
  obligation set so two replays of the same inputs collapse to
  byte-identical bytes.
* **Sovereign-stack neutral.** Policy is operator-side JSON-native;
  no vendor SDK is imported.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Any

__all__ = [
    "InvalidReviewScheduleError",
    "schedule_reviews",
]


_OBLIGATION_ID_RE = re.compile(r"^obligation\.[a-z][a-z0-9_-]*$")
_ISO_DURATION_RE = re.compile(
    r"^P([0-9]+Y)?([0-9]+M)?([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+S)?)?$"
)
_ISO_Z_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")

# Approximate-month / approximate-year handling deliberately avoids
# operator-locale ambiguity: months map to 30 days, years to 365 days.
# Cadence is contractual-coarse, not calendar-accurate; the EXTEND-schema
# sibling pins a richer cadence envelope.
_SECONDS_PER_UNIT = {
    "Y": 365 * 24 * 3600,
    "M": 30 * 24 * 3600,
    "D": 24 * 3600,
    "H": 3600,
    "MIN": 60,
    "S": 1,
}


class InvalidReviewScheduleError(ValueError):
    """Raised when the inputs cannot produce a valid review schedule."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidReviewScheduleError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidReviewScheduleError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _parse_iso_z(text: str, field: str) -> datetime:
    if not _ISO_Z_RE.match(text):
        raise InvalidReviewScheduleError(
            f"{field} {text!r} is not ISO-8601 UTC 'YYYY-MM-DDTHH:MM:SSZ'"
        )
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )


def _duration_to_seconds(duration: str, field: str) -> int:
    """Convert an ISO-8601 duration to seconds.

    Months default to 30 days, years to 365 days. The cadence is
    contractual-coarse, not calendar-accurate; an EXTEND-schema sibling
    will tighten this once the cross-jurisdictional cadence envelope is
    pinned.
    """
    if not _ISO_DURATION_RE.match(duration):
        raise InvalidReviewScheduleError(
            f"{field} {duration!r} is not an ISO-8601 duration"
        )
    total = 0
    head, _, tail = duration[1:].partition("T")
    for token, unit in _split_components(head, in_time=False):
        total += token * _SECONDS_PER_UNIT[unit]
    for token, unit in _split_components(tail, in_time=True):
        total += token * _SECONDS_PER_UNIT[unit]
    if total < 0:
        raise InvalidReviewScheduleError(
            f"{field} {duration!r} resolved to a negative duration"
        )
    return total


def _split_components(segment: str, in_time: bool) -> list[tuple[int, str]]:
    """Walk an ISO-8601 duration head/tail, yielding (n, unit) pairs.

    Date-side units: Y, M, D. Time-side units: H, M, S. The duplicated
    'M' is disambiguated by which segment it appears in.
    """
    out: list[tuple[int, str]] = []
    buf = ""
    for ch in segment:
        if ch.isdigit():
            buf += ch
            continue
        if not buf:
            raise InvalidReviewScheduleError(
                f"malformed ISO-8601 duration segment {segment!r}"
            )
        if in_time and ch == "M":
            out.append((int(buf), "MIN"))
        elif ch in ("Y", "M", "D", "H", "S"):
            out.append((int(buf), ch))
        else:
            raise InvalidReviewScheduleError(
                f"unknown ISO-8601 duration unit {ch!r} in {segment!r}"
            )
        buf = ""
    if buf:
        raise InvalidReviewScheduleError(
            f"trailing digits {buf!r} in ISO-8601 duration segment "
            f"{segment!r}"
        )
    return out


def _due_state(
    captured_at: datetime,
    next_due_at: datetime,
    due_soon_window_seconds: int,
    last_reviewed_at: str | None,
) -> str:
    if last_reviewed_at is None:
        return "unknown"
    if captured_at > next_due_at:
        return "overdue"
    if (next_due_at - captured_at).total_seconds() <= due_soon_window_seconds:
        return "due_soon"
    return "current"


def schedule_reviews(
    obligations: list,
    review_policy: dict,
    captured_at: str,
) -> list[dict[str, Any]]:
    """Build the canonical ``review_schedule[]`` array.

    Inputs
    ------
    obligations
        Output of
        :func:`...primitives.obligations.extract_obligations` — the
        canonical sorted obligation set.
    review_policy
        Operator-supplied JSON-native object. Required shape::

            {
              "fallback_cadence": "P1Y",                     # ISO-8601 duration
              "due_soon_window": "P30D",                     # ISO-8601 duration
              "last_reviewed_at": {                          # optional
                "obligation.<id>": "YYYY-MM-DDTHH:MM:SSZ",
                ...
              },
              "waived_obligation_ids": ["obligation.<id>"]   # optional
            }

    captured_at
        ISO-8601 UTC ``...Z`` timestamp anchor — same value as the
        artifact-level ``captured_at``. The schedule is derived
        relative to this anchor.

    Returns
    -------
    JSON-native list of review records, one per obligation, in the
    same order as ``obligations[]`` (matching the schema's
    one-to-one pairing requirement).
    """
    if not isinstance(obligations, list) or not obligations:
        raise InvalidReviewScheduleError(
            "obligations must be a non-empty list"
        )
    if not isinstance(review_policy, dict):
        raise InvalidReviewScheduleError(
            f"review_policy must be an object, got "
            f"{type(review_policy).__name__}"
        )

    fallback_cadence = _canonical_text(
        review_policy.get("fallback_cadence"),
        "review_policy.fallback_cadence",
    )
    fallback_seconds = _duration_to_seconds(
        fallback_cadence, "review_policy.fallback_cadence"
    )
    due_soon_window = _canonical_text(
        review_policy.get("due_soon_window"),
        "review_policy.due_soon_window",
    )
    due_soon_seconds = _duration_to_seconds(
        due_soon_window, "review_policy.due_soon_window"
    )

    last_reviewed_at_map: dict[str, str] = {}
    raw_last = review_policy.get("last_reviewed_at", {})
    if not isinstance(raw_last, dict):
        raise InvalidReviewScheduleError(
            "review_policy.last_reviewed_at must be an object (mapping "
            "obligation_id -> ISO-8601 UTC timestamp) when present"
        )
    for key, value in raw_last.items():
        oid = _canonical_text(key, "review_policy.last_reviewed_at[*]")
        if not _OBLIGATION_ID_RE.match(oid):
            raise InvalidReviewScheduleError(
                f"review_policy.last_reviewed_at key {key!r} is not a "
                "role-shaped obligation_id"
            )
        ts = _canonical_text(
            value, f"review_policy.last_reviewed_at[{oid!r}]"
        )
        _parse_iso_z(ts, f"review_policy.last_reviewed_at[{oid!r}]")
        last_reviewed_at_map[oid] = ts

    waived_ids: set[str] = set()
    raw_waived = review_policy.get("waived_obligation_ids", [])
    if not isinstance(raw_waived, list):
        raise InvalidReviewScheduleError(
            "review_policy.waived_obligation_ids must be a list when "
            "present"
        )
    for index, entry in enumerate(raw_waived):
        wid = _canonical_text(
            entry, f"review_policy.waived_obligation_ids[{index}]"
        )
        if not _OBLIGATION_ID_RE.match(wid):
            raise InvalidReviewScheduleError(
                f"review_policy.waived_obligation_ids[{index}] {wid!r} is "
                "not a role-shaped obligation_id"
            )
        waived_ids.add(wid)

    anchor = _parse_iso_z(captured_at, "captured_at")

    out: list[dict[str, Any]] = []
    for index, obligation in enumerate(obligations):
        if not isinstance(obligation, dict):
            raise InvalidReviewScheduleError(
                f"obligations[{index}] must be an object"
            )
        oid = obligation.get("obligation_id")
        if not isinstance(oid, str) or not _OBLIGATION_ID_RE.match(oid):
            raise InvalidReviewScheduleError(
                f"obligations[{index}].obligation_id {oid!r} is not "
                "role-shaped"
            )

        cadence = obligation.get("cadence")
        if cadence is None:
            cadence_seconds = fallback_seconds
        else:
            cadence_seconds = _duration_to_seconds(
                cadence, f"obligations[{index}].cadence"
            )

        last_reviewed_at = last_reviewed_at_map.get(oid)
        if last_reviewed_at is not None:
            base = _parse_iso_z(
                last_reviewed_at,
                f"review_policy.last_reviewed_at[{oid!r}]",
            )
        else:
            base = anchor
        next_due = base + timedelta(seconds=cadence_seconds)
        next_due_text = next_due.strftime("%Y-%m-%dT%H:%M:%SZ")

        if oid in waived_ids:
            state = "waived"
        else:
            state = _due_state(
                anchor, next_due, due_soon_seconds, last_reviewed_at
            )

        entry: dict[str, Any] = {
            "obligation_id": oid,
            "state": state,
            "next_review_due_at": next_due_text,
        }
        if last_reviewed_at is not None:
            entry["last_reviewed_at"] = last_reviewed_at
        else:
            entry["last_reviewed_at"] = None
        out.append(entry)

    return out
