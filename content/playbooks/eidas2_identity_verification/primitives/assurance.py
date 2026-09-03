"""Assurance-level assessment primitive (assess step).

Maps the Level of Assurance carried on the verified PID credential to
the operator-side access tier for the scope, per the operator's
documented assurance-to-tier table — and refuses explicitly where the
mapping cannot lawfully assign a tier.

Design constraints
------------------

* **Pure / replayable.** The mapping table is operator input; the
  primitive applies it.
* **No partial-trust state (acceptance criterion, pinned by tests).**
  Three explicit outcomes: ``tier_assigned``,
  ``refused_verification_failed`` (the verify step's false verdict
  short-circuits: the returned LoA is recorded but the tier stays
  empty), and ``refused_below_minimum`` (the returned LoA sits below
  the scope's declared minimum — the drift case; the principal is
  never quietly downgraded onto a lower tier).
* **An undocumented mapping fails loud.** A scope missing from the
  table, or a table row missing the returned LoA's tier, is operator
  documentation the provisioning hand-off cannot proceed without —
  silently inventing a tier would be a de-facto policy the framework
  has no authority to set.
* **The LoA ladder is closed and ordered** (``low`` <
  ``substantial`` < ``high``, the eIDAS 2.0 vocabulary).
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidAssuranceInputError",
    "assess_assurance_level",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_LOA_LADDER = ("low", "substantial", "high")


class InvalidAssuranceInputError(ValueError):
    """Raised when the assessment inputs cannot produce an outcome."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidAssuranceInputError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidAssuranceInputError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidAssuranceInputError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def _canonical_loa(value: object, field: str) -> str:
    loa = _canonical_pointer(value, field)
    if loa not in _LOA_LADDER:
        raise InvalidAssuranceInputError(
            f"{field} {loa!r} is not on the eIDAS 2.0 assurance ladder "
            f"{list(_LOA_LADDER)}"
        )
    return loa


def assess_assurance_level(
    loa_verdict: str,
    auth_scope: str,
    assurance_tier_table: dict,
    verification_verdict: bool,
) -> dict:
    """Assess one verified presentation against the tier table.

    Inputs
    ------
    loa_verdict
        The assurance level returned on the PID credential
        (``__loa_verdict__``): ``low`` / ``substantial`` / ``high``.
    auth_scope
        The access surface (``__auth_scope__``).
    assurance_tier_table
        The operator's documented mapping: an object keyed by scope,
        each row an object with ``minimum_loa`` (ladder value) and
        ``tier_by_loa`` (map of ladder value to role-shaped tier id
        for every level at or above the minimum).
    verification_verdict
        The verify step's verdict (``__verification_verdict__``) as a
        real boolean — a string ``"false"`` is truthy and would tier
        an unverified principal.

    Returns
    -------
    JSON-native assessment::

        {
            "loa_verdict": "...",
            "auth_scope": "...",
            "access_tier": "..." | "",
            "assessment": "tier_assigned"
                          | "refused_verification_failed"
                          | "refused_below_minimum",
            "minimum_loa": "..." | None
        }
    """
    loa = _canonical_loa(loa_verdict, "loa_verdict")
    scope = _canonical_pointer(auth_scope, "auth_scope")
    if not isinstance(verification_verdict, bool):
        raise InvalidAssuranceInputError(
            "verification_verdict must be a boolean, got "
            f"{type(verification_verdict).__name__} — a string 'false' is "
            "truthy and would tier an unverified principal"
        )

    if not verification_verdict:
        # Short-circuit (step contract): the returned LoA is recorded,
        # the tier stays empty, provisioning is never triggered.
        return {
            "loa_verdict": loa,
            "auth_scope": scope,
            "access_tier": "",
            "assessment": "refused_verification_failed",
            "minimum_loa": None,
        }

    if not isinstance(assurance_tier_table, dict):
        raise InvalidAssuranceInputError(
            "assurance_tier_table must be an object, got "
            f"{type(assurance_tier_table).__name__}"
        )
    row = assurance_tier_table.get(scope)
    if not isinstance(row, dict):
        raise InvalidAssuranceInputError(
            f"auth_scope {scope!r} has no documented assurance-to-tier "
            "row; provisioning cannot proceed against an undocumented "
            "mapping"
        )
    minimum = _canonical_loa(
        row.get("minimum_loa"), f"assurance_tier_table[{scope!r}].minimum_loa"
    )

    if _LOA_LADDER.index(loa) < _LOA_LADDER.index(minimum):
        # The drift case: below the declared minimum is an explicit
        # refusal, never a quiet downgrade onto a lower tier.
        return {
            "loa_verdict": loa,
            "auth_scope": scope,
            "access_tier": "",
            "assessment": "refused_below_minimum",
            "minimum_loa": minimum,
        }

    tiers = row.get("tier_by_loa")
    if not isinstance(tiers, dict) or loa not in tiers:
        raise InvalidAssuranceInputError(
            f"assurance_tier_table[{scope!r}].tier_by_loa carries no tier "
            f"for LoA {loa!r}; a tier the operator never documented cannot "
            "be invented"
        )
    tier = _canonical_pointer(
        tiers[loa], f"assurance_tier_table[{scope!r}].tier_by_loa[{loa!r}]"
    )

    return {
        "loa_verdict": loa,
        "auth_scope": scope,
        "access_tier": tier,
        "assessment": "tier_assigned",
        "minimum_loa": minimum,
    }
