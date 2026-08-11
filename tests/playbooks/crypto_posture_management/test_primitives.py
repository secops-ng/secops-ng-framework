"""Unit tests for the NIS2 Art. 21(2)(h) crypto-posture primitives (CORE).

The assertions worth reading pin the drift-versus-gap distinction, which is the
design's whole point: a posture contradicting a stated clause is a drift and
goes to whoever runs the infrastructure; one the policy is silent about is a
gap and goes to whoever owns the policy. Collapsing them sends the operator to
the wrong place.
"""
from __future__ import annotations

import pytest

from content.playbooks.crypto_posture_management.primitives.certificates import (
    InvalidCertPostureError,
    probe_cert_posture,
)
from content.playbooks.crypto_posture_management.primitives.evidence import (
    InvalidCryptoEvidenceError,
    capture_crypto_evidence,
    derive_posture_artifact_id,
)
from content.playbooks.crypto_posture_management.primitives.notify import (
    InvalidCryptoNotificationError,
    plan_crypto_owner_notification,
)
from content.playbooks.crypto_posture_management.primitives.policy import (
    CRYPTO_CONCERNS,
    InvalidCryptoPolicyError,
    inventory_crypto_policy,
)
from content.playbooks.crypto_posture_management.primitives.rotation import (
    InvalidKeyRotationError,
    check_key_rotation,
)

WINDOW = "2026-01-01/2026-03-31"
SCOPE = "tls-estate"
FLOOR = "TLS_AES_128_GCM_SHA256"


def _inv(**over):
    kw = {
        "posture_window": WINDOW, "crypto_scope": SCOPE,
        "policy_clauses": [
            {"clause_ref": "pol/3-1", "concern": "cipher_suite_floor",
             "threshold": FLOOR},
            {"clause_ref": "pol/3-2", "concern": "key_rotation_interval_days",
             "threshold": 365},
        ],
        "scoped_assets": ["asset-a", "asset-b"],
    }
    kw.update(over)
    return inventory_crypto_policy(**kw)


def _certs(inv=None, obs=None, **over):
    kw = {
        "crypto_scope": SCOPE, "policy_inventory": inv or _inv(),
        "certificate_observations": obs if obs is not None else [],
        "accepted_cipher_suites": [FLOOR],
    }
    kw.update(over)
    return probe_cert_posture(**kw)


def _rot(inv=None, keys=None, **over):
    kw = {"crypto_scope": SCOPE, "policy_inventory": inv or _inv(),
          "key_records": keys if keys is not None else []}
    kw.update(over)
    return check_key_rotation(**kw)


# --- policy inventory -------------------------------------------------------


def test_inventory_reports_governed_and_ungoverned_concerns() -> None:
    inv = _inv()
    assert inv["governed_concerns"] == [
        "cipher_suite_floor", "key_rotation_interval_days"
    ]
    assert set(inv["ungoverned_concerns"]) == CRYPTO_CONCERNS - set(
        inv["governed_concerns"]
    )


def test_two_clauses_for_one_concern_is_refused() -> None:
    """Two clauses governing one concern make every verdict ambiguous."""
    with pytest.raises(InvalidCryptoPolicyError, match="a second time"):
        _inv(policy_clauses=[
            {"clause_ref": "pol/a", "concern": "cipher_suite_floor", "threshold": FLOOR},
            {"clause_ref": "pol/b", "concern": "cipher_suite_floor", "threshold": FLOOR},
        ])


def test_unknown_concern_is_refused() -> None:
    """A typo would otherwise read as a policy gap — the worst outcome."""
    with pytest.raises(InvalidCryptoPolicyError, match="concern"):
        _inv(policy_clauses=[
            {"clause_ref": "pol/a", "concern": "cypher_floor", "threshold": FLOOR},
        ])


def test_empty_scope_is_refused() -> None:
    with pytest.raises(InvalidCryptoPolicyError, match="scope definition"):
        _inv(scoped_assets=[])


def test_policy_with_no_clauses_governs_nothing() -> None:
    """Legitimate state: an operator with no written crypto policy."""
    inv = _inv(policy_clauses=[])
    assert inv["governed_concerns"] == []
    assert len(inv["ungoverned_concerns"]) == len(CRYPTO_CONCERNS)


# --- drift versus gap -------------------------------------------------------


def test_expired_cert_is_a_gap_when_no_validity_clause_exists() -> None:
    """The policy states no maximum validity, so this is a policy gap — no
    amount of reissuing certificates fixes it."""
    cp = _certs(obs=[{"asset_id": "asset-a", "certificate_ref": "cert/a",
                      "not_after": "2026-01-15"}])
    assert [(f["kind"], f["verdict"], f["clause_ref"]) for f in cp["findings"]] == [
        ("expired_certificate", "gap", "")
    ]


