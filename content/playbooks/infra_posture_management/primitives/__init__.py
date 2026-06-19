"""Shared primitives for the infrastructure-posture-management (F-WF-06) playbook.

This package is the single source of truth for the deterministic,
replay-friendly helpers that the per-target CORE action bodies
(n8n, Temporal, LangGraph) all bind against. Each primitive lands as
its own module so the per-target compilers depend only on what they
need:

* :mod:`.collect` — :func:`collect_posture_state` (collect-posture).
  Canonicalises the operator-supplied raw posture-collection snapshot
  into the closed ``posture_state`` block the schema pins; the
  ``snapshot_hash`` is the SHA-256 of the canonical resource list so
  replay re-derivation is byte-stable.
* :mod:`.controls` — :func:`evaluate_controls` (evaluate-controls).
  Builds the per-control evaluation result set against the collected
  posture state and the operator-supplied policy — one entry per
  declared control with the attestation state (effective /
  partially_effective / ineffective) and the deviation list.
* :mod:`.artifact` — :func:`build_posture_artifact` (emit-posture-
  evidence). Assembles the JSON-native posture-evidence record shaped
  against ``schemas/evidence/posture.schema.json`` (stream:
  ``posture``). The deterministic ``artifact_id`` derives from
  ``SHA-256(<workflow_id>|<execution_id>|<compile_target>|<policy_version.value>)``
  per the schema's ``artifact_id`` contract; re-emissions inside the
  same execution under the same policy version produce byte-identical
  bytes.

Style: every primitive is pure, network-free, LLM-free, deterministic.
Inputs are JSON-native (strings, ints, lists, dicts); outputs are
JSON-native; no datetime objects on the boundary so n8n Code nodes and
Temporal activities marshal identically. Mirrors the discipline pinned
in ``content/playbooks/iam_auditor/primitives/__init__.py`` and
``content/playbooks/codebase_vuln_management/primitives/__init__.py``.
"""

from __future__ import annotations

from .artifact import (
    InvalidPostureArtifactError,
    build_posture_artifact,
    derive_posture_artifact_id,
)
from .collect import (
    InvalidPostureStateError,
    collect_posture_state,
)
from .controls import (
    InvalidControlEvaluationError,
    evaluate_controls,
)

__all__ = [
    "InvalidControlEvaluationError",
    "InvalidPostureArtifactError",
    "InvalidPostureStateError",
    "build_posture_artifact",
    "collect_posture_state",
    "derive_posture_artifact_id",
    "evaluate_controls",
]
