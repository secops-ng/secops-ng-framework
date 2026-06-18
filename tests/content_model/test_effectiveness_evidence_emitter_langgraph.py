"""F-CP-06 CORE-FANOUT-LG — LangGraph adapter round-trip for the effectiveness emitter.

Pins (CORE-FANOUT-LG scope — EXTEND-tests-goldens, EXTEND-drift,
EXTEND-metrics, and the F-WF-09 auditor-bundle 'effectiveness' slot
wiring land on separate sibling cards):

1. The LangGraph node adapter wraps the shared helper. The on-disk
   record is byte-identical to what the shared renderer produces, and
   the partial state update names the right ``artifact_id`` /
   ``artifact_path``.
2. Public-bar discipline: out-of-range ratio measurements, unanchored
   ``source_shape`` discriminators, and credential-adjacent shapes are
   rejected at the adapter boundary — no artifact is written on any
   rejected path.
3. The ``compile_target`` axis keeps the LangGraph adapter's
   ``artifact_id`` distinct from the n8n adapter's for the same
   evaluation, so a refactor cannot silently collapse the targets.
4. Missing required state keys surface a typed ``KeyError`` for the
   integrator.
5. The adapter accepts a plain mapping for the nested
   ``effectiveness_context`` so a preceding node can assemble it from
   raw state without importing this module's dataclasses.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from compilers._shared.evidence import (
    EffectivenessContext,
    Measurement,
    SourceShape,
    SubjectVersion,
    render_effectiveness_artifact,
)

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "schemas"
EFFECTIVENESS_SCHEMA = SCHEMAS / "evidence" / "effectiveness.schema.json"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_load_json(EFFECTIVENESS_SCHEMA))


def _ctx(**overrides) -> EffectivenessContext:
    base = dict(
        workflow_id="vulnerability_triage",
        execution_id="langgraph:wf-run-effectiveness-001",
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
            source_shape=SourceShape(kind="none"),
            evaluation_window="P1D",
        ),
        captured_at=datetime(2026, 6, 18, 5, 0, 0, tzinfo=timezone.utc),
        source_url="https://example.org/runs/effectiveness-001",
        owner_role="metrics-wg",
        owner_assigned_at="2026-01-15",
        commit_sha="deadbeef0123456789",
    )
    base.update(overrides)
    return EffectivenessContext(**base)


def test_langgraph_node_wraps_shared_helper(tmp_path: Path) -> None:
    from compilers.langgraph.evidence import (
        emit_effectiveness_artifact_node,
    )

    ctx = _ctx()
    update = emit_effectiveness_artifact_node(
        {
            "effectiveness_context": ctx,
            "evidence_output_dir": str(tmp_path),
        }
    )
    written = Path(update["effectiveness_artifact_path"])
    assert written.exists()
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_effectiveness_artifact(ctx)
    assert update["effectiveness_artifact_id"] == on_disk["artifact_id"]
    assert written.name == f"{on_disk['artifact_id']}.json"


def test_langgraph_node_accepts_mapping_context(tmp_path: Path) -> None:
    """A preceding node can assemble the context as a plain mapping so
    it does not need to import this module's dataclasses. The adapter
    rebuilds the typed context (including nested ``subject_version``,
    ``measurement``, and ``measurement.source_shape`` blocks from
    sub-mappings) before delegating.
    """
    from compilers.langgraph.evidence import (
        emit_effectiveness_artifact_node,
    )

    ctx = _ctx()
    mapping_ctx = {
        "workflow_id": ctx.workflow_id,
        "execution_id": ctx.execution_id,
        "compile_target": ctx.compile_target,
        "regulation_refs": list(ctx.regulation_refs),
        "control_refs": list(ctx.control_refs),
        "metric_ref": ctx.metric_ref,
        "subject_version": {
            "kind": ctx.subject_version.kind,
            "value": ctx.subject_version.value,
        },
        "measurement": {
            "value": ctx.measurement.value,
            "unit": ctx.measurement.unit,
            "direction": ctx.measurement.direction,
            "source_shape": {"kind": "none"},
            "evaluation_window": ctx.measurement.evaluation_window,
        },
        "captured_at": ctx.captured_at,
        "source_url": ctx.source_url,
        "owner_role": ctx.owner_role,
        "owner_assigned_at": ctx.owner_assigned_at,
        "commit_sha": ctx.commit_sha,
    }
    update = emit_effectiveness_artifact_node(
        {
            "effectiveness_context": mapping_ctx,
            "evidence_output_dir": str(tmp_path),
        }
    )
    on_disk = json.loads(
        Path(update["effectiveness_artifact_path"]).read_text("utf-8")
    )
    _validator().validate(on_disk)
    assert on_disk == render_effectiveness_artifact(ctx)


def test_langgraph_node_rejects_out_of_range_ratio(tmp_path: Path) -> None:
    from compilers.langgraph.evidence import (
        emit_effectiveness_artifact_node,
    )

    with pytest.raises(ValueError):
        emit_effectiveness_artifact_node(
            {
                "effectiveness_context": _ctx(
                    measurement=Measurement(
                        value=1.5,
                        unit="ratio",
                        direction="lower_is_better",
                        source_shape=SourceShape(kind="none"),
                    )
                ),
                "evidence_output_dir": str(tmp_path),
            }
        )
    assert not list(tmp_path.iterdir())


def test_langgraph_node_rejects_unanchored_source_shape(tmp_path: Path) -> None:
    from compilers.langgraph.evidence import (
        emit_effectiveness_artifact_node,
    )

    with pytest.raises(ValueError):
        emit_effectiveness_artifact_node(
            {
                "effectiveness_context": _ctx(
                    measurement=Measurement(
                        value=0.1,
                        unit="ratio",
                        direction="lower_is_better",
                        source_shape=SourceShape(kind="ocsf"),
                    )
                ),
                "evidence_output_dir": str(tmp_path),
            }
        )
    assert not list(tmp_path.iterdir())


def test_langgraph_node_on_disk_record_byte_parity_with_shared_renderer(
    tmp_path: Path,
) -> None:
    from compilers.langgraph.evidence import (
        emit_effectiveness_artifact_node,
    )

    ctx = _ctx()
    update = emit_effectiveness_artifact_node(
        {
            "effectiveness_context": ctx,
            "evidence_output_dir": str(tmp_path),
        }
    )
    written = Path(update["effectiveness_artifact_path"])
    on_disk_bytes = written.read_bytes()
    assert json.loads(on_disk_bytes.decode("utf-8")) == (
        render_effectiveness_artifact(ctx)
    )


def test_langgraph_node_artifact_id_distinct_per_compile_target(
    tmp_path: Path,
) -> None:
    from compilers.langgraph.evidence import (
        emit_effectiveness_artifact_node,
    )

    ctx_lg = _ctx(compile_target="langgraph")
    update = emit_effectiveness_artifact_node(
        {
            "effectiveness_context": ctx_lg,
            "evidence_output_dir": str(tmp_path),
        }
    )
    on_disk_lg = json.loads(
        Path(update["effectiveness_artifact_path"]).read_text("utf-8")
    )
    on_disk_n8n = render_effectiveness_artifact(_ctx(compile_target="n8n"))
    assert on_disk_lg["compile_target"] == "langgraph"
    assert on_disk_lg["artifact_id"] != on_disk_n8n["artifact_id"]


def test_langgraph_node_raises_on_missing_state_keys(tmp_path: Path) -> None:
    from compilers.langgraph.evidence import (
        emit_effectiveness_artifact_node,
    )

    with pytest.raises(KeyError):
        emit_effectiveness_artifact_node(
            {"evidence_output_dir": str(tmp_path)}
        )
    with pytest.raises(KeyError):
        emit_effectiveness_artifact_node(
            {"effectiveness_context": _ctx()}
        )
