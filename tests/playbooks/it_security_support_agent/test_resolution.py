"""Unit tests for the attempt-automated-resolution primitive (F-WF-12 PRIM)."""

from __future__ import annotations

import pytest

from content.playbooks.it_security_support_agent.primitives import (
    InvalidAutomatedResolutionError,
    attempt_automated_resolution,
)


def _record(kind: str = "actionable") -> dict:
    return {"request_kind": kind, "requester_handle": "helpdesk"}


def _cls(category: str = "actionable") -> dict:
    return {"category": category}


def _obs(**overrides) -> dict:
    o = {
        "outcome": "resolved",
        "declared_action_set": ["net.restart_tunnel"],
        "observed_state": "tunnel back up",
    }
    o.update(overrides)
    return o


class TestAutomatedResolutionHappyPath:
    @pytest.mark.parametrize(
        "outcome", ["resolved", "partial", "failed"]
    )
    def test_outcomes_with_actions(self, outcome: str) -> None:
        out = attempt_automated_resolution(
            _record(), _cls(), _obs(outcome=outcome)
        )
        assert out["outcome"] == outcome
        assert out["declared_action_set"] == ["net.restart_tunnel"]

    def test_not_attempted_requires_empty_action_set(self) -> None:
        out = attempt_automated_resolution(
            _record("incident-shaped"),
            _cls("incident-shaped"),
            _obs(
                outcome="not_attempted",
                declared_action_set=[],
                observed_state="handoff path",
            ),
        )
        assert out == {
            "outcome": "not_attempted",
            "declared_action_set": [],
            "observed_state": "handoff path",
        }

    def test_actions_deduplicated_in_order(self) -> None:
        # duplicate must be rejected (closed-shape determinism)
        with pytest.raises(
            InvalidAutomatedResolutionError, match="duplicate"
        ):
            attempt_automated_resolution(
                _record(),
                _cls(),
                _obs(declared_action_set=["net.a", "net.a"]),
            )

    def test_determinism(self) -> None:
        a = attempt_automated_resolution(_record(), _cls(), _obs())
        b = attempt_automated_resolution(_record(), _cls(), _obs())
        assert a == b


class TestAutomatedResolutionRejections:
    def test_incident_shaped_pins_not_attempted(self) -> None:
        with pytest.raises(
            InvalidAutomatedResolutionError,
            match="incident-shaped classification pins",
        ):
            attempt_automated_resolution(
                _record("incident-shaped"),
                _cls("incident-shaped"),
                _obs(outcome="resolved"),
            )

    def test_unknown_outcome(self) -> None:
        with pytest.raises(
            InvalidAutomatedResolutionError, match="outcome"
        ):
            attempt_automated_resolution(
                _record(), _cls(), _obs(outcome="kinda")
            )

    @pytest.mark.parametrize(
        "outcome", ["resolved", "partial", "failed"]
    )
    def test_non_not_attempted_requires_actions(self, outcome: str) -> None:
        with pytest.raises(
            InvalidAutomatedResolutionError, match="non-empty"
        ):
            attempt_automated_resolution(
                _record(),
                _cls(),
                _obs(outcome=outcome, declared_action_set=[]),
            )

    def test_not_attempted_with_actions_rejected(self) -> None:
        with pytest.raises(
            InvalidAutomatedResolutionError, match="must be empty"
        ):
            attempt_automated_resolution(
                _record("incident-shaped"),
                _cls("incident-shaped"),
                _obs(
                    outcome="not_attempted",
                    declared_action_set=["net.a"],
                ),
            )

    @pytest.mark.parametrize(
        "bad",
        ["NoDot", "family.WITHCAPS", "x.", "family.slug.extra"],
    )
    def test_bad_action_shape(self, bad: str) -> None:
        with pytest.raises(
            InvalidAutomatedResolutionError, match="<family>.<slug>"
        ):
            attempt_automated_resolution(
                _record(), _cls(), _obs(declared_action_set=[bad])
            )

    def test_action_over_128_chars(self) -> None:
        long_action = "net." + "x" * 130
        with pytest.raises(
            InvalidAutomatedResolutionError, match="<= 128"
        ):
            attempt_automated_resolution(
                _record(),
                _cls(),
                _obs(declared_action_set=[long_action]),
            )

    def test_observed_state_over_400(self) -> None:
        with pytest.raises(
            InvalidAutomatedResolutionError, match="<= 400"
        ):
            attempt_automated_resolution(
                _record(), _cls(), _obs(observed_state="x" * 401)
            )

    def test_observed_state_control_chars(self) -> None:
        with pytest.raises(
            InvalidAutomatedResolutionError,
            match="control characters",
        ):
            attempt_automated_resolution(
                _record(),
                _cls(),
                _obs(observed_state="line1\nline2"),
            )

    def test_non_dict_inputs(self) -> None:
        with pytest.raises(InvalidAutomatedResolutionError):
            attempt_automated_resolution("nope", _cls(), _obs())  # type: ignore[arg-type]
        with pytest.raises(InvalidAutomatedResolutionError):
            attempt_automated_resolution(_record(), "nope", _obs())  # type: ignore[arg-type]
        with pytest.raises(InvalidAutomatedResolutionError):
            attempt_automated_resolution(_record(), _cls(), "nope")  # type: ignore[arg-type]
