"""Broad-fan-out primitive (fan-out-to-broad-rings).

Deterministic broad-rollout-id derivation against the operator's
documented ring topology. On a healthy canary the primitive emits a
SHA-256 hex digest naming the broad-ring engagement. On an unhealthy
canary the step is a deterministic skip: ``broad_rollout_id`` is left
empty and ``broad_rollout_skip_reason`` carries ``"canary_unhealthy"``
so the evidence-capture step can record the skip explicitly without
forcing the broad rollout against a failing canary.

Design constraints
------------------

* **Pure / replayable.** No network, no clock reads, no LLMs.
* **Determinism.** Same inputs => byte-identical output, including the
  empty-id wire shape on the unhealthy-canary branch.
* **Closed wire shape.** Either ``broad_rollout_id`` is a 64-char hex
  digest and ``broad_rollout_skip_reason`` is ``None``, or
  ``broad_rollout_id`` is the empty string and
  ``broad_rollout_skip_reason`` is ``"canary_unhealthy"``.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

__all__ = [
    "InvalidPatchFanOutError",
    "fan_out_to_broad_rings",
]


_SUBJECT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$")
_REFERENCE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$")
_RING_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{0,127}$")
_STAGED_ID_RE = re.compile(r"^[0-9a-f]{64}$")


class InvalidPatchFanOutError(ValueError):
    """Raised when the fan-out inputs cannot produce a deterministic id."""


def _require_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidPatchFanOutError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    return unicodedata.normalize("NFKC", value).strip()


def _require_non_empty(value: object, field: str) -> str:
    text = _require_str(value, field)
    if not text:
        raise InvalidPatchFanOutError(
            f"{field} is empty after canonicalisation"
        )
    return text


def fan_out_to_broad_rings(
    update_subject: str,
    update_reference: str,
    staged_ring_id: str,
    canary_healthy: bool,
    broad_rings: list,
) -> dict:
    """Derive the broad-rollout-id (or the deterministic skip marker).

    Parameters
    ----------
    update_subject, update_reference
        Opaque operator-side identifiers (subject + advisory).
    staged_ring_id
        Output of :func:`stage_rollout_to_canary_ring` (64-char hex).
    canary_healthy
        Output of :func:`validate_canary`. When ``False`` the step is a
        deterministic skip.
    broad_rings
        Operator-documented list of broad-ring identifiers (role-shaped,
        lower-snake-case / hyphenated). Must be a non-empty list of
        unique entries; the canonical sorted form keys the digest.

    Returns
    -------
    JSON-native dict with ``broad_rollout_id`` (64-char hex on healthy
    canary, empty string on unhealthy canary) and
    ``broad_rollout_skip_reason`` (``None`` on healthy canary,
    ``"canary_unhealthy"`` on unhealthy canary).
    """
    subject = _require_non_empty(update_subject, "update_subject")
    if not _SUBJECT_RE.match(subject):
        raise InvalidPatchFanOutError(
            f"update_subject {subject!r} does not match the opaque "
            "subject-id pattern"
        )

    reference = _require_non_empty(update_reference, "update_reference")
    if not _REFERENCE_RE.match(reference):
        raise InvalidPatchFanOutError(
            f"update_reference {reference!r} does not match the opaque "
            "reference-id pattern"
        )

    staged = _require_non_empty(staged_ring_id, "staged_ring_id")
    if not _STAGED_ID_RE.match(staged):
        raise InvalidPatchFanOutError(
            f"staged_ring_id {staged!r} must be a 64-char lowercase hex digest"
        )

    if not isinstance(canary_healthy, bool):
        raise InvalidPatchFanOutError(
            "canary_healthy must be a bool, got "
            f"{type(canary_healthy).__name__}"
        )

    if not isinstance(broad_rings, list) or not broad_rings:
        raise InvalidPatchFanOutError(
            "broad_rings must be a non-empty list of ring identifiers"
        )
    seen: set[str] = set()
    canonical: list[str] = []
    for index, raw in enumerate(broad_rings):
        entry = _require_non_empty(raw, f"broad_rings[{index}]")
        if not _RING_ID_RE.match(entry):
            raise InvalidPatchFanOutError(
                f"broad_rings[{index}] {entry!r} does not match the role-"
                "shaped ring-id pattern"
            )
        if entry in seen:
            raise InvalidPatchFanOutError(
                f"broad_rings has duplicate entry {entry!r}"
            )
        seen.add(entry)
        canonical.append(entry)

    if not canary_healthy:
        return {
            "broad_rollout_id": "",
            "broad_rollout_skip_reason": "canary_unhealthy",
        }

    payload = json.dumps(
        {
            "update_subject": subject,
            "update_reference": reference,
            "staged_ring_id": staged,
            "broad_rings": sorted(canonical),
        },
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    broad_rollout_id = hashlib.sha256(payload).hexdigest()

    return {
        "broad_rollout_id": broad_rollout_id,
        "broad_rollout_skip_reason": None,
    }
