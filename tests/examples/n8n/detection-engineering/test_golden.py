"""F-WF-04 EXTEND-goldens — committed worked-example pins the n8n adapter.

The committed
``examples/n8n/detection-engineering/evidence/rule-effectiveness-snapshot.json``
is the n8n adapter's output for the payload pinned in the example's
``regenerate.py``, renamed from the deterministic ``<snapshot_id>.json``
the adapter writes to a stable human-friendly filename for diffing.
This test re-drives the adapter exactly as an n8n ``executeCommand`` /
``Code`` node would (JSON-native payload in, ``{artifact_id,
artifact_path}`` out) and pins the on-disk bytes against the committed
example — so a refactor of the shared emitter or the n8n adapter that
silently changes serialisation gets caught at the byte level.

The cross-target byte-parity assertions below pin the n8n output
against the Temporal and LangGraph siblings byte-for-byte: the shared
emitter is the source of truth and the per-target adapters are thin
glue, so any drift between the three is a bug in one of the adapters.

If the change is intentional, regenerate the example::

    PYTHONPATH=. python examples/n8n/detection-engineering/regenerate.py

and commit the updated bytes alongside the emitter change.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from compilers.n8n.evidence import emit_rule_effectiveness_snapshot_n8n

REPO = Path(__file__).resolve().parents[4]
EXAMPLE = REPO / "examples" / "n8n" / "detection-engineering"
SNAPSHOT = EXAMPLE / "evidence" / "rule-effectiveness-snapshot.json"
REGEN = EXAMPLE / "regenerate.py"


def _load_payload() -> dict:
    """Import the example's PAYLOAD constant without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_detection_engineering_n8n_regen", REGEN
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
    result = emit_rule_effectiveness_snapshot_n8n(payload, tmp_path)
    written = Path(result["artifact_path"])
    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "examples/n8n/detection-engineering/evidence/"
        "rule-effectiveness-snapshot.json drifted from the n8n "
        "adapter. If intentional, regenerate via "
        "`PYTHONPATH=. python examples/n8n/detection-engineering/"
        "regenerate.py` and commit the new bytes."
    )


def test_example_snapshot_carries_expected_anchors() -> None:
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    assert record["schema_version"] == "0.1.0-skeleton"
    assert record["rule_id"] == "rule.suspicious_oauth_grant"
    assert record["rule_version"] == "1.0.0"
    # snapshot_id is SHA-256(rule_id|rule_version|captured_at|metric.stable_id)
    assert len(record["snapshot_id"]) == 64
    assert record["metric"]["stable_id"] == "kpi.false_positive_rate@v1"
    assert record["source_data"]["ocsf_class_uid"] == 2001
    assert record["ref_viz"]["kind"] in {"line", "bar", "gauge", "table"}


def test_n8n_replay_matches_committed_temporal_sibling() -> None:
    """Cross-target byte-parity: n8n output must match the Temporal
    sibling byte-for-byte. The shared emitter is the source of truth;
    the per-target adapters are thin glue, so any drift here is a bug
    in one of the adapters.
    """
    temporal_snapshot = (
        REPO
        / "examples"
        / "temporal"
        / "detection-engineering"
        / "evidence"
        / "rule-effectiveness-snapshot.json"
    )
    assert temporal_snapshot.read_bytes() == SNAPSHOT.read_bytes()


def test_n8n_replay_matches_committed_langgraph_sibling() -> None:
    """Cross-target byte-parity: n8n output must match the LangGraph
    sibling byte-for-byte. Same rationale as the Temporal cross-target
    check above.
    """
    langgraph_snapshot = (
        REPO
        / "examples"
        / "langgraph"
        / "detection-engineering"
        / "evidence"
        / "rule-effectiveness-snapshot.json"
    )
    assert langgraph_snapshot.read_bytes() == SNAPSHOT.read_bytes()


def test_artifact_id_matches_path_stem(tmp_path: Path) -> None:
    payload = _load_payload()
    result = emit_rule_effectiveness_snapshot_n8n(payload, tmp_path)
    written = Path(result["artifact_path"])
    record = json.loads(written.read_text("utf-8"))
    # Adapter contract: written path stem == record snapshot_id ==
    # result["artifact_id"].
    assert written.stem == record["snapshot_id"]
    assert result["artifact_id"] == record["snapshot_id"]
