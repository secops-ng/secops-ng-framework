"""Unit tests for the regulator-submission contract.

Three frozen Pydantic v2 payloads + a destination-resolution helper
that fails closed when the operator has not wired a destination —
the framework ships NO default endpoint.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from content.playbooks.incident_management.primitives import (
    regulator_submission as rs,
)


UTC = timezone.utc
INCIDENT_ID = UUID("11111111-1111-4111-8111-111111111111")
OPENED = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)


def _common_kwargs() -> dict:
    return dict(
        incident_id=INCIDENT_ID,
        timeline_handle="incident-timeline/abc123",
        significant=True,
        cross_border=False,
        opened_at=OPENED,
    )


class TestEarlyWarning:
    def test_constructs_with_minimal_fields(self) -> None:
        msg = rs.EarlyWarningSubmission(
            suspected_malicious=True,
            suspected_cross_border_impact=False,
            **_common_kwargs(),
        )
        assert msg.stage == "early_warning"
        assert msg.incident_id == INCIDENT_ID

    def test_rejects_extra_field(self) -> None:
        with pytest.raises(ValidationError):
            rs.EarlyWarningSubmission(
                suspected_malicious=True,
                suspected_cross_border_impact=False,
                bogus=True,  # type: ignore[call-arg]
                **_common_kwargs(),
            )

    def test_naive_opened_at_rejected(self) -> None:
        kw = _common_kwargs()
        kw["opened_at"] = datetime(2026, 1, 1)
        with pytest.raises(ValidationError, match="timezone-aware"):
            rs.EarlyWarningSubmission(
                suspected_malicious=False,
                suspected_cross_border_impact=False,
                **kw,
            )

    def test_frozen(self) -> None:
        msg = rs.EarlyWarningSubmission(
            suspected_malicious=False,
            suspected_cross_border_impact=False,
            **_common_kwargs(),
        )
        with pytest.raises(ValidationError):
            msg.significant = False  # type: ignore[misc]


class TestNotification:
    def test_constructs_with_iocs(self) -> None:
        msg = rs.NotificationSubmission(
            severity_assessment="major",
            impact_assessment="service interruption for region eu-west",
            indicators_of_compromise=("hash:abc", "ip:10.0.0.1"),
            **_common_kwargs(),
        )
        assert msg.stage == "notification"
        assert msg.indicators_of_compromise == ("hash:abc", "ip:10.0.0.1")

    def test_iocs_default_empty(self) -> None:
        msg = rs.NotificationSubmission(
            severity_assessment="minor",
            impact_assessment="degraded throughput",
            **_common_kwargs(),
        )
        assert msg.indicators_of_compromise == ()

    def test_empty_string_rejected(self) -> None:
        with pytest.raises(ValidationError):
            rs.NotificationSubmission(
                severity_assessment="",
                impact_assessment="x",
                **_common_kwargs(),
            )


class TestFinalReport:
    def test_constructs_with_narrative_fields(self) -> None:
        msg = rs.FinalReportSubmission(
            narrative="What happened, in order.",
            root_cause="Misconfigured ingress accepted an unsigned token.",
            applied_mitigations="Rotated keys; pinned issuer; added a test.",
            **_common_kwargs(),
        )
        assert msg.stage == "final_report"
        assert msg.cross_border_impact_summary is None

    def test_cross_border_summary_optional(self) -> None:
        msg = rs.FinalReportSubmission(
            narrative="x",
            root_cause="y",
            applied_mitigations="z",
            cross_border_impact_summary="Affected DE and FR users.",
            **_common_kwargs(),
        )
        assert msg.cross_border_impact_summary == "Affected DE and FR users."


class TestResolveDestination:
    def test_returns_handle_when_present(self) -> None:
        dests = {
            "early_warning": "n8n:credential-id-1",
            "notification": "temporal:env-var-2",
            "final_report": "langgraph:config-3",
        }
        assert (
            rs.resolve_destination(dests, stage="early_warning")
            == "n8n:credential-id-1"
        )

    def test_strips_whitespace(self) -> None:
        assert (
            rs.resolve_destination(
                {"early_warning": "  abc  "}, stage="early_warning"
            )
            == "abc"
        )

    def test_missing_stage_raises(self) -> None:
        with pytest.raises(rs.MissingDestinationError, match="no destination"):
            rs.resolve_destination({}, stage="early_warning")

    def test_none_destination_raises(self) -> None:
        with pytest.raises(rs.MissingDestinationError, match="None"):
            rs.resolve_destination(
                {"early_warning": None}, stage="early_warning"
            )

    def test_empty_destination_raises(self) -> None:
        with pytest.raises(rs.MissingDestinationError, match="empty"):
            rs.resolve_destination(
                {"early_warning": "   "}, stage="early_warning"
            )

    def test_non_string_destination_raises(self) -> None:
        with pytest.raises(rs.MissingDestinationError, match="string"):
            rs.resolve_destination(
                {"early_warning": 1234}, stage="early_warning"
            )

    def test_non_mapping_destinations_raises(self) -> None:
        with pytest.raises(rs.MissingDestinationError, match="mapping"):
            rs.resolve_destination(
                "not a mapping",  # type: ignore[arg-type]
                stage="early_warning",
            )

    def test_unknown_stage_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="unknown stage"):
            rs.resolve_destination(
                {"early_warning": "x"},
                stage="bogus",  # type: ignore[arg-type]
            )


class TestRegulatorSubmissionStagesAlphabet:
    def test_three_stages_in_order(self) -> None:
        assert rs.REGULATOR_SUBMISSION_STAGES == (
            "early_warning",
            "notification",
            "final_report",
        )


def test_uuid_module_imports() -> None:
    # Defensive — keeps uuid4 import live so future test additions
    # have a generator handle.
    assert isinstance(uuid4(), UUID)
