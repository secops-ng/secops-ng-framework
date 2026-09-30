"""Unit coverage for content/playbooks/dora_major_incident_reporting/primitives (CORE-PRIM)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from content.playbooks.dora_major_incident_reporting.primitives import (
    MATERIALITY_CRITERIA,
    InvalidArchiveError,
    InvalidClassificationError,
    InvalidReportingError,
    classify_major_incident,
    compose_cycle_archive,
    compose_final_report,
    compose_initial_notification,
    compose_intermediate_report,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
INCIDENT = "3f2b8c1e-5d4a-4b6e-9c7f-1a2b3c4d5e6f"
AWARE, CLASSIFIED = "2026-09-30T06:00:00Z", "2026-09-30T08:00:00Z"
IMPACT = {"affected_functions": ["payments-clearing"], "affected_clients_count": 12000,
          "geographic_scope": ["DE", "NL"], "data_loss_indicator": "availability"}
IN_FLIGHT = {"state": "in_flight", "actions_in_flight": ["failover to secondary site"]}
FINAL_MIT = {"state": "remediated", "completed_actions": ["failover", "patch"],
             "root_cause": "expired certificate on the clearing gateway", "residual_risk": "low"}
SRC = "https://example.org/incident-register/entry"


def materiality(*met) -> dict:
    return {k: k in met for k in MATERIALITY_CRITERIA}


def criteria(critical=True, malicious=False, met=()) -> dict:
    return {"critical_services_affected": critical, "malicious_unauthorised_access": malicious,
            "materiality": materiality(*met)}


def major() -> dict:
    return classify_major_incident(INCIDENT, criteria(met=("clients_counterparts_transactions", "economic_impact")),
                                   CLASSIFIED)


def report_validator() -> Draft202012Validator:
    load = lambda p: json.loads((REPO_ROOT / p).read_text(encoding="utf-8"))
    schema = load("schemas/evidence/dora-art19-technical-incident-report.schema.json")
    milestone = load("schemas/dora_art19_report_milestone.json")
    registry = Registry().with_resource("https://secops-ng.org/schemas/dora_art19_report_milestone.json",
                                        Resource.from_contents(milestone))
    return Draft202012Validator(schema, registry=registry)


def initial(c=None, submitted="2026-09-30T10:00:00Z", **kw) -> dict:
    return compose_initial_notification(c or major(), "window:2026-q3", AWARE, submitted, IMPACT, IN_FLIGHT, SRC, **kw)


def intermediate(c=None, prev=None, submitted="2026-10-02T08:00:00Z") -> dict:
    c = c or major()
    return compose_intermediate_report(c, prev or initial(c), "window:2026-q3", AWARE, submitted, IMPACT,
                                       IN_FLIGHT, SRC)


def final(c=None, prev=None, submitted="2026-10-20T08:00:00Z") -> dict:
    c = c or major()
    return compose_final_report(c, prev or intermediate(c), "window:2026-q3", AWARE, submitted, IMPACT, FINAL_MIT, SRC)


# --------------------------------------------------------------------------- classification


@pytest.mark.parametrize(("crit", "expected", "basis"), [
    (criteria(critical=False, malicious=True, met=MATERIALITY_CRITERIA), False, "critical_services_not_affected"),
    (criteria(malicious=True), True, "malicious_unauthorised_access"),
    (criteria(met=("reputational_impact", "geographical_spread")), True, "two_or_more_materiality_thresholds"),
    (criteria(met=("data_losses",)), False, "fewer_than_two_materiality_thresholds"),
    (criteria(), False, "fewer_than_two_materiality_thresholds"),
])
def test_the_art_8_combination_rule(crit, expected, basis) -> None:
    c = classify_major_incident(INCIDENT, crit, CLASSIFIED)
    assert (c["major"], c["basis"]) == (expected, basis)


def test_critical_services_are_mandatory_on_both_limbs() -> None:
    every = criteria(critical=False, malicious=True, met=MATERIALITY_CRITERIA)
    c = classify_major_incident(INCIDENT, every, CLASSIFIED)
    assert c["major"] is False and "on both limbs" in c["reasons"][0]


def test_rule_ids_and_reasons_record_what_fired() -> None:
    c = classify_major_incident(INCIDENT, criteria(malicious=True, met=("data_losses",)), CLASSIFIED)
    assert c["rule_ids"] == ["dora.critical_services_affected", "dora.malicious_unauthorised_access",
                             "dora.materiality.data_losses"]
    assert classify_major_incident(INCIDENT, criteria(critical=False), CLASSIFIED)["rule_ids"] == ["dora.no_rule_met"]


def agg(**kw) -> dict:
    base = {"incident_refs": ["inc:1", "inc:2"], "same_apparent_root_cause": True,
            "first_occurred_at": "2026-04-01T00:00:00Z", "last_occurred_at": "2026-09-01T00:00:00Z"}
    base.update(kw)
    return base


def test_recurring_incidents_aggregate_only_under_the_rule() -> None:
    c = classify_major_incident(INCIDENT, criteria(met=("clients_counterparts_transactions", "economic_impact")),
                                CLASSIFIED, agg())
    assert c["major"] is True and c["recurring_incident"] is True and c["aggregated_incident_refs"] == ["inc:1", "inc:2"]
    edge = agg(first_occurred_at="2026-03-31T00:00:00Z", last_occurred_at="2026-09-30T00:00:00Z")   # clamp: 6 months
    assert classify_major_incident(INCIDENT, criteria(), CLASSIFIED, edge)["recurring_incident"] is True
    assert classify_major_incident(INCIDENT, criteria(), CLASSIFIED, "")["recurring_incident"] is False
    for bad in (agg(incident_refs=["inc:1"]), agg(same_apparent_root_cause=False),
                agg(last_occurred_at="2026-10-02T00:00:00Z"), agg(last_occurred_at="2026-03-01T00:00:00Z")):
        with pytest.raises(InvalidClassificationError):
            classify_major_incident(INCIDENT, criteria(), CLASSIFIED, bad)


@pytest.mark.parametrize(("incident", "crit"), [
    ("INC-42", criteria()),
    (INCIDENT, {**criteria(), "critical_services_affected": "true"}),
    (INCIDENT, {**criteria(), "materiality": {"data_losses": True}}),
    (INCIDENT, {"critical_services_affected": True, "materiality": materiality()}),
])
def test_classification_rejects_malformed_inputs(incident, crit) -> None:
    with pytest.raises(InvalidClassificationError):
        classify_major_incident(incident, crit, CLASSIFIED)


# --------------------------------------------------------------------------- notifications


def test_every_milestone_is_a_schema_conforming_art_19_report() -> None:
    v = report_validator()
    c = major()
    i = initial(c); m = intermediate(c, i); f = final(c, m)
    for out in (i, m, f):
        errors = [e.message for e in v.iter_errors(out["report"])]
        assert not errors, errors
    assert [x["report"]["report_variant"] for x in (i, m, f)] == ["initial_4h", "intermediate_72h", "final_1mo"]


def test_milestones_chain_to_their_predecessor() -> None:
    c = major()
    i = initial(c); m = intermediate(c, i); f = final(c, m)
    assert "previous_milestone_event_id" not in i["report"]["timeline_refs"]
    assert m["report"]["timeline_refs"]["previous_milestone_event_id"] == i["report"]["timeline_refs"]["stage_event_id"]
    assert f["report"]["timeline_refs"]["previous_milestone_event_id"] == m["report"]["timeline_refs"]["stage_event_id"]


def test_initial_deadline_is_the_earlier_of_4h_after_classification_and_24h_after_awareness() -> None:
    assert initial()["due_at"] == "2026-09-30T12:00:00Z"                                  # 4h after classification binds
    late_class = classify_major_incident(INCIDENT, criteria(malicious=True), "2026-10-01T04:00:00Z")
    assert initial(late_class, submitted="2026-10-01T05:00:00Z")["due_at"] == "2026-10-01T06:00:00Z"   # 24h after awareness binds
    assert initial(submitted="2026-09-30T12:00:00Z")["within_deadline"] is True
    assert initial(submitted="2026-09-30T12:00:01Z")["within_deadline"] is False


def test_intermediate_and_final_deadlines() -> None:
    c = major()
    assert intermediate(c)["due_at"] == "2026-10-03T08:00:00Z"
    jan = compose_intermediate_report(
        classify_major_incident(INCIDENT, criteria(malicious=True), "2027-01-29T08:00:00Z"),
        compose_initial_notification(classify_major_incident(INCIDENT, criteria(malicious=True), "2027-01-29T08:00:00Z"),
                                     "window:x", "2027-01-29T07:00:00Z", "2027-01-29T09:00:00Z", IMPACT, IN_FLIGHT, SRC),
        "window:x", "2027-01-29T07:00:00Z", "2027-01-31T10:00:00Z", IMPACT, IN_FLIGHT, SRC)
    f = compose_final_report(classify_major_incident(INCIDENT, criteria(malicious=True), "2027-01-29T08:00:00Z"), jan,
                             "window:x", "2027-01-29T07:00:00Z", "2027-02-20T10:00:00Z", IMPACT, FINAL_MIT, SRC)
    assert f["due_at"] == "2027-02-28T10:00:00Z"                                          # end-of-month clamp


def test_a_non_major_incident_is_never_reported() -> None:
    for gate in (False, "true"):
        c = major(); c["major"] = gate
        with pytest.raises(InvalidReportingError, match="only an incident classified as major"):
            initial(c)


def test_the_chain_cannot_be_broken_or_reordered() -> None:
    c = major()
    i = initial(c)
    with pytest.raises(InvalidReportingError, match="previous milestone must be the initial_4h"):
        compose_intermediate_report(c, intermediate(c, i), "window:2026-q3", AWARE, "2026-10-02T09:00:00Z",
                                    IMPACT, IN_FLIGHT, SRC)
    with pytest.raises(InvalidReportingError, match="before the one it follows"):
        intermediate(c, i, submitted="2026-09-30T09:00:00Z")
    other = classify_major_incident("9a8b7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d", criteria(malicious=True), CLASSIFIED)
    with pytest.raises(InvalidReportingError, match="different incident"):
        compose_intermediate_report(other, i, "window:2026-q3", AWARE, "2026-10-02T08:00:00Z", IMPACT, IN_FLIGHT, SRC)


def test_inconsistent_timing_fails_loud() -> None:
    with pytest.raises(InvalidReportingError, match="classified before the operator became aware"):
        compose_initial_notification(major(), "window:x", "2026-09-30T09:00:00Z", "2026-09-30T10:00:00Z",
                                     IMPACT, IN_FLIGHT, SRC)
    with pytest.raises(InvalidReportingError, match="before the incident was classified"):
        initial(submitted="2026-09-30T07:59:59Z")


def test_an_empty_submission_ref_is_omitted() -> None:
    assert "submission_ref" not in initial(submission_ref="")["report"]
    assert initial(submission_ref="receipt:abc")["report"]["submission_ref"] == "receipt:abc"


# --------------------------------------------------------------------------- archive


def test_a_major_cycle_archives_its_complete_chain() -> None:
    c = major()
    i = initial(c); m = intermediate(c, i); f = final(c, m)
    a = compose_cycle_archive(c, [i, m, f], ["nis2:early-warning:77", "gdpr:art33:12"], "wf:dora", "exec:1",
                              "2026-10-20T09:00:00Z")
    assert [s["report_variant"] for s in a["milestones"]] == ["initial_4h", "intermediate_72h", "final_1mo"]
    assert a["all_deadlines_met"] is True and a["cross_regime_refs"] == ["gdpr:art33:12", "nis2:early-warning:77"]
    assert a == compose_cycle_archive(c, [i, m, f], ["gdpr:art33:12", "nis2:early-warning:77"], "wf:dora",
                                      "exec:1", "2026-10-20T09:00:00Z")


def test_the_archive_refuses_states_that_should_not_exist() -> None:
    c = major()
    i = initial(c); m = intermediate(c, i)
    with pytest.raises(InvalidArchiveError, match="closes with"):
        compose_cycle_archive(c, [i, m], [], "wf:dora", "exec:1", "2026-10-20T09:00:00Z")
    not_major = classify_major_incident(INCIDENT, criteria(critical=False), CLASSIFIED)
    with pytest.raises(InvalidArchiveError, match="not reported"):
        compose_cycle_archive(not_major, [i], [], "wf:dora", "exec:1", "2026-10-20T09:00:00Z")
    closed = compose_cycle_archive(not_major, [], [], "wf:dora", "exec:1", "2026-10-20T09:00:00Z")
    assert closed["major"] is False and closed["milestones"] == [] and closed["all_deadlines_met"] is True


def test_a_late_milestone_is_on_the_record() -> None:
    c = major()
    i = initial(c, submitted="2026-09-30T13:00:00Z")          # past the 4h deadline
    m = intermediate(c, i); f = final(c, m)
    a = compose_cycle_archive(c, [i, m, f], [], "wf:dora", "exec:1", "2026-10-20T09:00:00Z")
    assert a["all_deadlines_met"] is False and a["milestones"][0]["within_deadline"] is False


# --------------------------------------------------------------------------- cross-cutting


def test_outputs_are_json_native() -> None:
    c = major()
    i = initial(c); m = intermediate(c, i); f = final(c, m)
    for out in (c, i, m, f, compose_cycle_archive(c, [i, m, f], [], "wf:dora", "exec:1", "2026-10-20T09:00:00Z")):
        assert json.loads(json.dumps(out)) == out
