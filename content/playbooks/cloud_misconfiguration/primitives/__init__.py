"""Shared primitives for the cloud_misconfiguration playbook.

The single source of truth for the deterministic helpers the per-target
CORE action bodies (n8n, Temporal, LangGraph) bind against, one per action
step of the per-finding posture remediation loop:

* :mod:`.finding` — :func:`normalise_posture_finding` (ingest finding). One
  finding, one case, fingerprinted by rule and resource; detection latency
  only when the introducing change is known.
* :mod:`.context` — :func:`resolve_resource_context` (enrich resource and
  owner). Owner with a recorded fallback to the default pool, severity
  shifted by the operator's classification policy, suppression only by a
  live, exact, time-boxed ledger entry, and recurrence as the KRI defines it.
* :mod:`.suppression` — :func:`compose_suppression_closure` (suppress and
  close). Closes on the matched entry without widening it, and only while it
  is still live.
* :mod:`.notification` — :func:`compose_owner_notification` (notify owner).
  A channel bound for every severity, never for a suppressed finding.
* :mod:`.remediation` — :func:`record_remediation_attempt` (guided
  remediation). An attested change: a change record always, an approver for
  an automated hand-off.
* :mod:`.verification` — :func:`verify_remediation` (re-scan). Verified
  only by a pass of the same rule, on the same resource and baseline, after
  the change.
* :mod:`.escalation` — :func:`compose_escalation` (escalate). The attempt
  and the failing evidence, for an unverified remediation only.

Pure, offline and LLM-free: JSON-native inputs and outputs, no datetime
objects on the boundary. The posture-management layer, the inventory and
ownership graph, the exception ledger, the channels and the change surface
stay adapter-bound operator surfaces.
"""

from __future__ import annotations

from ._common import CLASSES, CONTROL_ANCHORS, SEVERITIES
from .context import CLOSURE_OUTCOMES, EXCEPTION_KINDS, InvalidResourceContextError, resolve_resource_context
from .escalation import InvalidEscalationError, compose_escalation
from .finding import SOURCES, InvalidPostureFindingError, normalise_posture_finding
from .notification import InvalidOwnerNotificationError, compose_owner_notification
from .remediation import MODES, InvalidRemediationAttemptError, record_remediation_attempt
from .suppression import InvalidSuppressionError, compose_suppression_closure
from .verification import RESULTS, InvalidVerificationError, verify_remediation

__all__ = [
    "CLASSES",
    "CLOSURE_OUTCOMES",
    "CONTROL_ANCHORS",
    "EXCEPTION_KINDS",
    "MODES",
    "RESULTS",
    "SEVERITIES",
    "SOURCES",
    "InvalidEscalationError",
    "InvalidOwnerNotificationError",
    "InvalidPostureFindingError",
    "InvalidRemediationAttemptError",
    "InvalidResourceContextError",
    "InvalidSuppressionError",
    "InvalidVerificationError",
    "compose_escalation",
    "compose_owner_notification",
    "compose_suppression_closure",
    "normalise_posture_finding",
    "record_remediation_attempt",
    "resolve_resource_context",
    "verify_remediation",
]
