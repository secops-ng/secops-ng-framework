"""Shared primitives for the eu_ai_act_deployer_obligations playbook.

The single source of truth for the deterministic helpers the per-target
CORE action bodies (n8n, Temporal, LangGraph) bind against, one per action
step of the Regulation (EU) 2024/1689 deployer lifecycle:

* :mod:`.intended_use` — :func:`determine_intended_use` (confirm intended
  use). Art. 26(1): the declared contexts must stay inside the contexts the
  provider's instructions permit; Art. 26(7): a workplace deployment by an
  employer needs the dated notice to workers' representatives and affected
  workers first. A negative result is a first-class record, and every later
  primitive refuses it.
* :mod:`.oversight` — :func:`compose_oversight_assignment` (assign human
  oversight). Art. 26(2): each assignee is a natural person with evidence for
  competence, training, authority and support; any missing limb leaves the
  assignment incomplete.
* :mod:`.monitoring` — :func:`classify_monitoring_window` (monitor
  operation). Art. 26(4)–(5): the input-data determination, and the three
  escalation triggers kept apart — Art. 72 post-market feedback, the
  Art. 79(1) inform-and-suspend duty, and sequenced serious-incident
  notification on the severity-classed Art. 73 clock.
* :mod:`.fria` — :func:`assess_fundamental_rights_impact` (assess
  fundamental-rights impact). Art. 27: the scope determination, the six
  elements as a checklist complementing a GDPR Art. 35 DPIA, and the
  market-surveillance notification.
* :mod:`.retention` — :func:`compose_retention_evidence` (retain logs and
  evidence). Art. 26(6): the log-control determination and a retention
  period of at least six months unless applicable law provides otherwise,
  joined into the dated cycle-evidence artifact.

Pure, offline and LLM-free: JSON-native inputs and outputs, no datetime
objects on the boundary. The deployment register, the provider's
instructions, the training and governance surfaces, the monitoring feeds,
the DPIA and the log store stay adapter-bound operator surfaces.
"""

from __future__ import annotations

from .fria import ANNEX_III_POINTS, ELEMENTS, InvalidFundamentalRightsAssessmentError, assess_fundamental_rights_impact
from .intended_use import InvalidIntendedUseError, determine_intended_use
from .monitoring import FINDING_KINDS, INCIDENT_OUTCOMES, InvalidMonitoringWindowError, classify_monitoring_window
from .oversight import LIMBS, InvalidOversightAssignmentError, compose_oversight_assignment
from .retention import FLOOR_MONTHS, InvalidRetentionEvidenceError, compose_retention_evidence

__all__ = [
    "ANNEX_III_POINTS",
    "ELEMENTS",
    "FINDING_KINDS",
    "FLOOR_MONTHS",
    "INCIDENT_OUTCOMES",
    "LIMBS",
    "InvalidFundamentalRightsAssessmentError",
    "InvalidIntendedUseError",
    "InvalidMonitoringWindowError",
    "InvalidOversightAssignmentError",
    "InvalidRetentionEvidenceError",
    "assess_fundamental_rights_impact",
    "classify_monitoring_window",
    "compose_oversight_assignment",
    "compose_retention_evidence",
    "determine_intended_use",
]
