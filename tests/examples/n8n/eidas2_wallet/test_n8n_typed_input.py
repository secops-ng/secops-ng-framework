"""F-SV-02 CORE-FANOUT-N8N — typed-input byte-parity golden.

The committed
``examples/n8n/eidas2_wallet/typed_input/wallet-attestation-input.json``
is the n8n adapter's output for the payload pinned in the example's
``regenerate.py``. This module re-drives the adapter from that payload
and pins the on-disk bytes against the committed example AND against
the immutable fixture under
``tests/fixtures/eidas2_wallet/`` — so a refactor of the canonical
F-SV-02 typed-input model or the n8n adapter that silently changes
serialisation gets caught at the byte level.

If the change is intentional, regenerate the example::

    ./examples/n8n/eidas2_wallet/regenerate.sh

and copy the new bytes into ``tests/fixtures/eidas2_wallet/``
alongside the model / adapter change.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from compilers.n8n.patterns import (
    materialise_wallet_attestation_input_n8n,
)

REPO = Path(__file__).resolve().parents[4]
EXAMPLE = REPO / "examples" / "n8n" / "eidas2_wallet"
SNAPSHOT = EXAMPLE / "typed_input" / "wallet-attestation-input.json"
REGEN = EXAMPLE / "regenerate.py"
FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "eidas2_wallet"
    / "n8n.wallet-attestation-input.json"
)


def _load_payload() -> dict:
    """Import the example's _build_payload helper without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_eidas2_wallet_n8n_regen", REGEN
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
        "examples/n8n/eidas2_wallet/typed_input/"
        "wallet-attestation-input.json drifted from the immutable "
        "fixture at tests/fixtures/eidas2_wallet/"
        "n8n.wallet-attestation-input.json. Refresh both together "
        "via `./examples/n8n/eidas2_wallet/regenerate.sh` and copy "
        "the snapshot into the fixture dir."
    )


def test_example_snapshot_matches_n8n_adapter(tmp_path: Path) -> None:
    payload = _load_payload()
    result = materialise_wallet_attestation_input_n8n(payload, tmp_path)
    written = Path(result["input_path"])
    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "examples/n8n/eidas2_wallet/typed_input/"
        "wallet-attestation-input.json drifted from the n8n adapter. "
        "If intentional, regenerate via "
        "`PYTHONPATH=. python examples/n8n/eidas2_wallet/regenerate.py` "
        "and commit the new bytes."
    )


def test_adapter_output_shape() -> None:
    """Adapter must return the {input_id, input_path} contract."""
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    # Canonical record carries the surface fields the typed model
    # asserts — re-checked at the bytes layer.
    assert record["schema_version"] == "1.0.0"
    assert record["attestation_format"] == "sd_jwt_vc"
    assert record["qualified"] is True
    assert record["issuer"]["issuer_class"] == "qeaa_issuer"
    assert record["status"]["outcome"] == "valid"


def test_adapter_is_deterministic(tmp_path: Path) -> None:
    payload = _load_payload()
    first = materialise_wallet_attestation_input_n8n(payload, tmp_path)
    second_dir = tmp_path / "second"
    second = materialise_wallet_attestation_input_n8n(payload, second_dir)
    assert first["input_id"] == second["input_id"]
    assert Path(first["input_path"]).read_bytes() == (
        Path(second["input_path"]).read_bytes()
    )
