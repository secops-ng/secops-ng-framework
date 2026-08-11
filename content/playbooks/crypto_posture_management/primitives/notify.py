"""Owner-notification planning primitive (notify crypto owner).

Composes the notification the cryptography owner will receive. **It does not
send it.** The channel is an adapter-bound operator surface; this step records
what would go out, to whom, and why.

That split is the point. A primitive that dispatched would make the terminal
step of a read-only posture run a side effect on an external system, and a
failed send would either be swallowed or would fail a run whose posture work
had already completed successfully. Recording the plan keeps the run pure and
leaves delivery to a surface that can retry.

**A conforming posture still produces a plan.** The notification carries
``escalate: false`` rather than being suppressed, because "we ran the posture
check and it was clean" is the message an owner needs on a cadence — silence is
indistinguishable from the run never happening.

Design constraints
------------------

* **Pure / replayable.** No network, no clock reads, no LLMs.
* **Determinism.** Same inputs => byte-identical output.
* **Public-bar safe.** Recipient is a *role*, never a person or an address;
  the plan carries counts and the attestation reference, no finding detail.
* **Read-only-by-contract.** Nothing is transmitted.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidCryptoNotificationError",
    "plan_crypto_owner_notification",
]


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_ROLE_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")

_SCHEMA_VERSION = "1.0.0"
_STREAM = "crypto_posture_management_notify"


class InvalidCryptoNotificationError(ValueError):
    """Raised when a notification input or invariant is violated."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidCryptoNotificationError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidCryptoNotificationError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _require_pattern(value: object, field: str, pattern: re.Pattern[str]) -> str:
    text = _canonical_text(value, field)
    if not pattern.match(text):
        raise InvalidCryptoNotificationError(
            f"{field} {text!r} does not match the schema pattern"
        )
    return text


def plan_crypto_owner_notification(
    attestation: dict,
    crypto_scope: str,
    owner_role: str,
    channel_ref: str,
) -> dict:
    """Compose the owner notification plan for one posture run.

    Args:
        attestation: Envelope from the evidence step (``__attestation_id__``).
        crypto_scope: Scope identifier; must match the attestation's.
        owner_role: Role to notify. A role, never a named individual.
        channel_ref: Reference to the operator's declared channel. Recorded;
            delivery is adapter-bound.

    Returns:
        JSON-native plan envelope with ``schema_version``, ``stream``,
        ``notification_plan_id``, ``crypto_scope``, ``attestation_id``,
        ``artifact_id``, ``owner_role``, ``channel_ref``, ``drift_count``,
        ``gap_count``, ``escalate``, ``reason`` and ``dispatched`` — always
        ``False``, so a consumer cannot mistake the plan for a receipt.

    Raises:
        InvalidCryptoNotificationError: any input fails validation or the
            scope does not match the attestation.
    """
    if not isinstance(attestation, dict):
        raise InvalidCryptoNotificationError(
            f"attestation must be a mapping, got {type(attestation).__name__}"
        )
    scope = _require_pattern(crypto_scope, "crypto_scope", _ID_RE)
    if scope != attestation.get("crypto_scope"):
        raise InvalidCryptoNotificationError(
            f"crypto_scope {scope!r} does not match attestation "
            f"{attestation.get('crypto_scope')!r}"
        )
    role = _require_pattern(owner_role, "owner_role", _ROLE_RE)
    channel = _require_pattern(channel_ref, "channel_ref", _REF_RE)
    attestation_id = _require_pattern(
        attestation.get("attestation_id"), "attestation.attestation_id", _REF_RE
    )

    drift = attestation.get("drift_count")
    gap = attestation.get("gap_count")
    for name, value in (("drift_count", drift), ("gap_count", gap)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise InvalidCryptoNotificationError(
                f"attestation.{name} must be a non-negative int, got {value!r}"
            )

    if drift and gap:
        reason = "drift_and_policy_gap"
    elif drift:
        reason = "policy_drift"
    elif gap:
        reason = "policy_gap"
    else:
        reason = "posture_clean"

    return {
        "schema_version": _SCHEMA_VERSION,
        "stream": _STREAM,
        "notification_plan_id": f"{attestation_id}:notify",
        "crypto_scope": scope,
        "attestation_id": attestation_id,
        "artifact_id": _require_pattern(
            attestation.get("artifact_id"), "attestation.artifact_id", _REF_RE
        ),
        "owner_role": role,
        "channel_ref": channel,
        "drift_count": drift,
        "gap_count": gap,
        "escalate": bool(drift or gap),
        "reason": reason,
        "dispatched": False,
    }
