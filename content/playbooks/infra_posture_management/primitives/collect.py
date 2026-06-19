"""Posture-state collector primitive (collect-posture).

Canonicalises an operator-supplied raw posture-collection snapshot into
the closed ``posture_state`` block the F-WF-06 schema pins. The compile
target's runtime walks the operator's posture sources (cloud account
read APIs, identity-provider read APIs, network-baseline read APIs)
upstream — this primitive only normalises and hashes the resulting
list so the downstream artifact builder can shape the record without
re-deriving the same checks.

Design constraints
------------------

* **Pure / replayable.** No network, no clock, no LLMs. The
  ``scope_ref`` is operator-side; the framework does not interpret it.
* **Deterministic.** Resources are sorted on ``resource_id`` and exact-
  match duplicates collapse so the ``snapshot_hash`` is byte-stable
  under re-runs of the same collection walk.
* **Sovereign-stack neutral.** No vendor SDK is imported; the
  ``raw_posture`` argument is an operator-side JSON-native list.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any

__all__ = [
    "InvalidPostureStateError",
    "collect_posture_state",
]


_RESOURCE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:/@-]{0,254}$")


class InvalidPostureStateError(ValueError):
    """Raised when the inputs cannot produce a valid posture-state block."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidPostureStateError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidPostureStateError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _canonical_resource(entry: object, position: int) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise InvalidPostureStateError(
            f"raw_posture[{position}] must be an object, got "
            f"{type(entry).__name__}"
        )
    rid = entry.get("resource_id")
    rid_text = _canonical_text(rid, f"raw_posture[{position}].resource_id")
    if not _RESOURCE_ID_RE.match(rid_text):
        raise InvalidPostureStateError(
            f"raw_posture[{position}].resource_id {rid!r} does not match "
            "the role-shaped pattern pinned for posture resources; "
            "personal names, raw secrets, and free text are out of scope "
            "per AGENTS.md \u00a73"
        )
    config = entry.get("configuration", {})
    if not isinstance(config, dict):
        raise InvalidPostureStateError(
            f"raw_posture[{position}].configuration must be an object, got "
            f"{type(config).__name__}"
        )
    return {"resource_id": rid_text, "configuration": config}


def collect_posture_state(
    raw_posture: list,
    scope_ref: str,
) -> dict[str, Any]:
    """Build the canonical ``posture_state`` block.

    Inputs
    ------
    raw_posture
        Operator-supplied list of resources walked under the declared
        scope. Each entry is a JSON-native object with a role-shaped
        ``resource_id`` and a ``configuration`` sub-object the operator's
        collector produced.
    scope_ref
        Opaque pointer back to the operator's in-scope infrastructure
        manifest. The framework does not interpret it.

    Returns
    -------
    JSON-native dict matching the ``posture_state`` block of
    ``schemas/evidence/posture.schema.json`` plus an internal
    ``resources`` list the downstream artifact builder can hash or
    ignore. The ``snapshot_hash`` is the SHA-256 of the canonicalised
    resource list serialised with ``sort_keys=True``.
    """
    scope_text = _canonical_text(scope_ref, "scope_ref")
    if len(scope_text) > 400:
        raise InvalidPostureStateError(
            "scope_ref must be <= 400 chars per the schema"
        )
    if not isinstance(raw_posture, list):
        raise InvalidPostureStateError(
            f"raw_posture must be a list, got {type(raw_posture).__name__}"
        )

    seen: set[str] = set()
    canonical: list[dict[str, Any]] = []
    for index, entry in enumerate(raw_posture):
        item = _canonical_resource(entry, index)
        rid = item["resource_id"]
        if rid in seen:
            # Exact-match repeats collapse so re-runs that emit the same
            # resource twice do not corrupt the snapshot_hash.
            continue
        seen.add(rid)
        canonical.append(item)

    canonical.sort(key=lambda item: item["resource_id"])
    serialized = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    snapshot_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    return {
        "scope_ref": scope_text,
        "resource_count": len(canonical),
        "snapshot_hash": snapshot_hash,
        "resources": canonical,
    }
