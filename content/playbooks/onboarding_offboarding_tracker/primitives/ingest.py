"""Lifecycle-event ingest primitive (ingest-lifecycle-event).

Canonicalises and validates the operator-supplied raw lifecycle-event
record into the closed envelope the downstream primitives consume.
The runtime fetches the raw record from the operator's identity source
(a sovereign EU directory, an on-prem IdP, a Git-managed role-and-
capability repository); this primitive only re-shapes and re-validates
so a free-text or personal-name event field fails loud at the step
boundary rather than at the artifact-emit boundary downstream.

Design constraints
------------------

* **Pure / replayable.** No clock reads, no network, no LLMs. Inputs
  are JSON-native; outputs are JSON-native.
* **Closed event-kind enum.** ``joiner``, ``mover``, or ``leaver``.
  No implicit fall-through, no free-text event kinds.
* **Closed capability delta.** ``add_set`` and ``remove_set`` are
  verb.resource token lists. Wildcards, free text, and credential-
  shaped strings are rejected at the regex boundary.
* **Role-shaped principal.** Mirrors the schema-side regex for
  ``caller_identity.principal_id``; personal-user principals and
  credential-shaped strings are rejected here as a matter of public-
  bar discipline.
* **Per-event-kind shape.** A joiner event must declare a non-empty
  add-set and an empty remove-set; a leaver event must declare a
  non-empty remove-set and an empty add-set; a mover event may
  declare either or both, but at least one must be non-empty.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

__all__ = [
    "InvalidLifecycleEventError",
    "ingest_lifecycle_event",
]


_ALLOWED_EVENT_KINDS = frozenset({"joiner", "mover", "leaver"})
_ALLOWED_PRINCIPAL_TYPES = frozenset(
    {"service_account", "workflow_runtime", "automation_role"}
)
# Mirrors schemas/evidence/access.schema.json caller_identity.principal_id.
_PRINCIPAL_ID_RE = re.compile(
    r"^[a-zA-Z][a-zA-Z0-9_-]{0,127}(@[a-z0-9][a-z0-9.-]{0,127})?$"
)
_IDENTITY_PROVIDER_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_CAPABILITY_RE = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_EVENT_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_./:-]{0,255}$")


class InvalidLifecycleEventError(ValueError):
    """Raised when the lifecycle-event inputs cannot produce a valid record."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidLifecycleEventError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidLifecycleEventError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _validate_capability_set(
    value: object, field: str
) -> list[str]:
    if not isinstance(value, list):
        raise InvalidLifecycleEventError(
            f"{field} must be a list, got {type(value).__name__}"
        )
    seen: set[str] = set()
    out: list[str] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, str):
            raise InvalidLifecycleEventError(
                f"{field}[{index}] must be a string, got {type(raw).__name__}"
            )
        token = unicodedata.normalize("NFKC", raw).strip().lower()
        if not token:
            raise InvalidLifecycleEventError(
                f"{field}[{index}] is empty after canonicalisation"
            )
        if len(token) > 128:
            raise InvalidLifecycleEventError(
                f"{field}[{index}] must be <= 128 chars per the schema"
            )
        if not _CAPABILITY_RE.match(token):
            raise InvalidLifecycleEventError(
                f"{field}[{index}] {raw!r} does not match the verb.resource "
                "shape pinned by the schema"
            )
        if token in seen:
            # Silent dedup keeps the uniqueness guarantee intact.
            continue
        seen.add(token)
        out.append(token)
    return out


