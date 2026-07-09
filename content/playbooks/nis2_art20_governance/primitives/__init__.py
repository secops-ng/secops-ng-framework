"""Shared primitives for the NIS2 Art. 20 management-body governance (F-CACAO-NIS2-ART20) playbook.

Single source of truth for the deterministic, replay-friendly helpers
the per-target CORE action bodies (n8n, Temporal, LangGraph) all bind
against. Each primitive lands as its own module so the per-target
compilers depend only on what they need:

* :mod:`.cycle` -- :func:`resolve_governance_cycle`
  (schedule_management_review). Binds the operator's documented
  governance-cadence catalogue to ``__governance_cycle__`` and
  propagates the ad-hoc-trigger branch (empty ``__review_id__``)
  explicitly so the downstream evidence record captures the ad-hoc
  case rather than short-circuiting.

* :mod:`.review` -- :func:`conduct_art20_review`
  (present_risk_posture). Composes the per-cycle governance view of
  the operator's Article 21(2)(a)-(j) risk-posture and the training-
  completion evidence pull for the management-body cohort. Read-only
  against the evidence store.

* :mod:`.approval` -- :func:`record_management_approval`
  (approve_risk_measures). Records the signed management-body
  approval decision (approved / referred) and emits the dated
  governance-record JSON that carries the Article 20(2) training-
  completion attestation. Referral branch carries an empty
  ``approval_record_id`` explicitly.

* :mod:`.evidence` --
  :func:`emit_governance_evidence`
  (log_governance_evidence). Emits the OCSF API Activity
  (``class_uid`` 6003) governance-record artifact and the sibling
  audit-envelope the operator's evidence store persists. The
  deterministic ``artifact_id`` derives from
  ``SHA-256(<governance_cycle>|<review_id>|<approval_record_id>|<captured_at>)``
  -- ``compile_target`` is intentionally NOT part of the id so the
  three reference compilers re-derive byte-identical bytes
  (CORE-FANOUT byte-parity contract).

Style: every primitive is pure, network-free, LLM-free, deterministic.
Inputs are JSON-native (strings, ints, lists, dicts); outputs are
JSON-native; no datetime objects on the boundary so n8n Code nodes and
Temporal activities marshal identically. Mirrors the discipline pinned
in ``content/playbooks/mfa_secured_comms/primitives/__init__.py`` and
``content/playbooks/cra_cvd/primitives/__init__.py``.
"""

from __future__ import annotations

from .approval import (
    InvalidManagementApprovalError,
    record_management_approval,
)
from .cycle import (
    InvalidGovernanceCycleError,
    resolve_governance_cycle,
)
from .evidence import (
    InvalidGovernanceEvidenceError,
    derive_governance_evidence_artifact_id,
    emit_governance_evidence,
)
from .review import (
    InvalidArt20ReviewError,
    conduct_art20_review,
)

__all__ = [
    "InvalidArt20ReviewError",
    "InvalidGovernanceCycleError",
    "InvalidGovernanceEvidenceError",
    "InvalidManagementApprovalError",
    "conduct_art20_review",
    "derive_governance_evidence_artifact_id",
    "emit_governance_evidence",
    "record_management_approval",
    "resolve_governance_cycle",
]
