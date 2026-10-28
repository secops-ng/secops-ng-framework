"""Shared primitives for the data_protection_impact_assessment playbook.

The single source of truth for the deterministic helpers the per-target
CORE action bodies (n8n, Temporal, LangGraph) bind against, one per action
step of the GDPR Art. 35 assessment. Every rule was checked against
Regulation (EU) 2016/679 on EUR-Lex and, where the Regulation leaves the
method open, against the WP248 rev.01 guidelines the EDPB endorsed.

The first five steps (CORE-PRIM part 1):

* :mod:`.screening` — :func:`screen_dpia_triggers` (screen_dpia_triggers).
  Art. 35(10), similar-assessment coverage, Art. 35(3), the Art. 35(4) and
  35(5) lists and the WP248 two-criteria rule, in that order; a negative
  screening is retained with its basis.
* :mod:`.classification` — :func:`classify_processing`
  (classify_processing_type). The Art. 30 record's shape; the DPIA is the
  controller's, and lawfulness gaps under Arts. 6, 9(2) and 10 are recorded.
* :mod:`.description` — :func:`compose_processing_description`
  (gather_processing_description). The Art. 35(7)(a) description with the
  WP248 Annex 2 elements, and the gaps it still has.
* :mod:`.necessity` — :func:`assess_necessity_and_proportionality`
  (assess_necessity_and_proportionality). Art. 35(7)(b): necessity against
  less intrusive alternatives, data minimisation and storage limitation,
  and the rights measures still owed.
* :mod:`.risk` — :func:`assess_risks` (identify_and_assess_risks).
  Art. 35(7)(c): sources, threats, impacts, likelihood and severity per
  risk, all three reference events covered, on the operator's calibration.

The remaining five (mitigations, DPO consultation, the Art. 36 gate, the
document and the review cadence) are part 2. Pure, offline and LLM-free:
JSON-native inputs and outputs, no datetime objects on the boundary. The
Art. 30 record, the supervisory-authority lists, the risk taxonomy and the
evidence store stay adapter-bound operator surfaces.
"""

from __future__ import annotations

from ._common import ART_35_3, RISK_EVENTS, SPECIAL_CATEGORIES, VULNERABLE_SUBJECTS, WP248_CRITERIA
from .classification import ROLES, InvalidProcessingClassificationError, classify_processing
from .description import (
    ASSET_KINDS,
    RECIPIENT_ROLES,
    TRANSFER_MECHANISMS,
    InvalidProcessingDescriptionError,
    compose_processing_description,
)
from .necessity import OUTCOMES, RIGHTS_MEASURES, InvalidNecessityAssessmentError, assess_necessity_and_proportionality
from .risk import InvalidRiskAssessmentError, assess_risks
from .screening import BASES, InvalidScreeningError, screen_dpia_triggers

__all__ = [
    "ART_35_3",
    "ASSET_KINDS",
    "BASES",
    "OUTCOMES",
    "RECIPIENT_ROLES",
    "RIGHTS_MEASURES",
    "RISK_EVENTS",
    "ROLES",
    "SPECIAL_CATEGORIES",
    "TRANSFER_MECHANISMS",
    "VULNERABLE_SUBJECTS",
    "WP248_CRITERIA",
    "InvalidNecessityAssessmentError",
    "InvalidProcessingClassificationError",
    "InvalidProcessingDescriptionError",
    "InvalidRiskAssessmentError",
    "InvalidScreeningError",
    "assess_necessity_and_proportionality",
    "assess_risks",
    "classify_processing",
    "compose_processing_description",
    "screen_dpia_triggers",
]
