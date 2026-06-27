"""Temporal-side adapter for the asset-inventory-delta evidence emitter.

F-WF-ASSET CORE-FANOUT-TEMPORAL. Mirrors the merged n8n adapter at
:mod:`compilers.n8n.evidence.inventory_node` exactly — same
JSON-native payload contract, same return shape, same atomic-write
semantics. The asset-inventory-delta record is the
``stream='inventory'`` shape pinned by the F-WF-ASSET CORE-PRIM
primitive at
:func:`content.playbooks.asset_management.primitives.artifact.build_asset_inventory_delta_evidence_artifact`.

Unlike the F-CP-02 incidents and F-CP-07 access Temporal activities,
this activity does **not** delegate through a shared
``compilers/_shared/evidence`` helper — record assembly,
``artifact_id`` (SHA-256 of
``<workflow_id>|<execution_id>|<captured_at>``) derivation, and the
schema-conforming shape are all owned by the workflow-local primitive
at
:func:`content.playbooks.asset_management.primitives.artifact.build_asset_inventory_delta_evidence_artifact`,
which is purpose-shaped for the asset-management reconciliation
workflow (the delta-set, source-set, and snapshot identifiers it
emits are not reusable on other streams). This activity is glue
only: payload in (mapping), atomic write to disk via the primitive's
record, written absolute path out — exactly the shape the F-WF-12
interaction-evidence Temporal activity returns so a Temporal worker
sees one contract across workflow-local-primitive streams.

Importing ``temporalio`` is required at install time; it is already a
transitive dependency of the Temporal worked examples under
``examples/temporal/`` (including the F-WF-ASSET asset_management
worked example this activity wraps).

Per AGENTS.md § 3 — sovereign-stack default. The operator-configured
inventory sources (CMDB reference, IaC declaration set, cloud-provider
asset-API binding, endpoint-management agent fleet) and the
``emit-asset-inventory-delta`` evidence sink are all
operator-bound at execution time. The activity does not impose a
hosted CMDB SaaS or any non-EU endpoint; it persists the artifact
bytes to whatever ``output_dir`` the caller (a Temporal workflow or
operator harness) hands it.

Re-emission for the same ``(workflow_id, execution_id, captured_at)``
is idempotent: the primitive derives the same ``artifact_id``, and the
activity writes the same bytes through a sibling ``.tmp`` +
``os.replace`` so a concurrent reader cannot observe a partial write.
``artifact_id`` is intentionally NOT keyed on the compile target — re-
emission at the same ``captured_at`` instant under the n8n adapter or
the LangGraph node produces a byte-identical artifact (G-03 byte-parity
contract the CORE-FANOUT siblings collectively pin).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from temporalio import activity

from content.playbooks.asset_management.primitives import (
    build_asset_inventory_delta_evidence_artifact,
)

__all__ = ["emit_asset_inventory_delta_artifact_activity"]


def _serialise(record: Mapping[str, Any]) -> str:
    """Render the record bytes the activity writes to disk.

    Matches the convention the F-WF-ASSET n8n adapter and the
    workflow-local primitive use (``indent=2``, ``sort_keys=True``,
    trailing newline) so a diff of the asset-inventory-delta artifact
    against the n8n sibling reads byte-identical, and the per-target
    byte-parity invariant holds against the n8n and LangGraph siblings
    for the same canonical payload.
    """
    return json.dumps(record, indent=2, sort_keys=True) + "\n"


@activity.defn
async def emit_asset_inventory_delta_artifact_activity(
    payload: Mapping[str, Any],
    output_dir: str | os.PathLike[str],
) -> str:
    """Persist one asset-inventory-delta evidence artifact from a Temporal payload.

    Inputs
    ------
    payload
        JSON-native mapping mirroring the keyword arguments of
        :func:`build_asset_inventory_delta_evidence_artifact`. Required
        keys: ``workflow_id``, ``execution_id``, ``regulation_refs``,
        ``control_refs``, ``snapshot_window``, ``snapshot_id``,
        ``source_set_id``, ``delta_set``, ``delta_classification``,
        ``captured_at``, ``source_url``. Optional keys: ``commit_sha``,
        ``owner_role``, ``owner_assigned_at``, ``retention``.
    output_dir
        Operator-supplied directory the artifact lands in. Created if
        it does not exist.

    Returns
    -------
    Absolute path of the written record as a string so the Temporal-side
    caller can attach it to subsequent activity inputs (the
    inventory-owner notification step, downstream NIS2 Article 21(2)(i)
    KPI rollups once they land) and to the workflow's audit trail. The
    ``artifact_id`` is deterministic on
    ``(workflow_id, execution_id, captured_at)`` so a replay of the
    same execution at the same captured instant re-derives the same id
    and downstream deduplication is trivial.
    """
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

    return str(out_path.resolve())
