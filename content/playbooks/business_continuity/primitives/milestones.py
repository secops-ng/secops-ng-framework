"""Lifecycle milestone-record primitives (all steps).

The roadmap acceptance criterion: each lifecycle milestone emits an
OCSF record keyed to the event id — API Activity (class_uid 6003) at
the five operational milestones and Incident Finding (class_uid 2005)
at the notification and review milestones, the house binding corrected
from an invented availability class by #875/#877 and pinned on
``mappings.yaml``. These composers produce those records
deterministically; the per-target emitters wire them.

Design constraints
------------------

* **Pure / replayable.** ``occurred_ts`` is the supplied milestone
  instant; the epoch-millisecond conversion is arithmetic on it, not a
  clock read.
* **Closed milestone vocabularies.** The 6003 surface covers exactly
  the five operational steps the mapping enumerates
  (detect-and-declare, activate-plan, isolate, switch-to-backup,
  restore-and-verify); the 2005 surface covers exactly
  notify-competent-authority (activity Create — the notification
  record enters the reporting surface) and post-incident-review
  (activity Close — the lessons-learned record closes it).
* **Field shape follows the telemetry artifact.** The emitted fields
  are the ``fields_used`` subset of
  ``telemetry.ocsf.api_activity@v1`` this playbook exercises:
  ``time``, ``activity_id``, ``api.operation``, ``api.service.name``,
  ``resources`` (the event id) and ``status_id`` (1 success /
  2 failure from a real-boolean outcome).
"""

from __future__ import annotations

import calendar as _calendar
import re
import unicodedata
from datetime import datetime

__all__ = [
    "InvalidMilestoneInputError",
    "compose_incident_finding_record",
    "compose_milestone_record",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_INSTANT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_INSTANT_FMT = "%Y-%m-%dT%H:%M:%SZ"

_SERVICE_NAME = "playbook.business_continuity@v1"

_API_ACTIVITY_MILESTONES = frozenset(
    {
        "detect_and_declare_bcm_event",
        "activate_bcm_plan",
        "isolate_affected_systems",
        "switch_to_backup",
        "restore_and_verify",
    }
)
# OCSF Incident Finding activities: the notification record is created
# on the reporting surface (1 = Create); the PIR closes it (3 = Close).
_INCIDENT_FINDING_MILESTONES = {
    "notify_competent_authority": 1,
    "post_incident_review": 3,
}


class InvalidMilestoneInputError(ValueError):
    """Raised when a milestone record cannot be composed."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidMilestoneInputError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidMilestoneInputError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidMilestoneInputError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def _epoch_ms(value: object, field: str) -> int:
    if not isinstance(value, str):
        raise InvalidMilestoneInputError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    instant = unicodedata.normalize("NFKC", value).strip()
    if not _INSTANT_RE.match(instant):
        raise InvalidMilestoneInputError(
            f"{field} {instant!r} is not a Zulu instant "
            "(YYYY-MM-DDTHH:MM:SSZ)"
        )
    try:
        parsed = datetime.strptime(instant, _INSTANT_FMT)
    except ValueError as exc:
        raise InvalidMilestoneInputError(
            f"{field} {instant!r} is not a real calendar instant: {exc}"
        ) from exc
    return _calendar.timegm(parsed.timetuple()) * 1000


def compose_milestone_record(
    event_id: str, milestone: str, occurred_ts: str, succeeded: bool
) -> dict:
    """Compose one OCSF API Activity (6003) milestone record.

    Inputs
    ------
    event_id
        The declaration envelope's correlation key (``__event_id__``).
    milestone
        One of the five operational milestones the mapping enumerates.
    occurred_ts
        Zulu instant the milestone occurred (adapter-stamped).
    succeeded
        Real-boolean milestone outcome; maps to OCSF ``status_id``
        1 (Success) / 2 (Failure).

    Returns
    -------
    JSON-native OCSF-shaped record (the ``fields_used`` subset)::

        {
            "class_uid": 6003, "class_name": "API Activity",
            "category_uid": 6, "activity_id": 99,
            "time": <epoch ms>,
            "api": {"operation": "<milestone>",
                    "service": {"name": "playbook.business_continuity@v1"}},
            "resources": [{"type": "bcm_event", "uid": "<event id>"}],
            "status_id": 1 | 2
        }
    """
    event = _canonical_pointer(event_id, "event_id")
    if not isinstance(milestone, str) or milestone not in _API_ACTIVITY_MILESTONES:
        raise InvalidMilestoneInputError(
            f"milestone {milestone!r} is not one of the API Activity "
            f"milestones {sorted(_API_ACTIVITY_MILESTONES)}"
        )
    if not isinstance(succeeded, bool):
        raise InvalidMilestoneInputError(
            f"succeeded must be a boolean, got {type(succeeded).__name__}"
        )
    return {
        "class_uid": 6003,
        "class_name": "API Activity",
        "category_uid": 6,
        "activity_id": 99,
        "time": _epoch_ms(occurred_ts, "occurred_ts"),
        "api": {
            "operation": milestone,
            "service": {"name": _SERVICE_NAME},
        },
        "resources": [{"type": "bcm_event", "uid": event}],
        "status_id": 1 if succeeded else 2,
    }


def compose_incident_finding_record(
    event_id: str, milestone: str, occurred_ts: str, record_ref: str
) -> dict:
    """Compose one OCSF Incident Finding (2005) milestone record.

    Inputs
    ------
    event_id
        The declaration envelope's correlation key.
    milestone
        ``notify_competent_authority`` (activity 1, Create) or
        ``post_incident_review`` (activity 3, Close).
    occurred_ts
        Zulu instant the milestone occurred (adapter-stamped).
    record_ref
        The role-shaped reference the milestone produced — the
        notification / determination ref, or the PIR ref.

    Returns
    -------
    JSON-native OCSF-shaped record::

        {
            "class_uid": 2005, "class_name": "Incident Finding",
            "category_uid": 2, "activity_id": 1 | 3,
            "time": <epoch ms>,
            "finding_info": {"uid": "<record ref>",
                             "title": "<milestone>"},
            "resources": [{"type": "bcm_event", "uid": "<event id>"}],
            "status_id": 1
        }
    """
    event = _canonical_pointer(event_id, "event_id")
    if (
        not isinstance(milestone, str)
        or milestone not in _INCIDENT_FINDING_MILESTONES
    ):
        raise InvalidMilestoneInputError(
            f"milestone {milestone!r} is not one of the Incident Finding "
            f"milestones {sorted(_INCIDENT_FINDING_MILESTONES)}"
        )
    ref = _canonical_pointer(record_ref, "record_ref")
    return {
        "class_uid": 2005,
        "class_name": "Incident Finding",
        "category_uid": 2,
        "activity_id": _INCIDENT_FINDING_MILESTONES[milestone],
        "time": _epoch_ms(occurred_ts, "occurred_ts"),
        "finding_info": {"uid": ref, "title": milestone},
        "resources": [{"type": "bcm_event", "uid": event}],
        "status_id": 1,
    }
