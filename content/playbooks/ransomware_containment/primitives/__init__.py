"""Shared primitives for the ransomware_containment playbook.

The single source of truth for the deterministic helpers the per-target
CORE action bodies (n8n, Temporal, LangGraph) bind against:

* :mod:`.triage` — :func:`triage_ransomware_signal` (triage signal).
  Decides confirmation by an explicit evidence rule — a decisive artifact,
  corroborated encryption behaviour, or pre-encryption recovery inhibition
  — and EDR availability. An analyst verdict decides when present, and a
  disagreement with the evidence is recorded as an override.
* :mod:`.isolation` — :func:`compose_edr_isolation` and
  :func:`compose_network_isolation` (the two isolation branches). Each
  re-checks the gates behind it; a protected host always waits for
  approval.
* :mod:`.identity` — :func:`compose_identity_revocation` (identity
  revocation). Lists what the IdP cannot revoke instead of claiming it; a
  protected principal waits for approval.
* :mod:`.backup` — :func:`select_known_good_snapshot` (backup
  verification). Known-good means the newest snapshot before the
  compromise window whose digest matches the catalogue. Never restores.
* :mod:`.comms` — :func:`compose_comms_plan` (comms plan). Pages the IR
  lead and comms officer and stages the NIS2 Art. 23(4)(a) early warning
  for human sign-off; never auto-sends.

Pure, offline and LLM-free: JSON-native inputs and outputs, no datetime
objects on the boundary. Hydration, the EDR, the network chokepoint, the
IdP, the backup platform and the paging channels stay adapter-bound
operator surfaces.
"""

from __future__ import annotations

from .backup import InvalidBackupSelectionError, select_known_good_snapshot
from .comms import InvalidCommsPlanError, compose_comms_plan
from .identity import InvalidIdentityRevocationError, compose_identity_revocation
from .isolation import InvalidIsolationDirectiveError, compose_edr_isolation, compose_network_isolation
from .triage import INDICATORS, SIGNAL_SOURCES, InvalidRansomwareSignalError, triage_ransomware_signal

__all__ = [
    "INDICATORS",
    "SIGNAL_SOURCES",
    "InvalidBackupSelectionError",
    "InvalidCommsPlanError",
    "InvalidIdentityRevocationError",
    "InvalidIsolationDirectiveError",
    "InvalidRansomwareSignalError",
    "compose_comms_plan",
    "compose_edr_isolation",
    "compose_identity_revocation",
    "compose_network_isolation",
    "select_known_good_snapshot",
    "triage_ransomware_signal",
]
