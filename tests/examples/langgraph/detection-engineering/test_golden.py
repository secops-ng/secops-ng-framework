"""F-WF-04 CORE-LANGGRAPH — committed worked-example pins the LangGraph node adapter.

The committed
``examples/langgraph/detection-engineering/evidence/rule-effectiveness-snapshot.json``
is the LangGraph node adapter's output for the context pinned in the
example's ``regenerate.py``. This test re-drives the adapter exactly
as a LangGraph integrator would (typed
:class:`RuleEffectivenessContext` placed on a state mapping with the
output directory; node returns a partial state update carrying the
absolute artifact path) and pins the on-disk bytes against the
committed example — so a refactor of the shared emitter or the
LangGraph node adapter that silently changes serialisation gets caught
at the byte level.

The cross-target byte-parity assertion below pins the LangGraph output
against the n8n and Temporal siblings byte-for-byte: the shared
emitter is the source of truth and the per-target adapters are thin
glue, so any drift between the three is a bug in one of the adapters.
The full schema-validating cross-target golden lives in the F-WF-04
EXTEND-goldens sibling once it ships.

If the change is intentional, regenerate the example::

    PYTHONPATH=. python examples/langgraph/detection-engineering/regenerate.py

and commit the updated bytes alongside the emitter change.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from compilers.langgraph.evidence import emit_rule_effectiveness_snapshot_node

REPO = Path(__file__).resolve().parents[4]
EXAMPLE = REPO / "examples" / "langgraph" / "detection-engineering"
SNAPSHOT = EXAMPLE / "evidence" / "rule-effectiveness-snapshot.json"
REGEN = EXAMPLE / "regenerate.py"


def _load_ctx():
    """Import the example's CTX constant without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_detection_engineering_langgraph_regen", REGEN
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
    update = emit_rule_effectiveness_snapshot_node(
        {
            "rule_effectiveness_context": ctx,
            "evidence_output_dir": tmp_path,
        }
    )
    written = Path(update["rule_effectiveness_artifact_path"])
    assert written.read_bytes() == SNAPSHOT.read_bytes(), (
        "examples/langgraph/detection-engineering/evidence/"
        "rule-effectiveness-snapshot.json drifted from the LangGraph "
        "adapter. If intentional, regenerate via "
        "`PYTHONPATH=. python examples/langgraph/detection-engineering/"
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


def test_langgraph_replay_matches_committed_n8n_sibling() -> None:
    """Cross-target byte-parity: LangGraph output must match the n8n
    sibling byte-for-byte. The shared emitter is the source of truth;
    the per-target adapters are thin glue, so any drift here is a bug
    in one of the adapters. The full cross-target golden ships in the
    F-WF-04 EXTEND-goldens sibling.
    """
    n8n_snapshot = (
        REPO
        / "examples"
        / "n8n"
        / "detection-engineering"
        / "evidence"
        / "rule-effectiveness-snapshot.json"
    )
    assert n8n_snapshot.read_bytes() == SNAPSHOT.read_bytes()


def test_langgraph_replay_matches_committed_temporal_sibling() -> None:
    """Cross-target byte-parity: LangGraph output must match the
    Temporal sibling byte-for-byte. Same rationale as the n8n cross-
    target check above.
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


def test_artifact_path_matches_snapshot_id_in_record(tmp_path: Path) -> None:
    ctx = _load_ctx()
    update = emit_rule_effectiveness_snapshot_node(
        {
            "rule_effectiveness_context": ctx,
            "evidence_output_dir": tmp_path,
        }
    )
    written = Path(update["rule_effectiveness_artifact_path"])
    record = json.loads(written.read_text("utf-8"))
    # Adapter contract: written path stem == record snapshot_id ==
    # update["rule_effectiveness_artifact_id"].
    assert written.stem == record["snapshot_id"]
    assert update["rule_effectiveness_artifact_id"] == record["snapshot_id"]
