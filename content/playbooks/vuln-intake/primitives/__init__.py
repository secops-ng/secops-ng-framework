"""Shared primitives for the vulnerability-intake (F-WF-01) playbook.

This package is the single source of truth for the deterministic,
replay-friendly helpers that the per-target CORE action bodies
(n8n, Temporal, LangGraph) all bind against. Each primitive lands as
its own module so the per-target compilers depend only on what they
need:

* :mod:`.signatures` — DSPy signatures for **free-text fields only**
  (reporter narrative summarisation, advisory excerpt synthesis). See
  ``docs/FOUNDATION.md`` §LLM determinism: severity rating is
  expressed as deterministic code, not as a DSPy module — DSPy is
  reserved for fields where free-text-in / structured-out is the only
  sensible shape.

Sibling primitives (CVSS, EPSS, severity policy, deterministic dedup)
land via their own cards in the F-WF-01 CORE-PRIM wave and are exposed
through this ``__init__`` as they merge. To keep the per-card PRs
parallel-safe and the diffs reviewable, this file only re-exports the
slice owned by the PR shipping it.
"""

from __future__ import annotations

from .signatures import signature_schema

__all__ = [
    "signature_schema",
]
