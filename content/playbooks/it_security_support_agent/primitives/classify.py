"""Support-request classification primitive (classify-request).

Pure derivation: takes the ingested support-request record produced by
:func:`...primitives.ingest.ingest_support_request` and the operator-
supplied classification-policy table, returns the closed classification
verdict envelope. Deterministic on the same record + same policy version
— re-runs collapse to byte-identical bytes at the verdict layer.

Closed verdict shape
--------------------

* ``category``     — one of ``informational``, ``actionable``,
                     ``incident-shaped``.
* ``severity``     — one of ``Informational``, ``Low``, ``Medium``,
                     ``High``, ``Critical`` (mirrors the F-CP-02
                     incidents-schema severity band).
* ``rule_ids``     — ordered list of policy-rule ids that fired,
                     shape ``[a-z][a-z0-9_]*\\.[a-z][a-z0-9_]*$``.
                     The first segment is the rule family (``cls``,
                     ``sev``, etc.); the second is the rule slug.
* ``policy_version`` — opaque operator-supplied policy version string,
                     carried through for replay-vs-original diffing.

The policy table itself is operator-supplied and out of scope at the
primitive layer; this primitive only validates the closed verdict
shape so a free-text category or a wildcard severity cannot slip past
the step boundary.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

__all__ = [
    "InvalidClassificationError",
    "classify_request",
]


_ALLOWED_REQUEST_KINDS = frozenset(
    {"informational", "actionable", "incident-shaped"}
)
_ALLOWED_CATEGORIES = frozenset(
    {"informational", "actionable", "incident-shaped"}
)
_ALLOWED_SEVERITIES = frozenset(
    {"Informational", "Low", "Medium", "High", "Critical"}
)
_RULE_ID_RE = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
_POLICY_VERSION_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$")


class InvalidClassificationError(ValueError):
    """Raised when the classification inputs cannot produce a valid verdict."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidClassificationError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidClassificationError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def classify_request(
    support_request_record: dict,
    classification_verdict: dict,
) -> dict[str, Any]:
    """Validate and canonicalise the classification verdict.

    Inputs
    ------
    support_request_record
        The closed envelope produced by
        :func:`...primitives.ingest.ingest_support_request`. Carried
        through for replay traceability — the verdict's ``category``
        must agree with the record's ``request_kind`` because the
        canonical CACAO playbook pins those alphabets as identical.
    classification_verdict
        Operator-supplied verdict envelope: ``{category, severity,
        rule_ids, policy_version}``. The compile target's runtime is
        the source of truth for the verdict; this primitive only
        re-validates the shape.

    Returns
    -------
    JSON-native dict with the closed verdict envelope.
    """
    if not isinstance(support_request_record, dict):
        raise InvalidClassificationError(
            "support_request_record must be an object, got "
            f"{type(support_request_record).__name__}"
        )
    if not isinstance(classification_verdict, dict):
        raise InvalidClassificationError(
            "classification_verdict must be an object, got "
            f"{type(classification_verdict).__name__}"
        )

    request_kind = support_request_record.get("request_kind")
    if request_kind not in _ALLOWED_REQUEST_KINDS:
        raise InvalidClassificationError(
            f"support_request_record.request_kind {request_kind!r} is not "
            f"one of {sorted(_ALLOWED_REQUEST_KINDS)!r}; the upstream "
            "ingest primitive should have rejected this"
        )

    category = _canonical_text(
        classification_verdict.get("category"),
        "classification_verdict.category",
    )
    if category not in _ALLOWED_CATEGORIES:
        raise InvalidClassificationError(
            f"classification_verdict.category {category!r} is not one of "
            f"{sorted(_ALLOWED_CATEGORIES)!r}"
        )
    if category != request_kind:
        raise InvalidClassificationError(
            f"classification_verdict.category {category!r} does not match "
            f"support_request_record.request_kind {request_kind!r}; the "
            "two alphabets are pinned identical by the canonical playbook"
        )

    severity = _canonical_text(
        classification_verdict.get("severity"),
        "classification_verdict.severity",
    )
    if severity not in _ALLOWED_SEVERITIES:
        raise InvalidClassificationError(
            f"classification_verdict.severity {severity!r} is not one of "
            f"{sorted(_ALLOWED_SEVERITIES)!r}"
        )

    rule_ids_raw = classification_verdict.get("rule_ids")
    if not isinstance(rule_ids_raw, list) or not rule_ids_raw:
        raise InvalidClassificationError(
            "classification_verdict.rule_ids must be a non-empty list"
        )
    seen: set[str] = set()
    rule_ids: list[str] = []
    for index, raw in enumerate(rule_ids_raw):
        if not isinstance(raw, str):
            raise InvalidClassificationError(
                f"classification_verdict.rule_ids[{index}] must be a string, "
                f"got {type(raw).__name__}"
            )
        token = unicodedata.normalize("NFKC", raw).strip()
        if not token:
            raise InvalidClassificationError(
                f"classification_verdict.rule_ids[{index}] is empty after "
                "canonicalisation"
            )
        if len(token) > 200:
            raise InvalidClassificationError(
                f"classification_verdict.rule_ids[{index}] must be "
                "<= 200 chars"
            )
        if not _RULE_ID_RE.match(token):
            raise InvalidClassificationError(
                f"classification_verdict.rule_ids[{index}] {raw!r} does "
                "not match the <family>.<slug> shape pinned by the schema"
            )
        if token in seen:
            raise InvalidClassificationError(
                f"classification_verdict.rule_ids has duplicate entry "
                f"{token!r}"
            )
        seen.add(token)
        rule_ids.append(token)

    policy_version = _canonical_text(
        classification_verdict.get("policy_version"),
        "classification_verdict.policy_version",
    )
    if not _POLICY_VERSION_RE.match(policy_version):
        raise InvalidClassificationError(
            f"classification_verdict.policy_version {policy_version!r} does "
            "not match the policy-version opaque-token shape"
        )

    return {
        "category": category,
        "severity": severity,
        "rule_ids": rule_ids,
        "policy_version": policy_version,
    }
