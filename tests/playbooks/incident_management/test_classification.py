"""Unit tests for the significance + cross-border classification policy.

Table-driven: tests pin the public surface (the verdict) and the
load-time validation, then exercise each rule id by name so a
policy-table change surfaces as a deliberate diff against the YAML
under :mod:`content.playbooks.incident_management.primitives`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from content.playbooks.incident_management.primitives import classification


def _signals(**overrides) -> classification.IntakeSignals:
    base = dict(
        affected_essential_service_count=0,
        member_states_affected_count=1,
        disruption_severity="minor",
        data_classification="internal",
        cross_border_supply_chain=False,
    )
    base.update(overrides)
    return classification.IntakeSignals(**base)


class TestPolicyLoader:
    def test_loads_and_validates_default_policy(self) -> None:
        pol = classification.load_policy()
        assert pol["version"] == 1
        assert pol["significance_rules"]
        assert pol["cross_border_rules"]

    def test_policy_path_is_yaml_sibling(self) -> None:
        p = classification.policy_path()
        assert p.name == "classification_policy.yaml"
        assert p.is_file()

    def test_rejects_unknown_when_key(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.yaml"
        bad.write_text(
            "version: 1\n"
            "significance_rules:\n"
            "  - id: x\n"
            "    description: x\n"
            "    when: {nonsense: true}\n"
            "    then: {significant: true, reason: x}\n"
            "cross_border_rules:\n"
            "  - id: y\n"
            "    description: y\n"
            "    when: {}\n"
            "    then: {cross_border: false, reason: y}\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="unknown keys"):
            classification.load_policy(bad)

    def test_rejects_unknown_disruption_severity(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.yaml"
        bad.write_text(
            "version: 1\n"
            "significance_rules:\n"
            "  - id: x\n"
            "    description: x\n"
            "    when: {disruption_severity: catastrophic}\n"
            "    then: {significant: true, reason: x}\n"
            "cross_border_rules:\n"
            "  - id: y\n"
            "    description: y\n"
            "    when: {}\n"
            "    then: {cross_border: false, reason: y}\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="closed alphabet"):
            classification.load_policy(bad)


class TestSignificanceRules:
    def test_special_category_always_significant(self) -> None:
        v = classification.classify_significance(
            _signals(data_classification="special_category")
        )
        assert v.significant is True
        assert v.significance_rule == "sig.special_category_data"

    def test_severe_disruption_significant(self) -> None:
        v = classification.classify_significance(
            _signals(disruption_severity="severe")
        )
        assert v.significant is True
        assert v.significance_rule == "sig.severe_disruption"

    def test_major_disruption_plus_regulated_data_significant(self) -> None:
        v = classification.classify_significance(
            _signals(
                disruption_severity="major",
                data_classification="regulated",
            )
        )
        assert v.significant is True
        assert v.significance_rule == "sig.major_disruption_with_regulated_data"

    def test_multi_member_state_significant(self) -> None:
        v = classification.classify_significance(
            _signals(member_states_affected_count=3)
        )
        assert v.significant is True
        assert v.significance_rule == "sig.multi_member_state"

    def test_multi_essential_service_significant(self) -> None:
        v = classification.classify_significance(
            _signals(affected_essential_service_count=2)
        )
        assert v.significant is True
        assert v.significance_rule == "sig.multi_essential_service"

    def test_single_essential_service_minor_disruption_not_significant(
        self,
    ) -> None:
        v = classification.classify_significance(
            _signals(
                affected_essential_service_count=1,
                disruption_severity="minor",
            )
        )
        assert v.significant is False
        assert v.significance_rule == "sig.default_not_significant"

    def test_single_essential_service_major_disruption_significant(
        self,
    ) -> None:
        v = classification.classify_significance(
            _signals(
                affected_essential_service_count=1,
                disruption_severity="major",
            )
        )
        assert v.significant is True
        assert (
            v.significance_rule
            == "sig.single_essential_service_major_or_severe"
        )

    def test_default_not_significant_for_bland_signals(self) -> None:
        v = classification.classify_significance(_signals())
        assert v.significant is False
        assert v.significance_rule == "sig.default_not_significant"


class TestCrossBorderRules:
    def test_multi_member_state_cross_border(self) -> None:
        v = classification.classify_significance(
            _signals(member_states_affected_count=2)
        )
        assert v.cross_border is True
        assert v.cross_border_rule == "cb.multi_member_state"

    def test_single_state_with_supply_chain_cross_border(self) -> None:
        v = classification.classify_significance(
            _signals(
                member_states_affected_count=1,
                cross_border_supply_chain=True,
            )
        )
        assert v.cross_border is True
        assert v.cross_border_rule == "cb.single_state_supply_chain"

    def test_single_state_no_supply_chain_not_cross_border(self) -> None:
        v = classification.classify_significance(
            _signals(member_states_affected_count=1)
        )
        assert v.cross_border is False
        assert v.cross_border_rule == "cb.default_not_cross_border"


class TestDeterminism:
    def test_same_input_same_verdict(self) -> None:
        s = _signals(
            affected_essential_service_count=2,
            member_states_affected_count=3,
            disruption_severity="major",
            data_classification="regulated",
        )
        a = classification.classify_significance(s)
        b = classification.classify_significance(s)
        assert a == b
        assert a.inputs_digest == b.inputs_digest

    def test_digest_changes_with_input(self) -> None:
        a = classification.classify_significance(_signals())
        b = classification.classify_significance(
            _signals(member_states_affected_count=2)
        )
        assert a.inputs_digest != b.inputs_digest


class TestIntakeSignalsModel:
    def test_extra_field_rejected(self) -> None:
        with pytest.raises(Exception):
            classification.IntakeSignals(
                affected_essential_service_count=0,
                member_states_affected_count=1,
                disruption_severity="minor",
                data_classification="internal",
                bogus=True,  # type: ignore[call-arg]
            )

    def test_frozen(self) -> None:
        s = _signals()
        with pytest.raises(Exception):
            s.disruption_severity = "severe"  # type: ignore[misc]

    def test_negative_count_rejected(self) -> None:
        with pytest.raises(Exception):
            classification.IntakeSignals(
                affected_essential_service_count=-1,
                member_states_affected_count=1,
                disruption_severity="minor",
                data_classification="internal",
            )

    def test_unknown_disruption_severity_rejected(self) -> None:
        with pytest.raises(Exception):
            classification.IntakeSignals(
                affected_essential_service_count=0,
                member_states_affected_count=1,
                disruption_severity="catastrophic",  # type: ignore[arg-type]
                data_classification="internal",
            )


class TestRejectsNonModelInput:
    def test_dict_rejected(self) -> None:
        with pytest.raises(TypeError, match="IntakeSignals"):
            classification.classify_significance({})  # type: ignore[arg-type]
