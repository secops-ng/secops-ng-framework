"""Contract ingestion primitive (ingest-contract).

Canonicalises an operator-supplied raw supplier-contract record into
the closed ``contract`` block the F-WF-10 schema pins
(``contract_id``, ``supplier_ref``, ``effective_at``, optional
``expires_at`` / ``jurisdiction``). The compile target's runtime
fetches the record from the operator's supplier-contract store
upstream — this primitive only normalises and re-validates so a
free-text or personal-name contract field fails loud at the step
boundary rather than at the artifact-emit boundary downstream.

Design constraints
------------------

* **Pure / replayable.** No network, no clock, no LLMs.
* **Deterministic.** Same canonical input ⇒ same canonical output;
  the downstream artifact builder hashes the artifact key off the
  contract id so any reshape here is observable in the artifact id.
* **Public-bar safe.** Contract id and supplier id MUST stay
  role-shaped / namespaced; free-text labels and personal names are
  out of scope per AGENTS.md §3 and rejected here as a matter of
  schema discipline.
* **Sovereign-stack neutral.** No vendor SDK is imported; the
  ``raw_contract`` argument is an operator-side JSON-native object.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

__all__ = [
    "InvalidContractRecordError",
    "ingest_contract",
]


_CONTRACT_ID_RE = re.compile(
    r"^contract\.[a-z0-9][a-z0-9._-]*@v[0-9]+(\.[0-9]+){0,2}$"
)
_SUPPLIER_REF_RE = re.compile(
    r"^provider\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_ISO_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_JURISDICTION_RE = re.compile(r"^[A-Z]{2}$")


class InvalidContractRecordError(ValueError):
    """Raised when the inputs cannot produce a valid contract block."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidContractRecordError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidContractRecordError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def ingest_contract(
    raw_contract: dict,
    contract_ref: str,
) -> dict[str, Any]:
    """Build the canonical ``contract`` block.

    Inputs
    ------
    raw_contract
        Operator-supplied JSON-native object carrying the keys the
        F-WF-10 schema pins: required ``contract_id``,
        ``supplier_ref``, ``effective_at``; optional ``expires_at``
        and ``jurisdiction``.
    contract_ref
        Opaque operator-side pointer to the supplier-contract record
        the compile target's runtime resolved against (audit trail).
        The framework does not interpret it; it is checked only for
        non-empty shape.

    Returns
    -------
    JSON-native dict matching the ``contract`` block of
    ``schemas/evidence/contractual-obligations.schema.json``.
    """
    _ = _canonical_text(contract_ref, "contract_ref")

    if not isinstance(raw_contract, dict):
        raise InvalidContractRecordError(
            f"raw_contract must be an object, got {type(raw_contract).__name__}"
        )

    cid = _canonical_text(raw_contract.get("contract_id"), "contract.contract_id")
    if not _CONTRACT_ID_RE.match(cid) or len(cid) > 200:
        raise InvalidContractRecordError(
            f"contract.contract_id {cid!r} does not match the role-shaped "
            "contract.<id>@v<n> pattern pinned by the schema; opaque "
            "operator-side ids only — personal names and free-text labels "
            "are out of scope per AGENTS.md \u00a73"
        )

    sref = _canonical_text(
        raw_contract.get("supplier_ref"), "contract.supplier_ref"
    )
    if not _SUPPLIER_REF_RE.match(sref) or len(sref) > 200:
        raise InvalidContractRecordError(
            f"contract.supplier_ref {sref!r} does not match the "
            "role-shaped provider.<id>@v<n> pattern pinned by the schema"
        )

    eff = _canonical_text(
        raw_contract.get("effective_at"), "contract.effective_at"
    )
    if not _ISO_DATE_RE.match(eff):
        raise InvalidContractRecordError(
            f"contract.effective_at {eff!r} is not an ISO-8601 date "
            "(YYYY-MM-DD)"
        )

    out: dict[str, Any] = {
        "contract_id": cid,
        "supplier_ref": sref,
        "effective_at": eff,
    }

    expires = raw_contract.get("expires_at")
    if expires is not None:
        exp_text = _canonical_text(expires, "contract.expires_at")
        if not _ISO_DATE_RE.match(exp_text):
            raise InvalidContractRecordError(
                f"contract.expires_at {exp_text!r} is not an ISO-8601 date"
            )
        out["expires_at"] = exp_text

    jurisdiction = raw_contract.get("jurisdiction")
    if jurisdiction is not None:
        j_text = _canonical_text(jurisdiction, "contract.jurisdiction")
        if not _JURISDICTION_RE.match(j_text):
            raise InvalidContractRecordError(
                f"contract.jurisdiction {j_text!r} is not an ISO-3166 "
                "alpha-2 code"
            )
        out["jurisdiction"] = j_text

    return out
