"""Key-lifecycle evidence primitive (key-lifecycle step).

Judges one executed key-lifecycle action (generate / rotate / revoke)
against the resolved policy snapshot and composes the evidence record
the attestation carries and the sibling crypto_posture_management
overlay reads. The KMS action itself is the operator's adapter-bound
control plane; what is deterministic here is the metadata shape and
the per-clause verdicts.

Design constraints
------------------

* **No key material — actively enforced (pinned by tests).** The
  record is metadata only; an input carrying ``key_material``,
  ``private_key`` or ``secret`` fails loud rather than being quietly
  dropped, because a dropped secret has already crossed a boundary it
  must never cross.
* **Undocumented is not compliant (acceptance criterion, pinned).**
  Each policy check yields ``satisfied`` / ``violated`` /
  ``undocumented``; the record outcome is ``compliant`` only when
  every check is documented *and* satisfied, ``breach`` when any
  documented clause is violated, and ``undocumented`` when nothing is
  violated but a consulted clause is missing.
* **A breach is data, not an error.** The lifecycle action already
  happened on the operator's KMS; recording a floor violation loudly
  on the attestation is the point — refusing to record it would hide
  the breach from the audit trail.
* **Rotation cadence is the sibling's judgement.** The rotation record
  carries the backreference and instants; whether the previous key was
  overdue is the read-side posture playbook's check, not this
  write-side record's.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

__all__ = [
    "InvalidKeyLifecycleInputError",
    "record_key_lifecycle",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_INSTANT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

_KEY_EVENTS = frozenset({"key-generate", "key-rotate", "key-revoke"})
_FAMILIES = frozenset({"symmetric", "asymmetric"})
_FORBIDDEN_FIELDS = frozenset({"key_material", "private_key", "secret"})


class InvalidKeyLifecycleInputError(ValueError):
    """Raised when the key record cannot produce valid evidence."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidKeyLifecycleInputError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidKeyLifecycleInputError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidKeyLifecycleInputError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def _canonical_instant(value: object, field: str) -> str:
    text = _canonical_pointer(value, field)
    if not _INSTANT_RE.match(text):
        raise InvalidKeyLifecycleInputError(
            f"{field} {text!r} is not a Zulu instant (YYYY-MM-DDTHH:MM:SSZ)"
        )
    return text


def _clauses(policy_inventory: dict) -> dict:
    if not isinstance(policy_inventory, dict) or not isinstance(
        policy_inventory.get("clauses"), dict
    ):
        raise InvalidKeyLifecycleInputError(
            "policy_inventory must be a resolve_policy_inventory envelope "
            "carrying a clauses object"
        )
    return policy_inventory["clauses"]


