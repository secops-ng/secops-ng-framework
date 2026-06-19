"""F-WF-07 CORE-LANGGRAPH — committed worked-example pins the LangGraph adapter.

The committed
``examples/langgraph/codebase_vuln_management/evidence/disclosure-timeline-record.json``
is the LangGraph node adapter's output for the context pinned in the
example's ``regenerate.py``. This test re-drives the adapter exactly as
a LangGraph integrator would (state mapping in, partial-state update
out) and pins the on-disk bytes against the committed example — so a
refactor of the shared emitter or the LangGraph adapter that silently
changes serialisation gets caught at the byte level.

A full schema-validating byte-parity golden lives in the F-WF-07
EXTEND-goldens sibling once it ships; this smoke test pins the bare
adapter-replay invariant the CORE-LANGGRAPH deliverable promises, plus
the cross-target byte-parity floor against the n8n and Temporal
siblings.

If the change is intentional, regenerate the example::

    PYTHONPATH=. python examples/langgraph/codebase_vuln_management/regenerate.py

and commit the updated bytes alongside the emitter change.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from compilers.langgraph.evidence import emit_disclosure_timeline_artifact_node

REPO = Path(__file__).resolve().parents[3]
EXAMPLE = REPO / "examples" / "langgraph" / "codebase_vuln_management"
SNAPSHOT = EXAMPLE / "evidence" / "disclosure-timeline-record.json"
REGEN = EXAMPLE / "regenerate.py"


def _load_ctx():
    """Import the example's CTX constant without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_codebase_vuln_management_langgraph_regen", REGEN
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CTX


def test_example_snapshot_is_committed() -> None:
    assert SNAPSHOT.exists(), f"missing example snapshot: {SNAPSHOT}"
    assert SNAPSHOT.stat().st_size > 0


def test_example_snapshot_matches_langgraph_adapter(tmp_path: Path) -> None:
    ctx = _load_ctx()
    update = emit_disclosure_timeline_artifact_node(
        {
            "disclosure_timeline_context": ctx,
            "evidence_output_dir": tmp_path,
        }
    )
    written = Path(update["disclosure_timeline_artifact_path"])
    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "examples/langgraph/codebase_vuln_management/evidence/"
        "disclosure-timeline-record.json drifted from the LangGraph "
        "adapter. If intentional, regenerate via "
        "`PYTHONPATH=. python examples/langgraph/codebase_vuln_management/"
        "regenerate.py` and commit the new bytes."
    )
    # The partial state update carries the deterministic id; the
    # integrator joins this back into the running graph state.
    assert update["disclosure_timeline_artifact_id"] == written.stem


def test_example_snapshot_carries_expected_anchors() -> None:
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    assert record["schema_version"] == "0.1.0"
    assert record["stream"] == "codebase_vuln_management"
    assert record["workflow_id"] == "codebase_vuln_management"
    # The id is deterministic on the four pinned inputs (see schema).
    assert len(record["id"]) == 64
    assert record["severity"] in {"critical", "high", "medium", "low"}
    assert record["source_data"]["kind"] in {"ocsf", "telemetry", "none"}


def test_langgraph_replay_matches_committed_n8n_sibling() -> None:
    """Cross-target byte-parity: LangGraph output must match the n8n
    sibling byte-for-byte. The shared emitter is the source of truth;
    the per-target adapters are thin glue, so any drift here is a bug
    in one of the adapters. The full cross-target golden ships in the
    F-WF-07 EXTEND-goldens sibling.
    """
    n8n_snapshot = (
        REPO
        / "examples"
        / "n8n"
        / "codebase_vuln_management"
        / "evidence"
        / "disclosure-timeline-record.json"
    )
    assert n8n_snapshot.read_bytes() == SNAPSHOT.read_bytes()


def test_langgraph_replay_matches_committed_temporal_sibling() -> None:
    """Cross-target byte-parity: LangGraph output must match the
    Temporal sibling byte-for-byte. Same source-of-truth invariant as
    the n8n cross-target test; CORE-LANGGRAPH lands as the third leg
    of the three-target parity floor.
    """
    temporal_snapshot = (
        REPO
        / "examples"
        / "temporal"
        / "codebase_vuln_management"
        / "evidence"
        / "disclosure-timeline-record.json"
    )
    assert temporal_snapshot.read_bytes() == SNAPSHOT.read_bytes()
