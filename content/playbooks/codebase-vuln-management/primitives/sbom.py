"""SBOM ingest + dependency-finding normalisation primitives.

These are the deterministic helpers behind the ``ingest-sbom`` and
``review-deps`` CACAO action steps of the codebase-vulnerability-management
playbook (F-WF-07).

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
  The per-target adapters (n8n Code node, Temporal activity, LangGraph
  node) all wrap these helpers; the helpers themselves are
  ``compilers._shared.evidence``-style — JSON-native input, JSON-native
  output, byte-deterministic for a given input.
* **Sovereign-stack neutral.** No vendor scanner SDKs are imported.
  The scanner CLI is the operator's choice (the playbook README points
  at EU-hostable defaults); these primitives only consume its
  serialised output and the SBOM artefact bytes.
* **Public-bar safe.** No example payloads embed real advisory text,
  vendor names, or contact information; the per-finding shape only
  carries identifiers (advisory id, PURL, version, severity) and the
  ``source_data`` pointer convention used by the rest of the
  evidence streams.
"""

from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass

__all__ = [
    "NormalisedFinding",
    "SBOMContentHashError",
    "normalise_findings",
    "pin_sbom_content_hash",
]


_ALLOWED_SBOM_FORMATS = frozenset(
    {"cyclonedx_json", "cyclonedx_xml", "spdx_json", "spdx_tag_value"}
)

# Severity vocabulary the downstream disclosure-window primitive
# consumes. Mirrors the CVSS qualitative bands plus an explicit
# ``unknown`` sink for findings the scanner could not score so we
# never silently coerce missing data to ``low``.
_ALLOWED_SEVERITIES = ("critical", "high", "medium", "low", "info", "unknown")


class SBOMContentHashError(ValueError):
    """Raised when SBOM artefact bytes cannot be pinned deterministically."""


@dataclass(frozen=True)
class NormalisedFinding:
    """One canonical (component, advisory) finding row.

    Frozen + slots-shaped via dataclass so the per-target adapter
    serialises a list of these to JSON with stable key order. The
    fields are the minimum the disclosure-timeline emitter needs;
    callers that carry richer scanner output for their own UI keep
    it in ``source_data`` (an opaque JSON sub-object).
    """

    advisory_id: str
    purl: str
    version: str
    severity: str
    source_data: dict


def pin_sbom_content_hash(sbom_bytes: bytes, sbom_format: str) -> str:
    """Return the SHA-256 lower-hex digest of an SBOM artefact.

    ``sbom_format`` is validated against the allowed-list documented on
    the playbook's ``__sbom_format__`` variable so a typo at the
    upstream build-chain boundary fails loud here rather than silently
    pinning the wrong bytes downstream.

    Raises
    ------
    SBOMContentHashError
        If ``sbom_bytes`` is empty, ``sbom_format`` is missing or not
        one of the allowed formats.
    """
    if not isinstance(sbom_bytes, (bytes, bytearray)):
        raise SBOMContentHashError(
            f"sbom_bytes must be bytes, got {type(sbom_bytes).__name__}"
        )
    if not sbom_bytes:
        raise SBOMContentHashError("sbom_bytes is empty")
    if not isinstance(sbom_format, str):
        raise SBOMContentHashError(
            f"sbom_format must be a string, got {type(sbom_format).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", sbom_format).strip().lower()
    if normalised not in _ALLOWED_SBOM_FORMATS:
        raise SBOMContentHashError(
            f"sbom_format {sbom_format!r} is not one of "
            f"{sorted(_ALLOWED_SBOM_FORMATS)!r}"
        )
    return hashlib.sha256(bytes(sbom_bytes)).hexdigest()


def _canonical_severity(value: str) -> str:
    """Lower-case + NFKC-normalise a severity band; reject unknown values."""
    if not isinstance(value, str):
        raise ValueError(
            f"severity must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip().lower()
    if normalised not in _ALLOWED_SEVERITIES:
        raise ValueError(
            f"severity {value!r} is not one of {_ALLOWED_SEVERITIES!r}"
        )
    return normalised


def _canonical_text_field(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise ValueError(f"{field} is empty after canonicalisation")
    return normalised


def normalise_findings(
    raw_findings: list[dict], sbom_content_hash: str
) -> list[dict]:
    """Canonicalise a scanner's per-finding output to the playbook contract.

    The input ``raw_findings`` is whatever JSON the operator's chosen
    scanner CLI emits (one entry per matched ``(component, version,
    advisory)`` triple). Each entry MUST carry the four keys
    ``advisory_id``, ``purl``, ``version``, ``severity``; an optional
    ``source_data`` sub-object is passed through verbatim for downstream
    audit. Unknown keys on the input are ignored — operators free to
    enrich for their own UI without breaking the contract.

    Returns a sorted list of plain dicts (JSON-native; the n8n Code
    node and the Temporal activity both serialise this without
    further marshalling). Sort key is
    ``(advisory_id, purl, version)`` so two replays of the same scan
    against the same SBOM-pinned content hash collapse to byte-
    identical bytes.

    ``sbom_content_hash`` is checked for shape (64-char lower-hex) so a
    caller that forgot to plumb the ingest-sbom output through fails
    here rather than downstream.

    Raises
    ------
    ValueError
        On missing keys, empty fields, unknown severity bands, or a
        malformed SBOM content hash.
    """
    if not isinstance(raw_findings, list):
        raise ValueError(
            f"raw_findings must be a list, got {type(raw_findings).__name__}"
        )
    if not isinstance(sbom_content_hash, str) or len(sbom_content_hash) != 64:
        raise ValueError(
            "sbom_content_hash must be a 64-char SHA-256 lower-hex string"
        )
    try:
        int(sbom_content_hash, 16)
    except ValueError as exc:
        raise ValueError(
            "sbom_content_hash is not valid hex"
        ) from exc

    normalised: list[dict] = []
    for index, entry in enumerate(raw_findings):
        if not isinstance(entry, dict):
            raise ValueError(
                f"raw_findings[{index}] must be a dict, got "
                f"{type(entry).__name__}"
            )
        finding = NormalisedFinding(
            advisory_id=_canonical_text_field(
                entry.get("advisory_id", ""), f"raw_findings[{index}].advisory_id"
            ),
            purl=_canonical_text_field(
                entry.get("purl", ""), f"raw_findings[{index}].purl"
            ),
            version=_canonical_text_field(
                entry.get("version", ""), f"raw_findings[{index}].version"
            ),
            severity=_canonical_severity(entry.get("severity", "")),
            source_data=dict(entry.get("source_data") or {}),
        )
        normalised.append(
            {
                "advisory_id": finding.advisory_id,
                "purl": finding.purl,
                "version": finding.version,
                "severity": finding.severity,
                "source_data": finding.source_data,
                "sbom_content_hash": sbom_content_hash,
            }
        )

    normalised.sort(
        key=lambda f: (f["advisory_id"], f["purl"], f["version"])
    )
    return normalised
