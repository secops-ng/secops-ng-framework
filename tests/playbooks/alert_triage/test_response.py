"""Unit tests for the alert_triage response-routing primitives.

Covers all four response bodies on the same input shape:
:func:`escalation_route` (p1 severe), :func:`notify_on_call` (p2 high),
:func:`route_to_review_queue` (p3 routine) and :func:`log_and_close`
(p4 informational).

For ``escalation_route``:

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

For ``notify_on_call``:

* Stable verdict shape on the p2 happy path (primary on-call paging
  cadence, no regulator notification, deterministic digest).
* Non-crown-jewel routes to ``tier_primary_oncall`` /
  ``paging_cadence`` across the low / medium / high band.
* Crown-jewel at p2 routes to ``tier_executive`` /
  ``informational_notice`` — awareness, not page-now.
* ``regulated_data=True`` flips ``regulator_notification_required``
  without changing the routing on either branch.
* Crown-jewel + regulated_data combines both effects.
* Digest stability: same inputs → same digest; single input change
  on any of the four inputs → different digest.
* Priority rejection: p1 / p3 / p4 / empty / wrong-case raise
  ``ValueError`` naming the p2-high contract.
* Closed-alphabet rejection: unknown ``asset_criticality`` raises
  ``ValueError``.
* Boolean strictness: non-bool ``regulated_data`` / ``internet_exposed``
  raise ``TypeError``.
* Incident-management playbook reference is pinned and idempotent
  across re-fires.
"""

from __future__ import annotations

import pytest

from content.playbooks.alert_triage.primitives import (
    EscalationDirective,
    INCIDENT_MANAGEMENT_PLAYBOOK_REF,
    NotificationDirective,
    ClosureRecord,
    ReviewQueueDirective,
    escalation_route,
    log_and_close,
    notify_on_call,
    route_to_review_queue,
)


_HAPPY = dict(
    priority="p1_severe",
    asset_criticality="high",
    regulated_data=False,
    internet_exposed=False,
)

