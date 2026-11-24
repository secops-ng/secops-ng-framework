"""Unit coverage for the dora_tpr_management primitives (CORE-PRIM).

Each test pins one rule of Regulation (EU) 2022/2554, Art. 28 to 30, as the
primitives encode it, and the refusals at the JSON-native boundary.
"""

from __future__ import annotations

import copy

import pytest

from content.playbooks.dora_tpr_management.primitives import (
    CLAUSES,
    EU_EEA,
    TRIGGERS,
    InvalidExitAssessmentError,
    InvalidPeriodicReviewError,
    InvalidProvisionsCheckError,
    InvalidRegisterEntryError,
    InvalidRiskAssessmentError,
    assess_onboarding_risk,
    check_contractual_provisions,
    compose_exit_assessment,
    compose_register_entry,
    review_arrangement,
)

P = "provider.cloud_iaas_eu@v1"
SIBLING = "provider.cloud_iaas_group@v1"
SUB1, SUB2 = "provider.dc_operator@v1", "provider.backup_vault@v1"
T0, T1, T2 = "2026-11-01T09:00:00Z", "2026-11-02T09:00:00Z", "2027-05-01T09:00:00Z"
REGISTER = [{"function": "payments_settlement", "critical_or_important": True},
            {"function": "intranet_wiki", "critical_or_important": False}]


def profile(**over) -> dict:
    base = {"established_in": "DE", "service_locations": ["DE", "NL"], "data_locations": ["DE"],
            "substitutable": True, "closely_connected": [], "subcontracting_permitted": False, "subcontractors": []}
    base.update(over)
    return base


def assess(function="payments_settlement", register=None, prof=None, arrangements=None, supervisory=True,
           dd="dd:2026-11-cloud", coi=None, standards=None, at=T0, handle=P) -> dict:
    return assess_onboarding_risk(handle, function, REGISTER if register is None else register,
                                  profile() if prof is None else prof, arrangements or [], supervisory, dd,
                                  coi or {"assessed": True, "identified": []},
                                  ["std:iso27001-2022"] if standards is None else standards, at)


def all_clauses(cif=True, **over) -> dict:
    out = {c: {"status": "present", "deviation_ref": None} for c, _, every in CLAUSES if every or cif}
    out.update(over)
    return out


def check(a=None, clauses=None, micro=False, contract="contract:cloud-2026") -> dict:
    a = a or assess()
    return check_contractual_provisions(a, contract, all_clauses(a["critical_or_important"]) if clauses is None
                                        else clauses, micro, T0)


def row(a=None, p=None) -> dict:
    a = a or assess()
    p = p or check(a)
    return compose_register_entry(a, p, p["contract_ref"], "wf:dora-tpr", "exec:0001", T1)


def review(r=None, register=None, evidence=None, changes=None, breaches=None, impeded=False, at=T2) -> dict:
    return review_arrangement(r or row(), "window:2027-h1", REGISTER if register is None else register,
                              evidence or [], changes or [], breaches or [], impeded, at)


def strategy(**over) -> dict:
    base = {"plan_ref": "exit:cloud-plan", "last_tested_at": "2027-01-15T00:00:00Z",
            "last_reviewed_at": "2027-02-01T00:00:00Z", "max_age_days": 365, "alternatives": ["alt:inhouse"],
            "transition_plan_ref": "transition:cloud", "contingency_ref": "bcp:cloud"}
    base.update(over)
    return base


def exit_(r=None, rv=None, strat="default", trigger=None) -> dict:
    r = r or row()
    rv = rv or review(r)
    return compose_exit_assessment(r, rv, strategy() if strat == "default" else strat, trigger, "wf:dora-tpr",
                                   "exec:0002", T2)


# --- onboarding risk assessment (Art. 28(4), 28(5), 29) ----------------------------------------------------


def test_criticality_is_read_from_the_function_register():
    assert assess()["criticality"] == "critical_or_important"
    low = assess("intranet_wiki")
    assert low["criticality"] == "not_critical_or_important"
    assert low["concentration_findings"] == [] and low["considerations"] == []
    assert low["notify_competent_authority"] is False


def test_an_unregistered_function_is_refused_not_defaulted():
    with pytest.raises(InvalidRiskAssessmentError, match="not in the function register"):
        assess("unknown_function")


def test_a_clean_critical_arrangement_meets_its_preconditions_and_owes_notice():
    a = assess()
    assert a["preconditions_met"] is True and a["blocking"] == []
    assert a["notify_competent_authority"] is True  # Art. 28(3), fifth subparagraph
    assert [c["consideration"] for c in a["considerations"]] == [
        "alternative_solutions", "insolvency_law_and_urgent_data_recovery", "most_up_to_date_security_standards"]


