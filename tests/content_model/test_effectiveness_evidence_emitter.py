"""F-CP-06 — effectiveness evidence-artifact round-trip (shared emitter).

Pins (CORE-FANOUT scope — per-target byte-parity goldens, drift
scaffolding, metric-catalogue rollup, and the F-WF-09 auditor-bundle
'effectiveness' slot wiring land on separate sibling cards):

1. The shared emitter writes a record that validates against
   ``schemas/evidence/effectiveness.schema.json``.
2. The ``artifact_id`` is deterministic on
   ``(workflow_id, execution_id, compile_target, metric_ref,
   subject_version.value)`` — same inputs reproduce the same id;
   different inputs do not. ``captured_at`` is deliberately *not*
   part of the id.
3. The record persists to disk under ``<output_dir>/<artifact_id>.json``
   and re-reads byte-identical to the rendered record.
4. The Temporal activity wrapper delegates to the shared helper and
   produces the same on-disk record for the same context.
5. Public-bar discipline: ``measurement.value`` ranges are enforced
   per unit (ratio in [0, 1], percent in [0, 100], count >= 0 integer,
   duration_seconds >= 0); ``source_shape`` discriminator is enforced
   so a careless emitter cannot smuggle an unanchored payload past
   the boundary.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from compilers._shared.evidence import (
    EffectivenessContext,
    Measurement,
    OcsfPointer,
    SourceShape,
    SubjectVersion,
    derive_effectiveness_artifact_id,
    emit_effectiveness_artifact,
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
        execution_id="temporal:wf-run-effectiveness-001",
        compile_target="temporal",
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
            threshold_crossed="warn",
        ),
        captured_at=datetime(2026, 6, 18, 5, 0, 0, tzinfo=timezone.utc),
        source_url="https://example.org/runs/effectiveness-001",
        owner_role="metrics-wg",
        owner_assigned_at="2026-01-15",
        commit_sha="deadbeef0123456789",
    )
    base.update(overrides)
    return EffectivenessContext(**base)


# --------------------------------------------------------------------------- #
# Schema / determinism pins                                                   #
# --------------------------------------------------------------------------- #


def test_rendered_record_validates_against_schema() -> None:
    record = render_effectiveness_artifact(_ctx())
    _validator().validate(record)


def test_artifact_id_is_deterministic_on_anchors() -> None:
    ctx_a = _ctx()
    assert (
        render_effectiveness_artifact(ctx_a)["artifact_id"]
        == render_effectiveness_artifact(ctx_a)["artifact_id"]
    )
    expected = derive_effectiveness_artifact_id(
        ctx_a.workflow_id,
        ctx_a.execution_id,
        ctx_a.compile_target,
        ctx_a.metric_ref,
        ctx_a.subject_version.value,
    )
    assert render_effectiveness_artifact(ctx_a)["artifact_id"] == expected
    # Different execution_id → different id.
    ctx_b = _ctx(execution_id="temporal:wf-run-effectiveness-002")
    assert (
        render_effectiveness_artifact(ctx_b)["artifact_id"]
        != render_effectiveness_artifact(ctx_a)["artifact_id"]
    )
    # Different compile_target → different id.
    ctx_c = _ctx(compile_target="n8n")
    assert (
        render_effectiveness_artifact(ctx_c)["artifact_id"]
        != render_effectiveness_artifact(ctx_a)["artifact_id"]
    )
    # Different metric_ref → different id.
    ctx_d = _ctx(metric_ref="kpi.control_effectiveness_coverage@v1")
    assert (
        render_effectiveness_artifact(ctx_d)["artifact_id"]
        != render_effectiveness_artifact(ctx_a)["artifact_id"]
    )
    # Different subject_version.value → different id.
    ctx_e = _ctx(
        subject_version=SubjectVersion(kind="policy_version", value="1.3.0")
    )
    assert (
        render_effectiveness_artifact(ctx_e)["artifact_id"]
        != render_effectiveness_artifact(ctx_a)["artifact_id"]
    )


def test_artifact_id_is_independent_of_captured_at() -> None:
    """Re-emissions inside the same evaluation stay byte-identical at the
    path level — ``captured_at`` is deliberately not part of the id.
    """
    ctx_a = _ctx()
    ctx_b = _ctx(
        captured_at=datetime(2026, 6, 18, 6, 0, 0, tzinfo=timezone.utc)
    )
    assert (
        render_effectiveness_artifact(ctx_a)["artifact_id"]
        == render_effectiveness_artifact(ctx_b)["artifact_id"]
    )


def test_emit_persists_round_trip(tmp_path: Path) -> None:
    ctx = _ctx()
    written = emit_effectiveness_artifact(ctx, tmp_path)
    assert written.exists()
    assert (
        written.name
        == f"{render_effectiveness_artifact(ctx)['artifact_id']}.json"
    )
    on_disk = json.loads(written.read_text("utf-8"))
    assert on_disk == render_effectiveness_artifact(ctx)
    _validator().validate(on_disk)


def test_emit_omits_optional_blocks_when_caller_supplies_none(
    tmp_path: Path,
) -> None:
    ctx = _ctx(
        owner_role=None,
        owner_assigned_at=None,
        retention=None,
        commit_sha=None,
        measurement=Measurement(
            value=0.08,
            unit="ratio",
            direction="lower_is_better",
            source_shape=SourceShape(kind="none"),
        ),
    )
    written = emit_effectiveness_artifact(ctx, tmp_path)
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert "owner" not in on_disk
    assert "retention" not in on_disk
    assert "commit_sha" not in on_disk["provenance"]
    assert "evaluation_window" not in on_disk["measurement"]
    assert "threshold_crossed" not in on_disk["measurement"]


def test_emit_accepts_ocsf_source_shape(tmp_path: Path) -> None:
    ctx = _ctx(
        measurement=Measurement(
            value=12,
            unit="count",
            direction="lower_is_better",
            source_shape=SourceShape(
                kind="ocsf",
                ocsf=OcsfPointer(
                    class_uid=2004,
                    class_name="Detection Finding",
                    ocsf_version="1.1.0",
                ),
            ),
        )
    )
    written = emit_effectiveness_artifact(ctx, tmp_path)
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk["measurement"]["source_shape"]["ocsf"]["class_uid"] == 2004


def test_emit_accepts_telemetry_source_shape(tmp_path: Path) -> None:
    ctx = _ctx(
        measurement=Measurement(
            value=0.42,
            unit="ratio",
            direction="lower_is_better",
            source_shape=SourceShape(
                kind="telemetry",
                telemetry_ref="telemetry.control_attestation_state@v1",
            ),
        )
    )
    written = emit_effectiveness_artifact(ctx, tmp_path)
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)


# --------------------------------------------------------------------------- #
# Public-bar / shape rejections                                               #
# --------------------------------------------------------------------------- #


def test_emit_rejects_unknown_compile_target(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(_ctx(compile_target="make"), tmp_path)


def test_emit_rejects_bad_workflow_id(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(_ctx(workflow_id="Bad ID"), tmp_path)


def test_emit_rejects_bad_control_ref(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(
            _ctx(control_refs=("not-a-control-ref",)), tmp_path
        )


def test_emit_rejects_bad_regulation_ref(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(
            _ctx(regulation_refs=("invented:ref",)), tmp_path
        )


def test_emit_rejects_bad_metric_ref(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(
            _ctx(metric_ref="not-a-metric-ref"), tmp_path
        )


def test_emit_rejects_bad_subject_version_kind(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(
            _ctx(
                subject_version=SubjectVersion(
                    kind="not_a_kind", value="1.0.0"
                )
            ),
            tmp_path,
        )


def test_emit_rejects_bad_subject_version_value(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(
            _ctx(
                subject_version=SubjectVersion(
                    kind="policy_version", value="v1"
                )
            ),
            tmp_path,
        )


def test_emit_rejects_ratio_out_of_range(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(
            _ctx(
                measurement=Measurement(
                    value=1.5,
                    unit="ratio",
                    direction="lower_is_better",
                    source_shape=SourceShape(kind="none"),
                )
            ),
            tmp_path,
        )


def test_emit_rejects_negative_count(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(
            _ctx(
                measurement=Measurement(
                    value=-1,
                    unit="count",
                    direction="lower_is_better",
                    source_shape=SourceShape(kind="none"),
                )
            ),
            tmp_path,
        )


def test_emit_rejects_non_integer_count(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(
            _ctx(
                measurement=Measurement(
                    value=3.5,
                    unit="count",
                    direction="lower_is_better",
                    source_shape=SourceShape(kind="none"),
                )
            ),
            tmp_path,
        )


def test_emit_rejects_bad_unit(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(
            _ctx(
                measurement=Measurement(
                    value=0.1,
                    unit="bananas",
                    direction="lower_is_better",
                    source_shape=SourceShape(kind="none"),
                )
            ),
            tmp_path,
        )


def test_emit_rejects_bad_direction(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(
            _ctx(
                measurement=Measurement(
                    value=0.1,
                    unit="ratio",
                    direction="sideways",
                    source_shape=SourceShape(kind="none"),
                )
            ),
            tmp_path,
        )


def test_emit_rejects_ocsf_kind_without_ocsf_block(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(
            _ctx(
                measurement=Measurement(
                    value=0.1,
                    unit="ratio",
                    direction="lower_is_better",
                    source_shape=SourceShape(kind="ocsf"),
                )
            ),
            tmp_path,
        )


def test_emit_rejects_telemetry_kind_without_ref(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(
            _ctx(
                measurement=Measurement(
                    value=0.1,
                    unit="ratio",
                    direction="lower_is_better",
                    source_shape=SourceShape(kind="telemetry"),
                )
            ),
            tmp_path,
        )


def test_emit_rejects_none_kind_with_extra_pointer(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(
            _ctx(
                measurement=Measurement(
                    value=0.1,
                    unit="ratio",
                    direction="lower_is_better",
                    source_shape=SourceShape(
                        kind="none",
                        telemetry_ref="telemetry.foo@v1",
                    ),
                )
            ),
            tmp_path,
        )


def test_emit_rejects_bad_evaluation_window(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(
            _ctx(
                measurement=Measurement(
                    value=0.1,
                    unit="ratio",
                    direction="lower_is_better",
                    source_shape=SourceShape(kind="none"),
                    evaluation_window="2 days",
                )
            ),
            tmp_path,
        )


def test_emit_rejects_bad_threshold_token(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(
            _ctx(
                measurement=Measurement(
                    value=0.1,
                    unit="ratio",
                    direction="lower_is_better",
                    source_shape=SourceShape(kind="none"),
                    threshold_crossed="Warn!",
                )
            ),
            tmp_path,
        )


def test_emit_rejects_naive_captured_at(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(
            _ctx(captured_at=datetime(2026, 6, 18, 5, 0, 0)),
            tmp_path,
        )


def test_emit_rejects_partial_owner_block(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(
            _ctx(owner_role="metrics-wg", owner_assigned_at=None),
            tmp_path,
        )


def test_emit_rejects_bad_owner_assigned_at(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(
            _ctx(owner_assigned_at="2026/01/15"),
            tmp_path,
        )


def test_emit_rejects_bad_commit_sha(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(_ctx(commit_sha="not-hex"), tmp_path)


def test_emit_rejects_bad_retention(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_effectiveness_artifact(_ctx(retention="2years"), tmp_path)


# --------------------------------------------------------------------------- #
# n8n adapter round-trip (CORE-FANOUT-N8N)                                    #
# --------------------------------------------------------------------------- #


def _payload_from_ctx(ctx: EffectivenessContext) -> dict:
    """Re-shape a context as the JSON-native payload an n8n node sends."""
    sv = ctx.subject_version
    sv_payload = {"kind": sv.kind, "value": sv.value}

    ss = ctx.measurement.source_shape
    ss_payload: dict = {"kind": ss.kind}
    if ss.ocsf is not None:
        ocsf_payload: dict = {"class_uid": ss.ocsf.class_uid}
        if ss.ocsf.class_name is not None:
            ocsf_payload["class_name"] = ss.ocsf.class_name
        if ss.ocsf.ocsf_version is not None:
            ocsf_payload["ocsf_version"] = ss.ocsf.ocsf_version
        ss_payload["ocsf"] = ocsf_payload
    if ss.telemetry_ref is not None:
        ss_payload["telemetry_ref"] = ss.telemetry_ref

    m = ctx.measurement
    m_payload: dict = {
        "value": m.value,
        "unit": m.unit,
        "direction": m.direction,
        "source_shape": ss_payload,
    }
    if m.evaluation_window is not None:
        m_payload["evaluation_window"] = m.evaluation_window
    if m.threshold_crossed is not None:
        m_payload["threshold_crossed"] = m.threshold_crossed

    payload: dict = {
        "workflow_id": ctx.workflow_id,
        "execution_id": ctx.execution_id,
        "compile_target": ctx.compile_target,
        "regulation_refs": list(ctx.regulation_refs),
        "control_refs": list(ctx.control_refs),
        "metric_ref": ctx.metric_ref,
        "subject_version": sv_payload,
        "measurement": m_payload,
        "captured_at": ctx.captured_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_url": ctx.source_url,
    }
    if ctx.owner_role is not None:
        payload["owner_role"] = ctx.owner_role
        payload["owner_assigned_at"] = ctx.owner_assigned_at
    if ctx.commit_sha is not None:
        payload["commit_sha"] = ctx.commit_sha
    if ctx.retention is not None:
        payload["retention"] = ctx.retention
    return payload


def test_n8n_adapter_wraps_shared_helper(tmp_path: Path) -> None:
    from compilers.n8n.evidence import emit_effectiveness_artifact_n8n

    ctx = _ctx(compile_target="n8n")
    result = emit_effectiveness_artifact_n8n(
        _payload_from_ctx(ctx), tmp_path
    )
    written = Path(result["artifact_path"])
    assert written.exists()
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_effectiveness_artifact(ctx)
    assert result["artifact_id"] == on_disk["artifact_id"]
    assert written.name == f"{on_disk['artifact_id']}.json"


def test_n8n_adapter_rejects_out_of_range_ratio(tmp_path: Path) -> None:
    from compilers.n8n.evidence import emit_effectiveness_artifact_n8n

    ctx = _ctx(compile_target="n8n")
    payload = _payload_from_ctx(ctx)
    payload["measurement"]["value"] = 1.5
    with pytest.raises(ValueError):
        emit_effectiveness_artifact_n8n(payload, tmp_path)
    assert not list(tmp_path.iterdir())


def test_n8n_adapter_artifact_id_matches_temporal_for_same_evaluation(
    tmp_path: Path,
) -> None:
    """The compile-target axis is part of the id; n8n and temporal IDs
    diverge for the same evaluation. Pin the contract from both ends.
    """
    from compilers.n8n.evidence import emit_effectiveness_artifact_n8n

    ctx_n8n = _ctx(compile_target="n8n")
    result = emit_effectiveness_artifact_n8n(
        _payload_from_ctx(ctx_n8n), tmp_path
    )
    on_disk_n8n = json.loads(
        Path(result["artifact_path"]).read_text("utf-8")
    )
    on_disk_temporal = render_effectiveness_artifact(
        _ctx(compile_target="temporal")
    )
    assert on_disk_n8n["compile_target"] == "n8n"
    assert on_disk_n8n["artifact_id"] != on_disk_temporal["artifact_id"]


# --------------------------------------------------------------------------- #
# Temporal activity wrapper                                                   #
# --------------------------------------------------------------------------- #


def test_temporal_activity_wraps_shared_helper(tmp_path: Path) -> None:
    """Happy-path Temporal pin required by the F-CP-06 CORE-FANOUT card."""
    pytest.importorskip("temporalio")
    from compilers.temporal.evidence import (
        emit_effectiveness_artifact_activity,
    )

    ctx = _ctx()
    written_str = asyncio.run(
        emit_effectiveness_artifact_activity(ctx, str(tmp_path))
    )
    written = Path(written_str)
    assert written.exists()
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_effectiveness_artifact(ctx)
    written_files = [p for p in Path(tmp_path).iterdir() if p.suffix == ".json"]
    assert len(written_files) == 1
    assert written_files[0].name == f"{on_disk['artifact_id']}.json"
