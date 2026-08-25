"""Owner-notification composition primitive (notify authentication owner).

Composes the closed, deterministic notification payload that delivers
the posture-attestation reference to the authentication owner. The
split follows the house precedent set by incident_management's
regulator-submission steps (bound to a fail-closed *destination
resolver*, never to a sender): the deterministic half — what is being
delivered, to which role, referencing which attestation, under which
idempotency key — is a primitive; the delivery itself stays a
discipline of the compile target's messaging surface (ticketing
system, chat thread, email), which this primitive never touches.

Design constraints
------------------

* **Pure / replayable.** No network, no clock reads, no LLMs. Same
  attestation + same scope ⇒ byte-identical payload, so the
  human-acknowledgement record can be joined back to exactly one
  composed notification.
* **Idempotent delivery by construction.** ``notification_id`` is
  SHA-256 over ``mfa_secured_comms|notify|<attestation_ref>|<auth_scope>``
  — the operator's messaging surface can use it as a dedup key so a
  replayed workflow does not page the owner twice for one attestation.
* **Public-bar safe.** The recipient is the role, never a person:
  ``recipient_role`` is fixed to ``authentication-owner`` and no
  free-text recipient field exists to smuggle a name through.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

__all__ = [
    "InvalidOwnerNotificationError",
    "compose_owner_notification",
]


_ATTESTATION_REF_RE = re.compile(r"^[0-9a-f]{64}$")
_AUTH_SCOPE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_RECIPIENT_ROLE = "authentication-owner"
_NOTIFICATION_KIND = "mfa_posture_attestation_delivery"


class InvalidOwnerNotificationError(ValueError):
    """Raised when the notification inputs cannot produce a valid payload."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidOwnerNotificationError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidOwnerNotificationError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def compose_owner_notification(attestation_id: str, auth_scope: str) -> dict:
    """Compose the owner-notification payload for one attestation.

    Inputs
    ------
    attestation_id
        The dated posture-attestation record id produced by
        :func:`..artifact.build_mfa_posture_attestation_artifact`
        (64-char SHA-256 lower-hex — the shape is re-validated here so
        a caller passing a path or free text fails at this boundary,
        not at the messaging surface).
    auth_scope
        Identifier of the in-scope authentication surface the
        attestation covers (the CACAO ``__auth_scope__`` variable);
        echoed so the owner can route without dereferencing first.

    Returns
    -------
    JSON-native dict — the closed notification payload the compile
    target's messaging surface delivers verbatim::

        {
            "notification_id": "<sha256 dedup key>",
            "notification_kind": "mfa_posture_attestation_delivery",
            "recipient_role": "authentication-owner",
            "auth_scope": "...",
            "attestation_ref": "<attestation_id>",
            "summary": "<deterministic one-liner>"
        }
    """
    ref = _canonical_text(attestation_id, "attestation_id")
    if not _ATTESTATION_REF_RE.match(ref):
        raise InvalidOwnerNotificationError(
            f"attestation_id {attestation_id!r} is not a 64-char SHA-256 "
            "lower-hex attestation record id"
        )
    scope = _canonical_text(auth_scope, "auth_scope")
    if not _AUTH_SCOPE_RE.match(scope):
        raise InvalidOwnerNotificationError(
            f"auth_scope {auth_scope!r} does not match the opaque "
            "role-shaped pointer pattern; free text is out of scope per "
            "AGENTS.md §3"
        )

    notification_id = hashlib.sha256(
        f"mfa_secured_comms|notify|{ref}|{scope}".encode("utf-8")
    ).hexdigest()

    return {
        "notification_id": notification_id,
        "notification_kind": _NOTIFICATION_KIND,
        "recipient_role": _RECIPIENT_ROLE,
        "auth_scope": scope,
        "attestation_ref": ref,
        "summary": (
            "MFA and secured-communications posture attestation "
            f"{ref[:12]}… for scope {scope} is ready for owner review."
        ),
    }