@pytest.mark.parametrize("kwargs, finding, basis", [
    ({"supervisory": False}, "supervisory_conditions_not_met", "Art. 28(4)(b)"),
    ({"dd": None}, "due_diligence_not_undertaken", "Art. 28(4)(d)"),
    ({"dd": ""}, "due_diligence_not_undertaken", "Art. 28(4)(d)"),
    ({"coi": {"assessed": False, "identified": []}}, "conflicts_of_interest_not_assessed", "Art. 28(4)(e)"),
    ({"standards": []}, "no_information_security_standard", "Art. 28(5)"),
])
def test_each_precondition_blocks(kwargs, finding, basis):
    a = assess(**kwargs)
    assert a["preconditions_met"] is False
    assert a["blocking"] == [{"finding": finding, "basis": basis}]


def test_preconditions_apply_to_every_function_not_only_critical_ones():
    assert assess("intranet_wiki", standards=[])["preconditions_met"] is False


def test_concentration_findings():
    existing = [{"provider_handle": SIBLING, "function": "card_issuing", "critical_or_important": True},
                {"provider_handle": P, "function": "intranet_wiki", "critical_or_important": False}]
    a = assess(prof=profile(substitutable=False, closely_connected=[SIBLING]), arrangements=existing)
    assert a["concentration_findings"] == [
        {"finding": "not_easily_substitutable", "basis": "Art. 29(1)(a)", "refs": []},
        {"finding": "multiple_arrangements_same_or_connected_provider", "basis": "Art. 29(1)(b)", "refs": [SIBLING]},
    ]


def test_a_non_critical_arrangement_with_the_same_provider_is_not_concentration():
    existing = [{"provider_handle": P, "function": "intranet_wiki", "critical_or_important": False}]
    assert assess(arrangements=existing)["concentration_findings"] == []


def test_subcontracting_and_third_country_findings():
    prof = profile(established_in="US", subcontracting_permitted=True, subcontractors=[
        {"provider_handle": SUB1, "established_in": "IE", "tier": 1},
        {"provider_handle": SUB2, "established_in": "IN", "tier": 2}])
    a = assess(prof=prof)
    assert [(f["finding"], f["refs"]) for f in a["concentration_findings"]] == [
        ("subcontracting_permitted", [SUB1, SUB2]),
        ("third_country_subcontractor", [SUB2]),
        ("third_country_provider", [P]),
        ("subcontracting_chain", [SUB2]),
    ]
    assert a["subcontractors"][0]["tier"] == 1


def test_eea_states_are_not_third_countries():
    assert {"NO", "IS", "LI", "DE"} <= EU_EEA and "CH" not in EU_EEA and "GB" not in EU_EEA
    a = assess(prof=profile(established_in="NO", data_locations=["NO", "CH"]))
    assert all(f["finding"] != "third_country_provider" for f in a["concentration_findings"])
    assert a["locations_outside_eu_eea"] == ["CH"]


@pytest.mark.parametrize("prof, match", [
    (profile(subcontractors=[{"provider_handle": SUB1, "established_in": "IE", "tier": 1}]), "does not permit"),
    (profile(subcontracting_permitted=True, subcontractors=[{"provider_handle": SUB1, "established_in": "IE",
                                                             "tier": 2}]), "tier-1"),
    (profile(closely_connected=[P]), "itself"),
    (profile(data_locations=["Germany"]), "alpha-2"),
    (profile(service_locations=[]), "at least one country"),
])
def test_inconsistent_profiles_are_refused(prof, match):
    with pytest.raises(InvalidRiskAssessmentError, match=match):
        assess(prof=prof)


def test_boundary_refusals():
    with pytest.raises(InvalidRiskAssessmentError, match="provider handle"):
        assess(handle="Acme Cloud Ltd")
    with pytest.raises(InvalidRiskAssessmentError, match="boolean"):
        assess(supervisory="false")
    with pytest.raises(InvalidRiskAssessmentError, match="identified but not assessed"):
        assess(coi={"assessed": False, "identified": ["coi:1"]})
    with pytest.raises(InvalidRiskAssessmentError, match="twice"):
        assess(register=REGISTER + [REGISTER[0]])


def test_the_assessment_id_replays_and_tracks_content():
    assert assess()["assessment_id"] == assess()["assessment_id"]
    assert assess()["assessment_id"] != assess(standards=["std:iso27001-2022", "std:soc2"])["assessment_id"]


