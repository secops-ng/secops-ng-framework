"""Shared primitives for the agentic-threat-response (F-WF-AGENTIC-RESPONSE) playbook.

Single source of truth for the deterministic, replay-friendly helpers
the per-target CORE action bodies (n8n, Temporal, LangGraph) all bind
against. Each primitive lands as its own module so the per-target
compilers depend only on what they need:

* :mod:`.intake` -- :func:`hydrate_indicator` (ingest step).
  Canonicalises the detection layer's agentic-threat indicator into
  the closed response envelope: principal, source / destination
  context, self-correction cadence (divergence carried as data), and
  the implicated edge set. The agentic-activity classifier itself is
  an adapter-bound operator surface; the framework ships the contract,
  not a model.

* :mod:`.isolation` -- :func:`plan_credential_isolation` (isolate
  step). Derives the ordered credential cut-out ledger and composes
  the IAM-auditor alert; executing the revocations and delivering the
  alert are the compile target's IdP / messaging adapter surfaces.

* :mod:`.segmentation` -- :func:`derive_segmentation_rules` (contain
  step). Turns the lateral-movement path into deterministic deny
  rules, hard-bounded by the operator's authorisation policy.

* :mod:`.escalation` -- :func:`compose_escalation_envelope` (escalate
  step). Composes the ``playbook.incident_management@v1`` intake
  envelope with a signal id derived from the indicator, so
  cross-playbook dedup composes out of two derivations.

* :mod:`.evidence` -- :func:`seal_evidence_bundle` (preserve step).
  Seals the NIS2 Article 23 evidence manifest with a content-derived
  bundle id, joined to the case by the escalation signal id.

Style: every primitive is pure, network-free, LLM-free, deterministic.
Inputs are JSON-native (strings, ints, lists, dicts); outputs are
JSON-native; no datetime objects on the boundary so n8n Code nodes
and Temporal activities marshal identically. Mirrors the discipline
pinned in ``content/playbooks/cra_cvd/primitives/__init__.py`` and
``content/playbooks/backup_recovery/primitives/__init__.py``.
"""

from __future__ import annotations

from .escalation import (
    InvalidEscalationInputError,
    compose_escalation_envelope,
)
from .evidence import (
    ConflictingEvidenceError,
    IncompleteEvidenceError,
    InvalidEvidenceInputError,
    seal_evidence_bundle,
)
from .intake import (
    InvalidIndicatorError,
    hydrate_indicator,
)
from .isolation import (
    InvalidIsolationInputError,
    plan_credential_isolation,
)
from .segmentation import (
    InvalidSegmentationInputError,
    UnauthorisedSegmentError,
    derive_segmentation_rules,
)

__all__ = [
    "ConflictingEvidenceError",
    "IncompleteEvidenceError",
    "InvalidEscalationInputError",
    "InvalidEvidenceInputError",
    "InvalidIndicatorError",
    "InvalidIsolationInputError",
    "InvalidSegmentationInputError",
    "UnauthorisedSegmentError",
    "compose_escalation_envelope",
    "derive_segmentation_rules",
    "hydrate_indicator",
    "plan_credential_isolation",
    "seal_evidence_bundle",
]
