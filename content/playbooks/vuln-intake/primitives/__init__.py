"""Shared primitives for the vulnerability intake (F-WF-01) playbook.

This package is the *single source of truth* for the deterministic,
replay-friendly helpers that the per-target CORE action bodies (n8n,
Temporal, LangGraph) all bind against.

This PR lands the deterministic dedup helper:

* :mod:`.dedup` — case idempotency key built from the canonicalised
  ``cve_id`` + ``asset_ref`` pair, SHA-256 lower-hex. Two replays of the
  same disclosure against the same asset collapse to the same key.

Sibling SKEL PRs land the CVSS, EPSS, severity, and DSPy-signature
primitives in the same package.

See ``docs/FOUNDATION.md`` §determinism for the contract these
primitives close against.
"""

from __future__ import annotations

from .dedup import canonicalize_case_field, case_idempotency_key

__all__ = [
    "canonicalize_case_field",
    "case_idempotency_key",
]
