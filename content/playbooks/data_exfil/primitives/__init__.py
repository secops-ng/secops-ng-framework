"""Shared primitives for the data_exfil playbook.

The single source of truth for the deterministic helpers the per-target
CORE action bodies (n8n, Temporal, LangGraph) bind against:

* :mod:`.triage` — :func:`triage_egress_signal` (triage signal). Matches
  known-benign egress patterns, but never clears a signal that also saw a
  staging archive created.
* :mod:`.scope` — :func:`assess_exfil_scope` (scope assessment). Confirms
  exfiltration, resolves classification and distinct subjects, and decides
  the regulator threshold; content that could not be inspected routes as
  the worst case.
* :mod:`.containment` — :func:`compose_exfil_containment` (containment).
  Proportionate to classification and scope; protected assets wait for
  approval.
* :mod:`.notification` — :func:`compose_regulator_notification` and
  :func:`compose_subject_notification` (the two notification steps). One
  regulator notice per applicable regime with its own clock from
  awareness; a data-subject determination that always carries its basis.

Pure, offline and LLM-free: JSON-native inputs and outputs. Hydration,
content inspection, the egress and identity controls, and every
notification channel stay adapter-bound operator surfaces.
"""

from __future__ import annotations

from .containment import InvalidContainmentError, compose_exfil_containment
from .notification import (
    InvalidNotificationError,
    compose_regulator_notification,
    compose_subject_notification,
)
from .scope import CLASSIFICATIONS, InvalidScopeAssessmentError, assess_exfil_scope
from .triage import (
    EGRESS_CHANNELS,
    INDICATORS,
    SIGNAL_SOURCES,
    InvalidEgressSignalError,
    triage_egress_signal,
)

__all__ = [
    "CLASSIFICATIONS",
    "EGRESS_CHANNELS",
    "INDICATORS",
    "SIGNAL_SOURCES",
    "InvalidContainmentError",
    "InvalidEgressSignalError",
    "InvalidNotificationError",
    "InvalidScopeAssessmentError",
    "assess_exfil_scope",
    "compose_exfil_containment",
    "compose_regulator_notification",
    "compose_subject_notification",
    "triage_egress_signal",
]