def record_key_lifecycle(
    lifecycle_event: str, key_record: dict, policy_inventory: dict
) -> dict:
    """Compose the evidence record for one executed key-lifecycle action.

    Inputs
    ------
    lifecycle_event
        ``key-generate``, ``key-rotate`` or ``key-revoke``.
    key_record
        Metadata for the executed action — never material. Common
        required keys: ``key_id``, ``key_class`` (role-shaped),
        ``algorithm`` (name), ``key_bits`` (positive int), ``family``
        (``symmetric`` | ``asymmetric``), ``generated_at`` (Zulu
        instant of the acting key's generation). Rotate additionally
        requires ``previous_key_ref`` and ``rotated_at``; revoke
        additionally requires ``revocation_reason`` (non-empty text)
        and ``revoked_at``.
    policy_inventory
        The resolved snapshot
        (:func:`.policy.resolve_policy_inventory` output).

    Returns
    -------
    JSON-native key-lifecycle record::

        {
            "key_lifecycle_record_id": "cc-key-<24 hex>",
            "lifecycle_event": "...",
            "key_id": "...", "key_class": "...",
            "algorithm": "...", "key_bits": <int>, "family": "...",
            "generated_at": "...",
            "previous_key_ref": "..." | None,
            "rotated_at": "..." | None,
            "revocation_reason": "..." | None,
            "revoked_at": "..." | None,
            "checks": [{"clause": "...", "verdict": "satisfied"
                        | "violated" | "undocumented",
                        "detail": "..."}],
            "outcome": "compliant" | "breach" | "undocumented"
                       | "recorded"
        }
    """
    event = _canonical_pointer(lifecycle_event, "lifecycle_event")
    if event not in _KEY_EVENTS:
        raise InvalidKeyLifecycleInputError(
            f"lifecycle_event {event!r} is not a key event "
            f"({sorted(_KEY_EVENTS)})"
        )
    if not isinstance(key_record, dict):
        raise InvalidKeyLifecycleInputError(
            f"key_record must be an object, got {type(key_record).__name__}"
        )
    leaked = _FORBIDDEN_FIELDS & set(key_record)
    if leaked:
        raise InvalidKeyLifecycleInputError(
            f"key_record carries forbidden material fields "
            f"{sorted(leaked)}; no key material crosses this boundary — "
            "the record is metadata only"
        )

    key_id = _canonical_pointer(key_record.get("key_id"), "key_record.key_id")
    key_class = _canonical_pointer(
        key_record.get("key_class"), "key_record.key_class"
    )
    algorithm = _canonical_pointer(
        key_record.get("algorithm"), "key_record.algorithm"
    )
    family = _canonical_pointer(key_record.get("family"), "key_record.family")
    if family not in _FAMILIES:
        raise InvalidKeyLifecycleInputError(
            f"key_record.family {family!r} is not one of {sorted(_FAMILIES)}"
        )
    bits = key_record.get("key_bits")
    if isinstance(bits, bool) or not isinstance(bits, int) or bits <= 0:
        raise InvalidKeyLifecycleInputError(
            "key_record.key_bits must be a positive integer"
        )
    generated_at = _canonical_instant(
        key_record.get("generated_at"), "key_record.generated_at"
    )

    previous_key_ref = None
    rotated_at = None
    revocation_reason = None
    revoked_at = None
    if event == "key-rotate":
        previous_key_ref = _canonical_pointer(
            key_record.get("previous_key_ref"), "key_record.previous_key_ref"
        )
        rotated_at = _canonical_instant(
            key_record.get("rotated_at"), "key_record.rotated_at"
        )
    if event == "key-revoke":
        reason = key_record.get("revocation_reason")
        if not isinstance(reason, str):
            raise InvalidKeyLifecycleInputError(
                "key_record.revocation_reason must be a string"
            )
        revocation_reason = unicodedata.normalize("NFKC", reason).strip()
        if not revocation_reason:
            raise InvalidKeyLifecycleInputError(
                "key_record.revocation_reason is empty after "
                "canonicalisation; an unreasoned revocation is not a "
                "documented outcome"
            )
        revoked_at = _canonical_instant(
            key_record.get("revoked_at"), "key_record.revoked_at"
        )

    checks: list[dict] = []
    if event in ("key-generate", "key-rotate"):
        clauses = _clauses(policy_inventory)
        allow_clause = family + "_algorithms"
        allowed = clauses.get(allow_clause)
        if allowed is None:
            checks.append(
                {
                    "clause": allow_clause,
                    "verdict": "undocumented",
                    "detail": "no algorithm allow-list declared for "
                    + family
                    + " keys",
                }
            )
        elif algorithm in allowed:
            checks.append(
                {
                    "clause": allow_clause,
                    "verdict": "satisfied",
                    "detail": algorithm + " is on the declared allow-list",
                }
            )
        else:
            checks.append(
                {
                    "clause": allow_clause,
                    "verdict": "violated",
                    "detail": algorithm
                    + " is not on the declared allow-list",
                }
            )
        floors = clauses.get("minimum_key_bits")
        floor = None if floors is None else floors.get(algorithm)
        if floor is None:
            checks.append(
                {
                    "clause": "minimum_key_bits",
                    "verdict": "undocumented",
                    "detail": "no key-size floor declared for " + algorithm,
                }
            )
        elif bits >= floor:
            checks.append(
                {
                    "clause": "minimum_key_bits",
                    "verdict": "satisfied",
                    "detail": f"{bits} bits meets the declared floor of "
                    f"{floor}",
                }
            )
        else:
            checks.append(
                {
                    "clause": "minimum_key_bits",
                    "verdict": "violated",
                    "detail": f"{bits} bits is below the declared floor of "
                    f"{floor}",
                }
            )

    verdicts = {check["verdict"] for check in checks}
    if event == "key-revoke":
        outcome = "recorded"
    elif "violated" in verdicts:
        outcome = "breach"
    elif "undocumented" in verdicts:
        outcome = "undocumented"
    else:
        outcome = "compliant"

    body = {
        "lifecycle_event": event,
        "key_id": key_id,
        "key_class": key_class,
        "algorithm": algorithm,
        "key_bits": bits,
        "family": family,
        "generated_at": generated_at,
        "previous_key_ref": previous_key_ref,
        "rotated_at": rotated_at,
        "revocation_reason": revocation_reason,
        "revoked_at": revoked_at,
        "checks": checks,
        "outcome": outcome,
    }
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {"key_lifecycle_record_id": "cc-key-" + digest[:24], **body}
