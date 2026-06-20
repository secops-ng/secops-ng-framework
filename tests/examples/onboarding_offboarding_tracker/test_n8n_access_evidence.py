"""F-WF-11 CORE-FANOUT-N8N — committed worked-example pins the n8n adapter.

The committed
``examples/n8n/onboarding_offboarding_tracker/evidence/access-evidence.json``
is the n8n adapter's output for the payload pinned in the example's
``regenerate.py``. This test re-drives the adapter from that payload
and pins the on-disk bytes against the committed example AND against
the immutable fixture under
``tests/fixtures/onboarding_offboarding_tracker/`` — so a refactor of
the shared access-evidence emitter or the n8n adapter that silently
changes serialisation gets caught at the byte level.

If the change is intentional, regenerate the example::

    PYTHONPATH=. python examples/n8n/onboarding_offboarding_tracker/regenerate.py

and copy the new bytes into ``tests/fixtures/onboarding_offboarding_tracker/``
alongside the emitter change.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from compilers.n8n.evidence import emit_access_artifact_n8n

REPO = Path(__file__).resolve().parents[3]
EXAMPLE = REPO / "examples" / "n8n" / "onboarding_offboarding_tracker"
SNAPSHOT = EXAMPLE / "evidence" / "access-evidence.json"
REGEN = EXAMPLE / "regenerate.py"
FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "onboarding_offboarding_tracker"
    / "n8n.access-evidence-record.json"
)


def _load_payload() -> dict:
    """Import the example's _build_payload helper without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_onboarding_offboarding_tracker_n8n_regen", REGEN
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
        "examples/n8n/onboarding_offboarding_tracker/evidence/"
        "access-evidence.json drifted from the immutable fixture at "
        "tests/fixtures/onboarding_offboarding_tracker/"
        "n8n.access-evidence-record.json. Refresh both together via "
        "`./examples/n8n/onboarding_offboarding_tracker/regenerate.sh` "
        "and copy the snapshot into the fixture dir."
    )


def test_example_snapshot_matches_n8n_adapter(tmp_path: Path) -> None:
    payload = _load_payload()
    result = emit_access_artifact_n8n(payload, tmp_path)
    written = Path(result["artifact_path"])
    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "examples/n8n/onboarding_offboarding_tracker/evidence/"
        "access-evidence.json drifted from the n8n adapter. If "
        "intentional, regenerate via `PYTHONPATH=. python "
        "examples/n8n/onboarding_offboarding_tracker/regenerate.py` "
        "and commit the new bytes."
    )


def test_example_snapshot_carries_expected_anchors() -> None:
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    assert record["schema_version"] == "1.0.0"
    assert record["stream"] == "access"
    assert record["workflow_id"] == "onboarding_offboarding_tracker"
    assert record["compile_target"] == "n8n"
    # The id is deterministic on the three pinned inputs (see schema).
    assert len(record["artifact_id"]) == 64
    assert "nis2:art-21-2-i" in record["regulation_refs"]
    assert "control.jml_evidence@v1" in record["control_refs"]
    assert "control.privileged_access_review@v1" in record["control_refs"]
    assert (
        "control.cloud_identity_least_privilege@v1" in record["control_refs"]
    )
    # Caller is role-shaped, not a personal name.
    assert record["caller_identity"]["principal_type"] in {
        "service_account",
        "workflow_runtime",
        "automation_role",
    }
    # capabilities is the closed observed list; uniqueness + verb.resource
    # shape are pinned by the schema.
    assert len(record["capabilities"]) >= 1
    assert len(record["capabilities"]) == len(set(record["capabilities"]))
    assert record["capability_count"] == len(record["capabilities"])


def test_n8n_adapter_artifact_id_is_deterministic(tmp_path: Path) -> None:
    """Same payload → same artifact_id → byte-identical re-emission."""
    payload = _load_payload()
    first = emit_access_artifact_n8n(payload, tmp_path)
    second = emit_access_artifact_n8n(payload, tmp_path)
    assert first["artifact_id"] == second["artifact_id"]
    assert (
        Path(first["artifact_path"]).read_bytes()
        == Path(second["artifact_path"]).read_bytes()
    )
