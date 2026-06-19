"""F-WF-07 CORE-N8N — committed worked-example pins the n8n adapter.

The committed
``examples/n8n/codebase_vuln_management/evidence/disclosure-timeline-record.json``
is the n8n adapter's output for the payload pinned in the example's
``regenerate.py``. This test re-drives the adapter from that payload
and pins the on-disk bytes against the committed example — so a
refactor of the shared emitter or the n8n adapter that silently
changes serialisation gets caught at the byte level.

If the change is intentional, regenerate the example::

    PYTHONPATH=. python examples/n8n/codebase_vuln_management/regenerate.py

and commit the updated bytes alongside the emitter change.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from compilers.n8n.evidence import emit_disclosure_timeline_artifact_n8n

REPO = Path(__file__).resolve().parents[3]
EXAMPLE = REPO / "examples" / "n8n" / "codebase_vuln_management"
SNAPSHOT = EXAMPLE / "evidence" / "disclosure-timeline-record.json"
REGEN = EXAMPLE / "regenerate.py"


def _load_payload() -> dict:
    """Import the example's PAYLOAD constant without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_codebase_vuln_management_regen", REGEN
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
    result = emit_disclosure_timeline_artifact_n8n(payload, tmp_path)
    written = Path(result["artifact_path"])
    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "examples/n8n/codebase_vuln_management/evidence/"
        "disclosure-timeline-record.json drifted from the n8n adapter. "
        "If intentional, regenerate via "
        "`PYTHONPATH=. python examples/n8n/codebase_vuln_management/"
        "regenerate.py` and commit the new bytes."
    )


def test_example_snapshot_carries_expected_anchors() -> None:
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    assert record["schema_version"] == "0.1.0"
    assert record["stream"] == "codebase_vuln_management"
    assert record["workflow_id"] == "codebase_vuln_management"
    # The id is deterministic on the four pinned inputs (see schema).
    assert len(record["id"]) == 64
    assert record["severity"] in {"critical", "high", "medium", "low"}
    assert record["source_data"]["kind"] in {"ocsf", "telemetry", "none"}
