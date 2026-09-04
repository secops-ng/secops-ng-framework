"""Shared primitives for the EUDIW verification (F-WF-EIDAS2-IDV) playbook.

Single source of truth for the deterministic, replay-friendly helpers
the per-target CORE action bodies (n8n, Temporal, LangGraph) all bind
against. Each primitive lands as its own module so the per-target
compilers depend only on what they need:

* :mod:`.presentation` -- :func:`compose_presentation_request`
  (request step). The eIDAS 2.0 Art. 5c presentation request:
  credential types only, read-only against the wallet, correlation id
  derived from principal / scope / credential set / request instant.

* :mod:`.verification` -- :func:`record_pid_verification` (verify
  step). Consumes the adapter's typed report (trust anchor, signature
  chain, holder binding, revocation status) into one boolean verdict —
  no partial-trust state, unknown status fails closed — retaining the
  outcome and its provenance, never the attested attributes
  (attribute-shaped fields are actively refused).

* :mod:`.assurance` -- :func:`assess_assurance_level` (assess step).
  The closed low < substantial < high ladder against the operator's
  documented tier table; explicit refusals for the failed-verification
  and below-minimum branches — a principal is never quietly downgraded
  onto a lower tier; undocumented mappings fail loud.

* :mod:`.evidence` -- :func:`compose_identity_evidence_record` (emit
  step). The OCSF Account Change (class_uid 3001) audit record on
  every terminal path, failure branch included, with the evidence id
  derived exactly as the step prescribes
  (SHA-256 over principal | request | captured_at).

* :mod:`.provisioning` -- :func:`compose_provisioning_handoff`
  (trigger step). The hand-off into
  playbook.onboarding_offboarding_tracker@v1, correlated on the
  principal — or the explicit, reasoned no-hand-off on the refusal
  branches.

Style: every primitive is pure, network-free, LLM-free, deterministic.
Inputs are JSON-native (strings, ints, lists, dicts); outputs are
JSON-native; no datetime objects on the boundary so n8n Code nodes
and Temporal activities marshal identically. Mirrors the discipline
pinned in ``content/playbooks/cra_cvd/primitives/__init__.py`` and
``content/playbooks/data_subject_rights/primitives/__init__.py``.
"""

from __future__ import annotations

from .assurance import (
    InvalidAssuranceInputError,
    assess_assurance_level,
)
from .evidence import (
    InvalidIdentityEvidenceError,
    compose_identity_evidence_record,
)
from .presentation import (
    InvalidPresentationRequestError,
    compose_presentation_request,
)
from .provisioning import (
    InvalidProvisioningHandoffError,
    compose_provisioning_handoff,
)
from .verification import (
    InvalidVerificationReportError,
    record_pid_verification,
)

__all__ = [
    "InvalidAssuranceInputError",
    "InvalidIdentityEvidenceError",
    "InvalidPresentationRequestError",
    "InvalidProvisioningHandoffError",
    "InvalidVerificationReportError",
    "assess_assurance_level",
    "compose_identity_evidence_record",
    "compose_presentation_request",
    "compose_provisioning_handoff",
    "record_pid_verification",
]