# --- contractual provisions (Art. 30) ------------------------------------------------------------------------


def test_the_clause_set_follows_the_article():
    every = [c for c, _, e in CLAUSES if e]
    critical = [c for c, _, e in CLAUSES if not e]
    assert every == ["30(1)"] + [f"30(2)({x})" for x in "abcdefghi"]
    assert critical == ["30(3)(a)", "30(3)(b)", "30(3)(c)", "30(3)(d)", "30(3)(e)(i)", "30(3)(e)(ii)",
                        "30(3)(e)(iii)", "30(3)(e)(iv)", "30(3)(f)"]


def test_a_complete_contract_is_compliant():
    p = check()
    assert p["compliant"] is True and p["absent"] == [] and len(p["clauses"]) == len(CLAUSES)


def test_a_non_critical_arrangement_needs_only_30_1_and_30_2():
    a = assess("intranet_wiki")
    p = check(a, clauses=all_clauses(False))
    assert p["compliant"] is True and len(p["clauses"]) == 10


def test_an_art_30_3_clause_on_a_non_critical_arrangement_is_kept_as_not_required():
    a = assess("intranet_wiki")
    p = check(a, clauses=all_clauses(False, **{"30(3)(d)": {"status": "absent", "deviation_ref": None}}))
    assert p["compliant"] is True
    assert p["clauses"][-1] == {"clause": "30(3)(d)", "requires": CLAUSES[13][1], "required": False,
                                "status": "absent", "deviation_ref": None}


def test_absent_and_deviating_clauses_are_listed():
    p = check(clauses=all_clauses(**{"30(2)(f)": {"status": "absent", "deviation_ref": None},
                                     "30(3)(f)": {"status": "absent", "deviation_ref": None},
                                     "30(2)(h)": {"status": "present_with_deviation", "deviation_ref": "dev:notice"}}))
    assert p["compliant"] is False
    assert p["absent"] == ["30(2)(f)", "30(3)(f)"] and p["deviations"] == ["30(2)(h)"]


def test_a_missing_required_clause_is_refused_not_assumed():
    clauses = all_clauses()
    del clauses["30(3)(e)(iv)"]
    with pytest.raises(InvalidProvisionsCheckError, match=r"30\(3\)\(e\)\(iv\) has no status"):
        check(clauses=clauses)


def test_a_clause_the_article_does_not_have_is_refused():
    with pytest.raises(InvalidProvisionsCheckError, match="no clause"):
        check(clauses=all_clauses(**{"30(2)(j)": {"status": "present", "deviation_ref": None}}))


def test_delegation_only_for_a_microenterprise_and_only_audit_rights():
    delegated = {"status": "delegated", "deviation_ref": None}
    p = check(clauses=all_clauses(**{"30(3)(e)(i)": delegated}), micro=True)
    assert p["compliant"] is True
    with pytest.raises(InvalidProvisionsCheckError, match="microenterprise"):
        check(clauses=all_clauses(**{"30(3)(e)(i)": delegated}), micro=False)
    with pytest.raises(InvalidProvisionsCheckError, match="microenterprise"):
        check(clauses=all_clauses(**{"30(3)(f)": delegated}), micro=True)


def test_a_deviation_reference_is_set_exactly_with_a_deviation():
    with pytest.raises(InvalidProvisionsCheckError, match="reference"):
        check(clauses=all_clauses(**{"30(2)(a)": {"status": "present_with_deviation", "deviation_ref": None}}))
    with pytest.raises(InvalidProvisionsCheckError, match="is set but"):
        check(clauses=all_clauses(**{"30(2)(a)": {"status": "present", "deviation_ref": "dev:1"}}))


# --- register entry (Art. 28(3)) -----------------------------------------------------------------------------


def test_the_row_joins_both_steps_and_replays():
    r = row()
    a = assess()
    assert r["assessment_id"] == a["assessment_id"] and r["check_id"] == check(a)["check_id"]
    assert r["critical_or_important"] is True and r["notify_competent_authority"] is True
    assert r["row_id"] == row()["row_id"]


def test_a_non_compliant_arrangement_is_still_registered():
    a = assess(dd=None)
    p = check(a, clauses=all_clauses(**{"30(2)(d)": {"status": "absent", "deviation_ref": None}}))
    r = row(a, p)
    assert r["preconditions_met"] is False and r["provisions_compliant"] is False
    assert r["absent_clauses"] == ["30(2)(d)"]


