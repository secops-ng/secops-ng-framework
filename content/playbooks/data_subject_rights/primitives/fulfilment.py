"""Fulfilment-evidence compilation primitive (compile_fulfilment_evidence step).

Assembles the per-request fulfilment pack from the data-owner
acknowledgement envelopes returned against the routing manifest. The
pack can only close complete: every expected owner acknowledged, no
stranger acknowledgements, every item pointing at evidence on the
owner's store.

Design constraints
------------------

* **Pure / replayable.** Owner transports and timeouts are the compile
  target's concern; this primitive judges the returned set against the
  manifest and derives the pack identity.
* **Completeness fails loud, qualifications are data (pinned by
  tests).** A missing owner return means the pack cannot close — an
  incomplete pack that looks complete is exactly the accountability
  gap Article 5(2) reviewers probe. A *qualification* on a return
  (an Article 17(3) retention exemption on an erasure, an overriding-
  legitimate-interest determination on an objection) is a lawful
  partial outcome: carried as data, surfaced on the pack, never an
  error.
* **Stranger returns fail loud.** An acknowledgement from an owner the
  manifest never routed to is evidence attached to the wrong case —
  silently absorbing it would corrupt the audit trail.
* **Content-derived identity.** ``__fulfilment_pack_ref__`` is
  ``dsr-pack-`` + 24 hex over the manifest id and the canonicalised
  returns, so re-compiling the same returns resolves to the same pack.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

__all__ = [
    "IncompleteFulfilmentError",
    "InvalidOwnerReturnError",
    "compile_fulfilment_pack",
]


_POINTER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")


class InvalidOwnerReturnError(ValueError):
    """Raised when a return cannot join the pack."""


class IncompleteFulfilmentError(ValueError):
    """Raised when expected owner returns are missing."""


def _canonical_pointer(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidOwnerReturnError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidOwnerReturnError(
            f"{field} is empty after canonicalisation"
        )
    if not _POINTER_RE.match(normalised):
        raise InvalidOwnerReturnError(
            f"{field} {normalised!r} does not match the role-shaped "
            "pointer pattern; free text is out of scope per AGENTS.md §3"
        )
    return normalised


def compile_fulfilment_pack(manifest: dict, owner_returns: list) -> dict:
    """Compile the fulfilment evidence pack for one routed case.

    Inputs
    ------
    manifest
        The routing step's manifest
        (:func:`.routing.resolve_data_owner_manifest` output).
    owner_returns
        List of owner acknowledgement envelopes, each an object with
        ``ack_id`` (the manifest's expected ack id), ``evidence_ref``
        (role-shaped pointer to the evidence on the owner's store) and
        optionally ``qualification`` (non-empty text documenting a
        lawful partial outcome — an Article 17(3) retention exemption,
        an overriding-legitimate-interest determination). A duplicate
        return for one ack id fails loud.

    Returns
    -------
    JSON-native fulfilment pack::

        {
            "fulfilment_pack_ref": "dsr-pack-<24 hex>",
            "case_id": "...",
            "request_type": "...",
            "evidence_ask": "...",
            "items": [
                {"owner_ref": "...", "store_ref": "...",
                 "ack_id": "...", "evidence_ref": "...",
                 "qualification": "..." | None},
                ...  # manifest order
            ],
            "qualified_items": <int>
        }
    """
    if not isinstance(manifest, dict):
        raise InvalidOwnerReturnError(
            f"manifest must be an object, got {type(manifest).__name__}"
        )
    expected = manifest.get("expected")
    if not isinstance(expected, list) or not expected:
        raise InvalidOwnerReturnError(
            "manifest.expected must be a non-empty list"
        )
    if not isinstance(owner_returns, list):
        raise InvalidOwnerReturnError(
            f"owner_returns must be a list, got "
            f"{type(owner_returns).__name__}"
        )

    returns_by_ack: dict[str, dict] = {}
    for index, ret in enumerate(owner_returns):
        field = f"owner_returns[{index}]"
        if not isinstance(ret, dict):
            raise InvalidOwnerReturnError(
                f"{field} must be an object, got {type(ret).__name__}"
            )
        ack_id = _canonical_pointer(ret.get("ack_id"), f"{field}.ack_id")
        if ack_id in returns_by_ack:
            raise InvalidOwnerReturnError(
                f"{field} repeats ack_id {ack_id!r}; two returns for one "
                "acknowledgement must not be silently resolved"
            )
        evidence = _canonical_pointer(
            ret.get("evidence_ref"), f"{field}.evidence_ref"
        )
        qualification = None
        raw_qualification = ret.get("qualification")
        if raw_qualification is not None:
            if not isinstance(raw_qualification, str):
                raise InvalidOwnerReturnError(
                    f"{field}.qualification must be a string, got "
                    f"{type(raw_qualification).__name__}"
                )
            qualification = unicodedata.normalize(
                "NFKC", raw_qualification
            ).strip()
            if not qualification:
                raise InvalidOwnerReturnError(
                    f"{field}.qualification is empty after "
                    "canonicalisation; an empty qualification is not a "
                    "documented outcome"
                )
        returns_by_ack[ack_id] = {
            "evidence_ref": evidence,
            "qualification": qualification,
        }

    expected_ack_ids = {row["ack_id"] for row in expected}
    strangers = set(returns_by_ack) - expected_ack_ids
    if strangers:
        raise InvalidOwnerReturnError(
            f"owner_returns carries ack ids the manifest never routed: "
            f"{sorted(strangers)}; evidence attached to the wrong case "
            "must not be silently absorbed"
        )
    missing = expected_ack_ids - set(returns_by_ack)
    if missing:
        raise IncompleteFulfilmentError(
            "fulfilment pack cannot close; missing owner returns for: "
            + ", ".join(sorted(missing))
        )

    items = []
    for row in expected:
        ret = returns_by_ack[row["ack_id"]]
        items.append(
            {
                "owner_ref": row["owner_ref"],
                "store_ref": row["store_ref"],
                "ack_id": row["ack_id"],
                "evidence_ref": ret["evidence_ref"],
                "qualification": ret["qualification"],
            }
        )

    digest = hashlib.sha256(
        (
            str(manifest.get("manifest_id"))
            + "|"
            + json.dumps(items, sort_keys=True)
        ).encode("utf-8")
    ).hexdigest()

    return {
        "fulfilment_pack_ref": "dsr-pack-" + digest[:24],
        "case_id": manifest.get("case_id"),
        "request_type": manifest.get("request_type"),
        "evidence_ask": manifest.get("evidence_ask"),
        "items": items,
        "qualified_items": sum(
            1 for item in items if item["qualification"] is not None
        ),
    }
