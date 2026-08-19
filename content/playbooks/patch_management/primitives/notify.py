"""Maintenance-owner notification composition primitive (notify maintenance owner).

Composes the closed, deterministic notification payload that delivers
the patch-application evidence reference to the maintenance owner. The
split follows the incident_management destination-resolver precedent
(and the mfa_secured_comms notify wire): the deterministic half — what
is delivered, to which role, referencing which evidence record, at
which urgency — is a primitive; the delivery itself stays a discipline
of the compile target's messaging surface (ticketing system, chat
thread, change-management board), which this primitive never touches.

Design constraints
------------------

* **Pure / replayable.** No network, no clock reads, no LLMs. Same
  evidence + same subject + same canary outcome ⇒ byte-identical
  payload.
* **Urgency is derived, not free text.** A healthy canary composes a
  ``routine`` delivery; an unhealthy canary composes
  ``action_required`` and carries the step's documented next
  maintenance levers verbatim (rollback the canary, escalate the
  advisory, hold the broad rollout) — carrying the documented options
  is not choosing among them; the choice stays with the owner.
* **Booleans only.** ``canary_healthy`` must be a real JSON boolean —
  the string ``"false"`` is truthy in Python, so a marshalling layer
  that stringifies the flag would silently page at the wrong urgency;
  this boundary refuses it.
* **Idempotent delivery by construction.** ``notification_id`` is
  SHA-256 over ``patch_management|notify|<evidence_ref>|<update_subject>``
  so the messaging surface can dedup: a replayed workflow does not
  page the owner twice for one evidence record.
* **Public-bar safe.** The recipient is the role, never a person:
  ``recipient_role`` is fixed to ``maintenance-owner`` and no
  free-text recipient field exists.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

__all__ = [
    "InvalidMaintenanceNotificationError",
    "compose_maintenance_notification",
]


_EVIDENCE_REF_RE = re.compile(r"^[0-9a-f]{64}$")
_UPDATE_SUBJECT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_RECIPIENT_ROLE = "maintenance-owner"
_NOTIFICATION_KIND = "patch_evidence_delivery"
# The step description's documented next maintenance levers for an
# unhealthy canary, verbatim and in its order. Carried on the payload
# so the owner sees the documented options; the choice is theirs.
_ESCALATION_LEVERS = (
    "rollback_canary",
    "escalate_advisory",
    "hold_broad_rollout",
)


class InvalidMaintenanceNotificationError(ValueError):
    """Raised when the notification inputs cannot produce a valid payload."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidMaintenanceNotificationError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidMaintenanceNotificationError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def compose_maintenance_notification(
    evidence_id: str, update_subject: str, canary_healthy: bool
) -> dict:
    """Compose the maintenance-owner notification for one evidence record.

    Inputs
    ------
    evidence_id
        The dated patch-application evidence record id produced by
        :func:`..artifact.build_patch_application_evidence_artifact`
        (64-char SHA-256 lower-hex, re-validated here).
    update_subject
        Identifier of the tracked package / image / firmware line the
        update applies to (the CACAO ``__update_subject__`` variable);
        echoed so the owner can route without dereferencing first.
    canary_healthy
        Outcome of the validate-canary step (the CACAO
        ``__canary_healthy__`` variable). Must be a real JSON boolean.

    Returns
    -------
    JSON-native dict — the closed notification payload the compile
    target's messaging surface delivers verbatim. A healthy canary
    composes ``urgency: "routine"``; an unhealthy one composes
    ``urgency: "action_required"`` plus the documented
    ``escalation_levers`` list.
    """
    ref = _canonical_text(evidence_id, "evidence_id")
    if not _EVIDENCE_REF_RE.match(ref):
        raise InvalidMaintenanceNotificationError(
            f"evidence_id {evidence_id!r} is not a 64-char SHA-256 "
            "lower-hex evidence record id"
        )
    subject = _canonical_text(update_subject, "update_subject")
    if not _UPDATE_SUBJECT_RE.match(subject):
        raise InvalidMaintenanceNotificationError(
            f"update_subject {update_subject!r} does not match the opaque "
            "role-shaped pointer pattern; free text is out of scope per "
            "AGENTS.md §3"
        )
    if not isinstance(canary_healthy, bool):
        raise InvalidMaintenanceNotificationError(
            f"canary_healthy must be a boolean, got "
            f"{type(canary_healthy).__name__}; a stringified flag would "
            "page at the wrong urgency"
        )

    notification_id = hashlib.sha256(
        f"patch_management|notify|{ref}|{subject}".encode("utf-8")
    ).hexdigest()

    payload: dict = {
        "notification_id": notification_id,
        "notification_kind": _NOTIFICATION_KIND,
        "recipient_role": _RECIPIENT_ROLE,
        "update_subject": subject,
        "evidence_ref": ref,
        "canary_healthy": canary_healthy,
        "urgency": "routine" if canary_healthy else "action_required",
    }
    if canary_healthy:
        payload["summary"] = (
            f"Patch evidence {ref[:12]}… for {subject}: canary healthy, "
            "broad rollout proceeding per policy."
        )
    else:
        payload["escalation_levers"] = list(_ESCALATION_LEVERS)
        payload["summary"] = (
            f"Patch evidence {ref[:12]}… for {subject}: canary UNHEALTHY — "
            "owner action required (rollback the canary, escalate the "
            "advisory, or hold the broad rollout)."
        )
    return payload