def test_mismatched_joins_are_refused():
    a, other = assess(), assess(standards=["std:soc2"])
    with pytest.raises(InvalidRegisterEntryError, match="not composed from this assessment"):
        compose_register_entry(other, check(a), "contract:cloud-2026", "wf:x", "exec:1", T1)
    with pytest.raises(InvalidRegisterEntryError, match="different contract"):
        compose_register_entry(a, check(a), "contract:other", "wf:x", "exec:1", T1)
    tampered = copy.deepcopy(check(a))
    tampered["critical_or_important"] = False
    with pytest.raises(InvalidRegisterEntryError, match="disagree"):
        compose_register_entry(a, tampered, "contract:cloud-2026", "wf:x", "exec:1", T1)


# --- periodic review (Art. 28(3), 28(7)) ---------------------------------------------------------------------


def test_a_quiet_window_records_no_runtime_drift():
    rv = review()
    assert rv["runtime_drift"] == "no_runtime_drift" and rv["termination_grounds"] == []
    assert rv["exit_decision_due"] is False and rv["register_update_required"] is False


def test_no_impact_verdicts_are_not_drift():
    ev = [{"evidence_ref": "sce:1", "provider_handle": P, "verdict": "no_impact", "observed_at": T1}]
    assert review(evidence=ev)["runtime_drift"] == "no_runtime_drift"


def test_the_worst_verdict_is_recorded_and_a_compromise_is_ground_c():
    ev = [{"evidence_ref": "sce:2", "provider_handle": P, "verdict": "confirmed_compromise", "observed_at": T1},
          {"evidence_ref": "sce:1", "provider_handle": P, "verdict": "watch", "observed_at": T1}]
    rv = review(evidence=ev)
    assert rv["runtime_drift"] == "confirmed_compromise"
    assert rv["termination_grounds"] == [{"ground": "Art. 28(7)(c)", "refs": ["sce:2"]}]
    assert rv["exit_decision_due"] is True


def test_a_watch_verdict_is_drift_but_no_ground():
    ev = [{"evidence_ref": "sce:1", "provider_handle": P, "verdict": "watch", "observed_at": T1}]
    rv = review(evidence=ev)
    assert rv["runtime_drift"] == "watch" and rv["termination_grounds"] == []


def test_all_four_termination_grounds():
    rv = review(breaches=[{"breach_ref": "br:minor", "significant": False}, {"breach_ref": "br:sla", "significant": True}],
                changes=[{"change_ref": "chg:owner", "kind": "provider_situation", "capable_of_altering_performance": True,
                          "changed_at": T1},
                         {"change_ref": "chg:logo", "kind": "provider_situation",
                          "capable_of_altering_performance": False, "changed_at": T1}],
                evidence=[{"evidence_ref": "sce:9", "provider_handle": P, "verdict": "confirmed_compromise",
                           "observed_at": T1}],
                impeded=True)
    assert rv["termination_grounds"] == [
        {"ground": "Art. 28(7)(a)", "refs": ["br:sla"]},
        {"ground": "Art. 28(7)(b)", "refs": ["chg:owner"]},
        {"ground": "Art. 28(7)(c)", "refs": ["sce:9"]},
        {"ground": "Art. 28(7)(d)", "refs": []},
    ]
    assert rv["register_update_required"] is False  # a change of the provider's situation is not a row field


@pytest.mark.parametrize("kind", ["contract", "locations", "subcontracting", "function"])
def test_a_change_to_a_row_field_requires_a_register_update(kind):
    rv = review(changes=[{"change_ref": "chg:1", "kind": kind, "capable_of_altering_performance": False,
                          "changed_at": T1}])
    assert rv["register_update_required"] is True and rv["termination_grounds"] == []


def test_a_function_that_became_critical_is_flagged_and_notified():
    a = assess("intranet_wiki")
    r = row(a, check(a, clauses=all_clauses(False)))
    promoted = [{"function": "intranet_wiki", "critical_or_important": True}]
    rv = review(r, register=promoted)
    assert rv["became_critical_or_important"] is True and rv["notify_competent_authority"] is True
    assert rv["register_update_required"] is True


