"""F-SV-02 CORE-FANOUT-LANGGRAPH — typed-input byte-parity golden.

The committed
``examples/langgraph/eidas2_wallet/typed_input/wallet-attestation-input.json``
is the LangGraph node's output for the payload pinned in the example's
``regenerate.py``. This module re-drives the node from that payload
and pins the on-disk bytes against the committed example, against the
immutable LangGraph-side fixture under
``tests/fixtures/eidas2_wallet/langgraph.wallet-attestation-input.json``,
AND against the n8n + Temporal sibling fixtures — so a refactor of
the canonical F-SV-02 typed-input model, the LangGraph node, the n8n
adapter, or the Temporal activity that silently changes serialisation
or breaks cross-target parity gets caught at the byte level.

The cross-target parity check is the F-SV-02 CORE invariant: same
canonical payload ⇒ same ``input_id`` ⇒ byte-identical materialised
bundle across the three compile targets. If this test ever fails, one
of the three adapters drifted from the canonical serialisation
convention (``indent=2``, ``sort_keys=True``, trailing newline) the
F-CP-02 / F-CP-07 / F-WF-12 emitters share.

If the change is intentional, regenerate all three worked examples
and fixtures in the same PR::

    ./examples/n8n/eidas2_wallet/regenerate.sh
    ./examples/temporal/eidas2_wallet/regenerate.sh
    ./examples/langgraph/eidas2_wallet/regenerate.sh

then copy the new bytes into ``tests/fixtures/eidas2_wallet/`` for
all three target files.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from compilers.langgraph.patterns import (
    materialise_wallet_attestation_input_node,
)

REPO = Path(__file__).resolve().parents[4]
EXAMPLE = REPO / "examples" / "langgraph" / "eidas2_wallet"
SNAPSHOT = EXAMPLE / "typed_input" / "wallet-attestation-input.json"
REGEN = EXAMPLE / "regenerate.py"
FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "eidas2_wallet"
    / "langgraph.wallet-attestation-input.json"
)
N8N_FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "eidas2_wallet"
    / "n8n.wallet-attestation-input.json"
)
TEMPORAL_FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "eidas2_wallet"
    / "temporal.wallet-attestation-input.json"
)


def _load_payload() -> dict:
    """Import the example's _build_payload helper without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_eidas2_wallet_langgraph_regen", REGEN
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
        "examples/langgraph/eidas2_wallet/typed_input/"
        "wallet-attestation-input.json drifted from the immutable "
        "fixture at tests/fixtures/eidas2_wallet/"
        "langgraph.wallet-attestation-input.json. Refresh both together "
        "via `./examples/langgraph/eidas2_wallet/regenerate.sh` and "
        "copy the snapshot into the fixture dir."
    )


def test_example_snapshot_matches_langgraph_node(tmp_path: Path) -> None:
    payload = _load_payload()
    state = {
        "wallet_attestation_payload": payload,
        "wallet_input_output_dir": tmp_path,
    }
    update = materialise_wallet_attestation_input_node(state)
    written = Path(update["wallet_input_path"])
    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "examples/langgraph/eidas2_wallet/typed_input/"
        "wallet-attestation-input.json drifted from the LangGraph "
        "node. If intentional, regenerate via "
        "`PYTHONPATH=. python examples/langgraph/eidas2_wallet/regenerate.py` "
        "and commit the new bytes."
    )


def test_cross_target_byte_parity_with_n8n_fixture() -> None:
    """F-SV-02 CORE invariant: LangGraph + n8n write byte-identical bundles.

    Pins one leg of the three-target byte-parity invariant. The n8n
    fixture is the immutable anchor; the LangGraph fixture must match
    it byte-for-byte for the same canonical payload.
    """
    assert FIXTURE.read_bytes() == N8N_FIXTURE.read_bytes(), (
        "F-SV-02 cross-target byte-parity broke: the LangGraph "
        "fixture and the n8n fixture diverged. One of the adapters "
        "drifted from the canonical serialisation convention "
        "(indent=2, sort_keys=True, trailing newline). Re-run all "
        "three regenerate scripts and refresh all three fixtures "
        "together."
    )


def test_cross_target_byte_parity_with_temporal_fixture() -> None:
    """F-SV-02 CORE invariant: LangGraph + Temporal write byte-identical bundles.

    Pins the other leg of the three-target byte-parity invariant.
    With both legs pinned, the n8n + Temporal + LangGraph three-way
    parity holds by transitivity.
    """
    assert FIXTURE.read_bytes() == TEMPORAL_FIXTURE.read_bytes(), (
        "F-SV-02 cross-target byte-parity broke: the LangGraph "
        "fixture and the Temporal fixture diverged. One of the "
        "adapters drifted from the canonical serialisation "
        "convention (indent=2, sort_keys=True, trailing newline). "
        "Re-run all three regenerate scripts and refresh all three "
        "fixtures together."
    )


def test_node_output_shape() -> None:
    """Node must produce the canonical typed-input record shape."""
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    # Canonical record carries the surface fields the typed model
    # asserts — re-checked at the bytes layer.
    assert record["schema_version"] == "1.0.0"
    assert record["attestation_format"] == "sd_jwt_vc"
    assert record["qualified"] is True
    assert record["issuer"]["issuer_class"] == "qeaa_issuer"
    assert record["status"]["outcome"] == "valid"


def test_node_partial_state_update_contract(tmp_path: Path) -> None:
    """Node returns the {wallet_input_id, wallet_input_path} partial update."""
    payload = _load_payload()
    state = {
        "wallet_attestation_payload": payload,
        "wallet_input_output_dir": tmp_path,
    }
    update = materialise_wallet_attestation_input_node(state)
    assert set(update.keys()) == {
        "wallet_input_id",
        "wallet_input_path",
    }
    assert len(update["wallet_input_id"]) == 64
    assert Path(update["wallet_input_path"]).is_absolute()
    assert Path(update["wallet_input_path"]).exists()


def test_node_is_deterministic(tmp_path: Path) -> None:
    payload = _load_payload()
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first = materialise_wallet_attestation_input_node(
        {
            "wallet_attestation_payload": payload,
            "wallet_input_output_dir": first_dir,
        }
    )
    second = materialise_wallet_attestation_input_node(
        {
            "wallet_attestation_payload": payload,
            "wallet_input_output_dir": second_dir,
        }
    )
    assert first["wallet_input_id"] == second["wallet_input_id"]
    assert Path(first["wallet_input_path"]).read_bytes() == (
        Path(second["wallet_input_path"]).read_bytes()
    )


def test_node_missing_state_keys_raises_keyerror(tmp_path: Path) -> None:
    """Integrator typos in state keys surface as KeyError, not opaque failure."""
    import pytest

    with pytest.raises(KeyError):
        materialise_wallet_attestation_input_node(
            {"wallet_input_output_dir": tmp_path}
        )
    with pytest.raises(KeyError):
        materialise_wallet_attestation_input_node(
            {"wallet_attestation_payload": _load_payload()}
        )
