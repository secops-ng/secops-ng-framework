"""Unit tests for the four vuln_intake remediation lanes.

Each lane guards its own band, so a mis-wired switch fails loudly instead of
silently downgrading a critical vulnerability into the accept-risk lane. The
band vocabulary is the canonical ``Severity`` alphabet — the same values
``severity_policy`` emits — because the switch keys were previously lower-case
and matched nothing at runtime.

Two policy choices are pinned here because they are the kind a later change
would quietly reverse: the remediation window comes from the operator's CVD
policy rather than a hard-coded default, and a risk acceptance must carry both
a named accepting party and an expiry.
"""
from __future__ import annotations

import pytest

from content.playbooks.vuln_intake.primitives import (
    RemediationDirective,
    accept_risk,
    patch_and_advisory_critical,
    patch_and_advisory_high,
    schedule_remediation,
)

_TRIAGED = "2026-08-03T10:00:00Z"
_C = dict(severity="Critical", asset_criticality="high", triaged_at=_TRIAGED, sla_days=7)
_H = dict(severity="High", asset_criticality="high", triaged_at=_TRIAGED, sla_days=30)
_M = dict(severity="Medium", asset_criticality="low", triaged_at=_TRIAGED, sla_days=90)
_N = dict(severity="None", asset_criticality="low", triaged_at=_TRIAGED,
          accepted_by="sec-lead", review_after_days=90)


class TestCriticalLane:
    def test_happy_path(self) -> None:
        d = patch_and_advisory_critical(**_C)
        assert isinstance(d, RemediationDirective)
        assert d.lane == "patch_and_advisory_immediate"
        assert d.advisory == "advisory_published"
        assert d.remediate_by == "2026-08-10T10:00:00Z"   # +7d
        assert d.review_by is None
        assert len(d.inputs_digest) == 16

    def test_crown_jewel_halves_the_window(self) -> None:
        d = patch_and_advisory_critical(**{**_C, "asset_criticality": "crown_jewel"})
        assert d.remediate_by == "2026-08-07T10:00:00Z"   # 7 -> 4 (ceil)
        assert any("halved" in r for r in d.reasons)

    def test_crown_jewel_window_floors_at_one_day(self) -> None:
        d = patch_and_advisory_critical(
            **{**_C, "asset_criticality": "crown_jewel", "sla_days": 1})
        assert d.remediate_by == "2026-08-04T10:00:00Z"

    def test_directive_is_frozen(self) -> None:
        d = patch_and_advisory_critical(**_C)
        with pytest.raises(AttributeError):
            d.lane = "risk_accepted"  # type: ignore[misc]


class TestHighLane:
    def test_happy_path_window_unchanged(self) -> None:
        d = patch_and_advisory_high(**_H)
        assert d.lane == "patch_and_advisory_scheduled"
        assert d.advisory == "advisory_published"
        assert d.remediate_by == "2026-09-02T10:00:00Z"   # +30d

    def test_crown_jewel_flags_but_does_not_shorten(self) -> None:
        d = patch_and_advisory_high(**{**_H, "asset_criticality": "crown_jewel"})
        assert d.remediate_by == "2026-09-02T10:00:00Z"
        assert any("window unchanged" in r for r in d.reasons)


class TestScheduledLane:
    @pytest.mark.parametrize("band", ["Medium", "Low"])
    def test_both_bands_route_here(self, band: str) -> None:
        d = schedule_remediation(**{**_M, "severity": band})
        assert d.lane == "scheduled_remediation"
        assert d.advisory == "no_advisory"
        # The lane collapses two bands; the audit trail keeps the distinction.
        assert any(f"severity={band}" in r for r in d.reasons)

    @pytest.mark.parametrize("band", ["Critical", "High", "None"])
    def test_other_bands_rejected(self, band: str) -> None:
        with pytest.raises(ValueError, match="Medium/Low response body"):
            schedule_remediation(**{**_M, "severity": band})


