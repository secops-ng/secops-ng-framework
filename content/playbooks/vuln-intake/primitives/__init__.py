"""Shared primitives for the vulnerability-intake (F-WF-01) playbook.

This package is the single source of truth for the deterministic,
replay-friendly helpers that the per-target CORE action bodies
(n8n, Temporal, LangGraph) all bind against. Each primitive lands as
its own module so the per-target compilers depend only on what they
need:

* :mod:`.dedup` — case idempotency key built from the canonicalised
  ``cve_id`` + ``asset_ref`` pair, SHA-256 lower-hex. Two replays of the
  same disclosure against the same asset collapse to the same key.
* :mod:`.signatures` — DSPy signatures for **free-text fields only**
  (reporter narrative summarisation, advisory excerpt synthesis). See
  ``docs/FOUNDATION.md`` §LLM determinism: severity rating is
  expressed as deterministic code, not as a DSPy module — DSPy is
  reserved for fields where free-text-in / structured-out is the only
  sensible shape.

Sibling primitives (CVSS, EPSS, severity policy) land via their own
cards in the F-WF-01 CORE-PRIM wave and are exposed through this
``__init__`` as they merge. To keep the per-card PRs parallel-safe and
the diffs reviewable, this file only re-exports the slice owned by the
PRs shipping it.
"""

from __future__ import annotations

from .dedup import canonicalize_case_field, case_idempotency_key
from .signatures import signature_schema

__all__ = [
    "canonicalize_case_field",
    "case_idempotency_key",
    "signature_schema",
]
