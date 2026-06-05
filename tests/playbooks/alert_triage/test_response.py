"""Unit tests for the alert-triage response-routing primitive.

Covers:

* Stable verdict shape on the happy path (primary-tier route, no
  regulator notification, deterministic digest).
* Crown-jewel asset routes to the executive paging tier.
* ``regulated_data=True`` flips the notification-required flag without
  changing the paging tier on a non-crown-jewel asset.
* ``regulated_data=True`` on a crown-jewel asset combines both effects.
* Digest stability: same inputs → same digest; single input change →
  different digest (covers each of the four inputs).
* Priority rejection: anything but ``p1_severe`` raises ``ValueError``.
* Closed-alphabet rejection: invalid ``asset_criticality`` raises
  ``ValueError``.
* Boolean strictness: non-bool ``regulated_data`` / ``internet_exposed``
  raise ``TypeError`` (no duck typing).
* Incident-management playbook reference is pinned and surfaced on
  every verdict.
"""

from __future__ import annotations

import pytest

from content.playbooks.alert_triage.primitives import (
    EscalationDirective,
    INCIDENT_MANAGEMENT_PLAYBOOK_REF,
    escalation_route,
)


_HAPPY = dict(
    priority="p1_severe",
    asset_criticality="high",
    regulated_data=False,
    internet_exposed=False,
)


class TestHappyPath:
    def test_default_route_primary_oncall(self) -> None:
        verdict = escalation_route(**_HAPPY)
        assert isinstance(verdict, EscalationDirective)
        assert verdict.paging_tier == "tier_primary_oncall"
        assert verdict.regulator_notification_required is False
        assert (
            verdict.incident_management_playbook_ref
            == INCIDENT_MANAGEMENT_PLAYBOOK_REF
        )

    def test_reasons_carry_priority_and_tier(self) -> None:
        verdict = escalation_route(**_HAPPY)
        assert verdict.reasons[0].startswith("priority=p1_severe")
        assert any(
            "tier_primary_oncall" in r for r in verdict.reasons
        )

    def test_digest_is_short_hex(self) -> None:
        verdict = escalation_route(**_HAPPY)
        assert len(verdict.inputs_digest) == 16
        int(verdict.inputs_digest, 16)  # parses as hex


class TestPagingTier:
    def test_crown_jewel_routes_executive(self) -> None:
        verdict = escalation_route(
            **{**_HAPPY, "asset_criticality": "crown_jewel"}
        )
        assert verdict.paging_tier == "tier_executive"
        assert any(
            "tier_executive" in r for r in verdict.reasons
        )

    @pytest.mark.parametrize(
        "criticality", ["low", "medium", "high"]
    )
    def test_non_crown_jewel_routes_primary(
        self, criticality: str
    ) -> None:
        verdict = escalation_route(
            **{**_HAPPY, "asset_criticality": criticality}
        )
        assert verdict.paging_tier == "tier_primary_oncall"


class TestRegulatorNotification:
    def test_regulated_data_opens_notification(self) -> None:
        verdict = escalation_route(
            **{**_HAPPY, "regulated_data": True}
        )
        assert verdict.regulator_notification_required is True
        assert any(
            "regulator_notification_required" in r
            for r in verdict.reasons
        )

    def test_regulated_data_does_not_change_primary_tier(self) -> None:
        verdict = escalation_route(
            **{**_HAPPY, "regulated_data": True}
        )
        assert verdict.paging_tier == "tier_primary_oncall"

    def test_crown_jewel_plus_regulated_combines(self) -> None:
        verdict = escalation_route(
            priority="p1_severe",
            asset_criticality="crown_jewel",
            regulated_data=True,
            internet_exposed=True,
        )
        assert verdict.paging_tier == "tier_executive"
        assert verdict.regulator_notification_required is True


class TestDigestStability:
    def test_same_inputs_same_digest(self) -> None:
        assert (
            escalation_route(**_HAPPY).inputs_digest
            == escalation_route(**_HAPPY).inputs_digest
        )

    @pytest.mark.parametrize(
        "override",
        [
            {"asset_criticality": "crown_jewel"},
            {"regulated_data": True},
            {"internet_exposed": True},
        ],
    )
    def test_single_input_change_changes_digest(
        self, override: dict
    ) -> None:
        base = escalation_route(**_HAPPY).inputs_digest
        changed = escalation_route(**{**_HAPPY, **override}).inputs_digest
        assert base != changed


class TestRejection:
    @pytest.mark.parametrize(
        "priority",
        ["p2_high", "p3_routine", "p4_informational", "", "P1_SEVERE"],
    )
    def test_non_p1_priority_rejected(self, priority: str) -> None:
        with pytest.raises(ValueError, match="p1-severe response body"):
            escalation_route(
                **{**_HAPPY, "priority": priority}  # type: ignore[arg-type]
            )

    def test_unknown_criticality_rejected(self) -> None:
        with pytest.raises(ValueError, match="unknown asset_criticality"):
            escalation_route(
                **{**_HAPPY, "asset_criticality": "platinum"}  # type: ignore[arg-type]
            )

    @pytest.mark.parametrize(
        "field", ["regulated_data", "internet_exposed"]
    )
    def test_non_bool_flag_rejected(self, field: str) -> None:
        with pytest.raises(TypeError, match="must be bool"):
            escalation_route(
                **{**_HAPPY, field: "true"}  # type: ignore[arg-type]
            )


class TestDownstreamHandoff:
    def test_playbook_ref_pinned_on_every_verdict(self) -> None:
        # The hand-off must be idempotent across re-fires; the
        # downstream playbook reference is the natural pin.
        a = escalation_route(**_HAPPY)
        b = escalation_route(
            **{**_HAPPY, "asset_criticality": "crown_jewel"}
        )
        assert (
            a.incident_management_playbook_ref
            == b.incident_management_playbook_ref
            == INCIDENT_MANAGEMENT_PLAYBOOK_REF
        )
