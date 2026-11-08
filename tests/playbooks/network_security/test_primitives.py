from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from compilers._shared.cacao_parser import secops_extension
from content.playbooks.network_security.primitives import (
    CLASSIFICATIONS,
    DEFAULT_BINDING,
    InvalidPostureEvidenceError,
    InvalidRemediationDispatchError,
    InvalidSegmentationPolicyError,
    InvalidSegmentInventoryError,
    InvalidViolationDetectionError,
    compose_posture_evidence,
    compose_segment_inventory,
    detect_policy_violations,
    dispatch_remediation,
    evaluate_segmentation_policy,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
PLAYBOOK = REPO_ROOT / "content" / "playbooks" / "network_security" / "playbook.cacao.yaml"
WINDOW = "window:2026-11-nightly"
WEB, APP, DB, ADMIN, SHADOW = "seg:web-1", "seg:app-1", "seg:db-1", "seg:admin-1", "seg:app-shadow"
NET, VENDOR = "ext:internet", "ext:vendor"
T0 = "2026-11-08T01:00:00Z"


def seg(ref, zone, cidr, binding="vpc:prod", tenancy="tenant:shared", critical=False) -> dict:
    return {"segment_ref": ref, "zone_ref": zone, "binding_ref": binding, "cidrs": [cidr], "tenancy": tenancy,
            "critical": critical}


def iac() -> dict:
    return {"source_ref": "src:iac", "kind": "declarative", "segments": [
        seg(WEB, "zone:web", "10.0.1.0/24"), seg(APP, "zone:app", "10.0.2.0/24"),
        seg(DB, "zone:db", "10.0.3.0/24", critical=True), seg(ADMIN, "zone:admin", "10.0.9.0/24")]}


def cloud() -> dict:
    return {"source_ref": "src:cloud", "kind": "provider_api", "segments": [
        seg(WEB, "zone:web", "10.0.1.0/24"), seg(APP, "zone:app", "10.0.2.0/24", tenancy="tenant:payments"),
        seg(SHADOW, "zone:app", "10.0.4.0/24")]}


def inventory(sources=None, at="2026-11-08T01:00:00Z") -> dict:
    return compose_segment_inventory(WINDOW, [iac(), cloud()] if sources is None else sources, at)


def transit(src, dst, allowance="allowed", services=None, authorisation=None, valid_from=None,
            valid_until=None) -> dict:
    condition = None
    if allowance == "conditional":
        condition = {"services": services or [], "authorisation_ref": authorisation, "valid_from": valid_from,
                     "valid_until": valid_until}
    return {"from_zone": src, "to_zone": dst, "allowance": allowance, "condition": condition}


def matrix() -> list:
    return [
        transit(NET, "zone:web", "conditional", ["tcp/443"]),
        transit("zone:web", "zone:app", "conditional", ["tcp/8443"]),
        transit("zone:app", "zone:db", "allowed"),
        transit("zone:app", NET, "denied"),
        transit(VENDOR, "zone:app", "conditional", [], "auth:vendor-maint-17", "2026-11-07T22:00:00Z",
                "2026-11-08T00:30:00Z"),
        transit("zone:admin", "zone:web"), transit("zone:admin", "zone:app"), transit("zone:admin", "zone:db"),
    ]


def policy_doc(**over) -> dict:
    p = {"policy_ref": "policy:segmentation", "revision": "rev:42",
         "zones": ["zone:admin", "zone:app", "zone:db", "zone:web"], "external_zones": [NET, VENDOR],
         "admin_zone_ref": "zone:admin", "transits": matrix()}
    return {**p, **over}


def evaluate(inv=None, at="2026-11-08T01:05:00Z", **over) -> dict:
    return evaluate_segmentation_policy(inv or inventory(), policy_doc(**over), at)


def obs(src, dst, svc="tcp/443", first="2026-11-07T23:00:00Z", last="2026-11-07T23:30:00Z", source="flow_log",
        abuse=None) -> dict:
    return {"from_ref": src, "to_ref": dst, "service": svc, "first_seen": first, "last_seen": last,
            "source": source, "abuse_ref": abuse}


def rule(src, dst, svc="any", permits=True, control="fw:edge-1") -> dict:
    return {"control_ref": control, "from_zone": src, "to_zone": dst, "service": svc, "permits": permits}


def detect(observations=(), rules=(), inv=None, pol=None, at="2026-11-08T01:10:00Z") -> dict:
    inv = inv or inventory()
    return detect_policy_violations(inv, pol or evaluate(inv), list(observations), list(rules), at)


def classes(d: dict) -> list:
    return [(v["classification"], v["from_ref"], v["to_ref"], v["service"]) for v in d["violations"]]


def dispatch_all(d: dict, binding=None, automated=False, at="2026-11-08T01:20:00Z", surfaces=None) -> dict:
    routes = binding or DEFAULT_BINDING
    rows = []
    for n, v in enumerate(d["violations"]):
        surface = (surfaces or {}).get(v["violation_id"]) or (
            "isolation" if v["active_abuse"] and automated else routes[v["classification"]])
        rows.append({"violation_id": v["violation_id"], "surface": surface, "action_ref": f"chg:{n}",
                     "dispatched_at": "2026-11-08T01:15:00Z"})
    return dispatch_remediation(d, dict(routes), automated, rows, at)


def violating() -> dict:
    return detect([obs(APP, NET, "tcp/25"), obs(WEB, APP, "tcp/22")], [rule("zone:web", "zone:db")])


# --------------------------------------------------------------------------- inventory_network_segments


def test_the_higher_precedence_source_wins_and_disagreement_is_recorded() -> None:
    inv = inventory()
    segs = {s["segment_ref"]: s for s in inv["segments"]}
    assert segs[APP]["tenancy"] == "tenant:shared" and segs[APP]["reported_by"] == ["src:iac", "src:cloud"]
    assert inv["disagreements"] == [{"segment_ref": APP, "field": "tenancy", "kept_from": "src:iac",
                                     "differs_in": "src:cloud"}]
    assert inv["source_refs"] == ["src:iac", "src:cloud"] and inv["metric_stamps"] == []


def test_a_segment_no_declarative_source_reports_is_undocumented() -> None:
    inv = inventory()
    assert inv["undocumented_segments"] == [SHADOW]
    assert {s["segment_ref"]: s["documented"] for s in inv["segments"]}[WEB] is True


def test_the_inventory_identifier_replays_and_tracks_the_sources() -> None:
    assert inventory()["segment_inventory_id"] == inventory(at="2026-11-08T03:00:00Z")["segment_inventory_id"]
    assert inventory()["segment_inventory_id"] != inventory([cloud(), iac()])["segment_inventory_id"]
    assert inventory()["segment_inventory_id"] != compose_segment_inventory(
        "window:other", [iac(), cloud()], T0)["segment_inventory_id"]


def test_overlapping_ranges_are_listed_only_inside_one_binding() -> None:
    src = {"source_ref": "src:iac", "kind": "declarative", "segments": [
        seg("seg:a", "zone:app", "10.1.0.0/16"), seg("seg:b", "zone:app", "10.1.2.0/24"),
        seg("seg:c", "zone:app", "10.1.0.0/16", binding="vpc:other")]}
    assert inventory([src])["overlaps"] == [["seg:a", "seg:b"]]


def test_ranges_are_canonical_and_sorted() -> None:
    s = seg(WEB, "zone:web", "10.0.1.0/24")
    s["cidrs"] = ["2001:db8::/32", "10.0.1.0/24", "10.0.1.0/24"]
    (g,) = inventory([{"source_ref": "src:iac", "kind": "declarative", "segments": [s]}])["segments"]
    assert g["cidrs"] == ["10.0.1.0/24", "2001:db8::/32"]


@pytest.mark.parametrize("sources", [
    [],
    [iac(), iac()],
    [{"source_ref": "src:iac", "kind": "declarative", "segments": [seg(WEB, "zone:web", "10.0.1.0/24")] * 2}],
    [{"source_ref": "src:iac", "kind": "spreadsheet", "segments": []}],
    [{"source_ref": "src:iac", "kind": "declarative", "segments": [seg(WEB, "zone:web", "10.0.1.7/24")]}],
    [{"source_ref": "src:iac", "kind": "declarative", "segments": [{**seg(WEB, "zone:web", "10.0.1.0/24"),
                                                                    "cidrs": []}]}],
    [{"source_ref": "src:iac", "kind": "declarative", "segments": [{**seg(WEB, "zone:web", "10.0.1.0/24"),
                                                                    "critical": "false"}]}],
])
def test_a_malformed_source_or_segment_is_refused(sources) -> None:
    with pytest.raises(InvalidSegmentInventoryError):
        inventory(sources)


# --------------------------------------------------------------------------- evaluate_segmentation_policy


def test_the_matrix_is_normalised_and_its_snapshot_pinned() -> None:
    inv = inventory()
    p = evaluate(inv)
    assert (p["window_ref"], p["segment_inventory_id"]) == (WINDOW, inv["segment_inventory_id"])
    assert [(t["from_zone"], t["to_zone"]) for t in p["transits"]] == sorted(
        (t["from_zone"], t["to_zone"]) for t in matrix())
    vendor = next(t for t in p["transits"] if t["from_zone"] == VENDOR)
    assert vendor["condition"]["authorisation_ref"] == "auth:vendor-maint-17" and vendor["condition"]["services"] == []
    assert p["findings"] == [] and p["metric_stamps"] == []
    assert p["policy_snapshot_id"] == evaluate(at="2026-11-08T02:00:00Z")["policy_snapshot_id"]
    assert p["policy_snapshot_id"] != evaluate(revision="rev:43")["policy_snapshot_id"]


def test_the_policy_records_its_own_gaps() -> None:
    legacy = {"source_ref": "src:legacy-iac", "kind": "declarative", "segments": [seg("seg:old", "zone:legacy", "10.9.0.0/24")]}
    p = evaluate(inventory([iac(), legacy]), admin_zone_ref=None,
                 transits=matrix() + [transit(VENDOR, "zone:admin", "denied")])
    assert p["findings"] == ["zone_not_in_policy:zone:legacy", "no_admin_zone"]
    p = evaluate(transits=matrix() + [transit(NET, "zone:admin", "conditional", ["tcp/22"])])
    assert p["findings"] == [f"admin_zone_reachable_from_external:{NET}"]


def test_an_empty_matrix_is_still_a_snapshot() -> None:
    p = evaluate(transits=[])
    assert p["transits"] == [] and p["findings"] == ["no_allowances"] and len(p["policy_snapshot_id"]) == 64


@pytest.mark.parametrize("over", [
    {"transits": [transit("zone:web", "zone:nowhere")]},
    {"transits": [transit(NET, VENDOR)]},
    {"transits": [transit("zone:app", "zone:db"), transit("zone:app", "zone:db", "denied")]},
    {"transits": [{**transit("zone:app", "zone:db"), "condition": {"services": ["tcp/5432"]}}]},
    {"transits": [transit("zone:app", "zone:db", "conditional")]},
    {"transits": [transit("zone:app", "zone:db", "conditional", [], "auth:1", "2026-11-08T00:00:00Z", None)]},
    {"transits": [transit("zone:app", "zone:db", "conditional", ["tcp/5432"], "auth:1")]},
    {"transits": [transit("zone:app", "zone:db", "conditional", [], None, "2026-11-08T00:00:00Z",
                          "2026-11-09T00:00:00Z")]},
    {"transits": [transit("zone:app", "zone:db", "conditional", [], "auth:1", "2026-11-08T00:00:00Z",
                          "2026-11-08T00:00:00Z")]},
    {"transits": [transit("zone:app", "zone:db", "conditional", ["tcp/70000"])]},
    {"transits": [transit("zone:app", "zone:db", "conditional", ["https"])]},
    {"admin_zone_ref": NET},
    {"external_zones": [NET, "zone:web"]},
    {"zones": ["zone:app", "zone:app"]},
])
def test_a_malformed_policy_is_refused(over) -> None:
    with pytest.raises(InvalidSegmentationPolicyError):
        evaluate(**over)


def test_evaluation_before_the_inventory_is_refused() -> None:
    with pytest.raises(InvalidSegmentationPolicyError):
        evaluate(at="2026-11-08T00:59:59Z")


# --------------------------------------------------------------------------- detect_policy_violations


def test_allowed_and_satisfied_conditional_transits_are_compliant() -> None:
    d = detect([obs(APP, DB, "tcp/5432"), obs(WEB, APP, "tcp/8443"), obs(NET, WEB, "tcp/443"),
                obs(ADMIN, DB, "tcp/22")])
    assert d["violations"] == [] and (d["observation_count"], d["compliant_observations"]) == (4, 4)


def test_a_conditional_transit_on_another_service_is_undocumented() -> None:
    assert classes(detect([obs(WEB, APP, "tcp/22")])) == [("undocumented_transit", WEB, APP, "tcp/22")]


def test_every_unlisted_pair_is_denied_within_a_zone_too() -> None:
    d = detect([obs(APP, SHADOW, "tcp/9000"), obs(DB, APP, "tcp/5432")])
    assert classes(d) == [("undocumented_transit", APP, SHADOW, "tcp/9000"),
                          ("undocumented_transit", DB, APP, "tcp/5432")]


def test_traffic_to_an_external_zone_outside_the_matrix_is_unauthorised_egress() -> None:
    d = detect([obs(APP, NET, "tcp/25"), obs(DB, VENDOR, "tcp/443"), obs(NET, APP, "tcp/22")])
    assert classes(d) == [("unauthorised_egress", APP, NET, "tcp/25"), ("unauthorised_egress", DB, VENDOR, "tcp/443"),
                          ("undocumented_transit", NET, APP, "tcp/22")]


def test_a_time_boxed_allowance_covers_only_its_window() -> None:
    inside = obs(VENDOR, APP, "tcp/22", "2026-11-07T22:00:00Z", "2026-11-08T00:30:00Z")
    beyond = obs(VENDOR, APP, "tcp/22", "2026-11-07T23:00:00Z", "2026-11-08T00:30:01Z")
    assert detect([inside])["violations"] == []
    assert classes(detect([beyond])) == [("undocumented_transit", VENDOR, APP, "tcp/22")]


def test_repeated_sightings_merge_into_one_violation() -> None:
    (v,) = detect([obs(APP, NET, "tcp/25", "2026-11-07T23:00:00Z", "2026-11-07T23:10:00Z"),
                   obs(APP, NET, "tcp/25", "2026-11-07T22:00:00Z", "2026-11-07T22:05:00Z", "probe", "ti:c2-feed-9"),
                   obs(APP, NET, "tcp/25", "2026-11-08T00:00:00Z", "2026-11-08T00:01:00Z")])["violations"]
    assert (v["first_seen"], v["last_seen"]) == ("2026-11-07T22:00:00Z", "2026-11-08T00:01:00Z")
    assert (v["sources"], v["abuse_refs"], v["active_abuse"]) == (["flow_log", "probe"], ["ti:c2-feed-9"], True)


def test_a_violation_touching_a_critical_segment_is_marked() -> None:
    d = detect([obs(WEB, DB, "tcp/5432"), obs(WEB, SHADOW, "tcp/80")])
    assert {v["to_ref"]: v["critical"] for v in d["violations"]} == {DB: True, SHADOW: False}


@pytest.mark.parametrize("r, direction", [
    (rule("zone:web", "zone:db"), "more_permissive"),
    (rule("zone:app", NET, "tcp/443"), "more_permissive"),
    (rule("zone:web", "zone:app", "any"), "more_permissive"),
    (rule("zone:web", "zone:app", "tcp/22"), "more_permissive"),
    (rule(VENDOR, "zone:app", "tcp/22"), "more_permissive"),
    (rule("zone:app", "zone:db", "tcp/5432", permits=False), "more_restrictive"),
])
def test_a_boundary_rule_that_diverges_from_the_matrix_is_drift(r, direction) -> None:
    (v,) = detect(rules=[r])["violations"]
    assert (v["classification"], v["drift"], v["control_ref"]) == ("boundary_control_drift", direction, "fw:edge-1")
    assert v["first_seen"] is None and v["active_abuse"] is False


@pytest.mark.parametrize("r", [
    rule("zone:app", "zone:db", "tcp/5432"),
    rule("zone:web", "zone:app", "tcp/8443"),
    rule("zone:app", NET, "any", permits=False),
    rule("zone:web", "zone:db", permits=False),
])
def test_a_boundary_rule_in_line_with_the_matrix_is_not_drift(r) -> None:
    assert detect(rules=[r])["violations"] == []


def test_a_time_boxed_rule_inside_its_window_is_not_drift() -> None:
    assert detect(rules=[rule(VENDOR, "zone:app", "tcp/22")], at="2026-11-08T01:10:00Z")["violations"] != []
    inv = inventory(at="2026-11-07T21:00:00Z")
    pol = evaluate(inv, at="2026-11-07T21:05:00Z")
    assert detect(rules=[rule(VENDOR, "zone:app", "tcp/22")], inv=inv, pol=pol,
                  at="2026-11-08T00:00:00Z")["violations"] == []


def test_identifiers_replay_and_an_empty_set_has_one() -> None:
    d = violating()
    assert [v["violation_id"] for v in d["violations"]] == [v["violation_id"] for v in violating()["violations"]]
    clean = detect()
    assert clean["violations"] == [] and len(clean["violation_set_id"]) == 64
    assert clean["violation_set_id"] != d["violation_set_id"]
    other = detect([obs(APP, NET, "tcp/25"), obs(WEB, APP, "tcp/22")], [rule("zone:web", "zone:db")],
                   pol=evaluate(revision="rev:43"))
    assert {v["violation_id"] for v in other["violations"]}.isdisjoint(v["violation_id"] for v in d["violations"])


@pytest.mark.parametrize("observations, rules", [
    ([obs("seg:unknown", APP)], []),
    ([obs(NET, VENDOR)], []),
    ([obs(APP, DB, last="2026-11-08T01:10:01Z", first="2026-11-08T01:00:00Z")], []),
    ([obs(APP, DB, first="2026-11-08T00:00:00Z", last="2026-11-07T23:00:00Z")], []),
    ([obs(APP, DB, source="netflow-guess")], []),
    ([obs(APP, DB, svc="tcp/0")], []),
    ([], [rule("zone:app", "zone:db"), rule("zone:app", "zone:db")]),
    ([], [rule("zone:app", "zone:nowhere")]),
    ([], [rule("zone:app", "zone:db", permits="yes")]),
])
def test_a_malformed_observation_or_rule_is_refused(observations, rules) -> None:
    with pytest.raises(InvalidViolationDetectionError):
        detect(observations, rules)


def test_detection_against_another_inventory_is_refused() -> None:
    with pytest.raises(InvalidViolationDetectionError, match="different inventory"):
        detect(inv=inventory(), pol=evaluate(inventory([iac()])))


# --------------------------------------------------------------------------- enforce_remediation


def test_every_violation_is_dispatched_on_its_bound_surface() -> None:
    d = violating()
    r = dispatch_all(d)
    assert {row["classification"]: row["surface"] for row in r["dispatch_table"]} == DEFAULT_BINDING
    assert r["violation_set_id"] == d["violation_set_id"] and len(r["remediation_action_id"]) == 64
    assert r["metric_stamps"] == []


def test_isolation_needs_both_an_active_abuse_fingerprint_and_the_operators_consent() -> None:
    d = detect([obs(APP, NET, "tcp/25", abuse="ti:c2-feed-9"), obs(WEB, APP, "tcp/22")])
    r = dispatch_all(d, automated=True)
    assert {row["classification"]: row["surface"] for row in r["dispatch_table"]} == {
        "unauthorised_egress": "isolation", "undocumented_transit": "acl_change"}
    assert {row["surface"] for row in dispatch_all(d, automated=False)["dispatch_table"]} == {"acl_change"}
    calm = next(v["violation_id"] for v in d["violations"] if not v["active_abuse"])
    with pytest.raises(InvalidRemediationDispatchError, match="goes to acl_change"):
        dispatch_all(d, automated=True, surfaces={calm: "isolation"})


def test_the_operator_binding_is_honoured() -> None:
    binding = {**DEFAULT_BINDING, "boundary_control_drift": "acl_change"}
    r = dispatch_all(violating(), binding=binding)
    assert {row["surface"] for row in r["dispatch_table"]} == {"acl_change"}


@pytest.mark.parametrize("binding", [
    {**DEFAULT_BINDING, "boundary_control_drift": "isolation"},
    {k: v for k, v in DEFAULT_BINDING.items() if k != "unauthorised_egress"},
    {**DEFAULT_BINDING, "unauthorised_egress": "email"},
])
def test_a_malformed_binding_is_refused(binding) -> None:
    with pytest.raises(InvalidRemediationDispatchError):
        dispatch_remediation(violating(), binding, False, [], "2026-11-08T01:20:00Z")


def test_a_misrouted_unknown_repeated_or_missing_dispatch_is_refused() -> None:
    d = violating()
    good = dispatch_all(d)["dispatch_table"]
    rows = [{k: r[k] for k in ("violation_id", "surface", "action_ref", "dispatched_at")} for r in good]
    cases = [
        [{**rows[0], "surface": "posture_ticket"}] + rows[1:],
        rows + [{**rows[0], "violation_id": "f" * 64}],
        rows + [rows[0]],
        rows[:-1],
        [{**rows[0], "dispatched_at": "2026-11-08T01:09:59Z"}] + rows[1:],
        [{**rows[0], "action_ref": ""}] + rows[1:],
    ]
    for case in cases:
        with pytest.raises(InvalidRemediationDispatchError):
            dispatch_remediation(d, dict(DEFAULT_BINDING), False, case, "2026-11-08T01:20:00Z")


def test_an_empty_set_dispatches_nothing() -> None:
    r = dispatch_all(detect())
    assert (r["dispatch_table"], r["remediation_action_id"]) == ([], None)


# --------------------------------------------------------------------------- generate_posture_evidence_artifact


def chain(d=None) -> tuple:
    inv = inventory()
    pol = evaluate(inv)
    d = d or detect([obs(APP, NET, "tcp/25"), obs(WEB, APP, "tcp/22")], [rule("zone:web", "zone:db")], inv, pol)
    return inv, pol, d


def test_the_evidence_joins_each_finding_to_its_action_and_carries_open_items() -> None:
    inv, pol, d = chain()
    r = dispatch_all(d)
    e = compose_posture_evidence(inv, pol, d, r, "2026-11-08T01:30:00Z")
    assert [(f["classification"], f["surface"], f["action_ref"]) for f in e["findings"]] == [
        (row["classification"], row["surface"], row["action_ref"])
        for row in sorted(r["dispatch_table"], key=lambda row: [v["violation_id"] for v in d["violations"]].index(
            row["violation_id"]))]
    assert e["no_findings"] is False and e["remediation_action_id"] == r["remediation_action_id"]
    assert e["open_items"] == [f"undocumented_segment:{SHADOW}", f"source_disagreement:{APP}:tenancy"]
    assert e["assessment_subject"] == {"segment_inventory_id": inv["segment_inventory_id"], "segment_count": 5,
                                       "critical_segment_count": 1}
    assert e["posture_evidence_id"] == compose_posture_evidence(inv, pol, d, r, "2026-11-08T01:30:00Z")[
        "posture_evidence_id"]
    assert e["metric_stamps"] == []


@pytest.mark.parametrize("remediation", [None, "", "dispatched"])
def test_a_clean_window_still_closes_with_evidence(remediation) -> None:
    inv, pol, d = chain(detect())
    rem = dispatch_all(d) if remediation == "dispatched" else remediation
    e = compose_posture_evidence(inv, pol, d, rem, "2026-11-08T01:30:00Z")
    assert (e["findings"], e["no_findings"], e["remediation_action_id"]) == ([], True, None)


def test_violations_without_a_dispatch_record_are_refused() -> None:
    inv, pol, d = chain()
    with pytest.raises(InvalidPostureEvidenceError, match="required"):
        compose_posture_evidence(inv, pol, d, None, "2026-11-08T01:30:00Z")


def test_records_from_another_run_are_refused() -> None:
    inv, pol, d = chain()
    r = dispatch_all(d)
    other_inv = inventory([iac()])
    other_pol = evaluate(other_inv)
    other_d = detect([obs(APP, NET, "tcp/26")], inv=inv, pol=pol)
    cases = [
        (other_inv, pol, d, r),
        (inv, other_pol, d, r),
        (inv, evaluate(inv, revision="rev:43"), d, r),
        (inv, pol, d, dispatch_all(other_d)),
        (inv, pol, d, {**r, "dispatch_table": r["dispatch_table"][1:]}),
        (compose_segment_inventory("window:other", [iac(), cloud()], T0), pol, d, r),
    ]
    for case in cases:
        with pytest.raises(InvalidPostureEvidenceError):
            compose_posture_evidence(*case, "2026-11-08T01:30:00Z")


def test_evidence_before_the_dispatch_is_refused() -> None:
    inv, pol, d = chain()
    with pytest.raises(InvalidPostureEvidenceError):
        compose_posture_evidence(inv, pol, d, dispatch_all(d), "2026-11-08T01:19:59Z")


# --------------------------------------------------------------------------- catalogue contract


def test_the_primitives_back_every_action_step() -> None:
    doc = yaml.safe_load(PLAYBOOK.read_text(encoding="utf-8"))
    actions = [s["name"] for s in doc["workflow"].values() if s["type"] == "action"]
    assert actions == ["inventory_network_segments", "evaluate_segmentation_policy", "detect_policy_violations",
                       "enforce_remediation", "generate_posture_evidence_artifact"]


def test_no_step_stamps_a_metric_the_playbook_does_not_declare() -> None:
    doc = yaml.safe_load(PLAYBOOK.read_text(encoding="utf-8"))
    assert not secops_extension(doc).get("metric_refs")
    inv, pol, d = chain()
    r = dispatch_all(d)
    for out in (inv, pol, d, r, compose_posture_evidence(inv, pol, d, r, "2026-11-08T01:30:00Z")):
        assert out["metric_stamps"] == []


def test_the_classifications_and_default_binding_are_the_playbook_taxonomy() -> None:
    assert CLASSIFICATIONS == ("undocumented_transit", "unauthorised_egress", "boundary_control_drift")
    assert DEFAULT_BINDING == {"undocumented_transit": "acl_change", "unauthorised_egress": "acl_change",
                               "boundary_control_drift": "posture_ticket"}
