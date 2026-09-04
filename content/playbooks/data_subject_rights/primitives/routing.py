"""Data-owner routing primitive (route_to_data_owners step).

Turns the resolved owner set — the data-store owners whose stores hold
personal data on the subject, resolved by the adapter against the
controller's declared data-inventory surface — into the deterministic
manifest of per-owner acknowledgement envelopes the fulfilment step
waits on, each carrying the request-type-appropriate evidence ask.

Design constraints
------------------

* **Pure / replayable.** Which stores hold the subject's data is a
  runtime join against the controller's own records (sovereign-stack
  constraint); the adapter resolves it and hands the rows over. What
  is deterministic here is the ask vocabulary and the manifest
  identity.
* **The evidence ask is contractual per request type (pinned by
  tests).** access ⇒ the assembled subject copy; rectification ⇒ the
  applied correction; erasure ⇒ the deletion record or the documented
  Article 17(3) retention exemption; restriction ⇒ the applied
  restriction marker; portability ⇒ the structured data package;
  objection ⇒ the cessation record or the overriding-legitimate-
  interest note; automated_decision_review ⇒ the human-review referral
  record (the lifecycle hands off, so the owner-side evidence is the
  record that the referral reached the review surface).
* **Duplicate rows collapse; an empty owner set fails loud.** The
  same (owner, store) pair observed twice is one expected envelope;
  a request that resolves to zero owners cannot proceed to
  fulfilment — a controller holding no personal data on the subject
  answers through the response step, not through an empty manifest.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

__all__ = [
    "InvalidRoutingInputError",
    "resolve_data_owner_manifest",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")

_EVIDENCE_ASKS = {
    "access": "assembled_subject_copy",
    "rectification": "applied_correction",
    "erasure": "deletion_or_retention_exemption_record",
    "restriction": "applied_restriction_marker",
    "portability": "structured_data_package",
    "objection": "cessation_or_overriding_interest_note",
    "automated_decision_review": "human_review_referral_record",
}


class InvalidRoutingInputError(ValueError):
    """Raised when the owner rows cannot produce a valid manifest."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidRoutingInputError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidRoutingInputError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidRoutingInputError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def resolve_data_owner_manifest(
    case_id: str, request_type: str, owner_rows: list
) -> dict:
    """Build the per-owner acknowledgement manifest for one case.

    Inputs
    ------
    case_id
        The intake case id (``__case_id__``).
    request_type
        The classified type (closed Chapter III taxonomy).
    owner_rows
        Non-empty list of resolved inventory rows, each an object with
        role-shaped ``owner_ref`` and ``store_ref``. Duplicate
        (owner, store) pairs collapse to the first occurrence.

    Returns
    -------
    JSON-native owner manifest::

        {
            "manifest_id": "dsr-own-<24 hex>",
            "case_id": "...",
            "request_type": "...",
            "evidence_ask": "...",
            "expected": [
                {"owner_ref": "...", "store_ref": "...",
                 "ack_id": "dsr-ack-<24 hex>"},
                ...  # first-observation order
            ]
        }
    """
    case = _canonical_pointer(case_id, "case_id")
    if not isinstance(request_type, str) or request_type not in _EVIDENCE_ASKS:
        raise InvalidRoutingInputError(
            f"request_type {request_type!r} is not in the closed "
            f"taxonomy {sorted(_EVIDENCE_ASKS)}"
        )
    ask = _EVIDENCE_ASKS[request_type]

    if not isinstance(owner_rows, list) or not owner_rows:
        raise InvalidRoutingInputError(
            "owner_rows must be a non-empty list — a request resolving "
            "to zero owners answers through the response step, not "
            "through an empty manifest"
        )

    expected: list[dict] = []
    seen: set[tuple] = set()
    for index, row in enumerate(owner_rows):
        field = f"owner_rows[{index}]"
        if not isinstance(row, dict):
            raise InvalidRoutingInputError(
                f"{field} must be an object, got {type(row).__name__}"
            )
        owner = _canonical_pointer(row.get("owner_ref"), f"{field}.owner_ref")
        store = _canonical_pointer(row.get("store_ref"), f"{field}.store_ref")
        pair = (owner, store)
        if pair in seen:
            continue
        seen.add(pair)
        ack_digest = hashlib.sha256(
            (case + "|" + owner + "|" + store + "|" + ask).encode("utf-8")
        ).hexdigest()
        expected.append(
            {
                "owner_ref": owner,
                "store_ref": store,
                "ack_id": "dsr-ack-" + ack_digest[:24],
            }
        )

    manifest_digest = hashlib.sha256(
        (
            case
            + "|"
            + request_type
            + "|"
            + json.dumps(expected, sort_keys=True)
        ).encode("utf-8")
    ).hexdigest()

    return {
        "manifest_id": "dsr-own-" + manifest_digest[:24],
        "case_id": case,
        "request_type": request_type,
        "evidence_ask": ask,
        "expected": expected,
    }
