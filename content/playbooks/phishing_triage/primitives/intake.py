"""Reported-message intake for the phishing_triage playbook.

Backs the ``ingest report`` step. The fetch from the email-security
platform is the compile target's adapter concern; what is deterministic is
the grammar the fetched envelope must satisfy and its canonical form, so
that every later step — the fingerprint, the verdict join, the response
directives — reads one normalised shape.

This module is also where the message grammar lives for the rest of the
package: :mod:`.enrichment` imports :func:`canonical_url` and the verdict
keys it joins on are produced here, so the two steps cannot disagree about
what one URL or one attachment is.

Canonicalisation, in brief:

* strings are NFKC-normalised and stripped;
* an address keeps its local part verbatim (local parts are
  case-sensitive by RFC 5321) and lowercases its domain;
* a URL must be ``http`` or ``https`` with a host — the things a gateway
  can block; scheme and host are lowercased, the fragment is dropped (it
  never reaches the server), path and query are kept byte-for-byte;
* recipients, URLs and attachments are de-duplicated and sorted, so the
  envelope is independent of the order the platform listed them in.

Unknown envelope keys are rejected rather than ignored: a misspelled
``attachements`` silently read as "no attachments" would hide exactly the
evidence the malware branch acts on.
"""

from __future__ import annotations

import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit

__all__ = [
    "InvalidReportedMessageError",
    "REPORT_SOURCES",
    "canonical_address",
    "canonical_url",
    "validate_reported_message",
]

REPORT_SOURCES: tuple[str, ...] = ("user_report", "mailbox_sweep")

_ZULU = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ADDRESS = re.compile(r"^[^@\s]+@[^@\s.][^@\s]*\.[^@\s.]+$")
_REQUIRED = ("message_id", "sender", "recipients", "subject", "received_at")
_OPTIONAL = ("urls", "attachments")


class InvalidReportedMessageError(ValueError):
    """The fetched envelope does not satisfy the intake grammar."""


