"""Micro-segmentation rule derivation primitive (contain step).

Turns the resolved lateral-movement path into the deterministic set of
deny rules the network adapter applies, bounded by the
operator-supplied authorisation policy: an edge whose scope the policy
does not authorise fails loud — the primitive must never widen the
containment blast radius beyond what the operator signed off.

Design constraints
------------------

* **Pure / replayable.** No network calls; the segmentation surface
  (firewall, service mesh, identity-aware proxy) is the compile
  target's adapter downstream.
* **Deterministic rule identity.** Each ``rule_id`` is ``atr-seg-`` +
  the first 24 hex chars of SHA-256 over the edge triple
  (source | destination | edge_kind), so a replayed containment
  resolves to the same rules — idempotent application is a property
  of the derivation, not of firewall state.
* **Dedup asymmetry (pinned by tests).** The same edge observed twice
  collapses to one rule (containment is idempotent); the same edge
  triple carrying two *different* scopes fails loud — ambiguous
  authorisation must never silently pick a side.
* **Authorisation is a hard bound.** Every edge scope must appear in
  ``authorisation_policy.authorised_scopes``; an unauthorised edge
  raises rather than being skipped, because a partially-applied
  containment that looks complete is worse than a loud stop.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

__all__ = [
    "InvalidSegmentationInputError",
    "UnauthorisedSegmentError",
    "derive_segmentation_rules",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_EDGE_KINDS = frozenset({"network", "identity"})


class InvalidSegmentationInputError(ValueError):
    """Raised when the path or policy cannot produce valid rules."""


class UnauthorisedSegmentError(ValueError):
    """Raised when an edge falls outside the authorised scope set."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidSegmentationInputError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidSegmentationInputError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidSegmentationInputError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def derive_segmentation_rules(
    lateral_path: list, authorisation_policy: dict
) -> dict:
    """Derive the deny-rule set for one resolved lateral-movement path.

    Inputs
    ------
    lateral_path
        Non-empty list of implicated edges (the hydrated indicator's
        ``edges``), each an object with role-shaped ``source``,
        ``destination`` and ``scope`` plus ``edge_kind`` of
        ``network`` | ``identity``.
    authorisation_policy
        Operator-supplied bound: an object whose
        ``authorised_scopes`` is a non-empty list of role-shaped scope
        pointers the operator has signed off for containment action.

    Returns
    -------
    JSON-native segmentation plan::

        {
            "rules": [
                {"rule_id": "atr-seg-<24 hex>", "action": "deny_pivot",
                 "source": "...", "destination": "...",
                 "edge_kind": "...", "scope": "..."},
                ...
            ]
        }

    Rules keep first-observation order of their edge triples; duplicate
    observations of the same triple collapse into the first.
    """
    if not isinstance(lateral_path, list) or not lateral_path:
        raise InvalidSegmentationInputError(
            "lateral_path must be a non-empty list of edges"
        )
    if not isinstance(authorisation_policy, dict):
        raise InvalidSegmentationInputError(
            "authorisation_policy must be an object, got "
            f"{type(authorisation_policy).__name__}"
        )
    scopes_raw = authorisation_policy.get("authorised_scopes")
    if not isinstance(scopes_raw, list) or not scopes_raw:
        raise InvalidSegmentationInputError(
            "authorisation_policy.authorised_scopes must be a non-empty "
            "list"
        )
    authorised = {
        _canonical_pointer(
            s, f"authorisation_policy.authorised_scopes[{i}]"
        )
        for i, s in enumerate(scopes_raw)
    }

    rules: list[dict] = []
    seen: dict[tuple, str] = {}
    for index, edge in enumerate(lateral_path):
        field = f"lateral_path[{index}]"
        if not isinstance(edge, dict):
            raise InvalidSegmentationInputError(
                f"{field} must be an object, got {type(edge).__name__}"
            )
        kind = edge.get("edge_kind")
        if not isinstance(kind, str) or kind not in _EDGE_KINDS:
            raise InvalidSegmentationInputError(
                f"{field}.edge_kind {kind!r} is not one of "
                f"{sorted(_EDGE_KINDS)}"
            )
        source = _canonical_pointer(edge.get("source"), f"{field}.source")
        destination = _canonical_pointer(
            edge.get("destination"), f"{field}.destination"
        )
        scope = _canonical_pointer(edge.get("scope"), f"{field}.scope")
        if scope not in authorised:
            raise UnauthorisedSegmentError(
                f"{field} scope {scope!r} is not in the operator's "
                "authorised scope set; refusing to widen containment "
                "beyond the signed-off bound"
            )

        triple = (source, destination, kind)
        if triple in seen:
            if seen[triple] != scope:
                raise InvalidSegmentationInputError(
                    f"{field} repeats edge {source!r} -> {destination!r} "
                    f"({kind}) with scope {scope!r} after scope "
                    f"{seen[triple]!r}; ambiguous authorisation must not "
                    "silently pick a side"
                )
            continue
        seen[triple] = scope

        digest = hashlib.sha256(
            (source + "|" + destination + "|" + kind).encode("utf-8")
        ).hexdigest()
        rules.append(
            {
                "rule_id": "atr-seg-" + digest[:24],
                "action": "deny_pivot",
                "source": source,
                "destination": destination,
                "edge_kind": kind,
                "scope": scope,
            }
        )

    return {"rules": rules}
