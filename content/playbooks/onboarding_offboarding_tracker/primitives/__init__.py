"""Shared primitives for the onboarding/offboarding tracker (F-WF-11) playbook.

This package is the single source of truth for the deterministic,
replay-friendly helpers that the per-target CORE action bodies
(n8n, Temporal, LangGraph) all bind against. Each primitive lands as
its own module so the per-target compilers depend only on what they
need:

* :mod:`.ingest` — :func:`ingest_lifecycle_event` (ingest-lifecycle-event).
  Canonicalises the operator-supplied raw lifecycle-event record into
  the closed envelope the downstream primitives consume:
  ``event_kind`` (joiner | mover | leaver), role-shaped principal
  handle, declared capability delta (add-set, remove-set), and
  effective_at. Personal-user principals and credential-shaped strings
  are rejected at the primitive boundary so a free-text or personal-
  name field fails loud at the step boundary rather than at the
  artifact-emit boundary downstream.
* :mod:`.identity` — :func:`resolve_identity` (resolve-identity).
  Re-shapes the principal handle carried by the ingested lifecycle
  event into the role-shaped ``caller_identity`` block the F-CP-07
  schema pins. The compile target's runtime is the source of truth
  for the resolution result; this primitive validates against the
  same shape regex the schema enforces so a personal-user principal
  cannot slip past the step.
* :mod:`.delta` — :func:`apply_capability_delta` (apply-capability-delta).
  Pure derivation: given a normalised lifecycle event and a resolved
  identity, return the closed ``add_set`` / ``remove_set`` the
  workflow asked the operator's identity source to materialise. No
  IdP mutation happens here — the operator's compile target wires
  the actual write in its native idiom. The primitive only pins the
  closed-delta shape so re-runs collapse to byte-identical bytes.
* :mod:`.confirmation` — :func:`confirm_grant_revoke` (confirm-grant-revoke).
  Compare the operator-supplied observed capability list (read back
  from the identity source after the delta was applied) against the
  declared delta. Returns the closed observed capability list, a
  ``confirmed`` boolean, and the divergence detail (missing grants,
  lingering revokes) the access-evidence artifact carries downstream.
* :mod:`.artifact` — :func:`build_access_artifact` (emit-access-evidence).
  Assembles the JSON-native access-evidence record shaped against
  ``schemas/evidence/access.schema.json`` (stream: ``access``). Reuses
  the F-CP-07 closed ``caller_identity`` + ``capabilities`` envelope
  the F-WF-08 IAM auditor primitive already pins — the joiner-mover-
  leaver execution evidence shares the schema, the deterministic
  ``artifact_id`` derivation, and the byte-stable re-emission contract
  with the read-side per-execution capability inventory.

Style: every primitive is pure, network-free, LLM-free, deterministic.
Inputs are JSON-native (strings, ints, lists, dicts); outputs are
JSON-native; no datetime objects on the boundary so n8n Code nodes and
Temporal activities marshal identically. Mirrors the discipline pinned
in ``content/playbooks/iam_auditor/primitives/__init__.py`` and
``content/playbooks/contractual_obligations_tracker/primitives/__init__.py``.
"""

from __future__ import annotations

from .artifact import (
    InvalidAccessArtifactError,
    build_access_artifact,
    derive_access_artifact_id,
)
from .confirmation import (
    InvalidConfirmationError,
    confirm_grant_revoke,
)
from .delta import (
    InvalidCapabilityDeltaError,
    apply_capability_delta,
)
from .identity import (
    InvalidResolvedIdentityError,
    resolve_identity,
)
from .ingest import (
    InvalidLifecycleEventError,
    ingest_lifecycle_event,
)

__all__ = [
    "InvalidAccessArtifactError",
    "InvalidCapabilityDeltaError",
    "InvalidConfirmationError",
    "InvalidLifecycleEventError",
    "InvalidResolvedIdentityError",
    "apply_capability_delta",
    "build_access_artifact",
    "confirm_grant_revoke",
    "derive_access_artifact_id",
    "ingest_lifecycle_event",
    "resolve_identity",
]
