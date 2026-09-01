"""Shared primitives for the availability-attack response (F-WF-DDOS) playbook.

Single source of truth for the deterministic, replay-friendly helpers
the per-target CORE action bodies (n8n, Temporal, LangGraph) all bind
against. Each primitive lands as its own module so the per-target
compilers depend only on what they need:

* :mod:`.detect` -- :func:`resolve_availability_trigger` (detect
  step). Confirms the anomaly window is bounded and resolves the
  service's inventory row — objective plus the *fully pre-bound*
  three-surface mitigation ladder, which fails loud at detect time
  rather than mid-incident.

* :mod:`.classify` -- :func:`classify_attack_vector` (classify step).
  The closed three-vector taxonomy with pinned multi-signal precedence
  (volumetric > protocol > application_layer) and the time-boxed
  short-circuit semantics; the adapter enforces the clock, this
  module decides what its verdicts mean.

* :mod:`.mitigation` -- :func:`select_mitigation_engagement` (engage
  step). The contractual vector-to-discipline mapping, the
  most-restrictive fallback on the short-circuit branch, and the
  deterministic discipline-naming action id. Mitigation execution is
  an adapter-bound operator surface; the framework ships the hand-off,
  no scrubbing-provider binding.

* :mod:`.restoration` -- :func:`evaluate_service_restoration`
  (validate step). Restoration verified against observed traffic,
  never asserted on mitigation applied; a false outcome is data, and
  every breach is enumerated by dimension.

* :mod:`.evidence` -- :func:`compose_incident_evidence_record`
  (evidence step). The dated, content-identified NIS2 Art. 21(2)(b)
  record with machine-readable branch markers.

* :mod:`.notify` -- :func:`compose_owner_notification` (notify step).
  Urgency follows the restoration outcome; composition only, delivery
  is the messaging surface's.

Style: every primitive is pure, network-free, LLM-free, deterministic.
Inputs are JSON-native (strings, ints, lists, dicts); outputs are
JSON-native; no datetime objects on the boundary so n8n Code nodes
and Temporal activities marshal identically. Mirrors the discipline
pinned in ``content/playbooks/cra_cvd/primitives/__init__.py`` and
``content/playbooks/agentic_threat_response/primitives/__init__.py``.
"""

from __future__ import annotations

from .classify import (
    InvalidClassificationInputError,
    classify_attack_vector,
)
from .detect import (
    AmbiguousInventoryError,
    InvalidAvailabilityTriggerError,
    NoInventoryRowError,
    parse_anomaly_window,
    resolve_availability_trigger,
)
from .evidence import (
    InvalidEvidenceRecordError,
    compose_incident_evidence_record,
)
from .mitigation import (
    InvalidMitigationInputError,
    select_mitigation_engagement,
)
from .notify import (
    InvalidNotificationInputError,
    compose_owner_notification,
)
from .restoration import (
    InvalidObservationError,
    evaluate_service_restoration,
)

__all__ = [
    "AmbiguousInventoryError",
    "InvalidAvailabilityTriggerError",
    "InvalidClassificationInputError",
    "InvalidEvidenceRecordError",
    "InvalidMitigationInputError",
    "InvalidNotificationInputError",
    "InvalidObservationError",
    "NoInventoryRowError",
    "classify_attack_vector",
    "compose_incident_evidence_record",
    "compose_owner_notification",
    "evaluate_service_restoration",
    "parse_anomaly_window",
    "resolve_availability_trigger",
    "select_mitigation_engagement",
]
