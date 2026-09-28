"""Unit coverage for content/playbooks/ransomware_containment/primitives (CORE-PRIM)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from content.playbooks.ransomware_containment.primitives import (
    InvalidBackupSelectionError,
    InvalidCommsPlanError,
    InvalidIdentityRevocationError,
    InvalidIsolationDirectiveError,
    InvalidRansomwareSignalError,
    compose_comms_plan,
    compose_edr_isolation,
    compose_identity_revocation,
    compose_network_isolation,
    select_known_good_snapshot,
    triage_ransomware_signal,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
EDR_UP = {"agent_reachable": True, "isolate_capable": True}
EDR_DOWN = {"agent_reachable": False, "isolate_capable": True}
POLICY = {"auto_isolate": True, "protected_hosts": ["host:dc-01"]}
CAPS = {"token_revocation": True, "kerberos": True}
CHANNELS = {"ir_lead": "chan:ir-lead", "comms_officer": "chan:comms"}
A, B, C = "a" * 64, "b" * 64, "c" * 64


def signal(indicators, *, host="host:fs-07", identity="user:jdoe", source="edr") -> dict:
    return {"signal_id": "sig:4411", "source": source, "detected_at": "2026-09-25T02:00:00Z",
            "host_ref": host, "identity_ref": identity, "indicators": list(indicators)}


def confirmed(edr=EDR_UP, **kw) -> dict:
    return triage_ransomware_signal(signal(["ransom_note_observed"], **kw), edr)


# --------------------------------------------------------------------------- triage


@pytest.mark.parametrize(("indicators", "expected", "basis"), [
    (["known_ransomware_artifact"], True, "decisive_artifact"),
    (["ransom_note_observed"], True, "decisive_artifact"),
    (["mass_file_extension_rename", "shadow_copy_deletion"], True, "encryption_behaviour_corroborated"),
    (["mass_file_extension_rename", "credential_abuse"], True, "encryption_behaviour_corroborated"),
    (["shadow_copy_deletion", "backup_catalog_deletion"], True, "recovery_inhibition"),
    (["mass_file_extension_rename"], False, "insufficient_evidence"),
    (["shadow_copy_deletion"], False, "insufficient_evidence"),
    (["credential_abuse"], False, "insufficient_evidence"),
    ([], False, "insufficient_evidence"),
])
def test_the_confirmation_rule(indicators, expected, basis) -> None:
    t = triage_ransomware_signal(signal(indicators), EDR_UP)
    assert (t["ransomware_confirmed"], t["confirmation_basis"]) == (expected, basis)
    assert t["overridden_by_analyst"] is False


def test_recovery_inhibition_confirms_before_any_encryption() -> None:
    t = triage_ransomware_signal(signal(["backup_catalog_deletion", "shadow_copy_deletion"]), EDR_UP)
    assert t["ransomware_confirmed"] is True
    assert "mass_file_extension_rename" not in t["indicators"]


@pytest.mark.parametrize(("indicators", "verdict", "expected", "overridden"), [
    (["ransom_note_observed"], "benign", False, True),        # a red-team exercise looks real
    (["shadow_copy_deletion"], "confirmed", True, True),
    (["ransom_note_observed"], "confirmed", True, False),
    (["ransom_note_observed"], "", True, False),               # n8n's unset variable
    (["ransom_note_observed"], None, True, False),
])
def test_an_analyst_verdict_decides_and_disagreement_is_recorded(indicators, verdict, expected, overridden) -> None:
    t = triage_ransomware_signal(signal(indicators), EDR_UP, verdict)
    assert (t["ransomware_confirmed"], t["overridden_by_analyst"]) == (expected, overridden)


def test_edr_is_available_only_when_reachable_and_capable() -> None:
    assert confirmed(EDR_UP)["edr_available"] is True
    assert confirmed(EDR_DOWN)["edr_available"] is False
    assert confirmed({"agent_reachable": True, "isolate_capable": False})["edr_available"] is False


def test_triage_record_shape() -> None:
    t = triage_ransomware_signal(
        signal(["shadow_copy_deletion", "backup_catalog_deletion", "shadow_copy_deletion"], identity=None),
        EDR_UP)
    assert t["indicators"] == ["backup_catalog_deletion", "shadow_copy_deletion"]
    assert t["identity_ref"] is None
    assert t["triage_id"] == triage_ransomware_signal(signal(["ransom_note_observed"], identity=None),
                                                      EDR_UP)["triage_id"]


@pytest.mark.parametrize(("sig", "edr", "verdict"), [
    (signal(["encrypted_everything"]), EDR_UP, None),              # unknown indicator: fail loud
    (signal(["ransom_note_observed"], source="email"), EDR_UP, None),
    (signal(["ransom_note_observed"]), {"agent_reachable": "true", "isolate_capable": True}, None),
    (signal(["ransom_note_observed"]), {"agent_reachable": True}, None),
    (signal(["ransom_note_observed"]), EDR_UP, "maybe"),
    ({**signal(["ransom_note_observed"]), "detected_at": "yesterday"}, EDR_UP, None),
])
def test_triage_rejects_malformed_inputs(sig, edr, verdict) -> None:
    with pytest.raises(InvalidRansomwareSignalError):
        triage_ransomware_signal(sig, edr, verdict)


# --------------------------------------------------------------------------- isolation


def test_edr_isolation_keeps_the_management_channel() -> None:
    d = compose_edr_isolation(confirmed(), POLICY, "2026-09-25T02:05:00Z")
    assert d["action"] == "edr_isolate" and d["preserve"] == ["edr_management_channel"]
    assert (d["requires_approval"], d["approval_reason"]) == (False, None)


def test_a_protected_host_always_waits_for_approval() -> None:
    d = compose_edr_isolation(confirmed(host="host:dc-01"), POLICY, "2026-09-25T02:05:00Z")
    assert (d["requires_approval"], d["approval_reason"]) == (True, "protected_host")
    off = compose_edr_isolation(confirmed(), {"auto_isolate": False, "protected_hosts": []},
                                "2026-09-25T02:05:00Z")
    assert (off["requires_approval"], off["approval_reason"]) == (True, "auto_isolate_disabled")


def test_network_fallback() -> None:
    d = compose_network_isolation(confirmed(EDR_DOWN), POLICY, "fw:edge-01", "2026-09-25T02:05:00Z")
    assert d["action"] == "network_deny_all" and d["chokepoint_ref"] == "fw:edge-01"
    assert d["preserve"] == []


def test_each_isolation_branch_rechecks_its_gates() -> None:
    with pytest.raises(InvalidIsolationDirectiveError, match="edr_available is True"):
        compose_edr_isolation(confirmed(EDR_DOWN), POLICY, "2026-09-25T02:05:00Z")
    with pytest.raises(InvalidIsolationDirectiveError, match="edr_available is False"):
        compose_network_isolation(confirmed(EDR_UP), POLICY, "fw:edge-01", "2026-09-25T02:05:00Z")
    unconfirmed = triage_ransomware_signal(signal(["credential_abuse"]), EDR_UP)
    for gate in (False, "true"):
        unconfirmed["ransomware_confirmed"] = gate
        with pytest.raises(InvalidIsolationDirectiveError, match="only when ransomware_confirmed is True"):
            compose_edr_isolation(unconfirmed, POLICY, "2026-09-25T02:05:00Z")


def test_isolation_rejects_a_malformed_policy() -> None:
    with pytest.raises(InvalidIsolationDirectiveError):
        compose_edr_isolation(confirmed(), {"auto_isolate": "yes", "protected_hosts": []}, "2026-09-25T02:05:00Z")


# --------------------------------------------------------------------------- identity


def test_identity_revocation_full_capability() -> None:
    d = compose_identity_revocation(confirmed(), CAPS, [], "2026-09-25T02:06:00Z")
    assert [a["action"] for a in d["actions"]] == [
        "disable_account", "revoke_sessions", "revoke_tokens", "invalidate_kerberos_tickets"]
    assert d["unsupported"] == [] and d["requires_approval"] is False


def test_what_the_idp_cannot_revoke_is_listed_not_claimed() -> None:
    d = compose_identity_revocation(confirmed(), {"token_revocation": False, "kerberos": False}, [],
                                    "2026-09-25T02:06:00Z")
    assert [a["action"] for a in d["actions"]] == ["disable_account", "revoke_sessions"]
    assert d["unsupported"] == ["revoke_tokens", "invalidate_kerberos_tickets"]


def test_no_implicated_principal_means_no_target_invented() -> None:
    d = compose_identity_revocation(confirmed(identity=None), CAPS, [], "2026-09-25T02:06:00Z")
    assert d["identity_implicated"] is False and d["actions"] == []


def test_a_protected_identity_waits_for_approval() -> None:
    d = compose_identity_revocation(confirmed(identity="svc:backup"), CAPS, ["svc:backup"],
                                    "2026-09-25T02:06:00Z")
    assert (d["requires_approval"], d["approval_reason"]) == (True, "protected_identity")


def test_identity_revocation_rechecks_confirmation_and_capability_types() -> None:
    with pytest.raises(InvalidIdentityRevocationError):
        compose_identity_revocation(triage_ransomware_signal(signal([]), EDR_UP), CAPS, [],
                                    "2026-09-25T02:06:00Z")
    with pytest.raises(InvalidIdentityRevocationError):
        compose_identity_revocation(confirmed(), {"token_revocation": 1, "kerberos": True}, [],
                                    "2026-09-25T02:06:00Z")


# --------------------------------------------------------------------------- backup


SNAPS = [
    {"snapshot_id": "snap:0924-22", "taken_at": "2026-09-24T22:00:00Z", "sha256": A},   # newest before window
    {"snapshot_id": "snap:0924-12", "taken_at": "2026-09-24T12:00:00Z", "sha256": B},
    {"snapshot_id": "snap:0923-12", "taken_at": "2026-09-23T12:00:00Z", "sha256": C.upper()},
    {"snapshot_id": "snap:0925-01", "taken_at": "2026-09-25T01:00:00Z", "sha256": A},   # at the window start
    {"snapshot_id": "snap:0925-02", "taken_at": "2026-09-25T02:30:00Z", "sha256": A},
]
WINDOW = "2026-09-25T01:00:00Z"


def test_known_good_is_the_newest_verified_snapshot_before_the_window() -> None:
    catalogue = {"snap:0924-22": "d" * 64, "snap:0923-12": C}     # 0924-22 mismatches, 0924-12 unrecorded
    r = select_known_good_snapshot(SNAPS, catalogue, WINDOW)
    assert r["latest_known_good_snapshot"] == "snap:0923-12" and r["snapshot_integrity_ok"] is True
    assert r["rejected"] == [{"snapshot_id": "snap:0924-22", "reason": "digest_mismatch"},
                             {"snapshot_id": "snap:0924-12", "reason": "no_catalogue_record"}]
    assert r["inside_compromise_window"] == 2 and r["restored"] is False


def test_a_snapshot_taken_exactly_at_the_window_start_is_excluded() -> None:
    r = select_known_good_snapshot(SNAPS[3:4], {"snap:0925-01": A}, WINDOW)
    assert r["latest_known_good_snapshot"] is None and r["inside_compromise_window"] == 1


def test_nothing_verifies_means_no_known_good_snapshot() -> None:
    r = select_known_good_snapshot(SNAPS, {}, WINDOW)
    assert (r["latest_known_good_snapshot"], r["snapshot_integrity_ok"]) == (None, False)
    assert len(r["rejected"]) == 3


@pytest.mark.parametrize(("snaps", "catalogue"), [
    ([SNAPS[0], SNAPS[0]], {}),
    ([{**SNAPS[0], "sha256": "not-a-digest"}], {}),
    ([SNAPS[0]], {"snap:0924-22": "short"}),
    ("snap:0924-22", {}),
])
def test_backup_selection_rejects_malformed_inputs(snaps, catalogue) -> None:
    with pytest.raises(InvalidBackupSelectionError):
        select_known_good_snapshot(snaps, catalogue, WINDOW)


# --------------------------------------------------------------------------- comms


def backup_ok() -> dict:
    return select_known_good_snapshot(SNAPS, {"snap:0924-22": A}, WINDOW)


def test_comms_plan_stages_the_early_warning_for_sign_off() -> None:
    p = compose_comms_plan(confirmed(), backup_ok(), CHANNELS, "2026-09-25T09:00:00Z")
    ew = p["early_warning"]
    assert ew["status"] == "staged_for_sign_off" and ew["auto_send"] is False
    assert ew["due_at"] == "2026-09-26T02:00:00Z" and ew["within_clock"] is True
    assert ew["facts"]["latest_known_good_snapshot"] == "snap:0924-22"
    assert [n["role"] for n in p["notifications"]] == ["ir_lead", "comms_officer"]


def test_a_late_draft_records_the_overrun() -> None:
    p = compose_comms_plan(confirmed(), backup_ok(), CHANNELS, "2026-09-26T02:00:01Z")
    assert p["early_warning"]["within_clock"] is False
    edge = compose_comms_plan(confirmed(), backup_ok(), CHANNELS, "2026-09-26T02:00:00Z")
    assert edge["early_warning"]["within_clock"] is True


def test_comms_plan_rejects_inconsistent_inputs() -> None:
    with pytest.raises(InvalidCommsPlanError, match="before detection"):
        compose_comms_plan(confirmed(), backup_ok(), CHANNELS, "2026-09-25T01:59:59Z")
    with pytest.raises(InvalidCommsPlanError):
        compose_comms_plan(confirmed(), backup_ok(), {"ir_lead": "chan:x"}, "2026-09-25T09:00:00Z")
    with pytest.raises(InvalidCommsPlanError):
        compose_comms_plan(triage_ransomware_signal(signal([]), EDR_UP), backup_ok(), CHANNELS,
                           "2026-09-25T09:00:00Z")


# --------------------------------------------------------------------------- cross-cutting


def _outputs() -> list[dict]:
    t, down = confirmed(), confirmed(EDR_DOWN)
    return [
        compose_edr_isolation(t, POLICY, "2026-09-25T02:05:00Z"),
        compose_network_isolation(down, POLICY, "fw:edge-01", "2026-09-25T02:05:00Z"),
        compose_identity_revocation(t, CAPS, [], "2026-09-25T02:06:00Z"),
        backup_ok(),
        compose_comms_plan(t, backup_ok(), CHANNELS, "2026-09-25T09:00:00Z"),
    ]


def test_every_stamped_metric_is_declared_by_the_playbook() -> None:
    playbook = json.loads((REPO_ROOT / "content/playbooks/ransomware_containment/playbook.cacao.json")
                          .read_text(encoding="utf-8"))
    declared = set(playbook["x_secops_ng"]["metric_refs"])
    stamped = {m for out in _outputs() for m in out["metric_stamps"]}
    assert stamped <= declared, f"undeclared: {sorted(stamped - declared)}"


def test_outputs_are_json_native() -> None:
    for out in _outputs() + [confirmed()]:
        assert json.loads(json.dumps(out)) == out


def test_end_to_end_a_signal_flows_from_triage_to_the_comms_plan() -> None:
    t = triage_ransomware_signal(
        signal(["mass_file_extension_rename", "credential_abuse"], identity="user:jdoe"), EDR_DOWN)
    assert t["ransomware_confirmed"] is True and t["edr_available"] is False
    iso = compose_network_isolation(t, POLICY, "fw:edge-01", "2026-09-25T02:05:00Z")
    rev = compose_identity_revocation(t, CAPS, [], "2026-09-25T02:06:00Z")
    bkp = select_known_good_snapshot(SNAPS, {"snap:0924-22": A}, WINDOW)
    plan = compose_comms_plan(t, bkp, CHANNELS, "2026-09-25T03:00:00Z")
    assert iso["host_ref"] == plan["early_warning"]["facts"]["host_ref"] == t["host_ref"]
    assert rev["identity_ref"] == plan["early_warning"]["facts"]["identity_ref"] == t["identity_ref"]
    assert plan["early_warning"]["facts"]["snapshot_integrity_ok"] is True
