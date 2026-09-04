"""Owner-notification composition primitive (notify step).

Composes the notification that delivers the evidence reference to the
incident-management owner. The composition / delivery split from the
notify-lane precedent applies: this primitive composes the payload and
resolves the urgency; delivering it along the operator's pre-bound
channel (ticketing system, chat thread, page-out roster) is the
compile target's messaging surface.

Design constraints
------------------

* **Pure / replayable.** Same evidence reference and outcome ⇒
  byte-identical notification.
* **Urgency follows the restoration outcome (pinned by tests).** A
  false ``service_restored`` pages (the incident is live and the next
  mitigation lever is on the owner); a true one informs. The variable
  contract makes this explicit: the notification "carries the
  restoration outcome so a false __service_restored__ pages with
  appropriate urgency".
* **Real booleans only.** ``service_restored`` arrives as a workflow
  boolean; a string ``"false"`` is truthy and would demote a live
  incident to an informational note, so strings are refused outright.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidNotificationInputError",
    "compose_owner_notification",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")


class InvalidNotificationInputError(ValueError):
    """Raised when the notification inputs cannot compose a payload."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidNotificationInputError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidNotificationInputError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidNotificationInputError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def compose_owner_notification(
    evidence_id: str,
    protected_service: str,
    service_restored: bool,
    owner_channel: str,
) -> dict:
    """Compose the owner notification for one availability incident.

    Inputs
    ------
    evidence_id
        The published evidence record's id (``__evidence_id__``).
    protected_service
        Role-shaped service id (``__protected_service__``).
    service_restored
        The validate step's outcome (``__service_restored__``) as a
        real boolean.
    owner_channel
        Role-shaped reference to the operator's pre-bound delivery
        channel (ticketing system, chat thread, page-out roster).

    Returns
    -------
    JSON-native notification payload::

        {
            "channel_ref": "...",
            "urgency": "page" | "inform",
            "evidence_id": "...",
            "service_restored": <bool>,
            "headline": "...",
            "body": "..."
        }
    """
    evidence = _canonical_pointer(evidence_id, "evidence_id")
    service = _canonical_pointer(protected_service, "protected_service")
    channel = _canonical_pointer(owner_channel, "owner_channel")
    if not isinstance(service_restored, bool):
        raise InvalidNotificationInputError(
            "service_restored must be a boolean, got "
            f"{type(service_restored).__name__} — a string 'false' is "
            "truthy and would demote a live incident"
        )

    if service_restored:
        urgency = "inform"
        headline = (
            "availability incident on " + service + " — service restored"
        )
        body = (
            "Service "
            + service
            + " is observed back inside its availability objective. "
            "Evidence record " + evidence + " is published for the "
            "NIS2 Art. 21(2)(b) review trail."
        )
    else:
        urgency = "page"
        headline = (
            "availability incident on "
            + service
            + " — NOT restored, next mitigation lever needed"
        )
        body = (
            "Service "
            + service
            + " has not recovered inside the validation window. "
            "Evidence record " + evidence + " carries the breach "
            "detail; engage the next mitigation lever (escalate "
            "scrubbing tier, expand rate-limit scope, manual failover)."
        )

    return {
        "channel_ref": channel,
        "urgency": urgency,
        "evidence_id": evidence,
        "service_restored": service_restored,
        "headline": headline,
        "body": body,
    }