def test_expired_cert_is_a_drift_when_a_validity_clause_exists() -> None:
    inv = _inv(policy_clauses=[
        {"clause_ref": "pol/3-3", "concern": "certificate_validity_max_days",
         "threshold": 90},
    ])
    cp = _certs(inv=inv, accepted_cipher_suites=[],
                obs=[{"asset_id": "asset-a", "certificate_ref": "cert/a",
                      "not_after": "2026-01-15"}])
    f = cp["findings"][0]
    assert (f["kind"], f["verdict"], f["clause_ref"]) == (
        "expired_certificate", "drift", "pol/3-3"
    )


def test_weak_cipher_names_the_clause_it_contradicts() -> None:
    cp = _certs(obs=[{"asset_id": "asset-a", "certificate_ref": "cert/a",
                      "not_after": "2027-01-01",
                      "cipher_suite": "TLS_RSA_WITH_3DES_EDE_CBC_SHA"}])
    f = cp["findings"][0]
    assert (f["kind"], f["verdict"], f["clause_ref"]) == (
        "weak_cipher", "drift", "pol/3-1"
    )


def test_accepted_suite_is_conforming() -> None:
    cp = _certs(obs=[{"asset_id": "asset-a", "certificate_ref": "cert/a",
                      "not_after": "2027-01-01", "cipher_suite": FLOOR}])
    assert cp["findings"] == []
    assert cp["conforming_count"] == 1


def test_governed_cipher_floor_without_an_accepted_list_is_refused() -> None:
    """The clause names a floor; which suites clear it is the operator's list."""
    with pytest.raises(InvalidCertPostureError, match="operator's own list"):
        _certs(accepted_cipher_suites=[])


def test_pem_shaped_reference_is_refused() -> None:
    """The boundary against key material is here, not in the hygiene linter."""
    with pytest.raises(InvalidCertPostureError, match="PEM key material"):
        _certs(obs=[{"asset_id": "asset-a",
                     "certificate_ref": "BEGIN-RSA-PRIVATE-KEY-block",
                     "not_after": "2027-01-01"}])


def test_out_of_scope_observation_is_refused() -> None:
    with pytest.raises(InvalidCertPostureError, match="widen the posture"):
        _certs(obs=[{"asset_id": "asset-z", "certificate_ref": "cert/z",
                     "not_after": "2027-01-01"}])


def test_scope_mismatch_between_probe_and_inventory_is_refused() -> None:
    with pytest.raises(InvalidCertPostureError, match="does not match"):
        _certs(crypto_scope="other-estate")


# --- rotation ---------------------------------------------------------------


def test_overdue_key_is_a_drift_naming_the_interval_clause() -> None:
    rs = _rot(keys=[{"asset_id": "asset-a", "key_ref": "key/a",
                     "last_rotated_on": "2024-01-01"}])
    f = rs["findings"][0]
    assert (f["kind"], f["verdict"], f["clause_ref"]) == (
        "missed_rotation", "drift", "pol/3-2"
    )
    assert f["age_days"] == 820


def test_overdue_key_is_a_gap_when_no_interval_clause_exists() -> None:
    inv = _inv(policy_clauses=[])
    rs = _rot(inv=inv, keys=[{"asset_id": "asset-a", "key_ref": "key/a",
                              "last_rotated_on": "2000-01-01"}])
    assert rs["findings"][0]["verdict"] == "gap"
    assert rs["interval_days"] is None


def test_never_rotated_is_distinct_from_missed_rotation() -> None:
    """The absence of a schedule is not a lapse in one."""
    rs = _rot(keys=[{"asset_id": "asset-b", "key_ref": "key/b"}])
    assert rs["findings"][0]["kind"] == "never_rotated"
    assert rs["findings"][0]["age_days"] is None
    assert rs["never_rotated_count"] == 1


def test_key_inside_the_interval_is_conforming() -> None:
    rs = _rot(keys=[{"asset_id": "asset-a", "key_ref": "key/a",
                     "last_rotated_on": "2026-01-01"}])
    assert rs["findings"] == []
    assert rs["conforming_count"] == 1


def test_rotation_after_the_evaluation_date_is_refused() -> None:
    with pytest.raises(InvalidKeyRotationError, match="cannot have been rotated"):
        _rot(keys=[{"asset_id": "asset-a", "key_ref": "key/a",
                    "last_rotated_on": "2027-01-01"}])


