"""Policy-inventory resolution primitive (resolve-policy-inventory step).

Resolves the operator's declared cryptography policy for the in-scope
surface into the snapshot every downstream lifecycle branch measures
against. The policy is input, not content (acceptance criterion): the
framework ships no default cipher baseline — a shipped baseline would
become a de-facto standard the framework has no authority to set — so
an absent clause stays absent, explicitly flagged, and is never filled
with a default.

Design constraints
------------------

* **Pure / replayable.** No policy-store reads; the adapter resolves
  the operator's documented policy and hands it over.
* **Gaps are flagged, never filled (pinned by tests).** A missing
  policy — or any missing clause — yields an inventory whose
  ``undocumented_clauses`` names the gap; the downstream branches
  still run and record the missing-policy condition on the
  attestation rather than proceeding silently (step contract). No
  clause ever acquires a value the operator did not declare.
* **Closed clause vocabulary.** The seven clauses the variable table
  names: symmetric / asymmetric algorithm allow-lists, per-algorithm
  minimum key bits, per-key-class rotation cadence, the TLS-version
  floor, the declared trust anchors, and the certificate expiry
  buffer. Unknown clause keys fail loud — a misspelled clause that
  silently vanished would report as a gap the operator believes is
  covered.
* **Content-derived identity.** ``__policy_inventory_id__`` is
  ``cc-pol-`` + 24 hex over the scope and the canonical snapshot, so
  the same declared policy resolves to the same snapshot id.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

__all__ = [
    "InvalidPolicyDeclarationError",
    "resolve_policy_inventory",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_DURATION_RE = re.compile(r"^P(?!$)(\d+D)?(T(?=\d)(\d+H)?(\d+M)?(\d+S)?)?$")

_TLS_LADDER = ("1.0", "1.1", "1.2", "1.3")

_CLAUSES = (
    "symmetric_algorithms",
    "asymmetric_algorithms",
    "minimum_key_bits",
    "rotation_cadence",
    "tls_version_floor",
    "trust_anchors",
    "certificate_expiry_buffer",
)


class InvalidPolicyDeclarationError(ValueError):
    """Raised when a declared clause cannot be validated."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidPolicyDeclarationError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidPolicyDeclarationError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidPolicyDeclarationError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def _canonical_name_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise InvalidPolicyDeclarationError(
            f"{field} must be a non-empty list when declared"
        )
    names = []
    for index, item in enumerate(value):
        names.append(_canonical_pointer(item, f"{field}[{index}]"))
    return sorted(set(names))


def _canonical_bits(value: object, field: str) -> int:
    # bool is an int subclass; True would otherwise declare a 1-bit floor.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidPolicyDeclarationError(
            f"{field} must be an integer, got {type(value).__name__}"
        )
    if value <= 0:
        raise InvalidPolicyDeclarationError(
            f"{field} must be positive, got {value!r}"
        )
    return value


def _canonical_duration(value: object, field: str) -> str:
    text = _canonical_pointer(value, field)
    if not _DURATION_RE.match(text):
        raise InvalidPolicyDeclarationError(
            f"{field} {text!r} is not an ISO-8601 duration (e.g. P30D)"
        )
    return text


