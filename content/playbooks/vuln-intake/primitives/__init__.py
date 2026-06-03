"""Shared primitives for the vulnerability intake (F-WF-01) playbook.

This module is the *single source of truth* for the deterministic, replay-friendly
helpers that the per-target CORE action bodies (n8n, Temporal, LangGraph) all bind
against:

* :mod:`.cvss` — pure-Python CVSS v3.1 / v4.0 vector parsing + base / temporal
  score derivation. No network calls.
* :mod:`.epss` — EPSS exploit-probability score validation and canonicalisation.
* :mod:`.severity` — deterministic mapping ``(CVSS metrics, EPSS score) -> band``
  where band is one of ``{critical, high, medium, low, info}``. Severity is
  **expressed as code** (FOUNDATION.md §determinism), reviewable in diff and
  byte-identical across replays.
* :mod:`.dedup` — deterministic dedup helper: idempotency key built from the
  canonicalised ``__cve_id__`` + ``__asset_ref__`` case fields, SHA-256 lower-hex.
* :mod:`.signatures` — DSPy signatures for **free-text fields only** (reporter
  narrative summarisation, advisory excerpt synthesis). Severity is **not** a
  DSPy signature; see :mod:`.severity`. Imported lazily so the package can be
  used in environments where ``dspy`` is not installed.

See ``docs/FOUNDATION.md`` §LLM determinism and ``docs/ARCHITECTURE.md``
§"LLM reasoning — DSPy" for the contract these primitives close against.
"""

from __future__ import annotations

from .cvss import CVSSMetrics, parse_cvss_vector
from .dedup import case_idempotency_key, canonicalize_case_field
from .epss import EPSSScore, canonicalize_epss, parse_epss
from .severity import SEVERITY_BANDS, SeverityBand, derive_severity

__all__ = [
    "CVSSMetrics",
    "EPSSScore",
    "SEVERITY_BANDS",
    "SeverityBand",
    "canonicalize_case_field",
    "canonicalize_epss",
    "case_idempotency_key",
    "derive_severity",
    "parse_cvss_vector",
    "parse_epss",
]
