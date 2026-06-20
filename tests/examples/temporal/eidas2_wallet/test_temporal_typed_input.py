"""F-SV-02 CORE-FANOUT-TEMPORAL — typed-input byte-parity golden.

The committed
``examples/temporal/eidas2_wallet/typed_input/wallet-attestation-input.json``
is the Temporal activity's output for the payload pinned in the
example's ``regenerate.py``. This module re-drives the activity from
that payload and pins the on-disk bytes against the committed example,
against the immutable Temporal-side fixture under
``tests/fixtures/eidas2_wallet/temporal.wallet-attestation-input.json``,
AND against the n8n sibling's immutable fixture — so a refactor of
the canonical F-SV-02 typed-input model, the Temporal activity, or
the n8n adapter that silently changes serialisation or breaks
cross-target parity gets caught at the byte level.

The cross-target parity check is the F-SV-02 CORE invariant: same
canonical payload ⇒ same ``input_id`` ⇒ byte-identical materialised
bundle across compile targets. If this test ever fails, one of the
two adapters drifted from the canonical serialisation convention
(``indent=2``, ``sort_keys=True``, trailing newline) the F-CP-02 /
F-CP-07 / F-WF-12 emitters share.

If the change is intentional, regenerate both worked examples and
fixtures in the same PR::

    ./examples/n8n/eidas2_wallet/regenerate.sh
    ./examples/temporal/eidas2_wallet/regenerate.sh

then copy the new bytes into ``tests/fixtures/eidas2_wallet/`` for
both target files.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
from pathlib import Path

from compilers.temporal.patterns import (
    materialise_wallet_attestation_input_activity,
)

REPO = Path(__file__).resolve().parents[4]
EXAMPLE = REPO / "examples" / "temporal" / "eidas2_wallet"
SNAPSHOT = EXAMPLE / "typed_input" / "wallet-attestation-input.json"
REGEN = EXAMPLE / "regenerate.py"
FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "eidas2_wallet"
    / "temporal.wallet-attestation-input.json"
)
N8N_FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "eidas2_wallet"
    / "n8n.wallet-attestation-input.json"
)


def _load_payload() -> dict:
    """Import the example's _build_payload helper without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_eidas2_wallet_temporal_regen", REGEN
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
        "examples/temporal/eidas2_wallet/typed_input/"
        "wallet-attestation-input.json drifted from the immutable "
        "fixture at tests/fixtures/eidas2_wallet/"
        "temporal.wallet-attestation-input.json. Refresh both together "
        "via `./examples/temporal/eidas2_wallet/regenerate.sh` and "
        "copy the snapshot into the fixture dir."
    )


def test_example_snapshot_matches_temporal_activity(tmp_path: Path) -> None:
    payload = _load_payload()
    result = asyncio.run(
        materialise_wallet_attestation_input_activity(payload, tmp_path)
    )
    written = Path(result["input_path"])
    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "examples/temporal/eidas2_wallet/typed_input/"
        "wallet-attestation-input.json drifted from the Temporal "
        "activity. If intentional, regenerate via "
        "`PYTHONPATH=. python examples/temporal/eidas2_wallet/regenerate.py` "
        "and commit the new bytes."
    )


def test_cross_target_byte_parity_with_n8n_fixture() -> None:
    """F-SV-02 CORE invariant: n8n + Temporal write byte-identical bundles.

    The two compile targets must derive byte-identical canonical
    bytes for the same payload. The worked-example payloads at
    ``examples/n8n/eidas2_wallet/regenerate.py`` and
    ``examples/temporal/eidas2_wallet/regenerate.py`` are pinned
    identical, and the fixture comparison here pins that the resulting
    on-disk bytes are identical too.
    """
    assert FIXTURE.read_bytes() == N8N_FIXTURE.read_bytes(), (
        "F-SV-02 cross-target byte-parity broke: the Temporal fixture "
        "and the n8n fixture diverged. One of the two adapters drifted "
        "from the canonical serialisation convention (indent=2, "
        "sort_keys=True, trailing newline). Re-run both regenerate "
        "scripts and refresh both fixtures together."
    )


def test_activity_output_shape() -> None:
    """Activity must return the {input_id, input_path} contract."""
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    # Canonical record carries the surface fields the typed model
    # asserts — re-checked at the bytes layer.
    assert record["schema_version"] == "1.0.0"
    assert record["attestation_format"] == "sd_jwt_vc"
    assert record["qualified"] is True
    assert record["issuer"]["issuer_class"] == "qeaa_issuer"
    assert record["status"]["outcome"] == "valid"


def test_activity_is_deterministic(tmp_path: Path) -> None:
    payload = _load_payload()
    first = asyncio.run(
        materialise_wallet_attestation_input_activity(payload, tmp_path)
    )
    second_dir = tmp_path / "second"
    second = asyncio.run(
        materialise_wallet_attestation_input_activity(payload, second_dir)
    )
    assert first["input_id"] == second["input_id"]
    assert Path(first["input_path"]).read_bytes() == (
        Path(second["input_path"]).read_bytes()
    )