def test_review_refusals():
    with pytest.raises(InvalidPeriodicReviewError, match="no longer in the function register"):
        review(register=[REGISTER[1]])
    with pytest.raises(InvalidPeriodicReviewError, match="another provider"):
        review(evidence=[{"evidence_ref": "sce:1", "provider_handle": SIBLING, "verdict": "watch",
                          "observed_at": T1}])
    with pytest.raises(InvalidPeriodicReviewError, match="postdates"):
        review(evidence=[{"evidence_ref": "sce:1", "provider_handle": P, "verdict": "watch",
                          "observed_at": "2027-06-01T00:00:00Z"}])
    with pytest.raises(InvalidPeriodicReviewError, match="precede"):
        review(at=T0)
    with pytest.raises(InvalidPeriodicReviewError, match="must be one of"):
        review(evidence=[{"evidence_ref": "sce:1", "provider_handle": P, "verdict": "unknown",
                          "observed_at": T1}])


# --- exit assessment (Art. 28(8)) ----------------------------------------------------------------------------


def test_a_ready_strategy_without_a_trigger_attests_readiness():
    x = exit_()
    assert x["exit_invoked"] is False and x["exit_trigger"] is None and x["trigger_basis"] is None
    assert x["exit_strategy_required"] is True and x["exit_ready"] is True and x["gaps"] == []


def test_no_strategy_for_a_critical_function_is_a_gap():
    x = exit_(strat=None)
    assert x["exit_ready"] is False
    assert x["gaps"][0] == {"gap": "no_exit_strategy", "basis": "Art. 28(8), first subparagraph"}


def test_each_strategy_gap():
    x = exit_(strat=strategy(last_tested_at=None, last_reviewed_at="2025-01-01T00:00:00Z", alternatives=[],
                             transition_plan_ref="", contingency_ref=None))
    assert sorted(g["gap"] for g in x["gaps"]) == sorted([
        "exit_plan_never_tested", "exit_plan_review_overdue", "no_alternative_solution", "no_transition_plan",
        "no_contingency_measures"])


def test_a_contract_without_a_transition_period_is_a_gap():
    a = assess()
    r = row(a, check(a, clauses=all_clauses(**{"30(3)(f)": {"status": "absent", "deviation_ref": None}})))
    x = exit_(r)
    assert x["gaps"] == [{"gap": "no_contractual_transition_period", "basis": "Art. 30(3)(f)"}]


def test_a_function_promoted_after_registration_needs_its_contract_rechecked():
    a = assess("intranet_wiki")
    r = row(a, check(a, clauses=all_clauses(False)))
    rv = review(r, register=[{"function": "intranet_wiki", "critical_or_important": True}])
    x = exit_(r, rv)
    assert x["exit_strategy_required"] is True
    assert x["gaps"] == [{"gap": "contract_not_checked_against_art_30_3", "basis": "Art. 30(3)"}]


def test_a_non_critical_arrangement_needs_no_exit_strategy():
    a = assess("intranet_wiki")
    r = row(a, check(a, clauses=all_clauses(False)))
    x = exit_(r, strat=None)
    assert x["exit_strategy_required"] is False and x["exit_ready"] is True and x["gaps"] == []


def test_a_trigger_names_its_basis_and_whether_the_review_found_it():
    ev = [{"evidence_ref": "sce:2", "provider_handle": P, "verdict": "confirmed_compromise", "observed_at": T1}]
    r = row()
    found = exit_(r, review(r, evidence=ev), trigger="ict_risk_weakness")
    assert found["exit_invoked"] is True and found["trigger_basis"] == "Art. 28(7)(c)"
    assert found["trigger_identified_in_review"] is True
    unfound = exit_(r, trigger="significant_breach")
    assert unfound["trigger_identified_in_review"] is False
    elected = exit_(r, trigger="operator_election")
    assert elected["trigger_basis"] is None and elected["trigger_identified_in_review"] is None
    assert exit_(r, trigger="provider_failure")["trigger_basis"] == "Art. 28(8)"
    assert set(TRIGGERS) == {"significant_breach", "material_change", "ict_risk_weakness", "supervision_impeded",
                             "provider_failure", "service_deterioration", "operator_election"}


def test_exit_refusals_and_replay():
    r = row()
    other = compose_register_entry(assess(), check(), "contract:cloud-2026", "wf:dora-tpr", "exec:0009", T1)
    with pytest.raises(InvalidExitAssessmentError, match="another register row"):
        exit_(other, review(r))
    with pytest.raises(InvalidExitAssessmentError, match="must be one of"):
        exit_(r, trigger="regulatory_direction")
    with pytest.raises(InvalidExitAssessmentError, match="postdates"):
        exit_(r, strat=strategy(last_tested_at="2027-06-01T00:00:00Z"))
    assert exit_(r)["attestation_id"] == exit_(r)["attestation_id"]
    assert exit_(r, trigger="operator_election")["attestation_id"] == exit_(r)["attestation_id"]
