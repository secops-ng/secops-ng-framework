from __future__ import annotations

import json
from pathlib import Path

import pytest

from compilers._shared.cacao_parser import secops_extension
from content.playbooks.eu_ai_act_deployer_obligations.primitives import (
    LIMBS,
    InvalidFundamentalRightsAssessmentError,
    InvalidIntendedUseError,
    InvalidMonitoringWindowError,
    InvalidOversightAssignmentError,
    InvalidRetentionEvidenceError,
    assess_fundamental_rights_impact,
    classify_monitoring_window,
    compose_oversight_assignment,
    compose_retention_evidence,
    determine_intended_use,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
PLAYBOOK = REPO_ROOT / "content" / "playbooks" / "eu_ai_act_deployer_obligations" / "playbook.cacao.json"
SYSTEM = "provider:acme-score:v3"
NOW = "2026-10-01T09:00:00Z"
INSTRUCTIONS = {"system_reference": SYSTEM, "intended_purpose": "creditworthiness assessment of natural persons",
                "permitted_contexts": ["consumer_credit", "sme_credit"]}


def deployment(**kw) -> dict:
    d = {"deployment_id": "deploy:credit-01", "system_reference": SYSTEM, "declared_contexts": ["consumer_credit"],
         "workplace": False, "deployer_is_employer": True}
    return d | kw


def notice(at="2026-09-20T10:00:00Z", reps=True, workers=True) -> dict:
    return {"notified_at": at, "workers_representatives_informed": reps, "affected_workers_informed": workers}


def proceeding() -> dict:
    return determine_intended_use(deployment(), INSTRUCTIONS, None, NOW)


def person(ref="person:a", natural=True, **missing) -> dict:
    p = {"person_ref": ref, "natural_person": natural, "competence_ref": "cert:a", "training_ref": "train:a",
         "authority_ref": "delegation:a", "support_ref": "support:a"}
    return p | {f"{limb}_ref": None for limb in missing}


def oversight(iu=None) -> dict:
    return compose_oversight_assignment(iu or proceeding(), [person()], NOW)


WINDOW = {"window_start": "2026-10-01T00:00:00Z", "window_end": "2026-10-07T23:59:59Z"}
NO_CONTROL = {"deployer_controls_input_data": False, "relevant": None, "sufficiently_representative": None}
EVALUATED = "2026-10-08T00:00:00Z"


def window(findings, input_data=NO_CONTROL, iu=None, evaluated=EVALUATED) -> dict:
    iu = iu or proceeding()
    return classify_monitoring_window(iu, oversight(iu), WINDOW, input_data, findings, evaluated)


def incident(ref="si:1", outcomes=("serious_harm_to_health",), widespread=False, reachable=True,
             aware="2026-10-03T08:00:00Z") -> dict:
    return {"finding_ref": ref, "kind": "serious_incident", "determined_at": "2026-10-03T09:00:00Z",
            "aware_at": aware, "outcomes": list(outcomes), "widespread_infringement": widespread,
            "provider_reachable": reachable}


PUBLIC = {"public_law_body": True, "private_public_service_provider": False}
PRIVATE = {"public_law_body": False, "private_public_service_provider": False}
FULL = {letter: f"element {letter}" for letter in "abcdef"}


def fria(system=None, deployer=PUBLIC, assessment=None, dpia=None, exempt=False, template=None, iu=None) -> dict:
    return assess_fundamental_rights_impact(iu or proceeding(), system or {"high_risk_basis": "art_6_2",
                                            "annex_iii_point": "4"}, deployer,
                                            FULL if assessment is None else assessment, dpia, exempt, template, NOW)


CONTROLLED = {"logs_under_deployer_control": True, "retention_months": 6, "legal_basis_ref": None}


def evidence(log_retention=CONTROLLED, captured=NOW, **records) -> dict:
    iu = records.get("iu") or proceeding()
    ov = records.get("ov") or oversight(iu)
    ob = records.get("ob") or classify_monitoring_window(iu, ov, WINDOW, NO_CONTROL, [], EVALUATED)
    fr = records.get("fr") or fria(iu=iu)
    return compose_retention_evidence(iu, ov, ob, fr, log_retention, "wf:euai", "exec:1", captured)


# --------------------------------------------------------------------------- Art. 26(1) and 26(7)


def test_a_deployment_inside_the_intended_purpose_proceeds() -> None:
    iu = proceeding()
    assert iu["proceed"] is True and iu["conforms_to_intended_purpose"] is True
    assert iu["exceeded_contexts"] == [] and iu["blocking_reasons"] == []
    assert iu["workforce_notice_required"] is False and iu["workforce_notice_ok"] is None


def test_a_context_outside_the_instructions_blocks_the_deployment() -> None:
    iu = determine_intended_use(deployment(declared_contexts=["consumer_credit", "employment_screening"]),
                                INSTRUCTIONS, None, NOW)
    assert iu["proceed"] is False and iu["exceeded_contexts"] == ["employment_screening"]
    assert iu["blocking_reasons"] == ["outside_intended_purpose"]


@pytest.mark.parametrize(("given", "proceed", "reasons"), [
    (None, False, ["art_26_7_notice_missing"]),
    ("", False, ["art_26_7_notice_missing"]),
    (notice(), True, []),
    (notice(at="2026-10-02T09:00:00Z"), False, ["art_26_7_notice_after_determination"]),
    (notice(workers=False), False, ["art_26_7_notice_incomplete"]),
])
def test_the_art_26_7_workplace_notice_is_a_precondition(given, proceed, reasons) -> None:
    iu = determine_intended_use(deployment(workplace=True), INSTRUCTIONS, given, NOW)
    assert iu["workforce_notice_required"] is True
    assert iu["proceed"] is proceed and iu["blocking_reasons"] == reasons


def test_a_workplace_deployment_by_a_non_employer_needs_no_notice() -> None:
    iu = determine_intended_use(deployment(workplace=True, deployer_is_employer=False), INSTRUCTIONS, None, NOW)
    assert iu["workforce_notice_required"] is False and iu["proceed"] is True


@pytest.mark.parametrize("bad", [
    {"deployment": deployment(workplace="false")},
    {"deployment": deployment(declared_contexts=[])},
    {"instructions": INSTRUCTIONS | {"system_reference": "provider:other:v1"}},
    {"instructions": INSTRUCTIONS | {"intended_purpose": " "}},
    {"notice": notice(reps="yes")},
])
def test_intended_use_rejects_malformed_or_inconsistent_inputs(bad) -> None:
    with pytest.raises(InvalidIntendedUseError):
        determine_intended_use(bad.get("deployment", deployment()), bad.get("instructions", INSTRUCTIONS),
                               bad.get("notice"), NOW)


# --------------------------------------------------------------------------- Art. 26(2)


def test_a_complete_assignment_covers_all_four_limbs_for_every_assignee() -> None:
    a = compose_oversight_assignment(proceeding(), [person("person:b"), person("person:a")], NOW)
    assert a["complete"] is True and a["uncovered_assignees"] == []
    assert [x["person_ref"] for x in a["assignees"]] == ["person:a", "person:b"]
    assert a["metric_stamps"] == ["kpi.eu_ai_act_deployer_oversight_coverage@v1"]


def test_an_assignee_without_authority_cannot_lawfully_oversee() -> None:
    a = compose_oversight_assignment(proceeding(), [person("person:a"), person("person:b", authority=True)], NOW)
    assert a["complete"] is False and a["uncovered_assignees"] == ["person:b"]
    assert a["assignees"][1]["missing_limbs"] == ["authority"]


def test_oversight_is_assigned_to_natural_persons_only() -> None:
    a = compose_oversight_assignment(proceeding(), [person("role:ops-desk", natural=False)], NOW)
    assert a["complete"] is False and a["uncovered_assignees"] == ["role:ops-desk"]


def test_an_empty_evidence_reference_is_a_missing_limb() -> None:
    p = person() | {"training_ref": ""}
    a = compose_oversight_assignment(proceeding(), [p], NOW)
    assert a["assignees"][0]["missing_limbs"] == ["training"] and a["complete"] is False


def test_every_downstream_step_refuses_a_deployment_that_may_not_proceed() -> None:
    blocked = determine_intended_use(deployment(declared_contexts=["employment_screening"]), INSTRUCTIONS, None, NOW)
    ov = oversight()
    with pytest.raises(InvalidOversightAssignmentError, match="may proceed"):
        compose_oversight_assignment(blocked, [person()], NOW)
    with pytest.raises(InvalidMonitoringWindowError, match="may proceed"):
        classify_monitoring_window(blocked, ov, WINDOW, NO_CONTROL, [], EVALUATED)
    with pytest.raises(InvalidFundamentalRightsAssessmentError, match="may proceed"):
        fria(iu=blocked)
    with pytest.raises(InvalidRetentionEvidenceError, match="may proceed"):
        compose_retention_evidence(blocked, ov, {}, {}, CONTROLLED, "wf:euai", "exec:1", NOW)


@pytest.mark.parametrize("assignees", [[], [person(), person()], [person() | {"natural_person": "true"}]])
def test_oversight_rejects_malformed_assignees(assignees) -> None:
    with pytest.raises(InvalidOversightAssignmentError):
        compose_oversight_assignment(proceeding(), assignees, NOW)


# --------------------------------------------------------------------------- Art. 26(4) and 26(5)


def test_a_quiet_window_is_routine_and_obliges_nothing() -> None:
    w = window([])
    assert w["escalation_trigger_class"] == "routine" and w["actions"] == [] and w["metric_stamps"] == []


def test_routine_findings_feed_the_providers_post_market_monitoring() -> None:
    w = window([{"finding_ref": "obs:1", "kind": "routine", "determined_at": "2026-10-02T10:00:00Z"}])
    assert w["escalation_trigger_class"] == "routine"
    assert w["actions"] == [{"action": "inform_provider_post_market_monitoring", "basis": "Art. 26(5), Art. 72",
                             "finding_refs": ["obs:1"]}]


def test_an_art_79_risk_obliges_inform_and_suspend_and_measures_the_latency() -> None:
    w = window([{"finding_ref": "risk:1", "kind": "art_79_risk", "determined_at": "2026-10-02T10:00:00Z",
                 "suspended_at": "2026-10-03T16:30:00Z"}])
    assert w["escalation_trigger_class"] == "art_79_risk"
    assert [a["action"] for a in w["actions"]] == ["inform_provider_or_distributor",
                                                    "inform_market_surveillance_authority", "suspend_use"]
    assert all(a["timing"] == "without_undue_delay" for a in w["actions"])
    assert w["findings"][0]["suspension_latency_hours"] == 30
    assert w["suspensions_outstanding"] == []
    assert w["metric_stamps"] == ["kri.eu_ai_act_deployer_suspension_latency_hours@v1"]


def test_an_unrecorded_suspension_is_outstanding_not_assumed() -> None:
    w = window([{"finding_ref": "risk:1", "kind": "art_79_risk", "determined_at": "2026-10-02T10:00:00Z",
                 "suspended_at": ""}])
    assert w["findings"][0]["suspended_at"] is None and w["findings"][0]["suspension_latency_hours"] is None
    assert w["suspensions_outstanding"] == ["risk:1"]


@pytest.mark.parametrize(("outcomes", "widespread", "days", "basis"), [
    (("serious_harm_to_health",), False, 15, "Art. 73(2)"),
    (("fundamental_rights_infringement",), False, 15, "Art. 73(2)"),
    (("death",), False, 10, "Art. 73(4)"),
    (("critical_infrastructure_disruption",), False, 2, "Art. 73(3)"),
    (("serious_harm_to_property_or_environment",), True, 2, "Art. 73(3)"),
    (("death", "critical_infrastructure_disruption"), False, 2, "Art. 73(3)"),   # the shortest governs
])
def test_the_art_73_clock_is_severity_classed(outcomes, widespread, days, basis) -> None:
    clock = window([incident(outcomes=outcomes, widespread=widespread)])["findings"][0]["art_73_clock"]
    assert clock["bound_days"] == days and clock["basis"] == basis


def test_a_serious_incident_is_notified_immediately_provider_first() -> None:
    w = window([incident(outcomes=("death",))])
    assert w["escalation_trigger_class"] == "serious_incident"
    assert [(a["order"], a["action"]) for a in w["actions"]] == [
        (1, "inform_provider"), (2, "inform_importer_or_distributor"), (3, "inform_market_surveillance_authorities")]
    assert all(a["timing"] == "immediately" for a in w["actions"])
    clock = w["findings"][0]["art_73_clock"]
    assert clock["report_due_at"] == "2026-10-13T08:00:00Z" and clock["margin_hours"] == 128
    assert clock["reported_by"] == "provider"
    assert w["metric_stamps"] == ["kri.eu_ai_act_report_clock_margin_days@v1"]


def test_an_unreachable_provider_puts_the_art_73_report_on_the_deployer() -> None:
    w = window([incident(reachable=False)])
    assert w["actions"][-1]["action"] == "report_to_market_surveillance_authority_under_art_73"
    assert w["findings"][0]["art_73_clock"]["reported_by"] == "deployer"


def test_mixed_findings_escalate_to_the_most_severe_class_without_collapsing_duties() -> None:
    w = window([
        {"finding_ref": "obs:1", "kind": "routine", "determined_at": "2026-10-01T10:00:00Z"},
        {"finding_ref": "risk:1", "kind": "art_79_risk", "determined_at": "2026-10-02T10:00:00Z",
         "suspended_at": None},
        incident(),
    ])
    assert w["escalation_trigger_class"] == "serious_incident"
    kinds = {a["action"] for a in w["actions"]}
    assert {"inform_provider_post_market_monitoring", "suspend_use", "inform_provider"} <= kinds
    assert w["metric_stamps"] == ["kri.eu_ai_act_deployer_suspension_latency_hours@v1",
                                  "kri.eu_ai_act_report_clock_margin_days@v1"]


@pytest.mark.parametrize(("data", "ok", "basis"), [
    ({"deployer_controls_input_data": True, "relevant": True, "sufficiently_representative": True},
     True, "assessed_by_deployer"),
    ({"deployer_controls_input_data": True, "relevant": True, "sufficiently_representative": False},
     False, "assessed_by_deployer"),
    (NO_CONTROL, None, "not_under_deployer_control"),
])
def test_the_art_26_4_input_data_determination(data, ok, basis) -> None:
    d = window([], input_data=data)["input_data"]
    assert d["art_26_4_ok"] is ok and d["basis"] == basis


@pytest.mark.parametrize("bad", [
    {"input_data": {"deployer_controls_input_data": False, "relevant": True, "sufficiently_representative": None}},
    {"findings": [{"finding_ref": "obs:1", "kind": "routine", "determined_at": "2026-09-30T10:00:00Z"}]},
    {"findings": [incident(outcomes=("reputational_damage",))]},
    {"findings": [{"finding_ref": "obs:1", "kind": "rumour", "determined_at": "2026-10-02T10:00:00Z"}]},
    {"findings": [{"finding_ref": "risk:1", "kind": "art_79_risk", "determined_at": "2026-10-02T10:00:00Z",
                   "suspended_at": "2026-10-01T10:00:00Z"}]},
    {"evaluated": "2026-10-05T00:00:00Z"},
])
def test_monitoring_rejects_malformed_or_inconsistent_windows(bad) -> None:
    with pytest.raises(InvalidMonitoringWindowError):
        window(bad.get("findings", []), input_data=bad.get("input_data", NO_CONTROL),
               evaluated=bad.get("evaluated", EVALUATED))


def test_monitoring_refuses_an_oversight_record_from_another_deployment() -> None:
    other = determine_intended_use(deployment(deployment_id="deploy:other"), INSTRUCTIONS, None, NOW)
    with pytest.raises(InvalidMonitoringWindowError, match="different deployment"):
        classify_monitoring_window(proceeding(), oversight(other), WINDOW, NO_CONTROL, [], EVALUATED)


# --------------------------------------------------------------------------- Art. 27


@pytest.mark.parametrize(("system", "deployer", "in_scope", "basis"), [
    ({"high_risk_basis": "art_6_1", "annex_iii_point": None}, PUBLIC, False, "not_an_art_6_2_system"),
    ({"high_risk_basis": "art_6_2", "annex_iii_point": "2"}, PUBLIC, False, "annex_iii_point_2_excluded"),
    ({"high_risk_basis": "art_6_2", "annex_iii_point": "5(b)"}, PRIVATE, True, "annex_iii_point_5b"),
    ({"high_risk_basis": "art_6_2", "annex_iii_point": "5(c)"}, PRIVATE, True, "annex_iii_point_5c"),
    ({"high_risk_basis": "art_6_2", "annex_iii_point": "4"}, PUBLIC, True, "body_governed_by_public_law"),
    ({"high_risk_basis": "art_6_2", "annex_iii_point": "4"},
     {"public_law_body": False, "private_public_service_provider": True}, True,
     "private_entity_providing_public_services"),
    ({"high_risk_basis": "art_6_2", "annex_iii_point": "4"}, PRIVATE, False, "deployer_not_in_scope"),
])
def test_the_art_27_1_scope_determination(system, deployer, in_scope, basis) -> None:
    r = fria(system=system, deployer=deployer, assessment=FULL if in_scope else {})
    assert r["in_scope"] is in_scope and r["scope_basis"] == basis
    if not in_scope:
        assert r["complete"] is None and r["blocks_deployment"] is False
        assert r["notification"]["status"] == "not_applicable"


def test_a_complete_in_scope_assessment_owes_the_notification() -> None:
    r = fria()
    assert r["complete"] is True and r["missing_elements"] == [] and r["blocks_deployment"] is False
    assert r["notification"] == {"required": True, "exempt_art_46_1": False, "template_ref": None,
                                 "status": "due_template_unavailable"}
    assert fria(template="ai-office:fria-template:v1")["notification"]["status"] == "due"


def test_a_dpia_satisfies_elements_the_assessment_then_complements() -> None:
    r = fria(assessment={"a": "processes", "b": "period", "d": "risks", "f": "measures"},
             dpia={"dpia_ref": "dpia:credit-2026", "covered_elements": ["c", "e"]})
    assert {k: v["source"] for k, v in r["elements"].items()} == {
        "a": "fria", "b": "fria", "c": "dpia", "d": "fria", "e": "dpia", "f": "fria"}
    assert r["complete"] is True and r["dpia_ref"] == "dpia:credit-2026"


def test_a_missing_element_leaves_the_assessment_incomplete_and_blocks_the_notification() -> None:
    r = fria(assessment={k: v for k, v in FULL.items() if k != "d"})
    assert r["complete"] is False and r["missing_elements"] == ["d"]
    assert r["notification"]["status"] == "blocked_assessment_incomplete"
    assert r["blocks_deployment"] is True                       # Art. 27(1): prior to deploying


def test_the_art_46_1_derogation_exempts_the_notification() -> None:
    n = fria(exempt=True)["notification"]
    assert n["required"] is False and n["status"] == "exempt_art_46_1"


@pytest.mark.parametrize("bad", [
    {"system": {"high_risk_basis": "art_6_2", "annex_iii_point": "2"}, "assessment": FULL},
    {"assessment": {"g": "not an element"}},
    {"assessment": {"a": ""}},
    {"system": {"high_risk_basis": "art_6_1", "annex_iii_point": "4"}},
    {"dpia": {"dpia_ref": "dpia:x", "covered_elements": ["z"]}},
])
def test_fria_rejects_malformed_or_inconsistent_inputs(bad) -> None:
    with pytest.raises(InvalidFundamentalRightsAssessmentError):
        fria(system=bad.get("system"), assessment=bad.get("assessment"), dpia=bad.get("dpia"))


# --------------------------------------------------------------------------- Art. 26(6) and the cycle evidence


def test_six_months_is_the_floor_and_the_retention_end_is_dated() -> None:
    e = evidence(captured="2026-08-31T12:00:00Z")
    r = e["log_retention"]
    assert r["retention_months"] == 6 and r["basis"] == "art_26_6_floor_or_longer"
    assert r["retain_until"] == "2027-02-28T12:00:00Z"                     # end-of-month clamp


def test_a_shorter_period_needs_the_law_that_provides_otherwise() -> None:
    short = {"logs_under_deployer_control": True, "retention_months": 4, "legal_basis_ref": None}
    with pytest.raises(InvalidRetentionEvidenceError, match="floor"):
        evidence(short)
    r = evidence(short | {"legal_basis_ref": "law:national-dp-act:s12"})["log_retention"]
    assert r["basis"] == "applicable_law_provides_otherwise" and r["legal_basis_ref"] == "law:national-dp-act:s12"


def test_logs_outside_the_deployers_control_carry_no_period() -> None:
    off = {"logs_under_deployer_control": False, "retention_months": None, "legal_basis_ref": None}
    r = evidence(off)["log_retention"]
    assert r["basis"] == "not_under_deployer_control" and r["retain_until"] is None
    with pytest.raises(InvalidRetentionEvidenceError):
        evidence(off | {"retention_months": 6})


def test_the_cycle_evidence_joins_one_deployments_records_deterministically() -> None:
    e = evidence()
    assert e == evidence()
    assert e["escalation_trigger_class"] == "routine" and e["fria_in_scope"] is True and e["oversight_complete"] is True
    other = determine_intended_use(deployment(deployment_id="deploy:other"), INSTRUCTIONS, None, NOW)
    with pytest.raises(InvalidRetentionEvidenceError, match="different deployment"):
        evidence(fr=fria(iu=other))


# --------------------------------------------------------------------------- cross-cutting


def test_outputs_are_json_native() -> None:
    iu = proceeding()
    ov = oversight(iu)
    ob = classify_monitoring_window(iu, ov, WINDOW, NO_CONTROL, [incident()], EVALUATED)
    for out in (iu, ov, ob, fria(iu=iu), evidence()):
        assert json.loads(json.dumps(out)) == out


def test_metric_stamps_are_declared_on_the_playbook_and_on_the_step() -> None:
    doc = json.loads(PLAYBOOK.read_text(encoding="utf-8"))
    declared = set(secops_extension(doc)["metric_refs"])
    steps = {s["name"]: set((secops_extension(s) or {}).get("metric_refs") or []) for s in doc["workflow"].values()}
    iu = proceeding()
    ov = oversight(iu)
    ob = classify_monitoring_window(iu, ov, WINDOW, NO_CONTROL, [incident(), {
        "finding_ref": "risk:1", "kind": "art_79_risk", "determined_at": "2026-10-02T10:00:00Z",
        "suspended_at": None}], EVALUATED)
    for step, out in (("assign_human_oversight", ov), ("monitor_operation", ob),
                      ("assess_fundamental_rights_impact", fria(iu=iu)), ("retain_logs_and_evidence", evidence())):
        assert set(out["metric_stamps"]) <= declared and set(out["metric_stamps"]) <= steps[step], step


def test_the_limbs_are_the_four_art_26_2_names() -> None:
    assert LIMBS == ("competence", "training", "authority", "support")
