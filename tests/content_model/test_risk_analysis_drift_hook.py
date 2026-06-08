"""F-CP-01 SKELETON — drift-detection hook invocation.

Pins the surface (not the payload contract — that lands in CORE-WIRE):

1. When successive emissions on the same control change
   ``attestation_state`` between runs, the shared emitter invokes the
   supplied ``drift_hook`` with a :class:`DriftEvent` carrying the
   expected identifying fields.
2. Re-emitting at the same ``attestation_state`` does NOT fire the hook
   (only real transitions surface).
3. The default hook is :func:`noop_drift_hook` — a hook-less call is
   still a valid call.
4. All three target adapters (Temporal activity, n8n adapter, LangGraph
   node) thread the hook through to the shared helper unchanged.
"""
from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pytest

from compilers._shared.evidence import (
    DriftEvent,
    RiskAnalysisContext,
    emit_risk_analysis_artifact,
    noop_drift_hook,
)
from compilers.langgraph.evidence.risk_analysis_node import (
    emit_risk_analysis_artifact_node,
)
from compilers.n8n.evidence.risk_analysis_node import (
    emit_risk_analysis_artifact_n8n,
)
from compilers.temporal.evidence.risk_analysis_activity import (
    emit_risk_analysis_artifact_activity,
)


def _ctx(**overrides) -> RiskAnalysisContext:
    base = dict(
        control_ref="control.risk_management_policy@v1",
        regulation_refs=("nis2:art-21-2-a",),
        policy_version="1.2.0",
        attestation_state="effective",
        residual_exposure_summary="Operating as designed.",
        owner_role="risk-management-wg@example.org",
        owner_assigned_at="2026-01-15",
        review_cadence="P1Y",
        captured_at=datetime(2026, 6, 7, 5, 0, 0, tzinfo=timezone.utc),
        source_url="https://example.org/runs/abc123",
        commit_sha="deadbeef0123456789",
    )
    base.update(overrides)
    return RiskAnalysisContext(**base)


def _drift_ctx(*, current_state: str = "drifting") -> RiskAnalysisContext:
    """A second-cadence emission with a real state transition."""
    return _ctx(
        attestation_state=current_state,
        captured_at=datetime(2026, 6, 14, 5, 0, 0, tzinfo=timezone.utc),
        previous_artifact_id="prev-artifact-id-placeholder",
        previous_state="effective",
        previous_captured_at=datetime(2026, 6, 7, 5, 0, 0, tzinfo=timezone.utc),
    )


def test_hook_invoked_on_real_transition(tmp_path: Path) -> None:
    seen: list[DriftEvent] = []
    out = emit_risk_analysis_artifact(
        _drift_ctx(),
        tmp_path,
        drift_hook=seen.append,
    )
    assert len(seen) == 1
    event = seen[0]
    assert isinstance(event, DriftEvent)
    assert event.control_ref == "control.risk_management_policy@v1"
    assert event.previous_state == "effective"
    assert event.current_state == "drifting"
    assert event.previous_artifact_id == "prev-artifact-id-placeholder"
    assert event.current_artifact_id == out.stem
    assert event.workflow_id == "https://example.org/runs/abc123"
    assert event.record["attestation_state"] == "drifting"


def test_hook_not_invoked_on_steady_state(tmp_path: Path) -> None:
    """Re-emission at the same attestation_state is not drift."""
    seen: list[DriftEvent] = []
    ctx = _ctx(
        previous_artifact_id="prev-artifact-id-placeholder",
        previous_state="effective",  # identical to current attestation_state
        previous_captured_at=datetime(2026, 5, 31, 5, 0, 0, tzinfo=timezone.utc),
        captured_at=datetime(2026, 6, 7, 5, 0, 0, tzinfo=timezone.utc),
    )
    emit_risk_analysis_artifact(ctx, tmp_path, drift_hook=seen.append)
    assert seen == []


def test_hook_not_invoked_on_first_emission(tmp_path: Path) -> None:
    """No previous_state -> no transition observable -> no event."""
    seen: list[DriftEvent] = []
    emit_risk_analysis_artifact(_ctx(), tmp_path, drift_hook=seen.append)
    assert seen == []


def test_default_hook_is_noop(tmp_path: Path) -> None:
    """A hook-less call still writes the artifact and does not raise."""
    out = emit_risk_analysis_artifact(_drift_ctx(), tmp_path)
    assert out.exists()
    # The exported noop callable is safe to call directly.
    noop_drift_hook(
        DriftEvent(
            control_ref="control.x@v1",
            workflow_id="https://example.org/runs/x",
            previous_state="a",
            current_state="b",
            previous_artifact_id=None,
            current_artifact_id="x",
            captured_at="2026-06-07T05:00:00Z",
            record={},
        )
    )


def test_temporal_adapter_threads_hook(tmp_path: Path) -> None:
    seen: list[DriftEvent] = []
    asyncio.run(
        emit_risk_analysis_artifact_activity(
            _drift_ctx(),
            str(tmp_path),
            seen.append,
        )
    )
    assert len(seen) == 1
    assert seen[0].current_state == "drifting"


def test_n8n_adapter_threads_hook(tmp_path: Path) -> None:
    seen: list[DriftEvent] = []
    ctx = _drift_ctx()
    payload = asdict(ctx)
    # n8n payloads are JSON-native: datetimes are ISO-8601 strings.
    payload["captured_at"] = ctx.captured_at.isoformat().replace("+00:00", "Z")
    payload["previous_captured_at"] = ctx.previous_captured_at.isoformat().replace(
        "+00:00", "Z"
    )
    result = emit_risk_analysis_artifact_n8n(
        payload, tmp_path, drift_hook=seen.append
    )
    assert result["artifact_id"]
    assert len(seen) == 1
    assert seen[0].current_state == "drifting"


def test_langgraph_adapter_threads_hook(tmp_path: Path) -> None:
    seen: list[DriftEvent] = []
    state = {
        "risk_analysis_context": _drift_ctx(),
        "evidence_output_dir": tmp_path,
        "drift_hook": seen.append,
    }
    update = emit_risk_analysis_artifact_node(state)
    assert update["risk_analysis_artifact_path"]
    assert len(seen) == 1
    assert seen[0].current_state == "drifting"
