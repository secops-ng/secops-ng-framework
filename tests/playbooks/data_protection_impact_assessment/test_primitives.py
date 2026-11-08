from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from compilers._shared.cacao_parser import secops_extension
from content.playbooks.data_protection_impact_assessment.primitives import (
    CHANGE_TRIGGERS,
    RISK_EVENTS,
    SPECIAL_CATEGORIES,
    WP248_CRITERIA,
    InvalidConsultationError,
    InvalidDpiaDocumentError,
    InvalidMitigationsError,
    InvalidNecessityAssessmentError,
    InvalidPriorConsultationError,
    InvalidProcessingClassificationError,
    InvalidProcessingDescriptionError,
    InvalidReviewScheduleError,
    InvalidRiskAssessmentError,
    InvalidScreeningError,
    assess_necessity_and_proportionality,
    assess_risks,
    classify_processing,
    compose_dpia_document,
    compose_processing_description,
    determine_prior_consultation,
    document_mitigations,
    record_dpo_consultation,
    schedule_review,
    screen_dpia_triggers,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
PLAYBOOK = REPO_ROOT / "content" / "playbooks" / "data_protection_impact_assessment" / "playbook.cacao.yaml"
PROC = "ropa:hr-absence-analytics"
SCALE = ["negligible", "limited", "significant", "maximum"]
FLOOR = {"likelihood": "significant", "severity": "significant"}


def scr(**over) -> dict:
    s = {"art_35_3": [], "art_35_4_list_entry_ref": None, "art_35_5_list_entry_ref": None, "wp248_criteria": [],
         "art_35_10": None, "similar_assessment_ref": None, "not_high_risk_justification_ref": None,
         "dpo_designated": True, "dpo_views_ref": None, "controller_elects_dpia": False}
    return {**s, **over}


def screen(**over) -> dict:
    return screen_dpia_triggers(PROC, scr(**over), "2026-10-26T09:00:00Z")


def required() -> dict:
    return screen(wp248_criteria=["sensitive_or_highly_personal_data", "vulnerable_data_subjects"])


def ropa(**over) -> dict:
    r = {"processing_ref": PROC, "controller_role": "controller",
         "personal_data_categories": ["absence_records", "contact_details"], "special_categories": ["health_data"],
         "criminal_offence_data": False, "art_10_basis_ref": None, "subject_categories": ["employees"],
         "vulnerable_subjects": ["employees"], "lawful_bases": ["c", "f"], "art_9_2_condition": "b"}
    return {**r, **over}


def classify(s=None, **over) -> dict:
    return classify_processing(s or required(), ropa(**over), "2026-10-26T09:10:00Z")


def desc(**over) -> dict:
    d = {"purposes": ["sickness absence administration", "workforce planning"],
         "legitimate_interest": "planning cover for absent staff", "nature_scope_context_ref": "doc:nsc-1",
         "functional_description_ref": "doc:flow-1",
         "recipients": [{"recipient_ref": "org:payroll-processor", "role": "processor", "third_country": None,
                         "transfer_mechanism": None}],
         "retention": [{"data_category": "absence_records", "period": "P3Y", "criteria_ref": None},
                       {"data_category": "contact_details", "period": None, "criteria_ref": "policy:hr-retention"}],
         "assets": [{"asset_ref": "sys:hr-suite", "kind": "software"}, {"asset_ref": "team:hr-ops", "kind": "people"}],
         "codes_of_conduct": []}
    return {**d, **over}


def describe(c=None, **over) -> dict:
    return compose_processing_description(c or classify(), desc(**over), "2026-10-26T09:20:00Z")


RIGHTS = {"information": "notice:hr-1", "access_and_portability": "proc:dsar", "rectification_and_erasure": "proc:dsar",
          "objection_and_restriction": "proc:dsar", "processor_relationships": "dpa:payroll",
          "transfer_safeguards": None}


def necessity_input(**over) -> dict:
    a = {"necessary": True, "reasoning_ref": "memo:necessity-1", "alternatives": [],
         "data_minimisation": [{"data_category": "absence_records", "necessary": True},
                               {"data_category": "contact_details", "necessary": True}],
         "rights_measures": dict(RIGHTS)}
    return {**a, **over}


def assess(c=None, d=None, **over) -> dict:
    c = c or classify()
    return assess_necessity_and_proportionality(c, d or describe(c), necessity_input(**over), "2026-10-26T09:30:00Z")


def risk(ref, event, likelihood="limited", severity="limited") -> dict:
    return {"risk_ref": ref, "event": event, "sources": ["src:insider"], "threats": ["thr:over-broad-access"],
            "impacts": ["imp:discrimination"], "likelihood": likelihood, "severity": severity}


def all_events(**high) -> list:
    return [risk(f"risk:{ev}", ev, *high.get(ev, ("limited", "limited"))) for ev in RISK_EVENTS]


def risks(rs=None, n=None, scale=SCALE, floor=FLOOR) -> dict:
    return assess_risks(n or assess(), scale, floor, all_events() if rs is None else rs, "2026-10-26T09:40:00Z")


# --------------------------------------------------------------------------- screen_dpia_triggers


@pytest.mark.parametrize(("over", "req", "basis"), [
    ({"art_35_3": ["b"]}, True, "art_35_3"),
    ({"art_35_4_list_entry_ref": "sa:list:7"}, True, "art_35_4_list"),
    ({"art_35_5_list_entry_ref": "sa:whitelist:2"}, False, "art_35_5_list"),
    ({"wp248_criteria": ["large_scale", "systematic_monitoring"]}, True, "wp248_two_or_more_criteria"),
    ({"wp248_criteria": ["large_scale"]}, False, "wp248_single_criterion"),
    ({}, False, "no_high_risk_indicator"),
])
def test_screening_applies_article_35_and_the_wp248_rule(over, req, basis) -> None:
    s = screen(**over)
    assert s["dpia_required"] is req and s["basis"] == basis and s["retained_on_ledger"] is True


def test_the_article_35_10_exemption_comes_first() -> None:
    exemption = {"lawful_basis": "e", "legal_basis_ref": "law:act-12", "prior_assessment_ref": "ia:act-12",
                 "member_state_requires_dpia": False}
    s = screen(art_35_3=["a"], art_35_10=exemption)
    assert s["dpia_required"] is False and s["basis"] == "art_35_10_exemption" and s["art_35_10_applies"] is True


def test_the_exemption_falls_away_when_the_member_state_requires_a_dpia() -> None:
    exemption = {"lawful_basis": "c", "legal_basis_ref": "law:act-12", "prior_assessment_ref": "ia:act-12",
                 "member_state_requires_dpia": True}
    s = screen(art_35_3=["a"], art_35_10=exemption)
    assert s["dpia_required"] is True and s["basis"] == "art_35_3" and s["art_35_10_applies"] is False


def test_the_exemption_needs_an_article_6_1_c_or_e_basis() -> None:
    with pytest.raises(InvalidScreeningError):
        screen(art_35_10={"lawful_basis": "f", "legal_basis_ref": "law:x", "prior_assessment_ref": "ia:x",
                          "member_state_requires_dpia": False})


def test_an_existing_assessment_of_similar_processing_covers_it() -> None:
    s = screen(art_35_3=["c"], similar_assessment_ref="dpia:cctv-site-a")
    assert s["dpia_required"] is False and s["basis"] == "covered_by_similar_assessment"


def test_the_mandatory_cases_override_the_article_35_5_list() -> None:
    assert screen(art_35_4_list_entry_ref="sa:list:7", art_35_5_list_entry_ref="sa:whitelist:2")["dpia_required"]


def test_two_criteria_can_be_set_aside_only_with_a_justification_and_the_dpo_views() -> None:
    crit = ["large_scale", "matching_or_combining_datasets"]
    without_views = screen(wp248_criteria=crit, not_high_risk_justification_ref="memo:nhr-1")
    assert without_views["dpia_required"] is True and without_views["justification_rejected"] == "dpo_views_missing"
    with_views = screen(wp248_criteria=crit, not_high_risk_justification_ref="memo:nhr-1", dpo_views_ref="dpo:v-1")
    assert with_views["dpia_required"] is False and with_views["basis"] == "documented_not_high_risk"
    no_dpo = screen(wp248_criteria=crit, not_high_risk_justification_ref="memo:nhr-1", dpo_designated=False)
    assert no_dpo["dpia_required"] is False and no_dpo["justification_rejected"] is None


def test_the_controller_may_elect_a_dpia_where_none_is_required() -> None:
    s = screen(wp248_criteria=["large_scale"], controller_elects_dpia=True)
    assert s["dpia_required"] is True and s["controller_elected"] is True and s["basis"] == "wp248_single_criterion"
    assert screen(art_35_3=["a"], controller_elects_dpia=True)["controller_elected"] is False


def test_the_criteria_are_recorded_in_wp248_order() -> None:
    s = screen(wp248_criteria=["prevents_exercising_a_right", "evaluation_or_scoring"])
    assert s["wp248_criteria"] == ["evaluation_or_scoring", "prevents_exercising_a_right"]
    assert s["wp248_criteria_count"] == 2


@pytest.mark.parametrize("over", [
    {"art_35_3": ["d"]},
    {"wp248_criteria": ["large_scale", "large_scale"]},
    {"wp248_criteria": ["profiling"]},
    {"dpo_designated": "true"},
    {"controller_elects_dpia": 1},
])
def test_a_malformed_screening_is_refused(over) -> None:
    with pytest.raises(InvalidScreeningError):
        screen(**over)


def test_screening_ids_depend_on_the_outcome() -> None:
    assert screen()["screening_result_ref"] != screen(art_35_3=["a"])["screening_result_ref"]
    assert screen()["dpia_case_id"] == screen(art_35_3=["a"])["dpia_case_id"]
    assert screen() == screen()


# --------------------------------------------------------------------------- classify_processing_type


def test_classification_takes_the_shape_of_the_article_30_record() -> None:
    c = classify()
    assert c["special_categories"] == ["health_data"] and c["special_category_involved"] is True
    assert c["lawful_bases"] == ["c", "f"] and c["art_9_2_condition"] == "b" and c["lawfulness_gaps"] == []


@pytest.mark.parametrize(("over", "gaps"), [
    ({"lawful_bases": []}, ["no_article_6_basis"]),
    ({"art_9_2_condition": None}, ["no_article_9_2_condition"]),
    ({"criminal_offence_data": True}, ["no_article_10_basis"]),
])
def test_lawfulness_gaps_are_recorded(over, gaps) -> None:
    assert classify(**over)["lawfulness_gaps"] == gaps


def test_the_dpia_is_the_controllers_not_the_processors() -> None:
    with pytest.raises(InvalidProcessingClassificationError, match="processor"):
        classify(controller_role="processor")
    assert classify(controller_role="joint_controller")["controller_role"] == "joint_controller"


def test_classification_is_refused_when_no_dpia_is_required() -> None:
    with pytest.raises(InvalidProcessingClassificationError, match="dpia_required"):
        classify(s=screen())


@pytest.mark.parametrize("over", [
    {"processing_ref": "ropa:other"},
    {"special_categories": [], "art_9_2_condition": "a"},
    {"art_10_basis_ref": "law:x"},
    {"special_categories": ["criminal_records"]},
    {"personal_data_categories": []},
    {"vulnerable_subjects": ["students"]},
])
def test_an_inconsistent_record_is_refused(over) -> None:
    with pytest.raises(InvalidProcessingClassificationError):
        classify(**over)


# --------------------------------------------------------------------------- gather_processing_description


def test_a_full_description_is_complete() -> None:
    d = describe()
    assert d["complete"] is True and d["gaps"] == [] and d["transfers"] == []
    assert [r["data_category"] for r in d["retention"]] == ["absence_records", "contact_details"]


def test_missing_elements_are_recorded_as_gaps() -> None:
    d = describe(legitimate_interest=None, assets=[],
                 retention=[{"data_category": "absence_records", "period": None, "criteria_ref": None}],
                 recipients=[{"recipient_ref": "org:analytics-us", "role": "processor", "third_country": "US",
                              "transfer_mechanism": None}])
    assert d["complete"] is False
    assert d["gaps"] == ["legitimate_interest_undescribed", "retention_undetermined:absence_records",
                         "retention_undetermined:contact_details",
                         "transfer_without_chapter_v_basis:org:analytics-us", "assets_unidentified"]
    assert [t["recipient_ref"] for t in d["transfers"]] == ["org:analytics-us"]


def test_a_transfer_with_a_chapter_v_basis_is_not_a_gap() -> None:
    d = describe(recipients=[{"recipient_ref": "org:analytics-us", "role": "processor", "third_country": "US",
                              "transfer_mechanism": "appropriate_safeguards"}])
    assert d["complete"] is True and d["transfers"][0]["transfer_mechanism"] == "appropriate_safeguards"


@pytest.mark.parametrize("over", [
    {"purposes": []},
    {"purposes": ["x", "x"]},
    {"retention": [{"data_category": "unknown", "period": "P1Y", "criteria_ref": None}]},
    {"retention": [{"data_category": "absence_records", "period": "3 years", "criteria_ref": None}]},
    {"recipients": [{"recipient_ref": "org:x", "role": "processor", "third_country": None,
                     "transfer_mechanism": "derogation"}]},
    {"recipients": [{"recipient_ref": "org:x", "role": "processor", "third_country": "usa",
                     "transfer_mechanism": None}]},
    {"assets": [{"asset_ref": "sys:x", "kind": "cloud"}]},
])
def test_a_malformed_description_is_refused(over) -> None:
    with pytest.raises(InvalidProcessingDescriptionError):
        describe(**over)


def test_a_legitimate_interest_needs_article_6_1_f() -> None:
    with pytest.raises(InvalidProcessingDescriptionError, match="6\\(1\\)\\(f\\)"):
        describe(c=classify(lawful_bases=["c"]))


# --------------------------------------------------------------------------- assess_necessity_and_proportionality


def test_a_necessary_minimised_processing_with_its_measures_is_proportionate() -> None:
    n = assess()
    assert (n["necessary"], n["proportionate"], n["outcome"], n["findings"]) == \
        (True, True, "necessary_and_proportionate", [])


def test_a_less_intrusive_alternative_that_suffices_defeats_necessity() -> None:
    n = assess(alternatives=[{"alternative_ref": "alt:aggregate-only", "suffices": True, "reasoning_ref": "memo:a"},
                             {"alternative_ref": "alt:manual", "suffices": False, "reasoning_ref": "memo:b"}])
    assert n["necessary"] is False and n["outcome"] == "not_necessary"
    assert n["findings"] == ["less_intrusive_alternative_suffices:alt:aggregate-only"]


def test_excess_data_and_unsettled_storage_are_not_proportionate() -> None:
    c = classify()
    d = describe(c, retention=[{"data_category": "absence_records", "period": "P3Y", "criteria_ref": None}])
    n = assess(c, d, data_minimisation=[{"data_category": "absence_records", "necessary": True},
                                        {"data_category": "contact_details", "necessary": False}])
    assert n["outcome"] == "not_proportionate" and n["excess_categories"] == ["contact_details"]
    assert n["findings"] == ["not_minimised:contact_details", "storage_limitation_unsettled"]


def test_lawfulness_gaps_and_missing_rights_measures_are_owed() -> None:
    c = classify(art_9_2_condition=None)
    n = assess(c, rights_measures={**RIGHTS, "information": None, "processor_relationships": None})
    assert n["outcome"] == "measures_owed"
    assert n["measures_owed"] == ["no_article_9_2_condition", "information", "processor_relationships"]


def test_transfer_safeguards_are_owed_only_when_there_is_a_transfer() -> None:
    c = classify()
    d = describe(c, recipients=[{"recipient_ref": "org:analytics-us", "role": "controller", "third_country": "US",
                                 "transfer_mechanism": "adequacy_decision"}])
    assert assess(c, d)["measures_owed"] == ["transfer_safeguards"]
    assert assess(c)["measures_owed"] == []


def test_minimisation_must_cover_exactly_the_classified_categories() -> None:
    with pytest.raises(InvalidNecessityAssessmentError, match="exactly"):
        assess(data_minimisation=[{"data_category": "absence_records", "necessary": True}])


def test_a_description_of_another_classification_is_refused() -> None:
    with pytest.raises(InvalidNecessityAssessmentError, match="different classification"):
        assess_necessity_and_proportionality(classify(), describe(classify(lawful_bases=["c"],
                                                                           art_9_2_condition="b"),
                                                                  legitimate_interest=None),
                                             necessity_input(), "2026-10-26T09:30:00Z")


# --------------------------------------------------------------------------- identify_and_assess_risks


def test_risks_reaching_the_floor_on_both_axes_are_high() -> None:
    r = risks(all_events(illegitimate_access=("significant", "maximum"), disappearance=("maximum", "limited")))
    assert r["high_risks"] == ["risk:illegitimate_access"] and r["any_high_risk"] is True
    assert r["complete"] is True and r["unassessed_events"] == []


def test_an_assessment_missing_a_reference_event_is_incomplete() -> None:
    r = risks([risk("risk:a", "illegitimate_access"), risk("risk:b", "other")])
    assert r["complete"] is False and r["unassessed_events"] == ["undesired_modification", "disappearance"]


@pytest.mark.parametrize("field", ["sources", "threats", "impacts"])
def test_a_risk_without_sources_threats_or_impacts_is_refused(field) -> None:
    bad = {**risk("risk:a", "illegitimate_access"), field: []}
    with pytest.raises(InvalidRiskAssessmentError):
        risks([bad])


@pytest.mark.parametrize(("scale", "floor"), [
    (["only"], {"likelihood": "only", "severity": "only"}),
    (["low", "low"], {"likelihood": "low", "severity": "low"}),
    (SCALE, {"likelihood": "high", "severity": "maximum"}),
])
def test_a_malformed_calibration_is_refused(scale, floor) -> None:
    with pytest.raises(InvalidRiskAssessmentError):
        risks(scale=scale, floor=floor)


def test_the_necessity_outcome_is_carried_into_the_risk_record() -> None:
    n = assess(alternatives=[{"alternative_ref": "alt:x", "suffices": True, "reasoning_ref": "memo:x"}])
    assert risks(n=n)["necessity_outcome"] == "not_necessary"


# --------------------------------------------------------------------------- identity


def test_records_that_differ_in_any_field_have_different_ids() -> None:
    c = classify()
    assert classify(lawful_bases=["c"], art_9_2_condition="b")["classification_id"] != c["classification_id"]
    d = describe(c)
    other_retention = [{"data_category": "absence_records", "period": "P2Y", "criteria_ref": None},
                       {"data_category": "contact_details", "period": "P1Y", "criteria_ref": None}]
    assert describe(c, retention=other_retention)["processing_description_ref"] != d["processing_description_ref"]
    n = assess(c, d)
    assert assess(c, d, reasoning_ref="memo:necessity-2")["necessity_assessment_id"] != n["necessity_assessment_id"]
    other = [{**r, "sources": ["src:outsider"]} for r in all_events()]
    assert risks(other, n=n)["risk_assessment_ref"] != risks(n=n)["risk_assessment_ref"]
    assert risks(n=n) == risks(n=n)


# --------------------------------------------------------------------------- catalogue contract


def test_the_ten_primitives_back_the_ten_steps_and_stamp_no_undeclared_metric() -> None:
    doc = yaml.safe_load(PLAYBOOK.read_text(encoding="utf-8"))
    declared = set(secops_extension(doc).get("metric_refs") or [])
    names = [s["name"] for s in doc["workflow"].values() if s["type"] == "action"]
    assert names == ["screen_dpia_triggers", "classify_processing_type", "gather_processing_description",
                     "assess_necessity_and_proportionality", "identify_and_assess_risks",
                     "identify_and_document_mitigations", "dpo_consultation", "determine_article_36_gate",
                     "produce_dpia_document", "schedule_review_cadence"]
    chain = full_chain()
    for out in (*chain, schedule(chain[-1])):
        assert set(out["metric_stamps"]) <= declared


def test_the_vocabularies_follow_the_regulation_and_wp248() -> None:
    assert len(SPECIAL_CATEGORIES) == 8 and len(WP248_CRITERIA) == 9
    assert RISK_EVENTS == ("illegitimate_access", "undesired_modification", "disappearance")


# =========================================================================== CORE-PRIM part 2

HIGH_ACCESS = {"illegitimate_access": ("significant", "maximum")}
ENCRYPT = {"measure_ref": "m:encrypt-at-rest", "kind": "security_measure", "addresses": ["risk:illegitimate_access"],
           "control_refs": ["control.encryption_at_rest@v1"]}


def residual_as_assessed(r) -> list:
    return [{"risk_ref": x["risk_ref"], "likelihood": x["likelihood"], "severity": x["severity"]} for x in r["risks"]]


def lowered(r, ref="risk:illegitimate_access", to=("limited", "maximum")) -> list:
    return [{**x, "likelihood": to[0], "severity": to[1]} if x["risk_ref"] == ref else x for x in residual_as_assessed(r)]


def mitigate(r=None, measures=None, residual=None) -> dict:
    r = r or risks(all_events(**HIGH_ACCESS))
    return document_mitigations(r, [ENCRYPT] if measures is None else measures,
                                lowered(r) if residual is None else residual, "2026-10-26T09:50:00Z")


VIEWS = {"sought": True, "views_ref": "survey:staff-council-1", "decision_differs": False,
         "decision_reasons_ref": None, "not_sought_justification_ref": None}


def consult_input(**over) -> dict:
    c = {"dpo_designated": True, "dpo_ref": "person:dpo", "advice_ref": "advice:dpo-1", "advice_followed": True,
         "departure_reasons_ref": None, "alternative_accountability_ref": None, "data_subject_views": dict(VIEWS)}
    return {**c, **over}


def consult(m=None, **over) -> dict:
    return record_dpo_consultation(m or mitigate(), consult_input(**over), "2026-10-26T10:00:00Z")


def determine(m=None, member_state=False, submission=None) -> dict:
    return determine_prior_consultation(m or mitigate(), member_state, submission, "2026-10-26T10:10:00Z")


def full_chain(rs=None, residual=None, alternatives=(), consultation=None, member_state=False) -> tuple:
    s = required()
    c = classify(s)
    d = describe(c)
    n = assess(c, d, alternatives=list(alternatives))
    r = risks(all_events(**HIGH_ACCESS) if rs is None else rs, n=n)
    m = mitigate(r, residual=residual)
    k = consult(m, **(consultation or {}))
    g = determine(m, member_state)
    doc = compose_dpia_document(s, c, d, n, r, m, k, g, "wf:dpia", "exec:1", "2026-10-26T10:20:00Z")
    return s, c, d, n, r, m, k, g, doc


def schedule(doc, interval="P1Y", triggers=("purpose",), at="2026-10-26T10:30:00Z") -> dict:
    return schedule_review(doc, interval, list(triggers), "change:board", at)


# --------------------------------------------------------------------------- identify_and_document_mitigations


def test_a_measure_lowers_the_residual_risk_below_the_high_floor() -> None:
    m = mitigate()
    assert m["residual_high_risks"] == [] and m["untreated_risks"] == ["risk:disappearance",
                                                                       "risk:undesired_modification"]
    assert m["gaps"] == [] and m["complete"] is True
    assert next(x for x in m["residual_risks"] if x["risk_ref"] == "risk:illegitimate_access")["high"] is False


def test_an_untreated_high_risk_is_a_gap_and_stays_high() -> None:
    r = risks(all_events(**HIGH_ACCESS))
    m = mitigate(r, measures=[], residual=residual_as_assessed(r))
    assert m["gaps"] == ["untreated_high_risk:risk:illegitimate_access"]
    assert m["residual_high_risks"] == ["risk:illegitimate_access"]


@pytest.mark.parametrize("residual_of", [
    lambda r: lowered(r, to=("maximum", "maximum")),
    lambda r: lowered(r, ref="risk:disappearance", to=("negligible", "negligible")),
    lambda r: residual_as_assessed(r)[1:],
    lambda r: residual_as_assessed(r) + [residual_as_assessed(r)[0]],
])
def test_an_inconsistent_residual_level_is_refused(residual_of) -> None:
    r = risks(all_events(**HIGH_ACCESS))
    with pytest.raises(InvalidMitigationsError):
        mitigate(r, residual=residual_of(r))


def test_a_measure_for_an_unassessed_risk_is_refused() -> None:
    with pytest.raises(InvalidMitigationsError, match="does not list"):
        mitigate(measures=[{**ENCRYPT, "addresses": ["risk:unknown"]}])


def test_an_incomplete_risk_assessment_carries_over_as_a_gap() -> None:
    r = risks([risk("risk:illegitimate_access", "illegitimate_access")])
    assert mitigate(r, measures=[], residual=residual_as_assessed(r))["gaps"] == ["risk_assessment_incomplete"]


# --------------------------------------------------------------------------- dpo_consultation


def test_followed_dpo_advice_and_recorded_views_are_complete() -> None:
    k = consult()
    assert k["complete"] is True and k["advice_followed"] is True and k["data_subject_views"]["sought"] is True


@pytest.mark.parametrize(("over", "gap"), [
    ({"advice_followed": False}, "departure_from_dpo_advice_undocumented"),
    ({"advice_ref": None, "advice_followed": None}, "dpo_advice_missing"),
    ({"dpo_designated": False, "dpo_ref": None, "advice_ref": None, "advice_followed": None},
     "no_dpo_and_no_alternative_accountability"),
    ({"data_subject_views": {**VIEWS, "views_ref": None}}, "data_subject_views_unrecorded"),
    ({"data_subject_views": {**VIEWS, "decision_differs": True}}, "departure_from_data_subject_views_undocumented"),
    ({"data_subject_views": {**VIEWS, "sought": False, "views_ref": None}}, "not_seeking_views_unjustified"),
])
def test_undocumented_departures_and_missing_advice_are_gaps(over, gap) -> None:
    assert consult(**over)["gaps"] == [gap]


def test_documented_departures_and_alternatives_close_the_gaps() -> None:
    assert consult(advice_followed=False, departure_reasons_ref="memo:why-not")["complete"] is True
    assert consult(dpo_designated=False, dpo_ref=None, advice_ref=None, advice_followed=None,
                   alternative_accountability_ref="role:privacy-lead")["complete"] is True
    views = {**VIEWS, "sought": False, "views_ref": None, "not_sought_justification_ref": "memo:impracticable"}
    assert consult(data_subject_views=views)["complete"] is True


@pytest.mark.parametrize("over", [
    {"dpo_designated": False, "dpo_ref": None, "advice_ref": "advice:x", "advice_followed": None,
     "alternative_accountability_ref": "role:x"},
    {"advice_followed": None},
    {"advice_followed": "yes"},
])
def test_a_self_contradictory_consultation_is_refused(over) -> None:
    with pytest.raises(InvalidConsultationError):
        consult(**over)


# --------------------------------------------------------------------------- determine_article_36_gate


def test_a_residual_high_risk_requires_prior_consultation() -> None:
    r = risks(all_events(**HIGH_ACCESS))
    g = determine(mitigate(r, measures=[], residual=residual_as_assessed(r)))
    assert g["article_36_pre_consultation_flag"] is True and g["basis"] == ["residual_high_risk"]


def test_risks_mitigated_below_high_need_no_consultation_unless_member_state_law_says_so() -> None:
    assert determine()["article_36_pre_consultation_flag"] is False
    g = determine(member_state=True)
    assert g["article_36_pre_consultation_flag"] is True and g["basis"] == ["art_36_5_member_state_law"]


@pytest.mark.parametrize(("received", "extended", "due", "notice"), [
    ("2026-11-02T10:00:00Z", False, "2026-12-28T10:00:00Z", "2026-12-02T10:00:00Z"),
    ("2026-11-02T10:00:00Z", True, "2027-02-08T10:00:00Z", "2026-12-02T10:00:00Z"),
    ("2027-01-31T09:00:00Z", False, "2027-03-28T09:00:00Z", "2027-02-28T09:00:00Z"),
])
def test_the_article_36_2_windows_run_from_receipt(received, extended, due, notice) -> None:
    g = determine(member_state=True, submission={"received_at": received, "extended": extended})
    w = g["consultation_windows"]
    assert (w["advice_due_by"], w["extension_notice_due_by"]) == (due, notice)


def test_a_consultation_request_without_a_flag_is_refused() -> None:
    with pytest.raises(InvalidPriorConsultationError):
        determine(submission={"received_at": "2026-11-02T10:00:00Z", "extended": False})


# --------------------------------------------------------------------------- produce_dpia_document


def test_a_complete_chain_produces_a_final_document_that_may_proceed() -> None:
    doc = full_chain()[-1]
    assert doc["final"] is True and doc["open_items"] == [] and doc["conclusion"] == "may_proceed"


def test_a_residual_high_risk_concludes_prior_consultation_required() -> None:
    s, c, d, n, r, _, _, _, _ = full_chain()
    m = mitigate(r, measures=[ENCRYPT], residual=lowered(r, to=("significant", "significant")))
    k, g = consult(m), determine(m)
    doc = compose_dpia_document(s, c, d, n, r, m, k, g, "wf:dpia", "exec:1", "2026-10-26T10:20:00Z")
    assert doc["conclusion"] == "prior_consultation_required" and doc["article_36_pre_consultation_flag"] is True


def test_an_unnecessary_processing_concludes_do_not_proceed() -> None:
    alt = {"alternative_ref": "alt:aggregate-only", "suffices": True, "reasoning_ref": "memo:a"}
    assert full_chain(alternatives=[alt])[-1]["conclusion"] == "do_not_proceed"


def test_open_items_keep_the_document_a_draft() -> None:
    doc = full_chain(consultation={"advice_followed": False})[-1]
    assert doc["final"] is False and doc["open_items"] == ["consultation:departure_from_dpo_advice_undocumented"]


def test_records_from_another_chain_are_refused() -> None:
    s, c, d, n, r, m, k, g, _ = full_chain()
    other_m = mitigate(r, measures=[], residual=residual_as_assessed(r))
    assert other_m["mitigations_ref"] != m["mitigations_ref"]
    with pytest.raises(InvalidDpiaDocumentError, match="different predecessor"):
        compose_dpia_document(s, c, d, n, r, m, consult(other_m), g, "wf:dpia", "exec:1", "2026-10-26T10:20:00Z")


# --------------------------------------------------------------------------- schedule_review_cadence


def test_a_change_of_risk_always_triggers_a_review_within_the_interval() -> None:
    v = schedule(full_chain()[-1])
    assert v["change_triggers"] == ["change_of_risk", "purpose"]
    assert (v["review_cadence"], v["next_review_due"], v["document_final"]) == ("P1Y", "2027-10-26T10:30:00Z", True)


def test_the_next_review_clamps_to_the_end_of_a_shorter_month() -> None:
    assert schedule(full_chain()[-1], at="2028-02-29T00:00:00Z")["next_review_due"] == "2029-02-28T00:00:00Z"
    assert schedule(full_chain()[-1], interval="P1M2W")["next_review_due"] == "2026-12-10T10:30:00Z"


def test_a_draft_document_is_scheduled_and_says_so() -> None:
    assert schedule(full_chain(consultation={"advice_followed": False})[-1])["document_final"] is False


@pytest.mark.parametrize(("interval", "triggers"), [("1Y", ()), ("PT12H", ()), ("P1Y", ("weather",))])
def test_a_malformed_schedule_is_refused(interval, triggers) -> None:
    with pytest.raises(InvalidReviewScheduleError):
        schedule(full_chain()[-1], interval=interval, triggers=triggers)


def test_the_change_triggers_include_the_article_35_11_minimum() -> None:
    assert CHANGE_TRIGGERS[0] == "change_of_risk"
