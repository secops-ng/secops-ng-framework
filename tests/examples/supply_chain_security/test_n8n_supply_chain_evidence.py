"""F-WF-SCS CORE-FANOUT-N8N — supply-chain-evidence byte-parity.

The committed
``examples/n8n/supply_chain_security/evidence/supply-chain-evidence.json``
is the n8n adapter's output for the payload pinned in the example's
``regenerate.py``. This module re-drives the adapter from that payload
and pins the on-disk bytes against the committed example AND against
the immutable fixture under
``tests/fixtures/supply_chain_security/`` — so a refactor of the
F-CP-03 shared emitter, the n8n adapter, or the F-WF-SCS primitives
that silently changes serialisation gets caught at the byte level.

If the change is intentional, regenerate the example::

    PYTHONPATH=. python examples/n8n/supply_chain_security/regenerate.py

and copy the new bytes into ``tests/fixtures/supply_chain_security/``
alongside the primitive / adapter change.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from compilers.n8n.evidence import emit_supply_chain_artifact_n8n

REPO = Path(__file__).resolve().parents[3]
EXAMPLE = REPO / "examples" / "n8n" / "supply_chain_security"
SNAPSHOT = EXAMPLE / "evidence" / "supply-chain-evidence.json"
REGEN = EXAMPLE / "regenerate.py"
FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "supply_chain_security"
    / "n8n.supply-chain-evidence-record.json"
)


def _load_payload() -> dict:
    """Import the example's _build_payload helper without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_supply_chain_security_n8n_regen", REGEN
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._build_payload()


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
        "examples/n8n/supply_chain_security/evidence/"
        "supply-chain-evidence.json drifted from the immutable "
        "fixture at tests/fixtures/supply_chain_security/"
        "n8n.supply-chain-evidence-record.json. Refresh both together "
        "via `./examples/n8n/supply_chain_security/regenerate.sh` and "
        "copy the snapshot into the fixture dir."
    )


def test_example_snapshot_matches_n8n_adapter(tmp_path: Path) -> None:
    payload = _load_payload()
    result = emit_supply_chain_artifact_n8n(payload, tmp_path)
    written = Path(result["artifact_path"])
    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "examples/n8n/supply_chain_security/evidence/"
        "supply-chain-evidence.json drifted from the n8n adapter. "
        "If intentional, regenerate via `PYTHONPATH=. python "
        "examples/n8n/supply_chain_security/regenerate.py` and "
        "commit the new bytes."
    )


def test_example_snapshot_carries_expected_anchors() -> None:
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    # F-CP-03 supply-chain-stream shape, schema-version pin.
    assert record["schema_version"] == "1.0.0"
    assert record["stream"] == "supply-chain"
    assert record["workflow_id"] == "supply_chain_security"
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


def test_n8n_adapter_artifact_id_is_deterministic(tmp_path: Path) -> None:
    """Same payload → same artifact_id → byte-identical re-emission.

    Re-emission inside the same execution is the F-CP-03 contract:
    same ``(workflow_id, execution_id, captured_at)`` triple ⇒ same
    ``artifact_id`` ⇒ identical bytes.
    """
    payload = _load_payload()
    first = emit_supply_chain_artifact_n8n(payload, tmp_path)
    second = emit_supply_chain_artifact_n8n(payload, tmp_path)
    assert first["artifact_id"] == second["artifact_id"]
    assert (
        Path(first["artifact_path"]).read_bytes()
        == Path(second["artifact_path"]).read_bytes()
    )


def test_affected_supplier_handle_is_declared() -> None:
    """SCS-side join: the assessed supplier must be a declared dependency.

    The F-WF-SCS artifact primitive rejects an assessment that
    references a supplier not in the operator's declared dependency
    surface (no silently-orphaned artifacts). Pin the invariant on the
    committed payload too.
    """
    payload = _load_payload()
    declared = {dep["provider_id"] for dep in payload["dependencies"]}
    # The example's RAW_SIGNAL pins this supplier handle.
    assert "provider.upstream_dep_eu@v1" in declared
