from __future__ import annotations

import json
from pathlib import Path

import pytest

from compilers._shared.cacao_parser import secops_extension
from content.playbooks.ai_human_oversight.primitives import (
    CAPABILITIES,
    POWERS,
    InvalidBriefingRecordError,
    InvalidInterventionRecordError,
    InvalidOversightEvidenceError,
    InvalidOversightRosterError,
    InvalidReviewError,
    compose_briefing_record,
    compose_oversight_evidence,
    record_interventions,
    resolve_oversight_roster,
    review_flagged_decisions,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
PLAYBOOK = REPO_ROOT / "content" / "playbooks" / "ai_human_oversight" / "playbook.cacao.json"
DEPLOYMENT = "deploy:credit-01"
CYCLE = "2026-10-05T00:00:00Z/2026-10-11T23:59:59Z"
INSTR = "provider:acme-score:ifu:v3"
NOW = "2026-10-12T08:00:00Z"
NO_BIO = {"annex_iii_point_1a": False, "exemption_legal_basis_ref": None, "verifications": []}


def entry(ref, natural=True, on_watch=True, reachable=True, powers=POWERS, authority="delegation:ops") -> dict:
    return {"person_ref": ref, "natural_person": natural, "on_watch": on_watch, "reachable": reachable,
            "powers": list(powers), "authority_ref": authority}


def roster(*entries) -> dict:
    return resolve_oversight_roster(DEPLOYMENT, CYCLE, list(entries) or [entry("person:a"), entry("person:b")],
                                    "2026-10-05T00:00:00Z")


def brief(ref, deployment=DEPLOYMENT, instr=INSTR, at="2026-09-30T10:00:00Z", **limbs) -> dict:
    return {"person_ref": ref, "deployment_id": deployment, "instructions_ref": instr, "briefed_at": at,
            **{c: limbs.get(c, True) for c in CAPABILITIES}}


def briefing(r=None, briefings=None) -> dict:
    r = r or roster()
    return compose_briefing_record(r, INSTR, briefings if briefings is not None else
                                   [brief("person:a"), brief("person:b")], "2026-10-05T01:00:00Z")


def flag(ref, at="2026-10-06T09:00:00Z") -> dict:
    return {"decision_ref": ref, "flagged_at": at, "output_ref": f"out:{ref}"}


def rev(ref, reviewer="person:a", at="2026-10-06T12:00:00Z", disposition="upheld") -> dict:
    return {"decision_ref": ref, "reviewer_ref": reviewer, "reviewed_at": at, "disposition": disposition}


def disposition(flagged=(), reviews=(), bio=NO_BIO, r=None, b=None, cycle=CYCLE) -> dict:
    r = r or roster()
    b = b or briefing(r)
    return review_flagged_decisions(r, b, cycle, list(flagged), list(reviews), bio, NOW)


def intervene(ref, kind="override_or_reverse_output", who="person:a", at="2026-10-06T15:00:00Z") -> dict:
    return {"decision_ref": ref, "intervention_type": kind, "intervened_by": who,
            "basis": "applicant income evidence contradicts the model's input", "intervened_at": at}


# --------------------------------------------------------------------------- roster (Art. 14(4)(d)-(e))


def test_an_effective_roster_has_a_reachable_empowered_natural_person() -> None:
    r = roster()
    assert r["effective"] is True and r["empowered_overseers"] == ["person:a", "person:b"]
    assert r["not_empowered"] == []


@pytest.mark.parametrize(("e", "missing"), [
    (entry("person:c", powers=("decline_use", "disregard_output", "override_or_reverse_output")),
     ["interrupt_operation"]),
    (entry("person:c", authority=None), []),
    (entry("person:c", natural=False), []),
])
def test_an_entry_without_every_power_or_a_delegation_cannot_lawfully_oversee(e, missing) -> None:
    r = roster(entry("person:a"), e)
    c = next(x for x in r["entries"] if x["person_ref"] == "person:c")
    assert c["empowered"] is False and c["missing_powers"] == missing
    assert r["not_empowered"] == ["person:c"] and r["empowered_overseers"] == ["person:a"]


def test_a_roster_with_no_reachable_empowered_overseer_is_not_effective() -> None:
    r = roster(entry("person:a", reachable=False), entry("person:b", on_watch=False))
    assert r["effective"] is False and r["empowered_overseers"] == ["person:a"]
    assert r["reachable_empowered_overseers"] == []


@pytest.mark.parametrize("bad", [
    {"cycle": "2026-10-05T00:00:00Z"},
    {"cycle": "2026-10-11T00:00:00Z/2026-10-05T00:00:00Z"},
    {"entries": [entry("person:a", powers=("press_any_key",))]},
    {"entries": [entry("person:a"), entry("person:a")]},
    {"entries": []},
    {"entries": [entry("person:a") | {"reachable": "yes"}]},
])
def test_the_roster_rejects_malformed_input(bad) -> None:
    with pytest.raises(InvalidOversightRosterError):
        resolve_oversight_roster(DEPLOYMENT, bad.get("cycle", CYCLE), bad.get("entries", [entry("person:a")]), NOW)


# --------------------------------------------------------------------------- briefing (Art. 14(4)(a)-(c))


def test_every_empowered_overseer_briefed_on_this_system() -> None:
    b = briefing()
    assert b["all_briefed"] is True and b["briefed_overseers"] == ["person:a", "person:b"]
    assert b["rejected_briefings"] == []


def test_a_briefing_for_another_deployment_or_old_instructions_does_not_count() -> None:
    b = briefing(briefings=[brief("person:a"), brief("person:b", deployment="deploy:other"),
                            brief("person:b", instr="provider:acme-score:ifu:v2")])
    assert b["unbriefed_overseers"] == ["person:b"] and b["all_briefed"] is False
    assert b["rejected_briefings"] == [{"person_ref": "person:b", "reason": "different_deployment"},
                                       {"person_ref": "person:b", "reason": "superseded_instructions"}]


def test_automation_bias_is_a_briefing_limb_of_its_own() -> None:
    b = briefing(briefings=[brief("person:a"), brief("person:b", automation_bias_awareness=False)])
    o = next(x for x in b["overseers"] if x["person_ref"] == "person:b")
    assert o["briefed"] is False and o["missing_limbs"] == ["automation_bias_awareness"]


def test_the_latest_briefing_counts_and_an_absent_one_misses_every_limb() -> None:
    b = briefing(briefings=[brief("person:a", output_interpretation=False, at="2026-09-01T10:00:00Z"),
                            brief("person:a", at="2026-09-30T10:00:00Z")])
    by = {o["person_ref"]: o for o in b["overseers"]}
    assert by["person:a"]["briefed"] is True
    assert by["person:b"]["missing_limbs"] == list(CAPABILITIES)


def test_briefing_rejects_malformed_input() -> None:
    with pytest.raises(InvalidBriefingRecordError):
        briefing(briefings=[brief("person:a") | {"output_interpretation": "true"}])


# --------------------------------------------------------------------------- review and Art. 14(5)


def test_a_quiet_window_is_evidence_too() -> None:
    d = disposition()
    assert (d["flagged_count"], d["reviewed_count"], d["intervened_count"]) == (0, 0, 0)
    assert d["metric_stamps"] == ["kpi.eu_ai_act_oversight_intervention_rate@v1"]
    assert d["biometric_two_person_verification"] is None


def test_every_flagged_decision_ends_upheld_intervened_or_unreviewed() -> None:
    d = disposition([flag("d:1"), flag("d:2"), flag("d:3", at="2026-10-07T09:00:00Z")],
                    [rev("d:1"), rev("d:2", reviewer="person:b", disposition="intervened")])
    by = {x["decision_ref"]: x for x in d["decisions"]}
    assert [by[k]["disposition"] for k in ("d:1", "d:2", "d:3")] == ["upheld", "intervened", "unreviewed"]
    assert (d["reviewed_count"], d["intervened_count"]) == (2, 1)
    assert d["unreviewed_decisions"] == ["d:3"] and by["d:1"]["action_permitted"] is True


def test_only_a_qualified_overseers_review_counts() -> None:
    r = roster(entry("person:a"), entry("person:b"), entry("person:c", authority=None))
    b = briefing(r, [brief("person:a")])                       # person:b empowered but unbriefed
    d = disposition([flag("d:1"), flag("d:2")], [rev("d:1", reviewer="person:b"), rev("d:2", reviewer="person:c")],
                    r=r, b=b)
    assert d["reviewed_count"] == 0 and d["unreviewed_decisions"] == ["d:1", "d:2"]
    assert [x["reason"] for x in d["reviews_not_counted"]] == ["reviewer_not_qualified"] * 2


def test_art_14_5_needs_two_distinct_qualified_verifiers_before_action() -> None:
    bio = {"annex_iii_point_1a": True, "exemption_legal_basis_ref": None, "verifications": [
        {"decision_ref": "id:1", "verifier_refs": ["person:a", "person:b"]},
        {"decision_ref": "id:2", "verifier_refs": ["person:a", "person:a"]},       # one person twice
        {"decision_ref": "id:3", "verifier_refs": ["person:a", "person:z"]},       # person:z not qualified
    ]}
    d = disposition([flag("id:1"), flag("id:2"), flag("id:3")], [rev("id:1"), rev("id:2"), rev("id:3")], bio)
    v = d["biometric_two_person_verification"]
    assert v["applies"] is True and v["exempt"] is False
    assert v["verified_decisions"] == ["id:1"] and v["unverified_decisions"] == ["id:2", "id:3"]
    by = {x["decision_ref"]: x["action_permitted"] for x in d["decisions"]}
    assert by == {"id:1": True, "id:2": False, "id:3": False}


def test_the_art_14_5_exemption_records_its_legal_basis() -> None:
    bio = {"annex_iii_point_1a": True, "exemption_legal_basis_ref": "law:national-border-code:art-12",
           "verifications": []}
    v = disposition([flag("id:1")], [rev("id:1")], bio)["biometric_two_person_verification"]
    assert v["exempt"] is True and v["exemption_legal_basis_ref"] == "law:national-border-code:art-12"


@pytest.mark.parametrize("bad", [
    {"flagged": [flag("d:1", at="2026-10-01T09:00:00Z")]},
    {"flagged": [flag("d:1")], "reviews": [rev("d:9")]},
    {"flagged": [flag("d:1")], "reviews": [rev("d:1", at="2026-10-06T08:00:00Z")]},
    {"flagged": [flag("d:1")], "reviews": [rev("d:1"), rev("d:1")]},
    {"flagged": [flag("d:1")], "reviews": [rev("d:1", disposition="rubber_stamped")]},
    {"bio": {"annex_iii_point_1a": False, "exemption_legal_basis_ref": "law:x", "verifications": []}},
    {"cycle": "2026-10-04T00:00:00Z/2026-10-11T23:59:59Z"},
])
def test_review_rejects_malformed_or_inconsistent_input(bad) -> None:
    with pytest.raises(InvalidReviewError):
        disposition(bad.get("flagged", ()), bad.get("reviews", ()), bad.get("bio", NO_BIO),
                    cycle=bad.get("cycle", CYCLE))


def test_review_refuses_a_briefing_composed_against_another_roster() -> None:
    other = resolve_oversight_roster(DEPLOYMENT, CYCLE, [entry("person:a")], "2026-10-05T02:00:00Z")
    with pytest.raises(InvalidReviewError, match="different roster"):
        disposition(r=roster(), b=briefing(other))


# --------------------------------------------------------------------------- interventions (Art. 14(4)(d)-(e))


def test_a_window_without_interventions_closes_with_a_nil_record() -> None:
    i = record_interventions(disposition([flag("d:1")], [rev("d:1")]), [], NOW)
    assert i["nil_record"] is True and i["intervention_type"] == "none" and i["interventions"] == []
    assert i["metric_stamps"] == ["kpi.eu_ai_act_oversight_intervention_rate@v1"]


def test_an_intervention_names_its_exercise_latency_and_the_system_output() -> None:
    d = disposition([flag("d:1")], [rev("d:1", disposition="intervened")])
    i = record_interventions(d, [intervene("d:1")], NOW)
    x = i["interventions"][0]
    assert i["intervention_type"] == "override_or_reverse_output" and x["basis_article"] == "Art. 14(4)(d)"
    assert x["latency_hours"] == 6 and x["system_output_ref"] == "out:d:1"
    assert i["monitoring_signals"] == [{"decision_ref": "d:1", "system_output_ref": "out:d:1",
                                        "intervention_type": "override_or_reverse_output"}]
    assert i["metric_stamps"] == ["kpi.eu_ai_act_oversight_intervention_rate@v1",
                                  "kri.eu_ai_act_oversight_intervention_latency_hours@v1"]


def test_several_exercises_are_told_apart() -> None:
    d = disposition([flag("d:1"), flag("d:2")], [rev("d:1", disposition="intervened"),
                                                 rev("d:2", reviewer="person:b", disposition="intervened")])
    i = record_interventions(d, [intervene("d:1", kind="decline_use"),
                                 intervene("d:2", kind="interrupt_operation", who="person:b")], NOW)
    assert i["intervention_type"] == "multiple"
    assert i["intervention_types"] == ["decline_use", "interrupt_operation"]
    assert {x["intervention_type"]: x["basis_article"] for x in i["interventions"]} == {
        "decline_use": "Art. 14(4)(d)", "interrupt_operation": "Art. 14(4)(e)"}


@pytest.mark.parametrize("given", [
    [intervene("d:2")],                                      # d:2 was upheld, not intervened
    [],                                                      # d:1 was intervened and has no record
    [intervene("d:1", who="person:b")],                      # not the reviewer
    [intervene("d:1", at="2026-10-06T08:00:00Z")],           # before the flag
    [intervene("d:1") | {"basis": " "}],
    [intervene("d:1", kind="shrug")],
])
def test_interventions_must_agree_with_the_review(given) -> None:
    d = disposition([flag("d:1"), flag("d:2")], [rev("d:1", disposition="intervened"), rev("d:2")])
    with pytest.raises(InvalidInterventionRecordError):
        record_interventions(d, given, NOW)


# --------------------------------------------------------------------------- evidence


def cycle_records(flagged=(flag("d:1"),), reviews=(rev("d:1"),), bio=NO_BIO):
    r = roster()
    b = briefing(r)
    d = disposition(flagged, reviews, bio, r=r, b=b)
    return r, b, d, record_interventions(d, [], NOW)


def test_the_evidence_shows_oversight_exercised_not_merely_assigned() -> None:
    e = compose_oversight_evidence(*cycle_records(), "wf:aho", "exec:1", NOW)
    assert e["oversight_exercised"] is True and e["all_flagged_reviewed"] is True
    assert (e["flagged_count"], e["reviewed_count"], e["intervened_count"]) == (1, 1, 0)
    assert e == compose_oversight_evidence(*cycle_records(), "wf:aho", "exec:1", NOW)


def test_an_unreviewed_decision_means_oversight_was_not_exercised() -> None:
    bio = {"annex_iii_point_1a": True, "exemption_legal_basis_ref": None, "verifications": []}
    e = compose_oversight_evidence(*cycle_records((flag("d:1"), flag("d:2")), (rev("d:1"),), bio),
                                   "wf:aho", "exec:1", NOW)
    assert e["oversight_exercised"] is False and e["all_flagged_reviewed"] is False
    assert e["biometric_unverified_decisions"] == ["d:1"]


def test_the_evidence_refuses_records_from_another_review() -> None:
    r, b, d, i = cycle_records()
    other = disposition([flag("d:9")], [rev("d:9")], r=r, b=b)
    with pytest.raises(InvalidOversightEvidenceError, match="different review"):
        compose_oversight_evidence(r, b, other, i, "wf:aho", "exec:1", NOW)


# --------------------------------------------------------------------------- cross-cutting


def test_outputs_are_json_native() -> None:
    r, b, d, i = cycle_records()
    for out in (r, b, d, i, compose_oversight_evidence(r, b, d, i, "wf:aho", "exec:1", NOW)):
        assert json.loads(json.dumps(out)) == out


def test_metric_stamps_are_declared_on_the_playbook_and_on_the_step() -> None:
    doc = json.loads(PLAYBOOK.read_text(encoding="utf-8"))
    declared = set(secops_extension(doc)["metric_refs"])
    steps = {s["name"]: set((secops_extension(s) or {}).get("metric_refs") or []) for s in doc["workflow"].values()}
    r, b, _, _ = cycle_records()
    d = disposition([flag("d:1")], [rev("d:1", disposition="intervened")], r=r, b=b)
    i = record_interventions(d, [intervene("d:1")], NOW)
    for step, out in (("establish_oversight_roster", r), ("brief_oversight_personnel", b),
                      ("review_flagged_decisions", d), ("record_intervention", i),
                      ("emit_oversight_evidence", compose_oversight_evidence(r, b, d, i, "wf:aho", "exec:1", NOW))):
        assert set(out["metric_stamps"]) <= declared and set(out["metric_stamps"]) <= steps[step], step


def test_the_powers_are_the_four_art_14_4_d_e_exercises() -> None:
    assert POWERS == ("decline_use", "disregard_output", "override_or_reverse_output", "interrupt_operation")
