from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from compilers._shared.cacao_parser import secops_extension
from content.playbooks.threat_intel_ingest.primitives import (
    EXCLUSION_REASONS,
    HOLD_BACK_REASONS,
    KINDS,
    LANES,
    InvalidActivationError,
    InvalidFeedCaptureError,
    InvalidNormalisationError,
    InvalidPropagationError,
    capture_feed_batch,
    normalise_indicators,
    record_blocklist_propagation,
    record_detection_activation,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
PLAYBOOK = REPO_ROOT / "content" / "playbooks" / "threat_intel_ingest" / "playbook.cacao.json"
FEED = "feed:national-csirt"
URL = "https://taxii.csirt.example/api1/collections/indicators/"
SCHEDULED = "2026-10-29T08:00:00Z"
PULLED = "2026-10-29T08:01:00Z"
NOW = "2026-10-29T08:02:00Z"
STAMP = "2026-10-28T08:00:00.000Z"
SHA256 = "a" * 64
IP_RULE = "sigma:a3f55ebd-0c01-4ed6-adc0-8fb76d8cd3cd"
DNS_RULE = "sigma:b55ca2a3-7cff-4dda-8bdd-c7bfa63bf544"
HOST_RULE = "sigma:440a56bf-7873-4439-940a-1c8a671073c2"
PATTERN_RULE = "yara:operator-pattern-lane"


def sid(kind: str, n: int) -> str:
    return f"{kind}--00000000-0000-4000-8000-{n:012d}"


def ind(n: int, pattern: str, confidence: int | None = 80, **over) -> dict:
    o = {"type": "indicator", "spec_version": "2.1", "id": sid("indicator", n), "created": STAMP, "modified": STAMP,
         "pattern": pattern, "pattern_type": "stix", "valid_from": "2026-10-28T08:00:00Z"}
    if confidence is not None:
        o["confidence"] = confidence
    return {**o, **over}


def ip(n: int = 1, value: str = "1.2.3.4", **over) -> dict:
    return ind(n, f"[ipv4-addr:value = '{value}']", **over)


def domain(n: int = 2, value: str = "c2.evil.example", **over) -> dict:
    return ind(n, f"[domain-name:value = '{value}']", **over)


def file_hash(n: int = 3, value: str = SHA256, **over) -> dict:
    return ind(n, f"[file:hashes.'SHA-256' = '{value}']", **over)


def capture(objects=None, pages=None, **over) -> dict:
    args = {"feed_id": FEED, "feed_url": URL, "scheduled_for": SCHEDULED,
            "pages": pages if pages is not None else [{"objects": [ip(), domain(), file_hash()] if objects is None
                                                       else objects}],
            "pulled_at": PULLED}
    return capture_feed_batch(**{**args, **over})


def normalise(objects=None, threshold=70, never_block=(), recent=(), at=NOW) -> dict:
    return normalise_indicators(capture(objects), threshold, list(never_block), list(recent), at)


def by_id(n: dict) -> dict:
    return {i["stix_id"]: i for i in n["indicators"]}


def excluded(n: dict) -> dict:
    return {e["stix_id"]: e for e in n["excluded"]}


def receipt(stix_id, lane, point="fw:edge-1", accepted=True, at="2026-10-29T08:05:00Z") -> dict:
    return {"stix_id": stix_id, "lane": lane, "enforcement_point_ref": point, "accepted": accepted,
            "acknowledged_at": at}


def full_receipts() -> list:
    return [receipt(sid("indicator", 1), "perimeter_inbound"), receipt(sid("indicator", 1), "perimeter_outbound"),
            receipt(sid("indicator", 2), "dns_sinkhole", "dns:rpz-1"),
            receipt(sid("indicator", 3), "edr", "edr:fleet")]


def propagate(n=None, receipts=None, at="2026-10-29T08:07:00Z") -> dict:
    return record_blocklist_propagation(n or normalise(), full_receipts() if receipts is None else receipts, at)


PACK = [{"rule_ref": IP_RULE, "kinds": ["ip"]}, {"rule_ref": DNS_RULE, "kinds": ["domain"]},
        {"rule_ref": HOST_RULE, "kinds": ["file_hash"]}, {"rule_ref": PATTERN_RULE, "kinds": ["pattern"]}]


def act(ref, outcome="activated", at="2026-10-29T08:08:00Z") -> dict:
    return {"rule_ref": ref, "outcome": outcome, "acknowledged_at": at}


def activate(n=None, p="auto", pack=PACK, activations=None, at="2026-10-29T08:09:00Z") -> dict:
    n = n or normalise()
    if p == "auto":
        p = propagate(n) if n["high_confidence"] else None
    if activations is None:
        kinds = {i["kind"] for i in n["indicators"]}
        activations = [act(r["rule_ref"]) for r in pack if kinds.intersection(r["kinds"])]
    return record_detection_activation(n, p, pack, activations, at)


# --------------------------------------------------------------------------- pull upstream feed


def test_a_whole_capture_records_its_provenance_and_counts_for_coverage() -> None:
    b = capture()
    assert b["batch_id"] == hashlib.sha256(f"{FEED}\u001f{SCHEDULED}".encode()).hexdigest()
    assert (b["feed_id"], b["feed_url"], b["page_count"], b["object_count"]) == (FEED, URL, 1, 3)
    assert b["metric_stamps"] == ["kpi.coverage_threat_intel_feed@v1"]


def test_the_bundle_digest_does_not_depend_on_paging() -> None:
    one = capture()
    three = capture(pages=[{"more": True, "next": "p2", "objects": [file_hash()]},
                           {"more": True, "objects": [domain()]}, {"more": False, "objects": [ip()]}])
    assert three["page_count"] == 3 and three["bundle_digest"] == one["bundle_digest"]
    assert capture(objects=[ip(confidence=81)])["bundle_digest"] != one["bundle_digest"]


def test_an_empty_poll_is_a_batch_with_no_objects() -> None:
    b = capture(pages=[{}])
    assert b["object_count"] == 0 and b["objects"] == []


@pytest.mark.parametrize("url", ["http://taxii.csirt.example/api1/collections/indicators/",
                                 "https://user:secret@taxii.csirt.example/api1/", "https:///no-host", "", None])
def test_a_feed_url_must_be_https_without_credentials(url) -> None:
    with pytest.raises(InvalidFeedCaptureError):
        capture(feed_url=url)


@pytest.mark.parametrize("pages", [
    [{"more": True, "objects": [ip()]}],
    [{"objects": [ip()]}, {"objects": [domain()]}],
    [{"more": False, "objects": [ip()]}, {"more": False, "objects": [domain()]}],
    [{"more": "false", "objects": [ip()]}],
    [],
    [{"objects": [ip()], "date_added": PULLED}],
])
def test_a_capture_that_stops_early_or_is_not_an_envelope_list_is_refused(pages) -> None:
    with pytest.raises(InvalidFeedCaptureError):
        capture(pages=pages)


@pytest.mark.parametrize("obj", [
    "indicator--00000000-0000-4000-8000-000000000001",
    {"type": "indicator"},
    {"type": "malware", "id": sid("indicator", 1)},
    {"type": "indicator", "id": "indicator--not-a-uuid"},
])
def test_an_object_that_is_not_a_stix_object_is_refused(obj) -> None:
    with pytest.raises(InvalidFeedCaptureError):
        capture(objects=[ip(), obj])


def test_a_pull_before_its_scheduled_poll_is_refused() -> None:
    with pytest.raises(InvalidFeedCaptureError):
        capture(pulled_at="2026-10-29T07:59:59Z")


# --------------------------------------------------------------------------- normalise STIX to OCSF


def test_exact_values_with_a_stated_confidence_at_the_threshold_are_blocked() -> None:
    n = normalise([ip(confidence=70), domain(value="C2.Evil.Example."), file_hash(value="A" * 64)])
    got = {i["kind"]: (i["value"], i["action"], i["hold_back_reasons"]) for i in n["indicators"]}
    assert got == {"ip": ("1.2.3.4", "block", []), "domain": ("c2.evil.example", "block", []),
                   "file_hash": (SHA256, "block", [])}
    assert by_id(n)[sid("indicator", 3)]["hash_algorithm"] == "SHA-256"
    assert (n["indicator_count"], n["block_count"], n["high_confidence"]) == (3, 3, True)
    assert n["metric_stamps"] == []


@pytest.mark.parametrize("pattern, kind, value", [
    ("[ipv4-addr:value ISSUBSET '5.6.7.0/24']", "ip", "5.6.7.0/24"),
    ("[ipv4-addr:value = '1.2.3.4/32']", "ip", "1.2.3.4"),
    ("[ ipv6-addr:value = '2a00::1' ]", "ip", "2a00::1"),
    ("[file:hashes.MD5 = 'D41D8CD98F00B204E9800998ECF8427E']", "file_hash", "d41d8cd98f00b204e9800998ecf8427e"),
    ("[file:hashes.'SHA-1' = '" + "b" * 40 + "']", "file_hash", "b" * 40),
])
def test_each_exact_value_form_is_recognised_and_canonicalised(pattern, kind, value) -> None:
    (i,) = normalise([ind(7, pattern)])["indicators"]
    assert (i["kind"], i["value"], i["action"]) == (kind, value, "block")


@pytest.mark.parametrize("pattern, pattern_type", [
    ("[ipv4-addr:value = '1.2.3.4'] OR [ipv4-addr:value = '1.2.3.5']", "stix"),
    ("[url:value = 'https://c2.evil.example/x']", "stix"),
    ("[domain-name:value LIKE '%.evil.example']", "stix"),
    ("[file:hashes.SSDEEP = '3:AXGBicFlgVNhBGcL6wCrFQEv:AXGHsNhxLsr2C']", "stix"),
    ("[domain-name:value = 'bücher.example']", "stix"),
    ("rule evil { condition: true }", "yara"),
    ("[ipv4-addr:value = '1.2.3.4']", "snort"),
])
def test_anything_but_an_exact_value_is_armed_for_detection_only(pattern, pattern_type) -> None:
    (i,) = normalise([ind(7, pattern, confidence=100, pattern_type=pattern_type)])["indicators"]
    assert (i["kind"], i["value"], i["pattern_type"]) == ("pattern", pattern, pattern_type)
    assert (i["action"], i["hold_back_reasons"]) == ("detect", ["not_an_exact_value"])


@pytest.mark.parametrize("pattern", [
    "[ipv4-addr:value = '1.2.3.4/24']",
    "[ipv4-addr:value = '2a00::1']",
    "[ipv4-addr:value = '999.1.1.1']",
    "[domain-name:value = 'bad_name.example']",
    "[file:hashes.'SHA-256' = 'abc']",
    "[file:hashes.MD5 = '" + "z" * 32 + "']",
])
def test_a_malformed_exact_value_is_excluded_and_the_batch_proceeds(pattern) -> None:
    n = normalise([ind(7, pattern), domain()])
    assert excluded(n)[sid("indicator", 7)]["reason"] == "malformed"
    assert list(by_id(n)) == [sid("indicator", 2)]


@pytest.mark.parametrize("over, detail", [
    ({"spec_version": "2.0"}, "spec_version"),
    ({"confidence": 101}, "confidence"),
    ({"confidence": True}, "confidence"),
    ({"valid_until": "2026-10-28T08:00:00Z"}, "valid_until"),
    ({"created": "2026-10-28T09:00:00.000Z"}, "created"),
    ({"pattern_type": ""}, "pattern_type"),
    ({"valid_from": "2026-10-28 08:00:00"}, "valid_from"),
    ({"revoked": "true"}, "revoked"),
    ({"object_marking_refs": ["TLP:CLEAR"]}, "object_marking_refs"),
    ({"modified": "yesterday"}, "modified"),
])
def test_a_malformed_indicator_is_excluded_with_the_reason(over, detail) -> None:
    n = normalise([ip(**over), domain()])
    e = excluded(n)[sid("indicator", 1)]
    assert e["reason"] == "malformed" and detail in e["detail"]
    assert n["indicator_count"] == 1


def test_only_the_current_version_counts() -> None:
    old = ip(confidence=30)
    new = ip(confidence=90, modified="2026-10-28T09:00:00.5Z")
    n = normalise([new, old])
    assert by_id(n)[sid("indicator", 1)]["confidence"] == 90 and n["excluded"] == []
    assert by_id(n)[sid("indicator", 1)]["modified"] == "2026-10-28T09:00:00.5Z"


def test_a_repeated_identical_version_is_one_indicator() -> None:
    assert normalise([ip(), ip()])["indicator_count"] == 1


def test_two_different_objects_with_the_same_current_version_are_excluded() -> None:
    n = normalise([ip(confidence=90), ip(confidence=10)])
    assert excluded(n)[sid("indicator", 1)]["reason"] == "conflicting_versions" and n["indicators"] == []


def test_a_revoked_indicator_is_excluded_whatever_its_earlier_versions_said() -> None:
    n = normalise([ip(), ip(modified="2026-10-28T10:00:00Z", revoked=True)])
    assert excluded(n)[sid("indicator", 1)]["reason"] == "revoked" and n["indicators"] == []


@pytest.mark.parametrize("over, reason", [
    ({"valid_until": "2026-10-29T08:02:00Z"}, "expired"),
    ({"valid_until": "2026-10-29T08:01:59.999Z"}, "expired"),
    ({"valid_from": "2026-10-29T08:02:01Z", "valid_until": "2026-11-29T00:00:00Z"}, "not_yet_valid"),
])
def test_an_indicator_outside_its_validity_window_is_excluded(over, reason) -> None:
    assert excluded(normalise([ip(**over)]))[sid("indicator", 1)]["reason"] == reason


def test_an_indicator_valid_until_later_is_used() -> None:
    assert normalise([ip(valid_until="2026-10-29T08:02:01Z")])["indicator_count"] == 1


@pytest.mark.parametrize("confidence, reasons", [(None, ["confidence_unspecified"]), (69, ["below_threshold"]),
                                                 (0, ["below_threshold"])])
def test_an_unstated_or_low_confidence_never_blocks(confidence, reasons) -> None:
    (i,) = normalise([ip(confidence=confidence)])["indicators"]
    assert (i["action"], i["hold_back_reasons"], i["above_threshold"]) == ("detect", reasons, False)


@pytest.mark.parametrize("value", ["10.0.0.1", "127.0.0.1", "203.0.113.7", "0.0.0.0/0", "100.64.0.1"])
def test_an_address_that_is_not_globally_routable_is_never_blocked(value) -> None:
    (i,) = normalise([ip(value=value, confidence=100)])["indicators"]
    assert i["action"] == "detect" and "non_global_address" in i["hold_back_reasons"]


@pytest.mark.parametrize("indicator, protected", [
    (ip(value="1.2.3.4"), "1.2.3.0/24"),
    (ip(value="1.2.0.0/16"), "1.2.3.4"),
    (domain(value="mail.corp.example"), "corp.example"),
    (domain(value="corp.example"), "mail.corp.example"),
    (domain(value="corp.example"), "CORP.EXAMPLE."),
])
def test_an_indicator_overlapping_a_protected_value_is_never_blocked(indicator, protected) -> None:
    (i,) = normalise([indicator], never_block=[protected, "2a00::/16"])["indicators"]
    assert (i["action"], i["hold_back_reasons"]) == ("detect", ["protected"])


def test_a_neighbour_of_a_protected_value_is_still_blocked() -> None:
    n = normalise([ip(value="1.2.4.4"), domain(value="notcorp.example")], never_block=["1.2.3.0/24", "corp.example"])
    assert {i["action"] for i in n["indicators"]} == {"block"}


def test_a_single_label_name_is_never_blocked() -> None:
    (i,) = normalise([domain(value="corp")])["indicators"]
    assert (i["action"], i["hold_back_reasons"]) == ("detect", ["single_label_name"])


def test_a_batch_with_nothing_to_block_is_not_high_confidence() -> None:
    n = normalise([ip(confidence=10), ind(7, "rule x { condition: true }", pattern_type="yara")])
    assert (n["indicator_count"], n["block_count"], n["high_confidence"]) == (2, 0, False)


def test_within_a_batch_the_strongest_record_of_a_value_is_kept() -> None:
    n = normalise([ip(1, confidence=40), ip(4, confidence=95), ip(5, confidence=75)])
    assert list(by_id(n)) == [sid("indicator", 4)]
    assert {k: e["detail"] for k, e in excluded(n).items()} == {sid("indicator", 1): sid("indicator", 4),
                                                                sid("indicator", 5): sid("indicator", 4)}
    assert {e["reason"] for e in n["excluded"]} == {"duplicate_in_batch"}


def seen(indicator: dict, action: str, at: str) -> dict:
    (i,) = normalise([indicator])["indicators"]
    return {"key": i["key"], "action": action, "normalised_at": at}


def test_a_value_normalised_within_24_hours_is_not_repeated() -> None:
    n = normalise([ip(), domain()], recent=[seen(ip(), "block", "2026-10-28T08:02:01Z")])
    assert excluded(n)[sid("indicator", 1)]["reason"] == "seen_within_24h"
    assert list(by_id(n)) == [sid("indicator", 2)]


def test_a_value_last_seen_24_hours_ago_is_normalised_again() -> None:
    n = normalise([ip()], recent=[seen(ip(), "block", "2026-10-28T08:02:00Z")])
    assert n["indicator_count"] == 1


def test_a_duplicate_never_swallows_an_escalation_to_blocking() -> None:
    n = normalise([ip(confidence=90)], recent=[seen(ip(confidence=10), "detect", "2026-10-29T07:00:00Z")])
    assert by_id(n)[sid("indicator", 1)]["action"] == "block"


def test_a_value_once_blocked_within_the_window_stays_deduplicated() -> None:
    recent = [seen(ip(), "block", "2026-10-29T06:00:00Z"), seen(ip(), "detect", "2026-10-29T07:00:00Z")]
    assert normalise([ip(confidence=10)], recent=recent)["indicators"] == []


@pytest.mark.parametrize("entry", [
    {"key": "f" * 64, "action": "block", "normalised_at": "2026-10-29T08:02:01Z"},
    {"key": "not-a-key", "action": "block", "normalised_at": NOW},
    {"key": "f" * 64, "action": "quarantine", "normalised_at": NOW},
    {"key": "f" * 64, "action": "block"},
])
def test_a_malformed_or_future_recent_record_is_refused(entry) -> None:
    with pytest.raises(InvalidNormalisationError):
        normalise(recent=[entry])


def test_relationships_name_what_an_indicator_indicates() -> None:
    malware = {"type": "malware", "spec_version": "2.1", "id": sid("malware", 90), "name": "Tinyloader",
               "is_family": True, "created": STAMP, "modified": STAMP}
    actor = {"type": "threat-actor", "spec_version": "2.1", "id": sid("threat-actor", 91), "name": "Actor One",
             "created": STAMP, "modified": STAMP}
    renamed = {**actor, "name": "Actor Uno", "modified": "2026-10-28T09:00:00.5Z"}

    def rel(n, target, **over):
        return {"type": "relationship", "spec_version": "2.1", "id": sid("relationship", n), "created": STAMP,
                "modified": STAMP, "relationship_type": "indicates", "source_ref": sid("indicator", 1),
                "target_ref": target, **over}

    n = normalise([ip(), malware, renamed, actor, rel(80, sid("malware", 90)), rel(81, sid("threat-actor", 91)),
                   rel(82, sid("campaign", 92)), rel(83, sid("malware", 93), revoked=True),
                   rel(84, sid("identity", 94)), rel(85, sid("malware", 95), relationship_type="related-to")])
    assert by_id(n)[sid("indicator", 1)]["indicates"] == [
        {"ref": sid("campaign", 92), "name": None}, {"ref": sid("malware", 90), "name": "Tinyloader"},
        {"ref": sid("threat-actor", 91), "name": "Actor Uno"}]


def test_producer_and_markings_ride_with_the_record() -> None:
    tlp = "marking-definition--34098fce-860f-48ae-8e50-ebd3cc5e41da"
    (i,) = normalise([ip(created_by_ref=sid("identity", 50), object_marking_refs=[tlp])])["indicators"]
    assert (i["producer_ref"], i["marking_refs"]) == (sid("identity", 50), [tlp])


@pytest.mark.parametrize("threshold", [True, -1, 101, "70", 70.0])
def test_the_threshold_must_be_an_integer_percentage(threshold) -> None:
    with pytest.raises(InvalidNormalisationError):
        normalise(threshold=threshold)


@pytest.mark.parametrize("entry", ["1.2.3.4/24", "not a value", 7, "bad_name.example"])
def test_a_malformed_never_block_entry_is_refused(entry) -> None:
    with pytest.raises(InvalidNormalisationError):
        normalise(never_block=[entry])


def test_a_batch_whose_objects_do_not_match_its_digest_is_refused() -> None:
    b = capture()
    b["objects"][0]["confidence"] = 100
    with pytest.raises(InvalidNormalisationError, match="digest"):
        normalise_indicators(b, 70, [], [], NOW)


def test_normalisation_before_the_pull_is_refused() -> None:
    with pytest.raises(InvalidNormalisationError):
        normalise(at="2026-10-29T08:00:59Z")


def test_every_reason_recorded_is_a_declared_reason() -> None:
    n = normalise([ip(1, value="10.0.0.1", confidence=None), ip(4, revoked=True), ip(5, spec_version="2.0"),
                   ip(6, value="1.2.3.0/24", confidence=50), domain(valid_until="2026-10-29T00:00:00Z"),
                   ind(8, "[url:value = 'x']"), domain(9, value="corp")], never_block=["1.2.3.4"])
    assert {e["reason"] for e in n["excluded"]} <= set(EXCLUSION_REASONS)
    assert {r for i in n["indicators"] for r in i["hold_back_reasons"]} <= set(HOLD_BACK_REASONS)


# --------------------------------------------------------------------------- propagate to blocklist


def test_a_complete_propagation_is_stamped_from_the_confidence_gate() -> None:
    p = propagate()
    assert p["complete"] and p["propagation_minutes"] == 5
    assert p["metric_stamps"] == ["kpi.mttr_blocklist_propagation@v1"]
    assert [(o["kind"], o["lanes_accepted"]) for o in p["indicators"]] == [
        ("ip", ["perimeter_inbound", "perimeter_outbound"]), ("domain", ["dns_sinkhole"]), ("file_hash", ["edr"])]


def test_an_ip_needs_both_perimeter_directions() -> None:
    p = propagate(receipts=[r for r in full_receipts() if r["lane"] != "perimeter_outbound"])
    (o,) = [o for o in p["indicators"] if o["kind"] == "ip"]
    assert (o["propagated"], o["lanes_missing"]) == (False, ["perimeter_outbound"])
    assert (p["complete"], p["propagation_minutes"], p["metric_stamps"]) == (False, None, [])


def test_a_rejected_receipt_is_recorded_but_not_counted() -> None:
    receipts = full_receipts()
    receipts[2] = receipt(sid("indicator", 2), "dns_sinkhole", "dns:rpz-1", accepted=False)
    p = propagate(receipts=receipts)
    assert not p["complete"] and any(not r["accepted"] for r in p["receipts"])
    receipts.append(receipt(sid("indicator", 2), "dns_sinkhole", "dns:rpz-2"))
    assert propagate(receipts=receipts)["complete"]


@pytest.mark.parametrize("extra", [
    receipt(sid("indicator", 9), "edr"),
    receipt(sid("indicator", 2), "edr"),
    receipt(sid("indicator", 1), "perimeter_inbound"),
    receipt(sid("indicator", 3), "edr", "edr:fleet-2", at="2026-10-29T08:01:59Z"),
    receipt(sid("indicator", 3), "edr", "edr:fleet-2", at="2026-10-29T08:07:01Z"),
    receipt(sid("indicator", 3), "edr", "edr:fleet-2", accepted="yes"),
    receipt(sid("indicator", 3), "waf"),
])
def test_an_out_of_place_receipt_is_refused(extra) -> None:
    with pytest.raises(InvalidPropagationError):
        propagate(receipts=full_receipts() + [extra])


def test_a_receipt_for_a_held_back_indicator_is_refused() -> None:
    n = normalise([ip(), domain(confidence=10)])
    with pytest.raises(InvalidPropagationError, match="did not mark"):
        propagate(n, [receipt(sid("indicator", 2), "dns_sinkhole")])


def test_propagation_reruns_its_gate() -> None:
    with pytest.raises(InvalidPropagationError, match="high-confidence"):
        propagate(normalise([ip(confidence=10)]), [])


def test_propagation_before_normalisation_is_refused() -> None:
    with pytest.raises(InvalidPropagationError):
        propagate(receipts=[], at="2026-10-29T08:01:00Z")


# --------------------------------------------------------------------------- activate detection rule


def test_every_indicator_is_armed_by_the_rules_its_kind_selects() -> None:
    d = activate()
    assert [(a["kind"], a["rule_refs"]) for a in d["armed"]] == [("ip", [IP_RULE]), ("domain", [DNS_RULE]),
                                                                 ("file_hash", [HOST_RULE])]
    assert [r["rule_ref"] for r in d["rules"]] == sorted([IP_RULE, DNS_RULE, HOST_RULE])
    assert (d["complete"], d["gaps"], d["unarmed"]) == (True, [], [])
    assert d["metric_stamps"] == ["kpi.mttd_threat_intel_indicator@v1"]
    assert {a["created"] for a in d["armed"]} == {STAMP}


def test_the_low_confidence_branch_arms_without_propagation_and_without_the_mttd_stamp() -> None:
    n = normalise([ip(confidence=10), ind(7, "rule x { condition: true }", confidence=10, pattern_type="yara")])
    for unset in (None, ""):
        d = activate(n, unset)
        assert [a["kind"] for a in d["armed"]] == ["ip", "pattern"] and d["complete"]
        assert d["metric_stamps"] == []


def test_a_held_back_indicator_above_the_threshold_still_anchors_the_mttd() -> None:
    n = normalise([ip(value="10.0.0.1", confidence=95)])
    assert not n["high_confidence"]
    assert activate(n, None)["metric_stamps"] == ["kpi.mttd_threat_intel_indicator@v1"]


def test_a_kind_without_a_rule_or_with_only_failed_rules_is_a_gap() -> None:
    pack = [{"rule_ref": IP_RULE, "kinds": ["ip", "domain"]}, {"rule_ref": HOST_RULE, "kinds": ["file_hash"]}]
    d = activate(pack=pack, activations=[act(IP_RULE), act(HOST_RULE, "failed")])
    assert d["unarmed"] == [{"stix_id": sid("indicator", 3), "kind": "file_hash", "reason": "rules_failed"}]
    assert [a["kind"] for a in d["armed"]] == ["ip", "domain"]
    d = activate(pack=pack[:1], activations=[act(IP_RULE)])
    assert (d["gaps"], d["complete"]) == (["no_rule_for_kind:file_hash"], False)


@pytest.mark.parametrize("activations", [
    [act(IP_RULE), act(DNS_RULE), act(HOST_RULE), act(PATTERN_RULE)],
    [act(IP_RULE), act(DNS_RULE)],
    [act(IP_RULE), act(DNS_RULE), act(HOST_RULE), act(IP_RULE, "refreshed")],
    [act(IP_RULE), act(DNS_RULE), act(HOST_RULE, "disabled")],
    [act(IP_RULE), act(DNS_RULE), act(HOST_RULE, at="2026-10-29T08:06:59Z")],
])
def test_receipts_must_answer_exactly_the_selected_rules(activations) -> None:
    with pytest.raises(InvalidActivationError):
        activate(activations=activations)


def test_the_branch_records_must_fit() -> None:
    n_high, n_low = normalise(), normalise([ip(confidence=10)])
    with pytest.raises(InvalidActivationError, match="required"):
        activate(n_high, None)
    with pytest.raises(InvalidActivationError, match="skips propagation"):
        activate(n_low, propagate(n_high))
    other = normalise_indicators(capture(scheduled_for="2026-10-29T07:00:00Z"), 70, [], [], NOW)
    with pytest.raises(InvalidActivationError, match="different batch"):
        activate(n_high, propagate(other))


def test_activation_before_the_preceding_step_is_refused() -> None:
    with pytest.raises(InvalidActivationError):
        activate(at="2026-10-29T08:06:00Z")


def test_an_empty_batch_arms_nothing_and_is_complete() -> None:
    d = activate(normalise([]), None, activations=[])
    assert (d["rules"], d["armed"], d["complete"], d["metric_stamps"]) == ([], [], True, [])


@pytest.mark.parametrize("pack", [
    PACK + [{"rule_ref": IP_RULE, "kinds": ["ip"]}],
    [{"rule_ref": IP_RULE, "kinds": []}],
    [{"rule_ref": IP_RULE, "kinds": ["ip", "ip"]}],
    [{"rule_ref": IP_RULE, "kinds": ["url"]}],
    [{"rule_ref": "not a ref", "kinds": ["ip"]}],
])
def test_a_malformed_rule_pack_is_refused(pack) -> None:
    with pytest.raises(InvalidActivationError):
        activate(pack=pack, activations=[])


# --------------------------------------------------------------------------- catalogue contract


def test_each_step_stamps_only_metrics_it_declares() -> None:
    doc = json.loads(PLAYBOOK.read_text(encoding="utf-8"))
    declared = set(secops_extension(doc)["metric_refs"])
    steps = {s["name"]: set((secops_extension(s) or {}).get("metric_refs") or []) for s in doc["workflow"].values()}
    n = normalise()
    p = propagate(n)
    for step, out in (("pull upstream feed", capture()), ("normalise STIX to OCSF", n), ("propagate to blocklist", p),
                      ("activate detection rule", activate(n, p))):
        assert set(out["metric_stamps"]) <= declared and set(out["metric_stamps"]) <= steps[step], step


def test_the_primitives_back_every_action_step() -> None:
    doc = json.loads(PLAYBOOK.read_text(encoding="utf-8"))
    actions = [s["name"] for s in doc["workflow"].values() if s["type"] == "action"]
    assert actions == ["pull upstream feed", "normalise STIX to OCSF", "propagate to blocklist",
                       "activate detection rule"]


def test_the_kinds_and_lanes_are_the_cookbook_enforcement_plane() -> None:
    assert KINDS == ("ip", "domain", "file_hash", "pattern")
    assert set(LANES) == set(KINDS) - {"pattern"}
    assert LANES["ip"] == ("perimeter_inbound", "perimeter_outbound")