def resolve_policy_inventory(
    crypto_scope: str, declared_policy: dict | None
) -> dict:
    """Resolve the policy snapshot for one lifecycle run.

    Inputs
    ------
    crypto_scope
        Role-shaped identifier of the in-scope cryptography surface
        (``__crypto_scope__``).
    declared_policy
        The operator's documented policy for the scope, or ``None``
        when no policy is declared. When present, an object carrying
        any subset of the closed clause vocabulary:
        ``symmetric_algorithms`` / ``asymmetric_algorithms``
        (non-empty allow-lists), ``minimum_key_bits`` (map of
        algorithm name to positive integer bits), ``rotation_cadence``
        (map of key class to ISO-8601 duration), ``tls_version_floor``
        (one of 1.0 / 1.1 / 1.2 / 1.3), ``trust_anchors`` (non-empty
        list of CA refs), ``certificate_expiry_buffer`` (ISO-8601
        duration). Unknown keys fail loud.

    Returns
    -------
    JSON-native policy inventory::

        {
            "policy_inventory_id": "cc-pol-<24 hex>",
            "crypto_scope": "...",
            "policy_declared": <bool>,
            "clauses": {<clause>: <value> | None, ...},   # all seven keys
            "undocumented_clauses": [<clause>, ...]        # sorted
        }
    """
    scope = _canonical_pointer(crypto_scope, "crypto_scope")

    clauses: dict = {name: None for name in _CLAUSES}
    if declared_policy is not None:
        if not isinstance(declared_policy, dict):
            raise InvalidPolicyDeclarationError(
                "declared_policy must be an object or None, got "
                f"{type(declared_policy).__name__}"
            )
        unknown = set(declared_policy) - set(_CLAUSES)
        if unknown:
            raise InvalidPolicyDeclarationError(
                f"declared_policy carries unknown clauses {sorted(unknown)}; "
                f"the clause vocabulary is closed over {list(_CLAUSES)} — a "
                "misspelled clause silently dropped would report as an "
                "operator gap"
            )
        for name in ("symmetric_algorithms", "asymmetric_algorithms"):
            if declared_policy.get(name) is not None:
                clauses[name] = _canonical_name_list(
                    declared_policy[name], f"declared_policy.{name}"
                )
        if declared_policy.get("minimum_key_bits") is not None:
            raw = declared_policy["minimum_key_bits"]
            if not isinstance(raw, dict) or not raw:
                raise InvalidPolicyDeclarationError(
                    "declared_policy.minimum_key_bits must be a non-empty "
                    "object when declared"
                )
            clauses["minimum_key_bits"] = {
                _canonical_pointer(
                    k, "declared_policy.minimum_key_bits key"
                ): _canonical_bits(
                    v, f"declared_policy.minimum_key_bits[{k!r}]"
                )
                for k, v in raw.items()
            }
        if declared_policy.get("rotation_cadence") is not None:
            raw = declared_policy["rotation_cadence"]
            if not isinstance(raw, dict) or not raw:
                raise InvalidPolicyDeclarationError(
                    "declared_policy.rotation_cadence must be a non-empty "
                    "object when declared"
                )
            clauses["rotation_cadence"] = {
                _canonical_pointer(
                    k, "declared_policy.rotation_cadence key"
                ): _canonical_duration(
                    v, f"declared_policy.rotation_cadence[{k!r}]"
                )
                for k, v in raw.items()
            }
        if declared_policy.get("tls_version_floor") is not None:
            floor = _canonical_pointer(
                declared_policy["tls_version_floor"],
                "declared_policy.tls_version_floor",
            )
            if floor not in _TLS_LADDER:
                raise InvalidPolicyDeclarationError(
                    f"declared_policy.tls_version_floor {floor!r} is not "
                    f"one of {list(_TLS_LADDER)}"
                )
            clauses["tls_version_floor"] = floor
        if declared_policy.get("trust_anchors") is not None:
            clauses["trust_anchors"] = _canonical_name_list(
                declared_policy["trust_anchors"],
                "declared_policy.trust_anchors",
            )
        if declared_policy.get("certificate_expiry_buffer") is not None:
            clauses["certificate_expiry_buffer"] = _canonical_duration(
                declared_policy["certificate_expiry_buffer"],
                "declared_policy.certificate_expiry_buffer",
            )

    undocumented = sorted(
        name for name in _CLAUSES if clauses[name] is None
    )
    body = {
        "crypto_scope": scope,
        "policy_declared": declared_policy is not None,
        "clauses": clauses,
        "undocumented_clauses": undocumented,
    }
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {"policy_inventory_id": "cc-pol-" + digest[:24], **body}
