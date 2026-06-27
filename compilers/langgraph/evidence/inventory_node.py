"""LangGraph node adapter for the asset-inventory-delta evidence emitter.

F-WF-ASSET CORE-FANOUT-LANGGRAPH. Mirrors the merged n8n adapter at
:mod:`compilers.n8n.evidence.inventory_node` and the Temporal activity
at
:mod:`compilers.temporal.evidence.inventory_activity` exactly — same
JSON-native payload contract, same atomic-write semantics, same
deterministic ``artifact_id`` derivation. The asset-inventory-delta
record is the ``stream='inventory'`` shape pinned by the F-WF-ASSET
CORE-PRIM primitive at
:func:`content.playbooks.asset_management.primitives.artifact.build_asset_inventory_delta_evidence_artifact`.

The adapter is a plain LangGraph node function: ``state -> state``.
The integrator wires it into a ``StateGraph`` with
``graph.add_node("emit_asset_inventory_delta",
emit_asset_inventory_delta_artifact_node)``; no LangGraph or
LangChain import is required at the compiler layer, matching the
runtime-free convention documented in
``compilers/langgraph/__init__.py``.

Unlike the F-CP-02 incidents adapter under
:mod:`compilers.langgraph.evidence.incidents_node`, this adapter does
**not** delegate through a shared ``compilers/_shared/evidence``
helper — record assembly, ``artifact_id`` (SHA-256 of
``<workflow_id>|<execution_id>|<captured_at>``) derivation, and the
schema-conforming shape are all owned by the workflow-local primitive
at
:func:`content.playbooks.asset_management.primitives.artifact.build_asset_inventory_delta_evidence_artifact`,
which is purpose-shaped for the asset-management reconciliation
workflow (the delta-set, source-set, and snapshot identifiers it
emits are not reusable on other streams). The node is glue only:
state mapping in, atomic write to disk, partial state update out —
same shape the n8n adapter and Temporal activity produce so cross-
target byte-parity holds against the same canonical payload.

Expected state keys:

* ``asset_inventory_delta_payload`` — a JSON-native mapping mirroring
  the keyword arguments of
  :func:`build_asset_inventory_delta_evidence_artifact`. Required
  keys: ``workflow_id``, ``execution_id``, ``regulation_refs``,
  ``control_refs``, ``snapshot_window``, ``snapshot_id``,
  ``source_set_id``, ``delta_set``, ``delta_classification``,
  ``captured_at``, ``source_url``. Optional keys: ``commit_sha``,
  ``owner_role``, ``owner_assigned_at``, ``retention``.
* ``evidence_output_dir`` — operator-supplied directory the artifact
  lands in. Created if it does not exist.

The node returns a partial state update:
``{"asset_inventory_delta_artifact_path": <abspath>,
   "asset_inventory_delta_artifact_id": <sha256>}``. LangGraph merges
the update into the running state by key so downstream nodes (the
inventory-owner notification step, downstream NIS2 Article 21(2)(i)
KPI rollups once they land) can attach the path to their own audit
trail.

Re-emission for the same ``(workflow_id, execution_id, captured_at)``
is idempotent: the primitive derives the same ``artifact_id``, and the
node writes the same bytes through a sibling ``.tmp`` + ``os.replace``
so a concurrent reader cannot observe a partial write.
``artifact_id`` is intentionally NOT keyed on the compile target — re-
emission at the same ``captured_at`` instant under the n8n adapter or
the Temporal activity produces a byte-identical artifact (G-03
byte-parity contract the CORE-FANOUT siblings collectively pin).

Per AGENTS.md § 3 — sovereign-stack default. The operator-configured
inventory sources (CMDB reference, IaC declaration set, cloud-provider
asset-API binding, endpoint-management agent fleet) and the
``emit-asset-inventory-delta`` evidence sink are all
operator-bound at execution time. The node does not impose a hosted
CMDB SaaS or any non-EU endpoint; it persists the artifact bytes to
whatever ``evidence_output_dir`` the integrator binds in state.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from content.playbooks.asset_management.primitives import (
    build_asset_inventory_delta_evidence_artifact,
)

__all__ = ["emit_asset_inventory_delta_artifact_node"]


def _serialise(record: Mapping[str, Any]) -> str:
    """Render the record bytes the node writes to disk.

    Matches the convention the F-WF-ASSET n8n adapter and Temporal
    activity use (``indent=2``, ``sort_keys=True``, trailing newline)
    so a diff of the asset-inventory-delta artifact against the n8n
    and Temporal siblings reads byte-identical, and the per-target
    byte-parity invariant holds against both for the same canonical
    payload.
    """
    return json.dumps(record, indent=2, sort_keys=True) + "\n"


def emit_asset_inventory_delta_artifact_node(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist one asset-inventory-delta evidence artifact from LangGraph state.

    Reads ``asset_inventory_delta_payload`` and ``evidence_output_dir``
    from ``state`` and returns a partial state update carrying the
    written path and the deterministic ``artifact_id``. The primitive
    does its own validation; this function is a thin adapter only.

    CORE-FANOUT pins the payload contract; the per-target byte-parity
    golden and the cross-target byte-parity invariant are pinned by
    the sibling tests under
    ``tests/examples/asset_management/``.
    """
    try:
        payload = state["asset_inventory_delta_payload"]
        output_dir = state["evidence_output_dir"]
    except KeyError as exc:  # pragma: no cover - guard against integrator typos
        raise KeyError(
            "emit_asset_inventory_delta_artifact_node requires "
            "'asset_inventory_delta_payload' and 'evidence_output_dir' "
            "in state"
        ) from exc

    record = build_asset_inventory_delta_evidence_artifact(
        workflow_id=payload["workflow_id"],
        execution_id=payload["execution_id"],
        regulation_refs=payload["regulation_refs"],
        control_refs=payload["control_refs"],
        snapshot_window=payload["snapshot_window"],
        snapshot_id=payload["snapshot_id"],
        source_set_id=payload["source_set_id"],
        delta_set=payload["delta_set"],
        delta_classification=payload["delta_classification"],
        captured_at=payload["captured_at"],
        source_url=payload["source_url"],
        commit_sha=payload.get("commit_sha"),
        owner_role=payload.get("owner_role"),
        owner_assigned_at=payload.get("owner_assigned_at"),
        retention=payload.get("retention"),
    )

    artifact_id = record["artifact_id"]

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{artifact_id}.json"
    tmp_path = out_dir / f".{artifact_id}.json.tmp"
    tmp_path.write_text(_serialise(record), encoding="utf-8")
    os.replace(tmp_path, out_path)

    return {
        "asset_inventory_delta_artifact_path": str(out_path.resolve()),
        "asset_inventory_delta_artifact_id": artifact_id,
    }
