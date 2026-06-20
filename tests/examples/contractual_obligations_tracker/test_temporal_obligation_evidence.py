"""F-WF-10 CORE-FANOUT-TEMPORAL — committed worked example pins the Temporal adapter.

The committed
``examples/temporal/contractual_obligations_tracker/evidence/obligation-evidence-record.json``
is the Temporal activity adapter's output for the payload pinned in
the example's ``regenerate.py``. This test re-drives the activity
from that payload and pins the on-disk bytes against the committed
example AND against the immutable fixture under
``tests/fixtures/contractual_obligations_tracker/`` — so a refactor of
the shared emitter or the Temporal activity adapter that silently
changes serialisation gets caught at the byte level.

Cross-target byte parity with the n8n sibling is pinned here too:
the obligation-evidence artifact is target-agnostic on the wire (the
schema carries no ``compile_target`` field), so the n8n and Temporal
adapters must emit byte-identical records for the same canonical
payload. The committed n8n fixture under
``tests/fixtures/contractual_obligations_tracker/n8n.obligation-evidence-record.json``
is the reference; the Temporal fixture must match it byte-for-byte.

If the change is intentional, regenerate the example::

    PYTHONPATH=. python examples/temporal/contractual_obligations_tracker/regenerate.py

and copy the new bytes into
``tests/fixtures/contractual_obligations_tracker/temporal.obligation-evidence-record.json``
alongside the emitter change.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
from pathlib import Path

from compilers.temporal.evidence import (
    emit_contractual_obligations_artifact_activity,
)

REPO = Path(__file__).resolve().parents[3]
EXAMPLE = REPO / "examples" / "temporal" / "contractual_obligations_tracker"
SNAPSHOT = EXAMPLE / "evidence" / "obligation-evidence-record.json"
REGEN = EXAMPLE / "regenerate.py"
FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "contractual_obligations_tracker"
    / "temporal.obligation-evidence-record.json"
)
N8N_FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "contractual_obligations_tracker"
    / "n8n.obligation-evidence-record.json"
)


def _load_ctx():
    """Import the example's CTX constant without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_contractual_obligations_tracker_temporal_regen", REGEN
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CTX


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
        "examples/temporal/contractual_obligations_tracker/evidence/"
        "obligation-evidence-record.json drifted from the immutable "
        "fixture at tests/fixtures/contractual_obligations_tracker/"
        "temporal.obligation-evidence-record.json. Refresh both together "
        "via `./examples/temporal/contractual_obligations_tracker/"
        "regenerate.sh` and copy the snapshot into the fixture dir."
    )


def test_temporal_fixture_matches_n8n_fixture() -> None:
    """Cross-target byte parity invariant.

    The obligation-evidence artifact is target-agnostic on the wire —
    the schema carries no ``compile_target`` field. Every CORE-FANOUT
    target must therefore emit byte-identical records for the same
    canonical payload. Both fixtures here are produced from
    byte-identical payloads driven through the same shared helper at
    ``compilers._shared.evidence.contractual_obligations``.
    """
    assert FIXTURE.read_bytes() == N8N_FIXTURE.read_bytes(), (
        "Temporal and n8n contractual-obligations fixtures drifted — "
        "the target-agnostic CORE invariant says they must be "
        "byte-identical for the canonical worked-example payload. "
        "Refresh both together via the per-target regenerate scripts."
    )


def test_example_snapshot_matches_temporal_activity(tmp_path: Path) -> None:
    ctx = _load_ctx()
    written_str = asyncio.run(
        emit_contractual_obligations_artifact_activity(ctx, tmp_path)
    )
    written = Path(written_str)
    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "examples/temporal/contractual_obligations_tracker/evidence/"
        "obligation-evidence-record.json drifted from the Temporal "
        "activity adapter. If intentional, regenerate via "
        "`PYTHONPATH=. python examples/temporal/contractual_obligations_tracker/"
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


def test_temporal_adapter_artifact_id_is_deterministic(tmp_path: Path) -> None:
    """Same context → same artifact_id → byte-identical re-emission."""
    ctx = _load_ctx()
    first = Path(
        asyncio.run(
            emit_contractual_obligations_artifact_activity(ctx, tmp_path)
        )
    )
    second = Path(
        asyncio.run(
            emit_contractual_obligations_artifact_activity(ctx, tmp_path)
        )
    )
    assert first.name == second.name
    assert first.read_bytes() == second.read_bytes()
