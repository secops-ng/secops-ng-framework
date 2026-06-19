"""Unit tests for the alert_triage prioritisation policy.

The policy is deterministic: detection axis + asset axis + suppression
axis → one of four priority bands. Tests pin every rule in isolation,
then exercise edge cases (informational sink, never-lower invariant,
regulated-data floor, inputs-digest stability across replays, closed
alphabet rejection).
"""

from __future__ import annotations

import pytest

from content.playbooks.alert_triage.primitives import (
    AssetContext,
    PriorityVerdict,
    prioritise,
)


def _ctx(
    *,
    asset_criticality: str = "medium",
    internet_exposed: bool = False,
    regulated_data: bool = False,
) -> AssetContext:
    return AssetContext(
        asset_criticality=asset_criticality,  # type: ignore[arg-type]
        internet_exposed=internet_exposed,
        regulated_data=regulated_data,
    )


class TestStartingBand:
    @pytest.mark.parametrize(
        "severity,expected",
        [
            ("low", "p4_informational"),
            ("medium", "p3_routine"),
            ("high", "p2_high"),
            ("critical", "p1_severe"),
        ],
    )
    def test_detection_severity_maps_to_band(
        self, severity: str, expected: str
    ) -> None:
        v = prioritise(
            detection_class="anomaly",
            detection_severity=severity,  # type: ignore[arg-type]
            context=_ctx(),
        )
        assert v.starting_band == expected
        # No context bumps with vanilla medium ctx (no crown_jewel,
        # not internet-exposed, not regulated). Anomaly class adds no
        # floor either, so final == starting.
        assert v.priority == expected


class TestDeterminism:
    def test_same_input_same_output(self) -> None:
        kw = dict(
            detection_class="exploit_attempt",
            detection_severity="high",
            context=_ctx(
                asset_criticality="crown_jewel",
                internet_exposed=True,
                regulated_data=True,
            ),
            correlates_open_case=True,
        )
        a = prioritise(**kw)
        b = prioritise(**kw)
        assert a == b
        assert a.inputs_digest == b.inputs_digest

    def test_inputs_digest_shape(self) -> None:
        v = prioritise(
            detection_class="anomaly",
            detection_severity="medium",
            context=_ctx(),
        )
        assert len(v.inputs_digest) == 16
        assert all(c in "0123456789abcdef" for c in v.inputs_digest)

    def test_inputs_digest_sensitive_to_every_field(self) -> None:
        base = dict(
            detection_class="policy_violation",
            detection_severity="medium",
            context=_ctx(),
            correlates_open_case=False,
        )
        ref = prioritise(**base).inputs_digest

        # Flip detection_class.
        d = prioritise(**{**base, "detection_class": "anomaly"})
        assert d.inputs_digest != ref
        # Flip detection_severity.
        d = prioritise(**{**base, "detection_severity": "high"})
        assert d.inputs_digest != ref
        # Flip crown jewel.
        d = prioritise(
            **{**base, "context": _ctx(asset_criticality="crown_jewel")}
        )
        assert d.inputs_digest != ref
        # Flip exposed.
        d = prioritise(**{**base, "context": _ctx(internet_exposed=True)})
        assert d.inputs_digest != ref
        # Flip regulated.
        d = prioritise(**{**base, "context": _ctx(regulated_data=True)})
        assert d.inputs_digest != ref
        # Flip correlates.
        d = prioritise(**{**base, "correlates_open_case": True})
        assert d.inputs_digest != ref


class TestInformationalSink:
    def test_informational_ignores_context_bumps(self) -> None:
        v = prioritise(
            detection_class="informational",
            detection_severity="critical",
            context=_ctx(
                asset_criticality="crown_jewel",
                internet_exposed=True,
                regulated_data=True,
            ),
            correlates_open_case=True,
        )
        # Sinks to p4 regardless of context — informational detections
        # do not escalate.
        assert v.priority == "p4_informational"
        # Starting band is still recorded for audit.
        assert v.starting_band == "p1_severe"


class TestClassFloor:
    def test_exploit_attempt_floors_at_p2_high(self) -> None:
        v = prioritise(
            detection_class="exploit_attempt",
            detection_severity="low",
            context=_ctx(),
        )
        # Detection severity low → starting p4, but the class floor
        # raises to p2_high before context applies.
        assert v.starting_band == "p4_informational"
        assert v.priority == "p2_high"

    def test_policy_violation_floors_at_p3_routine(self) -> None:
        v = prioritise(
            detection_class="policy_violation",
            detection_severity="low",
            context=_ctx(),
        )
        assert v.priority == "p3_routine"


