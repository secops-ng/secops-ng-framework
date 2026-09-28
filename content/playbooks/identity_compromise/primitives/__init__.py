"""Shared primitives for the identity_compromise playbook.

The single source of truth for the deterministic helpers the per-target
CORE action bodies (n8n, Temporal, LangGraph) bind against:

* :mod:`.triage` — :func:`triage_identity_signal` (triage identity signal).
  Benign patterns clear impossible travel only; a decisive detection, two
  corroborating ones, or any detection on a privileged principal confirms;
  an analyst verdict decides when present.
* :mod:`.mfa` — :func:`compose_mfa_reset` (reset MFA factors). Documents
  factors before and after; records "not applicable" for principals that
  cannot hold factors.
* :mod:`.sessions` — :func:`compose_session_revocation` (revoke active
  sessions). Counts what it revokes and names the tenants nobody
  enumerated.
* :mod:`.hunt` — :func:`summarise_lateral_hunt` (lateral-movement hunt).
  Counts distinct resources touched inside the window and reports which
  surfaces were never hunted.
* :mod:`.persistence` — :func:`plan_persistence_removal` (IAM audit and
  persistence removal). Removes what was created inside the compromise
  window without an authorising change record; says why everything else
  stays.

Pure, offline and LLM-free: JSON-native inputs and outputs. The IdP, the
SaaS tenants, the hunt queries and the change-management system stay
adapter-bound operator surfaces.
"""

from __future__ import annotations

from .hunt import HUNT_SURFACES, InvalidHuntSummaryError, summarise_lateral_hunt
from .mfa import FACTOR_KINDS, InvalidMfaResetError, compose_mfa_reset
from .persistence import IAM_ITEM_KINDS, InvalidPersistenceRemovalError, plan_persistence_removal
from .sessions import SESSION_KINDS, InvalidSessionRevocationError, compose_session_revocation
from .triage import DETECTIONS, PRINCIPAL_TYPES, SIGNAL_SOURCES, InvalidIdentitySignalError, triage_identity_signal

__all__ = [
    "DETECTIONS",
    "FACTOR_KINDS",
    "HUNT_SURFACES",
    "IAM_ITEM_KINDS",
    "PRINCIPAL_TYPES",
    "SESSION_KINDS",
    "SIGNAL_SOURCES",
    "InvalidHuntSummaryError",
    "InvalidIdentitySignalError",
    "InvalidMfaResetError",
    "InvalidPersistenceRemovalError",
    "InvalidSessionRevocationError",
    "compose_mfa_reset",
    "compose_session_revocation",
    "plan_persistence_removal",
    "summarise_lateral_hunt",
    "triage_identity_signal",
]
