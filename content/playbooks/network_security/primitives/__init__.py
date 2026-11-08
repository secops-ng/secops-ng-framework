"""Shared primitives for the network_security playbook.

The single source of truth for the deterministic helpers the per-target
CORE action bodies (n8n, Temporal, LangGraph) bind against, one per action
step of the per-window segmentation reconciliation:

* :mod:`.inventory` — :func:`compose_segment_inventory`
  (inventory_network_segments). Sources in the operator's precedence order,
  disagreements recorded, undeclared segments listed as undocumented, and an
  identifier that replays.
* :mod:`.policy` — :func:`evaluate_segmentation_policy`
  (evaluate_segmentation_policy). The allowed / denied / conditional matrix,
  every unlisted pair denied, conditions as services or a time-boxed
  authorisation, and the policy's own gaps recorded.
* :mod:`.detection` — :func:`detect_policy_violations`
  (detect_policy_violations). Observed transits outside the matrix as
  undocumented transit or unauthorised egress; boundary rules that diverge
  from it as drift, in either direction.
* :mod:`.remediation` — :func:`dispatch_remediation` (enforce_remediation).
  Every violation to its bound surface, isolation only for active abuse with
  the operator's consent, and an identifier for every dispatch.
* :mod:`.evidence` — :func:`compose_posture_evidence`
  (generate_posture_evidence_artifact). One checked chain, a finding per
  violation with its action, and the window's open items.

Pure, offline and LLM-free: JSON-native inputs and outputs, no datetime
objects on the boundary. The inventory sources, the policy source, the
telemetry, the remediation surfaces and the evidence store stay adapter-bound
operator surfaces.
"""

from __future__ import annotations

from ._common import CLASSIFICATIONS
from .detection import OBSERVATION_SOURCES, InvalidViolationDetectionError, detect_policy_violations
from .evidence import InvalidPostureEvidenceError, compose_posture_evidence
from .inventory import SOURCE_KINDS, InvalidSegmentInventoryError, compose_segment_inventory
from .policy import ALLOWANCES, InvalidSegmentationPolicyError, evaluate_segmentation_policy
from .remediation import (
    DEFAULT_BINDING,
    SURFACES,
    InvalidRemediationDispatchError,
    dispatch_remediation,
)

__all__ = [
    "ALLOWANCES",
    "CLASSIFICATIONS",
    "DEFAULT_BINDING",
    "OBSERVATION_SOURCES",
    "SOURCE_KINDS",
    "SURFACES",
    "InvalidPostureEvidenceError",
    "InvalidRemediationDispatchError",
    "InvalidSegmentInventoryError",
    "InvalidSegmentationPolicyError",
    "InvalidViolationDetectionError",
    "compose_posture_evidence",
    "compose_segment_inventory",
    "detect_policy_violations",
    "dispatch_remediation",
    "evaluate_segmentation_policy",
]
