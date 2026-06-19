"""Shared primitives for the iam-auditor (F-WF-08) playbook.

This package is the single source of truth for the deterministic,
replay-friendly helpers that the per-target CORE action bodies
(n8n, Temporal, LangGraph) all bind against. Each primitive lands as
its own module so the per-target compilers depend only on what they
need:

* :mod:`.identity` — :func:`resolve_caller_identity` (enumerate-
  identities). Returns the role-shaped ``caller_identity`` block the
  access-evidence artifact joins to. The identity is supplied by the
  compile target's runtime (n8n credential binding, Temporal worker
  identity, LangGraph runtime principal); this primitive only
  canonicalises and validates it against the F-CP-07 schema discipline
  so a personal-user principal or credential-shaped string fails loud
  at the step boundary rather than at the artifact-emit boundary
  downstream.
* :mod:`.capabilities` — :func:`build_capability_list` (enumerate-
  capabilities). Canonicalises the closed verb.resource capability
  list the caller held at execution time. Dedups, lower-cases, and
  preserves the operator-side ordering so two replays of the same
  identity walk produce byte-identical bytes.
* :mod:`.artifact` — :func:`build_access_artifact` (emit-access-
  evidence). Assembles the JSON-native access-evidence record shaped
  against ``schemas/evidence/access.schema.json`` (stream: ``access``).
  The deterministic ``artifact_id`` derives from
  ``SHA-256(<workflow_id>|<execution_id>|<compile_target>)`` per the
  schema's ``artifact_id`` contract; re-emissions inside the same
  execution produce byte-identical bytes.

Style: every primitive is pure, network-free, LLM-free, deterministic.
Inputs are JSON-native (strings, ints, lists, dicts); outputs are
JSON-native; no datetime objects on the boundary so n8n Code nodes and
Temporal activities marshal identically. Mirrors the discipline pinned
in ``content/playbooks/vuln_intake/primitives/__init__.py`` and
``content/playbooks/codebase_vuln_management/primitives/__init__.py``.
"""

from __future__ import annotations

from .artifact import (
    InvalidAccessArtifactError,
    build_access_artifact,
    derive_access_artifact_id,
)
from .capabilities import (
    InvalidCapabilityListError,
    build_capability_list,
)
from .identity import (
    InvalidCallerIdentityError,
    resolve_caller_identity,
)

__all__ = [
    "InvalidAccessArtifactError",
    "InvalidCallerIdentityError",
    "InvalidCapabilityListError",
    "build_access_artifact",
    "build_capability_list",
    "derive_access_artifact_id",
    "resolve_caller_identity",
]
