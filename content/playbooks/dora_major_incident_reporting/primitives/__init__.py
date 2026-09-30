"""Shared primitives for the dora_major_incident_reporting playbook.

The single source of truth for the deterministic helpers the per-target
CORE action bodies (n8n, Temporal, LangGraph) bind against:

* :mod:`.classification` — :func:`classify_major_incident` (detect and
  classify). The Commission Delegated Regulation (EU) 2024/1772 Art. 8(1)
  combination rule — critical services affected, and either malicious
  unauthorised access or two or more materiality thresholds met — plus the
  recurring-incident aggregation, over per-criterion determinations the
  operator's classification policy supplies.
* :mod:`.notification` — :func:`compose_initial_notification`,
  :func:`compose_intermediate_report` and :func:`compose_final_report`
  (the three notify-authority steps). Thin JSON-native wrappers around the
  existing Art. 19 report builder in
  ``compilers/_shared/evidence/dora_art19_report.py``, adding the chain
  between milestones, each milestone's deadline, and the major-only gate.
* :mod:`.archive` — :func:`compose_cycle_archive` (close and archive).
  Always emitted; refuses a major incident without its complete chain and
  a non-major incident with any report attached.

Pure, offline and LLM-free. The incident register, the competent-authority
channel and the evidence store stay adapter-bound operator surfaces.
"""

from __future__ import annotations

from .archive import InvalidArchiveError, compose_cycle_archive
from .classification import MATERIALITY_CRITERIA, InvalidClassificationError, classify_major_incident
from .notification import (
    InvalidReportingError,
    compose_final_report,
    compose_initial_notification,
    compose_intermediate_report,
)

__all__ = [
    "MATERIALITY_CRITERIA",
    "InvalidArchiveError",
    "InvalidClassificationError",
    "InvalidReportingError",
    "classify_major_incident",
    "compose_cycle_archive",
    "compose_final_report",
    "compose_initial_notification",
    "compose_intermediate_report",
]
