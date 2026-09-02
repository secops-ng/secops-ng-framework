"""Crypto-owner notification primitive (notify-crypto-owner step).

Composes the notification that delivers the lifecycle-attestation
reference to the cryptography owner. The composition / delivery split
from the notify-lane precedent applies: this primitive composes the
payload and resolves the urgency; delivery along the operator's
pre-bound channel is the compile target's messaging surface.

Design constraints
------------------

* **Pure / replayable.** Same attestation flags ⇒ byte-identical
  notification.
* **Urgency follows the attestation flags (pinned by tests).** A
  breach (violated clause or gate deny) or a policy gap elevates to
  ``attention`` — both are conditions the owner must act on (fix the
  surface, or document the policy); a clean attestation informs.
* **Real booleans only.** The two flags arrive as workflow booleans;
  a string ``"false"`` is truthy and would either page on a clean run
  or, worse, demote a breach — strings are refused outright.
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
    lifecycle_attestation_id: str,
    crypto_scope: str,
    lifecycle_event: str,
    has_breach: bool,
    has_policy_gap: bool,
    owner_channel: str,
) -> dict:
    """Compose the crypto-owner notification for one attestation.

    Inputs
    ------
    lifecycle_attestation_id
        The published attestation's id
        (``__lifecycle_attestation_id__``).
    crypto_scope, lifecycle_event
        Case context, role-shaped.
    has_breach, has_policy_gap
        The attestation's computed flags, as real booleans.
    owner_channel
        Role-shaped reference to the operator's pre-bound delivery
        channel (ticketing system, chat thread, email).

    Returns
    -------
    JSON-native notification payload::

        {
            "channel_ref": "...",
            "urgency": "attention" | "inform",
            "lifecycle_attestation_id": "...",
            "has_breach": <bool>,
            "has_policy_gap": <bool>,
            "headline": "...",
            "body": "..."
        }
    """
    attestation = _canonical_pointer(
        lifecycle_attestation_id, "lifecycle_attestation_id"
    )
    scope = _canonical_pointer(crypto_scope, "crypto_scope")
    event = _canonical_pointer(lifecycle_event, "lifecycle_event")
    channel = _canonical_pointer(owner_channel, "owner_channel")
    for name, flag in (
        ("has_breach", has_breach),
        ("has_policy_gap", has_policy_gap),
    ):
        if not isinstance(flag, bool):
            raise InvalidNotificationInputError(
                f"{name} must be a boolean, got {type(flag).__name__} — a "
                "string 'false' is truthy and would misgrade the urgency"
            )

    if has_breach or has_policy_gap:
        urgency = "attention"
        concerns = []
        if has_breach:
            concerns.append("a documented policy clause was breached")
        if has_policy_gap:
            concerns.append(
                "the declared policy leaves consulted clauses undocumented"
            )
        headline = (
            "crypto-controls "
            + event
            + " on "
            + scope
            + " — attention needed"
        )
        body = (
            "Lifecycle attestation "
            + attestation
            + " for "
            + scope
            + " ("
            + event
            + ") requires attention: "
            + "; ".join(concerns)
            + ". The attestation carries the per-clause detail."
        )
    else:
        urgency = "inform"
        headline = (
            "crypto-controls " + event + " on " + scope + " — recorded"
        )
        body = (
            "Lifecycle attestation "
            + attestation
            + " for "
            + scope
            + " ("
            + event
            + ") is recorded with every consulted clause documented and "
            "satisfied."
        )

    return {
        "channel_ref": channel,
        "urgency": urgency,
        "lifecycle_attestation_id": attestation,
        "has_breach": has_breach,
        "has_policy_gap": has_policy_gap,
        "headline": headline,
        "body": body,
    }
