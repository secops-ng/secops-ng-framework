"""F-CP-02 — incidents evidence-artifact round-trip (SKELETON).

Pins:

1. The shared emitter writes a record that validates against
   ``schemas/evidence/incidents.schema.json`` (with the promoted
   ``nis2_incident_notification_milestone`` schema resolved).
2. The ``artifact_id`` is deterministic on ``(incident_id, execution_id)``
   — same inputs reproduce the same id; different inputs do not.
3. The record persists to disk under ``<output_dir>/<artifact_id>.json``
   and re-reads byte-identical to the rendered record.
4. The Temporal-side activity wrapper delegates to the shared helper
   and produces the same on-disk record for the same context — the
   n8n + LangGraph adapters land in CORE-FANOUT and per-target
   byte-parity goldens land in the EXTEND-tests sibling.

The Temporal happy-path test is the activity-level pin the F-CP-02
EMITTER SKELETON card requires.
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
