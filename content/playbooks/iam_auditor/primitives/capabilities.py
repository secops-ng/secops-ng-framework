"""Capability-list builder primitive (enumerate-capabilities).

Canonicalises the closed verb.resource capability list the resolved
caller identity held at execution time. The compile target's runtime
walks the upstream IAM provider; this primitive only validates and
canonicalises the resulting list to the F-CP-07 schema discipline so
the downstream ``build_access_artifact`` primitive can shape the
record without re-deriving the same checks.

Design constraints
------------------

* **Closed list.** No implicit grants, no wildcards. Each entry is a
  single ``verb.resource`` token (lower-snake-case verb, single dot,
  lower-snake-case resource). The runtime-side assertion is paired
  with the F-PT-01 platform-side guarantee that the caller actually
  held the listed capabilities at boot — that orthogonal check is out
  of scope here.
* **Determinism.** The output preserves the operator-supplied order
  *and* dedups exact-match repeats. Two replays of the same identity
  walk against the same provider produce byte-identical bytes.
* **Public-bar safe.** Free text, wildcards, and credential-shaped
  strings are rejected at the regex boundary so the artifact never
  carries a token that would leak operator-internal vocabulary.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidCapabilityListError",
    "build_capability_list",
]


# Mirrors schemas/evidence/access.schema.json#/properties/capabilities/
# items/pattern.
_CAPABILITY_RE = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")


class InvalidCapabilityListError(ValueError):
    """Raised when the capability inputs cannot produce a valid list."""


def _canonical_capability(value: object, position: int) -> str:
    if not isinstance(value, str):
        raise InvalidCapabilityListError(
            f"capabilities[{position}] must be a string, got "
            f"{type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip().lower()
    if not normalised:
        raise InvalidCapabilityListError(
            f"capabilities[{position}] is empty after canonicalisation"
        )
    if len(normalised) > 128:
        raise InvalidCapabilityListError(
            f"capabilities[{position}] must be <= 128 chars per the schema"
        )
    if not _CAPABILITY_RE.match(normalised):
        raise InvalidCapabilityListError(
            f"capabilities[{position}] {value!r} does not match the "
            "verb.resource shape pinned by the schema; wildcards, free "
            "text, and credential-shaped strings are rejected at the "
            "schema boundary"
        )
    return normalised


def build_capability_list(capabilities: list) -> list:
    """Canonicalise a raw capability list to the schema contract.

    Inputs
    ------
    capabilities
        Operator-supplied list of ``verb.resource`` tokens. Order is
        the caller's; this primitive preserves first-seen order and
        drops exact-match repeats so a runtime that emits the same
        capability twice does not corrupt the artifact's uniqueness
        guarantee.

    Returns
    -------
    JSON-native list of canonical capability strings ready for the
    downstream :func:`...primitives.artifact.build_access_artifact`
    call.
    """
    if not isinstance(capabilities, list):
        raise InvalidCapabilityListError(
            f"capabilities must be a list, got {type(capabilities).__name__}"
        )
    if not capabilities:
        raise InvalidCapabilityListError(
            "capabilities must carry at least one entry; an execution "
            "with no declared capabilities is not the F-CP-07 artifact"
        )

    seen: set[str] = set()
    out: list[str] = []
    for index, raw in enumerate(capabilities):
        token = _canonical_capability(raw, index)
        if token in seen:
            # Exact-match repeats are dropped; the schema pins
            # uniqueness so silent dedup keeps the contract intact
            # without forcing the upstream walker to track state.
            continue
        seen.add(token)
        out.append(token)
    return out
