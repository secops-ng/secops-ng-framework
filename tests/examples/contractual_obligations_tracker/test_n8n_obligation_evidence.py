"""F-WF-10 CORE-FANOUT-N8N — committed worked-example pins the n8n adapter.

The committed
``examples/n8n/contractual_obligations_tracker/evidence/obligation-evidence-record.json``
is the n8n adapter's output for the payload pinned in the example's
``regenerate.py``. This test re-drives the adapter from that payload
and pins the on-disk bytes against the committed example AND against
the immutable fixture under
``tests/fixtures/contractual_obligations_tracker/`` — so a refactor
of the shared emitter or the n8n adapter that silently changes
serialisation gets caught at the byte level.

If the change is intentional, regenerate the example::

    PYTHONPATH=. python examples/n8n/contractual_obligations_tracker/regenerate.py

and copy the new bytes into ``tests/fixtures/contractual_obligations_tracker/``
alongside the emitter change.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from compilers.n8n.evidence import emit_contractual_obligations_artifact_n8n

REPO = Path(__file__).resolve().parents[3]
EXAMPLE = REPO / "examples" / "n8n" / "contractual_obligations_tracker"
SNAPSHOT = EXAMPLE / "evidence" / "obligation-evidence-record.json"
REGEN = EXAMPLE / "regenerate.py"
FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "contractual_obligations_tracker"
    / "n8n.obligation-evidence-record.json"
)


def _load_payload() -> dict:
    """Import the example's PAYLOAD constant without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_contractual_obligations_tracker_n8n_regen", REGEN
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.PAYLOAD


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
        "examples/n8n/contractual_obligations_tracker/evidence/"
        "obligation-evidence-record.json drifted from the immutable "
        "fixture at tests/fixtures/contractual_obligations_tracker/"
        "n8n.obligation-evidence-record.json. Refresh both together via "
        "`./examples/n8n/contractual_obligations_tracker/regenerate.sh` "
        "and copy the snapshot into the fixture dir."
    )


def test_example_snapshot_matches_n8n_adapter(tmp_path: Path) -> None:
    payload = _load_payload()
    result = emit_contractual_obligations_artifact_n8n(payload, tmp_path)
    written = Path(result["artifact_path"])
    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "examples/n8n/contractual_obligations_tracker/evidence/"
        "obligation-evidence-record.json drifted from the n8n adapter. "
        "If intentional, regenerate via "
        "`PYTHONPATH=. python examples/n8n/contractual_obligations_tracker/"
        "regenerate.py` and commit the new bytes."
    )


def test_example_snapshot_carries_expected_anchors() -> None:
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    assert record["schema_version"] == "0.1.0"
    assert record["stream"] == "contractual-obligations"
    assert record["workflow_id"] == "contractual_obligations_tracker"
    # The id is deterministic on the four pinned inputs (see schema).
    assert len(record["artifact_id"]) == 64
    assert "nis2:art-21-2-d" in record["regulation_refs"]
    assert "control.supplier_inventory@v1" in record["control_refs"]
    assert "control.provider_attestation@v1" in record["control_refs"]
    assert record["contract"]["contract_id"].startswith("contract.")
    assert record["contract"]["supplier_ref"].startswith("provider.")
    assert len(record["obligations"]) >= 1
    assert len(record["obligations"]) == len(record["review_schedule"])
    # One-to-one ordering invariant pinned by the schema.
    for obl, rev in zip(record["obligations"], record["review_schedule"]):
        assert obl["obligation_id"] == rev["obligation_id"]
    # Owner is role-shaped, not a personal name.
    assert "@" in record["owner"]["role"] or record["owner"]["role"].count(" ") == 0


def test_n8n_adapter_artifact_id_is_deterministic(tmp_path: Path) -> None:
    """Same payload → same artifact_id → byte-identical re-emission."""
    payload = _load_payload()
    first = emit_contractual_obligations_artifact_n8n(payload, tmp_path)
    second = emit_contractual_obligations_artifact_n8n(payload, tmp_path)
    assert first["artifact_id"] == second["artifact_id"]
    assert (
        Path(first["artifact_path"]).read_bytes()
        == Path(second["artifact_path"]).read_bytes()
    )
