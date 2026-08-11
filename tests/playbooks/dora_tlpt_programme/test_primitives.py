"""Unit tests for the DORA Chapter IV DORT / TLPT primitives (CORE).

The assertions worth reading pin statutory decisions rather than type checks:

* a function the asset register cannot resolve is a scope gap, not a silent
  narrowing of the testing programme;
* the Art. 26(1) 36-month interval is a ceiling — an operator may tighten it
  and not loosen it;
* an entity out of TLPT scope emits a positive record, because an absent
  record proves nothing;
* Art. 27 internal testers need the independence attestation and external
  ones a certification; the wrong evidence for the posture is refused;
* a boundary provider is a participant or a reasoned carve-out, never a
  silent omission;
* remediation deadlines are derived from the rubric, never asserted.
"""
from __future__ import annotations

import pytest

from content.playbooks.dora_tlpt_programme.primitives.remediation import (
    InvalidRemediationTrackingError,
    derive_attestation_artifact_id,
    track_remediation,
)
from content.playbooks.dora_tlpt_programme.primitives.scope import (
    InvalidDortScopeError,
    define_dort_scope,
)
from content.playbooks.dora_tlpt_programme.primitives.scoping import (
    InvalidRedTeamScopingError,
    approve_red_team_scoping,
)
from content.playbooks.dora_tlpt_programme.primitives.trigger import (
    STATUTORY_MAX_INTERVAL_MONTHS,
    InvalidTlptTriggerError,
    evaluate_tlpt_trigger,
)

WINDOW = "2026-01-01/2026-12-31"


def _scope(**over):
    kw = {
        "testing_window": WINDOW,
        "critical_functions": ["fn-payments", "fn-custody"],
        "asset_register": {"fn-payments": ["a1", "a2"], "fn-custody": ["a3"]},
        "third_party_register": {"fn-payments": ["tp-core"], "fn-custody": []},
    }
    kw.update(over)
    return define_dort_scope(**kw)


def _trigger(scope=None, **over):
    kw = {
        "dort_scope": scope or _scope(),
        "entity_significance_tier": "significant",
        "tlpt_identified": True,
        "threat_intelligence_source": "ti-source-a",
        "tester_posture": "external",
        "authority_notification_ref": "notif/2026/001",
        "last_tlpt_completed_on": "2022-06-30",
    }
    kw.update(over)
    return evaluate_tlpt_trigger(**kw)


def _scoping(scope=None, trigger=None, **over):
    scope = scope or _scope()
    kw = {
        "dort_scope": scope,
        "tlpt_trigger": trigger or _trigger(scope),
        "tester_ref": "rt-provider-x",
        "outcome": "approved",
        "tester_certification_ref": "cert/crest/001",
    }
    kw.update(over)
    return approve_red_team_scoping(**kw)


# --- scope ------------------------------------------------------------------


def test_scope_composes_the_three_registers() -> None:
    s = _scope()
    assert s["complete"] is True
    assert s["asset_count"] == 3
    assert s["third_party_count"] == 1
    assert [e["function_id"] for e in s["functions"]] == ["fn-custody", "fn-payments"]


def test_function_without_assets_is_a_scope_gap() -> None:
    """Art. 24 coverage cannot be demonstrated for a function the asset
    register does not resolve — reported, not silently dropped."""
    s = _scope(asset_register={"fn-payments": ["a1"]})
    assert s["unresolved_functions"] == ["fn-custody"]
    assert s["complete"] is False


def test_register_naming_an_unscoped_function_is_refused() -> None:
    with pytest.raises(InvalidDortScopeError, match="widen the testing boundary"):
        _scope(asset_register={"fn-payments": ["a1"], "fn-rogue": ["a9"]})


def test_empty_critical_functions_is_refused() -> None:
    with pytest.raises(InvalidDortScopeError, match="Art. 8 identification"):
        _scope(critical_functions=[])


def test_inverted_window_is_refused() -> None:
    with pytest.raises(InvalidDortScopeError, match="start before it ends"):
        _scope(testing_window="2026-12-31/2026-01-01")


def test_scope_is_deterministic() -> None:
    assert _scope() == _scope()


# --- trigger ----------------------------------------------------------------


def test_elapsed_interval_makes_tlpt_due() -> None:
    t = _trigger()
    assert t["tlpt_due"] is True
    assert t["basis"] == "interval_elapsed"
    assert t["interval_months"] == STATUTORY_MAX_INTERVAL_MONTHS


def test_no_prior_tlpt_makes_it_due() -> None:
    t = _trigger(last_tlpt_completed_on=None)
    assert (t["tlpt_due"], t["basis"]) == (True, "no_prior_tlpt")
    assert t["months_since_last_tlpt"] is None


