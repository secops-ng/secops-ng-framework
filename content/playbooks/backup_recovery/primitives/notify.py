"""Continuity-owner notification composition (notify continuity owner).

Composes the notification payload; **dispatch belongs to the runtime**, so
the payload is emitted with ``dispatched: false`` and an opaque address
reference into the operator's own channel binding. No transport, no
templating engine, no prose beyond a fixed-form subject — the notification's
value is the attestation reference it carries, not its wording.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
* **Determinism.** Same inputs => byte-identical payload; keys sorted.
* **Public-bar safe.** ``address_ref`` is an opaque operator reference
  (ticket queue id, channel id, mailbox alias) validated against a closed
  regex — never a person's name or address in the clear.
* **Read-only-by-contract.** Composes; the runtime dispatches.
"""

from __future__ import annotations

import re

__all__ = [
    "InvalidOwnerBindingError",
    "compose_continuity_notification",
]

_CHANNEL_KINDS = ("chat", "email", "ticket")
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,199}$")


class InvalidOwnerBindingError(ValueError):
    """The owner binding does not match the documented shape."""


def compose_continuity_notification(
    attestation: dict,
    backup_scope: str,
    owner_binding: dict,
) -> dict:
    """Return the composed, undispatched notification payload.

    ``owner_binding`` shape::

        {"channel_kind": "ticket" | "chat" | "email",
         "address_ref": str,          # opaque reference, operator-owned
         "owner_role": str}           # role, not a person
    """
    if not isinstance(attestation, dict) or not attestation.get("attestation_id"):
        raise InvalidOwnerBindingError("attestation record with attestation_id is required")
    if not isinstance(owner_binding, dict):
        raise InvalidOwnerBindingError("owner_binding must be a mapping")
    kind = owner_binding.get("channel_kind")
    if kind not in _CHANNEL_KINDS:
        raise InvalidOwnerBindingError(
            f"channel_kind must be one of {_CHANNEL_KINDS}, got {kind!r}"
        )
    address_ref = owner_binding.get("address_ref", "")
    if not _REF_RE.match(address_ref):
        raise InvalidOwnerBindingError("address_ref is not a valid opaque reference")
    owner_role = owner_binding.get("owner_role", "")
    if not owner_role or not _REF_RE.match(owner_role):
        raise InvalidOwnerBindingError("owner_role is required (a role, not a person)")

    verdict = attestation.get("verdict", "")
    return {
        "address_ref": address_ref,
        "attestation_id": attestation["attestation_id"],
        "backup_scope": backup_scope,
        "channel_kind": kind,
        "dispatched": False,
        "owner_role": owner_role,
        "severity": "info" if verdict == "drill-verified" else "warn",
        "subject": f"backup restore drill [{backup_scope}]: {verdict or 'unknown'}",
        "verdict": verdict,
    }
