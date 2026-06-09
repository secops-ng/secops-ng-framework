"""F-CP-02 — incidents evidence-artifact round-trip (cross-target).

Pins:

1. The shared emitter writes a record that validates against
   ``schemas/evidence/incidents.schema.json`` (with the promoted
   ``nis2_incident_notification_milestone`` schema resolved).
2. The ``artifact_id`` is deterministic on ``(incident_id, execution_id)``
   — same inputs reproduce the same id; different inputs do not.
3. The record persists to disk under ``<output_dir>/<artifact_id>.json``
   and re-reads byte-identical to the rendered record.
4. All three compile-target adapters (Temporal activity, n8n CLI/Code
   adapter, LangGraph node) delegate to the shared helper and produce
   the same on-disk record for the same context — CORE-FANOUT pins
   parity at the record-shape level; per-target byte-parity goldens
   against a checked-in fixture land in the EXTEND-tests sibling.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, RefResolver

from compilers._shared.evidence import (
    ClassificationVerdict,
    IncidentsContext,
    KpiWindows,
    Lifecycle,
    NotificationMilestone,
    derive_incidents_artifact_id,
    emit_incidents_artifact,
    render_incidents_artifact,
)

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "schemas"
NIS2_MILESTONE_SCHEMA = SCHEMAS / "nis2_incident_notification_milestone.json"
INCIDENTS_EVIDENCE_SCHEMA = SCHEMAS / "evidence" / "incidents.schema.json"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    schema = _load_json(INCIDENTS_EVIDENCE_SCHEMA)
    store = {
        "https://secops-ng.org/schemas/nis2_incident_notification_milestone.json": _load_json(
            NIS2_MILESTONE_SCHEMA
        ),
    }
    resolver = RefResolver(base_uri=schema["$id"], referrer=schema, store=store)
    return Draft202012Validator(schema, resolver=resolver)


def _incident_id() -> str:
    # RFC 4122 v4 UUID — pinned literal so artifact_id is reproducible
    # across test runs without random state.
    return "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d"


def _ctx(**overrides) -> IncidentsContext:
    base = dict(
        incident_id=_incident_id(),
        execution_id="temporal:wf-run-incident-001",
        regulation_refs=(
            "nis2:art-21-2-b",
            "nis2:art-23-early-warning",
            "nis2:art-23-notification-72h",
            "nis2:art-23-final-report",
        ),
        control_refs=(
            "control.incident_handling_capability@v1",
            "control.incident_timeline_signals@v1",
        ),
        classification=ClassificationVerdict(
            significant=True,
            cross_border=False,
            reasons=(
                "Severe disruption to availability of an essential service.",
            ),
            rule_ids=("sig.severe_disruption",),
            severity="High",
            summary=(
                "Authentication-edge availability lost for 47 minutes; "
                "containment via failover to standby region; root cause "
                "scoped to misapplied configuration change."
            ),
        ),
        lifecycle=Lifecycle(
            first_observation_at=datetime(
                2026, 6, 5, 12, 0, 0, tzinfo=timezone.utc
            ),
            detected_at=datetime(2026, 6, 5, 12, 30, 0, tzinfo=timezone.utc),
            triaged_at=datetime(2026, 6, 5, 12, 45, 0, tzinfo=timezone.utc),
            contained_at=datetime(2026, 6, 5, 13, 17, 0, tzinfo=timezone.utc),
            eradicated_at=datetime(2026, 6, 5, 14, 0, 0, tzinfo=timezone.utc),
            recovered_at=datetime(2026, 6, 5, 14, 30, 0, tzinfo=timezone.utc),
            closed_at=datetime(2026, 6, 6, 9, 0, 0, tzinfo=timezone.utc),
        ),
        owner_role="csirt@example.org",
        owner_assigned_at="2026-06-05",
        captured_at=datetime(2026, 6, 6, 9, 0, 0, tzinfo=timezone.utc),
        source_url="https://example.org/runs/incident-001",
        notification_timeline=(
            NotificationMilestone(
                milestone="early_warning_24h",
                clock_started_at=datetime(
                    2026, 6, 5, 12, 30, 0, tzinfo=timezone.utc
                ),
                submitted_at=datetime(
                    2026, 6, 5, 18, 0, 0, tzinfo=timezone.utc
                ),
                submission_ref="csirt-ticket-001",
                on_time=True,
            ),
            NotificationMilestone(
                milestone="incident_notification_72h",
                clock_started_at=datetime(
                    2026, 6, 5, 12, 30, 0, tzinfo=timezone.utc
                ),
                submitted_at=datetime(
                    2026, 6, 6, 9, 0, 0, tzinfo=timezone.utc
                ),
                submission_ref="csirt-ticket-002",
                on_time=True,
            ),
        ),
        kpi_windows=KpiWindows(
            mttd_minutes=30.0,
            mttr_minutes=47.0,
            containment_window_minutes=43.0,
            eradication_window_minutes=30.0,
        ),
        commit_sha="deadbeef0123456789",
    )
    base.update(overrides)
    return IncidentsContext(**base)


def test_rendered_record_validates_against_schema() -> None:
    record = render_incidents_artifact(_ctx())
    _validator().validate(record)


def test_artifact_id_is_deterministic_on_incident_id_and_execution_id() -> None:
    ctx_a = _ctx()
    assert (
        render_incidents_artifact(ctx_a)["artifact_id"]
        == render_incidents_artifact(ctx_a)["artifact_id"]
    )
    expected = derive_incidents_artifact_id(
        ctx_a.incident_id, ctx_a.execution_id
    )
    assert render_incidents_artifact(ctx_a)["artifact_id"] == expected
    # Different execution_id → different id; same incident_id carries through.
    ctx_b = _ctx(execution_id="temporal:wf-run-incident-002")
    rendered_b = render_incidents_artifact(ctx_b)
    assert (
        rendered_b["artifact_id"]
        != render_incidents_artifact(ctx_a)["artifact_id"]
    )
    assert rendered_b["incident_id"] == render_incidents_artifact(ctx_a)[
        "incident_id"
    ]


def test_emit_persists_round_trip(tmp_path: Path) -> None:
    ctx = _ctx()
    written = emit_incidents_artifact(ctx, tmp_path)
    assert written.exists()
    assert (
        written.name
        == f"{render_incidents_artifact(ctx)['artifact_id']}.json"
    )
    on_disk = json.loads(written.read_text("utf-8"))
    assert on_disk == render_incidents_artifact(ctx)
    _validator().validate(on_disk)


def test_emit_covers_all_three_nis2_milestones(tmp_path: Path) -> None:
    """Acceptance pin: SCHEMA names three NIS2 Article 23(4) milestones;
    one artifact MUST be able to carry all three on a single
    ``notification_timeline``.
    """
    started = datetime(2026, 6, 5, 12, 30, 0, tzinfo=timezone.utc)
    submitted = datetime(2026, 7, 5, 12, 0, 0, tzinfo=timezone.utc)
    timeline = tuple(
        NotificationMilestone(
            milestone=name,
            clock_started_at=started,
            submitted_at=submitted,
            submission_ref=f"csirt-{name}",
            on_time=True,
        )
        for name in (
            "early_warning_24h",
            "incident_notification_72h",
            "final_report_1mo",
        )
    )
    written = emit_incidents_artifact(
        _ctx(notification_timeline=timeline), tmp_path
    )
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert [m["milestone"] for m in on_disk["notification_timeline"]] == [
        "early_warning_24h",
        "incident_notification_72h",
        "final_report_1mo",
    ]


def test_emit_accepts_non_significant_intake(tmp_path: Path) -> None:
    """A significance == false case takes the intake-only audit-close
    branch — empty notification_timeline, severity / summary may be
    omitted, the lifecycle carries detected_at and not much else.
    """
    ctx = _ctx(
        classification=ClassificationVerdict(
            significant=False,
            cross_border=False,
            reasons=("Below the significance threshold.",),
            rule_ids=("sig.below_threshold",),
        ),
        lifecycle=Lifecycle(
            detected_at=datetime(2026, 6, 5, 12, 30, 0, tzinfo=timezone.utc),
            triaged_at=datetime(2026, 6, 5, 12, 45, 0, tzinfo=timezone.utc),
            closed_at=datetime(2026, 6, 5, 13, 0, 0, tzinfo=timezone.utc),
        ),
        notification_timeline=(),
        kpi_windows=None,
    )
    written = emit_incidents_artifact(ctx, tmp_path)
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk["classification"]["significant"] is False
    assert on_disk["notification_timeline"] == []
    assert "kpi_windows" not in on_disk
    assert "severity" not in on_disk["classification"]


def test_emit_omits_kpi_windows_when_not_supplied(tmp_path: Path) -> None:
    """The schema marks ``kpi_windows`` as optional; the helper must
    not emit an empty key.
    """
    ctx = _ctx(kpi_windows=None)
    written = emit_incidents_artifact(ctx, tmp_path)
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert "kpi_windows" not in on_disk


def test_emit_rejects_bad_incident_id(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_incidents_artifact(_ctx(incident_id="not-a-uuid"), tmp_path)


def test_emit_rejects_bad_milestone(tmp_path: Path) -> None:
    bad = NotificationMilestone(
        milestone="bogus_stage",
        clock_started_at=datetime(2026, 6, 5, 12, 30, 0, tzinfo=timezone.utc),
        submitted_at=datetime(2026, 6, 5, 18, 0, 0, tzinfo=timezone.utc),
    )
    with pytest.raises(ValueError):
        emit_incidents_artifact(
            _ctx(notification_timeline=(bad,)), tmp_path
        )


def test_emit_rejects_duplicate_milestone(tmp_path: Path) -> None:
    started = datetime(2026, 6, 5, 12, 30, 0, tzinfo=timezone.utc)
    submitted = datetime(2026, 6, 5, 18, 0, 0, tzinfo=timezone.utc)
    dup = (
        NotificationMilestone(
            milestone="early_warning_24h",
            clock_started_at=started,
            submitted_at=submitted,
        ),
        NotificationMilestone(
            milestone="early_warning_24h",
            clock_started_at=started,
            submitted_at=submitted,
        ),
    )
    with pytest.raises(ValueError):
        emit_incidents_artifact(_ctx(notification_timeline=dup), tmp_path)


def test_emit_rejects_naive_captured_at(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_incidents_artifact(
            _ctx(captured_at=datetime(2026, 6, 6, 9, 0, 0)),
            tmp_path,
        )


def test_emit_rejects_naive_detected_at(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_incidents_artifact(
            _ctx(lifecycle=Lifecycle(detected_at=datetime(2026, 6, 5, 12, 30, 0))),
            tmp_path,
        )


def test_emit_rejects_bad_severity(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_incidents_artifact(
            _ctx(
                classification=ClassificationVerdict(
                    significant=True,
                    cross_border=False,
                    severity="catastrophic",
                )
            ),
            tmp_path,
        )


def test_emit_rejects_bad_owner_assigned_at(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_incidents_artifact(
            _ctx(owner_assigned_at="2026/06/05"),
            tmp_path,
        )


def test_temporal_activity_wraps_shared_helper(tmp_path: Path) -> None:
    """Happy-path Temporal pin required by the F-CP-02 EMITTER SKELETON card.

    The activity-level test asserts one well-formed incidents evidence
    record is emitted per workflow execution by exercising the
    Temporal-side wrapper end-to-end.
    """
    # Import lazily so the rest of the test module still runs in environments
    # without temporalio installed.
    pytest.importorskip("temporalio")
    from compilers.temporal.evidence import emit_incidents_artifact_activity

    ctx = _ctx()
    # ``@activity.defn`` returns the original async callable, so the
    # function is awaitable directly without unwrapping.
    written_str = asyncio.run(
        emit_incidents_artifact_activity(ctx, str(tmp_path))
    )
    written = Path(written_str)
    assert written.exists()
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_incidents_artifact(ctx)
    # One artifact per workflow execution — directory has exactly one
    # record file (ignoring the atomic-write tempfile, which os.replace
    # removes on success).
    written_files = [p for p in Path(tmp_path).iterdir() if p.suffix == ".json"]
    assert len(written_files) == 1
    assert written_files[0].name == f"{on_disk['artifact_id']}.json"


def _payload_from_ctx(ctx: IncidentsContext) -> dict:
    """Re-shape a context as the JSON-native payload an n8n node sends.

    n8n cannot transport Python objects across the node-process boundary,
    so datetimes arrive as ISO-8601 strings and nested dataclasses arrive
    as JSON objects / arrays. We mirror the on-the-wire shape here so
    the adapter exercises the same parse path an operator would hit in
    production.
    """
    cls = ctx.classification
    classification: dict = {
        "significant": cls.significant,
        "cross_border": cls.cross_border,
        "reasons": list(cls.reasons),
        "rule_ids": list(cls.rule_ids),
    }
    if cls.severity is not None:
        classification["severity"] = cls.severity
    if cls.summary is not None:
        classification["summary"] = cls.summary

    lc = ctx.lifecycle
    lifecycle: dict = {
        "detected_at": lc.detected_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    for name in (
        "first_observation_at",
        "triaged_at",
        "contained_at",
        "eradicated_at",
        "recovered_at",
        "closed_at",
    ):
        value = getattr(lc, name)
        if value is not None:
            lifecycle[name] = value.strftime("%Y-%m-%dT%H:%M:%SZ")

    payload: dict = {
        "incident_id": ctx.incident_id,
        "execution_id": ctx.execution_id,
        "regulation_refs": list(ctx.regulation_refs),
        "control_refs": list(ctx.control_refs),
        "classification": classification,
        "lifecycle": lifecycle,
        "owner_role": ctx.owner_role,
        "owner_assigned_at": ctx.owner_assigned_at,
        "captured_at": ctx.captured_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_url": ctx.source_url,
    }
    if ctx.commit_sha:
        payload["commit_sha"] = ctx.commit_sha
    if ctx.retention:
        payload["retention"] = ctx.retention
    if ctx.notification_timeline:
        payload["notification_timeline"] = []
        for m in ctx.notification_timeline:
            entry: dict = {
                "milestone": m.milestone,
                "clock_started_at": m.clock_started_at.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "submitted_at": m.submitted_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            if m.submission_ref is not None:
                entry["submission_ref"] = m.submission_ref
            if m.on_time is not None:
                entry["on_time"] = m.on_time
            payload["notification_timeline"].append(entry)
    if ctx.kpi_windows is not None:
        kw = ctx.kpi_windows
        windows: dict = {}
        if kw.mttd_minutes is not None:
            windows["mttd_minutes"] = kw.mttd_minutes
        if kw.mttr_minutes is not None:
            windows["mttr_minutes"] = kw.mttr_minutes
        if kw.containment_window_minutes is not None:
            windows["containment_window_minutes"] = kw.containment_window_minutes
        if kw.eradication_window_minutes is not None:
            windows["eradication_window_minutes"] = kw.eradication_window_minutes
        if windows:
            payload["kpi_windows"] = windows
    return payload


def test_n8n_adapter_wraps_shared_helper(tmp_path: Path) -> None:
    from compilers.n8n.evidence import emit_incidents_artifact_n8n

    ctx = _ctx()
    result = emit_incidents_artifact_n8n(_payload_from_ctx(ctx), tmp_path)
    written = Path(result["artifact_path"])
    assert written.exists()
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_incidents_artifact(ctx)
    assert result["artifact_id"] == on_disk["artifact_id"]
    assert written.name == f"{on_disk['artifact_id']}.json"
    # One artifact per workflow execution.
    written_files = [p for p in Path(tmp_path).iterdir() if p.suffix == ".json"]
    assert len(written_files) == 1


def test_langgraph_node_wraps_shared_helper(tmp_path: Path) -> None:
    from compilers.langgraph.evidence import emit_incidents_artifact_node

    ctx = _ctx()
    state = {
        "incidents_context": ctx,
        "evidence_output_dir": str(tmp_path),
    }
    update = emit_incidents_artifact_node(state)
    written = Path(update["incidents_artifact_path"])
    assert written.exists()
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_incidents_artifact(ctx)
    assert update["incidents_artifact_id"] == on_disk["artifact_id"]
    # One artifact per workflow execution.
    written_files = [p for p in Path(tmp_path).iterdir() if p.suffix == ".json"]
    assert len(written_files) == 1


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
    from compilers.temporal.evidence import emit_incidents_artifact_activity
    from compilers.n8n.evidence import emit_incidents_artifact_n8n
    from compilers.langgraph.evidence import emit_incidents_artifact_node

    ctx = _ctx()

    tmp_temporal = tmp_path / "temporal"
    tmp_n8n = tmp_path / "n8n"
    tmp_langgraph = tmp_path / "langgraph"

    temporal_path = Path(
        asyncio.run(emit_incidents_artifact_activity(ctx, str(tmp_temporal)))
    )
    n8n_result = emit_incidents_artifact_n8n(_payload_from_ctx(ctx), tmp_n8n)
    n8n_path = Path(n8n_result["artifact_path"])
    langgraph_update = emit_incidents_artifact_node(
        {
            "incidents_context": ctx,
            "evidence_output_dir": str(tmp_langgraph),
        }
    )
    langgraph_path = Path(langgraph_update["incidents_artifact_path"])

    # Same artifact_id across all three targets.
    assert temporal_path.stem == n8n_path.stem == langgraph_path.stem

    # Byte-identical on-disk JSON.
    bytes_temporal = temporal_path.read_bytes()
    bytes_n8n = n8n_path.read_bytes()
    bytes_langgraph = langgraph_path.read_bytes()
    assert bytes_temporal == bytes_n8n == bytes_langgraph
