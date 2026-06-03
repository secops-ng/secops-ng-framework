"""Shared primitives for the vulnerability intake (F-WF-01) playbook.

This package is the *single source of truth* for the deterministic,
replay-friendly helpers that the per-target CORE action bodies (n8n,
Temporal, LangGraph) all bind against.

Currently landed:

* :mod:`.dedup` — case idempotency key built from the canonicalised
  ``cve_id`` + ``asset_ref`` pair, SHA-256 lower-hex. Two replays of the
  same disclosure against the same asset collapse to the same key.
* :mod:`.epss`  — EPSS exploit-probability score validation (range,
  freshness, source attribution) + canonicalisation to a two-decimal
  ROUND_HALF_EVEN string for byte-identical replays.

Sibling SKEL PRs land the CVSS, severity, and DSPy-signature primitives
in the same package.

See ``docs/FOUNDATION.md`` §determinism for the contract these
primitives close against.
"""

from __future__ import annotations

from .dedup import canonicalize_case_field, case_idempotency_key
from .epss import (
    DEFAULT_FRESHNESS_WINDOW,
    EPSSScore,
    StaleEPSSWarning,
    canonicalize_epss,
    parse_epss,
)

__all__ = [
    "DEFAULT_FRESHNESS_WINDOW",
    "EPSSScore",
    "StaleEPSSWarning",
    "canonicalize_case_field",
    "canonicalize_epss",
    "case_idempotency_key",
    "parse_epss",
]
