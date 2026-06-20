"""Grant/revoke confirmation primitive (confirm-grant-revoke).

Pure derivation. Given the applied capability delta and the operator-
supplied observed capability list (read back from the identity source
*after* the delta was applied), return the closed observed capability
list, a ``confirmed`` boolean, and the divergence detail (missing
grants, lingering revokes) the access-evidence artifact carries
downstream.

Design constraints
------------------

* **Pure / replayable.** No network, no clock reads, no LLMs. The
  observed list arrives as a JSON-native list of verb.resource tokens
  the runtime walked from the operator's identity source on the
  read-back step.
* **Closed observed list.** Same verb.resource shape, same canonicalisation
  (NFKC + lower-case + exact-match dedup) as the upstream capability
  list primitives so two replays of the same read-back collapse to
  byte-identical bytes.
* **Divergence is data, not an exception.** A missing grant or a
  lingering revoke surfaces as ``confirmed=False`` plus the divergence
  detail on the emitted artifact — the workflow does NOT raise in
  that case, because the access-evidence artifact's job is to *record*
  the divergence for downstream reviewers.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

__all__ = [
    "InvalidConfirmationError",
    "confirm_grant_revoke",
]


_CAPABILITY_RE = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")


class InvalidConfirmationError(ValueError):
    """Raised when the confirmation inputs cannot produce a valid record."""


def _canonicalise_observed(value: object) -> list[str]:
    if not isinstance(value, list):
        raise InvalidConfirmationError(
            f"observed_capabilities must be a list, got {type(value).__name__}"
        )
    seen: set[str] = set()
    out: list[str] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, str):
            raise InvalidConfirmationError(
                f"observed_capabilities[{index}] must be a string, got "
                f"{type(raw).__name__}"
            )
        token = unicodedata.normalize("NFKC", raw).strip().lower()
        if not token or not _CAPABILITY_RE.match(token) or len(token) > 128:
            raise InvalidConfirmationError(
                f"observed_capabilities[{index}] {raw!r} does not match the "
                "verb.resource shape pinned by the schema"
            )
        if token in seen:
            continue
        seen.add(token)
        out.append(token)
    return out


def confirm_grant_revoke(
    capability_delta: dict,
    observed_capabilities: list,
) -> dict[str, Any]:
    """Compare the observed capability list against the declared delta.

    Inputs
    ------
    capability_delta
        The closed delta produced by
        :func:`...primitives.delta.apply_capability_delta`.
    observed_capabilities
        Operator-supplied JSON-native list of verb.resource tokens the
        runtime walked from the operator's identity source on the
        read-back step (after the delta was applied).

    Returns
    -------
    JSON-native dict with the closed observed list and the divergence
    detail::

        {
            "confirmed": bool,
            "capabilities": [...],            # closed observed list
            "missing_grants": [...],          # add-set entries not observed
            "lingering_revokes": [...],       # remove-set entries still
                                              # observed
        }
    """
    if not isinstance(capability_delta, dict):
        raise InvalidConfirmationError(
            "capability_delta must be an object, got "
            f"{type(capability_delta).__name__}"
        )

    add_set_raw = capability_delta.get("add_set")
    remove_set_raw = capability_delta.get("remove_set")
    if not isinstance(add_set_raw, list) or not isinstance(remove_set_raw, list):
        raise InvalidConfirmationError(
            "capability_delta must carry list-typed add_set and remove_set"
        )
    add_set = set(add_set_raw)
    remove_set = set(remove_set_raw)

    observed = _canonicalise_observed(observed_capabilities)
    observed_set = set(observed)

    missing_grants = sorted(add_set - observed_set)
    lingering_revokes = sorted(observed_set & remove_set)
    confirmed = not missing_grants and not lingering_revokes

    return {
        "confirmed": confirmed,
        "capabilities": observed,
        "missing_grants": missing_grants,
        "lingering_revokes": lingering_revokes,
    }