def test_within_interval_is_not_due() -> None:
    t = _trigger(last_tlpt_completed_on="2025-06-30")
    assert (t["tlpt_due"], t["basis"]) == (False, "within_interval")


def test_out_of_scope_entity_emits_a_positive_record() -> None:
    """An absent record proves nothing; the operator must be able to show why
    no TLPT ran."""
    t = _trigger(tlpt_identified=False)
    assert (t["tlpt_due"], t["basis"]) == (False, "not_identified")
    assert t["entity_significance_tier"] == "significant"


def test_operator_may_tighten_the_statutory_interval() -> None:
    t = _trigger(declared_cadence_months=24, last_tlpt_completed_on="2024-06-30")
    assert t["interval_months"] == 24
    assert t["tlpt_due"] is True  # 30 months elapsed against a 24-month cadence


def test_operator_may_not_loosen_the_statutory_interval() -> None:
    with pytest.raises(InvalidTlptTriggerError, match="tighten the statutory interval"):
        _trigger(declared_cadence_months=48)


def test_interval_boundary_is_exact_at_36_months() -> None:
    """Against a window ending 2026-12-31: 2023-12-31 is exactly 36 months
    and due; one day later is 35 and is not."""
    on_boundary = _trigger(last_tlpt_completed_on="2023-12-31")
    assert on_boundary["months_since_last_tlpt"] == 36
    assert on_boundary["tlpt_due"] is True

    one_day_short = _trigger(last_tlpt_completed_on="2024-01-01")
    assert one_day_short["months_since_last_tlpt"] == 35
    assert one_day_short["tlpt_due"] is False


def test_day_of_month_does_not_round_up_into_compliance() -> None:
    """36 calendar months apart by month arithmetic, but the day is short.

    2023-12-31 -> 2026-12-30 is month-difference 36 with the day going
    backwards, so it counts as 35. Without the day-of-month adjustment this
    would report an interval as elapsed a day before it is.
    """
    t = _trigger(
        scope=_scope(testing_window="2026-01-01/2026-12-30"),
        last_tlpt_completed_on="2023-12-31",
    )
    assert t["months_since_last_tlpt"] == 35
    assert t["tlpt_due"] is False


def test_tier_is_not_derived_from_identification() -> None:
    """`tlpt_identified` must be supplied — the tier does not imply it."""
    with pytest.raises(InvalidTlptTriggerError, match="declaration"):
        _trigger(tlpt_identified="yes")


def test_prior_tlpt_after_the_window_is_refused() -> None:
    with pytest.raises(InvalidTlptTriggerError, match="cannot have completed after"):
        _trigger(last_tlpt_completed_on="2027-01-01")


# --- scoping ----------------------------------------------------------------


def test_scoping_binds_participants_and_outcome() -> None:
    s = _scoping()
    assert s["engagement_may_proceed"] is True
    assert s["third_party_participants"] == ["tp-core"]
    assert len(s["red_team_scoping_id"]) == 16


def test_nothing_is_scoped_when_nothing_is_due() -> None:
    scope = _scope()
    not_due = _trigger(scope, tlpt_identified=False)
    with pytest.raises(InvalidRedTeamScopingError, match="nothing to scope"):
        _scoping(scope=scope, trigger=not_due)


def test_internal_posture_requires_the_art27_attestation() -> None:
    scope = _scope()
    internal = _trigger(scope, tester_posture="internal")
    with pytest.raises(InvalidRedTeamScopingError, match="Art. 27 permits internal"):
        approve_red_team_scoping(
            dort_scope=scope, tlpt_trigger=internal,
            tester_ref="rt-internal", outcome="approved",
        )


def test_internal_posture_rejects_a_certification() -> None:
    scope = _scope()
    internal = _trigger(scope, tester_posture="internal")
    with pytest.raises(InvalidRedTeamScopingError, match="for an external posture"):
        approve_red_team_scoping(
            dort_scope=scope, tlpt_trigger=internal,
            tester_ref="rt-internal", outcome="approved",
            tester_certification_ref="cert/crest/001",
        )


def test_external_posture_requires_a_certification() -> None:
    with pytest.raises(InvalidRedTeamScopingError, match="requires tester_certification_ref"):
        _scoping(tester_certification_ref=None)


def test_carve_out_removes_a_participant_with_a_reason() -> None:
    s = _scoping(third_party_carve_outs={"tp-core": "contractual-restriction"})
    assert s["third_party_participants"] == []
    assert s["third_party_carve_outs"] == {"tp-core": "contractual-restriction"}


def test_carve_out_of_a_provider_outside_the_boundary_is_refused() -> None:
    with pytest.raises(InvalidRedTeamScopingError, match="never in scope"):
        _scoping(third_party_carve_outs={"tp-absent": "not-applicable"})


def test_deferred_outcome_blocks_the_engagement_without_erroring() -> None:
    s = _scoping(outcome="deferred")
    assert s["outcome"] == "deferred"
    assert s["engagement_may_proceed"] is False


