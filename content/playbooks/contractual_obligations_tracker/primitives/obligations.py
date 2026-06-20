"""Obligation extractor primitive (extract-obligations).

Canonicalises the operator-supplied raw obligation list against the
ingested contract record into the closed ``obligations[]`` array shape
the F-WF-10 schema pins — one entry per declared obligation with the
clause reference, obligation text, obligation kind enum, and optional
contractual cadence. Sorted by ``obligation_id`` so two replays of
the same inputs collapse to byte-identical bytes.

Design constraints
------------------

* **Pure / replayable.** No network, no clock, no LLMs. Operator
  contracts and obligations are the only inputs.
* **Deterministic.** Output is sorted by ``obligation_id`` and
  duplicate ids fail loud (the framework does not silently collapse
  obligations — operators choose how to dedupe upstream).
* **Public-bar safe.** Obligation text MUST stay role-shaped per
  AGENTS.md §3 — no personal names, no operator branding. The
  schema's ``maxLength`` is enforced here so a misshaped contract
  field fails at the step boundary.
* **Sovereign-stack neutral.** Inputs are JSON-native; no vendor SDK.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

__all__ = [
    "InvalidObligationSetError",
    "extract_obligations",
]


_OBLIGATION_ID_RE = re.compile(r"^obligation\.[a-z][a-z0-9_-]*$")
_OBLIGATION_KINDS = frozenset(
    {
        "security_control_commitment",
        "audit_right",
        "attestation_cadence",
        "sub_processor_disclosure",
        "breach_notification_cadence",
        "data_localisation",
        "other",
    }
)
_ISO_DURATION_RE = re.compile(
    r"^P([0-9]+Y)?([0-9]+M)?([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+S)?)?$"
)


class InvalidObligationSetError(ValueError):
    """Raised when the inputs cannot produce a valid obligation set."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidObligationSetError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidObligationSetError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _canonical_obligation(entry: object, position: int) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise InvalidObligationSetError(
            f"raw_obligations[{position}] must be an object, got "
            f"{type(entry).__name__}"
        )

    oid = _canonical_text(
        entry.get("obligation_id"), f"raw_obligations[{position}].obligation_id"
    )
    if not _OBLIGATION_ID_RE.match(oid) or len(oid) > 200:
        raise InvalidObligationSetError(
            f"raw_obligations[{position}].obligation_id {oid!r} does not "
            "match the role-shaped obligation.<id> pattern pinned by the "
            "schema"
        )

    clause = _canonical_text(
        entry.get("clause_ref"), f"raw_obligations[{position}].clause_ref"
    )
    if len(clause) > 200:
        raise InvalidObligationSetError(
            f"raw_obligations[{position}].clause_ref must be <= 200 chars "
            "per the schema"
        )

    kind = _canonical_text(
        entry.get("obligation_kind"),
        f"raw_obligations[{position}].obligation_kind",
    )
    if kind not in _OBLIGATION_KINDS:
        raise InvalidObligationSetError(
            f"raw_obligations[{position}].obligation_kind {kind!r} is not "
            f"one of {sorted(_OBLIGATION_KINDS)}"
        )

    text = _canonical_text(
        entry.get("text"), f"raw_obligations[{position}].text"
    )
    if len(text) > 2000:
        raise InvalidObligationSetError(
            f"raw_obligations[{position}].text must be <= 2000 chars per "
            "the schema"
        )

    out: dict[str, Any] = {
        "obligation_id": oid,
        "clause_ref": clause,
        "obligation_kind": kind,
        "text": text,
    }

    cadence = entry.get("cadence")
    if cadence is not None:
        c_text = _canonical_text(cadence, f"raw_obligations[{position}].cadence")
        if not _ISO_DURATION_RE.match(c_text):
            raise InvalidObligationSetError(
                f"raw_obligations[{position}].cadence {c_text!r} is not an "
                "ISO-8601 duration"
            )
        out["cadence"] = c_text

    return out


def extract_obligations(
    raw_obligations: list,
    contract: dict,
) -> list[dict[str, Any]]:
    """Build the canonical ``obligations[]`` array.

    Inputs
    ------
    raw_obligations
        Operator-supplied list of obligation records the contract
        extraction step produced. One entry per declared obligation
        with at minimum the four required keys
        (``obligation_id``, ``clause_ref``, ``obligation_kind``,
        ``text``); ``cadence`` is optional.
    contract
        Output of :func:`...primitives.ingest.ingest_contract`. The
        contract record itself is not re-validated here (the upstream
        primitive owns that); the link is held so a future extension
        can join obligation extraction to per-jurisdiction policy
        without changing this function's signature.

    Returns
    -------
    JSON-native list of obligation entries matching the
    ``obligations[]`` shape of
    ``schemas/evidence/contractual-obligations.schema.json``,
    sorted by ``obligation_id`` for byte-stable replay.
    """
    if not isinstance(contract, dict):
        raise InvalidObligationSetError(
            f"contract must be an object, got {type(contract).__name__}"
        )

    if not isinstance(raw_obligations, list):
        raise InvalidObligationSetError(
            f"raw_obligations must be a list, got "
            f"{type(raw_obligations).__name__}"
        )
    if not raw_obligations:
        raise InvalidObligationSetError(
            "raw_obligations must carry at least one entry; an artifact "
            "for a contract with zero extracted obligations is not the "
            "F-WF-10 artifact"
        )

    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for index, entry in enumerate(raw_obligations):
        item = _canonical_obligation(entry, index)
        oid = item["obligation_id"]
        if oid in seen:
            raise InvalidObligationSetError(
                f"raw_obligations carries duplicate obligation_id {oid!r}; "
                "operators dedupe upstream — the framework does not "
                "silently collapse obligations"
            )
        seen.add(oid)
        out.append(item)

    out.sort(key=lambda item: item["obligation_id"])
    return out