_HAPPY_P2 = dict(
    priority="p2_high",
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


class TestP2HappyPath:
    def test_default_route_primary_oncall_paging_cadence(self) -> None:
        verdict = notify_on_call(**_HAPPY_P2)
        assert isinstance(verdict, NotificationDirective)
        assert verdict.paging_tier == "tier_primary_oncall"
        assert verdict.cadence == "paging_cadence"
        assert verdict.regulator_notification_required is False
        assert (
            verdict.incident_management_playbook_ref
            == INCIDENT_MANAGEMENT_PLAYBOOK_REF
        )

    def test_p2_reasons_carry_priority_and_route(self) -> None:
        verdict = notify_on_call(**_HAPPY_P2)
        assert verdict.reasons[0].startswith("priority=p2_high")
        assert any("paging_cadence" in r for r in verdict.reasons)

    def test_p2_digest_is_short_hex(self) -> None:
        verdict = notify_on_call(**_HAPPY_P2)
        assert len(verdict.inputs_digest) == 16
        int(verdict.inputs_digest, 16)


class TestP2PagingTier:
    def test_crown_jewel_routes_executive_informational(self) -> None:
        verdict = notify_on_call(
            **{**_HAPPY_P2, "asset_criticality": "crown_jewel"}
        )
        assert verdict.paging_tier == "tier_executive"
        assert verdict.cadence == "informational_notice"
        assert any(
            "informational_notice" in r for r in verdict.reasons
        )

    @pytest.mark.parametrize("criticality", ["low", "medium", "high"])
    def test_non_crown_jewel_routes_primary_paging(
        self, criticality: str
    ) -> None:
        verdict = notify_on_call(
            **{**_HAPPY_P2, "asset_criticality": criticality}
        )
        assert verdict.paging_tier == "tier_primary_oncall"
        assert verdict.cadence == "paging_cadence"


class TestP2RegulatorNotification:
    def test_p2_regulated_data_opens_notification(self) -> None:
        verdict = notify_on_call(
            **{**_HAPPY_P2, "regulated_data": True}
        )
        assert verdict.regulator_notification_required is True
        assert any(
            "regulator_notification_required" in r
            for r in verdict.reasons
        )

    def test_p2_regulated_does_not_change_primary_route(self) -> None:
        verdict = notify_on_call(
            **{**_HAPPY_P2, "regulated_data": True}
        )
        assert verdict.paging_tier == "tier_primary_oncall"
        assert verdict.cadence == "paging_cadence"

    def test_p2_crown_jewel_plus_regulated_combines(self) -> None:
        verdict = notify_on_call(
            priority="p2_high",
            asset_criticality="crown_jewel",
            regulated_data=True,
            internet_exposed=True,
        )
        assert verdict.paging_tier == "tier_executive"
        assert verdict.cadence == "informational_notice"
        assert verdict.regulator_notification_required is True


class TestP2DigestStability:
    def test_p2_same_inputs_same_digest(self) -> None:
        assert (
            notify_on_call(**_HAPPY_P2).inputs_digest
            == notify_on_call(**_HAPPY_P2).inputs_digest
        )

    @pytest.mark.parametrize(
        "override",
        [
            {"asset_criticality": "crown_jewel"},
            {"regulated_data": True},
            {"internet_exposed": True},
        ],
    )
    def test_p2_single_input_change_changes_digest(
        self, override: dict
    ) -> None:
        base = notify_on_call(**_HAPPY_P2).inputs_digest
        changed = notify_on_call(**{**_HAPPY_P2, **override}).inputs_digest
        assert base != changed

    def test_p1_and_p2_digests_differ_on_priority(self) -> None:
        # The priority itself is part of the canonical inputs digest;
        # the p1 verdict and the p2 verdict for the same asset must
        # not collide on the digest field.
        p1 = escalation_route(**_HAPPY)
        p2 = notify_on_call(**_HAPPY_P2)
        assert p1.inputs_digest != p2.inputs_digest


class TestP2Rejection:
    @pytest.mark.parametrize(
        "priority",
        ["p1_severe", "p3_routine", "p4_informational", "", "P2_HIGH"],
    )
    def test_non_p2_priority_rejected(self, priority: str) -> None:
        with pytest.raises(ValueError, match="p2-high response body"):
            notify_on_call(
                **{**_HAPPY_P2, "priority": priority}  # type: ignore[arg-type]
            )

    def test_p2_unknown_criticality_rejected(self) -> None:
        with pytest.raises(ValueError, match="unknown asset_criticality"):
            notify_on_call(
                **{**_HAPPY_P2, "asset_criticality": "platinum"}  # type: ignore[arg-type]
            )

    @pytest.mark.parametrize(
        "field", ["regulated_data", "internet_exposed"]
    )
    def test_p2_non_bool_flag_rejected(self, field: str) -> None:
        with pytest.raises(TypeError, match="must be bool"):
            notify_on_call(
                **{**_HAPPY_P2, field: "true"}  # type: ignore[arg-type]
            )


class TestP2DownstreamHandoff:
    def test_p2_playbook_ref_pinned_on_every_verdict(self) -> None:
        a = notify_on_call(**_HAPPY_P2)
        b = notify_on_call(
            **{**_HAPPY_P2, "asset_criticality": "crown_jewel"}
        )
        assert (
            a.incident_management_playbook_ref
            == b.incident_management_playbook_ref
            == INCIDENT_MANAGEMENT_PLAYBOOK_REF
        )


_HAPPY_P3 = dict(
    priority="p3_routine",
    asset_criticality="high",
    regulated_data=False,
    internet_exposed=False,
)


class TestP3HappyPath:
    def test_default_route_tier_queue_standard_sla(self) -> None:
        verdict = route_to_review_queue(**_HAPPY_P3)
        assert isinstance(verdict, ReviewQueueDirective)
        assert verdict.review_tier == "tier_queue"
        assert verdict.cadence == "review_queue_standard_sla"
        assert verdict.regulator_notification_required is False
        assert (
            verdict.incident_management_playbook_ref
            == INCIDENT_MANAGEMENT_PLAYBOOK_REF
        )

    def test_p3_reasons_carry_priority_and_route(self) -> None:
        verdict = route_to_review_queue(**_HAPPY_P3)
        assert verdict.reasons[0].startswith("priority=p3_routine")
        assert any("tier_queue" in r for r in verdict.reasons)
        assert any(
            "review_queue_standard_sla" in r for r in verdict.reasons
        )

    def test_p3_digest_is_short_hex(self) -> None:
        verdict = route_to_review_queue(**_HAPPY_P3)
        assert len(verdict.inputs_digest) == 16
        int(verdict.inputs_digest, 16)


class TestP3ReviewTier:
    def test_crown_jewel_routes_primary_oncall_best_effort(self) -> None:
        verdict = route_to_review_queue(
            **{**_HAPPY_P3, "asset_criticality": "crown_jewel"}
        )
        assert verdict.review_tier == "tier_primary_oncall"
        assert verdict.cadence == "best_effort_review"
        assert any(
            "best_effort_review" in r for r in verdict.reasons
        )

    @pytest.mark.parametrize("criticality", ["low", "medium", "high"])
    def test_non_crown_jewel_routes_tier_queue(
        self, criticality: str
    ) -> None:
        verdict = route_to_review_queue(
            **{**_HAPPY_P3, "asset_criticality": criticality}
        )
        assert verdict.review_tier == "tier_queue"
        assert verdict.cadence == "review_queue_standard_sla"


class TestP3RegulatorNotification:
    def test_p3_regulated_data_opens_notification(self) -> None:
        verdict = route_to_review_queue(
            **{**_HAPPY_P3, "regulated_data": True}
        )
        assert verdict.regulator_notification_required is True
        assert any(
            "regulator_notification_required" in r
            for r in verdict.reasons
        )

    def test_p3_regulated_does_not_change_tier_queue_route(self) -> None:
        verdict = route_to_review_queue(
            **{**_HAPPY_P3, "regulated_data": True}
        )
        assert verdict.review_tier == "tier_queue"
        assert verdict.cadence == "review_queue_standard_sla"

    def test_p3_crown_jewel_plus_regulated_combines(self) -> None:
        verdict = route_to_review_queue(
            priority="p3_routine",
            asset_criticality="crown_jewel",
            regulated_data=True,
            internet_exposed=True,
        )
        assert verdict.review_tier == "tier_primary_oncall"
        assert verdict.cadence == "best_effort_review"
        assert verdict.regulator_notification_required is True


class TestP3DigestStability:
    def test_p3_same_inputs_same_digest(self) -> None:
        assert (
            route_to_review_queue(**_HAPPY_P3).inputs_digest
            == route_to_review_queue(**_HAPPY_P3).inputs_digest
        )

    @pytest.mark.parametrize(
        "override",
        [
            {"asset_criticality": "crown_jewel"},
            {"regulated_data": True},
            {"internet_exposed": True},
        ],
    )
    def test_p3_single_input_change_changes_digest(
        self, override: dict
    ) -> None:
        base = route_to_review_queue(**_HAPPY_P3).inputs_digest
        changed = route_to_review_queue(
            **{**_HAPPY_P3, **override}
        ).inputs_digest
        assert base != changed

    def test_p3_digest_differs_from_p1_and_p2(self) -> None:
        # Priority is part of the canonical inputs digest; the p3
        # verdict and the p1 / p2 verdicts for the same asset must not
        # collide on the digest field.
        p1 = escalation_route(**_HAPPY)
        p2 = notify_on_call(**_HAPPY_P2)
        p3 = route_to_review_queue(**_HAPPY_P3)
        assert p3.inputs_digest != p1.inputs_digest
        assert p3.inputs_digest != p2.inputs_digest


class TestP3Rejection:
    @pytest.mark.parametrize(
        "priority",
        ["p1_severe", "p2_high", "p4_informational", "", "P3_ROUTINE"],
    )
    def test_non_p3_priority_rejected(self, priority: str) -> None:
        with pytest.raises(ValueError, match="p3-routine response body"):
            route_to_review_queue(
                **{**_HAPPY_P3, "priority": priority}  # type: ignore[arg-type]
            )

    def test_p3_unknown_criticality_rejected(self) -> None:
        with pytest.raises(ValueError, match="unknown asset_criticality"):
            route_to_review_queue(
                **{**_HAPPY_P3, "asset_criticality": "platinum"}  # type: ignore[arg-type]
            )

    @pytest.mark.parametrize(
        "field", ["regulated_data", "internet_exposed"]
    )
    def test_p3_non_bool_flag_rejected(self, field: str) -> None:
        with pytest.raises(TypeError, match="must be bool"):
            route_to_review_queue(
                **{**_HAPPY_P3, field: "true"}  # type: ignore[arg-type]
            )


class TestP3DownstreamHandoff:
    def test_p3_playbook_ref_pinned_on_every_verdict(self) -> None:
        a = route_to_review_queue(**_HAPPY_P3)
        b = route_to_review_queue(
            **{**_HAPPY_P3, "asset_criticality": "crown_jewel"}
        )
        assert (
            a.incident_management_playbook_ref
            == b.incident_management_playbook_ref
            == INCIDENT_MANAGEMENT_PLAYBOOK_REF
        )


_HAPPY_P4 = dict(
    priority="p4_informational",
    asset_criticality="medium",
    regulated_data=False,
    internet_exposed=False,
)


class TestLogAndClose:
    def test_p4_happy_path_shape(self) -> None:
        record = log_and_close(**_HAPPY_P4)
        assert isinstance(record, ClosureRecord)
        assert record.disposition == "closed_informational"
        assert record.regulator_notification_required is False
        assert record.reasons[0] == "priority=p4_informational → log-and-close"
        assert len(record.inputs_digest) == 16
        assert record.inputs_digest == record.inputs_digest.lower()

    @pytest.mark.parametrize("criticality", ["low", "medium", "high"])
    def test_p4_non_crown_jewel_closes_plain(self, criticality: str) -> None:
        record = log_and_close(
            **{**_HAPPY_P4, "asset_criticality": criticality}
        )
        assert record.disposition == "closed_informational"
        assert any("closed_informational" in r for r in record.reasons)

    def test_p4_crown_jewel_keeps_retention_pointer(self) -> None:
        record = log_and_close(
            **{**_HAPPY_P4, "asset_criticality": "crown_jewel"}
        )
        assert record.disposition == "closed_with_retention_pointer"
        assert any("crown_jewel" in r for r in record.reasons)
        # A retention pointer is not a page and not a regulator clock.
        assert record.regulator_notification_required is False

    def test_p4_regulated_data_keeps_pointer_and_opens_clock(self) -> None:
        record = log_and_close(**{**_HAPPY_P4, "regulated_data": True})
        assert record.disposition == "closed_with_retention_pointer"
        assert record.regulator_notification_required is True
        assert any("regulator_notification_required" in r for r in record.reasons)

    def test_p4_crown_jewel_plus_regulated_combines(self) -> None:
        record = log_and_close(
            **{
                **_HAPPY_P4,
                "asset_criticality": "crown_jewel",
                "regulated_data": True,
            }
        )
        assert record.disposition == "closed_with_retention_pointer"
        assert record.regulator_notification_required is True
        # Both rules fire and both are named, in order.
        joined = "\n".join(record.reasons)
        assert "crown_jewel" in joined and "regulated_data=true" in joined

    def test_p4_record_is_frozen(self) -> None:
        record = log_and_close(**_HAPPY_P4)
        with pytest.raises(AttributeError):
            record.disposition = "closed_with_retention_pointer"  # type: ignore[misc]


class TestP4Digest:
    def test_p4_same_inputs_same_digest(self) -> None:
        assert (
            log_and_close(**_HAPPY_P4).inputs_digest
            == log_and_close(**_HAPPY_P4).inputs_digest
        )

    @pytest.mark.parametrize(
        "override",
        [
            {"asset_criticality": "crown_jewel"},
            {"regulated_data": True},
            {"internet_exposed": True},
        ],
    )
    def test_p4_single_input_change_changes_digest(
        self, override: dict
    ) -> None:
        base = log_and_close(**_HAPPY_P4).inputs_digest
        changed = log_and_close(**{**_HAPPY_P4, **override}).inputs_digest
        assert base != changed

    def test_p4_internet_exposed_changes_digest_not_disposition(self) -> None:
        # Exposure is digest-only at p4: the close stays informational,
        # but a replay against a changed exposure flag must be visibly
        # a different verdict.
        base = log_and_close(**_HAPPY_P4)
        exposed = log_and_close(**{**_HAPPY_P4, "internet_exposed": True})
        assert exposed.disposition == base.disposition
        assert exposed.inputs_digest != base.inputs_digest

    def test_p4_digest_differs_from_siblings(self) -> None:
        # Priority is part of the canonical inputs digest; the p4
        # record must not collide with p1 / p2 / p3 for the same asset.
        p1 = escalation_route(**{**_HAPPY, "asset_criticality": "medium"})
        p2 = notify_on_call(**{**_HAPPY_P2, "asset_criticality": "medium"})
        p3 = route_to_review_queue(
            **{**_HAPPY_P3, "asset_criticality": "medium"}
        )
        p4 = log_and_close(**_HAPPY_P4)
        assert p4.inputs_digest not in {
            p1.inputs_digest,
            p2.inputs_digest,
            p3.inputs_digest,
        }


class TestP4Rejection:
    @pytest.mark.parametrize(
        "priority",
        ["p1_severe", "p2_high", "p3_routine", "", "P4_INFORMATIONAL"],
    )
    def test_non_p4_priority_rejected(self, priority: str) -> None:
        with pytest.raises(ValueError, match="p4-informational response body"):
            log_and_close(
                **{**_HAPPY_P4, "priority": priority}  # type: ignore[arg-type]
            )

    def test_p4_unknown_criticality_rejected(self) -> None:
        with pytest.raises(ValueError, match="unknown asset_criticality"):
            log_and_close(
                **{**_HAPPY_P4, "asset_criticality": "platinum"}  # type: ignore[arg-type]
            )

    @pytest.mark.parametrize(
        "field", ["regulated_data", "internet_exposed"]
    )
    def test_p4_non_bool_flag_rejected(self, field: str) -> None:
        with pytest.raises(TypeError, match="must be bool"):
            log_and_close(
                **{**_HAPPY_P4, field: "true"}  # type: ignore[arg-type]
            )
