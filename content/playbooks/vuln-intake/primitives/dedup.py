"""Deterministic dedup helper for vulnerability intake cases.

A case is uniquely identified by the pair ``(CVE id, asset ref)``. The
:func:`case_idempotency_key` function returns a SHA-256 lower-hex digest over
the canonicalised pair so that two replays of the same disclosure against the
same asset collapse to a single case.

Canonicalisation rules (:func:`canonicalize_case_field`):

* Unicode-NFKC normalisation so visually-identical inputs hash identically.
* Whitespace collapsed (leading/trailing trimmed, internal runs replaced by a
  single space).
* ASCII lowercasing for the alphanumeric portion of CVE-style ids and PURLs.
* Empty / whitespace-only inputs raise :class:`ValueError`.

The key is **not** a security token — it is an idempotency handle. The
deterministic part is what matters: a replay must produce the same key, and a
different ``(cve, asset)`` pair must produce a different key.
"""

from __future__ import annotations

import hashlib
import unicodedata


def canonicalize_case_field(value: str) -> str:
    """Return the canonical form of a single case field (``cve_id``, ``asset_ref``).

    Raises :class:`ValueError` if ``value`` is empty or whitespace-only.
    """
    if not isinstance(value, str):
        raise ValueError(f"case field must be a string, got {type(value).__name__}")
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise ValueError("case field is empty after canonicalisation")
    # Collapse internal whitespace runs.
    collapsed = " ".join(normalised.split())
    return collapsed.lower()


def case_idempotency_key(cve_id: str, asset_ref: str) -> str:
    """Return the SHA-256 lower-hex idempotency key for a case.

    The two fields are canonicalised independently and joined with a literal
    ``\\u001f`` (ASCII Unit Separator) — a character that cannot legally
    appear inside either input after canonicalisation — so the separator is
    unambiguous.
    """
    canonical_cve = canonicalize_case_field(cve_id)
    canonical_asset = canonicalize_case_field(asset_ref)
    payload = f"{canonical_cve}\x1f{canonical_asset}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
