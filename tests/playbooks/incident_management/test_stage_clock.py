"""Unit tests for the NIS2 Article 23 stage-clock primitive.

The clock is deterministic: stage + opened_at + submitted_at → an
on-time / overdue verdict with a digest. Tests pin every public
helper in isolation, then exercise edge cases (timezone enforcement,
overrun arithmetic, replay-vs-original digest stability).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from content.playbooks.incident_management.primitives import stage_clock


UTC = timezone.utc
OPENED = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)


class TestStageDurations:
    def test_alphabet_is_three_stages_in_order(self) -> None:
        assert stage_clock.stages_in_order() == (
            "early_warning",
            "notification",
            "final_report",
        )

    def test_early_warning_is_24_hours(self) -> None:
        assert stage_clock.STAGE_DURATIONS["early_warning"] == timedelta(hours=24)

    def test_notification_is_72_hours(self) -> None:
        assert stage_clock.STAGE_DURATIONS["notification"] == timedelta(hours=72)

    def test_final_report_is_30_days(self) -> None:
        assert stage_clock.STAGE_DURATIONS["final_report"] == timedelta(days=30)


class TestDueAt:
    @pytest.mark.parametrize(
        "stage,offset",
        [
            ("early_warning", timedelta(hours=24)),
            ("notification", timedelta(hours=72)),
            ("final_report", timedelta(days=30)),
        ],
    )
    def test_due_at_matches_stage_offset(
        self, stage: str, offset: timedelta
    ) -> None:
        assert (
            stage_clock.due_at(opened_at=OPENED, stage=stage)  # type: ignore[arg-type]
            == OPENED + offset
        )

    def test_unknown_stage_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="unknown stage"):
            stage_clock.due_at(opened_at=OPENED, stage="bogus")  # type: ignore[arg-type]

    def test_naive_opened_at_rejected(self) -> None:
        with pytest.raises(ValueError, match="timezone-aware"):
            stage_clock.due_at(
                opened_at=datetime(2026, 1, 1),
                stage="early_warning",
            )

    def test_non_utc_offset_normalised_to_utc(self) -> None:
        # 02:00+02:00 == 00:00 UTC; due_at must reflect the canonical
        # instant regardless of the carrying offset.
        offset_tz = timezone(timedelta(hours=2))
        opened = datetime(2026, 1, 1, 2, 0, tzinfo=offset_tz)
        due = stage_clock.due_at(opened_at=opened, stage="early_warning")
        assert due == OPENED + timedelta(hours=24)
        assert due.tzinfo == UTC


class TestStageWindow:
    def test_stage_window_round_trips(self) -> None:
        w = stage_clock.stage_window(
            opened_at=OPENED, stage="notification"
        )
        assert w.stage == "notification"
        assert w.opened_at == OPENED
        assert w.due_at == OPENED + timedelta(hours=72)
        assert w.duration == timedelta(hours=72)

    def test_stage_window_is_frozen(self) -> None:
        w = stage_clock.stage_window(opened_at=OPENED, stage="early_warning")
        with pytest.raises((AttributeError, Exception)):
            w.stage = "notification"  # type: ignore[misc]


class TestStageBudget:
    def test_remaining_positive_when_pre_deadline(self) -> None:
        b = stage_clock.stage_budget(
            opened_at=OPENED,
            stage="early_warning",
            now=OPENED + timedelta(hours=6),
        )
        assert b.remaining == timedelta(hours=18)
        assert b.is_overdue is False

    def test_overdue_when_past_deadline(self) -> None:
        b = stage_clock.stage_budget(
            opened_at=OPENED,
            stage="early_warning",
            now=OPENED + timedelta(hours=25),
        )
        assert b.remaining == -timedelta(hours=1)
        assert b.is_overdue is True

    def test_overdue_at_exact_deadline(self) -> None:
        # remaining=0 is non-positive → overdue, by design — the
        # window closes the instant it elapses.
        b = stage_clock.stage_budget(
            opened_at=OPENED,
            stage="notification",
            now=OPENED + timedelta(hours=72),
        )
        assert b.remaining == timedelta(0)
        assert b.is_overdue is True


class TestVerdict:
    def test_on_time_when_within_window(self) -> None:
        v = stage_clock.verdict_for_submission(
            stage="early_warning",
            opened_at=OPENED,
            submitted_at=OPENED + timedelta(hours=20),
        )
        assert v.on_time is True
        assert v.slack == timedelta(hours=4)

    def test_overdue_when_past_window(self) -> None:
        v = stage_clock.verdict_for_submission(
            stage="early_warning",
            opened_at=OPENED,
            submitted_at=OPENED + timedelta(hours=25),
        )
        assert v.on_time is False
        assert v.slack == -timedelta(hours=1)

    def test_on_time_exactly_at_deadline(self) -> None:
        # submitted_at == due_at: the regulator gets the submission in
        # the same instant the window closes — on time.
        v = stage_clock.verdict_for_submission(
            stage="notification",
            opened_at=OPENED,
            submitted_at=OPENED + timedelta(hours=72),
        )
        assert v.on_time is True
        assert v.slack == timedelta(0)

    def test_digest_stable_across_calls(self) -> None:
        # Same input → same digest. Replay-vs-original is a single
        # string-equal check.
        kw = dict(
            stage="final_report",
            opened_at=OPENED,
            submitted_at=OPENED + timedelta(days=29),
        )
        a = stage_clock.verdict_for_submission(**kw)
        b = stage_clock.verdict_for_submission(**kw)
        assert a.inputs_digest == b.inputs_digest
        assert a == b

    def test_digest_changes_when_input_changes(self) -> None:
        a = stage_clock.verdict_for_submission(
            stage="early_warning",
            opened_at=OPENED,
            submitted_at=OPENED + timedelta(hours=1),
        )
        b = stage_clock.verdict_for_submission(
            stage="early_warning",
            opened_at=OPENED,
            submitted_at=OPENED + timedelta(hours=2),
        )
        assert a.inputs_digest != b.inputs_digest

    def test_digest_invariant_under_equivalent_tz(self) -> None:
        # Same instant carried in a different offset must yield the
        # same digest (canonical-UTC normalisation).
        offset_tz = timezone(timedelta(hours=5))
        a = stage_clock.verdict_for_submission(
            stage="early_warning",
            opened_at=OPENED,
            submitted_at=OPENED + timedelta(hours=10),
        )
        b = stage_clock.verdict_for_submission(
            stage="early_warning",
            opened_at=datetime(2026, 1, 1, 5, 0, tzinfo=offset_tz),
            submitted_at=datetime(2026, 1, 1, 15, 0, tzinfo=offset_tz),
        )
        assert a.inputs_digest == b.inputs_digest
        assert a.on_time == b.on_time
        assert a.slack == b.slack

    def test_unknown_stage_rejected(self) -> None:
        with pytest.raises(ValueError, match="unknown stage"):
            stage_clock.verdict_for_submission(
                stage="bogus",  # type: ignore[arg-type]
                opened_at=OPENED,
                submitted_at=OPENED,
            )

    def test_naive_submitted_at_rejected(self) -> None:
        with pytest.raises(ValueError, match="timezone-aware"):
            stage_clock.verdict_for_submission(
                stage="early_warning",
                opened_at=OPENED,
                submitted_at=datetime(2026, 1, 1, 1, 0),
            )

    def test_non_datetime_rejected(self) -> None:
        with pytest.raises(TypeError):
            stage_clock.verdict_for_submission(
                stage="early_warning",
                opened_at=OPENED,
                submitted_at="2026-01-01T01:00:00Z",  # type: ignore[arg-type]
            )

    def test_reasons_carry_stage_and_window(self) -> None:
        v = stage_clock.verdict_for_submission(
            stage="early_warning",
            opened_at=OPENED,
            submitted_at=OPENED + timedelta(hours=5),
        )
        joined = " ".join(v.reasons)
        assert "stage=early_warning" in joined
        assert "on_time=true" in joined


class TestElapsed:
    def test_elapsed_returns_positive_delta_forward(self) -> None:
        e = stage_clock.elapsed(
            opened_at=OPENED, now=OPENED + timedelta(hours=3)
        )
        assert e == timedelta(hours=3)

    def test_elapsed_returns_negative_when_backwards(self) -> None:
        e = stage_clock.elapsed(
            opened_at=OPENED, now=OPENED - timedelta(minutes=1)
        )
        assert e == -timedelta(minutes=1)
