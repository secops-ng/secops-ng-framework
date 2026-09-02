"""Post-incident-review record primitive (post_incident_review step).

Composes the audit-evident PIR record — lessons learned, corrective
actions, plan revisions — keyed to the event id. Persisting it on the
operator's evidence store is the compile target's adapter concern.

Design constraints
------------------

* **Lessons are mandatory, revisions are not.** A review with no
  lesson recorded is not a review; corrective actions and plan
  revisions may legitimately be empty (an exemplary run teaches
  without changing anything).
* **Running without a plan is marked, never hidden.** When the event
  ran with no plan on file, the record carries the
  ``ran_without_plan`` marker — the machine-readable hook the
  accountability posture and any Art. 23 final-report supplement or
  Art. 32 information request reads.
* **Content-derived identity.** ``__pir_ref__`` is ``bcm-pir-`` + 24
  hex over the record body, so re-persisting the same review is
  idempotent against the evidence store.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

__all__ = [
    "InvalidPirRecordError",
    "compose_pir_record",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")


class InvalidPirRecordError(ValueError):
    """Raised when the inputs cannot compose a review record."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidPirRecordError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidPirRecordError(f"{field} is empty after canonicalisation")
    return normalised


def _canonical_pointer(value: object, field: str) -> str:
    text = _canonical_text(value, field)
    if not _POINTER_RE.match(text):
        raise InvalidPirRecordError(
            f"{field} {text!r} does not match the role-shaped pointer "
            "pattern; free text is out of scope per AGENTS.md §3"
        )
    return text


def compose_pir_record(
    event_id: str,
    plan_on_file: bool,
    lessons_learned: list,
    corrective_actions: list,
    plan_revisions: list,
    linked_refs: dict | None = None,
) -> dict:
    """Compose the post-incident-review record for one event.

    Inputs
    ------
    event_id
        The declaration envelope's correlation key.
    plan_on_file
        The activation step's finding, as a real boolean; ``False``
        stamps the ``ran_without_plan`` marker.
    lessons_learned
        Non-empty list of non-empty lesson texts.
    corrective_actions
        List (possibly empty) of objects with ``action`` (non-empty
        text) and ``owner_ref`` (role-shaped).
    plan_revisions
        List (possibly empty) of non-empty revision texts surfaced by
        the event.
    linked_refs
        Optional object of role-shaped references joined onto the
        record (the notification ref, the recovery ref, the failover
        ref) keyed by name; empty-string values are dropped (the
        no-notification branch's empty ``__notification_ref__``).

    Returns
    -------
    JSON-native review record::

        {
            "pir_ref": "bcm-pir-<24 hex>",
            "event_id": "...",
            "markers": ["ran_without_plan"?],
            "lessons_learned": [...],
            "corrective_actions": [{"action": "...",
                                    "owner_ref": "..."}, ...],
            "plan_revisions": [...],
            "linked_refs": {...}
        }
    """
    event = _canonical_pointer(event_id, "event_id")
    if not isinstance(plan_on_file, bool):
        raise InvalidPirRecordError(
            "plan_on_file must be a boolean, got "
            f"{type(plan_on_file).__name__}"
        )

    if not isinstance(lessons_learned, list) or not lessons_learned:
        raise InvalidPirRecordError(
            "lessons_learned must be a non-empty list — a review with no "
            "lesson recorded is not a review"
        )
    lessons = [
        _canonical_text(item, f"lessons_learned[{i}]")
        for i, item in enumerate(lessons_learned)
    ]

    if not isinstance(corrective_actions, list):
        raise InvalidPirRecordError(
            "corrective_actions must be a list (possibly empty)"
        )
    actions = []
    for index, item in enumerate(corrective_actions):
        field = f"corrective_actions[{index}]"
        if not isinstance(item, dict):
            raise InvalidPirRecordError(
                f"{field} must be an object, got {type(item).__name__}"
            )
        actions.append(
            {
                "action": _canonical_text(item.get("action"), f"{field}.action"),
                "owner_ref": _canonical_pointer(
                    item.get("owner_ref"), f"{field}.owner_ref"
                ),
            }
        )

    if not isinstance(plan_revisions, list):
        raise InvalidPirRecordError(
            "plan_revisions must be a list (possibly empty)"
        )
    revisions = [
        _canonical_text(item, f"plan_revisions[{i}]")
        for i, item in enumerate(plan_revisions)
    ]

    refs: dict = {}
    if linked_refs is not None:
        if not isinstance(linked_refs, dict):
            raise InvalidPirRecordError(
                f"linked_refs must be an object, got "
                f"{type(linked_refs).__name__}"
            )
        for key in sorted(linked_refs):
            name = _canonical_text(key, "linked_refs key")
            value = linked_refs[key]
            if value == "" or value is None:
                continue  # the no-notification branch's empty ref
            refs[name] = _canonical_pointer(value, f"linked_refs[{name!r}]")

    markers = [] if plan_on_file else ["ran_without_plan"]

    body = {
        "event_id": event,
        "markers": markers,
        "lessons_learned": lessons,
        "corrective_actions": actions,
        "plan_revisions": revisions,
        "linked_refs": refs,
    }
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {"pir_ref": "bcm-pir-" + digest[:24], **body}
