"""F-WF-ASSET CORE-FANOUT-N8N — committed worked-example pins the n8n adapter.

The committed
``examples/n8n/asset_management/evidence/asset-inventory-delta-record.json``
is the n8n adapter's output for the payload pinned in the example's
``regenerate.py``. This test re-drives the adapter from that payload
and pins the on-disk bytes against the committed example — so a
refactor of the shared CORE-PRIM primitive or the n8n adapter that
silently changes serialisation gets caught at the byte level.

If the change is intentional, regenerate the example::

    PYTHONPATH=. python examples/n8n/asset_management/regenerate.py

and commit the updated bytes alongside the emitter change.

This is also the n8n end of the G-03 byte-parity contract: the
``artifact_id`` derives from
``SHA-256(<workflow_id>|<execution_id>|<captured_at>)`` and does NOT
key on the compile target, so the Temporal and LangGraph CORE-FANOUT
siblings will re-derive the same record bytes (and the same
``artifact_id``) from the same primitive output.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from compilers.n8n.evidence import emit_asset_inventory_delta_artifact_n8n

REPO = Path(__file__).resolve().parents[3]
EXAMPLE = REPO / "examples" / "n8n" / "asset_management"
SNAPSHOT = EXAMPLE / "evidence" / "asset-inventory-delta-record.json"
REGEN = EXAMPLE / "regenerate.py"


def _load_payload() -> dict:
    """Import the example's PAYLOAD constant without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_asset_management_regen", REGEN
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.PAYLOAD


def test_example_snapshot_is_committed() -> None:
    assert SNAPSHOT.exists(), f"missing example snapshot: {SNAPSHOT}"
    assert SNAPSHOT.stat().st_size > 0


def test_example_snapshot_matches_n8n_adapter(tmp_path: Path) -> None:
    payload = _load_payload()
    result = emit_asset_inventory_delta_artifact_n8n(payload, tmp_path)
    written = Path(result["artifact_path"])
    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "examples/n8n/asset_management/evidence/"
        "asset-inventory-delta-record.json drifted from the n8n adapter. "
        "If intentional, regenerate via "
        "`PYTHONPATH=. python examples/n8n/asset_management/regenerate.py` "
        "and commit the new bytes."
    )


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
    # Pre-computed exception-bucket cardinality the inventory-owner
    # notification step pages on (NIS2 Art. 21(2)(i) exception
    # bucket).
    assert record["unmanaged_discovered_count"] == 1


def test_example_snapshot_artifact_id_is_target_agnostic() -> None:
    """G-03 byte-parity contract: artifact_id keys on
    (workflow_id, execution_id, captured_at) only — never on
    compile_target. This test pins the derivation so a regression
    that adds compile_target into the id derivation gets caught at
    the n8n end before the Temporal / LangGraph siblings land."""
    import hashlib

    record = json.loads(SNAPSHOT.read_text("utf-8"))
    expected = hashlib.sha256(
        (
            f"{record['workflow_id']}|{record['execution_id']}|"
            f"{record['captured_at']}"
        ).encode("utf-8")
    ).hexdigest()
    assert record["artifact_id"] == expected
