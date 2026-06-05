"""Shared primitives for the alert-triage (F-WF-03) playbook.

This package is the single source of truth for the deterministic,
replay-friendly helpers that the per-target CORE action bodies
(n8n, Temporal, LangGraph) all bind against. Each primitive lands as
its own module so the per-target compilers depend only on what they
need:

* :mod:`.prioritisation` — deterministic priority policy. Maps the
  detection axis + asset axis + suppression axis into one of four
  priority bands (``p1_severe`` / ``p2_high`` / ``p3_routine`` /
  ``p4_informational``). The priority decision is **code, not LM** per
  ``docs/FOUNDATION.md`` §LLM determinism.
* :mod:`.suppression` — canonical seen-key derivation and the
  sliding suppression-window helper. Two re-fires of the same alert
  (same detection rule, same subject, same asset, same classification)
  inside the window collapse onto one case.
* :mod:`.payloads` — typed-payload validators for the two source
  shapes the playbook ingests (push from a detection pipeline, pull
  from a shared alert store). Backed by the workflow-local Pydantic
  models under ``content.playbooks.alert_triage.payloads``.
* :mod:`.signatures` — DSPy signature for **free-text fields only**
  (analyst summary + narrative for the case view). See
  ``docs/FOUNDATION.md`` §LLM determinism: priority is deterministic
  code, DSPy is reserved for free-text fields where free-text-in /
  structured-out is the only sensible shape.
"""

from __future__ import annotations

from .payloads import (
    AlertPayload,
    PayloadValidationError,
    SUPPORTED_SHAPES,
    validate_alert_payload,
)
from .prioritisation import (
    AssetContext,
    AssetCriticality,
    DetectionClass,
    DetectionSeverity,
    Priority,
    PriorityVerdict,
    prioritise,
)
from .response import (
    EscalationDirective,
    INCIDENT_MANAGEMENT_PLAYBOOK_REF,
    PagingTier,
    escalation_route,
)
from .signatures import signature_schema
from .suppression import (
    SeenRecord,
    SuppressionVerdict,
    SuppressionWindow,
    canonical_seen_key,
)

__all__ = [
    "AlertPayload",
    "AssetContext",
    "AssetCriticality",
    "DetectionClass",
    "DetectionSeverity",
    "EscalationDirective",
    "INCIDENT_MANAGEMENT_PLAYBOOK_REF",
    "PagingTier",
    "PayloadValidationError",
    "Priority",
    "PriorityVerdict",
    "SUPPORTED_SHAPES",
    "SeenRecord",
    "SuppressionVerdict",
    "SuppressionWindow",
    "canonical_seen_key",
    "escalation_route",
    "prioritise",
    "signature_schema",
    "validate_alert_payload",
]
