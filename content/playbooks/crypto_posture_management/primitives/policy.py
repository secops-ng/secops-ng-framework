"""Crypto-policy inventory primitive (inventory crypto policy).

Reads the operator's declared cryptography policy and the assets in scope for
one posture window, and returns the inventory the two probe steps classify
against.

**The clause vocabulary is what makes a finding interpretable.** Every clause
declares the *concern* it governs — a cipher-suite floor, a maximum
certificate validity, a key-rotation interval. That is what lets a downstream
finding say whether the observed posture contradicts a clause the policy does
state (a **drift**) or concerns something the policy is silent about (a
**gap**). Without the concern, both collapse into "non-compliant", and the two
have completely different remediation: a drift is an infrastructure fix, a gap
is a policy the operator has not written yet.

**No default baseline ships.** A shipped cipher floor would become a de-facto
standard this framework has no authority to set, and an operator scored against
someone else's baseline learns nothing about their own policy. An asset in
scope with no clause governing a concern yields a gap, not a silent pass.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
* **Determinism.** Same inputs => byte-identical output; clauses and assets
  are emitted sorted.
* **Public-bar safe.** Clause and asset identifiers are matched against closed
  regexes. No policy prose is accepted — the inventory carries references into
  the operator's own policy document, not its text.
* **Read-only-by-contract.** The policy and the asset register are read;
  neither is written.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "CRYPTO_CONCERNS",
    "InvalidCryptoPolicyError",
    "classify_against_policy",
    "inventory_crypto_policy",
]


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_WINDOW_RE = re.compile(r"^\d{4}-\d{2}-\d{2}/\d{4}-\d{2}-\d{2}$")

# The concerns a clause may govern. Closed, because the two probe steps
# classify against these names and a typo would otherwise read as a policy
# gap — the most misleading outcome available.
CRYPTO_CONCERNS: frozenset[str] = frozenset({
    "cipher_suite_floor",
    "certificate_validity_max_days",
    "key_rotation_interval_days",
    "protocol_version_floor",
})

# Verdicts the probe steps assign. `gap` and `drift` are deliberately
# distinct; see the module docstring.
CONFORMING = "conforming"
DRIFT = "drift"
GAP = "gap"

_SCHEMA_VERSION = "1.0.0"
_STREAM = "crypto_posture_management_policy"


class InvalidCryptoPolicyError(ValueError):
    """Raised when a policy input or clause invariant is violated."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidCryptoPolicyError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidCryptoPolicyError(f"{field} is empty after canonicalisation")
    return normalised


def _require_pattern(value: object, field: str, pattern: re.Pattern[str]) -> str:
    text = _canonical_text(value, field)
    if not pattern.match(text):
        raise InvalidCryptoPolicyError(
            f"{field} {text!r} does not match the schema pattern"
        )
    return text


def classify_against_policy(
    policy_inventory: dict, concern: str
) -> tuple[str, str]:
    """Return ``(clause_ref, verdict_when_absent)`` for one concern.

    A concern the inventory carries a clause for can produce
    :data:`DRIFT` or :data:`CONFORMING`; one it does not carry can only
    produce :data:`GAP`. Returning the clause reference alongside is what lets
    a finding name the clause it contradicts.
    """
    clauses = policy_inventory.get("clauses") or {}
    entry = clauses.get(concern)
    if entry is None:
        return "", GAP
    return entry["clause_ref"], DRIFT