def _nfkc(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidReportedMessageError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    return unicodedata.normalize("NFKC", value).strip()


def _token(value: object, field: str) -> str:
    text = _nfkc(value, field)
    if not text or any(ch.isspace() for ch in text):
        raise InvalidReportedMessageError(
            f"{field} must be a non-empty string without whitespace, got {value!r}"
        )
    return text


def _zulu(value: object, field: str) -> str:
    text = _nfkc(value, field)
    if not _ZULU.match(text):
        raise InvalidReportedMessageError(
            f"{field} must be a Zulu instant YYYY-MM-DDTHH:MM:SSZ, got {value!r}"
        )
    return text


def canonical_address(value: object, field: str = "address") -> str:
    """Canonical form of one email address: local part verbatim, domain lowercased."""
    text = _token(value, field)
    if not _ADDRESS.match(text):
        raise InvalidReportedMessageError(f"{field} is not an email address: {value!r}")
    local, _, domain = text.rpartition("@")
    return f"{local}@{domain.lower()}"


def canonical_url(value: object, field: str = "url") -> str:
    """Canonical form of one URL a gateway could block.

    Lowercases scheme and host, keeps any userinfo and port, drops the
    fragment, and leaves path and query untouched. ``http://brand.example@evil.example/``
    keeps its userinfo, so the host that matters — ``evil.example`` — is the
    one a reader sees after the ``@``.
    """
    text = _token(value, field)
    parts = urlsplit(text)
    scheme = parts.scheme.lower()
    if scheme not in ("http", "https") or not parts.hostname:
        raise InvalidReportedMessageError(
            f"{field} must be an http(s) URL with a host, got {value!r}"
        )
    userinfo, at, hostport = parts.netloc.rpartition("@")
    netloc = f"{userinfo}{at}{hostport.lower()}"
    return urlunsplit((scheme, netloc, parts.path, parts.query, ""))


def _attachment(entry: object, index: int) -> dict:
    where = f"attachments[{index}]"
    if not isinstance(entry, dict) or set(entry) != {"filename", "sha256", "size_bytes"}:
        raise InvalidReportedMessageError(
            f"{where} must be an object with exactly filename, sha256, size_bytes"
        )
    filename = _nfkc(entry["filename"], f"{where}.filename")
    if not filename:
        raise InvalidReportedMessageError(f"{where}.filename must not be empty")
    digest = _nfkc(entry["sha256"], f"{where}.sha256").lower()
    if not _SHA256.match(digest):
        raise InvalidReportedMessageError(f"{where}.sha256 must be 64 hex characters")
    size = entry["size_bytes"]
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise InvalidReportedMessageError(
            f"{where}.size_bytes must be a non-negative integer, got {size!r}"
        )
    return {"filename": filename, "sha256": digest, "size_bytes": size}


def validate_reported_message(raw_message: dict, report_source: str) -> dict:
    """Validate and canonicalise a fetched reported-message envelope.

    Parameters
    ----------
    raw_message
        ``message_id``, ``sender``, ``recipients`` (non-empty list),
        ``subject`` (may be empty — phishing mail sometimes has none) and
        ``received_at`` (Zulu instant) are required; ``urls`` and
        ``attachments`` (``filename`` / ``sha256`` / ``size_bytes``) are
        optional and default to empty. Any other key is rejected.
    report_source
        ``user_report`` or ``mailbox_sweep``. Carried forward because the
        suppression-rate and simulation click-rate metrics are accounted
        per source.

    Returns
    -------
    The canonical envelope, with ``sender_domain`` split out for the
    known-benign-sender lookup and ``report_source`` attached.

    Raises
    ------
    InvalidReportedMessageError
        On any grammar violation, including one attachment digest listed
        twice with different sizes — two files cannot share a SHA-256.
    """
    if not isinstance(raw_message, dict):
        raise InvalidReportedMessageError(
            f"raw_message must be an object, got {type(raw_message).__name__}"
        )
    missing = [k for k in _REQUIRED if k not in raw_message]
    unknown = sorted(set(raw_message) - set(_REQUIRED) - set(_OPTIONAL))
    if missing or unknown:
        raise InvalidReportedMessageError(
            f"raw_message keys: missing {missing}, unknown {unknown}"
        )
    source = _nfkc(report_source, "report_source")
    if source not in REPORT_SOURCES:
        raise InvalidReportedMessageError(
            f"report_source must be one of {list(REPORT_SOURCES)}, got {report_source!r}"
        )

    sender = canonical_address(raw_message["sender"], "sender")
    recipients_raw = raw_message["recipients"]
    if not isinstance(recipients_raw, list) or not recipients_raw:
        raise InvalidReportedMessageError("recipients must be a non-empty list")
    recipients = sorted(
        {canonical_address(r, f"recipients[{i}]") for i, r in enumerate(recipients_raw)}
    )
    urls_raw = raw_message.get("urls", [])
    if not isinstance(urls_raw, list):
        raise InvalidReportedMessageError("urls must be a list")
    urls = sorted({canonical_url(u, f"urls[{i}]") for i, u in enumerate(urls_raw)})

    attachments_raw = raw_message.get("attachments", [])
    if not isinstance(attachments_raw, list):
        raise InvalidReportedMessageError("attachments must be a list")
    by_digest: dict[str, dict] = {}
    for i, entry in enumerate(attachments_raw):
        item = _attachment(entry, i)
        seen = by_digest.get(item["sha256"])
        if seen is None:
            by_digest[item["sha256"]] = item
        elif seen["size_bytes"] != item["size_bytes"]:
            raise InvalidReportedMessageError(
                f"attachment {item['sha256']} listed with sizes "
                f"{seen['size_bytes']} and {item['size_bytes']}"
            )
        elif item["filename"] < seen["filename"]:
            by_digest[item["sha256"]] = item

    return {
        "message_id": _token(raw_message["message_id"], "message_id"),
        "sender": sender,
        "sender_domain": sender.rpartition("@")[2],
        "recipients": recipients,
        "subject": " ".join(_nfkc(raw_message["subject"], "subject").split()),
        "received_at": _zulu(raw_message["received_at"], "received_at"),
        "urls": urls,
        "attachments": [by_digest[d] for d in sorted(by_digest)],
        "report_source": source,
    }
