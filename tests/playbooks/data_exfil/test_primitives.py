"""Unit coverage for content/playbooks/data_exfil/primitives (CORE-PRIM)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from content.playbooks.data_exfil.primitives import (
    InvalidContainmentError,
    InvalidEgressSignalError,
    InvalidNotificationError,
    InvalidScopeAssessmentError,
    assess_exfil_scope,
    compose_exfil_containment,
    compose_regulator_notification,
    compose_subject_notification,
    triage_egress_signal,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
ROUTING = {"regulator_classifications": ["restricted", "special-category"], "subject_threshold": 100}
AUTH = {"protected_hosts": ["host:hr-db"], "protected_identities": ["user:ciso"], "isolation_subject_threshold": 500}
HIGH_RISK = {"high_risk_classifications": ["restricted", "special-category"]}
CHANNELS = {"gdpr": "authority:dpa", "nis2": "authority:csirt", "dora": "authority:nca"}
DETECTED, AWARE = "2026-09-25T08:00:00Z", "2026-09-25T10:00:00Z"


def signal(**kw) -> dict:
    base = {"signal_id": "sig:dlp-77", "source": "dlp", "detected_at": DETECTED, "actor_ref": "user:jdoe",
            "asset_ref": "host:lt-12", "destination": "Files.Example-Share.com", "channel": "https",
            "bytes_out": 52_428_800, "indicators": ["dlp_policy_match"]}
    base.update(kw)
    return base


def triage(benign=(), **kw) -> dict:
    return triage_egress_signal(signal(**kw), list(benign))


def findings(*pairs) -> list:
    return [{"classification": c, "subject_refs": list(refs)} for c, refs in pairs]


def scope(t=None, found=None, control="allowed", routing=ROUTING) -> dict:
    return assess_exfil_scope(t or triage(), findings(("confidential", ["s1", "s2"])) if found is None else found,
                              control, routing)


# --------------------------------------------------------------------------- triage


def test_triage_record_and_canonical_destination() -> None:
    t = triage()
    assert t["destination"] == "files.example-share.com"
    assert t["known_benign"] is False and t["matched_pattern"] is None


def test_a_benign_pattern_matches_only_on_every_field_it_names() -> None:
    assert triage([{"destination": "files.example-share.com"}])["known_benign"] is True
    assert triage([{"destination": "files.example-share.com", "actor_ref": "user:backup"}])["known_benign"] is False
    assert triage([{"destination": "files.example-share.com", "channel": "https"}])["known_benign"] is True


def test_a_staging_archive_is_never_cleared_by_a_benign_pattern() -> None:
    t = triage([{"destination": "files.example-share.com"}],
               indicators=["dlp_policy_match", "staging_archive_created"])
    assert t["known_benign"] is False and t["benign_refused"] == "staging_archive_created"


@pytest.mark.parametrize("override", [
    {"indicators": ["exfil_detected"]}, {"source": "email"}, {"channel": "carrier_pigeon"},
    {"bytes_out": -1}, {"bytes_out": True}, {"detected_at": "today"},
])
def test_triage_rejects_malformed_signals(override) -> None:
    with pytest.raises(InvalidEgressSignalError):
        triage(**override)


# --------------------------------------------------------------------------- scope


@pytest.mark.parametrize(("t_kw", "benign", "control", "confirmed", "basis"), [
    ({}, (), "allowed", True, "data_left_boundary"),
    ({}, (), "partial", True, "data_left_boundary"),
    ({}, (), "blocked", False, "prevented_in_line"),
    ({"bytes_out": 0}, (), "allowed", False, "no_data_left"),
    ({}, ({"destination": "files.example-share.com"},), "allowed", False, "known_benign_egress"),
])
def test_confirmation(t_kw, benign, control, confirmed, basis) -> None:
    s = scope(triage(benign, **t_kw), control=control)
    assert (s["exfil_confirmed"], s["confirmation_basis"]) == (confirmed, basis)
    if not confirmed:
        assert s["regulator_required"] is False


def test_classification_is_the_most_sensitive_seen_and_subjects_are_distinct() -> None:
    s = scope(found=findings(("internal", ["s1", "s2"]), ("restricted", ["s2", "s3"]), ("public", [])))
    assert s["data_classification"] == "restricted" and s["affected_subjects_count"] == 3
    assert s["regulator_reasons"] == ["listed_classification"]


def test_uninspected_content_routes_as_the_worst_case() -> None:
    s = scope(found=findings(("internal", ["s1"]), ("unknown", [])))
    assert s["uninspected_content"] is True and s["subjects_count_is_lower_bound"] is True
    assert s["regulator_required"] is True and "uninspected_content" in s["regulator_reasons"]
    none_found = scope(found=[])
    assert none_found["data_classification"] == "unknown" and none_found["regulator_required"] is True


def test_the_subject_threshold_is_inclusive() -> None:
    refs = [f"s{i}" for i in range(100)]
    assert scope(found=findings(("internal", refs)))["regulator_reasons"] == ["subject_threshold"]
    assert scope(found=findings(("internal", refs[:99])))["regulator_required"] is False


@pytest.mark.parametrize(("found", "control", "routing"), [
    (findings(("secret", [])), "allowed", ROUTING),
    ([{"classification": "internal"}], "allowed", ROUTING),
    (findings(("internal", [])), "maybe", ROUTING),
    (findings(("internal", [])), "allowed", {"regulator_classifications": ["top-secret"], "subject_threshold": 1}),
    (findings(("internal", [])), "allowed", {"regulator_classifications": [], "subject_threshold": 0}),
])
def test_scope_rejects_malformed_inputs(found, control, routing) -> None:
    with pytest.raises(InvalidScopeAssessmentError):
        assess_exfil_scope(triage(), found, control, routing)


# --------------------------------------------------------------------------- containment


def actions(d) -> list:
    return [a["action"] for a in d["actions"]]


@pytest.mark.parametrize(("found", "expected"), [
    (findings(("internal", ["s1"])), ["block_egress_destination", "revoke_sessions"]),
    (findings(("confidential", ["s1"])), ["block_egress_destination", "revoke_sessions", "force_credential_rotation"]),
    (findings(("restricted", ["s1"])), ["block_egress_destination", "revoke_sessions", "force_credential_rotation",
                                         "isolate_host"]),
    (findings(("unknown", [])), ["block_egress_destination", "revoke_sessions", "force_credential_rotation",
                                  "isolate_host"]),
    (findings(("internal", [f"s{i}" for i in range(500)])), ["block_egress_destination", "revoke_sessions",
                                                             "isolate_host"]),
])
def test_containment_is_proportionate(found, expected) -> None:
    t = triage()
    assert actions(compose_exfil_containment(t, scope(t, found), AUTH, "2026-09-25T10:05:00Z")) == expected


def test_protected_assets_wait_for_approval() -> None:
    t = triage(actor_ref="user:ciso", asset_ref="host:hr-db")
    d = compose_exfil_containment(t, scope(t, findings(("restricted", ["s1"]))), AUTH, "2026-09-25T10:05:00Z")
    assert d["requires_approval"] is True and d["approval_reasons"] == ["protected_host", "protected_identity"]


def test_containment_rechecks_the_gate() -> None:
    t = triage()
    for gate in (False, "true"):
        s = scope(t)
        s["exfil_confirmed"] = gate
        with pytest.raises(InvalidContainmentError, match="only when exfil_confirmed is True"):
            compose_exfil_containment(t, s, AUTH, "2026-09-25T10:05:00Z")


# --------------------------------------------------------------------------- regulator notification


def regulated(found=None):
    t = triage()
    return t, scope(t, found if found is not None else findings(("restricted", ["s1", "s2"])))


def test_one_notification_per_regime_with_its_own_clock_from_awareness() -> None:
    t, s = regulated()
    n = compose_regulator_notification(t, s, CHANNELS, AWARE)
    assert [(x["regime"], x["basis"], x["due_at"]) for x in n["notifications"]] == [
        ("dora", "DORA Art. 19(4)(a)", "2026-09-26T10:00:00Z"),
        ("gdpr", "GDPR Art. 33(1)", "2026-09-28T10:00:00Z"),
        ("nis2", "NIS2 Art. 23(4)(a)", "2026-09-26T10:00:00Z"),
    ]
    assert n["finding"]["data_classification"] == "restricted" and n["skipped"] == []


def test_gdpr_is_skipped_only_when_no_personal_data_can_be_affected() -> None:
    t, s = regulated(findings(("restricted", [])))
    n = compose_regulator_notification(t, s, CHANNELS, AWARE)
    assert [x["regime"] for x in n["notifications"]] == ["dora", "nis2"]
    assert n["skipped"] == [{"regime": "gdpr", "reason": "no_personal_data_affected"}]
    t2, s2 = regulated(findings(("unknown", [])))            # uninspected: cannot rule personal data out
    assert "gdpr" in [x["regime"] for x in compose_regulator_notification(t2, s2, CHANNELS, AWARE)["notifications"]]


def test_an_unroutable_obligation_fails_loud() -> None:
    t, s = regulated(findings(("restricted", [])))
    with pytest.raises(InvalidNotificationError, match="no configured authority channel applies"):
        compose_regulator_notification(t, s, {"gdpr": "authority:dpa"}, AWARE)


def test_regulator_notification_rechecks_both_gates_and_the_awareness_instant() -> None:
    t = triage()
    below = scope(t, findings(("internal", ["s1"])))
    with pytest.raises(InvalidNotificationError, match="regulator_required is True"):
        compose_regulator_notification(t, below, CHANNELS, AWARE)
    t, s = regulated()
    with pytest.raises(InvalidNotificationError, match="before detection"):
        compose_regulator_notification(t, s, CHANNELS, "2026-09-25T07:59:59Z")
    with pytest.raises(InvalidNotificationError):
        compose_regulator_notification(t, s, {"sec": "authority:x"}, AWARE)


# --------------------------------------------------------------------------- subject notification


@pytest.mark.parametrize(("found", "required", "basis"), [
    (findings(("restricted", ["s1"])), True, "GDPR Art. 34(1): high-risk classification"),
    (findings(("confidential", ["s1"])), False, "below_high_risk_policy"),
    (findings(("unknown", [])), True, "GDPR Art. 34(1): uninspected content treated as high risk"),
    (findings(("restricted", [])), False, "no_affected_subjects"),
])
def test_the_subject_determination_always_carries_its_basis(found, required, basis) -> None:
    t = triage()
    d = compose_subject_notification(t, scope(t, found), HIGH_RISK, "notify:subjects", AWARE)
    assert (d["required"], d["basis"]) == (required, basis)
    assert (d["notice"] is not None) == required


def test_subject_notification_rejects_a_malformed_policy() -> None:
    t = triage()
    with pytest.raises(InvalidNotificationError):
        compose_subject_notification(t, scope(t), {"high_risk_classifications": ["secret"]}, "notify:subjects", AWARE)


# --------------------------------------------------------------------------- cross-cutting


def _outputs() -> list:
    t, s = regulated()
    return [compose_exfil_containment(t, s, AUTH, "2026-09-25T10:05:00Z"),
            compose_regulator_notification(t, s, CHANNELS, AWARE),
            compose_subject_notification(t, s, HIGH_RISK, "notify:subjects", AWARE)]


def test_every_stamped_metric_is_declared_by_the_playbook() -> None:
    playbook = json.loads((REPO_ROOT / "content/playbooks/data_exfil/playbook.cacao.json").read_text(encoding="utf-8"))
    declared = set(playbook["x_secops_ng"]["metric_refs"])
    stamped = {m for out in _outputs() for m in out["metric_stamps"]}
    assert stamped <= declared, f"undeclared: {sorted(stamped - declared)}"


def test_outputs_are_json_native() -> None:
    t, s = regulated()
    for out in _outputs() + [t, s]:
        assert json.loads(json.dumps(out)) == out


def test_end_to_end_a_signal_flows_to_both_notifications() -> None:
    t = triage([{"destination": "files.example-share.com"}], indicators=["staging_archive_created"])
    s = assess_exfil_scope(t, findings(("special-category", ["s1", "s2", "s3"])), "partial", ROUTING)
    assert s["exfil_confirmed"] is True and s["regulator_required"] is True
    c = compose_exfil_containment(t, s, AUTH, "2026-09-25T10:05:00Z")
    r = compose_regulator_notification(t, s, {"gdpr": "authority:dpa"}, AWARE)
    d = compose_subject_notification(t, s, HIGH_RISK, "notify:subjects", AWARE)
    assert "isolate_host" in actions(c)
    assert r["finding"] == d["finding"] and d["required"] is True
