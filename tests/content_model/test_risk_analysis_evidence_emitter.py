"""F-CP-01 EMITTER SKELETON — risk-analysis evidence-artifact round-trip.

Pins:

1. The shared emitter writes a record that validates against
   ``schemas/evidence/risk-analysis.schema.json``.
2. The ``artifact_id`` is deterministic on ``(control_ref, captured_at)``
   — same inputs reproduce the same id; different inputs do not.
3. The record persists to disk under ``<output_dir>/<artifact_id>.json``
   and re-reads byte-identical to the rendered record.
4. The Temporal-side activity wrapper delegates to the shared helper
   (the SKELETON's one wired compile target).
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
    # without temporalio installed; the activity wrapper is the SKELETON's
    # one wired compile target so we exercise it here.
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
