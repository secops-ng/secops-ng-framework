"""Shared primitives for the ``vuln-intake`` playbook.

Pure-Python helpers that the per-target CORE action bodies (n8n, Temporal,
LangGraph) bind against. This package is grown by the F-WF-01 CORE-PRIM
sibling wave; each sibling card adds one primitive module:

  * :mod:`.epss`       — EPSS exploit-probability score validation (range,
                         freshness, source attribution) + canonicalisation
  * (siblings):        CVSS vector parse + base score, deterministic
                         severity band derivation, case dedup key, DSPy
                         signatures for free-text fields

This card ships the EPSS module only. Public re-exports are added by each
sibling as it lands.
"""

from __future__ import annotations

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
    "canonicalize_epss",
    "parse_epss",
]
