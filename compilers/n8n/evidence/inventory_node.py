"""n8n-side adapter for the asset-inventory-delta evidence emitter.

n8n runs workflows in Node.js, so the integration point on the n8n
side is a node that hands its JSON payload to an out-of-process Python
helper — typically an ``n8n-nodes-base.executeCommand`` node invoking
``python -m compilers.n8n.evidence.inventory_node`` or a ``Code`` node
embedding the equivalent call. Either way the adapter is a pure
function: ``payload (mapping) + output_dir`` in, ``{artifact_id,
artifact_path}`` out.

Record assembly, schema-conforming shape, and the deterministic
``artifact_id`` derivation all live on the F-WF-ASSET CORE-PRIM
primitive at
``content.playbooks.asset_management.primitives.artifact``; this
adapter is glue that marshals the JSON-native payload, calls the
primitive, and persists the record atomically. ``artifact_id`` is
derived from ``SHA-256(<workflow_id>|<execution_id>|<captured_at>)``
and is intentionally NOT keyed on the compile target — re-emission at
the same ``captured_at`` instant under a different target produces a
byte-identical artifact at the path level (G-03 byte-parity contract
the CORE-FANOUT siblings assert against).

CORE-FANOUT-N8N only — Temporal and LangGraph adapters live in
separate CORE-FANOUT-TEMPORAL / CORE-FANOUT-LANGGRAPH siblings.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from content.playbooks.asset_management.primitives import (
    build_asset_inventory_delta_evidence_artifact,
)

__all__ = ["emit_asset_inventory_delta_artifact_n8n"]


def emit_asset_inventory_delta_artifact_n8n(
    payload: Mapping[str, Any],
    output_dir: str | os.PathLike[str],
) -> dict[str, Any]:
    """Persist one asset-inventory-delta evidence artifact from an n8n payload.

    The payload mirrors the keyword arguments of
    :func:`build_asset_inventory_delta_evidence_artifact`. Every field
    is a JSON-native type because n8n cannot ship Python objects
    across the node-process boundary. ``captured_at`` arrives as the
    canonical ISO-8601 ``...Z`` string and is passed through unchanged
    — the primitive validates the shape.

    Returns a JSON-serialisable dict shaped for an n8n node's
    next-node output::

        {"artifact_id": <sha256>, "artifact_path": "<abspath>"}

    Re-emission for the same ``(workflow_id, execution_id,
    captured_at)`` is byte-identical at the path level: the shared
    record assembly is deterministic and this adapter writes through
    a sibling ``.tmp`` plus ``os.replace`` so a concurrent reader
    cannot observe a partial write.
    """
    fields = dict(payload)
    record = build_asset_inventory_delta_evidence_artifact(
        workflow_id=fields["workflow_id"],
        execution_id=fields["execution_id"],
        regulation_refs=fields["regulation_refs"],
        control_refs=fields["control_refs"],
        snapshot_window=fields["snapshot_window"],
        snapshot_id=fields["snapshot_id"],
        source_set_id=fields["source_set_id"],
        delta_set=fields["delta_set"],
        delta_classification=fields["delta_classification"],
        captured_at=fields["captured_at"],
        source_url=fields["source_url"],
        commit_sha=fields.get("commit_sha"),
        owner_role=fields.get("owner_role"),
        owner_assigned_at=fields.get("owner_assigned_at"),
        retention=fields.get("retention"),
    )
    artifact_id = record["artifact_id"]
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{artifact_id}.json"
    tmp_path = out_dir / f".{artifact_id}.json.tmp"
    serialised = json.dumps(record, indent=2, sort_keys=True) + "\n"
    tmp_path.write_text(serialised, encoding="utf-8")
    os.replace(tmp_path, out_path)
    return {
        "artifact_id": artifact_id,
        "artifact_path": str(out_path.resolve()),
    }
