"""Unit tests for the classify-request primitive (F-WF-12 PRIM)."""

from __future__ import annotations

import pytest

from content.playbooks.it_security_support_agent.primitives import (
    InvalidClassificationError,
    classify_request,
)


def _record(kind: str = "actionable") -> dict:
    return {
        "request_kind": kind,
        "requester_handle": "helpdesk-rota",
        "declared_symptom": "x",
        "received_at": "2026-06-01T12:00:00Z",
        "support_request_ref": "ticket/x",
    }


def _verdict(**overrides) -> dict:
    v = {
        "category": "actionable",
        "severity": "Medium",
        "rule_ids": ["cls.network", "sev.medium"],
        "policy_version": "v1.2.0",
    }
    v.update(overrides)
    return v


class TestClassifyRequestHappyPath:
    def test_canonical_verdict_shape(self) -> None:
        out = classify_request(_record(), _verdict())
        assert out == {
            "category": "actionable",
            "severity": "Medium",
            "rule_ids": ["cls.network", "sev.medium"],
            "policy_version": "v1.2.0",
        }

    @pytest.mark.parametrize(
        "kind", ["informational", "actionable", "incident-shaped"]
    )
    def test_all_categories(self, kind: str) -> None:
        out = classify_request(
            _record(kind), _verdict(category=kind)
        )
        assert out["category"] == kind

    @pytest.mark.parametrize(
        "sev", ["Informational", "Low", "Medium", "High", "Critical"]
    )
    def test_all_severities(self, sev: str) -> None:
        out = classify_request(_record(), _verdict(severity=sev))
        assert out["severity"] == sev

    def test_rule_ids_preserved_in_order(self) -> None:
        out = classify_request(
            _record(),
            _verdict(rule_ids=["sev.medium", "cls.network", "ext.q"]),
        )
        assert out["rule_ids"] == ["sev.medium", "cls.network", "ext.q"]

    def test_determinism(self) -> None:
        a = classify_request(_record(), _verdict())
        b = classify_request(_record(), _verdict())
        assert a == b


class TestClassifyRequestRejections:
    def test_category_must_match_request_kind(self) -> None:
        with pytest.raises(
            InvalidClassificationError, match="alphabets are pinned"
        ):
            classify_request(
                _record("actionable"),
                _verdict(category="incident-shaped"),
            )

    def test_unknown_category(self) -> None:
        with pytest.raises(InvalidClassificationError, match="category"):
            classify_request(_record(), _verdict(category="emergency"))

    def test_unknown_severity(self) -> None:
        with pytest.raises(InvalidClassificationError, match="severity"):
            classify_request(_record(), _verdict(severity="Severe"))

    def test_empty_rule_ids_rejected(self) -> None:
        with pytest.raises(InvalidClassificationError, match="non-empty"):
            classify_request(_record(), _verdict(rule_ids=[]))

    def test_duplicate_rule_ids_rejected(self) -> None:
        with pytest.raises(InvalidClassificationError, match="duplicate"):
            classify_request(
                _record(),
                _verdict(rule_ids=["cls.x", "cls.x"]),
            )

    @pytest.mark.parametrize(
        "bad",
        ["Cls.Family", "no_dot", "x.", ".y", "family.WithCAPS", "family.slug.extra"],
    )
    def test_bad_rule_id_shape(self, bad: str) -> None:
        with pytest.raises(
            InvalidClassificationError, match="family|<family>"
        ):
            classify_request(_record(), _verdict(rule_ids=[bad]))

    def test_non_string_rule_id(self) -> None:
        with pytest.raises(InvalidClassificationError):
            classify_request(_record(), _verdict(rule_ids=[7]))

    def test_bad_policy_version(self) -> None:
        with pytest.raises(
            InvalidClassificationError, match="policy_version"
        ):
            classify_request(
                _record(), _verdict(policy_version="has space")
            )

    def test_non_dict_record(self) -> None:
        with pytest.raises(InvalidClassificationError):
            classify_request("nope", _verdict())  # type: ignore[arg-type]

    def test_non_dict_verdict(self) -> None:
        with pytest.raises(InvalidClassificationError):
            classify_request(_record(), "nope")  # type: ignore[arg-type]

    def test_upstream_record_with_bad_kind(self) -> None:
        bad = _record()
        bad["request_kind"] = "garbage"
        with pytest.raises(
            InvalidClassificationError, match="upstream ingest"
        ):
            classify_request(bad, _verdict())