def ingest_lifecycle_event(
    raw_event: dict,
    lifecycle_event_ref: str,
) -> dict[str, Any]:
    """Canonicalise one operator-supplied lifecycle-event record.

    Inputs
    ------
    raw_event
        Operator-supplied JSON-native event record. Required keys:
        ``event_kind`` (joiner | mover | leaver), ``principal_type``,
        ``principal_id``, ``effective_at`` (ISO-8601 UTC). Optional:
        ``identity_provider``, ``add_set``, ``remove_set``.
    lifecycle_event_ref
        Operator-side opaque pointer to the source event record (carried
        through into the canonical record for join-back).

    Returns
    -------
    JSON-native dict with the closed envelope:
    ``{event_kind, principal_type, principal_id, identity_provider?,
    add_set, remove_set, effective_at, lifecycle_event_ref}``.
    """
    if not isinstance(raw_event, dict):
        raise InvalidLifecycleEventError(
            f"raw_event must be an object, got {type(raw_event).__name__}"
        )

    ref = _canonical_text(lifecycle_event_ref, "lifecycle_event_ref")
    if not _EVENT_REF_RE.match(ref):
        raise InvalidLifecycleEventError(
            f"lifecycle_event_ref {lifecycle_event_ref!r} does not match the "
            "expected opaque-pointer shape"
        )

    event_kind = _canonical_text(
        raw_event.get("event_kind"), "raw_event.event_kind"
    )
    if event_kind not in _ALLOWED_EVENT_KINDS:
        raise InvalidLifecycleEventError(
            f"raw_event.event_kind {event_kind!r} is not one of "
            f"{sorted(_ALLOWED_EVENT_KINDS)!r}"
        )

    ptype = _canonical_text(
        raw_event.get("principal_type"), "raw_event.principal_type"
    )
    if ptype not in _ALLOWED_PRINCIPAL_TYPES:
        raise InvalidLifecycleEventError(
            f"raw_event.principal_type {ptype!r} is not one of "
            f"{sorted(_ALLOWED_PRINCIPAL_TYPES)!r}; personal-user principals "
            "are out of scope for F-CP-07"
        )

    pid = _canonical_text(
        raw_event.get("principal_id"), "raw_event.principal_id"
    )
    if len(pid) > 200:
        raise InvalidLifecycleEventError(
            "raw_event.principal_id must be <= 200 chars per the schema"
        )
    if not _PRINCIPAL_ID_RE.match(pid):
        raise InvalidLifecycleEventError(
            f"raw_event.principal_id {pid!r} does not match the role-shaped "
            "pattern pinned by the schema; individual personal names and "
            "credential-shaped strings are out of scope per AGENTS.md \u00a73"
        )

    effective_at = _canonical_text(
        raw_event.get("effective_at"), "raw_event.effective_at"
    )
    if not _ISO_Z_RE.match(effective_at):
        raise InvalidLifecycleEventError(
            f"raw_event.effective_at {effective_at!r} is not ISO-8601 UTC "
            "'YYYY-MM-DDTHH:MM:SSZ'"
        )

    add_set = _validate_capability_set(
        raw_event.get("add_set", []), "raw_event.add_set"
    )
    remove_set = _validate_capability_set(
        raw_event.get("remove_set", []), "raw_event.remove_set"
    )
    overlap = set(add_set) & set(remove_set)
    if overlap:
        raise InvalidLifecycleEventError(
            f"raw_event.add_set and raw_event.remove_set overlap on "
            f"{sorted(overlap)!r}; a capability cannot be granted and "
            "revoked in the same lifecycle event"
        )

    if event_kind == "joiner":
        if not add_set:
            raise InvalidLifecycleEventError(
                "joiner events must declare a non-empty add_set"
            )
        if remove_set:
            raise InvalidLifecycleEventError(
                "joiner events must declare an empty remove_set"
            )
    elif event_kind == "leaver":
        if not remove_set:
            raise InvalidLifecycleEventError(
                "leaver events must declare a non-empty remove_set"
            )
        if add_set:
            raise InvalidLifecycleEventError(
                "leaver events must declare an empty add_set"
            )
    else:  # mover
        if not add_set and not remove_set:
            raise InvalidLifecycleEventError(
                "mover events must declare at least one of add_set or "
                "remove_set"
            )

    out: dict[str, Any] = {
        "event_kind": event_kind,
        "principal_type": ptype,
        "principal_id": pid,
        "add_set": add_set,
        "remove_set": remove_set,
        "effective_at": effective_at,
        "lifecycle_event_ref": ref,
    }

    if "identity_provider" in raw_event and raw_event["identity_provider"] is not None:
        idp = _canonical_text(
            raw_event["identity_provider"], "raw_event.identity_provider"
        )
        if not _IDENTITY_PROVIDER_RE.match(idp):
            raise InvalidLifecycleEventError(
                f"raw_event.identity_provider {idp!r} does not match the "
                "[a-z][a-z0-9_-]{0,63} shape pinned by the schema"
            )
        out["identity_provider"] = idp

    return out
