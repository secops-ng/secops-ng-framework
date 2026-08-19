"""CVD case-intake primitive (intake).

Canonicalises an operator-supplied raw vulnerability report received
through the operator's CVD intake surface (RFC 9116 security.txt
address, disclosure mailbox, bug-bounty portal) into the closed case
envelope the triage step consumes, and derives the ``__case_id__``
deterministically from the report content — the same report
re-received through the same channel resolves to the same case, so
intake dedup is a property of the derivation, not of mailbox state.

Design constraints
------------------

* **Pure / replayable.** No network, no clock reads, no LLMs. The
  intake surface adapter (address resolution, PGP decryption, portal
  webhook) is the compile target's ingress concern upstream; this
  primitive only validates and shapes what it hands over.
* **Determinism.** ``case_id`` is ``cvd-`` + the first 24 hex chars of
  SHA-256 over the intake channel and the canonicalised report JSON
  (sorted keys), so two replays of the same report collapse to one
  case and two distinct reports cannot collide in practice.
* **Public-bar safe.** ``reporter_contact`` is treated as an opaque
  handle at this boundary (mirroring ``reporter.send_acknowledgement``)
  — the primitive does not inspect it for personal-name shapes; that
  is the ingress adapter's responsibility. Free-text product handles
  are rejected: the product must be a role-shaped identifier matching
  the operator's inventory convention.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata

__all__ = [
    "InvalidCvdReportError",
    "open_cvd_case",
]


_CHANNELS = frozenset({"security_txt", "disclosure_mailbox", "bug_bounty_portal"})
_PRODUCT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class InvalidCvdReportError(ValueError):
    """Raised when the raw report cannot produce a valid case envelope."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidCvdReportError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidCvdReportError(f"{field} is empty after canonicalisation")
    return normalised


def open_cvd_case(raw_report: dict, intake_channel: str) -> dict:
    """Open one CVD case from one raw vulnerability report.

    Inputs
    ------
    raw_report
        Operator-supplied JSON-native report record. Required keys:
        ``reporter_contact`` (opaque handle), ``product`` (role-shaped
        identifier from the operator's inventory), ``affected_versions``
        (non-empty list of version strings), ``reproduction`` (the
        reporter's reproduction narrative — carried opaquely, only
        required non-empty). Optional: ``proposed_embargo``
        (ISO-8601 date the reporter proposes).
    intake_channel
        Which CVD intake surface received the report: one of
        ``security_txt``, ``disclosure_mailbox``, ``bug_bounty_portal``.

    Returns
    -------
    JSON-native case envelope::

        {
            "case_id": "cvd-<24 hex>",
            "intake_channel": "...",
            "reporter_contact": "...",
            "product": "...",
            "affected_versions": [...],
            "reproduction": "...",
            "proposed_embargo": "YYYY-MM-DD" | None
        }
    """
    channel = _canonical_text(intake_channel, "intake_channel")
    if channel not in _CHANNELS:
        raise InvalidCvdReportError(
            f"intake_channel {intake_channel!r} is not one of "
            f"{sorted(_CHANNELS)}"
        )
    if not isinstance(raw_report, dict):
        raise InvalidCvdReportError(
            f"raw_report must be an object, got {type(raw_report).__name__}"
        )

    contact = _canonical_text(
        raw_report.get("reporter_contact"), "raw_report.reporter_contact"
    )
    product = _canonical_text(raw_report.get("product"), "raw_report.product")
    if not _PRODUCT_RE.match(product):
        raise InvalidCvdReportError(
            f"raw_report.product {product!r} does not match the role-shaped "
            "inventory-identifier pattern; free text is out of scope per "
            "AGENTS.md §3"
        )

    versions_raw = raw_report.get("affected_versions")
    if not isinstance(versions_raw, list) or not versions_raw:
        raise InvalidCvdReportError(
            "raw_report.affected_versions must be a non-empty list"
        )
    versions: list[str] = []
    for index, v in enumerate(versions_raw):
        versions.append(
            _canonical_text(v, f"raw_report.affected_versions[{index}]")
        )

    reproduction = _canonical_text(
        raw_report.get("reproduction"), "raw_report.reproduction"
    )

    envelope: dict = {
        "intake_channel": channel,
        "reporter_contact": contact,
        "product": product,
        "affected_versions": versions,
        "reproduction": reproduction,
        "proposed_embargo": None,
    }
    embargo = raw_report.get("proposed_embargo")
    if embargo is not None:
        embargo_text = _canonical_text(embargo, "raw_report.proposed_embargo")
        if not _ISO_DATE_RE.match(embargo_text):
            raise InvalidCvdReportError(
                f"raw_report.proposed_embargo {embargo_text!r} is not an "
                "ISO-8601 date (YYYY-MM-DD)"
            )
        envelope["proposed_embargo"] = embargo_text

    digest = hashlib.sha256(
        (channel + "|" + json.dumps(envelope, sort_keys=True)).encode("utf-8")
    ).hexdigest()
    case_id = "cvd-" + digest[:24]

    return {"case_id": case_id, **envelope}
