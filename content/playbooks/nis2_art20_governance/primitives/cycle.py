"""Governance-cycle resolution primitive (schedule_management_review).

Binds the operator's documented governance-cadence catalogue to the
current cycle key (``__governance_cycle__``) and records the resolved
management-body review slot as ``__review_id__``. Read-only against
the catalogue: no calendar entry is mutated -- the operator's
governance workflow owns the calendar surface; this step records the
resolved slot the review will occupy.

Ad-hoc-trigger branch (no scheduled slot available for the cycle) is
carried explicitly: ``review_id`` is empty in the returned envelope
and ``trigger`` is ``ad_hoc`` so downstream steps proceed against the
ad-hoc marker rather than short-circuiting.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
* **Determinism.** Same inputs => byte-identical output.
* **Public-bar safe.** Cycle-id, forum-id, meeting-id, and agenda-slot
  are matched against closed regexes; personal-name / credential-
  shaped strings fail loud at this boundary.
* **Read-only-by-contract.** No calendar-entry write is represented.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidGovernanceCycleError",
    "resolve_governance_cycle",
]


_CYCLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_FORUM_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_MEETING_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_AGENDA_SLOT_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_TRIGGERS = frozenset({"scheduled", "ad_hoc", "supervisory_request"})
_SCHEMA_VERSION = "1.0.0"
_STREAM = "nis2_art20_governance_cycle"


class InvalidGovernanceCycleError(ValueError):
    """Raised when the cycle inputs cannot produce a deterministic envelope."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidGovernanceCycleError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidGovernanceCycleError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _require_pattern(value: object, field: str, pattern: re.Pattern[str]) -> str:
    text = _canonical_text(value, field)
    if not pattern.match(text):
        raise InvalidGovernanceCycleError(
            f"{field} {text!r} does not match the schema pattern"
        )
    return text


def resolve_governance_cycle(
    governance_cycle: str,
    trigger: str,
    forum_id: str | None = None,
    meeting_id: str | None = None,
    agenda_slot: str | None = None,
    meeting_date_iso: str | None = None,
) -> dict:
    """Resolve the current governance cycle against the operator catalogue.

    Args:
        governance_cycle: Identifier of the management-body cybersecurity
            governance cycle this run discharges (``__governance_cycle__``).
        trigger: Which cadence branch fires this run. One of
            ``scheduled``, ``ad_hoc``, ``supervisory_request``.
        forum_id: Optional role-shaped identifier of the management-body
            forum. Required for the ``scheduled`` branch, forbidden for
            ``ad_hoc``.
        meeting_id: Optional identifier of the scheduled review meeting.
            Required for the ``scheduled`` branch.
        agenda_slot: Optional slug of the agenda slot the cybersecurity
            review will occupy. Required for the ``scheduled`` branch.
        meeting_date_iso: Optional ISO-8601 date the meeting is scheduled
            for. Required for the ``scheduled`` branch.

    Returns:
        JSON-native envelope with ``schema_version``, ``stream``,
        ``governance_cycle``, ``trigger``, ``review_id`` (empty for
        ad-hoc / supervisory_request branches), and the optional
        ``forum_id``, ``meeting_id``, ``agenda_slot``, ``meeting_date``
        the scheduled branch pins.

    Raises:
        InvalidGovernanceCycleError: any input fails validation or the
            per-branch invariants are violated.
    """
    cycle = _require_pattern(governance_cycle, "governance_cycle", _CYCLE_ID_RE)
    trig = _canonical_text(trigger, "trigger")
    if trig not in _TRIGGERS:
        raise InvalidGovernanceCycleError(
            f"trigger {trig!r} not in {sorted(_TRIGGERS)}"
        )

    envelope: dict = {
        "schema_version": _SCHEMA_VERSION,
        "stream": _STREAM,
        "governance_cycle": cycle,
        "trigger": trig,
        "review_id": "",
    }

    if trig == "scheduled":
        if forum_id is None or meeting_id is None or agenda_slot is None or meeting_date_iso is None:
            raise InvalidGovernanceCycleError(
                "scheduled trigger requires forum_id, meeting_id, "
                "agenda_slot, and meeting_date_iso"
            )
        forum = _require_pattern(forum_id, "forum_id", _FORUM_ID_RE)
        meeting = _require_pattern(meeting_id, "meeting_id", _MEETING_ID_RE)
        slot = _require_pattern(agenda_slot, "agenda_slot", _AGENDA_SLOT_RE)
        date_text = _canonical_text(meeting_date_iso, "meeting_date_iso")
        if not _ISO_DATE_RE.match(date_text):
            raise InvalidGovernanceCycleError(
                f"meeting_date_iso {date_text!r} is not 'YYYY-MM-DD'"
            )
        envelope["review_id"] = meeting
        envelope["forum_id"] = forum
        envelope["meeting_id"] = meeting
        envelope["agenda_slot"] = slot
        envelope["meeting_date"] = date_text
    else:
        # ad_hoc / supervisory_request branches carry empty review_id
        # explicitly. Any scheduled-branch fields supplied are rejected
        # so the branch invariant is loud.
        for extra_field, extra_value in (
            ("forum_id", forum_id),
            ("meeting_id", meeting_id),
            ("agenda_slot", agenda_slot),
            ("meeting_date_iso", meeting_date_iso),
        ):
            if extra_value is not None:
                raise InvalidGovernanceCycleError(
                    f"{trig} trigger must not supply {extra_field}"
                )

    return envelope