# --- attestation ------------------------------------------------------------


def _att(**over):
    inv = over.pop("inv", None) or _inv()
    kw = {
        "policy_inventory": inv,
        "cert_posture": _certs(inv=inv),
        "rotation_status": _rot(inv=inv),
        "posture_window": WINDOW, "owner_role": "crypto-owner",
        "workflow_id": "wf-1", "execution_id": "ex-1",
        "captured_at": "2026-04-01T09:00:00Z",
    }
    kw.update(over)
    return capture_crypto_evidence(**kw)


def test_clean_posture_is_conforming() -> None:
    a = _att()
    assert (a["drift_count"], a["gap_count"]) == (0, 0)
    assert a["posture_conforming"] is True


def test_one_finding_makes_the_window_non_conforming() -> None:
    """The conjunction, not an average: one expired cert is one expired cert."""
    inv = _inv()
    a = _att(inv=inv, cert_posture=_certs(
        inv=inv, obs=[{"asset_id": "asset-a", "certificate_ref": "cert/a",
                       "not_after": "2026-01-15"}]))
    assert a["gap_count"] == 1
    assert a["posture_conforming"] is False


def test_drift_and_gap_stay_separate_to_the_top() -> None:
    """They route to different owners, so one merged count would misroute."""
    inv = _inv()
    a = _att(inv=inv,
             cert_posture=_certs(inv=inv, obs=[
                 {"asset_id": "asset-a", "certificate_ref": "cert/a",
                  "not_after": "2026-01-15",
                  "cipher_suite": "TLS_RSA_WITH_3DES_EDE_CBC_SHA"}]),
             rotation_status=_rot(inv=inv, keys=[
                 {"asset_id": "asset-a", "key_ref": "key/a",
                  "last_rotated_on": "2024-01-01"}]))
    assert a["drift_count"] == 2 and a["gap_count"] == 1


def test_envelope_scope_disagreement_is_refused() -> None:
    other = _inv(crypto_scope="other-estate")
    with pytest.raises(InvalidCryptoEvidenceError, match="one posture run"):
        _att(cert_posture=probe_cert_posture(
            crypto_scope="other-estate", policy_inventory=other,
            certificate_observations=[], accepted_cipher_suites=[FLOOR]))


def test_attestation_carries_a_disclaimer_about_gap_verdicts() -> None:
    assert "policy is silent" in _att()["disclaimer"]


def test_artifact_id_follows_the_house_derivation() -> None:
    import hashlib
    expected = hashlib.sha256(b"wf-1|ex-1|2026-04-01T09:00:00Z").hexdigest()
    assert _att()["artifact_id"] == expected
    assert derive_posture_artifact_id(
        "wf-1", "ex-1", "2026-04-01T09:00:00Z") == expected


def test_attestation_is_deterministic() -> None:
    assert _att() == _att()


# --- notification -----------------------------------------------------------


def test_plan_is_never_a_receipt() -> None:
    n = plan_crypto_owner_notification(
        _att(), SCOPE, "crypto-owner", "chan/crypto")
    assert n["dispatched"] is False


def test_clean_posture_still_produces_a_plan() -> None:
    """Silence is indistinguishable from the run never happening."""
    n = plan_crypto_owner_notification(
        _att(), SCOPE, "crypto-owner", "chan/crypto")
    assert n["reason"] == "posture_clean"
    assert n["escalate"] is False


def test_reason_distinguishes_drift_gap_and_both() -> None:
    inv = _inv()
    drift_only = _att(inv=inv, rotation_status=_rot(inv=inv, keys=[
        {"asset_id": "asset-a", "key_ref": "key/a", "last_rotated_on": "2024-01-01"}]))
    gap_only = _att(inv=inv, cert_posture=_certs(inv=inv, obs=[
        {"asset_id": "asset-a", "certificate_ref": "cert/a", "not_after": "2026-01-15"}]))
    plan = lambda a: plan_crypto_owner_notification(  # noqa: E731
        a, SCOPE, "crypto-owner", "chan/crypto")["reason"]
    assert plan(drift_only) == "policy_drift"
    assert plan(gap_only) == "policy_gap"


def test_notification_scope_mismatch_is_refused() -> None:
    with pytest.raises(InvalidCryptoNotificationError, match="does not match"):
        plan_crypto_owner_notification(
            _att(), "other-estate", "crypto-owner", "chan/crypto")


def test_owner_is_a_role_not_a_person() -> None:
    with pytest.raises(InvalidCryptoNotificationError, match="owner_role"):
        plan_crypto_owner_notification(
            _att(), SCOPE, "Jane Doe", "chan/crypto")