class TestAcceptRiskLane:
    def test_happy_path_has_no_remediation_deadline(self) -> None:
        d = accept_risk(**_N)
        assert d.lane == "risk_accepted"
        assert d.remediate_by is None
        assert d.review_by == "2026-11-01T10:00:00Z"   # +90d
        assert any("sec-lead" in r for r in d.reasons)

    def test_unattributed_acceptance_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-empty accepted_by"):
            accept_risk(**{**_N, "accepted_by": "   "})

    @pytest.mark.parametrize("bad", [0, -1])
    def test_non_positive_review_window_rejected(self, bad: int) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            accept_risk(**{**_N, "review_after_days": bad})

    def test_non_int_review_window_rejected(self) -> None:
        with pytest.raises(TypeError, match="must be an int"):
            accept_risk(**{**_N, "review_after_days": "90"})  # type: ignore[arg-type]


class TestBandGuards:
    """A mis-wired switch must fail loudly, never downgrade silently."""

    @pytest.mark.parametrize("band", ["High", "Medium", "Low", "None", "critical", ""])
    def test_critical_lane_rejects_other_bands(self, band: str) -> None:
        with pytest.raises(ValueError, match="'Critical' response body"):
            patch_and_advisory_critical(**{**_C, "severity": band})

    @pytest.mark.parametrize("band", ["Critical", "Medium", "None", "high"])
    def test_high_lane_rejects_other_bands(self, band: str) -> None:
        with pytest.raises(ValueError, match="'High' response body"):
            patch_and_advisory_high(**{**_H, "severity": band})

    @pytest.mark.parametrize("band", ["Critical", "Low", "info"])
    def test_accept_lane_rejects_other_bands(self, band: str) -> None:
        with pytest.raises(ValueError, match="'None' response body"):
            accept_risk(**{**_N, "severity": band})

    def test_lower_case_band_is_rejected_everywhere(self) -> None:
        """The old switch keys were lower-case; they must not silently work."""
        for fn, kwargs in (
            (patch_and_advisory_critical, {**_C, "severity": "critical"}),
            (patch_and_advisory_high, {**_H, "severity": "high"}),
            (accept_risk, {**_N, "severity": "none"}),
        ):
            with pytest.raises(ValueError):
                fn(**kwargs)


class TestSharedValidation:
    @pytest.mark.parametrize("fn,kwargs", [
        (patch_and_advisory_critical, _C),
        (patch_and_advisory_high, _H),
        (schedule_remediation, _M),
    ])
    def test_unknown_criticality_rejected(self, fn, kwargs: dict) -> None:
        with pytest.raises(ValueError, match="unknown asset_criticality"):
            fn(**{**kwargs, "asset_criticality": "platinum"})

    @pytest.mark.parametrize("fn,kwargs", [
        (patch_and_advisory_critical, _C),
        (patch_and_advisory_high, _H),
        (schedule_remediation, _M),
    ])
    def test_naive_triage_timestamp_rejected(self, fn, kwargs: dict) -> None:
        with pytest.raises(ValueError, match="explicit UTC offset"):
            fn(**{**kwargs, "triaged_at": "2026-08-03T10:00:00"})

    @pytest.mark.parametrize("bad", [0, -5])
    def test_non_positive_sla_rejected(self, bad: int) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            patch_and_advisory_critical(**{**_C, "sla_days": bad})

    def test_bool_sla_rejected(self) -> None:
        with pytest.raises(TypeError, match="must be an int"):
            patch_and_advisory_critical(**{**_C, "sla_days": True})


class TestDigests:
    def test_lanes_do_not_collide_on_digest(self) -> None:
        digests = {
            patch_and_advisory_critical(**_C).inputs_digest,
            patch_and_advisory_high(**_H).inputs_digest,
            schedule_remediation(**_M).inputs_digest,
            accept_risk(**_N).inputs_digest,
        }
        assert len(digests) == 4

    @pytest.mark.parametrize("override", [
        {"asset_criticality": "crown_jewel"},
        {"triaged_at": "2026-08-03T11:00:00Z"},
        {"sla_days": 14},
    ])
    def test_single_input_change_changes_digest(self, override: dict) -> None:
        assert (
            patch_and_advisory_critical(**_C).inputs_digest
            != patch_and_advisory_critical(**{**_C, **override}).inputs_digest
        )
