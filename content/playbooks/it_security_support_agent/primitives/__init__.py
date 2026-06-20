"""Shared primitives for the IT and security support-agent (F-WF-12) playbook.

This package is the single source of truth for the deterministic,
replay-friendly helpers that the per-target CORE action bodies
(n8n, Temporal, LangGraph) all bind against. Each primitive lands as
its own module so the per-target compilers depend only on what they
need:

* :mod:`.ingest` — :func:`ingest_support_request` (ingest-support-request).
  Canonicalises the operator-supplied raw support-request record into
  the closed envelope the downstream primitives consume: ``request_kind``
  (informational | actionable | incident-shaped), role-shaped
  ``requester_handle``, ``declared_symptom``, ``received_at``. Personal-
  user requester handles and credential-shaped strings are rejected at
  the primitive boundary so a free-text or personal-name field fails
  loud at the step boundary rather than at the artifact-emit boundary
  downstream.
* :mod:`.classify` — :func:`classify_request` (classify-request). Pure
  derivation: given the ingested support-request record and the
  operator-supplied classification-policy table, returns the closed
  verdict envelope (``category``, severity band, ordered ``rule_ids``).
  Deterministic on the same record + same policy version.
* :mod:`.resolution` — :func:`attempt_automated_resolution`
  (attempt-automated-resolution). Captures the closed observation
  envelope read back from the operator's self-service surface after
  the workflow ran the declared automated-resolution action set
  (``outcome`` in {resolved, partial, not_attempted, failed},
  ``declared_action_set`` it ran, ``observed_state`` it read back).
  The actual self-service execution is the compile target's job; this
  primitive only pins the closed-observation shape so re-runs collapse
  to byte-identical bytes.
* :mod:`.handoff` — :func:`escalate_with_human_handoff`
  (escalate-with-human-handoff). First-class explicit handoff
  primitive. ALWAYS materialises a closed handoff envelope —
  ``handoff_fired`` is set explicitly on every path, ``responder_queue``
  is role-shaped (responder rota, automation responder role, on-call
  shift handle; personal-user responder handles are rejected here),
  ``trigger_reason`` pins the closed decision rule (incident-shaped
  classification → handoff; automated-resolution outcome ≠ resolved →
  handoff; operator policy override → handoff; otherwise no handoff
  with the closure reason recorded). The workflow MUST NOT silently
  auto-close.
* :mod:`.artifact` — :func:`build_interaction_artifact`
  (emit-interaction-evidence). Assembles the JSON-native interaction-
  evidence record shaped against ``schemas/evidence/incidents.schema.json``
  (stream: ``incidents``). Reuses the F-CP-02 incidents stream that the
  F-WF-05 incident-management workflow already binds onto —
  significant=true on a handoff_fired=true path so the F-CP-02
  incidents-stream KPI surface counts the support→incident handoff once
  on the same NIS2 Article 21(2)(b) anchor F-WF-05 discharges,
  significant=false on the schema's intake-only audit-close branch when
  the support interaction closed without a handoff. The deterministic
  ``incident_id`` (UUIDv5 of ``<workflow_id>|<execution_id>``) and
  ``artifact_id`` (SHA-256 of ``<incident_id>|<execution_id>``) derive
  on the primitive boundary so re-emission inside the same execution
  is byte-identical.

Style: every primitive is pure, network-free, LLM-free, deterministic.
Inputs are JSON-native (strings, ints, lists, dicts); outputs are
JSON-native; no datetime objects on the boundary so n8n Code nodes and
Temporal activities marshal identically. Mirrors the discipline pinned
in ``content/playbooks/iam_auditor/primitives/__init__.py``,
``content/playbooks/contractual_obligations_tracker/primitives/__init__.py``,
and ``content/playbooks/onboarding_offboarding_tracker/primitives/__init__.py``.
"""

from __future__ import annotations

from .artifact import (
    InvalidInteractionArtifactError,
    build_interaction_artifact,
    derive_interaction_artifact_id,
    derive_interaction_incident_id,
)
from .classify import (
    InvalidClassificationError,
    classify_request,
)
from .handoff import (
    InvalidHumanHandoffError,
    escalate_with_human_handoff,
)
from .ingest import (
    InvalidSupportRequestError,
    ingest_support_request,
)
from .resolution import (
    InvalidAutomatedResolutionError,
    attempt_automated_resolution,
)

__all__ = [
    "InvalidAutomatedResolutionError",
    "InvalidClassificationError",
    "InvalidHumanHandoffError",
    "InvalidInteractionArtifactError",
    "InvalidSupportRequestError",
    "attempt_automated_resolution",
    "build_interaction_artifact",
    "classify_request",
    "derive_interaction_artifact_id",
    "derive_interaction_incident_id",
    "escalate_with_human_handoff",
    "ingest_support_request",
]
