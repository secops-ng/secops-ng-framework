"""Unit coverage for content/playbooks/identity_compromise/primitives (CORE-PRIM)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from content.playbooks.identity_compromise.primitives import (
    InvalidHuntSummaryError,
    InvalidIdentitySignalError,
    InvalidMfaResetError,
    InvalidPersistenceRemovalError,
    InvalidSessionRevocationError,
    compose_mfa_reset,
    compose_session_revocation,
    plan_persistence_removal,
    summarise_lateral_hunt,
    triage_identity_signal,
)
from compilers._shared.cacao_parser import secops_extension

REPO_ROOT = Path(__file__).resolve().parents[3]
DETECTED = "2026-09-28T09:00:00Z"
USER = {"principal_type": "user", "privileged": False}
ADMIN = {"principal_type": "user", "privileged": True}
TRAVEL = {"principal_id": "user:jdoe", "kind": "planned_travel",
          "valid_from": "2026-09-27T00:00:00Z", "valid_until": "2026-09-30T00:00:00Z"}


def signal(detections, principal="user:jdoe") -> dict:
    return {"signal_id": "sig:idp-9", "source": "idp_risk_event", "detected_at": DETECTED,
            "principal_id": principal, "detections": list(detections)}


def triage(detections, ctx=USER, patterns=(), verdict=None, principal="user:jdoe") -> dict:
    return triage_identity_signal(signal(detections, principal), ctx, list(patterns), verdict)


def confirmed(ctx=USER) -> dict:
    return triage(["mfa_bypass_signin"], ctx)


# --------------------------------------------------------------------------- triage


@pytest.mark.parametrize(("detections", "ctx", "patterns", "expected", "basis"), [
    (["mfa_bypass_signin"], USER, (), True, "decisive_detection"),
    (["mfa_disabled"], USER, (), True, "decisive_detection"),
    (["assume_role_misuse"], USER, (), True, "decisive_detection"),
    (["impossible_travel", "password_spray"], USER, (), True, "corroborated_detections"),
    (["impossible_travel"], USER, (), False, "insufficient_evidence"),
    (["password_spray"], USER, (), False, "insufficient_evidence"),
    (["impossible_travel"], ADMIN, (), True, "privileged_principal"),
    (["impossible_travel"], USER, (TRAVEL,), False, "cleared_by_benign_pattern"),
    (["impossible_travel"], ADMIN, (TRAVEL,), False, "cleared_by_benign_pattern"),
    (["impossible_travel", "password_spray"], USER, (TRAVEL,), False, "insufficient_evidence"),
    (["impossible_travel", "password_spray"], ADMIN, (TRAVEL,), True, "privileged_principal"),
])
def test_the_confirmation_rule(detections, ctx, patterns, expected, basis) -> None:
    t = triage(detections, ctx, patterns)
    assert (t["compromise_confirmed"], t["confirmation_basis"]) == (expected, basis)


def test_a_benign_pattern_never_clears_an_mfa_bypass() -> None:
    t = triage(["impossible_travel", "mfa_bypass_signin"], USER, [TRAVEL])
    assert t["cleared"] == ["impossible_travel"] and t["compromise_confirmed"] is True


def test_a_benign_pattern_is_active_only_for_its_principal_and_window() -> None:
    other = {**TRAVEL, "principal_id": "user:someone-else"}
    expired = {**TRAVEL, "valid_until": "2026-09-28T08:59:59Z"}
    for p in (other, expired):
        assert triage(["impossible_travel"], ADMIN, [p])["compromise_confirmed"] is True
    edge = {**TRAVEL, "valid_until": DETECTED}
    assert triage(["impossible_travel"], ADMIN, [edge])["cleared"] == ["impossible_travel"]


@pytest.mark.parametrize(("detections", "verdict", "expected", "overridden"), [
    (["mfa_disabled"], "benign", False, True),
    (["password_spray"], "confirmed", True, True),
    (["mfa_disabled"], "confirmed", True, False),
    (["mfa_disabled"], "", True, False),
])
def test_an_analyst_verdict_decides(detections, verdict, expected, overridden) -> None:
    t = triage(detections, USER, (), verdict)
    assert (t["compromise_confirmed"], t["overridden_by_analyst"]) == (expected, overridden)


@pytest.mark.parametrize(("sig", "ctx", "patterns"), [
    (signal(["token_theft"]), USER, []),
    ({**signal([]), "source": "email"}, USER, []),
    (signal([]), {"principal_type": "robot", "privileged": False}, []),
    (signal([]), {"principal_type": "user", "privileged": "yes"}, []),
    (signal([]), USER, [{**TRAVEL, "kind": "vacation"}]),
    (signal([]), USER, [{**TRAVEL, "valid_until": "2026-09-26T00:00:00Z"}]),
])
def test_triage_rejects_malformed_inputs(sig, ctx, patterns) -> None:
    with pytest.raises(InvalidIdentitySignalError):
        triage_identity_signal(sig, ctx, patterns)


# --------------------------------------------------------------------------- mfa


FACTORS = [{"factor_id": "f:webauthn-1", "kind": "webauthn"}, {"factor_id": "f:app-2", "kind": "app_password"},
           {"factor_id": "f:totp-1", "kind": "totp"}]


def test_mfa_reset_documents_before_and_after() -> None:
    d = compose_mfa_reset(confirmed(), FACTORS, "2026-09-28T09:05:00Z")
    assert [a["action"] for a in d["actions"]] == ["invalidate_app_password", "revoke_factor", "revoke_factor",
                                                   "require_reenrolment_with_step_up"]
    assert [f["factor_id"] for f in d["factors_before"]] == ["f:app-2", "f:totp-1", "f:webauthn-1"]
    assert d["factors_after"] == [] and d["applicable"] is True


def test_mfa_does_not_apply_to_a_service_principal() -> None:
    sp = triage(["assume_role_misuse"], {"principal_type": "service_principal", "privileged": False},
                principal="sp:deployer")
    d = compose_mfa_reset(sp, [], "2026-09-28T09:05:00Z")
    assert (d["applicable"], d["reason"], d["actions"]) == (False, "principal_type_has_no_mfa", [])
    with pytest.raises(InvalidMfaResetError, match="cannot hold MFA factors"):
        compose_mfa_reset(sp, FACTORS, "2026-09-28T09:05:00Z")


def test_mfa_reset_rechecks_the_gate_and_rejects_duplicates() -> None:
    for gate in (False, "true"):
        t = confirmed()
        t["compromise_confirmed"] = gate
        with pytest.raises(InvalidMfaResetError, match="only when compromise_confirmed is True"):
            compose_mfa_reset(t, FACTORS, "2026-09-28T09:05:00Z")
    with pytest.raises(InvalidMfaResetError, match="listed twice"):
        compose_mfa_reset(confirmed(), FACTORS + FACTORS[:1], "2026-09-28T09:05:00Z")


# --------------------------------------------------------------------------- sessions


SESSIONS = [{"session_ref": "s:1", "tenant_ref": "tenant:idp", "kind": "session"},
            {"session_ref": "rt:9", "tenant_ref": "tenant:idp", "kind": "refresh_token"},
            {"session_ref": "s:4", "tenant_ref": "tenant:crm", "kind": "session"},
            {"session_ref": "s:1", "tenant_ref": "tenant:idp", "kind": "session"}]


def test_session_revocation_counts_and_names_the_coverage_gap() -> None:
    d = compose_session_revocation(confirmed(), SESSIONS, ["tenant:idp", "tenant:crm", "tenant:hr"],
                                   ["tenant:idp", "tenant:crm"], "2026-09-28T09:06:00Z")
    assert d["sessions_revoked_count"] == 3
    assert d["revoked_by_kind"] == {"session": 2, "refresh_token": 1, "device_grant": 0}
    assert d["uncovered_tenants"] == ["tenant:hr"]


def test_session_revocation_rejects_inconsistent_tenants() -> None:
    with pytest.raises(InvalidSessionRevocationError, match="not enumerated"):
        compose_session_revocation(confirmed(), SESSIONS, ["tenant:idp", "tenant:crm"], ["tenant:idp"],
                                   "2026-09-28T09:06:00Z")
    with pytest.raises(InvalidSessionRevocationError, match="cannot reach"):
        compose_session_revocation(confirmed(), [], ["tenant:idp"], ["tenant:idp", "tenant:x"],
                                   "2026-09-28T09:06:00Z")


# --------------------------------------------------------------------------- hunt


def finding(surface, resource, at) -> dict:
    return {"surface": surface, "resource_ref": resource, "observed_at": at}


def test_hunt_counts_distinct_resources_inside_the_window_and_reports_coverage() -> None:
    found = [finding("sts_assume_role", "role:prod-admin", "2026-09-28T08:00:00Z"),
             finding("host_logon", "role:prod-admin", "2026-09-28T08:30:00Z"),
             finding("host_logon", "host:jump-1", "2026-09-27T09:00:00Z"),      # exactly 24h: inside
             finding("host_logon", "host:old", "2026-09-27T08:59:59Z")]         # outside
    d = summarise_lateral_hunt(confirmed(), found, ["sts_assume_role", "host_logon", "api_token_reuse"], 24)
    assert d["lateral_findings_count"] == 2 and d["findings_outside_window"] == 1
    assert d["touched_resources"][1] == {"resource_ref": "role:prod-admin", "surfaces": ["host_logon", "sts_assume_role"]}
    assert d["unhunted_surfaces"] == ["cross_tenant_access", "oauth_grant_escalation"]
    assert d["coverage_percent"] == 60


def test_a_finding_on_an_unhunted_surface_fails_loud() -> None:
    with pytest.raises(InvalidHuntSummaryError, match="was not hunted"):
        summarise_lateral_hunt(confirmed(), [finding("api_token_reuse", "tok:1", DETECTED)], ["host_logon"], 24)
    with pytest.raises(InvalidHuntSummaryError):
        summarise_lateral_hunt(confirmed(), [], ["host_logon"], True)


# --------------------------------------------------------------------------- persistence


def item(ref, kind, created, change=None) -> dict:
    return {"item_ref": ref, "kind": kind, "created_at": created, "change_ref": change}


def test_persistence_removal_follows_the_window_and_change_record_rule() -> None:
    items = [item("oauth:mailreader", "oauth_consent", "2026-09-27T12:00:00Z"),
             item("rule:fwd-all", "inbox_rule", "2026-09-27T13:00:00Z"),
             item("role:global-admin", "role_assignment", "2026-09-27T14:00:00Z"),
             item("role:helpdesk", "role_assignment", "2026-09-27T15:00:00Z", "chg:4471"),
             item("device:old-laptop", "device_registration", "2026-01-10T00:00:00Z"),
             item("grant:new", "app_grant", "2026-09-28T10:00:00Z")]
    p = plan_persistence_removal(confirmed(), items, "2026-09-27T00:00:00Z")
    assert [r["item_ref"] for r in p["removals"]] == ["oauth:mailreader", "role:global-admin", "rule:fwd-all"]
    assert {k["item_ref"]: k["reason"] for k in p["kept"]} == {
        "device:old-laptop": "predates_compromise_window", "grant:new": "created_after_detection",
        "role:helpdesk": "authorised_change"}


def test_persistence_removal_rejects_inconsistent_inputs() -> None:
    with pytest.raises(InvalidPersistenceRemovalError, match="after detection"):
        plan_persistence_removal(confirmed(), [], "2026-09-28T09:00:01Z")
    with pytest.raises(InvalidPersistenceRemovalError, match="listed twice"):
        plan_persistence_removal(confirmed(), [item("x", "inbox_rule", DETECTED)] * 2, "2026-09-27T00:00:00Z")


# --------------------------------------------------------------------------- cross-cutting


def _outputs() -> list:
    t = confirmed()
    return [t,
            compose_mfa_reset(t, FACTORS, "2026-09-28T09:05:00Z"),
            compose_session_revocation(t, SESSIONS[:1], ["tenant:idp"], ["tenant:idp"], "2026-09-28T09:06:00Z"),
            summarise_lateral_hunt(t, [], ["host_logon"], 24)]


def test_every_stamped_metric_is_declared_by_the_playbook() -> None:
    playbook = json.loads((REPO_ROOT / "content/playbooks/identity_compromise/playbook.cacao.json").read_text(encoding="utf-8"))
    declared = set(secops_extension(playbook)["metric_refs"])
    stamped = {m for out in _outputs() for m in out["metric_stamps"]}
    assert stamped <= declared, f"undeclared: {sorted(stamped - declared)}"


def test_outputs_are_json_native() -> None:
    for out in _outputs() + [plan_persistence_removal(confirmed(), [], "2026-09-27T00:00:00Z")]:
        assert json.loads(json.dumps(out)) == out


def test_end_to_end_a_privileged_signal_is_contained_and_cleaned_up() -> None:
    t = triage(["impossible_travel"], ADMIN)
    assert t["compromise_confirmed"] is True and t["confirmation_basis"] == "privileged_principal"
    mfa = compose_mfa_reset(t, FACTORS, "2026-09-28T09:05:00Z")
    rev = compose_session_revocation(t, SESSIONS, ["tenant:idp", "tenant:crm"], ["tenant:idp", "tenant:crm"],
                                     "2026-09-28T09:06:00Z")
    hunt = summarise_lateral_hunt(t, [], list(("sts_assume_role", "cross_tenant_access", "api_token_reuse",
                                               "oauth_grant_escalation", "host_logon")), 72)
    plan = plan_persistence_removal(t, [item("rule:fwd-all", "inbox_rule", "2026-09-28T01:00:00Z")],
                                    "2026-09-28T00:00:00Z")
    assert mfa["principal_id"] == rev["principal_id"] == hunt["principal_id"] == plan["principal_id"] == "user:jdoe"
    assert rev["uncovered_tenants"] == [] and hunt["coverage_percent"] == 100
    assert [r["item_ref"] for r in plan["removals"]] == ["rule:fwd-all"]
