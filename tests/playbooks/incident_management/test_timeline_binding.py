"""Unit tests for the F-PT-02 incident-timeline binding adapter."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from content.playbooks.incident_management.primitives import (
    timeline_binding as tb,
)


UTC = timezone.utc
INCIDENT_ID = UUID("22222222-2222-4222-8222-222222222222")
OPENED = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)


class TestBindingStatus:
    def test_adapter_status_until_pattern_lands(self) -> None:
        # The gap inventory § 4 q.1 mitigation: adapter today, real
        # pattern when ``patterns/incident_timeline/`` lands on main.
        assert tb.PT02_BINDING_STATUS == "adapter"


class TestOpenTimeline:
    def test_returns_session_with_handle_and_open_event(self) -> None:
        s = tb.open_timeline(incident_id=INCIDENT_ID, opened_at=OPENED)
        assert s.handle.startswith("incident-timeline/")
        assert s.incident_id == INCIDENT_ID
        assert s.opened_at == OPENED
        assert s.closed_at is None
        assert len(s.events) == 1
        assert s.events[0].stage == "timeline_open"

    def test_open_is_deterministic(self) -> None:
        a = tb.open_timeline(incident_id=INCIDENT_ID, opened_at=OPENED)
        b = tb.open_timeline(incident_id=INCIDENT_ID, opened_at=OPENED)
        assert a.handle == b.handle

    def test_open_rejects_naive_datetime(self) -> None:
        with pytest.raises(ValueError, match="timezone-aware"):
            tb.open_timeline(
                incident_id=INCIDENT_ID, opened_at=datetime(2026, 1, 1)
            )

    def test_open_rejects_non_uuid_incident_id(self) -> None:
        with pytest.raises(TypeError, match="UUID"):
            tb.open_timeline(
                incident_id="not-a-uuid",  # type: ignore[arg-type]
                opened_at=OPENED,
            )


class TestRecordEvent:
    def test_appends_event_per_stage(self) -> None:
        s = tb.open_timeline(incident_id=INCIDENT_ID, opened_at=OPENED)
        e1 = tb.record_event(
            s,
            stage="early_warning",
            occurred_at=OPENED + timedelta(hours=12),
            summary="early warning submitted",
            payload_digest="aaaaaaaaaaaaaaaa",
        )
        e2 = tb.record_event(
            s,
            stage="notification",
            occurred_at=OPENED + timedelta(hours=48),
            summary="72h notification submitted",
            payload_digest="bbbbbbbbbbbbbbbb",
        )
        assert s.events[1] is e1
        assert s.events[2] is e2
        assert e1.stage == "early_warning"
        assert e2.stage == "notification"

    def test_unknown_stage_rejected(self) -> None:
        s = tb.open_timeline(incident_id=INCIDENT_ID, opened_at=OPENED)
        with pytest.raises(ValueError, match="unknown stage"):
            tb.record_event(
                s,
                stage="bogus",  # type: ignore[arg-type]
                occurred_at=OPENED + timedelta(hours=1),
                summary="x",
                payload_digest="x",
            )

    def test_closed_timeline_rejects_event(self) -> None:
        s = tb.open_timeline(incident_id=INCIDENT_ID, opened_at=OPENED)
        tb.close_timeline(s, closed_at=OPENED + timedelta(days=30))
        with pytest.raises(ValueError, match="already closed"):
            tb.record_event(
                s,
                stage="early_warning",
                occurred_at=OPENED + timedelta(days=31),
                summary="x",
                payload_digest="x",
            )

    def test_event_id_changes_per_input(self) -> None:
        s = tb.open_timeline(incident_id=INCIDENT_ID, opened_at=OPENED)
        e1 = tb.record_event(
            s,
            stage="early_warning",
            occurred_at=OPENED + timedelta(hours=1),
            summary="x",
            payload_digest="x",
        )
        e2 = tb.record_event(
            s,
            stage="early_warning",
            occurred_at=OPENED + timedelta(hours=2),
            summary="x",
            payload_digest="x",
        )
        assert e1.event_id != e2.event_id


class TestCloseTimeline:
    def test_returns_closure_with_artefact_path(self) -> None:
        s = tb.open_timeline(incident_id=INCIDENT_ID, opened_at=OPENED)
        c = tb.close_timeline(s, closed_at=OPENED + timedelta(days=30))
        assert c.incident_id == INCIDENT_ID
        assert c.handle == s.handle
        assert c.artefact_path == (
            f"content/evidence/incidents/{INCIDENT_ID}/timeline.json"
        )
        assert c.binding_status == "adapter"
        assert c.event_count == len(s.events)

    def test_double_close_rejected(self) -> None:
        s = tb.open_timeline(incident_id=INCIDENT_ID, opened_at=OPENED)
        tb.close_timeline(s, closed_at=OPENED + timedelta(days=30))
        with pytest.raises(ValueError, match="already closed"):
            tb.close_timeline(s, closed_at=OPENED + timedelta(days=31))

    def test_close_appends_close_event(self) -> None:
        s = tb.open_timeline(incident_id=INCIDENT_ID, opened_at=OPENED)
        tb.close_timeline(s, closed_at=OPENED + timedelta(days=30))
        assert s.events[-1].stage == "timeline_close"


class TestArtefactPath:
    def test_path_uses_forward_slash(self) -> None:
        p = tb.timeline_artefact_path(INCIDENT_ID)
        assert "/" in p
        assert "\\" not in p
        assert str(INCIDENT_ID) in p
        assert p.endswith("/timeline.json")
