"""Shared primitives for the patch_management (F-WF-PATCH) playbook.

This package is the single source of truth for the deterministic,
replay-friendly helpers that the per-target CORE action bodies
(n8n, Temporal, LangGraph) all bind against. Each primitive lands as
its own module so the per-target compilers depend only on what they
need:

* :mod:`.detect` -- :func:`detect_patch_availability`. Normalises an
  advisory / update observation against a tracked package / image /
  firmware line into a deterministic ``update-subject`` +
  ``update-reference`` record. Pure / replay-friendly.

* :mod:`.classify` -- :func:`classify_patch_criticality`. Per-update
  taxonomy resolver over the closed criticality enumeration
  (``security-critical``, ``security-routine``, ``feature-only``).
  Emits the sentinel ``unclassified`` when the documented intake
  deadline elapses.

* :mod:`.stage` -- :func:`stage_rollout_to_canary_ring`. Deterministic
  staged-ring-id derivation against the documented ring topology
  (test -> canary -> broad). Pure: same topology + canary cohort +
  update subject / reference yields a byte-identical SHA-256 id.

* :mod:`.validate` -- :func:`validate_canary`. Deterministic health-
  gate evaluation producing ``__canary_healthy__`` from the documented
  gate inputs (functional probe, error-rate threshold, latency
  threshold, rollback readiness). Pure over its inputs.

* :mod:`.fanout` -- :func:`fan_out_to_broad_rings`. Deterministic
  broad-rollout-id derivation; on an unhealthy canary the step is a
  deterministic skip leaving ``__broad_rollout_id__`` empty with an
  explicit ``broad_rollout_skip_reason='canary_unhealthy'`` marker.

* :mod:`.artifact` --
  :func:`build_patch_application_evidence_artifact`. Assembles the
  JSON-native patch-application evidence record shaped against
  ``schemas/evidence/patch.schema.json`` (stream: ``patch``). The
  deterministic ``artifact_id`` derives from
  ``SHA-256(<workflow_id>|<execution_id>|<captured_at>)`` -- the
  byte-parity contract the F-WF-PATCH CORE-FANOUT siblings assert
  against (``compile_target`` is intentionally NOT part of the id so
  the three reference compilers re-derive byte-identical bytes).

Style: every primitive is pure, network-free, LLM-free, deterministic.
Inputs are JSON-native (strings, ints, lists, dicts); outputs are
JSON-native; no datetime objects on the boundary so n8n Code nodes and
Temporal activities marshal identically. Mirrors the discipline pinned
in ``content/playbooks/asset_management/primitives/__init__.py`` and
``content/playbooks/iam_auditor/primitives/__init__.py``.
"""

from __future__ import annotations

from .artifact import (
    InvalidPatchApplicationArtifactError,
    build_patch_application_evidence_artifact,
    derive_patch_application_artifact_id,
)
from .classify import (
    InvalidPatchCriticalityError,
    classify_patch_criticality,
)
from .detect import (
    InvalidPatchDetectionError,
    detect_patch_availability,
)
from .fanout import (
    InvalidPatchFanOutError,
    fan_out_to_broad_rings,
)
from .stage import (
    InvalidPatchStagingError,
    stage_rollout_to_canary_ring,
)
from .validate import (
    InvalidCanaryValidationError,
    validate_canary,
)

__all__ = [
    "InvalidCanaryValidationError",
    "InvalidPatchApplicationArtifactError",
    "InvalidPatchCriticalityError",
    "InvalidPatchDetectionError",
    "InvalidPatchFanOutError",
    "InvalidPatchStagingError",
    "build_patch_application_evidence_artifact",
    "classify_patch_criticality",
    "derive_patch_application_artifact_id",
    "detect_patch_availability",
    "fan_out_to_broad_rings",
    "stage_rollout_to_canary_ring",
    "validate_canary",
]
