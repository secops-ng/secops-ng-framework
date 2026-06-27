"""F-WF-ASSET CORE-FANOUT-LANGGRAPH — committed worked-example pins the LangGraph adapter.

The committed
``examples/langgraph/asset_management/evidence/asset-inventory-delta-record.json``
is the LangGraph node adapter's output for the payload pinned in the
example's ``regenerate.py``. This test re-drives the adapter exactly
as a LangGraph integrator would (state mapping in, partial-state
update out) and pins the on-disk bytes against the committed example
— so a refactor of the workflow-local CORE-PRIM primitive or the
LangGraph node adapter that silently changes serialisation gets
caught at the byte level.

This is also the LangGraph end of the G-03 byte-parity contract: the
``artifact_id`` derives from
``SHA-256(<workflow_id>|<execution_id>|<captured_at>)`` and does NOT
key on the compile target, so the n8n and Temporal CORE-FANOUT
siblings re-derive the same record bytes (and the same
``artifact_id``) from the same primitive output. Cross-target
byte-parity invariants against the n8n and Temporal siblings are
pinned below.

If the change is intentional, regenerate the example::

    PYTHONPATH=. python examples/langgraph/asset_management/regenerate.py

and commit the updated bytes alongside the emitter change.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from compilers.langgraph.evidence import (
    emit_asset_inventory_delta_artifact_node,
)

REPO = Path(__file__).resolve().parents[3]
EXAMPLE = REPO / "examples" / "langgraph" / "asset_management"
SNAPSHOT = EXAMPLE / "evidence" / "asset-inventory-delta-record.json"
REGEN = EXAMPLE / "regenerate.py"


def _load_payload() -> dict:
    """Import the example's PAYLOAD constant without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_asset_management_langgraph_regen", REGEN
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.PAYLOAD


def test_example_snapshot_is_committed() -> None:
    assert SNAPSHOT.exists(), f"missing example snapshot: {SNAPSHOT}"
    assert SNAPSHOT.stat().st_size > 0


def test_example_snapshot_matches_langgraph_adapter(tmp_path: Path) -> None:
    payload = _load_payload()
    update = emit_asset_inventory_delta_artifact_node(
        {
            "asset_inventory_delta_payload": payload,
            "evidence_output_dir": tmp_path,
        }
    )
    written = Path(update["asset_inventory_delta_artifact_path"])
    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "examples/langgraph/asset_management/evidence/"
        "asset-inventory-delta-record.json drifted from the LangGraph "
        "adapter. If intentional, regenerate via "
        "`PYTHONPATH=. python examples/langgraph/asset_management/"
        "regenerate.py` and commit the new bytes."
    )
    # The partial state update carries the deterministic artifact_id;
    # the integrator joins this back into the running graph state.
    assert update["asset_inventory_delta_artifact_id"] == written.stem


def test_example_snapshot_carries_expected_anchors() -> None:
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    assert record["schema_version"] == "1.0.0"
    assert record["stream"] == "inventory"
    assert record["workflow_id"] == "asset_management"
    # artifact_id is deterministic SHA-256(workflow_id|execution_id|
    # captured_at) per the schema contract.
    assert len(record["artifact_id"]) == 64
    assert record["regulation_refs"] == ["nis2:art-21-2-i"]
    assert record["control_refs"] == ["control.asset_inventory_delta@v1"]
    # The four-bucket walk through the closed delta taxonomy.
    assert record["delta_classification"] == [
        "new-managed",
        "unmanaged-discovered",
        "decommissioned",
        "baseline-drift",
    ]
    assert record["unmanaged_discovered_count"] == 1


def test_example_snapshot_artifact_id_is_target_agnostic() -> None:
    """G-03 byte-parity contract: artifact_id keys on
    (workflow_id, execution_id, captured_at) only — never on
    compile_target."""
    import hashlib

    record = json.loads(SNAPSHOT.read_text("utf-8"))
    expected = hashlib.sha256(
        (
            f"{record['workflow_id']}|{record['execution_id']}|"
            f"{record['captured_at']}"
        ).encode("utf-8")
    ).hexdigest()
    assert record["artifact_id"] == expected


def test_langgraph_replay_matches_committed_n8n_sibling() -> None:
    """Cross-target byte-parity: LangGraph output must match the n8n
    sibling byte-for-byte. The workflow-local CORE-PRIM primitive is
    the source of truth."""
    n8n_snapshot = (
        REPO
        / "examples"
        / "n8n"
        / "asset_management"
        / "evidence"
        / "asset-inventory-delta-record.json"
    )
    assert n8n_snapshot.read_bytes() == SNAPSHOT.read_bytes()


def test_langgraph_replay_matches_committed_temporal_sibling() -> None:
    """Cross-target byte-parity: LangGraph output must match the
    Temporal sibling byte-for-byte. Closes the three-target G-03
    parity ring for asset_management — n8n ⇔ Temporal is pinned by
    the temporal-side test, n8n ⇔ LangGraph and Temporal ⇔ LangGraph
    are pinned here."""
    temporal_snapshot = (
        REPO
        / "examples"
        / "temporal"
        / "asset_management"
        / "evidence"
        / "asset-inventory-delta-record.json"
    )
    assert temporal_snapshot.read_bytes() == SNAPSHOT.read_bytes()


def test_langgraph_node_artifact_id_is_deterministic(tmp_path: Path) -> None:
    """Same payload → same artifact_id → byte-identical re-emission."""
    payload = _load_payload()
    first = emit_asset_inventory_delta_artifact_node(
        {
            "asset_inventory_delta_payload": payload,
            "evidence_output_dir": tmp_path,
        }
    )
    second = emit_asset_inventory_delta_artifact_node(
        {
            "asset_inventory_delta_payload": payload,
            "evidence_output_dir": tmp_path,
        }
    )
    assert (
        first["asset_inventory_delta_artifact_id"]
        == second["asset_inventory_delta_artifact_id"]
    )
    assert (
        Path(first["asset_inventory_delta_artifact_path"]).read_bytes()
        == Path(second["asset_inventory_delta_artifact_path"]).read_bytes()
    )


def test_langgraph_node_requires_state_keys() -> None:
    """Missing state keys raise a clear KeyError naming both fields."""
    import pytest

    with pytest.raises(KeyError) as exc_info:
        emit_asset_inventory_delta_artifact_node({})
    msg = str(exc_info.value)
    assert "asset_inventory_delta_payload" in msg
    assert "evidence_output_dir" in msg
