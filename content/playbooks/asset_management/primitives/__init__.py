"""Shared primitives for the asset_management (F-WF-ASSET) playbook.

This package is the single source of truth for the deterministic,
replay-friendly helpers that the per-target CORE action bodies
(n8n, Temporal, LangGraph) all bind against. Each primitive lands as
its own module so the per-target compilers depend only on what they
need:

* :mod:`.reconcile` \u2014 :func:`reconcile_inventory_snapshot`
  (reconcile-authoritative-inventory). Merges per-source asset
  observations under the operator's documented source-precedence
  ordering and emits the deterministic ``snapshot_id`` /
  ``source_set_id`` / canonical asset record list. Pure, replay-
  friendly; same inputs (under any input ordering) yield byte-
  identical output.

* :mod:`.classify` \u2014 :func:`classify_inventory_delta`
  (classify-delta). Resolves each per-asset delta against the closed
  delta taxonomy (``new-managed``, ``unmanaged-discovered``,
  ``decommissioned``, ``baseline-drift``) or returns the single
  sentinel ``[\"unclassified\"]`` when the documented reconciliation
  deadline elapses. Per-delta consistency invariants (change-kind vs
  state transition) are enforced at the primitive boundary.

* :mod:`.artifact` \u2014
  :func:`build_asset_inventory_delta_evidence_artifact`
  (capture-evidence). Assembles the JSON-native asset-inventory-delta
  evidence record shaped against ``schemas/evidence/inventory.schema.json``
  (stream: ``inventory``). The deterministic ``artifact_id`` derives
  from ``SHA-256(<workflow_id>|<execution_id>|<captured_at>)`` per the
  schema contract \u2014 ``compile_target`` is intentionally NOT part of
  the id so the three reference compilers re-derive byte-identical
  bytes (CORE-FANOUT byte-parity contract).

Style: every primitive is pure, network-free, LLM-free, deterministic.
Inputs are JSON-native (strings, ints, lists, dicts); outputs are
JSON-native; no datetime objects on the boundary so n8n Code nodes and
Temporal activities marshal identically. Mirrors the discipline pinned
in ``content/playbooks/supply_chain_security/primitives/__init__.py``
and ``content/playbooks/iam_auditor/primitives/__init__.py``.
"""

from __future__ import annotations

from .artifact import (
    InvalidAssetInventoryDeltaArtifactError,
    build_asset_inventory_delta_evidence_artifact,
    derive_asset_inventory_delta_artifact_id,
)
from .classify import (
    InvalidInventoryDeltaClassificationError,
    classify_inventory_delta,
)
from .reconcile import (
    InvalidInventorySnapshotError,
    reconcile_inventory_snapshot,
)

__all__ = [
    "InvalidAssetInventoryDeltaArtifactError",
    "InvalidInventoryDeltaClassificationError",
    "InvalidInventorySnapshotError",
    "build_asset_inventory_delta_evidence_artifact",
    "classify_inventory_delta",
    "derive_asset_inventory_delta_artifact_id",
    "reconcile_inventory_snapshot",
]