class TestContextBumps:
    def test_crown_jewel_bumps_one_band(self) -> None:
        v = prioritise(
            detection_class="anomaly",
            detection_severity="medium",
            context=_ctx(asset_criticality="crown_jewel"),
        )
        assert v.priority == "p2_high"  # p3 + 1

    def test_internet_exposed_with_high_severity_bumps(self) -> None:
        v = prioritise(
            detection_class="anomaly",
            detection_severity="high",
            context=_ctx(internet_exposed=True),
        )
        # Anomaly class has no floor effect at p2_high starting; the
        # internet+high bump raises to p1_severe.
        assert v.priority == "p1_severe"

    def test_internet_exposed_with_medium_severity_does_not_bump(self) -> None:
        v = prioritise(
            detection_class="anomaly",
            detection_severity="medium",
            context=_ctx(internet_exposed=True),
        )
        assert v.priority == "p3_routine"

    def test_regulated_data_floors_at_p2_high(self) -> None:
        v = prioritise(
            detection_class="anomaly",
            detection_severity="low",
            context=_ctx(regulated_data=True),
        )
        assert v.priority == "p2_high"

    def test_regulated_data_never_lowers(self) -> None:
        v = prioritise(
            detection_class="exploit_attempt",
            detection_severity="critical",
            context=_ctx(regulated_data=True),
        )
        # p1_severe stays p1_severe — floor never lowers.
        assert v.priority == "p1_severe"

    def test_correlates_open_case_bumps(self) -> None:
        v = prioritise(
            detection_class="anomaly",
            detection_severity="medium",
            context=_ctx(),
            correlates_open_case=True,
        )
        assert v.priority == "p2_high"


class TestCapAndNeverLower:
    def test_cap_at_p1_severe(self) -> None:
        v = prioritise(
            detection_class="exploit_attempt",
            detection_severity="critical",
            context=_ctx(
                asset_criticality="crown_jewel",
                internet_exposed=True,
                regulated_data=True,
            ),
            correlates_open_case=True,
        )
        # All bumps stacked — caps at p1_severe.
        assert v.priority == "p1_severe"

    def test_never_lowers_starting_band(self) -> None:
        # Even with the gentlest context, an exploit_attempt at
        # critical stays at p1_severe.
        v = prioritise(
            detection_class="exploit_attempt",
            detection_severity="critical",
            context=_ctx(),
        )
        assert v.priority == "p1_severe"


class TestRejections:
    def test_bad_context_type_rejected(self) -> None:
        with pytest.raises(TypeError):
            prioritise(
                detection_class="anomaly",
                detection_severity="medium",
                context={"asset_criticality": "medium"},  # type: ignore[arg-type]
            )

    def test_unknown_detection_class_rejected(self) -> None:
        with pytest.raises(ValueError, match="unknown detection_class"):
            prioritise(
                detection_class="phishing",  # type: ignore[arg-type]
                detection_severity="medium",
                context=_ctx(),
            )

    def test_unknown_detection_severity_rejected(self) -> None:
        with pytest.raises(ValueError, match="unknown detection_severity"):
            prioritise(
                detection_class="anomaly",
                detection_severity="warning",  # type: ignore[arg-type]
                context=_ctx(),
            )

    def test_asset_context_extra_field_rejected(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AssetContext(
                asset_criticality="medium",
                internet_exposed=False,
                regulated_data=False,
                phantom_field="x",  # type: ignore[call-arg]
            )

    def test_asset_context_is_frozen(self) -> None:
        from pydantic import ValidationError

        ctx = _ctx()
        with pytest.raises((ValidationError, TypeError)):
            ctx.asset_criticality = "crown_jewel"  # type: ignore[misc]


class TestVerdictShape:
    def test_returns_priority_verdict(self) -> None:
        v = prioritise(
            detection_class="anomaly",
            detection_severity="medium",
            context=_ctx(),
        )
        assert isinstance(v, PriorityVerdict)
        assert v.reasons  # at least the starting-band reason
        assert all(isinstance(r, str) for r in v.reasons)
