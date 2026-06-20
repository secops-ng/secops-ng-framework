"""F-WF-10 CORE-FANOUT-LANGGRAPH — committed worked example pins the LangGraph adapter.

The committed
``examples/langgraph/contractual_obligations_tracker/evidence/obligation-evidence-record.json``
is the LangGraph node adapter's output for the context pinned in the
example's ``regenerate.py``. This test re-drives the adapter exactly
as a LangGraph integrator would (state mapping in, partial-state
update out) and pins the on-disk bytes against the committed example
AND against the immutable fixture under
``tests/fixtures/contractual_obligations_tracker/`` — so a refactor of
the shared emitter or the LangGraph adapter that silently changes
serialisation gets caught at the byte level.

Cross-target byte parity with the n8n + Temporal siblings is pinned
here too: the obligation-evidence artifact is target-agnostic on the
wire (the schema carries no ``compile_target`` field), so the n8n,
Temporal, and LangGraph adapters must emit byte-identical records for
the same canonical payload. The committed n8n fixture under
``tests/fixtures/contractual_obligations_tracker/n8n.obligation-evidence-record.json``
is the reference; the LangGraph fixture must match it byte-for-byte.

If the change is intentional, regenerate the example::

    PYTHONPATH=. python examples/langgraph/contractual_obligations_tracker/regenerate.py

and copy the new bytes into
``tests/fixtures/contractual_obligations_tracker/langgraph.obligation-evidence-record.json``
alongside the emitter change.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from compilers.langgraph.evidence import (
    emit_contractual_obligations_artifact_node,
)

REPO = Path(__file__).resolve().parents[3]
EXAMPLE = REPO / "examples" / "langgraph" / "contractual_obligations_tracker"
SNAPSHOT = EXAMPLE / "evidence" / "obligation-evidence-record.json"
REGEN = EXAMPLE / "regenerate.py"
FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "contractual_obligations_tracker"
    / "langgraph.obligation-evidence-record.json"
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
        "_contractual_obligations_tracker_langgraph_regen", REGEN
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
        "examples/langgraph/contractual_obligations_tracker/evidence/"
        "obligation-evidence-record.json drifted from the immutable "
        "fixture at tests/fixtures/contractual_obligations_tracker/"
        "langgraph.obligation-evidence-record.json. Refresh both together "
        "via `PYTHONPATH=. python examples/langgraph/"
        "contractual_obligations_tracker/regenerate.py` and copy the "
        "snapshot into the fixture dir."
    )


def test_langgraph_fixture_matches_n8n_fixture() -> None:
    """Cross-target byte parity invariant.

    The obligation-evidence artifact is target-agnostic on the wire —
    the schema carries no ``compile_target`` field. Every CORE-FANOUT
    target must therefore emit byte-identical records for the same
    canonical payload. All three fixtures here (n8n, Temporal,
    LangGraph) are produced from byte-identical payloads driven
    through the same shared helper at
    ``compilers._shared.evidence.contractual_obligations``.
    """
    assert FIXTURE.read_bytes() == N8N_FIXTURE.read_bytes(), (
        "LangGraph and n8n contractual-obligations fixtures drifted — "
        "the target-agnostic CORE invariant says they must be "
        "byte-identical for the canonical worked-example payload. "
        "Refresh both together via the per-target regenerate scripts."
    )


def test_example_snapshot_matches_langgraph_adapter(tmp_path: Path) -> None:
    ctx = _load_ctx()
    update = emit_contractual_obligations_artifact_node(
        {
            "contractual_obligations_context": ctx,
            "evidence_output_dir": tmp_path,
        }
    )
    written = Path(update["contractual_obligations_artifact_path"])
    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "examples/langgraph/contractual_obligations_tracker/evidence/"
        "obligation-evidence-record.json drifted from the LangGraph "
        "node adapter. If intentional, regenerate via "
        "`PYTHONPATH=. python examples/langgraph/"
        "contractual_obligations_tracker/regenerate.py` and commit the "
        "new bytes."
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


def test_langgraph_adapter_artifact_id_is_deterministic(tmp_path: Path) -> None:
    """Same context → same artifact_id → byte-identical re-emission."""
    ctx = _load_ctx()
    first_update = emit_contractual_obligations_artifact_node(
        {
            "contractual_obligations_context": ctx,
            "evidence_output_dir": tmp_path,
        }
    )
    second_update = emit_contractual_obligations_artifact_node(
        {
            "contractual_obligations_context": ctx,
            "evidence_output_dir": tmp_path,
        }
    )
    assert (
        first_update["contractual_obligations_artifact_id"]
        == second_update["contractual_obligations_artifact_id"]
    )
    assert (
        Path(first_update["contractual_obligations_artifact_path"]).read_bytes()
        == Path(second_update["contractual_obligations_artifact_path"]).read_bytes()
    )
