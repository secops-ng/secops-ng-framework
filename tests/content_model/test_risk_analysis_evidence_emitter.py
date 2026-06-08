"""F-CP-01 — risk-analysis evidence-artifact round-trip (cross-target).

Pins:

1. The shared emitter writes a record that validates against
   ``schemas/evidence/risk-analysis.schema.json``.
2. The ``artifact_id`` is deterministic on ``(control_ref, captured_at)``
   — same inputs reproduce the same id; different inputs do not.
3. The record persists to disk under ``<output_dir>/<artifact_id>.json``
   and re-reads byte-identical to the rendered record.
4. All three compile-target adapters (Temporal activity, n8n CLI/Code
   adapter, LangGraph node) delegate to the shared helper and produce
   the same on-disk record for the same context — CORE-FANOUT pins
   parity at the record-shape level; per-target byte-parity goldens
   land in the EXTEND-tests sibling.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, RefResolver

from compilers._shared.evidence import (
    RiskAnalysisContext,
    derive_artifact_id,
    emit_risk_analysis_artifact,
    render_risk_analysis_artifact,
)

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "schemas"
ATTESTATION_STATE_SCHEMA = SCHEMAS / "attestation_state.json"
RISK_ANALYSIS_SCHEMA = SCHEMAS / "evidence" / "risk-analysis.schema.json"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    schema = _load_json(RISK_ANALYSIS_SCHEMA)
    store = {
        "https://secops-ng.org/schemas/attestation_state.json": _load_json(
            ATTESTATION_STATE_SCHEMA
        ),
        "attestation_state.json": _load_json(ATTESTATION_STATE_SCHEMA),
    }
    resolver = RefResolver(base_uri=schema["$id"], referrer=schema, store=store)
    return Draft202012Validator(schema, resolver=resolver)


def _ctx(**overrides) -> RiskAnalysisContext:
    base = dict(
        control_ref="control.risk_management_policy@v1",
        regulation_refs=("nis2:art-21-2-a", "dora:art-5-governance"),
        policy_version="1.2.0",
        attestation_state="effective",
        residual_exposure_summary=(
            "Control operating as designed; residual exposure limited to "
            "scenarios outside the policy's declared scope."
        ),
        owner_role="risk-management-wg@example.org",
        owner_assigned_at="2026-01-15",
        review_cadence="P1Y",
        captured_at=datetime(2026, 6, 7, 5, 0, 0, tzinfo=timezone.utc),
        source_url="https://example.org/runs/abc123",
        commit_sha="deadbeef0123456789",
    )
    base.update(overrides)
    return RiskAnalysisContext(**base)


def test_rendered_record_validates_against_schema() -> None:
    record = render_risk_analysis_artifact(_ctx())
    _validator().validate(record)


def test_artifact_id_is_deterministic_on_control_ref_and_captured_at() -> None:
    ctx_a = _ctx()
    # Same inputs → same id.
    assert (
        render_risk_analysis_artifact(ctx_a)["artifact_id"]
        == render_risk_analysis_artifact(ctx_a)["artifact_id"]
    )
    expected = derive_artifact_id(ctx_a.control_ref, ctx_a.captured_at)
    assert render_risk_analysis_artifact(ctx_a)["artifact_id"] == expected
    # Different captured_at → different id.
    ctx_b = _ctx(captured_at=datetime(2027, 6, 7, 5, 0, 0, tzinfo=timezone.utc))
    assert (
        render_risk_analysis_artifact(ctx_b)["artifact_id"]
        != render_risk_analysis_artifact(ctx_a)["artifact_id"]
    )


def test_emit_persists_round_trip(tmp_path: Path) -> None:
    ctx = _ctx()
    written = emit_risk_analysis_artifact(ctx, tmp_path)
    assert written.exists()
    assert written.name == f"{render_risk_analysis_artifact(ctx)['artifact_id']}.json"
    on_disk = json.loads(written.read_text("utf-8"))
    assert on_disk == render_risk_analysis_artifact(ctx)
    _validator().validate(on_disk)


def test_emit_with_delta_and_drift_round_trip(tmp_path: Path) -> None:
    ctx = _ctx(
        previous_artifact_id="c" * 64,
        previous_state="partially_effective",
        previous_captured_at=datetime(2025, 6, 7, 5, 0, 0, tzinfo=timezone.utc),
        baseline_drift={"changed": False},
        scoped_scenarios=("ransomware", "supply-chain compromise"),
    )
    written = emit_risk_analysis_artifact(ctx, tmp_path)
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk["attestation_state_delta"]["previous_artifact_id"] == "c" * 64
    assert on_disk["baseline_drift"] == {"changed": False}


def test_emit_rejects_bad_control_ref(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_risk_analysis_artifact(_ctx(control_ref="ctl:bad"), tmp_path)


def test_emit_rejects_naive_captured_at(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_risk_analysis_artifact(
            _ctx(captured_at=datetime(2026, 6, 7, 5, 0, 0)), tmp_path
        )


def test_temporal_activity_wraps_shared_helper(tmp_path: Path) -> None:
    # Import lazily so the rest of the test module still runs in environments
    # without temporalio installed.
    pytest.importorskip("temporalio")
    from compilers.temporal.evidence import emit_risk_analysis_artifact_activity

    ctx = _ctx()
    # Activities are async; run via asyncio.
    # ``@activity.defn`` returns the original async callable, so the
    # function is awaitable directly without unwrapping.
    written_str = asyncio.run(
        emit_risk_analysis_artifact_activity(ctx, str(tmp_path))
    )
    written = Path(written_str)
    assert written.exists()
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_risk_analysis_artifact(ctx)


def _payload_from_ctx(ctx: RiskAnalysisContext) -> dict:
    """Re-shape a context as the JSON-native payload an n8n node sends.

    n8n cannot transport Python objects across the node-process boundary,
    so datetimes arrive as ISO-8601 strings. We mirror the on-the-wire
    shape here so the adapter exercises the same parse path an operator
    would hit in production.
    """
    payload: dict = {
        "control_ref": ctx.control_ref,
        "regulation_refs": list(ctx.regulation_refs),
        "policy_version": ctx.policy_version,
        "attestation_state": ctx.attestation_state,
        "residual_exposure_summary": ctx.residual_exposure_summary,
        "owner_role": ctx.owner_role,
        "owner_assigned_at": ctx.owner_assigned_at,
        "review_cadence": ctx.review_cadence,
        "captured_at": ctx.captured_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_url": ctx.source_url,
    }
    if ctx.commit_sha:
        payload["commit_sha"] = ctx.commit_sha
    if ctx.scoped_scenarios:
        payload["scoped_scenarios"] = list(ctx.scoped_scenarios)
    if ctx.deviations_from_baseline:
        payload["deviations_from_baseline"] = list(ctx.deviations_from_baseline)
    if ctx.compensating_controls:
        payload["compensating_controls"] = list(ctx.compensating_controls)
    if ctx.previous_artifact_id:
        payload["previous_artifact_id"] = ctx.previous_artifact_id
    if ctx.previous_state:
        payload["previous_state"] = ctx.previous_state
    if ctx.previous_captured_at is not None:
        payload["previous_captured_at"] = ctx.previous_captured_at.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    if ctx.baseline_drift is not None:
        payload["baseline_drift"] = dict(ctx.baseline_drift)
    return payload


def test_n8n_adapter_wraps_shared_helper(tmp_path: Path) -> None:
    from compilers.n8n.evidence import emit_risk_analysis_artifact_n8n

    ctx = _ctx()
    result = emit_risk_analysis_artifact_n8n(_payload_from_ctx(ctx), tmp_path)
    written = Path(result["artifact_path"])
    assert written.exists()
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_risk_analysis_artifact(ctx)
    assert result["artifact_id"] == on_disk["artifact_id"]
    assert written.name == f"{on_disk['artifact_id']}.json"


def test_langgraph_node_wraps_shared_helper(tmp_path: Path) -> None:
    from compilers.langgraph.evidence import emit_risk_analysis_artifact_node

    ctx = _ctx()
    state = {
        "risk_analysis_context": ctx,
        "evidence_output_dir": str(tmp_path),
    }
    update = emit_risk_analysis_artifact_node(state)
    written = Path(update["risk_analysis_artifact_path"])
    assert written.exists()
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_risk_analysis_artifact(ctx)
    assert update["risk_analysis_artifact_id"] == on_disk["artifact_id"]


def test_all_three_targets_produce_byte_identical_records(tmp_path: Path) -> None:
    """CORE-FANOUT parity pin.

    The whole point of the shared emitter is that the three compile
    targets cannot drift on record shape. Each adapter writes the same
    context into its own subdirectory; the on-disk JSON must match byte
    for byte across targets. Per-target byte-parity goldens against a
    checked-in fixture land in the EXTEND-tests sibling; this test
    pins the cross-target equivalence today.
    """
    pytest.importorskip("temporalio")
    from compilers.temporal.evidence import emit_risk_analysis_artifact_activity
    from compilers.n8n.evidence import emit_risk_analysis_artifact_n8n
    from compilers.langgraph.evidence import emit_risk_analysis_artifact_node

    ctx = _ctx()

    tmp_temporal = tmp_path / "temporal"
    tmp_n8n = tmp_path / "n8n"
    tmp_langgraph = tmp_path / "langgraph"

    temporal_path = Path(
        asyncio.run(
            emit_risk_analysis_artifact_activity(ctx, str(tmp_temporal))
        )
    )
    n8n_result = emit_risk_analysis_artifact_n8n(
        _payload_from_ctx(ctx), tmp_n8n
    )
    n8n_path = Path(n8n_result["artifact_path"])
    langgraph_update = emit_risk_analysis_artifact_node(
        {
            "risk_analysis_context": ctx,
            "evidence_output_dir": str(tmp_langgraph),
        }
    )
    langgraph_path = Path(langgraph_update["risk_analysis_artifact_path"])

    # Same artifact_id across all three targets.
    assert temporal_path.stem == n8n_path.stem == langgraph_path.stem

    # Byte-identical on-disk JSON.
    bytes_temporal = temporal_path.read_bytes()
    bytes_n8n = n8n_path.read_bytes()
    bytes_langgraph = langgraph_path.read_bytes()
    assert bytes_temporal == bytes_n8n == bytes_langgraph
