"""F-WF-SCS CORE-FANOUT-TMP — supply-chain-evidence byte-parity.

The committed
``examples/temporal/supply_chain_security/evidence/supply-chain-evidence.json``
is the Temporal activity adapter's output for the context pinned in
the example's ``regenerate.py``. This module re-drives the activity
from that context and pins the on-disk bytes against the committed
example AND against the immutable fixture under
``tests/fixtures/supply_chain_security/`` — so a refactor of the
F-CP-03 shared emitter, the Temporal activity adapter, or the
F-WF-SCS primitives that silently changes serialisation gets caught
at the byte level.

If the change is intentional, regenerate the example::

    PYTHONPATH=. python examples/temporal/supply_chain_security/regenerate.py

and copy the new bytes into ``tests/fixtures/supply_chain_security/``
alongside the primitive / adapter change.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
from pathlib import Path

from compilers._shared.evidence import SupplyChainContext
from compilers.temporal.evidence import emit_supply_chain_artifact_activity

REPO = Path(__file__).resolve().parents[3]
EXAMPLE = REPO / "examples" / "temporal" / "supply_chain_security"
SNAPSHOT = EXAMPLE / "evidence" / "supply-chain-evidence.json"
REGEN = EXAMPLE / "regenerate.py"
FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "supply_chain_security"
    / "temporal.supply-chain-evidence-record.json"
)


def _load_context() -> SupplyChainContext:
    """Import the example's _build_context helper without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_supply_chain_security_temporal_regen", REGEN
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._build_context()


def test_example_snapshot_is_committed() -> None:
    assert SNAPSHOT.exists(), f"missing example snapshot: {SNAPSHOT}"
    assert SNAPSHOT.stat().st_size > 0


def test_fixture_is_committed() -> None:
    assert FIXTURE.exists(), f"missing byte-parity fixture: {FIXTURE}"
    assert FIXTURE.stat().st_size > 0


def test_example_snapshot_matches_fixture() -> None:
    """The committed worked example and the immutable fixture must agree.

    A drift here means the worked example was regenerated without the
    fixture being refreshed — both must move together.
    """
    assert SNAPSHOT.read_bytes() == FIXTURE.read_bytes(), (
        "examples/temporal/supply_chain_security/evidence/"
        "supply-chain-evidence.json drifted from the immutable "
        "fixture at tests/fixtures/supply_chain_security/"
        "temporal.supply-chain-evidence-record.json. Refresh both "
        "together via "
        "`./examples/temporal/supply_chain_security/regenerate.sh` "
        "and copy the snapshot into the fixture dir."
    )


def test_example_snapshot_matches_temporal_activity(tmp_path: Path) -> None:
    ctx = _load_context()
    written_str = asyncio.run(
        emit_supply_chain_artifact_activity(ctx, tmp_path)
    )
    written = Path(written_str)
    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "examples/temporal/supply_chain_security/evidence/"
        "supply-chain-evidence.json drifted from the Temporal "
        "activity adapter. If intentional, regenerate via "
        "`PYTHONPATH=. python "
        "examples/temporal/supply_chain_security/regenerate.py` "
        "and commit the new bytes."
    )


def test_example_snapshot_carries_expected_anchors() -> None:
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    # F-CP-03 supply-chain-stream shape, schema-version pin.
    assert record["schema_version"] == "1.0.0"
    assert record["stream"] == "supply-chain"
    assert record["workflow_id"] == "supply_chain_security"
    assert record["execution_id"] == "temporal:exec-scs-0001"
    # The id is deterministic on (workflow_id, execution_id, captured_at).
    assert len(record["artifact_id"]) == 64
    # NIS2 Article 21(2)(d) — supply-chain risk management.
    assert "nis2:art-21-2-d" in record["regulation_refs"]
    assert "control.supplier_inventory@v1" in record["control_refs"]
    # Dependencies declared; affected supplier handle joins back.
    assert len(record["dependencies"]) >= 1
    provider_ids = {dep["provider_id"] for dep in record["dependencies"]}
    assert "provider.upstream_dep_eu@v1" in provider_ids
    # Owner is role-shaped per AGENTS.md §3.
    assert "@" in record["owner"]["role"] or (
        record["owner"]["role"].count(" ") == 0
    )


def test_temporal_adapter_artifact_id_is_deterministic(tmp_path: Path) -> None:
    """Same context → same artifact_id → byte-identical re-emission.

    Re-emission inside the same execution is the F-CP-03 contract:
    same ``(workflow_id, execution_id, captured_at)`` triple ⇒ same
    ``artifact_id`` ⇒ identical bytes.
    """
    ctx = _load_context()
    first = Path(
        asyncio.run(emit_supply_chain_artifact_activity(ctx, tmp_path))
    )
    second = Path(
        asyncio.run(emit_supply_chain_artifact_activity(ctx, tmp_path))
    )
    assert first.name == second.name
    assert first.read_bytes() == second.read_bytes()


def test_temporal_and_n8n_snapshots_share_artifact_id_axes() -> None:
    """Cross-target invariant: the n8n and Temporal snapshots agree on
    every per-execution axis the F-CP-03 contract pins together except
    the ``execution_id`` (which is intentionally the per-target run id).

    The cross-target byte-parity ring is closed in the F-WF-SCS EXTEND
    sibling card; this test pins the shape invariants the EXTEND card
    will harden.
    """
    n8n_snapshot = (
        REPO
        / "examples"
        / "n8n"
        / "supply_chain_security"
        / "evidence"
        / "supply-chain-evidence.json"
    )
    n8n_record = json.loads(n8n_snapshot.read_text("utf-8"))
    tmp_record = json.loads(SNAPSHOT.read_text("utf-8"))
    assert n8n_record["schema_version"] == tmp_record["schema_version"]
    assert n8n_record["stream"] == tmp_record["stream"]
    assert n8n_record["workflow_id"] == tmp_record["workflow_id"]
    assert n8n_record["regulation_refs"] == tmp_record["regulation_refs"]
    assert n8n_record["control_refs"] == tmp_record["control_refs"]
    # execution_id differs by design — that is the per-target run id.
    assert n8n_record["execution_id"] != tmp_record["execution_id"]
    # ...therefore artifact_id differs too (it joins on execution_id).
    assert n8n_record["artifact_id"] != tmp_record["artifact_id"]
