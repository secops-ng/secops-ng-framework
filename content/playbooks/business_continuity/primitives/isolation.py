"""Isolation-scope resolution primitive (isolate_affected_systems step).

Resolves the isolation scope from the activated plan's documented
isolation targets. Executing the isolation against the operator's
isolation surface is the compile target's adapter concern; what is
deterministic here is the scope identity and the skip semantics.

Design constraints
------------------

* **Skipping is data (pinned by tests).** Where the plan documents no
  isolation step for the event class — a pure availability outage with
  no compromise indicator, or no plan on file at all — the step is
  skipped with an empty ``__isolation_scope__``, exactly as the step
  text specifies. A skip is a recorded decision, never an error.
* **Deterministic scope identity.** ``scope_id`` is ``bcm-iso-`` + 24
  hex over the event id and the ordered target set, so a replayed
  isolation resolves to the same scope and the cutback discipline in
  restore-and-verify can key on it.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

__all__ = [
    "InvalidIsolationScopeError",
    "resolve_isolation_scope",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")


class InvalidIsolationScopeError(ValueError):
    """Raised when the activation envelope cannot resolve a scope."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidIsolationScopeError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidIsolationScopeError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidIsolationScopeError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def resolve_isolation_scope(activation: dict) -> dict:
    """Resolve the isolation scope for one activated event.

    Inputs
    ------
    activation
        The activation envelope
        (:func:`.activation.activate_bcm_plan` output); reads
        ``event_id`` and ``isolation_targets``.

    Returns
    -------
    JSON-native isolation scope::

        {
            "event_id": "...",
            "scope_id": "bcm-iso-<24 hex>" | "",
            "skipped": <bool>,
            "targets": [...]
        }

    ``scope_id`` is the empty string exactly when the plan documents no
    isolation targets (``skipped: true``) — the empty
    ``__isolation_scope__`` contract from the step text.
    """
    if not isinstance(activation, dict):
        raise InvalidIsolationScopeError(
            f"activation must be an object, got {type(activation).__name__}"
        )
    event_id = _canonical_pointer(
        activation.get("event_id"), "activation.event_id"
    )
    targets_raw = activation.get("isolation_targets")
    if not isinstance(targets_raw, list):
        raise InvalidIsolationScopeError(
            "activation.isolation_targets must be a list (possibly empty)"
        )
    targets = []
    seen = set()
    for index, ref in enumerate(targets_raw):
        canonical = _canonical_pointer(
            ref, f"activation.isolation_targets[{index}]"
        )
        if canonical in seen:
            continue
        seen.add(canonical)
        targets.append(canonical)

    if not targets:
        return {
            "event_id": event_id,
            "scope_id": "",
            "skipped": True,
            "targets": [],
        }

    digest = hashlib.sha256(
        (event_id + "|" + json.dumps(targets)).encode("utf-8")
    ).hexdigest()
    return {
        "event_id": event_id,
        "scope_id": "bcm-iso-" + digest[:24],
        "skipped": False,
        "targets": targets,
    }
