"""Shared primitives for the cryptographic-controls (F-WF-CRYPTO-CONTROLS) playbook.

Single source of truth for the deterministic, replay-friendly helpers
the per-target CORE action bodies (n8n, Temporal, LangGraph) all bind
against. Each primitive lands as its own module so the per-target
compilers depend only on what they need:

* :mod:`.policy` -- :func:`resolve_policy_inventory`
  (resolve-policy-inventory step). The policy is input, not content:
  the closed seven-clause vocabulary, gaps flagged and never filled
  with a default — a shipped baseline would become a de-facto standard
  the framework has no authority to set (sovereign-stack constraint).

* :mod:`.keys` -- :func:`record_key_lifecycle` (key-lifecycle step).
  Metadata-only evidence for generate / rotate / revoke — key material
  is actively refused at the boundary; per-clause verdicts on the
  satisfied / violated / undocumented ladder, with ``compliant``
  reserved for documented-and-satisfied (undocumented is never
  compliant — acceptance criterion).

* :mod:`.certificates` -- :func:`record_certificate_lifecycle`
  (certificate-lifecycle step). Trust-anchor and expiry-buffer
  verdicts on the same ladder; a revocation requires its reason and
  the revocation-list reference.

* :mod:`.enforcement` -- :func:`decide_enforcement_gate`
  (enforce-encryption step). Read-and-decide only: deny iff a
  documented clause is violated; an undocumented clause admits but is
  enumerated, never reported satisfied; a missing at-rest key binding
  is structurally violated regardless of clause coverage.

* :mod:`.attestation` -- :func:`compose_lifecycle_attestation`
  (record-lifecycle-evidence step). The dated write-side attestation
  the crypto_posture_management read-side measures against;
  event-class / payload cross-consistency fails loud; breach and
  policy-gap flags computed once here.

* :mod:`.notify` -- :func:`compose_owner_notification`
  (notify-crypto-owner step). Urgency follows the attestation flags;
  composition only, delivery is the messaging surface's.

Style: every primitive is pure, network-free, LLM-free, deterministic.
Inputs are JSON-native (strings, ints, lists, dicts); outputs are
JSON-native; no datetime objects on the boundary so n8n Code nodes
and Temporal activities marshal identically. Mirrors the discipline
pinned in ``content/playbooks/cra_cvd/primitives/__init__.py`` and
``content/playbooks/ddos_response/primitives/__init__.py``.
"""

from __future__ import annotations

from .attestation import (
    InvalidAttestationInputError,
    compose_lifecycle_attestation,
)
from .certificates import (
    InvalidCertificateLifecycleInputError,
    record_certificate_lifecycle,
)
from .enforcement import (
    InvalidEnforcementInputError,
    decide_enforcement_gate,
)
from .keys import (
    InvalidKeyLifecycleInputError,
    record_key_lifecycle,
)
from .notify import (
    InvalidNotificationInputError,
    compose_owner_notification,
)
from .policy import (
    InvalidPolicyDeclarationError,
    resolve_policy_inventory,
)

__all__ = [
    "InvalidAttestationInputError",
    "InvalidCertificateLifecycleInputError",
    "InvalidEnforcementInputError",
    "InvalidKeyLifecycleInputError",
    "InvalidNotificationInputError",
    "InvalidPolicyDeclarationError",
    "compose_lifecycle_attestation",
    "compose_owner_notification",
    "decide_enforcement_gate",
    "record_certificate_lifecycle",
    "record_key_lifecycle",
    "resolve_policy_inventory",
]