def inventory_crypto_policy(
    posture_window: str,
    crypto_scope: str,
    policy_clauses: list,
    scoped_assets: list,
) -> dict:
    """Compose the crypto-policy inventory for one posture window.

    Args:
        posture_window: ``YYYY-MM-DD/YYYY-MM-DD`` (``__posture_window__``).
        crypto_scope: Identifier of the scope this run covers
            (``__crypto_scope__``).
        policy_clauses: Clause records, each with ``clause_ref``, ``concern``
            (one of :data:`CRYPTO_CONCERNS`) and ``threshold`` — an int for
            the day-count and floor concerns, a string for a named floor.
        scoped_assets: Asset identifiers in scope for this window.

    Returns:
        JSON-native inventory envelope with ``schema_version``, ``stream``,
        ``policy_inventory_id``, ``posture_window``, ``crypto_scope``,
        ``clauses`` keyed by concern, ``governed_concerns``,
        ``ungoverned_concerns`` and sorted ``assets``.

    Raises:
        InvalidCryptoPolicyError: any input fails validation, a concern is
            unknown or declared twice, or the window is malformed.
    """
    window = _canonical_text(posture_window, "posture_window")
    if not _WINDOW_RE.match(window):
        raise InvalidCryptoPolicyError(
            f"posture_window {window!r} is not YYYY-MM-DD/YYYY-MM-DD"
        )
    start, end = window.split("/")
    if start >= end:
        raise InvalidCryptoPolicyError(
            f"posture_window {window!r} does not start before it ends"
        )
    scope = _require_pattern(crypto_scope, "crypto_scope", _ID_RE)

    if isinstance(policy_clauses, str) or not isinstance(
        policy_clauses, (list, tuple)
    ):
        raise InvalidCryptoPolicyError("policy_clauses must be a list of clauses")
    clauses: dict[str, dict] = {}
    for i, record in enumerate(policy_clauses):
        if not isinstance(record, dict):
            raise InvalidCryptoPolicyError(
                f"policy_clauses[{i}] must be a mapping, got "
                f"{type(record).__name__}"
            )
        concern = _canonical_text(
            record.get("concern"), f"policy_clauses[{i}].concern"
        )
        if concern not in CRYPTO_CONCERNS:
            raise InvalidCryptoPolicyError(
                f"policy_clauses[{i}].concern {concern!r} not in "
                f"{sorted(CRYPTO_CONCERNS)}"
            )
        if concern in clauses:
            raise InvalidCryptoPolicyError(
                f"policy_clauses[{i}] declares {concern!r} a second time; two "
                f"clauses governing one concern make the verdict ambiguous"
            )
        clause_ref = _require_pattern(
            record.get("clause_ref"), f"policy_clauses[{i}].clause_ref", _REF_RE
        )
        threshold = record.get("threshold")
        if isinstance(threshold, bool) or threshold is None:
            raise InvalidCryptoPolicyError(
                f"policy_clauses[{i}].threshold must be an int or a named floor"
            )
        if isinstance(threshold, int):
            if threshold < 0:
                raise InvalidCryptoPolicyError(
                    f"policy_clauses[{i}].threshold must be non-negative"
                )
            value: object = threshold
        else:
            value = _canonical_text(
                threshold, f"policy_clauses[{i}].threshold"
            )
        clauses[concern] = {"clause_ref": clause_ref, "threshold": value}

    if isinstance(scoped_assets, str) or not isinstance(
        scoped_assets, (list, tuple)
    ):
        raise InvalidCryptoPolicyError("scoped_assets must be a list of ids")
    assets = sorted({
        _require_pattern(a, f"scoped_assets[{i}]", _ID_RE)
        for i, a in enumerate(scoped_assets)
    })
    if not assets:
        raise InvalidCryptoPolicyError(
            "scoped_assets is empty; a posture window covering no asset is a "
            "finding about the scope definition rather than an empty inventory"
        )

    return {
        "schema_version": _SCHEMA_VERSION,
        "stream": _STREAM,
        "policy_inventory_id": f"{scope}:{window}",
        "posture_window": window,
        "window_start": start,
        "window_end": end,
        "crypto_scope": scope,
        "clauses": {k: clauses[k] for k in sorted(clauses)},
        "governed_concerns": sorted(clauses),
        "ungoverned_concerns": sorted(CRYPTO_CONCERNS - set(clauses)),
        "assets": assets,
    }
