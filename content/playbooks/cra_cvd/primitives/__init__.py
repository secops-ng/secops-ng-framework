"""Shared primitives for the CRA Article 14 CVD (F-WF-CRA-CVD) playbook.

Single source of truth for the deterministic, replay-friendly helpers
the per-target CORE action bodies (n8n, Temporal, LangGraph) all bind
against. Each primitive lands as its own module so the per-target
compilers depend only on what they need:

* :mod:`.reporter` -- :func:`send_acknowledgement` (ack_to_reporter).
  Canonicalises the operator-supplied acknowledgement inputs and
  returns a pure JSON-native envelope carrying the ack payload plus
  the operator-supplied SMTP endpoint handle. The framework ships no
  default endpoint; the operator wires the concrete SMTP endpoint at
  the compile target's config layer (typically via env-var indirection
  in the runtime, resolved to the ``smtp_endpoint`` argument here) and
  the primitive fails closed on an empty / missing endpoint.

* :mod:`.disclosure` -- :func:`build_advisory_artifact` (publish_advisory).
  Builds the CSAF 2.0 shape stub envelope the human-readable and
  machine-readable advisory templates render from. Pure envelope
  dict; template rendering (Jinja2) is owned by the per-target
  compiler adapters, not this module.

* :mod:`.csirt` -- :func:`notify_national_csirt` (coordinate_disclosure
  side-effect, not currently CORE-bound as an action body; kept in the
  primitive surface so the EXTEND scope can wire it later). Returns a
  pure JSON-native notify envelope with an operator-supplied CSIRT
  endpoint handle. Framework ships no default endpoint.

Style: every primitive is pure, network-free, LLM-free, deterministic.
Inputs are JSON-native (strings, ints, lists, dicts); outputs are
JSON-native; no datetime objects on the boundary so n8n Code nodes
and Temporal activities marshal identically. Mirrors the discipline
pinned in ``content/playbooks/mfa_secured_comms/primitives/__init__.py``
and ``content/playbooks/supply_chain_security/primitives/__init__.py``.
"""

from __future__ import annotations

from .csirt import (
    InvalidCsirtNotificationError,
    notify_national_csirt,
)
from .disclosure import (
    InvalidAdvisoryArtifactError,
    build_advisory_artifact,
)
from .reporter import (
    InvalidAcknowledgementError,
    send_acknowledgement,
)

__all__ = [
    "InvalidAcknowledgementError",
    "InvalidAdvisoryArtifactError",
    "InvalidCsirtNotificationError",
    "build_advisory_artifact",
    "notify_national_csirt",
    "send_acknowledgement",
]
