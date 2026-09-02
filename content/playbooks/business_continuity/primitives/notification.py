"""Competent-authority notification primitive (notify_competent_authority step).

Composes either the NIS2 Art. 23 notification envelope (when the event
crossed the significance threshold) or the locally-logged
no-notification determination (when it did not). Delivery to the
per-Member-State competent-authority surface is the compile target's
adapter concern; what is deterministic here is the Art. 23 cascade
arithmetic and the two mutually exclusive record shapes.

Design constraints
------------------

* **Pure / replayable.** The Art. 23 clock anchors on the supplied
  declaration instant: 24 hours (early warning) and 72 hours (incident
  notification) are exact second arithmetic; the one-month final
  report uses calendar-month arithmetic with the end-of-month clamp —
  the same convention the DSR Article 12(3) clock pins.
* **The two dispositions are exclusive and complete.** A significant
  incident composes a notification for one of the three closed phases
  with a full preliminary assessment; a non-significant one composes
  the no-notification determination, which requires a non-empty
  rationale — **an unjustified no-notification is not representable**,
  because the locally-logged determination is precisely the record an
  Art. 32 supervisory query reads.
* **Cross-border effect is a real boolean.** A string ``"false"`` is
  truthy and would assert cross-border effect on a domestic outage.
"""

from __future__ import annotations

import calendar as _calendar
import hashlib
import json
import re
import unicodedata
from datetime import datetime, timedelta

__all__ = [
    "InvalidNotificationInputError",
    "compose_authority_notification",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_INSTANT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_INSTANT_FMT = "%Y-%m-%dT%H:%M:%SZ"

# The Art. 23 cascade: phase -> deadline derivation.
_PHASES = ("early_warning", "incident_notification", "final_report")
_HOUR_DEADLINES = {"early_warning": 24, "incident_notification": 72}


class InvalidNotificationInputError(ValueError):
    """Raised when the inputs cannot compose a lawful record."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidNotificationInputError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidNotificationInputError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _canonical_pointer(value: object, field: str) -> str:
    text = _canonical_text(value, field)
    if not _POINTER_RE.match(text):
        raise InvalidNotificationInputError(
            f"{field} {text!r} does not match the role-shaped pointer "
            "pattern; free text is out of scope per AGENTS.md §3"
        )
    return text


def _parse_instant(value: object, field: str) -> datetime:
    text = _canonical_text(value, field)
    if not _INSTANT_RE.match(text):
        raise InvalidNotificationInputError(
            f"{field} {text!r} is not a Zulu instant (YYYY-MM-DDTHH:MM:SSZ)"
        )
    try:
        return datetime.strptime(text, _INSTANT_FMT)
    except ValueError as exc:
        raise InvalidNotificationInputError(
            f"{field} {text!r} is not a real calendar instant: {exc}"
        ) from exc


def _add_calendar_month(anchor: datetime) -> datetime:
    month_index = anchor.year * 12 + anchor.month  # zero-based index + 1 month
    year, month_zero = divmod(month_index, 12)
    month = month_zero + 1
    day = min(anchor.day, _calendar.monthrange(year, month)[1])
    return anchor.replace(year=year, month=month, day=day)


def compose_authority_notification(
    event_id: str,
    event_declared_ts: str,
    significant_incident: bool,
    phase: str | None = None,
    assessment: dict | None = None,
    no_notification_rationale: str | None = None,
) -> dict:
    """Compose the Art. 23 record for one declared event.

    Inputs
    ------
    event_id, event_declared_ts
        The declaration envelope's correlation key and Art. 23 anchor.
    significant_incident
        The activation step's threshold verdict
        (``__significant_incident__``) as a real boolean.
    phase
        Required when significant: one of ``early_warning`` (24h),
        ``incident_notification`` (72h), ``final_report`` (one
        calendar month, end-of-month clamped). Forbidden otherwise.
    assessment
        Required when significant: ``preliminary_assessment`` and
        ``impact_scope`` (non-empty text, carried opaquely) and
        ``cross_border_effect`` (real boolean). Forbidden otherwise.
    no_notification_rationale
        Required when NOT significant: the non-empty rationale for the
        locally-logged determination. Forbidden otherwise.

    Returns
    -------
    JSON-native record — one of two exclusive shapes::

        {"disposition": "notification",
         "notification_ref": "bcm-not-<24 hex>", "event_id": "...",
         "event_declared_ts": "...", "phase": "...",
         "phase_deadline": "...", "preliminary_assessment": "...",
         "impact_scope": "...", "cross_border_effect": <bool>}

        {"disposition": "no_notification_determination",
         "notification_ref": "", "determination_ref":
         "bcm-nnd-<24 hex>", "event_id": "...",
         "event_declared_ts": "...", "rationale": "..."}
    """
    event = _canonical_pointer(event_id, "event_id")
    anchor = _parse_instant(event_declared_ts, "event_declared_ts")
    declared = anchor.strftime(_INSTANT_FMT)
    if not isinstance(significant_incident, bool):
        raise InvalidNotificationInputError(
            "significant_incident must be a boolean, got "
            f"{type(significant_incident).__name__} — a string 'false' is "
            "truthy and would notify on a non-significant event"
        )

    if significant_incident:
        if no_notification_rationale is not None:
            raise InvalidNotificationInputError(
                "a significant incident composes a notification; a "
                "no-notification rationale is not representable here"
            )
        if not isinstance(phase, str) or phase not in _PHASES:
            raise InvalidNotificationInputError(
                f"phase {phase!r} is not one of {list(_PHASES)}"
            )
        if not isinstance(assessment, dict):
            raise InvalidNotificationInputError(
                "assessment must be an object with preliminary_assessment, "
                "impact_scope and cross_border_effect"
            )
        preliminary = _canonical_text(
            assessment.get("preliminary_assessment"),
            "assessment.preliminary_assessment",
        )
        impact = _canonical_text(
            assessment.get("impact_scope"), "assessment.impact_scope"
        )
        cross_border = assessment.get("cross_border_effect")
        if not isinstance(cross_border, bool):
            raise InvalidNotificationInputError(
                "assessment.cross_border_effect must be a boolean, got "
                f"{type(cross_border).__name__}"
            )

        if phase in _HOUR_DEADLINES:
            deadline = anchor + timedelta(hours=_HOUR_DEADLINES[phase])
        else:
            deadline = _add_calendar_month(anchor)

        digest = hashlib.sha256(
            (event + "|" + phase + "|" + deadline.strftime(_INSTANT_FMT)).encode(
                "utf-8"
            )
        ).hexdigest()
        return {
            "disposition": "notification",
            "notification_ref": "bcm-not-" + digest[:24],
            "event_id": event,
            "event_declared_ts": declared,
            "phase": phase,
            "phase_deadline": deadline.strftime(_INSTANT_FMT),
            "preliminary_assessment": preliminary,
            "impact_scope": impact,
            "cross_border_effect": cross_border,
        }

    if phase is not None or assessment is not None:
        raise InvalidNotificationInputError(
            "a non-significant event composes the no-notification "
            "determination; a notification phase or assessment is not "
            "representable here"
        )
    rationale = _canonical_text(
        no_notification_rationale, "no_notification_rationale"
    )
    body = {
        "event_id": event,
        "event_declared_ts": declared,
        "rationale": rationale,
    }
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {
        "disposition": "no_notification_determination",
        "notification_ref": "",
        "determination_ref": "bcm-nnd-" + digest[:24],
        **body,
    }