def test_window_mismatch_between_envelopes_is_refused() -> None:
    other = _scope(testing_window="2025-01-01/2025-12-31")
    with pytest.raises(InvalidRedTeamScopingError, match="does not match"):
        approve_red_team_scoping(
            dort_scope=other, tlpt_trigger=_trigger(), tester_ref="rt-x",
            outcome="approved", tester_certification_ref="cert/1",
        )


# --- remediation ------------------------------------------------------------


def _remediate(**over):
    scope = _scope()
    kw = {
        "dort_scope": scope,
        "red_team_scoping": _scoping(scope=scope),
        "findings": [
            {"finding_id": "f1", "severity": "critical",
             "observed_on": "2026-08-01", "evidence_ref": "ev/1"},
        ],
        "severity_rubric": {"critical": 14, "high": 60},
        "workflow_id": "wf-1",
        "execution_id": "ex-1",
        "captured_at": "2026-11-15T10:00:00Z",
    }
    kw.update(over)
    return track_remediation(**kw)


def test_deadline_is_derived_from_the_rubric() -> None:
    r = _remediate()
    assert r["findings"][0]["remediation_deadline"] == "2026-08-15"


def test_register_is_embedded_in_the_attestation() -> None:
    """An attestation cannot exist without the register it attests to."""
    r = _remediate()
    assert r["findings_register_id"].endswith(":findings")
    assert r["remediation_attestation_id"].startswith(
        r["red_team_scoping_id"]
    )


def test_open_and_overdue_are_reported_not_blocking() -> None:
    r = _remediate(findings=[
        {"finding_id": "f1", "severity": "critical",
         "observed_on": "2026-08-01", "evidence_ref": "ev/1"},
        {"finding_id": "f2", "severity": "high",
         "observed_on": "2026-11-01", "evidence_ref": "ev/2"},
    ])
    assert r["open_count"] == 2
    assert r["overdue_count"] == 1        # f1 due 2026-08-15, f2 due 2026-12-31
    assert r["all_findings_closed"] is False


def test_closed_finding_is_never_overdue() -> None:
    r = _remediate(findings=[
        {"finding_id": "f1", "severity": "critical", "observed_on": "2026-08-01",
         "evidence_ref": "ev/1", "closed_on": "2026-08-10"},
    ])
    assert (r["open_count"], r["overdue_count"]) == (0, 0)
    assert r["all_findings_closed"] is True


def test_severity_outside_the_rubric_is_refused() -> None:
    with pytest.raises(InvalidRemediationTrackingError, match="ships no defaults"):
        _remediate(findings=[
            {"finding_id": "f1", "severity": "moderate",
             "observed_on": "2026-08-01", "evidence_ref": "ev/1"},
        ])


def test_duplicate_finding_id_is_refused() -> None:
    with pytest.raises(InvalidRemediationTrackingError, match="more than once"):
        _remediate(findings=[
            {"finding_id": "f1", "severity": "critical",
             "observed_on": "2026-08-01", "evidence_ref": "ev/1"},
            {"finding_id": "f1", "severity": "high",
             "observed_on": "2026-08-02", "evidence_ref": "ev/2"},
        ])


def test_unapproved_engagement_has_nothing_to_attest() -> None:
    scope = _scope()
    with pytest.raises(InvalidRemediationTrackingError, match="no engagement to attest"):
        _remediate(
            dort_scope=scope,
            red_team_scoping=_scoping(scope=scope, outcome="rejected"),
        )


def test_closure_before_observation_is_refused() -> None:
    with pytest.raises(InvalidRemediationTrackingError, match="precedes observed_on"):
        _remediate(findings=[
            {"finding_id": "f1", "severity": "critical", "observed_on": "2026-08-01",
             "evidence_ref": "ev/1", "closed_on": "2026-07-01"},
        ])


def test_artifact_id_follows_the_house_derivation() -> None:
    import hashlib
    expected = hashlib.sha256(b"wf-1|ex-1|2026-11-15T10:00:00Z").hexdigest()
    assert _remediate()["artifact_id"] == expected
    assert derive_attestation_artifact_id(
        "wf-1", "ex-1", "2026-11-15T10:00:00Z"
    ) == expected


def test_findings_are_emitted_sorted() -> None:
    r = _remediate(findings=[
        {"finding_id": "f9", "severity": "high",
         "observed_on": "2026-08-01", "evidence_ref": "ev/9"},
        {"finding_id": "f1", "severity": "critical",
         "observed_on": "2026-08-01", "evidence_ref": "ev/1"},
    ])
    assert [e["finding_id"] for e in r["findings"]] == ["f1", "f9"]


def test_remediation_is_deterministic() -> None:
    assert _remediate() == _remediate()
