"""Unit tests for the escalate-with-human-handoff primitive (F-WF-12 PRIM).

Acceptance focus: the workflow MUST NOT silently auto-close. The
primitive ALWAYS materialises a closed handoff envelope with
``handoff_fired`` set explicitly — on every path, including the
no-handoff (automated_resolution_closure) closure.
"""

from __future__ import annotations

import pytest

from content.playbooks.it_security_support_agent.primitives import (
    InvalidHumanHandoffError,
    escalate_with_human_handoff,
)


def _cls(category: str = "actionable") -> dict:
    return {"category": category}


def _res(outcome: str = "resolved") -> dict:
    return {"outcome": outcome}


_INPUTS_FIRED = {
    "responder_queue": "soc-oncall",
    "acknowledgement_ref": "queue/recv-1",
}


class TestHandoffFiredPaths:
    def test_incident_shaped_fires_first(self) -> None:
        # Trigger order matters — incident-shaped wins even if outcome
        # would also fire ("not_attempted" pins for that case anyway).
        env = escalate_with_human_handoff(
            _cls("incident-shaped"),
            _res("not_attempted"),
            _INPUTS_FIRED,
        )
        assert env == {
            "handoff_fired": True,
            "trigger_reason": "incident_shaped_classification",
            "responder_queue": "soc-oncall",
            "acknowledgement_ref": "queue/recv-1",
        }

    @pytest.mark.parametrize(
        "outcome", ["partial", "failed", "not_attempted"]
    )
    def test_non_resolved_outcome_fires(self, outcome: str) -> None:
        env = escalate_with_human_handoff(
            _cls("actionable"), _res(outcome), _INPUTS_FIRED
        )
        assert env["handoff_fired"] is True
        assert env["trigger_reason"] == "automated_resolution_not_resolved"

    def test_policy_override_fires(self) -> None:
        env = escalate_with_human_handoff(
            _cls("actionable"),
            _res("resolved"),
            {**_INPUTS_FIRED, "policy_override": True},
        )
        assert env["handoff_fired"] is True
        assert env["trigger_reason"] == "policy_override"
        assert env["responder_queue"] == "soc-oncall"

    def test_trigger_order_classification_beats_outcome(self) -> None:
        env = escalate_with_human_handoff(
            _cls("incident-shaped"),
            _res("failed"),
            _INPUTS_FIRED,
        )
        assert env["trigger_reason"] == "incident_shaped_classification"


class TestHandoffNoFirePath:
    def test_resolved_actionable_does_not_fire(self) -> None:
        env = escalate_with_human_handoff(
            _cls("actionable"), _res("resolved"), {}
        )
        # ALWAYS materialises a closed envelope with handoff_fired explicit
        assert env == {
            "handoff_fired": False,
            "trigger_reason": "automated_resolution_closure",
        }

    def test_handoff_fired_field_present_and_explicit(self) -> None:
        env = escalate_with_human_handoff(
            _cls("informational"), _res("resolved"), {}
        )
        assert "handoff_fired" in env
        assert env["handoff_fired"] is False  # explicit, never absent

    def test_no_fire_path_omits_responder_fields(self) -> None:
        env = escalate_with_human_handoff(
            _cls("actionable"),
            _res("resolved"),
            {"responder_queue": None, "acknowledgement_ref": None},
        )
        assert "responder_queue" not in env
        assert "acknowledgement_ref" not in env

    def test_no_fire_with_stale_responder_queue_rejected(self) -> None:
        with pytest.raises(
            InvalidHumanHandoffError, match="must be absent"
        ):
            escalate_with_human_handoff(
                _cls("actionable"),
                _res("resolved"),
                {"responder_queue": "stale-rota"},
            )

    def test_policy_override_false_does_not_fire(self) -> None:
        env = escalate_with_human_handoff(
            _cls("actionable"),
            _res("resolved"),
            {"policy_override": False},
        )
        assert env["handoff_fired"] is False


class TestHandoffShapeRejections:
    def test_responder_queue_required_when_fired(self) -> None:
        with pytest.raises(InvalidHumanHandoffError):
            escalate_with_human_handoff(
                _cls("incident-shaped"),
                _res("not_attempted"),
                {"acknowledgement_ref": "queue/x"},
            )

    def test_acknowledgement_ref_required_when_fired(self) -> None:
        with pytest.raises(InvalidHumanHandoffError):
            escalate_with_human_handoff(
                _cls("incident-shaped"),
                _res("not_attempted"),
                {"responder_queue": "soc-oncall"},
            )

    @pytest.mark.parametrize(
        "bad_queue",
        [
            "First Last",  # personal name
            "1-leading-digit",
            "queue with spaces",
            "x" * 201,  # over length
        ],
    )
    def test_rejects_non_role_shaped_responder_queue(
        self, bad_queue: str
    ) -> None:
        with pytest.raises(InvalidHumanHandoffError):
            escalate_with_human_handoff(
                _cls("incident-shaped"),
                _res("not_attempted"),
                {
                    "responder_queue": bad_queue,
                    "acknowledgement_ref": "queue/r",
                },
            )

    def test_bad_acknowledgement_ref_shape(self) -> None:
        with pytest.raises(
            InvalidHumanHandoffError, match="opaque-pointer"
        ):
            escalate_with_human_handoff(
                _cls("incident-shaped"),
                _res("not_attempted"),
                {
                    "responder_queue": "soc-oncall",
                    "acknowledgement_ref": "has spaces",
                },
            )

    def test_non_dict_inputs(self) -> None:
        with pytest.raises(InvalidHumanHandoffError):
            escalate_with_human_handoff("nope", _res(), {})  # type: ignore[arg-type]
        with pytest.raises(InvalidHumanHandoffError):
            escalate_with_human_handoff(_cls(), "nope", {})  # type: ignore[arg-type]
        with pytest.raises(InvalidHumanHandoffError):
            escalate_with_human_handoff(_cls(), _res(), "nope")  # type: ignore[arg-type]


class TestHandoffDeterminism:
    def test_same_inputs_same_envelope(self) -> None:
        a = escalate_with_human_handoff(
            _cls("incident-shaped"),
            _res("not_attempted"),
            _INPUTS_FIRED,
        )
        b = escalate_with_human_handoff(
            _cls("incident-shaped"),
            _res("not_attempted"),
            _INPUTS_FIRED,
        )
        assert a == b
