"""BCM event-declaration primitive (detect_and_declare_bcm_event step).

Canonicalises a business-continuity trigger received on the operator's
event-declaration surface into the event envelope the lifecycle
correlates on, and derives ``__event_id__`` deterministically from the
trigger content — the same trigger re-received resolves to the same
event, so declaration dedup is a property of the derivation.

Design constraints
------------------

* **Pure / replayable.** No clock reads: ``declared_ts`` is the
  supplied declaration instant the NIS2 Art. 23 clock anchors on
  (24h early warning / 72h incident notification / one-month final
  report), stamped by the declaring surface, validated here.
* **Closed trigger vocabulary.** The step is authored against the
  major-outage escalation (incident-management lane), the ransomware
  containment escalation (containment lane), the upstream-dependency
  failure signal, and the facility-loss declaration; anything else is
  the declaring surface mislabelling its escalation.
* **Declaration does not read the plan register.** Whether a plan is
  on file is the activation step's question — a continuity event with
  no plan on file is declared and reported like any other (roadmap
  acceptance criterion), so this primitive takes no register input at
  all.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

__all__ = [
    "InvalidBcmTriggerError",
    "declare_bcm_event",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_INSTANT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

_TRIGGER_CLASSES = frozenset(
    {
        "major_outage_escalation",
        "ransomware_containment_escalation",
        "upstream_dependency_failure",
        "facility_loss_declaration",
    }
)


class InvalidBcmTriggerError(ValueError):
    """Raised when the raw trigger cannot produce a valid event."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidBcmTriggerError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidBcmTriggerError(f"{field} is empty after canonicalisation")
    if not _POINTER_RE.match(normalised):
        raise InvalidBcmTriggerError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def declare_bcm_event(raw_trigger: dict) -> dict:
    """Declare one business-continuity event from one trigger.

    Inputs
    ------
    raw_trigger
        Declaring-surface JSON-native record. Required keys:
        ``trigger_class`` (one of ``major_outage_escalation``,
        ``ransomware_containment_escalation``,
        ``upstream_dependency_failure``,
        ``facility_loss_declaration``), ``affected_service``
        (role-shaped service id), ``source_ref`` (role-shaped pointer
        to the escalating lane's record — the incident, the containment
        case, the dependency alert, the facility declaration), and
        ``declared_ts`` (Zulu instant of the declaration — the
        Art. 23 anchor).

    Returns
    -------
    JSON-native event envelope::

        {
            "event_id": "bcm-<24 hex>",
            "trigger_class": "...",
            "affected_service": "...",
            "source_ref": "...",
            "event_declared_ts": "YYYY-MM-DDTHH:MM:SSZ"
        }
    """
    if not isinstance(raw_trigger, dict):
        raise InvalidBcmTriggerError(
            f"raw_trigger must be an object, got {type(raw_trigger).__name__}"
        )
    trigger_class = raw_trigger.get("trigger_class")
    if not isinstance(trigger_class, str) or trigger_class not in _TRIGGER_CLASSES:
        raise InvalidBcmTriggerError(
            f"raw_trigger.trigger_class {trigger_class!r} is not one of "
            f"{sorted(_TRIGGER_CLASSES)}"
        )
    declared = raw_trigger.get("declared_ts")
    if not isinstance(declared, str) or not _INSTANT_RE.match(
        unicodedata.normalize("NFKC", declared).strip()
    ):
        raise InvalidBcmTriggerError(
            f"raw_trigger.declared_ts {declared!r} is not a Zulu instant "
            "(YYYY-MM-DDTHH:MM:SSZ); the Art. 23 clock cannot anchor on it"
        )

    body = {
        "trigger_class": trigger_class,
        "affected_service": _canonical_pointer(
            raw_trigger.get("affected_service"), "raw_trigger.affected_service"
        ),
        "source_ref": _canonical_pointer(
            raw_trigger.get("source_ref"), "raw_trigger.source_ref"
        ),
        "event_declared_ts": unicodedata.normalize("NFKC", declared).strip(),
    }
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {"event_id": "bcm-" + digest[:24], **body}
