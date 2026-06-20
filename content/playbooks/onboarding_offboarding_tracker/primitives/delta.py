"""Capability-delta primitive (apply-capability-delta).

Pure derivation. Given the normalised lifecycle event and the resolved
caller-identity block, return the closed ``add_set`` / ``remove_set``
the workflow asked the operator's identity source to materialise
against the resolved principal. No IdP mutation happens here — the
operator's compile target wires the actual write in its native idiom
(n8n credential-binding node, Temporal activity, LangGraph tool node).
The primitive only pins the closed-delta shape so re-runs collapse to
byte-identical bytes at the delta layer; the SKELETON-layer contract
notes the actual provider mutation lives downstream.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

__all__ = [
    "InvalidCapabilityDeltaError",
    "apply_capability_delta",
]


_ALLOWED_EVENT_KINDS = frozenset({"joiner", "mover", "leaver"})
_CAPABILITY_RE = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")


class InvalidCapabilityDeltaError(ValueError):
    """Raised when the delta inputs cannot produce a valid record."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidCapabilityDeltaError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidCapabilityDeltaError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _validate_capability_set(value: object, field: str) -> list[str]:
    if not isinstance(value, list):
        raise InvalidCapabilityDeltaError(
            f"{field} must be a list, got {type(value).__name__}"
        )
    seen: set[str] = set()
    out: list[str] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, str):
            raise InvalidCapabilityDeltaError(
                f"{field}[{index}] must be a string, got {type(raw).__name__}"
            )
        token = unicodedata.normalize("NFKC", raw).strip().lower()
        if not token or not _CAPABILITY_RE.match(token) or len(token) > 128:
            raise InvalidCapabilityDeltaError(
                f"{field}[{index}] {raw!r} does not match the verb.resource "
                "shape pinned by the schema"
            )
        if token in seen:
            continue
        seen.add(token)
        out.append(token)
    return out


def apply_capability_delta(
    lifecycle_event_record: dict,
    resolved_identity: dict,
) -> dict[str, Any]:
    """Return the closed capability delta the workflow declares.

    Inputs
    ------
    lifecycle_event_record
        Normalised event record produced by
        :func:`...primitives.ingest.ingest_lifecycle_event`.
    resolved_identity
        Role-shaped caller-identity block produced by
        :func:`...primitives.identity.resolve_identity`.

    Returns
    -------
    JSON-native dict pinning the closed delta:
    ``{event_kind, principal_id, add_set, remove_set, effective_at}``.
    Re-runs collapse to byte-identical bytes; the actual write on the
    operator's identity source is delegated to the compile target.
    """
    if not isinstance(lifecycle_event_record, dict):
        raise InvalidCapabilityDeltaError(
            "lifecycle_event_record must be an object, got "
            f"{type(lifecycle_event_record).__name__}"
        )
    if not isinstance(resolved_identity, dict):
        raise InvalidCapabilityDeltaError(
            "resolved_identity must be an object, got "
            f"{type(resolved_identity).__name__}"
        )

    event_kind = _canonical_text(
        lifecycle_event_record.get("event_kind"),
        "lifecycle_event_record.event_kind",
    )
    if event_kind not in _ALLOWED_EVENT_KINDS:
        raise InvalidCapabilityDeltaError(
            f"event_kind {event_kind!r} is not one of "
            f"{sorted(_ALLOWED_EVENT_KINDS)!r}"
        )

    event_pid = _canonical_text(
        lifecycle_event_record.get("principal_id"),
        "lifecycle_event_record.principal_id",
    )
    resolved_pid = _canonical_text(
        resolved_identity.get("principal_id"),
        "resolved_identity.principal_id",
    )
    if event_pid != resolved_pid:
        raise InvalidCapabilityDeltaError(
            "resolved_identity.principal_id "
            f"{resolved_pid!r} does not match "
            f"lifecycle_event_record.principal_id {event_pid!r}; the "
            "delta MUST target the resolved principal"
        )

    add_set = _validate_capability_set(
        lifecycle_event_record.get("add_set", []),
        "lifecycle_event_record.add_set",
    )
    remove_set = _validate_capability_set(
        lifecycle_event_record.get("remove_set", []),
        "lifecycle_event_record.remove_set",
    )

    if event_kind == "joiner" and (not add_set or remove_set):
        raise InvalidCapabilityDeltaError(
            "joiner delta must declare a non-empty add_set and an empty "
            "remove_set"
        )
    if event_kind == "leaver" and (not remove_set or add_set):
        raise InvalidCapabilityDeltaError(
            "leaver delta must declare a non-empty remove_set and an "
            "empty add_set"
        )
    if event_kind == "mover" and not (add_set or remove_set):
        raise InvalidCapabilityDeltaError(
            "mover delta must declare at least one of add_set or remove_set"
        )

    effective_at = _canonical_text(
        lifecycle_event_record.get("effective_at"),
        "lifecycle_event_record.effective_at",
    )

    return {
        "event_kind": event_kind,
        "principal_id": resolved_pid,
        "add_set": add_set,
        "remove_set": remove_set,
        "effective_at": effective_at,
    }
