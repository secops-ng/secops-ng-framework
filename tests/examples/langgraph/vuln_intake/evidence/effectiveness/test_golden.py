"""F-CP-06 EXTEND-tests-goldens (LangGraph) — byte-parity replay golden.

Pins the committed effectiveness worked example for the LangGraph
target under ``examples/langgraph/vuln_intake/evidence/effectiveness/``
against a fresh re-emission driven through the LangGraph node adapter
at :func:`compilers.langgraph.evidence.emit_effectiveness_artifact_node`.

The committed snapshot — ``control-effectiveness-snapshot.json`` — is
the human-friendly rename of the deterministic ``<artifact_id>.json``
file the shared emitter writes. This test re-runs the node adapter
the way an integrator's ``StateGraph`` would (typed
``EffectivenessContext`` placed on a state mapping with the output
directory, partial state update returned with the artifact path),
schema-validates the result against
``schemas/evidence/effectiveness.schema.json``, and asserts
byte-equality with the committed snapshot.

Coverage axes:

1. **Schema-conformant emit.** The re-emitted artifact validates
   against the effectiveness schema before the byte comparison runs.
2. **Byte-parity with the committed example.** The re-emitted
   artifact's on-disk bytes match the committed
   ``control-effectiveness-snapshot.json`` exactly.
3. **Indicator-anchor + NIS2 Article 21(2)(f) shape.** ``metric_ref``,
   ``subject_version``, the pre-computed indicator value, and the
   regulatory anchor are all carried.

Sibling note: ``CTX`` below is kept byte-identical to ``CTX`` in
``examples/langgraph/vuln_intake/evidence/effectiveness/regenerate.py``.
The filename in that path contains a hyphen, so the regenerate module
cannot be imported by ``import`` — the context is duplicated here on
purpose and the byte-parity assertion catches drift on either side.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

from compilers._shared.evidence import (
    EffectivenessContext,
    Measurement,
    OcsfPointer,
    SourceShape,
    SubjectVersion,
)
from compilers.langgraph.evidence import emit_effectiveness_artifact_node

REPO = Path(__file__).resolve().parents[6]
SCHEMA = REPO / "schemas" / "evidence" / "effectiveness.schema.json"
EXAMPLE_DIR = (
    REPO
    / "examples"
    / "langgraph"
    / "vuln_intake"
    / "evidence"
    / "effectiveness"
)
GOLDEN = EXAMPLE_DIR / "control-effectiveness-snapshot.json"


# Mirrors CTX in
# examples/langgraph/vuln_intake/evidence/effectiveness/regenerate.py.
# Kept byte-identical on purpose; the byte-parity test below catches
# drift on either side.
CTX = EffectivenessContext(
    workflow_id="vulnerability_triage",
    execution_id="langgraph:vuln_intake_effectiveness_example_0001",
    compile_target="langgraph",
    regulation_refs=("nis2:art-21-2-f",),
    control_refs=(
        "control.control_effectiveness_test@v1",
        "control.risk_management_policy@v1",
    ),
    metric_ref="kri.control_effectiveness@v1",
    subject_version=SubjectVersion(kind="policy_version", value="1.2.0"),
    measurement=Measurement(
        value=0.08,
        unit="ratio",
        direction="lower_is_better",
        source_shape=SourceShape(
            kind="ocsf",
            ocsf=OcsfPointer(
                class_uid=2004,
                class_name="Detection Finding",
                ocsf_version="1.1.0",
            ),
        ),
        evaluation_window="P1D",
        threshold_crossed="warn",
    ),
    captured_at=datetime(2026, 6, 18, 5, 0, 0, tzinfo=timezone.utc),
    source_url=(
        "https://example.org/runs/effectiveness-vuln-intake-example-0001"
    ),
    owner_role="metrics-wg",
    owner_assigned_at="2026-01-15",
    retention="P2Y",
)


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_load_json(SCHEMA))


# --------------------------------------------------------------------------- #
# Fixture-on-disk guardrails                                                  #
# --------------------------------------------------------------------------- #


def test_committed_example_exists() -> None:
    assert GOLDEN.exists(), f"missing committed example: {GOLDEN}"
    assert GOLDEN.stat().st_size > 0, f"empty committed example: {GOLDEN}"


# --------------------------------------------------------------------------- #
# Coverage axis 1: schema-conformant emit                                     #
# --------------------------------------------------------------------------- #


def test_committed_example_validates_against_schema() -> None:
    _validator().validate(_load_json(GOLDEN))


def test_replay_artifact_validates_against_schema(tmp_path: Path) -> None:
    update = emit_effectiveness_artifact_node(
        {"effectiveness_context": CTX, "evidence_output_dir": tmp_path}
    )
    written = Path(update["effectiveness_artifact_path"])
    _validator().validate(_load_json(written))


# --------------------------------------------------------------------------- #
# Coverage axis 2: byte-parity replay against the committed example           #
# --------------------------------------------------------------------------- #


def _drift_hint() -> str:
    return (
        "LangGraph effectiveness example drifted from a fresh adapter "
        "replay. If the change is intentional, regenerate the example "
        "via `PYTHONPATH=. python examples/langgraph/vuln_intake/"
        "evidence/effectiveness/regenerate.py` and commit the new bytes "
        "alongside the emitter / adapter change."
    )


def test_langgraph_replay_matches_committed_example(tmp_path: Path) -> None:
    update = emit_effectiveness_artifact_node(
        {"effectiveness_context": CTX, "evidence_output_dir": tmp_path}
    )
    written = Path(update["effectiveness_artifact_path"])
    assert written.read_bytes() == GOLDEN.read_bytes(), _drift_hint()


# --------------------------------------------------------------------------- #
# Coverage axis 3: indicator-anchor + NIS2 Article 21(2)(f) shape             #
# --------------------------------------------------------------------------- #


def test_committed_example_carries_indicator_anchors() -> None:
    record = _load_json(GOLDEN)
    assert record["metric_ref"] == "kri.control_effectiveness@v1"
    assert record["subject_version"]["kind"] == "policy_version"
    assert record["subject_version"]["value"] == "1.2.0"
    assert record["measurement"]["unit"] == "ratio"
    assert record["measurement"]["direction"] == "lower_is_better"
    assert record["measurement"]["source_shape"]["kind"] == "ocsf"
    assert "nis2:art-21-2-f" in record["regulation_refs"]


def test_artifact_id_is_deterministic_sha256(tmp_path: Path) -> None:
    """``artifact_id`` matches SHA-256(``<workflow_id>|<execution_id>|
    <compile_target>|<metric_ref>|<subject_version.value>``).
    """
    import hashlib

    record = _load_json(GOLDEN)
    expected = hashlib.sha256(
        (
            f"{record['workflow_id']}|{record['execution_id']}|"
            f"{record['compile_target']}|{record['metric_ref']}|"
            f"{record['subject_version']['value']}"
        ).encode("utf-8")
    ).hexdigest()
    assert record["artifact_id"] == expected

    update = emit_effectiveness_artifact_node(
        {"effectiveness_context": CTX, "evidence_output_dir": tmp_path}
    )
    assert update["effectiveness_artifact_id"] == expected
